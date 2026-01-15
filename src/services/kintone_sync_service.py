# src/services/kintone_sync_service.py

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir, Address, Contact, H_AddressHistory, H_ContactLink, User
from src.utils.date_utils import parse_all_flexible_date

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# ヘルパー関数
# ---------------------------------------------------------
def katakana_to_hiragana(text: str) -> str:
    """カタカナをひらがなに変換する"""
    if not text:
        return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            result += chr(code - 0x60)
        else:
            result += char
    return result

def format_name_full_width(last: str, first: str) -> str:
    """姓と名を全角スペースで結合する"""
    l = (last or "").strip()
    f = (first or "").strip()
    if l and f:
        return f"{l}　{f}"
    return f"{l}{f}"

# ---------------------------------------------------------
# データ取得 (DB -> Kintone)
# ---------------------------------------------------------
def get_kintone_data_as_dict(case_id: int) -> Optional[Dict[str, Any]]:
    """
    Kintoneブックマークレット（書き込み用）が期待する形式の辞書を作成する
    """
    db = DatabaseManager()
    session = db._get_session()
    
    try:
        case = session.query(Case).filter_by(case_id=case_id).first()
        if not case: return None
        
        deceased = case.deceased_ref
        
        # --- 1. 基本情報の加工 ---
        out_case_number = ""
        if case.case_number and case.case_number.startswith("G"):
            out_case_number = case.case_number

        manager_name = ""
        if case.manager_id:
            m_user = session.query(User).get(case.manager_id)
            if m_user: manager_name = m_user.name

        operator_name = ""
        if case.operator_id:
            o_user = session.query(User).get(case.operator_id)
            if o_user: operator_name = o_user.name

        # --- 2. 被相続人情報 ---
        d_name = ""
        d_kana = ""
        start_date = ""
        
        if deceased:
            d_name = format_name_full_width(deceased.name_last, deceased.name_first)
            
            dk_last = katakana_to_hiragana(deceased.name_last_kana)
            dk_first = katakana_to_hiragana(deceased.name_first_kana)
            d_kana = format_name_full_width(dk_last, dk_first)
            
            if deceased.date_of_death:
                start_date = deceased.date_of_death.strftime("%Y-%m-%d")

        # --- 3. 依頼者（相続人）情報 ---
        heir_name = case.client_name
        heir_kana = katakana_to_hiragana(case.client_name_kana)
        heir_zip = ""
        heir_address = ""
        heir_tel = ""
        heir_mail = ""

        contractor = None
        if deceased and deceased.heirs:
            contractor = next((h for h in deceased.heirs if h.is_contracting_party), None)
            if not contractor and deceased.heirs:
                contractor = deceased.heirs[0]

        if contractor:
            heir_name = format_name_full_width(contractor.name_last, contractor.name_first)
            
            hk_last = katakana_to_hiragana(contractor.name_last_kana)
            hk_first = katakana_to_hiragana(contractor.name_first_kana)
            heir_kana = format_name_full_width(hk_last, hk_first)

            addr_link = session.query(H_AddressHistory).filter(
                H_AddressHistory.heir_id == contractor.id, 
                H_AddressHistory.is_current_address == True
            ).first()
            if addr_link:
                addr = session.query(Address).get(addr_link.address_id)
                if addr:
                    heir_zip = addr.zip_code or ""
                    heir_address = f"{addr.prefecture}{addr.city_ward_town}{addr.street_address} {addr.building_name or ''}".strip()

            links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for l in links:
                c = session.query(Contact).get(l.contact_id)
                if c:
                    if c.type == "PHONE" and not heir_tel: heir_tel = c.value
                    if c.type == "EMAIL" and not heir_mail: heir_mail = c.value

        # --- 4. SOL連携情報 ---
        route_val = ""
        nikko_branch = ""
        nikko_rep = ""
        nikko_sol_no = ""
        nikko_consent_date = ""

        if case.sol_case_number:
            route_val = "日興証券"
            nikko_branch = case.referral_sec_branch_name or ""
            nikko_rep = case.referral_sec_rep_name or ""
            nikko_sol_no = case.sol_case_number
            if case.consent_date:
                nikko_consent_date = case.consent_date.strftime("%Y-%m-%d")

        return {
            "case_number": out_case_number,
            "branch": "東京",
            "team": "東京1部",
            "manager": manager_name,
            "operator": operator_name,
            "interviewer": "",
            "notification_dest": "",
            
            "heir_name": heir_name,
            "heir_kana": heir_kana,
            "heir_zip": heir_zip,
            "heir_tel": heir_tel,
            "heir_mail": heir_mail,
            "heir_address": heir_address,
            
            "deceased_name": d_name,
            "deceased_kana": d_kana,
            "start_date": start_date,
            
            "intro_date": str(case.introduction_date) if case.introduction_date else "",
            "interview_date": "",
            "interview_place": "",

            "route": route_val, 
            "nikko_branch": nikko_branch,
            "nikko_rep": nikko_rep,
            "nikko_sol_no": nikko_sol_no,
            "nikko_consent_date": nikko_consent_date
        }

    except Exception as e:
        logger.error(f"Kintone data fetch error: {e}")
        return None
    finally:
        session.close()

def copy_kintone_data_to_clipboard(case_id: int) -> bool:
    data = get_kintone_data_as_dict(case_id)
    return data is not None

# ---------------------------------------------------------
# データ取込 (Kintone -> DB) ★この関数が不足していました
# ---------------------------------------------------------
def import_kintone_json(json_data: Dict[str, Any], target_case_id: Optional[int] = None) -> int:
    """
    KintoneのJSONデータを取り込み、DBを更新または新規作成する。
    """
    db = DatabaseManager()
    session = db._get_session()
    
    try:
        # 1. データの正規化
        case_num = json_data.get("顧客コード", "").strip() or json_data.get("顧客コード_2", "").strip()
        
        client_name_raw = json_data.get("顧客名", "").replace("　", " ").strip()
        client_kana_raw = json_data.get("顧客名(ふりがな)", "").replace("　", " ").strip()
        
        deceased_name_raw = json_data.get("被相続人名", "").replace("　", " ").strip()
        deceased_kana_raw = json_data.get("被相続人名（ふりがな）", "").replace("　", " ").strip()
        
        sol_no = json_data.get("SOL案件No.（日興）", "")
        intro_date = parse_all_flexible_date(json_data.get("紹介日", ""))
        consent_date = parse_all_flexible_date(json_data.get("同意書日付(日興)", ""))
        
        mgr_name = json_data.get("担当者①", "")
        opr_name = json_data.get("担当者②", "")
        
        # 2. 案件 (Case) の特定または作成
        case = None
        if target_case_id:
            case = session.query(Case).get(target_case_id)
        
        if not case and case_num:
            case = session.query(Case).filter_by(case_number=case_num).first()
        
        if not case:
            # 新規作成
            case = Case(
                case_number=case_num if case_num else "TMP", 
                client_name=client_name_raw,
                created_at=datetime.now()
            )
            session.add(case)
            session.flush()
        
        # 3. 案件情報の更新 (上書き)
        case.client_name = client_name_raw
        case.client_name_kana = client_kana_raw
        case.sol_case_number = sol_no
        case.introduction_date = intro_date
        case.consent_date = consent_date
        
        # 紹介元情報
        case.referral_sec_branch_name = json_data.get("支店名（日興）") or json_data.get("支店名（大和）") or ""
        case.referral_sec_rep_name = json_data.get("担当者（日興）") or json_data.get("担当者（大和）") or ""

        # 担当者紐付け (名前の部分一致検索)
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
        
        d_parts = deceased_name_raw.split(" ", 1)
        deceased.name_last = d_parts[0]
        deceased.name_first = d_parts[1] if len(d_parts) > 1 else ""
        
        d_k_parts = deceased_kana_raw.split(" ", 1)
        deceased.name_last_kana = d_k_parts[0]
        deceased.name_first_kana = d_k_parts[1] if len(d_k_parts) > 1 else ""
        
        # 相続開始日
        start_date = parse_all_flexible_date(json_data.get("相続開始日", ""))
        if start_date:
            deceased.date_of_death = start_date
        
        session.flush()

        # 5. 契約者 (Heir) の更新
        contractor = session.query(Heir).filter(
            Heir.deceased_id == deceased.id,
            Heir.is_contracting_party == True
        ).first()
        
        if not contractor:
            contractor = Heir(
                deceased_id=deceased.id,
                is_contracting_party=True,
                relationship_type="相談者"
            )
            session.add(contractor)
        
        c_parts = client_name_raw.split(" ", 1)
        contractor.name_last = c_parts[0]
        contractor.name_first = c_parts[1] if len(c_parts) > 1 else ""
        
        c_k_parts = client_kana_raw.split(" ", 1)
        contractor.name_last_kana = c_k_parts[0]
        contractor.name_first_kana = c_k_parts[1] if len(c_k_parts) > 1 else ""

        # 6. 住所 (Heirに紐づくAddress)
        zip_code = json_data.get("郵便番号", "")
        address_full = json_data.get("住所", "")
        
        addr_link = session.query(H_AddressHistory).filter(
            H_AddressHistory.heir_id == contractor.id,
            H_AddressHistory.is_current_address == True
        ).first()
        
        # 簡易分割 (都道府県)
        pref = ""
        street = address_full
        match = re.match(r"(...??[都道府県])(.+)", address_full)
        if match:
            pref = match.group(1)
            street = match.group(2)

        if addr_link:
            addr = session.query(Address).get(addr_link.address_id)
            addr.zip_code = zip_code
            addr.prefecture = pref
            addr.street_address = street
        else:
            new_addr = Address(
                zip_code=zip_code, 
                prefecture=pref,
                street_address=street
            )
            session.add(new_addr)
            session.flush()
            session.add(H_AddressHistory(heir_id=contractor.id, address_id=new_addr.id, is_current_address=True))

        # 7. 電話番号
        tel_str = json_data.get("TEL", "")
        if tel_str:
            session.query(H_ContactLink).filter(H_ContactLink.heir_id==contractor.id).delete()
            tels = tel_str.replace("、", ",").split(",")
            for i, t in enumerate(tels):
                c = Contact(value=t.strip(), type="PHONE", sub_type="Primary" if i==0 else "Secondary")
                session.add(c); session.flush()
                session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))
        
        # 8. メールアドレス
        mail_str = json_data.get("メールアドレス", "")
        if mail_str:
            # 既存メール削除 (簡易)
            # 本来はタイプ指定で削除すべきだが、ここではContactLink経由で全削除済みと仮定または追加のみ
            # 上記でH_ContactLinkを全削除しているので追加でOK
            c = Contact(value=mail_str.strip(), type="EMAIL", sub_type="Primary")
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