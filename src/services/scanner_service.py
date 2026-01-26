# src/services/scanner_service.py

import os
import time
import shutil
import logging
import datetime
import json
import base64
import uuid
import unicodedata
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage
from sqlalchemy.orm import joinedload 
from sqlalchemy import or_, func

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Case, FinancialAsset, BankMaster, BranchMaster, AccountTypeMaster,
    Deceased, Heir, Address, H_AddressHistory, Contact, H_ContactLink
)
from legal_system.core.schemas import HeirListAnalysisResult
from services.deceased_service import find_cases_by_attributes

logger = logging.getLogger(__name__)

# ==========================================
# ヘルパー関数: Zenginデータ検索 (共通化)
# ==========================================
BASE_DIR = Path(__file__).resolve().parents[2] # src/services/ -> src/ -> root
ZENGIN_DATA_DIR = BASE_DIR / "data" / "zengin"

def normalize_name(text: str) -> str:
    if not text: return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace(" ", "").replace("　", "")
    return normalized.replace("銀行", "").replace("支店", "")

def find_bank_in_zengin(search_name: str):
    """Zenginデータから銀行を検索し、(code, name) を返す"""
    banks_path = ZENGIN_DATA_DIR / "banks.json"
    if not banks_path.exists(): return None, None

    search_key = normalize_name(search_name)
    try:
        with open(banks_path, "r", encoding="utf-8") as f:
            banks = json.load(f)
        
        # 1. 完全一致
        for code, info in banks.items():
            if search_key == normalize_name(info["name"]):
                return code, info["name"]
        
        # 2. 逆包含 ("三菱UFJ" -> "三菱UFJ銀行")
        for code, info in banks.items():
            if search_key in normalize_name(info["name"]):
                return code, info["name"]
    except: pass
    return None, None

def find_branch_in_zengin(bank_code: str, branch_search_name: str):
    """指定された銀行コード内の支店を検索し、(code, name) を返す"""
    if not bank_code or not branch_search_name: return None, None
    branch_path = ZENGIN_DATA_DIR / "branches" / f"{bank_code}.json"
    if not branch_path.exists(): return None, None

    search_key = normalize_name(branch_search_name)
    try:
        with open(branch_path, "r", encoding="utf-8") as f:
            branches = json.load(f)

        # 1. 完全一致
        for code, info in branches.items():
            if search_key == normalize_name(info["name"]):
                return code, info["name"]
        
        # 2. 部分一致
        for code, info in branches.items():
            if search_key in normalize_name(info["name"]):
                return code, info["name"]
    except: pass
    return None, None

def katakana_to_hiragana(text: str) -> str:
    """カタカナをひらがなに変換する"""
    if not text: return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            result += chr(code - 0x60)
        else:
            result += char
    return result

# ==========================================
# 1. ハンドラー基底クラス (共通ロジック)
# ==========================================
class DocumentHandler(ABC):
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    @abstractmethod
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
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
            except Exception: return None

        if not target_keyword:
            return parent_dir

        target_dir = None
        for item in parent_dir.iterdir():
            if item.is_dir() and target_keyword in item.name:
                target_dir = item
                break
        
        if not target_dir:
            try:
                target_dir = parent_dir / f"00_{target_keyword}"
                target_dir.mkdir(exist_ok=True)
            except Exception: return None
            
        return target_dir

    def _move_file(self, src: Path, dest_dir: Path, filename: str):
        dest_path = dest_dir / filename
        if dest_path.exists():
            base = dest_path.stem; ext = dest_path.suffix; counter = 1
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
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        new_filename = self._generate_filename(case, "残高証明書", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "取得代行資料", "残高証明書")
        if dest_dir: self._move_file(original_path, dest_dir, new_filename)

        balance = analysis_data.get("meta", {}).get("balance", 0)
        if balance:
            self._upsert_asset(session, case.case_id, bank_name, balance)

    def _upsert_asset(self, session, case_id, bank_name, balance):
        try:
            # Zengin検索 (簡易)
            z_code, z_name = find_bank_in_zengin(bank_name)
            bank_code_to_use = z_code if z_code else f"TMP-{uuid.uuid4().hex[:6]}"
            bank_name_to_use = z_name if z_name else bank_name

            bank = session.query(BankMaster).filter(
                or_(BankMaster.bank_name == bank_name_to_use, BankMaster.bank_code == bank_code_to_use)
            ).first()
            
            if not bank:
                bank = BankMaster(bank_name=bank_name_to_use, bank_code=bank_code_to_use)
                session.add(bank); session.flush()

            existing = session.query(FinancialAsset).filter_by(case_id=case_id, bank_id=bank.id).first()
            if existing:
                existing.balance = balance
                existing.status = "残高証明書確認済"
            else:
                new_asset = FinancialAsset(case_id=case_id, bank_id=bank.id, account_number="AI読取", balance=balance, status="残高証明書確認済")
                session.add(new_asset)
        except Exception: pass

class TransactionDetailHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        new_filename = self._generate_filename(case, "取引明細書", bank_name)
        dest_dir = self._find_target_folder(case.folder_path, "取得代行資料", "取引履歴")
        if dest_dir: self._move_file(original_path, dest_dir, new_filename)

class BankPassbookHandler(DocumentHandler):
    """通帳用ハンドラー"""
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        meta = analysis_data.get("meta", {})
        branch_name = meta.get("branch_name", "")
        acc_type_name = meta.get("account_type", "普通")
        acc_number = meta.get("account_number", "")

        identifier = f"{bank_name}_{branch_name}" if branch_name else bank_name
        new_filename = self._generate_filename(case, "通帳", identifier)
        dest_dir = self._find_target_folder(case.folder_path, "受領資料")
        
        if dest_dir:
            self._move_file(original_path, dest_dir, new_filename)

        if bank_name:
            self._register_passbook_asset(session, case.case_id, bank_name, branch_name, acc_type_name, acc_number)

    def _register_passbook_asset(self, session, case_id, bank_name, branch_name, acc_type_name, acc_number):
        try:
            # ------------------------------------
            # A. 銀行マスタ検索/登録 (Zengin優先)
            # ------------------------------------
            z_bank_code, z_bank_name = find_bank_in_zengin(bank_name)
            
            # DB内検索 (コード優先、次に名前)
            bank = None
            if z_bank_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_bank_code).first()
            if not bank:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == (z_bank_name or bank_name)).first()

            # 新規登録
            if not bank:
                code_to_use = z_bank_code if z_bank_code else f"TMP-{uuid.uuid4().hex[:6]}"
                name_to_use = z_bank_name if z_bank_name else bank_name
                bank = BankMaster(bank_name=name_to_use, bank_code=code_to_use)
                session.add(bank)
                session.flush()

            # ------------------------------------
            # B. 支店マスタ検索/登録 (Zengin優先)
            # ------------------------------------
            branch = None
            if branch_name:
                # Zengin検索 (銀行が正規コードを持っている場合のみ)
                z_br_code, z_br_name = None, None
                if bank.bank_code and not bank.bank_code.startswith("TMP"):
                    z_br_code, z_br_name = find_branch_in_zengin(bank.bank_code, branch_name)

                # DB内検索
                if z_br_code:
                    branch = session.query(BranchMaster).filter(
                        BranchMaster.bank_id == bank.id,
                        BranchMaster.branch_code == z_br_code
                    ).first()
                
                if not branch:
                    branch = session.query(BranchMaster).filter(
                        BranchMaster.bank_id == bank.id,
                        BranchMaster.branch_name == (z_br_name or branch_name)
                    ).first()

                # 新規登録
                if not branch:
                    br_code_to_use = z_br_code if z_br_code else f"B-{uuid.uuid4().hex[:6]}"
                    br_name_to_use = z_br_name if z_br_name else branch_name
                    
                    branch = BranchMaster(
                        bank_id=bank.id, 
                        branch_name=br_name_to_use, 
                        branch_code=br_code_to_use
                    )
                    session.add(branch)
                    session.flush()

            # ------------------------------------
            # C. 口座種別マスタ
            # ------------------------------------
            if not acc_type_name: acc_type_name = "普通"
            ac_type = session.query(AccountTypeMaster).filter(AccountTypeMaster.type_name.like(f"%{acc_type_name}%")).first()
            if not ac_type:
                ac_type = AccountTypeMaster(type_name=acc_type_name)
                session.add(ac_type)
                session.flush()

            # ------------------------------------
            # D. 資産データ登録 (重複チェック)
            # ------------------------------------
            existing = session.query(FinancialAsset).filter(
                FinancialAsset.case_id == case_id,
                FinancialAsset.bank_id == bank.id,
                FinancialAsset.account_number == (acc_number if acc_number else "AI読取")
            ).first()

            if existing:
                if "確認済" not in (existing.status or ""): existing.status = "通帳確認済"
                # 支店が特定できていれば更新
                if not existing.branch_id and branch:
                    existing.branch_id = branch.id
                logger.info(f"   🔄 口座情報更新: {bank.bank_name} {branch.branch_name if branch else ''}")
            else:
                new_asset = FinancialAsset(
                    case_id=case_id, 
                    bank_id=bank.id, 
                    branch_id=branch.id if branch else None,
                    account_type_id=ac_type.id, 
                    account_number=acc_number if acc_number else "AI読取",
                    balance=0, 
                    status="通帳確認", 
                    asset_type="BANK"
                )
                session.add(new_asset)
                logger.info(f"   🆕 口座情報登録: {bank.bank_name} {branch.branch_name if branch else ''}")

        except Exception as e:
            logger.error(f"   ❌ 通帳DB登録失敗: {e}")

class HeirContactListHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path):
        # (省略: 変更なし)
        pass

# ==========================================
# 3. ScannerService (メインサービス)
# ==========================================
class ScannerService:
    def __init__(self, inbox_path: str, processed_root: str):
        self.inbox_path = Path(inbox_path)
        self.processed_root = Path(processed_root)
        self.db = DatabaseManager()
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        
        self.handlers: Dict[str, DocumentHandler] = {
            "balance_certificate": BalanceCertificateHandler(self.db),
            "transaction_detail": TransactionDetailHandler(self.db),
            "heir_contact_list": HeirContactListHandler(self.db),
            "bank_passbook": BankPassbookHandler(self.db),
        }

    def process_file(self, file_path: str):
        path = Path(file_path)
        time.sleep(2) 
        logger.info(f"🖨️ スキャン検知: {path.name}")
        
        try:
            with open(path, "rb") as f:
                file_bytes = f.read()
            
            analysis = self._analyze_document(file_bytes)
            logger.info(f"   🧠 AI解析結果: {analysis}")

            if not analysis.get("case_candidates"):
                logger.warning("   ⚠️ 案件を特定できませんでした（移動せず残します）。")
                return

            target_case_id = analysis["case_candidates"][0]["case_id"]
            doc_type = analysis.get("doc_type", "other")
            
            session = self.db._get_session()
            try:
                case = session.query(Case).options(joinedload(Case.deceased_ref)).get(target_case_id)
                if not case: return

                logger.info(f"   📂 ターゲット案件: {case.client_name} (G{case.case_number})")
                handler = self.handlers.get(doc_type)
                
                if handler:
                    handler.handle(session, case, analysis, path)
                    session.commit()
                else:
                    logger.info("   ℹ️ 未定義の書類タイプのためスキップ")

            except Exception as e:
                session.rollback(); raise e
            finally:
                session.close()

        except Exception as e:
            logger.error(f"   ❌ 処理エラー: {e}")

    def _analyze_document(self, file_bytes: bytes) -> dict:
        """Gemini Visionで分類と案件特定情報を抽出（PDF/画像ダイレクト送信）"""
        
        mime_type = "image/jpeg"
        if file_bytes.startswith(b"%PDF"):
            mime_type = "application/pdf"
        
        import base64
        doc_b64 = base64.b64encode(file_bytes).decode("utf-8")
        
        prompt = """
        この書類を解析し、以下の情報をJSONで抽出してください。
        
        1. **names**: 
           - 文書内の「被相続人(故人)」または「依頼者」の氏名。
           - **【重要】通帳の場合**: 「名義人」の氏名（カタカナ含む）を必ず抽出してください（例: "トミタ ソウコ"）。
        2. **bank_name**: 金融機関名（正式名称）。
        3. **doc_type**: 以下のいずれか。
           - "bank_passbook": 銀行の通帳（表紙、裏表紙、明細面）
           - "balance_certificate": 残高証明書
           - "transaction_detail": 取引明細
           - "heir_contact_list": 推定相続人連絡先一覧
           - "other": その他
        4. **meta**: 
           - 通帳の場合: "branch_name"(支店名), "account_type"(普通/定期), "account_number"(番号), "holder_name"(名義人)
        """
        
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{doc_b64}"}
            }
        ])
        
        ai_data = {}
        try:
            resp = self.llm.invoke([msg])
            content = resp.content.replace("```json", "").replace("```", "").strip()
            ai_data = json.loads(content)
        except Exception as e:
            logger.error(f"AI解析エラー: {e}")
            return {}
        
        # 5. 案件検索ロジック (カナ/ひらがな対応)
        names = ai_data.get("names", [])
        holder = ai_data.get("meta", {}).get("holder_name")
        if holder and holder not in names:
            names.append(holder)

        candidates = []
        if names:
            session = self.db._get_session()
            try:
                for name in names:
                    hits = find_cases_by_attributes(deceased_name=name)
                    if not hits:
                        hits = find_cases_by_attributes(client_name=name)
                    
                    if not hits:
                        clean_kana = name.replace(" ", "").replace("　", "")
                        clean_hira = katakana_to_hiragana(clean_kana)
                        logger.info(f"   🔍 カナ検索試行: {clean_kana} / {clean_hira}")

                        res = session.query(Case).options(joinedload(Case.deceased_ref)).filter(
                            or_(
                                func.replace(func.replace(Case.client_name_kana, ' ', ''), '　', '').contains(clean_kana),
                                func.replace(func.replace(Case.client_name_kana, ' ', ''), '　', '').contains(clean_hira),
                                Case.deceased_ref.has(func.replace(func.replace(Deceased.name_last_kana, ' ', ''), '　', '').contains(clean_kana)),
                                Case.deceased_ref.has(func.replace(func.replace(Deceased.name_last_kana, ' ', ''), '　', '').contains(clean_hira)),
                                Case.deceased_ref.has(func.replace(func.replace(Deceased.name_first_kana, ' ', ''), '　', '').contains(clean_kana)),
                                Case.deceased_ref.has(func.replace(func.replace(Deceased.name_first_kana, ' ', ''), '　', '').contains(clean_hira))
                            )
                        ).all()
                        
                        for c in res:
                            d_name = f"{c.deceased_ref.name_last} {c.deceased_ref.name_first}" if c.deceased_ref else ""
                            hits.append({
                                "case_id": c.case_id,
                                "case_number": c.case_number,
                                "client_name": c.client_name,
                                "deceased_name": d_name
                            })
                    
                    candidates.extend(hits)
            finally:
                session.close()
        
        unique_candidates = {c['case_id']: c for c in candidates}.values()
        ai_data["case_candidates"] = list(unique_candidates)
        
        return ai_data