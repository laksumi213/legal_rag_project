# src/services/koseki_service.py

import logging
import base64
import json
import re
import time
import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, Literal
from io import BytesIO
from dateutil.relativedelta import relativedelta

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import asc
from pdf2image import convert_from_bytes

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import FamilyRegister, Case, Deceased, Heir
from src.utils.date_utils import parse_all_flexible_date

logger = logging.getLogger(__name__)

class KosekiService:
    def __init__(self):
        self.db = DatabaseManager()
        # 構造化データ抽出のため temperature=0.0
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def _invoke_llm_with_timeout(self, messages: List[HumanMessage], timeout_sec: int = 300):
        try:
            return self.llm.invoke(messages, config={"timeout": timeout_sec})
        except TypeError:
            return self.llm.invoke(messages)

    def _normalize_name(self, name: str) -> str:
        return (name or "").replace(" ", "").replace("　", "").strip()

    def _format_date_yyyy_mm_dd(self, date_str: Optional[str]) -> str:
        if not date_str:
            return ""
        d = parse_all_flexible_date(date_str)
        return d.strftime("%Y-%m-%d") if d else ""

    def _extract_json_list_safe(self, content: str) -> List[Dict[str, Any]]:
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\[.*\])', content, re.DOTALL)
            if match:
                candidate = match.group(1)
                try:
                    parsed = json.loads(candidate)
                    return parsed if isinstance(parsed, list) else []
                except json.JSONDecodeError:
                    pass
            parsed = json.loads(content)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def _build_all_persons(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        persons: List[Dict[str, Any]] = []

        for member in data.get("family_list", []) or []:
            raw_name = member.get("name", "")
            clean_name = self._normalize_name(raw_name)
            if not clean_name:
                continue
            persons.append({
                "name": raw_name,
                "rel": member.get("rel", ""),
                "birth_date": self._format_date_yyyy_mm_dd(member.get("birth_date")),
                "death_date": self._format_date_yyyy_mm_dd(member.get("death_date")),
            })

        head_name = data.get("head_name")
        if head_name and self._normalize_name(head_name):
            persons.append({
                "name": head_name,
                "rel": "筆頭者",
                "birth_date": "",
                "death_date": "",
            })

        target_person = data.get("target_person")
        if target_person and self._normalize_name(target_person):
            persons.append({
                "name": target_person,
                "rel": "対象者",
                "birth_date": self._format_date_yyyy_mm_dd(data.get("target_birth_date")),
                "death_date": self._format_date_yyyy_mm_dd(data.get("target_death_date")),
            })

        dedup: Dict[str, Dict[str, Any]] = {}
        for p in persons:
            key = self._normalize_name(p.get("name", ""))
            if not key:
                continue
            if key not in dedup:
                dedup[key] = p
                continue

            current = dedup[key]
            if not current.get("rel") and p.get("rel"):
                current["rel"] = p.get("rel")
            if not current.get("birth_date") and p.get("birth_date"):
                current["birth_date"] = p.get("birth_date")
            if not current.get("death_date") and p.get("death_date"):
                current["death_date"] = p.get("death_date")

        return list(dedup.values())

    def _heuristic_is_heir(self, rel: str, death_date: str) -> bool:
        if death_date:
            return False
        rel_norm = (rel or "").strip()
        if not rel_norm:
            return False

        keywords = [
            "妻", "夫", "配偶者",
            "子", "長男", "次男", "三男", "四男", "五男",
            "長女", "次女", "三女", "四女", "五女",
            "養子", "養女",
            "父", "母", "実父", "実母",
            "兄", "弟", "姉", "妹",
        ]
        return any(k in rel_norm for k in keywords)

    def mark_inheritors(
        self,
        persons: List[Dict[str, Any]],
        base_person_name: str,
        case_mode: Literal["will", "inheritance"],
    ) -> List[Dict[str, Any]]:
        base_key = self._normalize_name(base_person_name)

        items_for_llm = [
            {
                "name": p.get("name", ""),
                "rel": p.get("rel", ""),
                "birth_date": p.get("birth_date", ""),
                "death_date": p.get("death_date", ""),
            }
            for p in persons
        ]

        system_prompt = """
あなたは相続実務に精通した行政書士の補助者です。
以下の戸籍の人物一覧について、基準人物の推定相続人に該当する人物を判定し、各人物に is_heir(true/false) を付与してください。

判断方針:
- case_mode が inheritance の場合: 基準人物は被相続人。
- case_mode が will の場合: 基準人物は遺言者(契約者)。
- death_date がある人物は原則として相続人ではないものとして is_heir=false。
- 代襲相続等の複雑な判断は行わず、判断不能の場合は false。

出力は JSON 配列のみ。
要素は {"name": "氏名", "is_heir": true/false } のみ。
""".strip()

        user_prompt = json.dumps(
            {
                "case_mode": case_mode,
                "base_person": base_person_name,
                "persons": items_for_llm,
            },
            ensure_ascii=False,
        )

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{payload}"),
            ])
            chain = prompt | self.llm | StrOutputParser()
            resp_text = chain.invoke({"payload": user_prompt})
            flags = self._extract_json_list_safe(resp_text)
            flag_map: Dict[str, bool] = {}
            for f in flags:
                name_key = self._normalize_name(str(f.get("name", "")))
                if not name_key:
                    continue
                flag_map[name_key] = bool(f.get("is_heir", False))

            marked: List[Dict[str, Any]] = []
            for p in persons:
                key = self._normalize_name(p.get("name", ""))
                is_heir = flag_map.get(key)
                if is_heir is None:
                    is_heir = self._heuristic_is_heir(p.get("rel", ""), p.get("death_date", ""))
                if key and base_key and key == base_key:
                    is_heir = False
                marked.append({**p, "is_heir": bool(is_heir)})
            return marked
        except Exception:
            marked: List[Dict[str, Any]] = []
            for p in persons:
                key = self._normalize_name(p.get("name", ""))
                is_heir = self._heuristic_is_heir(p.get("rel", ""), p.get("death_date", ""))
                if key and base_key and key == base_key:
                    is_heir = False
                marked.append({**p, "is_heir": bool(is_heir)})
            return marked

    def extract_people_table_rows(
        self,
        analysis_result: Dict[str, Any],
        base_person_name: str,
        case_mode: Literal["will", "inheritance"],
    ) -> List[Dict[str, Any]]:
        persons = self._build_all_persons(analysis_result)
        return self.mark_inheritors(persons, base_person_name=base_person_name, case_mode=case_mode)

    def _extract_json_safe(self, content: str) -> Dict[str, Any]:
        """AIの回答からJSON部分だけを安全に切り出すヘルパー関数"""
        def _strip_fences(text: str) -> str:
            return (text or "").replace("```json", "").replace("```", "").strip()

        def _extract_object_text(text: str) -> str:
            s = text or ""
            start = s.find("{")
            if start < 0:
                return ""
            end = s.rfind("}")
            if end > start:
                return s[start : end + 1]
            return s[start:]

        def _repair_truncated_json(text: str) -> str:
            s = (text or "").strip()
            if not s:
                return s

            in_string = False
            escape = False
            stack: List[str] = []

            for ch in s:
                if in_string:
                    if escape:
                        escape = False
                        continue
                    if ch == "\\":
                        escape = True
                        continue
                    if ch == '"':
                        in_string = False
                    continue

                if ch == '"':
                    in_string = True
                    continue
                if ch in "{[":
                    stack.append(ch)
                    continue
                if ch == "}" and stack and stack[-1] == "{":
                    stack.pop()
                    continue
                if ch == "]" and stack and stack[-1] == "[":
                    stack.pop()
                    continue

            if in_string and escape and s.endswith("\\"):
                s = s[:-1]
                escape = False

            if in_string:
                s += '"'

            for opener in reversed(stack):
                s += "}" if opener == "{" else "]"

            return s

        def _try_json_load(text: str) -> Optional[Dict[str, Any]]:
            try:
                obj = json.loads(text)
                return obj if isinstance(obj, dict) else None
            except Exception:
                return None

        def _salvage_partial(text: str) -> Optional[Dict[str, Any]]:
            raw = text or ""
            result: Dict[str, Any] = {}

            scalar_keys = [
                "doc_type",
                "honseki",
                "head_name",
                "target_person",
                "valid_from",
                "valid_to",
                "target_birth_date",
                "target_death_date",
            ]

            for k in scalar_keys:
                m = re.search(rf'"{re.escape(k)}"\s*:\s*"([^\"]*)"', raw)
                if m:
                    result[k] = m.group(1)
                    continue
                m_null = re.search(rf'"{re.escape(k)}"\s*:\s*null', raw)
                if m_null:
                    result[k] = None

            fam_match = re.search(r'"family_list"\s*:\s*\[', raw)
            if fam_match:
                start = fam_match.end() - 1
                arr_text = raw[start:]

                in_str = False
                esc = False
                depth = 0
                end_idx: Optional[int] = None
                for i, ch in enumerate(arr_text):
                    if in_str:
                        if esc:
                            esc = False
                            continue
                        if ch == "\\":
                            esc = True
                            continue
                        if ch == '"':
                            in_str = False
                        continue
                    if ch == '"':
                        in_str = True
                        continue
                    if ch == "[":
                        depth += 1
                        continue
                    if ch == "]":
                        depth -= 1
                        if depth == 0:
                            end_idx = i
                            break

                candidate = arr_text[: end_idx + 1] if end_idx is not None else arr_text
                candidate = _repair_truncated_json(candidate)
                try:
                    arr = json.loads(candidate)
                    if isinstance(arr, list):
                        result["family_list"] = arr
                except Exception:
                    pass

            if "family_list" not in result:
                result["family_list"] = []

            return result if result else None

        try:
            cleaned = _strip_fences(content)
            candidate = _extract_object_text(cleaned)

            obj = _try_json_load(candidate) or _try_json_load(cleaned)
            if obj is not None:
                return obj

            repaired_candidate = _repair_truncated_json(candidate)
            obj = _try_json_load(repaired_candidate)
            if obj is not None:
                return obj

            repaired_cleaned = _repair_truncated_json(cleaned)
            obj = _try_json_load(repaired_cleaned)
            if obj is not None:
                return obj

            partial = _salvage_partial(cleaned)
            if partial is not None:
                return partial

            return {"error": "JSON解析失敗: 解析可能なJSONが見つかりません"}
        except Exception as e:
            return {"error": f"JSON解析失敗: {str(e)}"}

    def analyze_koseki_image(self, file_bytes: bytes, mime_type: str, expected_name: str = "", family_name_hint: str = "") -> Dict[str, Any]:
        """
        戸籍謄本（複数ページ可）をAIで解析する
        :param expected_name: 対象者のフルネーム（抽出ターゲット）
        :param family_name_hint: 名字のヒント（誤読防止用）
        """
        image_contents = []
        if mime_type == "application/pdf":
            try:
                # PDFを画像リストに変換 (dpi=200程度で十分)
                images = convert_from_bytes(file_bytes, dpi=200)
                for img in images:
                    buf = BytesIO()
                    img.save(buf, format="JPEG")
                    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
                    image_contents.append({
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{b64_data}"
                    })
            except Exception as e:
                return {"error": f"PDF変換エラー: {e}"}
        else:
            img_b64 = base64.b64encode(file_bytes).decode("utf-8")
            image_contents.append({
                "type": "image_url",
                "image_url": f"data:{mime_type};base64,{img_b64}"
            })

        # プロンプトの構築（ヒント注入）
        name_hint_str = ""
        if expected_name:
            name_hint_str += f"- ターゲット人物: 「{expected_name}」\n"
        if family_name_hint:
            name_hint_str += f"- 名字のヒント: 「{family_name_hint}」 (手書き文字の認識優先度を上げてください)\n"

        def _build_prompt(strict_level: Literal["full", "lite"] = "full") -> str:
            forbid = """
        【重要: 出力制約】
        - 絶対に禁止: 戸籍の全文書き起こし、原文の貼り付け、ページごとのテキスト化、raw text/raw_text/transcriptionキーの出力
        - 絶対に禁止: 解説文、手順説明、根拠説明、Markdown、コードフェンス(```)
        - 出力は JSONオブジェクト1つのみ（前後に一切の文字を付けない）
        - 指定したキー以外は出力しない（余計なキーは禁止）
        """.strip()

            if strict_level == "lite":
                return f"""
        あなたは日本の戸籍解読のエキスパートAIです。
        提示された画像から、人物情報の抽出に必要な最小限の情報だけをJSONで返してください。

        {forbid}

        【読取精度向上のためのヒント】
        {name_hint_str}

        ### 抽出ルール
        - 記載されている人物を可能な限り列挙してください（筆頭者・対象者・配偶者・子・父母・養子など）。
        - 文字が判読不能な場合は空文字で構いません。

        ### 出力JSONスキーマ（このキーのみ）
        {{
          "doc_type": "現在戸籍|除籍謄本|改製原戸籍|住民票|不明",
          "honseki": "本籍地（不明なら空文字）",
          "head_name": "筆頭者氏名（不明なら空文字）",
          "target_person": "対象者氏名（不明なら空文字）",
          "valid_from": "YYYY-MM-DD（不明なら空文字）",
          "valid_to": "YYYY-MM-DD（不明なら空文字）",
          "target_birth_date": "YYYY-MM-DD（不明なら空文字）",
          "target_death_date": "YYYY-MM-DD または null",
          "family_list": [{{"name":"氏名","rel":"続柄","birth_date":"YYYY-MM-DD","death_date":"YYYY-MM-DD または null"}}]
        }}
        """.strip()

            return f"""
        あなたは日本の戸籍解読のエキスパートAIです。
        提示された戸籍謄本・除籍謄本・改製原戸籍・住民票（複数ページの場合あり）を読み取り、人物情報を統合してJSONで抽出してください。

        {forbid}

        【読取精度向上のためのヒント】
        {name_hint_str}
        ※「旧字体」や「変体仮名」が含まれる場合がありますが、現代の常用漢字・現代仮名遣いに直して出力してください。

        ### 抽出ルール
        1. **筆頭者との混同注意**: 戸籍の冒頭にある「筆頭者」ではなく、氏名欄がターゲット人物となっていいる箇所の情報を「対象者(target_person)」として抽出してください。
        2. **全関係者の抽出 (family_list)**:
           - 対象者だけでなく、記載されている**すべて**の人物（配偶者、子、父母、養子、兄弟姉妹、孫、同居人など）を抽出してください。
           - 「除籍」されている人物も抽出してください。
           - 身分事項欄などから、それぞれの「続柄（長男、妻、養女など）」を特定してください。
           - family_list は人物ごとに1要素とし、同一人物が複数回出てくる場合は統合して構いません。
           - family_list が空にならないよう、判読できる氏名がある限り全て列挙してください。

        ### 出力JSONスキーマ（このキーのみ）
        {{
          "doc_type": "現在戸籍|除籍謄本|改製原戸籍|住民票|不明",
          "honseki": "本籍地（不明なら空文字）",
          "head_name": "筆頭者氏名（不明なら空文字）",
          "target_person": "対象者氏名（不明なら空文字）",
          "valid_from": "YYYY-MM-DD（不明なら空文字）",
          "valid_to": "YYYY-MM-DD（不明なら空文字）",
          "target_birth_date": "YYYY-MM-DD（不明なら空文字）",
          "target_death_date": "YYYY-MM-DD または null",
          "family_list": [{{"name":"氏名","rel":"続柄","birth_date":"YYYY-MM-DD","death_date":"YYYY-MM-DD または null"}}]
        }}
        """.strip()

        prompt = _build_prompt("full")

        content_list = [{"type": "text", "text": prompt}] + image_contents
        msg = HumanMessage(content=content_list)

        try:
            timeout_sec = 360

            resp = self._invoke_llm_with_timeout([msg], timeout_sec=timeout_sec)
            parsed = self._extract_json_safe(getattr(resp, "content", ""))
            if "error" not in parsed:
                return parsed

            time.sleep(0.5)
            retry_prompt = _build_prompt("lite")
            retry_content_list = [{"type": "text", "text": retry_prompt}] + image_contents
            retry_msg = HumanMessage(content=retry_content_list)
            resp2 = self._invoke_llm_with_timeout([retry_msg], timeout_sec=timeout_sec)
            parsed2 = self._extract_json_safe(getattr(resp2, "content", ""))
            if "error" not in parsed2:
                return parsed2

            if len(image_contents) > 1:
                merged: Dict[str, Any] = {
                    "doc_type": "",
                    "honseki": "",
                    "head_name": "",
                    "target_person": "",
                    "valid_from": "",
                    "valid_to": "",
                    "target_birth_date": "",
                    "target_death_date": None,
                    "family_list": [],
                }
                seen: set[str] = set()

                for img_item in image_contents:
                    page_content_list = [{"type": "text", "text": retry_prompt}, img_item]
                    page_msg = HumanMessage(content=page_content_list)
                    page_resp = self._invoke_llm_with_timeout([page_msg], timeout_sec=timeout_sec)
                    page_parsed = self._extract_json_safe(getattr(page_resp, "content", ""))
                    if "error" in page_parsed:
                        continue

                    for k in [
                        "doc_type",
                        "honseki",
                        "head_name",
                        "target_person",
                        "valid_from",
                        "valid_to",
                        "target_birth_date",
                    ]:
                        if not merged.get(k) and page_parsed.get(k):
                            merged[k] = page_parsed.get(k)

                    if merged.get("target_death_date") in (None, "") and page_parsed.get("target_death_date") not in (None, ""):
                        merged["target_death_date"] = page_parsed.get("target_death_date")

                    for member in page_parsed.get("family_list", []) or []:
                        if not isinstance(member, dict):
                            continue
                        raw_name = str(member.get("name", ""))
                        key = self._normalize_name(raw_name)
                        if not key or key in seen:
                            continue
                        seen.add(key)
                        merged["family_list"].append(member)

                if merged.get("family_list"):
                    return merged

            return {"error": parsed.get("error") or parsed2.get("error") or "JSON解析失敗"}
        except Exception as e:
            logger.error(f"Koseki Analysis Error: {e}")
            return {"error": str(e)}

    def register_koseki_record(self, case_id: int, target_id: int, target_type: str, data: Dict[str, Any]) -> str:
        """解析結果をDBに保存し、対象者情報および全家族情報を自動登録する"""
        session = self.db._get_session()
        try:
            start_date = parse_all_flexible_date(data.get("valid_from"))
            end_date = parse_all_flexible_date(data.get("valid_to"))

            # 1. 戸籍履歴テーブル(FamilyRegister)への登録
            new_rec = FamilyRegister(
                case_id=case_id,
                doc_type=data.get("doc_type"),
                issuing_authority=data.get("honseki"),
                head_of_family=data.get("head_name"),
                valid_from=start_date,
                valid_to=end_date
            )
            
            if target_type == "deceased":
                new_rec.deceased_id = target_id
            else:
                new_rec.heir_id = target_id
            
            session.add(new_rec)

            updated_items = []
            person = None
            parent_deceased_id = None
            
            # 2. 対象者本人の情報更新（生年月日・死亡日など）
            if target_type == "deceased":
                person = session.query(Deceased).get(target_id)
                parent_deceased_id = target_id
            else:
                person = session.query(Heir).get(target_id)
                if person:
                    parent_deceased_id = person.deceased_id

            if person:
                if not person.date_of_birth:
                    b_date = parse_all_flexible_date(data.get("target_birth_date"))
                    if b_date:
                        person.date_of_birth = b_date
                        updated_items.append("生年月日")
                
                if target_type == "deceased" and not person.date_of_death:
                    d_date = parse_all_flexible_date(data.get("target_death_date"))
                    if d_date:
                        person.date_of_death = d_date
                        updated_items.append("死亡日")
                
                if hasattr(person, "hometown") and not person.hometown:
                    honseki = data.get("honseki")
                    if honseki:
                        person.hometown = honseki
                        updated_items.append("本籍地")

            # 3. 家族リスト(family_list)の取り込み -> Heirテーブルへ追加
            family_list = data.get("family_list", [])
            if parent_deceased_id and family_list:
                existing_heirs = session.query(Heir).filter(Heir.deceased_id == parent_deceased_id).all()
                existing_names = set()
                
                # 既存チェック（名寄せ）
                for h in existing_heirs:
                    full = f"{h.name_last}{h.name_first}".replace(" ", "").replace("　", "")
                    existing_names.add(full)
                
                # 被相続人本人も除外リストに追加
                deceased_obj = session.query(Deceased).get(parent_deceased_id)
                if deceased_obj:
                    d_full = f"{deceased_obj.name_last}{deceased_obj.name_first}".replace(" ", "").replace("　", "")
                    existing_names.add(d_full)

                added_count = 0
                for member in family_list:
                    raw_name = member.get("name", "")
                    clean_name = raw_name.replace(" ", "").replace("　", "")
                    if not clean_name or clean_name in existing_names: continue

                    # 氏名の分割 (全角スペース前提)
                    parts = raw_name.replace("　", " ").split(" ", 1)
                    lname = parts[0]
                    fname = parts[1] if len(parts) > 1 else ""
                    
                    b_date = parse_all_flexible_date(member.get("birth_date"))
                    d_date = parse_all_flexible_date(member.get("death_date"))
                    
                    new_heir = Heir(
                        deceased_id=parent_deceased_id,
                        name_last=lname,
                        name_first=fname,
                        relationship_type=member.get("rel", "関係者"),
                        date_of_birth=b_date,
                        date_of_death=d_date,
                        is_contracting_party=False
                    )
                    session.add(new_heir)
                    existing_names.add(clean_name)
                    added_count += 1
                
                if added_count > 0:
                    updated_items.append(f"関係者{added_count}名をリストに追加")

            session.commit()
            msg = "戸籍情報を登録しました。"
            if updated_items:
                msg += f"\n✨ 自動更新: {'・'.join(updated_items)}"
            return f"Success: {msg}"

        except Exception as e:
            session.rollback()
            logger.error(f"DB Save Error: {e}")
            return f"Error: {str(e)}"
        finally:
            session.close()

    def check_continuity_gaps(self, deceased_id: int) -> Tuple[List[Dict], List[str]]:
        """
        【相続用】連続性チェック
        被相続人の出生〜死亡までの戸籍期間に「空白」がないかチェックする。
        """
        session = self.db._get_session()
        try:
            person = session.query(Deceased).get(deceased_id)
            if not person or not person.date_of_birth or not person.date_of_death:
                return [], ["被相続人の「生年月日」と「死亡日」が必要です。（基本情報を登録してください）"]

            birth_date = person.date_of_birth
            death_date = person.date_of_death

            records = session.query(FamilyRegister).filter(
                FamilyRegister.deceased_id == deceased_id
            ).order_by(asc(FamilyRegister.valid_from)).all()

            if not records:
                return [], ["戸籍が登録されていません。"]

            gaps = []
            intervals = []
            
            # 有効な期間を持つレコードのみ抽出
            for r in records:
                if r.valid_from and r.valid_to:
                    intervals.append((r.valid_from, r.valid_to))
            
            # 開始日でソート
            intervals.sort(key=lambda x: x[0])

            # A. 出生時の不足チェック
            if intervals and intervals[0][0] > birth_date:
                gaps.append({
                    "start": birth_date,
                    "end": intervals[0][0],
                    "reason": "出生時の戸籍不足"
                })
            
            # B. 中間の不足チェック
            # ロジック: 前の終了日と次の開始日が連続しているか？
            merged_end = intervals[0][1] if intervals else birth_date
            
            for i in range(len(intervals) - 1):
                this_end = intervals[i][1]
                next_start = intervals[i+1][0]
                
                # 1日以上のギャップがあれば不足とみなす
                if next_start > this_end + datetime.timedelta(days=1):
                    gaps.append({
                        "start": this_end,
                        "end": next_start,
                        "reason": "連続性の欠如 (転籍・改製など)"
                    })
                
                # 終了日を更新（重複期間を考慮して最大を取る）
                if intervals[i+1][1] > merged_end:
                    merged_end = intervals[i+1][1]

            # C. 死亡時の不足チェック
            if merged_end < death_date:
                gaps.append({
                    "start": merged_end,
                    "end": death_date,
                    "reason": "死亡時の戸籍不足"
                })

            advice = []
            if not gaps:
                advice.append("✅ 出生から死亡まで連続しています。")
            else:
                for g in gaps:
                    s_str = g['start'].strftime('%Y/%m/%d')
                    e_str = g['end'].strftime('%Y/%m/%d')
                    advice.append(f"⚠️ {s_str} 〜 {e_str} の期間が不足しています。")

            return gaps, advice

        except Exception as e:
            return [], [f"エラー: {e}"]
        finally:
            session.close()

    def recommend_missing_koseki_action(self, deceased_id: int, gaps: List[Dict]) -> str:
        """
        不足期間（ギャップ）と登録済み戸籍情報に基づき、
        AIが「次にどこの役所に何を請求すべきか」をアドバイスする。
        """
        if not gaps:
            return "不足期間はありません。すべて揃っています。"

        session = self.db._get_session()
        try:
            # 登録済みの戸籍情報をテキスト化
            records = session.query(FamilyRegister).filter(
                FamilyRegister.deceased_id == deceased_id
            ).order_by(asc(FamilyRegister.valid_from)).all()
            
            records_text = ""
            for r in records:
                s = r.valid_from.strftime('%Y-%m-%d') if r.valid_from else "?"
                e = r.valid_to.strftime('%Y-%m-%d') if r.valid_to else "?"
                records_text += f"- {r.doc_type}: {s}〜{e} (本籍: {r.issuing_authority}, 筆頭者: {r.head_of_family})\n"

            # ギャップ情報テキスト化
            gaps_text = ""
            for g in gaps:
                s = g['start'].strftime('%Y-%m-%d')
                e = g['end'].strftime('%Y-%m-%d')
                gaps_text += f"- 不足期間: {s}〜{e} ({g['reason']})\n"

            # プロンプト作成
            system_prompt = """
            あなたは相続業務専門の行政書士です。
            現在、被相続人の「出生から死亡まで」の戸籍を収集中ですが、一部に不足（空白期間）があります。
            これまでの取得状況と不足期間に基づき、担当者が「次にどのアクションを取るべきか」を具体的にアドバイスしてください。

            【判断ロジック】
            - **出生時の不足**: 最初の戸籍よりさらに前の「改製原戸籍」や「除籍謄本」が必要です。「従前戸籍」欄を確認するよう促してください。
            - **中間の不足**: 転籍や改製によって途切れている可能性があります。「転籍日」や「改製日」を確認し、転籍前の本籍地へ請求するよう促してください。
            - **死亡時の不足**: 死亡の記載がある戸籍（除籍謄本）が必要です。

            【出力フォーマット】
            結論（次に請求すべき役所・書類）を具体的に、箇条書きで答えてください。
            推測が含まれる場合は「〜の可能性があります」と添えてください。
            """

            user_prompt = f"""
            【現在の取得済み戸籍】
            {records_text}

            【不足している期間】
            {gaps_text}

            担当者への次の一手アドバイスをお願いします。
            """

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({})

        except Exception as e:
            return f"アドバイス生成エラー: {e}"
        finally:
            session.close()