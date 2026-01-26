# src/services/kintone_sync_service.py

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, List

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address, Case, Contact, Deceased, H_AddressHistory, H_ContactLink, Heir, User
)
from src.utils.date_utils import parse_all_flexible_date
from services.deceased_service import get_next_case_number_service

logger = logging.getLogger(__name__)

# ... (ヘルパー関数群 katakana_to_hiragana, format_name_full_width 等は変更なし) ...
def katakana_to_hiragana(text: str) -> str:
    if not text: return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6: result += chr(code - 0x60)
        else: result += char
    return result

def format_name_full_width(last: str, first: str) -> str:
    l = (last or "").strip(); f = (first or "").strip()
    return f"{l}　{f}" if l and f else f"{l}{f}"

def get_value_from_keys(data: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        if k in data and data[k]:
            val = str(data[k]).strip()
            if val.lower() != "none": return val
    return ""

def get_raw_value(data: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in data:
            val = str(data[k]).strip()
            if val.lower() == "none": return ""
            return val
    return None

# ... (get_kintone_data_as_dict は変更なし) ...
def get_kintone_data_as_dict(case_id: int) -> Optional[Dict[str, Any]]:
    # 省略（既存コードのまま）
    db = DatabaseManager()
    session = db._get_session()
    try:
        case = session.query(Case).filter_by(case_id=case_id).first()
        if not case: return None
        deceased = case.deceased_ref
        
        manager_name = ""
        if case.manager_id:
            m_user = session.query(User).get(case.manager_id)
            if m_user: manager_name = m_user.name
        operator_name = ""
        if case.operator_id:
            o_user = session.query(User).get(case.operator_id)
            if o_user: operator_name = o_user.name

        d_name = ""; d_kana = ""; start_date = ""
        if deceased:
            d_name = format_name_full_width(deceased.name_last, deceased.name_first)
            d_kana = format_name_full_width(katakana_to_hiragana(deceased.name_last_kana), katakana_to_hiragana(deceased.name_first_kana))
            if deceased.date_of_death: start_date = deceased.date_of_death.strftime("%Y-%m-%d")

        contractor = None
        if deceased and deceased.heirs:
            contractor = next((h for h in deceased.heirs if h.is_contracting_party), None)
            if not contractor and deceased.heirs: contractor = deceased.heirs[0]

        heir_tel = ""; heir_mail = ""
        if contractor:
            links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for l in links:
                c = session.query(Contact).get(l.contact_id)
                if c:
                    if c.type == "PHONE" and not heir_tel: heir_tel = c.value
                    if c.type == "EMAIL" and not heir_mail: heir_mail = c.value

        return {
            "顧客コード_2": case.case_number,
            "顧客名": case.client_name,
            "顧客名(ふりがな)": case.client_name_kana,
            "TEL": heir_tel,
            "メールアドレス": heir_mail,
            "被相続人名": d_name,
            "被相続人名（ふりがな）": d_kana,
            "相続開始日": start_date,
            "担当者①": manager_name,
            "担当者②": operator_name,
            "SOL案件No.（日興）": case.sol_case_number or "",
            "支店名（日興）": case.referral_sec_branch_name or "",
            "担当者（日興）": case.referral_sec_rep_name or "",
            "紹介日": str(case.introduction_date) if case.introduction_date else "",
            "備考": f"【紹介元電話】{case.referral_sec_phone}" if case.referral_sec_phone else "",
        }
    except Exception as e:
        logger.error(f"Kintone data build error: {e}"); return None
    finally:
        session.close()

def copy_kintone_data_to_clipboard(case_id: int) -> bool:
    data = get_kintone_data_as_dict(case_id)
    return data is not None

# ---------------------------------------------------------
# データ取込 (Kintone -> DB)
# ---------------------------------------------------------
def import_kintone_json(
    json_data: Dict[str, Any], target_case_id: Optional[int] = None
) -> int:
    """
    KintoneのJSONデータを取り込み、DBを更新または新規作成する。
    """
    db = DatabaseManager()
    session = db._get_session()

    try:
        # 1. データの正規化
        k_rec_id_raw = get_value_from_keys(json_data, ["$id", "record_id", "レコード番号"])
        k_record_id = int(k_rec_id_raw) if k_rec_id_raw and k_rec_id_raw.isdigit() else None
        case_num = get_value_from_keys(json_data, ["顧客コード", "顧客コード_2", "case_number", "案件番号"])
        client_name_raw = get_value_from_keys(json_data, ["顧客名", "client_name", "氏名"]).replace("　", " ")
        client_kana_raw = get_value_from_keys(json_data, ["顧客名(ふりがな)", "顧客名（ふりがな）", "client_name_kana", "フリガナ"]).replace("　", " ")
        deceased_name_raw = get_value_from_keys(json_data, ["被相続人名", "deceased_name", "被相続人"]).replace("　", " ")
        deceased_kana_raw = get_value_from_keys(json_data, ["被相続人名（ふりがな）", "被相続人名(ふりがな)", "deceased_name_kana"]).replace("　", " ")
        sol_no = get_value_from_keys(json_data, ["SOL案件No.（日興）", "SOL案件No", "sol_case_number"])
        intro_date = parse_all_flexible_date(get_value_from_keys(json_data, ["紹介日", "introduction_date"]))
        consent_date = parse_all_flexible_date(get_value_from_keys(json_data, ["同意書日付(日興)", "同意書日付", "consent_date"]))
        mgr_name = get_value_from_keys(json_data, ["担当者①", "manager_name", "担当者1"])
        opr_name = get_value_from_keys(json_data, ["担当者②", "operator_name", "担当者2"])

        # 2. 案件 (Case) の特定または作成
        case = None
        if target_case_id:
            case = session.query(Case).get(target_case_id)
        if not case and case_num:
            case = session.query(Case).filter_by(case_number=case_num).first()
        if not case:
            if case_num: temp_num = case_num
            else:
                try: temp_num = get_next_case_number_service()
                except: temp_num = f"TMP-{datetime.now().strftime('%H%M%S')}"
            case = Case(case_number=temp_num, client_name=client_name_raw or "名称未設定", created_at=datetime.now())
            session.add(case)
            session.flush()

        # 3. 案件情報の更新
        if k_record_id: case.kintone_record_id = k_record_id
        if client_name_raw: case.client_name = client_name_raw
        if client_kana_raw: case.client_name_kana = client_kana_raw
        case.sol_case_number = sol_no
        case.introduction_date = intro_date
        case.consent_date = consent_date
        case.referral_sec_branch_name = get_value_from_keys(json_data, ["支店名（日興）", "支店名（大和）", "紹介元支店", "referral_branch"])
        case.referral_sec_rep_name = get_value_from_keys(json_data, ["担当者（日興）", "担当者（大和）", "紹介元担当者", "referral_rep"])
        
        if mgr_name:
            u = session.query(User).filter(User.name.contains(mgr_name)).first()
            if u: case.manager_id = u.id
        if opr_name:
            u = session.query(User).filter(User.name.contains(opr_name)).first()
            if u: case.operator_id = u.id
        session.flush()

        # 4. 被相続人 (Deceased) の更新
        deceased = session.query(Deceased).filter_by(case_id=case.case_id).first()
        if not deceased:
            deceased = Deceased(case_id=case.case_id)
            session.add(deceased)
        if deceased_name_raw:
            d_parts = deceased_name_raw.split(" ", 1)
            deceased.name_last = d_parts[0]
            deceased.name_first = d_parts[1] if len(d_parts) > 1 else ""
        if deceased_kana_raw:
            d_k_parts = deceased_kana_raw.split(" ", 1)
            deceased.name_last_kana = d_k_parts[0]
            deceased.name_first_kana = d_k_parts[1] if len(d_k_parts) > 1 else ""
        start_date = parse_all_flexible_date(get_value_from_keys(json_data, ["相続開始日", "死亡日", "date_of_death", "death_date"]))
        if start_date: deceased.date_of_death = start_date
        session.flush()

        # =======================================================
        # 5. 契約者 (Heir) の更新 (★ここを修正)
        # =======================================================
        contractor = (
            session.query(Heir)
            .filter(Heir.deceased_id == deceased.id, Heir.is_contracting_party == True)
            .first()
        )

        # 契約者フラグが立っている人がいない場合、
        # いきなり新規作成するのではなく、既存の相続人がいればその人を契約者に昇格させる
        if not contractor:
            existing_heir = session.query(Heir).filter(Heir.deceased_id == deceased.id).first()
            if existing_heir:
                contractor = existing_heir
                contractor.is_contracting_party = True # 昇格
            else:
                # 誰もいない場合のみ新規作成
                contractor = Heir(
                    deceased_id=deceased.id,
                    is_contracting_party=True,
                    relationship_type="相談者",
                )
                session.add(contractor)

        # 氏名更新
        if client_name_raw:
            c_parts = client_name_raw.split(" ", 1)
            contractor.name_last = c_parts[0]
            contractor.name_first = c_parts[1] if len(c_parts) > 1 else ""
        if client_kana_raw:
            c_k_parts = client_kana_raw.split(" ", 1)
            contractor.name_last_kana = c_k_parts[0]
            contractor.name_first_kana = c_k_parts[1] if len(c_k_parts) > 1 else ""

        # 6. 住所 (Heirに紐づくAddress)
        zip_code = get_value_from_keys(json_data, ["郵便番号", "zip_code"])
        address_full = get_value_from_keys(json_data, ["住所", "address"])

        if zip_code or address_full:
            addr_link = session.query(H_AddressHistory).filter(H_AddressHistory.heir_id == contractor.id, H_AddressHistory.is_current_address == True).first()
            pref = ""; street = address_full
            match = re.match(r"(.{2,3}[都道府県])(.+)", address_full)
            if match:
                pref = match.group(1); street = match.group(2)

            if addr_link:
                addr = session.query(Address).get(addr_link.address_id)
                addr.zip_code = zip_code
                addr.prefecture = pref
                addr.city_ward_town = "" 
                addr.street_address = street
                addr.building_name = "" 
            else:
                new_addr = Address(zip_code=zip_code, prefecture=pref, street_address=street)
                session.add(new_addr)
                session.flush()
                session.add(H_AddressHistory(heir_id=contractor.id, address_id=new_addr.id, is_current_address=True))

        # 7. 電話番号 (TEL) の取込 (完全上書きモード)
        raw_tel = get_raw_value(json_data, ["TEL", "電話番号", "phone", "mobile"])
        if raw_tel is not None:
            existing_links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for link in existing_links:
                contact = session.query(Contact).get(link.contact_id)
                if contact and contact.type == "PHONE":
                    session.delete(contact); session.delete(link)
            
            if raw_tel:
                tels = raw_tel.replace("、", ",").split(",")
                for i, t in enumerate(tels):
                    clean_tel = t.strip()
                    if clean_tel:
                        c = Contact(value=clean_tel, type="PHONE", sub_type="Primary" if i == 0 else "Secondary")
                        session.add(c); session.flush()
                        session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))

        # 8. メールアドレス (Email) の取込 (完全上書きモード)
        raw_mail = get_raw_value(json_data, ["メールアドレス", "email", "mail"])
        if raw_mail is not None:
            existing_links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for link in existing_links:
                contact = session.query(Contact).get(link.contact_id)
                if contact and contact.type == "EMAIL":
                    session.delete(contact); session.delete(link)

            if raw_mail:
                c = Contact(value=raw_mail.strip(), type="EMAIL", sub_type="Primary")
                session.add(c); session.flush()
                session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))

        session.commit()
        return case.case_id

    except Exception as e:
        session.rollback()
        logger.error(f"Import Error: {e}")
        return -1
    finally:
        session.close()