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
        """
        処理実行メソッド
        """
        pass

    def _generate_filename(self, case: Case, doc_name: str, identifier: str = "") -> str:
        g_number = case.case_number or "G不明"
        client_full = case.client_name or "不明"
        client_last = client_full.replace("　", " ").split(" ")[0]
        today_str = datetime.datetime.now().strftime('%Y%m%d')
        id_part = f"_{identifier}" if identifier else ""
        return f"{g_number}{client_last}様_{doc_name}{id_part}_{today_str}.pdf"

    # --- フォルダ操作ヘルパー ---
    
    def _find_folder(self, root_path: str, keyword: str) -> Optional[Path]:
        """指定したキーワードを含むフォルダを検索して返す（なければNone）"""
        if not root_path: return None
        root = Path(root_path)
        if not root.exists(): return None
        
        for item in root.iterdir():
            if item.is_dir() and keyword in item.name:
                return item
        return None

    def _ensure_folder(self, root_path: str, keyword: str, force_name: str = None) -> Optional[Path]:
        """
        指定したキーワードを含むフォルダを検索して返す。
        なければ作成して返す。
        force_nameが指定されていればその名前で作成、なければ '00_{keyword}' で作成。
        """
        if not root_path: return None
        root = Path(root_path)
        if not root.exists(): return None # ルート自体がない場合は諦める

        # 1. 検索
        found = self._find_folder(root_path, keyword)
        if found: return found
        
        # 2. 作成
        new_folder_name = force_name if force_name else f"00_{keyword}"
        new_path = root / new_folder_name
        try:
            new_path.mkdir(exist_ok=True)
            return new_path
        except Exception as e:
            logger.error(f"フォルダ作成失敗: {new_path} - {e}")
            return None

    def _find_target_folder(self, root_path: str, parent_keyword: str, target_keyword: str = None) -> Optional[Path]:
        """旧ロジック互換用（必要に応じて使用）"""
        parent_dir = self._ensure_folder(root_path, parent_keyword)
        if not parent_dir: return None
        
        if not target_keyword: return parent_dir
        
        # サブフォルダ検索・作成
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
            
            conf_score = 1.0 if status == "CONFIRMED" else 0.0

            if existing:
                existing.case_id = case_id
                existing.filename = file_path.name
                existing.file_path = str(file_path)
                existing.doc_type = doc_type
                existing.status = status
                existing.ai_confidence = conf_score
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
                    ai_confidence=conf_score,
                    extracted_data=extracted_json
                )
                session.add(new_reg)
                logger.info(f"   💾 FileRegistry新規登録: {file_path.name}")

        except Exception as e:
            logger.error(f"   ⚠️ FileRegistry登録エラー: {e}")

# =========================================================
# ハンドラー実装
# =========================================================

class CorporateRegistryHandler(DocumentHandler):
    """
    商業・法人登記簿謄本用ハンドラー
    ・「取得代行資料/商業登記」などのフォルダに保存
    """
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"🏢 商業登記・ハンドラー起動")
        meta = analysis_data.get("meta", {})
        corp_name = meta.get("corporate_name", "法人")
        
        # ファイル名: Gxxxx様_商業登記(法人名)_YYYYMMDD.pdf
        new_filename = self._generate_filename(case, "商業登記簿", corp_name)
        
        # 保存先: 「取得代行資料」の中の「商業登記」または直下
        parent_dir = self._ensure_folder(case.folder_path, "取得代行資料")
        if parent_dir:
            dest_dir = self._ensure_folder(str(parent_dir), "商業登記", force_name="商業登記")
        else:
            dest_dir = None
            
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "corporate_registry", analysis_data, file_hash, status="CONFIRMED")
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】商業登記簿({corp_name})を保存しました: {saved_path.name}")
                session.add(log)
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

class TaxPaymentNoticeHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"💴 固定資産税・ハンドラー起動")
        new_filename = self._generate_filename(case, "固定資産税納税通知書")
        dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
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
        dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
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
        
        dest_dir = self._find_folder(case.folder_path, "残高証明書")
        if not dest_dir:
            dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
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

class SecuritiesStatementHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        sec_company_name = analysis_data.get("bank_name", "不明証券").strip()
        meta = analysis_data.get("meta", {})
        branch_name = meta.get("branch_name", "")
        account_number = meta.get("account_number", "")
        total_balance = meta.get("balance", 0)
        
        logger.info(f"📈 証券ハンドラー起動: {sec_company_name} (Acc: {account_number})")

        new_filename = self._generate_filename(case, "取引残高報告書", sec_company_name)
        
        dest_dir = self._find_target_folder(case.folder_path, "受領資料", "証券")
        if not dest_dir: dest_dir = self._ensure_folder(case.folder_path, "受領資料")

        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "証券取引報告書", analysis_data, file_hash, status="CONFIRMED")
                session.add(ContactLog(case_id=case.case_id, contact_content=f"【自動処理】{sec_company_name}の報告書を保存しました: {saved_path.name}")
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

        if sec_company_name:
            self._register_securities_asset(session, case.case_id, sec_company_name, branch_name, account_number, total_balance)

    def _register_securities_asset(self, session, case_id, company_name, branch_name, account_number, balance):
        try:
            z_code, z_name = find_bank_in_zengin(company_name)
            if z_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_code).first()
            else:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == company_name).first()
            
            if not bank:
                use_code = z_code if z_code else f"SEC-{uuid.uuid4().hex[:6]}"
                use_name = z_name if z_name else company_name
                bank = BankMaster(bank_name=use_name, bank_code=use_code)
                session.add(bank)
                session.flush()

            branch = None
            if branch_name:
                branch = session.query(BranchMaster).filter(BranchMaster.bank_id == bank.id, BranchMaster.branch_name == branch_name).first()
                if not branch:
                    branch = BranchMaster(bank_id=bank.id, branch_name=branch_name, branch_code=f"B-{uuid.uuid4().hex[:3]}")
                    session.add(branch)
                    session.flush()

            search_num = account_number if account_number else "AI読取"
            existing = session.query(FinancialAsset).filter(
                FinancialAsset.case_id == case_id, 
                FinancialAsset.bank_id == bank.id, 
                FinancialAsset.account_number == search_num
            ).first()

            if existing:
                existing.balance = balance
                existing.status = "証券明細確認済"
                existing.asset_type = "SECURITY"
                if not existing.branch_id and branch: 
                    existing.branch_id = branch.id
            else:
                new_asset = FinancialAsset(
                    case_id=case_id, 
                    bank_id=bank.id, 
                    branch_id=branch.id if branch else None, 
                    account_number=search_num, 
                    balance=balance, 
                    status="証券明細確認済", 
                    asset_type="SECURITY"
                )
                session.add(new_asset)

        except Exception as e:
            logger.error(f"証券DB登録失敗: {e}")

class TransactionDetailHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        new_filename = self._generate_filename(case, "取引明細書", bank_name)
        
        dest_dir = self._find_folder(case.folder_path, "取引履歴")
        if not dest_dir:
            dest_dir = self._ensure_folder(case.folder_path, "受領資料")
            
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
        
        dest_dir = self._ensure_folder(case.folder_path, "請求書", force_name="請求書")
        
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
        
        dest_dir = self._find_folder(case.folder_path, "名寄帳")
        if not dest_dir:
            dest_dir = self._ensure_folder(case.folder_path, "不動産登記情報", force_name="不動産登記情報")

        saved_path = self._save_file_copy(original_path, dest_dir, final_filename) if dest_dir else None
        if saved_path:
            self._update_or_create_registry(session, case.case_id, saved_path, "不動産登記情報", analysis_data, file_hash)
            msg = f"【自動処理】不動産登記情報を保存しました。\n保存先: {dest_dir.name}/{saved_path.name}\n※Home画面の「不動産登録」から登録してください。"
            session.add(ContactLog(case_id=case.case_id, contact_content=msg))

class OtherDocumentHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        doc_type = analysis_data.get("doc_type", "書類")
        final_filename = self._generate_filename(case, doc_type)
        
        dest_dir = Path(case.folder_path) if case.folder_path and os.path.exists(case.folder_path) else None
        
        saved_path = self._save_file_copy(original_path, dest_dir, final_filename) if dest_dir else None
        if saved_path:
            self._update_or_create_registry(session, case.case_id, saved_path, doc_type, analysis_data, file_hash)
            msg = f"【自動処理】{doc_type}を保存しました。\n保存先: {saved_path.name}"
            session.add(ContactLog(case_id=case.case_id, contact_content=msg))

class HeirListHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"👨‍👩‍👧‍👦 相続人リスト・ハンドラー起動")
        new_filename = self._generate_filename(case, "推定相続人連絡先一覧")
        # デフォルト動作: 受領資料
        dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
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
            "corporate_registry": CorporateRegistryHandler(self.db), # ★新規
            "balance_certificate": BalanceCertificateHandler(self.db),
            "transaction_detail": TransactionDetailHandler(self.db),
            "bank_passbook": BankPassbookHandler(self.db),
            "securities_statement": SecuritiesStatementHandler(self.db),
            "invoice": InvoiceHandler(self.db),
            "registry_document": RegistryDocumentHandler(self.db),
            "heir_list": HeirListHandler(self.db),
            "tax_payment_notice": TaxPaymentNoticeHandler(self.db),
            "other": OtherDocumentHandler(self.db)
        }

    def process_file(self, file_path: str):
        """Watcherからの自動処理エントリーポイント"""
        path = Path(file_path)
        logger.info(f"🚀 [Scanner] 処理開始: {path.name}")
        time.sleep(1.0)
        try:
            if not path.exists():
                logger.error(f"   ❌ ファイル消失: {path}")
                return
            with open(path, "rb") as f: file_bytes = f.read()
            f_hash = hashlib.md5(file_bytes).hexdigest()
            
            logger.info("   🤖 AI解析を実行中...")
            analysis = self._analyze_document(file_bytes)
            candidates = analysis.get("case_candidates", [])
            doc_type = analysis.get('doc_type', 'unknown')
            
            logger.info(f"   📋 解析完了: {doc_type}")
            logger.info(f"   💡 候補案件: {len(candidates)} 件")
            
            session = self.db._get_session()
            try:
                # ----------------------------------------------------------------
                # 自律実行モード (Auto Mode)
                # 条件: 候補が1件だけ かつ 書類種別が明確
                # ※ 商業登記(corporate_registry)は誤紐付け防止のため自動処理から除外する
                # ----------------------------------------------------------------
                is_high_confidence = (len(candidates) == 1) and \
                                     (doc_type not in ["other", "unknown", "corporate_registry"])
                
                if is_high_confidence:
                    target_case_id = candidates[0]['case_id']
                    logger.info(f"   ✨ 高信頼度 (100%) -> 自動処理を実行します (Case: {target_case_id})")
                    
                    self._execute_handler(session, target_case_id, analysis, path, file_hash=f_hash)
                    
                    try:
                        os.remove(path)
                        logger.info("   🗑️ 元ファイルを削除しました (処理完了)")
                    except Exception as ex:
                        logger.warning(f"   ⚠️ 元ファイル削除失敗: {ex}")
                        
                else:
                    # ----------------------------------------------------------------
                    # 従来モード (保留 / PENDING)
                    # ----------------------------------------------------------------
                    logger.info("   🤔 確認が必要 -> 受信トレイ(Pending)へ")
                    
                    temp_storage = Config.DATA_DIR / "uploads" / "pending"
                    temp_storage.mkdir(parents=True, exist_ok=True)
                    saved_path = temp_storage / path.name
                    shutil.copy2(str(path), str(saved_path))
                    
                    candidate_id = candidates[0]['case_id'] if candidates else None
                    self._register_file_entry(session, candidate_id, saved_path, doc_type, analysis, status="PENDING")
                    
                    try:
                        os.remove(path)
                    except: pass
                
                session.commit()
                
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
        conf = 1.0 if status == "CONFIRMED" else 0.0
        
        if existing:
            existing.status = status
            existing.extracted_data = extracted_json
            existing.filename = file_path.name
            existing.ai_confidence = conf
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
                ai_confidence=conf,
                extracted_data=extracted_json
            )
            session.add(new_reg)

    def _execute_handler(self, session, case_id: int, analysis: dict, path: Path, file_hash: str):
        case = session.query(Case).options(joinedload(Case.deceased_ref)).get(case_id)
        if case:
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
            
            if override_doc_type:
                analysis["doc_type"] = override_doc_type

            self._execute_handler(session, target_case_id, analysis, file_path, file_hash=buffer_id)
            
            file_entry = session.query(FileRegistry).filter_by(file_hash=buffer_id).first() 
            if file_entry and file_entry.status != "CONFIRMED":
                file_entry.status = "CONFIRMED"
                file_entry.case_id = target_case_id
                file_entry.ai_confidence = 1.0
            
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
        - **names**: 「遺言者」「依頼者」「契約者」「お客様」などの氏名を最優先で抽出。なければ被相続人名。
        - **bank_name**: 金融機関名・証券会社名。
        
        # 2. 書類種別 (doc_type) の判定
        - **corporate_registry**: 「全部事項証明書」「履歴事項全部証明書」など、会社の登記簿謄本。タイトルに「事項証明書」とあり、かつ「商号」「本店」の記載があるもの。
        - **securities_statement**: 証券会社の報告書。
        - **tax_payment_notice**: 固定資産税納税通知書。
        - **heir_list**: 相続人一覧。
        - registry_document: 不動産登記情報 (土地・建物)。
        - bank_passbook: 通帳。
        - balance_certificate: 残高証明書。
        - transaction_detail: 取引明細。
        - invoice: 請求書。
        - other: その他。

        # 3. メタデータ (meta) の抽出
        
        **【A】corporate_registry (商業登記) の場合**
        - **corporate_name**: 商号（会社名）。「株式会社〇〇」など。
        - **head_office**: 本店所在地。

        **【B】securities_statement (証券関連) の場合**
        - branch_name, account_number, balance, holdings.

        **【C】balance_certificate / bank_passbook (銀行関連) の場合**
        - branch_name, account_number, balance, holder_name, account_type.

        # 出力JSON例 (商業登記)
        {
            "names": [],
            "doc_type": "corporate_registry",
            "meta": {
                "corporate_name": "株式会社チェスター",
                "head_office": "東京都中央区..."
            },
            "case_candidates": []
        }
        """
        
        msg = HumanMessage(content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": f"data:{mime};base64,{doc_b64}"}])
        try:
            resp = self.llm.invoke([msg])
            ai_data = json.loads(resp.content.replace("```json", "").replace("```", "").strip())
        except: return {}
        
        # --- Pythonによる後処理 ---
        bank_name = ai_data.get("bank_name", "")
        doc_type = ai_data.get("doc_type", "")
        
        if "証券" in bank_name or "證券" in bank_name:
            if doc_type != "securities_statement":
                ai_data["doc_type"] = "securities_statement"
        
        if "野村" in bank_name and doc_type == "balance_certificate":
             ai_data["doc_type"] = "securities_statement"

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