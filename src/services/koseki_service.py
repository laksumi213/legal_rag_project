# src/services/koseki_service.py

import logging
import base64
import json
import re
import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
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

    def _extract_json_safe(self, content: str) -> Dict[str, Any]:
        """AIの回答からJSON部分だけを安全に切り出すヘルパー関数"""
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match:
                candidate = match.group(1)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
            return json.loads(content)
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

        prompt = f"""
        あなたは日本の戸籍解読のエキスパートAIです。
        提示された戸籍謄本・除籍謄本・改製原戸籍・住民票（複数ページの場合あり）を読み取り、情報を統合してJSONで抽出してください。

        【読取精度向上のためのヒント】
        {name_hint_str}
        ※上記の名字や人物名が含まれている可能性が高いです。
        ※「旧字体」や「変体仮名」が含まれる場合がありますが、現代の常用漢字・現代仮名遣いに直して出力してください。

        ### 抽出ルール
        1. **筆頭者との混同注意**: 戸籍の冒頭にある「筆頭者」ではなく、氏名欄がターゲット人物となっている箇所の情報を「対象者(target_person)」として抽出してください。
        2. **全関係者の抽出 (family_list)**: 
           - 対象者だけでなく、記載されている**すべて**の人物（配偶者、子、父母、養子、兄弟姉妹、孫、同居人など）を抽出してください。
           - 「除籍」されている人物も抽出してください。
           - 身分事項欄などから、それぞれの「続柄（長男、妻、養女など）」を特定してください。

        ### 抽出項目 (JSON keys)
        1. **doc_type**: "現在戸籍", "除籍謄本", "改製原戸籍", "住民票" のいずれか。
        2. **honseki**: 本籍地。
        3. **head_name**: 筆頭者の氏名。
        4. **target_person**: 対象者の氏名。
        5. **valid_from**: 編製日または入籍日 (YYYY-MM-DD)。
        6. **valid_to**: 除籍日、または現在戸籍の場合は「発行日」 (YYYY-MM-DD)。
        7. **target_birth_date**: 対象者本人の生年月日 (YYYY-MM-DD)。
        8. **target_death_date**: 対象者の死亡日 (YYYY-MM-DD)。生存ならnull。
        9. **family_list**: [{{ "name": "氏名", "rel": "続柄", "birth_date": "YYYY-MM-DD", "death_date": "YYYY-MM-DD" }}, ...]

        ### 出力形式
        JSONのみ出力してください。
        """

        content_list = [{"type": "text", "text": prompt}] + image_contents
        msg = HumanMessage(content=content_list)

        try:
            resp = self.llm.invoke([msg])
            return self._extract_json_safe(resp.content)
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