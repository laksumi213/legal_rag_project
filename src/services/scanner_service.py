# src/services/scanner_service.py

import os
import time
import shutil
import logging
import datetime
import json
import base64
import uuid
import hashlib
import unicodedata
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage
from sqlalchemy.orm import joinedload 
from sqlalchemy import or_, func

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.config import Config
from legal_system.models.tables import (
    Case, FinancialAsset, BankMaster, BranchMaster, AccountTypeMaster,
    ContactLog, IncomingNoteBuffer, Liability, Deceased, FileRegistry, Heir
)
from services.deceased_service import find_cases_by_attributes, search_zip_by_address_api, search_address_by_zip_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ヘルパー関数群
BASE_DIR = Path(__file__).resolve().parents[2]
ZENGIN_DATA_DIR = BASE_DIR / "data" / "zengin"

def normalize_name(text: str) -> str:
    if not text: return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace(" ", "").replace("　", "")
    return normalized.replace("銀行", "").replace("支店", "")

def find_bank_in_zengin(search_name: str):
    banks_path = ZENGIN_DATA_DIR / "banks.json"
    if not banks_path.exists(): return None, None
    search_key = normalize_name(search_name)
    try:
        with open(banks_path, "r", encoding="utf-8") as f:
            banks = json.load(f)
        for code, info in banks.items():
            if search_key == normalize_name(info["name"]): return code, info["name"]
        for code, info in banks.items():
            if search_key in normalize_name(info["name"]): return code, info["name"]
    except: pass
    return None, None

def find_branch_in_zengin(bank_code: str, branch_search_name: str):
    if not bank_code or not branch_search_name: return None, None
    branch_path = ZENGIN_DATA_DIR / "branches" / f"{bank_code}.json"
    if not branch_path.exists(): return None, None
    search_key = normalize_name(branch_search_name)
    try:
        with open(branch_path, "r", encoding="utf-8") as f:
            branches = json.load(f)
        for code, info in branches.items():
            if search_key == normalize_name(info["name"]): return code, info["name"]
        for code, info in branches.items():
            if search_key in normalize_name(info["name"]): return code, info["name"]
    except: pass
    return None, None

def katakana_to_hiragana(text: str) -> str:
    if not text: return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6: result += chr(code - 0x60)
        else: result += char
    return result

# ---------------------------------------------------------
# ハンドラー定義
# ---------------------------------------------------------
class DocumentHandler(ABC):
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    @abstractmethod
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        pass

    def _generate_filename(self, case: Case, doc_name: str, identifier: str = "") -> str:
        g_number = case.case_number or "G不明"
        client_full = case.client_name or "不明"
        client_last = client_full.replace("　", " ").split(" ")[0]
        today_str = datetime.datetime.now().strftime('%Y%m%d')
        id_part = f"_{identifier}" if identifier else ""
        return f"{g_number}{client_last}様_{doc_name}{id_part}_{today_str}.pdf"

    def _find_target_folder(self, root_path: str, parent_keyword: str, target_keyword: str = None) -> Optional[Path]:
        if not root_path: return None
        root = Path(root_path)
        if not root.exists(): return None
        parent_dir = None
        for item in root.iterdir():
            if item.is_dir() and parent_keyword in item.name:
                parent_dir = item
                break
        if not parent_dir:
            try:
                parent_dir = root / f"00_{parent_keyword}"
                parent_dir.mkdir(exist_ok=True)
            except: return None
        if not target_keyword: return parent_dir
        target_dir = None
        for item in parent_dir.iterdir():
            if item.is_dir() and target_keyword in item.name:
                target_dir = item
                break
        if not target_dir:
            try:
                target_dir = parent_dir / f"00_{target_keyword}"
                target_dir.mkdir(exist_ok=True)
            except: return None
        return target_dir

    def _save_file_copy(self, src: Path, dest_dir: Path, filename: str):
        dest_path = dest_dir / filename
        if dest_path.exists():
            base = dest_path.stem; ext = dest_path.suffix; counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{base}_{counter}{ext}"
                counter += 1
        try:
            if not src.exists():
                logger.error(f"   ❌ Source file missing: {src}")
                return None
            
            shutil.copy2(str(src), str(dest_path))
            logger.info(f"   ✅ [File Copied] {dest_path}")
            return dest_path

        except Exception as e:
            logger.error(f"   ❌ [File Copy Error] {e}")
            return None

    def _update_or_create_registry(self, session, case_id: int, file_path: Path, doc_type: str, analysis_data: dict, file_hash: str = None, status: str = "CONFIRMED"):
        try:
            if not file_path or not file_path.exists():
                return
            if not file_hash:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                file_hash = hashlib.md5(file_bytes).hexdigest()
            
            extracted_json = json.dumps(analysis_data, ensure_ascii=False) if analysis_data else None
            
            existing = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            if existing:
                existing.case_id = case_id
                existing.filename = file_path.name
                existing.file_path = str(file_path)
                existing.doc_type = doc_type
                existing.status = status
                if extracted_json: existing.extracted_data = extracted_json
                existing.registered_at = datetime.datetime.now()
                logger.info(f"   🔄 FileRegistry更新(移動反映): {file_path.name}")
            else:
                new_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=file_path.name,
                    case_id=case_id,
                    doc_type=doc_type,
                    file_path=str(file_path),
                    registered_at=datetime.datetime.now(),
                    status=status,
                    extracted_data=extracted_json
                )
                session.add(new_reg)
                logger.info(f"   💾 FileRegistry新規登録: {file_path.name}")

        except Exception as e:
            logger.error(f"   ⚠️ FileRegistry登録エラー: {e}")

# =========================================================
# ハンドラー実装
# =========================================================

class TaxPaymentNoticeHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"💴 固定資産税・ハンドラー起動")
        new_filename = self._generate_filename(case, "固定資産税納税通知書")
        dest_dir = self._find_target_folder(case.folder_path, "受領資料")
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "固定資産税納税通知書", analysis_data, file_hash, status="CONFIRMED")
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】固定資産税納税通知書を保存しました: {saved_path.name}")
                session.add(log)
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

class BankPassbookHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        meta = analysis_data.get("meta", {})
        branch_name = meta.get("branch_name", "")
        acc_type_name = meta.get("account_type", "普通") 
        acc_number = meta.get("account_number", "")
        
        logger.info(f"📘 通帳ハンドラー起動: {bank_name} {branch_name}")

        new_filename = self._generate_filename(case, "通帳コピー", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "受領資料")
        
        if dest_dir: 
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "通帳", analysis_data, file_hash, status="CONFIRMED")
                session.add(ContactLog(case_id=case.case_id, contact_content=f"【自動処理】通帳コピーを保存しました: {saved_path.name}"))
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

        if bank_name: 
            self._register_passbook_asset(session, case.case_id, bank_name, branch_name, acc_type_name, acc_number)

    def _register_passbook_asset(self, session, case_id, bank_name, branch_name, acc_type_name, acc_number):
        try:
            z_bank_code, z_bank_name = find_bank_in_zengin(bank_name)
            
            if z_bank_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_bank_code).first()
            else:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == bank_name).first()
            
            if not bank:
                use_code = z_bank_code if z_bank_code else f"TMP-{uuid.uuid4().hex[:6]}"
                use_name = z_bank_name if z_bank_name else bank_name
                bank = BankMaster(bank_name=use_name, bank_code=use_code)
                session.add(bank)
                session.flush()

            branch = None
            if branch_name:
                z_br_code, z_br_name = (None, None)
                if not bank.bank_code.startswith("TMP"):
                    z_br_code, z_br_name = find_branch_in_zengin(bank.bank_code, branch_name)
                
                if z_br_code:
                    branch = session.query(BranchMaster).filter(BranchMaster.bank_id == bank.id, BranchMaster.branch_code == z_br_code).first()
                else:
                    branch = session.query(BranchMaster).filter(BranchMaster.bank_id == bank.id, BranchMaster.branch_name == branch_name).first()
                
                if not branch:
                    use_br_code = z_br_code if z_br_code else f"B-{uuid.uuid4().hex[:3]}"
                    use_br_name = z_br_name if z_br_name else branch_name
                    branch = BranchMaster(bank_id=bank.id, branch_name=use_br_name, branch_code=use_br_code)
                    session.add(branch)
                    session.flush()

            ac_type = session.query(AccountTypeMaster).filter(AccountTypeMaster.type_name.like(f"%{acc_type_name}%")).first()
            if not ac_type:
                ac_type = AccountTypeMaster(type_name=acc_type_name)
                session.add(ac_type)
                session.flush()

            search_num = acc_number if acc_number else "AI読取"
            
            existing = session.query(FinancialAsset).filter(
                FinancialAsset.case_id == case_id, 
                FinancialAsset.bank_id == bank.id, 
                FinancialAsset.account_number == search_num
            ).first()

            if existing:
                existing.status = "通帳確認済"
                if not existing.branch_id and branch: 
                    existing.branch_id = branch.id
                logger.info(f"   💰 資産更新: {bank.bank_name}")
            else:
                new_asset = FinancialAsset(
                    case_id=case_id, 
                    bank_id=bank.id, 
                    branch_id=branch.id if branch else None, 
                    account_type_id=ac_type.id, 
                    account_number=search_num, 
                    balance=0, 
                    status="通帳確認", 
                    asset_type="BANK"
                )
                session.add(new_asset)
                logger.info(f"   💰 資産新規登録: {bank.bank_name}")

        except Exception as e:
            logger.error(f"通帳DB登録失敗: {e}")

class BalanceCertificateHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        logger.info(f"🏦 残高証明書ハンドラー起動: {bank_name}")
        new_filename = self._generate_filename(case, "残高証明書", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "残高証明書")
        
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】{bank_name}の残高証明書を保存・登録しました: {saved_path.name}")
                session.add(log)
                self._update_or_create_registry(session, case.case_id, saved_path, "残高証明書", analysis_data, file_hash, status="CONFIRMED")
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

        balance = analysis_data.get("meta", {}).get("balance", 0)
        if balance: self._upsert_asset(session, case.case_id, bank_name, balance)

    def _upsert_asset(self, session, case_id, bank_name, balance):
        try:
            z_code, z_name = find_bank_in_zengin(bank_name)
            if z_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_code).first()
            else:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == bank_name).first()

            if not bank:
                use_code = z_code if z_code else f"TMP-{uuid.uuid4().hex[:6]}"
                use_name = z_name if z_name else bank_name
                bank = BankMaster(bank_name=use_name, bank_code=use_code)
                session.add(bank); session.flush()

            existing = session.query(FinancialAsset).filter_by(case_id=case_id, bank_id=bank.id).first()
            if existing:
                existing.balance = balance
                existing.status = "残高証明書確認済"
            else:
                new_asset = FinancialAsset(case_id=case_id, bank_id=bank.id, account_number="AI読取", balance=balance, status="残高証明書確認済")
                session.add(new_asset)
        except Exception as e:
            logger.error(f"   ❌ 資産登録エラー: {e}")

class TransactionDetailHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        new_filename = self._generate_filename(case, "取引明細書", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "取引履歴")
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "取引明細書", analysis_data, file_hash)
                session.add(ContactLog(case_id=case.case_id, contact_content=f"【自動処理】取引明細書を保存しました: {saved_path.name}"))

class InvoiceHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        meta = analysis_data.get("meta", {})
        sender = meta.get("sender_name", "不明な請求元")
        amount = meta.get("amount", 0)
        due_date = meta.get("due_date", "")
        identifier = sender.replace(" ", "").replace("　", "")
        new_filename = self._generate_filename(case, "請求書", identifier)
        dest_dir = self._find_target_folder(case.folder_path, "受領資料", "請求書")
        
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "請求書", analysis_data, file_hash)
                msg = f"【自動処理】請求書を保存しました。\n請求元: {sender}\n金額: {amount:,}円\n保存先: {saved_path.name}"
                session.add(ContactLog(case_id=case.case_id, contact_content=msg))
        
        existing_debt = session.query(Liability).filter(Liability.case_id == case.case_id, Liability.description.like(f"%{sender}%"), Liability.amount == amount).first()
        if not existing_debt:
            new_liability = Liability(case_id=case.case_id, is_debt=True, description=f"【請求書】{sender} (期限: {due_date})", amount=amount, is_funeral_cost=False)
            session.add(new_liability)

class RegistryDocumentHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        final_filename = original_path.name
        dest_dir = self._find_target_folder(case.folder_path, "取得代行資料")
        saved_path = self._save_file_copy(original_path, dest_dir, final_filename) if dest_dir else None
        if saved_path:
            self._update_or_create_registry(session, case.case_id, saved_path, "不動産登記情報", analysis_data, file_hash)
            msg = f"【自動処理】不動産登記情報を保存しました。\n保存先: 取得代行資料/{saved_path.name}\n※Home画面の「不動産登録」から登録してください。"
            session.add(ContactLog(case_id=case.case_id, contact_content=msg))

class OtherDocumentHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        doc_type = analysis_data.get("doc_type", "書類")
        final_filename = self._generate_filename(case, doc_type)
        dest_dir = self._find_target_folder(case.folder_path, "受領資料")
        saved_path = self._save_file_copy(original_path, dest_dir, final_filename) if dest_dir else None
        if saved_path:
            self._update_or_create_registry(session, case.case_id, saved_path, doc_type, analysis_data, file_hash)
            msg = f"【自動処理】{doc_type}を保存しました。\n保存先: 受領資料/{saved_path.name}"
            session.add(ContactLog(case_id=case.case_id, contact_content=msg))

class HeirListHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"👨‍👩‍👧‍👦 相続人リスト・ハンドラー起動")
        new_filename = self._generate_filename(case, "推定相続人連絡先一覧")
        dest_dir = self._find_target_folder(case.folder_path, "受領資料")
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "推定相続人連絡先一覧", analysis_data, file_hash, status="CONFIRMED")
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】推定相続人連絡先一覧を保存しました: {saved_path.name}")
                session.add(log)

# ---------------------------------------------------------
# メインサービスクラス
# ---------------------------------------------------------
class ScannerService:
    def __init__(self, inbox_path: str = None, processed_root: str = None):
        self.inbox_path = Path(inbox_path) if inbox_path else Path(os.path.join(os.path.expanduser("~"), "Downloads"))
        if processed_root: self.processed_root = Path(processed_root)
        else: self.processed_root = Config.DATA_DIR / "cases"
        self.db = DatabaseManager()
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        self.handlers = {
            "balance_certificate": BalanceCertificateHandler(self.db),
            "transaction_detail": TransactionDetailHandler(self.db),
            "bank_passbook": BankPassbookHandler(self.db),
            "invoice": InvoiceHandler(self.db),
            "registry_document": RegistryDocumentHandler(self.db),
            "heir_list": HeirListHandler(self.db),
            "tax_payment_notice": TaxPaymentNoticeHandler(self.db), # ★追加
            "other": OtherDocumentHandler(self.db)
        }

    def process_file(self, file_path: str):
        path = Path(file_path)
        logger.info(f"🚀 [Scanner] 処理開始: {path.name}")
        time.sleep(1.0)
        try:
            if not path.exists():
                logger.error(f"   ❌ ファイル消失: {path}")
                return
            with open(path, "rb") as f: file_bytes = f.read()
            
            logger.info("   🤖 AI解析を実行中...")
            analysis = self._analyze_document(file_bytes)
            candidates = analysis.get("case_candidates", [])
            doc_type = analysis.get('doc_type', 'unknown')
            
            logger.info(f"   📋 解析完了: {doc_type}")
            logger.info(f"   💡 候補案件: {len(candidates)} 件")
            
            session = self.db._get_session()
            try:
                temp_storage = Config.DATA_DIR / "uploads" / "pending"
                temp_storage.mkdir(parents=True, exist_ok=True)
                saved_path = temp_storage / path.name
                shutil.copy2(str(path), str(saved_path))
                
                self._register_file_entry(session, candidates[0]['case_id'] if candidates else None, saved_path, doc_type, analysis, status="PENDING")
                
                session.commit()
                logger.info("   ✅ 処理完了: DB登録 (PENDING)")
                
            except Exception as e:
                session.rollback()
                logger.error(f"   ❌ DB保存エラー: {e}")
                raise e
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"   ❌ ファイル処理エラー (Top Level): {e}")

    def _register_file_entry(self, session, case_id, file_path, doc_type, analysis_data, status="PENDING"):
        if not file_path or not file_path.exists(): return
        with open(file_path, "rb") as f: file_bytes = f.read()
        f_hash = hashlib.md5(file_bytes).hexdigest()
        
        extracted_json = json.dumps(analysis_data, ensure_ascii=False) if analysis_data else None
        
        existing = session.query(FileRegistry).filter_by(file_hash=f_hash).first()
        if existing:
            existing.status = status
            existing.extracted_data = extracted_json
            existing.filename = file_path.name
            if case_id: existing.case_id = case_id
        else:
            new_reg = FileRegistry(
                file_hash=f_hash,
                filename=file_path.name,
                case_id=case_id,
                doc_type=doc_type,
                file_path=str(file_path),
                registered_at=datetime.datetime.now(),
                status=status,
                extracted_data=extracted_json
            )
            session.add(new_reg)

    def _execute_handler(self, session, case_id: int, analysis: dict, path: Path, file_hash: str):
        case = session.query(Case).options(joinedload(Case.deceased_ref)).get(case_id)
        if case:
            # ★修正: 引数で渡されたdoc_typeを優先し、ハンドラを決定する
            doc_type = analysis.get("doc_type", "other")
            handler = self.handlers.get(doc_type, self.handlers["other"])
            
            if handler: 
                logger.info(f"   🔧 ハンドラー実行: {doc_type} -> Case {case.case_number}")
                handler.handle(session, case, analysis, path, file_hash=file_hash)
        else:
            logger.error(f"Case ID {case_id} not found.")

    def process_pending_buffer(self, buffer_id: str, target_case_id: int, override_doc_type: str = None) -> bool:
        session = self.db._get_session()
        try:
            file_entry = session.query(FileRegistry).filter_by(file_hash=buffer_id).first()
            if not file_entry:
                logger.error(f"FileHash {buffer_id} not found.")
                return False
            
            logger.info(f"承認処理開始: File {file_entry.filename} -> Case ID {target_case_id}")
            
            file_path = Path(file_entry.file_path) if file_entry.file_path else None
            
            if not file_path or not file_path.exists():
                logger.error(f"❌ 実ファイルが見つかりません: {file_path}")
                return False

            analysis = {}
            if file_entry.extracted_data:
                try: analysis = json.loads(file_entry.extracted_data)
                except: pass
            
            # ★重要: UIで選択されたタイプで上書きする
            if override_doc_type:
                analysis["doc_type"] = override_doc_type

            # ハンドラー実行 (コピー移動・リネーム・ログ保存 & DBレコードのパス更新)
            self._execute_handler(session, target_case_id, analysis, file_path, file_hash=buffer_id)
            
            file_entry = session.query(FileRegistry).filter_by(file_hash=buffer_id).first() 
            if file_entry and file_entry.status != "CONFIRMED":
                file_entry.status = "CONFIRMED"
                file_entry.case_id = target_case_id
            
            session.commit()
            logger.info("✅ 承認処理成功")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"承認処理エラー: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            session.close()

    def _analyze_document(self, file_bytes: bytes) -> dict:
        mime = "application/pdf" if file_bytes.startswith(b"%PDF") else "image/jpeg"
        doc_b64 = base64.b64encode(file_bytes).decode("utf-8")
        
        prompt = """
        この書類を解析し、以下のJSON形式で出力してください。
        
        # 1. 基本情報抽出
        - **names**: 書類下部の「遺言者様に関する情報」欄（または「ご依頼者様」「契約者」欄）に記載された氏名を**最優先**で抽出。なければ被相続人名。
        - **bank_name**: 銀行名（あれば）。
        
        # 2. 書類種別 (doc_type) の判定
        - **tax_payment_notice**: 「固定資産税 納税通知書」「課税明細書」「固定資産税・都市計画税」などの記載がある場合。
        - **heir_list**: 「推定相続人連絡先一覧」「相続関係説明図」など。
        - registry_document: 不動産登記情報
        - bank_passbook: 通帳 (表紙、または明細ページ)
        - balance_certificate: 残高証明書
        - transaction_detail: 取引明細
        - invoice: 請求書・領収書
        - other: その他

        # 3. メタデータ (meta) の抽出
        
        **【A】heir_list (相続人一覧) の場合**
        - **heirs**: 配列。各要素に以下の情報を含めること。
          - name: 氏名
          - relationship: 続柄 (長男, 妻, 妹 など)
          - zip_code: 郵便番号 (〒マークや数字7桁があれば抽出)
          - address: 住所 (郵便番号は除外して、都道府県から記載すること)
          - occupation: 職業 (会社員, 無職など。記載があれば)
          - honseki: 本籍地 (「本籍」欄があれば抽出)
          - birth_date: 生年月日 (YYYY-MM-DD形式。和暦の場合は変換すること)
          - phone: 電話番号

        **【B】balance_certificate / bank_passbook (金融関連) の場合**
        - branch_name: 支店名（ゆうちょ銀行の場合は「〇〇八」などの店名、または記号・番号から変換可能なため空欄でも可だが、記載があれば抽出）
        - account_number: 口座番号。
          - 一般的な銀行: 7桁の半角数字。
          - **ゆうちょ銀行**: 「記号(5桁)」と「番号(8桁)」が記載されている場合、**「記号-番号」（例: 10120-12345678）** の形式で抽出してください。
        - balance: 残高 (数値)
        - holder_name: 名義人
        - account_type: 預金種別 (普通, 定期, 貯蓄, 当座)

        **【C】invoice (請求書) の場合**
        - sender_name, amount, due_date

        **【D】tax_payment_notice (固定資産税) の場合**
        - 資産情報の抽出は不要です。

        # 出力JSON例
        {
            "names": ["宮崎 修武"],
            "doc_type": "heir_list",
            "meta": {
                "heirs": [
                    {
                        "name": "宮崎 栄子", "relationship": "妻", 
                        "zip_code": "815-0075", "address": "福岡県福岡市南区長丘5-13-1",
                        "occupation": "無職", "honseki": "福岡県福岡市南区...", 
                        "birth_date": "1948-11-01", "phone": "090-xxxx-xxxx"
                    }
                ]
            },
            "case_candidates": [] 
        }
        """
        
        msg = HumanMessage(content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": f"data:{mime};base64,{doc_b64}"}])
        try:
            resp = self.llm.invoke([msg])
            ai_data = json.loads(resp.content.replace("```json", "").replace("```", "").strip())
        except: return {}
        
        # --- Pythonによる後処理: 欠損データの補完 ---
        if ai_data.get("doc_type") == "heir_list":
            meta = ai_data.get("meta", {})
            heirs = meta.get("heirs", [])
            for h in heirs:
                addr = h.get("address", "")
                zip_c = h.get("zip_code", "")
                
                if addr and not zip_c:
                    found_zip = search_zip_by_address_api(addr)
                    if found_zip:
                        h["zip_code"] = found_zip
                        zip_c = found_zip
                
                if zip_c and addr:
                    if not re.match(r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)', addr):
                        addr_info = search_address_by_zip_api(zip_c)
                        if addr_info:
                            pref = addr_info.get("prefecture", "")
                            if pref and not addr.startswith(pref):
                                h["address"] = f"{pref}{addr}"
        
        # 名前クレンジング & 案件検索
        names = ai_data.get("names", [])
        holder = ai_data.get("meta", {}).get("holder_name")
        if holder and holder not in names: names.append(holder)
        cleaned_names = [n.replace("様", "").replace("殿", "").strip() for n in names]

        candidates = []
        if cleaned_names:
            session = self.db._get_session()
            try:
                for name in cleaned_names:
                    hits = find_cases_by_attributes(client_name=name) or find_cases_by_attributes(deceased_name=name)
                    if hits: candidates.extend(hits)
            finally: session.close()
            
        unique_candidates = {c['case_id']: c for c in candidates}.values()
        final_candidates_list = []
        for c in unique_candidates:
            new_c = c.copy()
            for k, v in new_c.items():
                if isinstance(v, (datetime.date, datetime.datetime)):
                    new_c[k] = v.strftime('%Y-%m-%d')
            final_candidates_list.append(new_c)

        ai_data["case_candidates"] = final_candidates_list
        ai_data["names"] = cleaned_names
        return ai_data