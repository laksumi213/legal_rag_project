# src/services/scanner_service.py

import os
import time
import shutil
import logging
import datetime
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage
from sqlalchemy.orm import joinedload  # 追加

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, FinancialAsset, BankMaster, Deceased, Heir, Address, H_AddressHistory, Contact, H_ContactLink
from legal_system.core.schemas import HeirListAnalysisResult # 追加
from services.deceased_service import find_cases_by_attributes

logger = logging.getLogger(__name__)

# ==========================================
# 1. ハンドラー基底クラス (共通ロジック)
# ==========================================
class DocumentHandler(ABC):
    """すべての書類ハンドラーの基底クラス"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        # ハンドラー内でもAIを使えるようにしておく
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    @abstractmethod
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        """
        具体的な処理（移動、DB登録など）を実装する抽象メソッド
        """
        pass

    # --- 共通ヘルパーメソッド ---
    
    def _generate_filename(self, case: Case, doc_name: str, identifier: str = "") -> str:
        """
        ファイル名生成ルール:
        {G番号}{契約者苗字}様_{書類名}{識別子}_{YYYYMMDD}.pdf
        """
        g_number = case.case_number or "G不明"
        
        # 契約者名から苗字を抽出 (スペース区切りを想定)
        client_full = case.client_name or "不明"
        client_last = client_full.replace("　", " ").split(" ")[0]
        
        today_str = datetime.datetime.now().strftime('%Y%m%d')
        
        id_part = identifier if identifier else ""
        
        return f"{g_number}{client_last}様_{doc_name}{id_part}_{today_str}.pdf"

    def _find_target_folder(self, root_path: str, parent_keyword: str, target_keyword: str) -> Optional[Path]:
        """
        案件フォルダ内で、指定キーワードを含むフォルダ階層を探索して返す。
        """
        if not root_path: return None
        root = Path(root_path)
        if not root.exists(): return None

        # 1. 第1階層
        parent_dir = None
        for item in root.iterdir():
            if item.is_dir() and parent_keyword in item.name:
                parent_dir = item
                break
        
        if not parent_dir:
            logger.info(f"   📂 フォルダ '{parent_keyword}' がないため作成します")
            try:
                parent_dir = root / f"00_{parent_keyword}"
                parent_dir.mkdir(exist_ok=True)
            except Exception as e:
                logger.error(f"   ❌ フォルダ作成エラー: {e}")
                return None

        # 2. 第2階層
        target_dir = None
        for item in parent_dir.iterdir():
            if item.is_dir() and target_keyword in item.name:
                target_dir = item
                break
        
        if not target_dir:
            logger.info(f"   📂 サブフォルダ '{target_keyword}' がないため作成します")
            try:
                target_dir = parent_dir / f"00_{target_keyword}"
                target_dir.mkdir(exist_ok=True)
            except Exception as e:
                logger.error(f"   ❌ フォルダ作成エラー: {e}")
                return None
            
        return target_dir

    def _move_file(self, src: Path, dest_dir: Path, filename: str):
        """ファイルを移動（同名ファイルがある場合は連番付与）"""
        dest_path = dest_dir / filename
        
        # 同名回避
        if dest_path.exists():
            base = dest_path.stem
            ext = dest_path.suffix
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{base}_{counter}{ext}"
                counter += 1
        
        try:
            shutil.move(str(src), str(dest_path))
            logger.info(f"   📂 移動完了: {dest_path}")
        except Exception as e:
            logger.error(f"   ❌ ファイル移動エラー: {e}")


# ==========================================
# 2. 具体的なハンドラー実装
# ==========================================

class BalanceCertificateHandler(DocumentHandler):
    """残高証明書用ハンドラー: ファイル移動 ＋ DB登録"""

    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        bank_name = analysis_data.get("bank_name", "").replace(" ", "").replace("　", "")
        if not bank_name: bank_name = "不明銀行"

        # 1. ファイル移動
        # ルール: 案件フォルダ > 取得代行資料 > 残高証明書
        new_filename = self._generate_filename(case, "残高証明書", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "取得代行資料", "残高証明書")
        
        if dest_dir:
            self._move_file(original_path, dest_dir, new_filename)
        else:
            logger.warning("   ⚠️ 移動先フォルダパスが無効なため、移動をスキップします。")

        # 2. DB登録 (FinancialAsset)
        balance = analysis_data.get("meta", {}).get("balance", 0)
        if balance:
            self._upsert_asset(session, case.case_id, bank_name, balance)

    def _upsert_asset(self, session, case_id, bank_name, balance):
        """資産データの登録・更新ロジック"""
        try:
            # 銀行マスタ検索 (部分一致)
            bank = session.query(BankMaster).filter(BankMaster.bank_name.like(f"%{bank_name}%")).first()
            bank_id = bank.id if bank else None
            
            if bank_id:
                # 既存チェック
                existing = session.query(FinancialAsset).filter_by(case_id=case_id, bank_id=bank_id).first()
                
                if existing:
                    existing.balance = balance
                    existing.status = "残高証明書確認済"
                    logger.info(f"   🔄 DB更新: {bank_name} ¥{balance}")
                else:
                    new_asset = FinancialAsset(
                        case_id=case_id,
                        bank_id=bank_id,
                        account_number="AI読取",
                        balance=balance,
                        status="残高証明書確認済"
                    )
                    session.add(new_asset)
                    logger.info(f"   🆕 DB登録: {bank_name} ¥{balance}")
            else:
                logger.warning(f"   ⚠️ 銀行マスタに '{bank_name}' が見つからないため、DB登録をスキップしました。")

            # Kintoneブックマークレット用データ生成
            try:
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                kintone_data = {
                    "bank_name": bank_name,
                    "balance": balance,
                    "date": today
                }
                json_str = json.dumps(kintone_data, ensure_ascii=False)
                logger.info("-" * 40)
                logger.info("📋 【Kintone連携】以下のデータをコピーして、ブックマークレットに貼り付けてください:")
                logger.info(json_str)
                logger.info("-" * 40)
            except Exception as e:
                logger.error(f"Bookmarklet Data Generation Error: {e}")

        except Exception as e:
            logger.error(f"   ❌ DB登録失敗: {e}")


class TransactionDetailHandler(DocumentHandler):
    """取引明細用ハンドラー: ファイル移動のみ (DB登録なし)"""

    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        bank_name = analysis_data.get("bank_name", "").replace(" ", "").replace("　", "")
        if not bank_name: bank_name = "不明銀行"

        new_filename = self._generate_filename(case, "取引明細書", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "取得代行資料", "取引履歴")
        
        if dest_dir:
            self._move_file(original_path, dest_dir, new_filename)
        else:
            logger.warning("   ⚠️ 移動先フォルダパスが無効なため、移動をスキップします。")


class HeirContactListHandler(DocumentHandler):
    """
    【新規追加】相続人連絡先一覧ハンドラー
    手書きの連絡先一覧を読み取り、DBに相続人情報を登録・更新し、ファイルを移動する。
    """

    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        logger.info("   🔍 相続人連絡先一覧の詳細解析を開始します...")
        
        # 1. 詳細AI解析 (Extraction)
        # 共通解析では抽出できていない「手書きの表データ」を専用プロンプトで読み取る
        try:
            with open(original_path, "rb") as f:
                file_bytes = f.read()
            
            # Pydanticモデルを使った構造化抽出
            heir_analysis = self._extract_heir_data(file_bytes)
            
            if not heir_analysis.heirs:
                logger.warning("   ⚠️ 相続人情報が読み取れませんでした。")
            else:
                # 2. DB登録 (Heir, Address, Contact)
                self._register_heirs(session, case, heir_analysis.heirs)
                logger.info(f"   💾 相続人 {len(heir_analysis.heirs)} 名の情報を更新しました。")

        except Exception as e:
            logger.error(f"   ❌ 詳細解析/登録エラー: {e}")
            # エラーでもファイル移動は試みる

        # 3. ファイル移動
        # ルール: 案件フォルダ > 01_基本情報(仮) > 連絡先一覧
        # フォルダ構成は実際の運用に合わせて調整してください。ここではルート直下に置く例とします。
        
        # タイムスタンプ付きでリネーム
        new_filename = f"推定相続人連絡先一覧_{case.client_name}様_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 移動先: 案件フォルダ直下、または「基本資料」フォルダなど
        dest_dir = Path(case.folder_path)
        if not dest_dir.exists():
            logger.warning(f"   ⚠️ 案件フォルダが存在しません: {case.folder_path}")
            return

        self._move_file(original_path, dest_dir, new_filename)

    def _extract_heir_data(self, file_bytes: bytes) -> HeirListAnalysisResult:
        """Gemini Visionで手書き表を解析"""
        import base64
        # PDFの場合は1ページ目を画像化（簡易実装として先頭のみ。必要なら全ページ対応）
        img_b64 = ""
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
            if images:
                from io import BytesIO
                buf = BytesIO()
                images[0].save(buf, format="JPEG")
                img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception as e:
            logger.error(f"PDF Image Convert Error: {e}")
            # 画像変換失敗時は空を返すかエラー
            raise e

        prompt = """
        この画像は「推定相続人連絡先一覧」という手書きの表です。
        以下の情報を抽出して構造化データ(JSON)にしてください。
        
        1. **書類判定**: 「推定相続人様　連絡先一覧」というタイトルがあるか確認（あれば処理続行）。
        2. **案件特定情報**: 「被相続人名」や「案件番号」があれば抽出。
        3. **相続人情報**: 表の中の手書き文字から、相続人の「氏名」「続柄」「住所」「電話番号」をリスト化してください。
           - 手書き文字のため、慎重に読み取ってください。
           - 読み取れない箇所は null にしてください。
        """

        structured_llm = self.llm.with_structured_output(HeirListAnalysisResult)
        
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
        ]
        
        msg = HumanMessage(content=content)
        return structured_llm.invoke([msg])

    def _register_heirs(self, session, case: Case, heirs_data: list):
        """相続人データのUpsert処理"""
        deceased = case.deceased_ref
        if not deceased:
            # 被相続人が未作成なら作成
            deceased = Deceased(case_id=case.case_id, name_last="", name_first="")
            session.add(deceased)
            session.flush()

        for h_info in heirs_data:
            if not h_info.name: continue
            
            # 氏名の正規化
            raw_name = h_info.name.replace("　", " ").strip()
            parts = raw_name.split(" ", 1)
            lname = parts[0]
            fname = parts[1] if len(parts) > 1 else ""
            
            # 既存チェック (氏名一致)
            # スペースを無視して比較するために replace を使うなど工夫してもよい
            existing_heir = session.query(Heir).filter(
                Heir.deceased_id == deceased.id,
                Heir.name_last == lname,
                Heir.name_first == fname
            ).first()

            target_heir = existing_heir
            
            if not target_heir:
                # 新規登録
                target_heir = Heir(
                    deceased_id=deceased.id,
                    name_last=lname,
                    name_first=fname,
                    relationship_type=h_info.relationship
                )
                session.add(target_heir)
                session.flush() # ID確定
                logger.info(f"   ➕ 相続人新規登録: {raw_name}")
            else:
                logger.info(f"   🔄 既存相続人を更新: {raw_name}")
                # 続柄が空でなければ更新
                if h_info.relationship:
                    target_heir.relationship_type = h_info.relationship

            # 住所情報の登録/更新
            if h_info.address:
                # 既存の住所リンクを確認
                addr_link = session.query(H_AddressHistory).filter_by(
                    heir_id=target_heir.id, is_current_address=True
                ).first()
                
                if addr_link:
                    # 更新: 住所マスタを書き換え（履歴管理するなら新規作成だが、今回は上書き）
                    addr = session.query(Address).get(addr_link.address_id)
                    addr.street_address = h_info.address # 分割せずstreetに入れる
                    # addr.prefecture = "" # 必要ならクリア
                else:
                    new_addr = Address(prefecture="", street_address=h_info.address)
                    session.add(new_addr)
                    session.flush()
                    session.add(H_AddressHistory(heir_id=target_heir.id, address_id=new_addr.id, is_current_address=True))

            # 電話番号の登録
            if h_info.phone:
                # 重複チェック
                exists_tel = session.query(H_ContactLink).join(Contact).filter(
                    H_ContactLink.heir_id == target_heir.id,
                    Contact.value == h_info.phone
                ).first()
                
                if not exists_tel:
                    new_con = Contact(value=h_info.phone, type="PHONE", sub_type="Scanner")
                    session.add(new_con)
                    session.flush()
                    session.add(H_ContactLink(heir_id=target_heir.id, contact_id=new_con.id))


# ==========================================
# 3. ScannerService (メインサービス)
# ==========================================

class ScannerService:
    def __init__(self, inbox_path: str, processed_root: str):
        self.inbox_path = Path(inbox_path)
        self.processed_root = Path(processed_root)
        self.db = DatabaseManager()
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        
        # ハンドラーの登録
        self.handlers: Dict[str, DocumentHandler] = {
            "balance_certificate": BalanceCertificateHandler(self.db),
            "transaction_detail": TransactionDetailHandler(self.db),
            "heir_contact_list": HeirContactListHandler(self.db), # ★追加
        }

    def process_file(self, file_path: str):
        """スキャンファイルのメイン処理フロー"""
        path = Path(file_path)
        
        # 1. ファイル書き込み完了待ち
        time.sleep(2) 
        
        logger.info(f"🖨️ スキャン検知: {path.name}")
        
        try:
            # 2. AIによる解析 (Gemini 2.0 Flash)
            with open(path, "rb") as f:
                file_bytes = f.read()
            
            analysis = self._analyze_document(file_bytes)
            logger.info(f"   🧠 AI解析結果: {analysis}")

            if not analysis.get("case_candidates"):
                logger.warning("   ⚠️ 案件を特定できませんでした（移動せず残します）。")
                return

            # 3. 案件の確定 (確度が高いものを採用)
            target_case_id = analysis["case_candidates"][0]["case_id"]
            doc_type = analysis.get("doc_type", "other")
            
            # 4. ハンドラーへの委譲
            session = self.db._get_session()
            try:
                case = session.query(Case).options(joinedload(Case.deceased_ref)).get(target_case_id)
                if not case:
                    logger.error(f"   ❌ 案件ID {target_case_id} がDBに見つかりません。")
                    return

                logger.info(f"   📂 ターゲット案件: {case.client_name} (G{case.case_number})")

                handler = self.handlers.get(doc_type)
                
                if handler:
                    # 登録されたハンドラーがあれば実行
                    handler.handle(session, case, analysis, path)
                    session.commit() # ハンドラー内での変更をコミット
                else:
                    # ハンドラーがない場合（その他）
                    logger.info("   ℹ️ 'その他'の書類のため、移動せずにフォルダに残します。")

            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()

        except Exception as e:
            logger.error(f"   ❌ 処理エラー: {e}")
            # エラー時も移動せず残す

    def _analyze_document(self, file_bytes: bytes) -> dict:
        """Gemini Visionで分類と案件特定情報を抽出 (共通ロジック)"""
        import base64
        # PDFの場合は先頭ページだけ画像化してトークン節約
        img_b64 = ""
        try:
            from pdf2image import convert_from_bytes
            images = convert_from_bytes(file_bytes, dpi=100, first_page=1, last_page=1)
            if images:
                from io import BytesIO
                buf = BytesIO()
                images[0].save(buf, format="JPEG")
                img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except:
            # 画像化に失敗、またはPDFでない場合はそのまま
            img_b64 = base64.b64encode(file_bytes).decode("utf-8")
        
        prompt = """
        このスキャン画像を解析し、以下の情報をJSONで抽出してください。
        
        1. **names**: 文書内の「被相続人(故人)」または「依頼者(相続人代表)」と思われる氏名リスト。
        2. **bank_name**: 金融機関名（正式名称、なければ"不明銀行"）。
        3. **doc_type**: 以下のいずれかに分類してください。
           - "heir_contact_list": 書類上部に「推定相続人様 連絡先一覧」（または類似の表題）がある場合。
           - "balance_certificate": 残高証明書
           - "transaction_detail": 取引明細・入出金明細
           - "other": その他
        4. **meta**: 
           - 残高証明書の場合: "balance" (合計金額の数値)
        """
        
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
        ])
        
        ai_data = {}
        try:
            resp = self.llm.invoke([msg])
            content = resp.content.replace("```json", "").replace("```", "").strip()
            # JSONパースのロバスト性向上
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end != 0:
                ai_data = json.loads(content[start:end])
            else:
                ai_data = {"names": [], "doc_type": "other"}
        except Exception as e:
            logger.error(f"AI解析エラー: {e}")
            return {}
        
        # DBから案件検索 (名寄せ)
        names = ai_data.get("names", [])
        candidates = []
        if names:
            for name in names:
                hits = find_cases_by_attributes(deceased_name=name)
                if not hits:
                    hits = find_cases_by_attributes(client_name=name)
                candidates.extend(hits)
        
        unique_candidates = {c['case_id']: c for c in candidates}.values()
        ai_data["case_candidates"] = list(unique_candidates)
        
        return ai_data