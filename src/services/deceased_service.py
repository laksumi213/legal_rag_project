# src/services/deceased_service.py

import datetime
import logging
import re
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import requests
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address,
    Case,
    Contact,
    D_ContactLink,
    Deceased,
    H_AddressHistory,
    H_ContactLink,
    Heir,
    User,
    IncomingNoteBuffer,
)
from src.utils.date_utils import parse_all_flexible_date

logger = logging.getLogger(__name__)


# ==========================================
# セッション管理ヘルパー
# ==========================================
def get_db_session():
    """現在のDatabaseManagerからセッションを取得"""
    return DatabaseManager()._get_session()


# ==========================================
# 1. ユーティリティ (パス正規化など)
# ==========================================
def normalize_folder_path(path_str: str) -> str:
    if not path_str:
        return ""
    cleaned = path_str.strip().strip('"').strip("'")
    return cleaned.replace("/", "\\")


def get_next_provisional_number(session) -> str:
    """仮番号（整数4桁）の最大値+1を取得する"""
    cases = session.query(Case.case_number).all()
    max_num = 1000  # 初期値

    for (c_num,) in cases:
        if c_num and c_num.isdigit():
            try:
                val = int(c_num)
                if val > max_num:
                    max_num = val
            except:
                pass

    return str(max_num + 1)


def get_next_case_number_service() -> str:
    session = get_db_session()
    try:
        return get_next_provisional_number(session)
    finally:
        session.close()


def is_case_number_duplicate(case_number: str) -> bool:
    session = get_db_session()
    try:
        return (
            session.query(Case).filter(Case.case_number == case_number).first()
            is not None
        )
    finally:
        session.close()


def promote_to_formal_case_number(case_id: int) -> bool:
    """仮番号を正式番号(G番号)に昇格させる"""
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        if not case:
            return False

        current_num = case.case_number
        if current_num.startswith("G"):
            return True

        if current_num.isdigit():
            new_num = f"G{current_num}"
            existing = session.query(Case).filter(Case.case_number == new_num).first()
            if existing:
                return False

            case.case_number = new_num
            session.commit()
            return True
        return False
    except:
        session.rollback()
        return False
    finally:
        session.close()


# ==========================================
# ★異体字展開ロジック (名寄せ強化)
# ==========================================
def _expand_name_variants(name: str) -> Set[str]:
    """
    入力された氏名に対し、一般的な異体字（旧字・俗字）の組み合わせを展開して返す。
    例: "宮崎" -> {"宮崎", "宮﨑"}
    """
    if not name:
        return set()

    clean_base = name.replace(" ", "").replace("　", "")
    candidates = {clean_base}

    variant_map = {
        "崎": ["崎", "﨑", "嵜"],
        "﨑": ["崎", "﨑", "嵜"],
        "高": ["高", "髙"],
        "髙": ["高", "髙"],
        "沢": ["沢", "澤"],
        "澤": ["沢", "澤"],
        "斉": ["斉", "斎", "齋", "齊"],
        "斎": ["斉", "斎", "齋", "齊"],
        "辺": ["辺", "邉", "邊"],
        "浜": ["浜", "濱"],
        "濱": ["浜", "濱"],
        "吉": ["吉", "𠮷"],
        "𠮷": ["吉", "𠮷"],
        "富": ["富", "冨"],
        "冨": ["富", "冨"],
    }

    for char, variants in variant_map.items():
        if char in clean_base:
            current_list = list(candidates)
            for base_str in current_list:
                for v in variants:
                    candidates.add(base_str.replace(char, v))

    return candidates


# ==========================================
# 2. 案件 (Case) 操作 & 検索 (大幅強化版)
# ==========================================
def find_cases_by_attributes(
    client_name: Optional[str] = None, 
    deceased_name: Optional[str] = None,
    case_number: Optional[str] = None
) -> List[Dict[str, Any]]:
    session = get_db_session()
    results = []
    
    logger.info(f"🔎 FindCase Search: Num={case_number}, Client={client_name}, Dec={deceased_name}")

    try:
        query = session.query(Case).outerjoin(Case.deceased_ref)
        conditions = []

        if case_number:
            c_num = case_number.strip()
            conditions.append(Case.case_number.ilike(f"%{c_num}%"))

        if client_name:
            c_variants = _expand_name_variants(client_name)
            if c_variants:
                db_client_clean = func.replace(func.replace(Case.client_name, ' ', ''), '　', '')
                variant_conditions = [db_client_clean.contains(v) for v in c_variants]
                conditions.append(or_(*variant_conditions))

        if deceased_name:
            clean_search_key = deceased_name.replace(" ", "").replace("　", "")
            d_variants = _expand_name_variants(clean_search_key)
            full_name_db = Deceased.name_last + Deceased.name_first
            full_name_clean = func.replace(func.replace(full_name_db, ' ', ''), '　', '')
            
            v_conds = []
            for v in d_variants:
                v_conds.append(full_name_clean.contains(v))
                v_conds.append(Deceased.name_last.contains(v))
            
            conditions.append(or_(*v_conds))

        if not conditions:
            return []

        cases = query.filter(or_(*conditions)).limit(20).all()
        logger.info(f"   -> Hits: {len(cases)} cases found.")

        for c in cases:
            d_name = "未登録"
            d_date = None
            if c.deceased_ref:
                d_name = f"{c.deceased_ref.name_last} {c.deceased_ref.name_first}"
                d_date = c.deceased_ref.date_of_death

            results.append(
                {
                    "case_id": c.case_id,
                    "case_number": c.case_number,
                    "client_name": c.client_name,
                    "deceased_name": d_name,
                    "date_of_death": d_date,
                }
            )
        return results
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return []
    finally:
        session.close()


def add_new_case_for_client_registration(case_number, name, **kwargs) -> int:
    session = get_db_session()
    try:
        name_parts = name.replace("　", " ").split(" ", 1)
        lname = name_parts[0]
        fname = name_parts[1] if len(name_parts) > 1 else ""

        kana_last = kwargs.get("kana_last", "")
        kana_first = kwargs.get("kana_first", "")
        client_kana = f"{kana_last} {kana_first}".strip()

        new_case = Case(
            case_number=case_number,
            client_name=name,
            client_name_kana=client_kana,
            manager_id=kwargs.get("manager_id"),
            operator_id=kwargs.get("operator_id"),
            folder_path=normalize_folder_path(kwargs.get("folder_path", "")),
            contract_date=datetime.date.today(),
            current_status_id=1,
            created_at=datetime.datetime.now(),
        )
        session.add(new_case)
        session.flush()

        deceased = Deceased(
            case_id=new_case.case_id,
            name_last="",
            name_first="",
            relationship_type="本人",
        )
        session.add(deceased)
        session.flush()

        heir = Heir(
            deceased_id=deceased.id,
            name_last=lname,
            name_first=fname,
            name_last_kana=kana_last,
            name_first_kana=kana_first,
            relationship_type=kwargs.get("rel", ""),
            hometown=kwargs.get("hometown", ""),
            is_contracting_party=True,
        )
        session.add(heir)
        session.flush()

        if kwargs.get("pref") or kwargs.get("street"):
            addr = Address(
                zip_code=kwargs.get("zip_code"),
                prefecture=kwargs.get("pref"),
                city_ward_town=kwargs.get("city"),
                street_address=kwargs.get("street"),
                building_name=kwargs.get("building"),
            )
            session.add(addr)
            session.flush()
            session.add(
                H_AddressHistory(
                    heir_id=heir.id, address_id=addr.id, is_current_address=True
                )
            )

        session.commit()
        return deceased.id
    except Exception as e:
        session.rollback()
        logger.error(f"Registration Error: {e}")
        return -1
    finally:
        session.close()


def get_case_id_by_deceased_id(deceased_id: int) -> Optional[int]:
    session = get_db_session()
    try:
        d = session.query(Deceased).get(deceased_id)
        return d.case_id if d else None
    finally:
        session.close()


def update_case_folder_path(case_id: int, folder_path: str) -> bool:
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        if case:
            case.folder_path = normalize_folder_path(folder_path)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def update_case_number(case_id: int, new_number: str) -> bool:
    if not new_number:
        return False
    session = get_db_session()
    try:
        exists = (
            session.query(Case)
            .filter(Case.case_number == new_number, Case.case_id != case_id)
            .first()
        )
        if exists:
            return False

        case = session.query(Case).get(case_id)
        if case:
            case.case_number = new_number
            session.commit()
            return True
        return False
    except:
        session.rollback()
        return False
    finally:
        session.close()


def get_case_folder_path(case_id: int) -> Optional[str]:
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        return case.folder_path if case else None
    finally:
        session.close()


get_case_folder_path_service = get_case_folder_path


def get_case_by_id(case_id: int) -> Optional[Case]:
    session = get_db_session()
    try:
        return (
            session.query(Case)
            .options(joinedload(Case.deceased_ref).joinedload(Deceased.heirs))
            .filter(Case.case_id == case_id)
            .first()
        )
    finally:
        session.close()


def get_deceased_by_case_id(case_id: int) -> Optional[Deceased]:
    session = get_db_session()
    try:
        return session.query(Deceased).filter(Deceased.case_id == case_id).first()
    finally:
        session.close()


def get_deceased_by_id(deceased_id: int) -> Optional[Deceased]:
    session = get_db_session()
    try:
        return (
            session.query(Deceased).options(joinedload(Deceased.heirs)).get(deceased_id)
        )
    finally:
        session.close()


def delete_case_and_all_related_data(case_number: str) -> bool:
    session = get_db_session()
    try:
        case = session.query(Case).filter(Case.case_number == case_number).first()
        if case:
            session.query(IncomingNoteBuffer).filter(
                IncomingNoteBuffer.linked_case_id == case.case_id
            ).delete(synchronize_session=False)

            session.delete(case)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Delete Error: {e}")
        return False
    finally:
        session.close()


def update_case_assignment(
    case_id: int, manager_id: Optional[int], operator_id: Optional[int]
) -> bool:
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        if case:
            case.manager_id = manager_id
            case.operator_id = operator_id
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_all_users() -> Dict[int, str]:
    session = get_db_session()
    try:
        users = session.query(User).all()
        return {u.id: u.name for u in users}
    finally:
        session.close()


# ==========================================
# 3. 連絡先・住所関連 (参照用)
# ==========================================
def get_address_by_id(address_id: int) -> Optional[Address]:
    session = get_db_session()
    try:
        return session.query(Address).get(address_id)
    finally:
        session.close()


def get_address_info(target_type: str, target_id: int) -> dict:
    session = get_db_session()
    try:
        addr = None
        if target_type == "heir":
            link = (
                session.query(H_AddressHistory)
                .filter(
                    H_AddressHistory.heir_id == target_id,
                    H_AddressHistory.is_current_address == True,
                )
                .first()
            )
            if link:
                addr = session.query(Address).get(link.address_id)
        elif target_type == "deceased":
            d = session.query(Deceased).get(target_id)
            if d and d.last_address_id:
                addr = session.query(Address).get(d.last_address_id)

        if addr:
            return {
                "zip_code": addr.zip_code,
                "prefecture": addr.prefecture,
                "city_ward_town": addr.city_ward_town or "",
                "street_address": addr.street_address or "",
                "building_name": addr.building_name or "",
            }
        return {}
    finally:
        session.close()


def get_contact_info(target_type: str, target_id: int) -> List[dict]:
    session = get_db_session()
    try:
        contacts = []
        if target_type == "heir":
            links = (
                session.query(H_ContactLink)
                .filter(H_ContactLink.heir_id == target_id)
                .all()
            )
            for link in links:
                c = session.query(Contact).get(link.contact_id)
                if c:
                    contacts.append(
                        {
                            "id": c.id,
                            "type": c.type,
                            "value": c.value,
                            "sub_type": c.sub_type,
                        }
                    )
        elif target_type == "deceased":
            links = (
                session.query(D_ContactLink)
                .filter(D_ContactLink.deceased_id == target_id)
                .all()
            )
            for link in links:
                c = session.query(Contact).get(link.contact_id)
                if c:
                    contacts.append(
                        {
                            "id": c.id,
                            "type": c.type,
                            "value": c.value,
                            "sub_type": c.sub_type,
                        }
                    )
        return contacts
    finally:
        session.close()


# ==========================================
# 4. 被相続人・相続人 (CRUD)
# ==========================================
def update_deceased(deceased_id: int, **kwargs) -> bool:
    session = get_db_session()
    try:
        d = session.query(Deceased).get(deceased_id)
        if not d:
            return False

        d.name_last = kwargs.get("name_last", d.name_last)
        d.name_first = kwargs.get("name_first", d.name_first)
        d.name_last_kana = kwargs.get("kana_last", d.name_last_kana)
        d.name_first_kana = kwargs.get("kana_first", d.name_first_kana)

        if "hometown" in kwargs:
            d.hometown = kwargs["hometown"]

        # ★修正: 日付型のチェックを入れる
        if kwargs.get("dob"):
            val = kwargs["dob"]
            if isinstance(val, (datetime.date, datetime.datetime)):
                d.date_of_birth = val
            else:
                d.date_of_birth = parse_all_flexible_date(val)
        
        if kwargs.get("dod"):
            val = kwargs["dod"]
            if isinstance(val, (datetime.date, datetime.datetime)):
                d.date_of_death = val
            else:
                d.date_of_death = parse_all_flexible_date(val)

        # ★修正: 住所関連のキーが1つでも存在すれば更新処理に入る
        address_keys = ["last_pref", "last_city", "last_street", "last_building", "last_zip_code"]
        if any(k in kwargs for k in address_keys):
            if d.last_address_id:
                addr = session.query(Address).get(d.last_address_id)
                if addr:
                    addr.zip_code = kwargs.get("last_zip_code", addr.zip_code)
                    addr.prefecture = kwargs.get("last_pref", addr.prefecture)
                    addr.city_ward_town = kwargs.get("last_city", addr.city_ward_town)
                    addr.street_address = kwargs.get("last_street", addr.street_address)
                    addr.building_name = kwargs.get("last_building", addr.building_name)
            else:
                new_addr = Address(
                    zip_code=kwargs.get("last_zip_code", ""),
                    prefecture=kwargs.get("last_pref", ""),
                    city_ward_town=kwargs.get("last_city", ""),
                    street_address=kwargs.get("last_street", ""),
                    building_name=kwargs.get("last_building", ""),
                )
                session.add(new_addr)
                session.flush()
                d.last_address_id = new_addr.id

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Update Deceased Error: {e}")
        return False
    finally:
        session.close()


def add_heir(deceased_id: int, name: str, rel: str, **kwargs) -> int:
    session = get_db_session()
    try:
        parts = name.replace("　", " ").split(" ", 1)
        lname = parts[0]
        fname = parts[1] if len(parts) > 1 else ""
        
        # 日付変換
        dob_val = kwargs.get("dob")
        if dob_val and not isinstance(dob_val, (datetime.date, datetime.datetime)):
            dob_val = parse_all_flexible_date(dob_val)

        new_heir = Heir(
            deceased_id=deceased_id,
            name_last=lname,
            name_first=fname,
            name_last_kana=kwargs.get("kana_last"),
            name_first_kana=kwargs.get("kana_first"),
            relationship_type=rel,
            is_contracting_party=kwargs.get("is_contracting_party", False),
            occupation=kwargs.get("occupation"),
            hometown=kwargs.get("hometown"),
            date_of_birth=dob_val
        )
        session.add(new_heir)
        session.flush()

        # 住所登録
        street = kwargs.get("street", "")
        pref = kwargs.get("pref", "")
        
        if street or pref or kwargs.get("city") or kwargs.get("building"):
            zip_val = kwargs.get("zip_code", "")
            
            new_addr = Address(
                zip_code=zip_val,
                prefecture=pref,
                city_ward_town=kwargs.get("city", ""),
                street_address=street,
                building_name=kwargs.get("building", "")
            )
            session.add(new_addr)
            session.flush()
            
            session.add(H_AddressHistory(
                heir_id=new_heir.id,
                address_id=new_addr.id,
                is_current_address=True
            ))

        # 連絡先
        if "phone_contacts" in kwargs:
            for c_data in kwargs["phone_contacts"]:
                val = c_data.get("value")
                if val:
                    nc = Contact(value=val, type="PHONE", sub_type="Primary")
                    session.add(nc)
                    session.flush()
                    session.add(H_ContactLink(heir_id=new_heir.id, contact_id=nc.id))

        session.commit()
        return new_heir.id
    except Exception as e:
        session.rollback()
        logger.error(f"Add Heir Error: {e}")
        return -1
    finally:
        session.close()


def update_heir(heir_id: int, name: str, rel: str, **kwargs) -> bool:
    session = get_db_session()
    try:
        heir = session.query(Heir).get(heir_id)
        if not heir:
            return False

        parts = name.replace("　", " ").split(" ", 1)
        heir.name_last = parts[0]
        heir.name_first = parts[1] if len(parts) > 1 else ""
        heir.relationship_type = rel

        if "kana_last" in kwargs:
            heir.name_last_kana = kwargs["kana_last"]
        if "kana_first" in kwargs:
            heir.name_first_kana = kwargs["kana_first"]

        # ★修正: 日付型のチェックを入れる
        if kwargs.get("dob"):
            val = kwargs["dob"]
            if isinstance(val, (datetime.date, datetime.datetime)):
                heir.date_of_birth = val
            else:
                heir.date_of_birth = parse_all_flexible_date(val)
            
        if "occupation" in kwargs:
            heir.occupation = kwargs["occupation"]
        if "hometown" in kwargs:
            heir.hometown = kwargs["hometown"]

        # ★修正: 住所関連のキーが1つでも存在すれば更新処理に入る
        address_keys = ["pref", "city", "street", "building", "zip_code"]
        if any(k in kwargs for k in address_keys):
            link = (
                session.query(H_AddressHistory)
                .filter(
                    H_AddressHistory.heir_id == heir_id,
                    H_AddressHistory.is_current_address == True,
                )
                .first()
            )

            if link:
                addr = session.query(Address).get(link.address_id)
                addr.zip_code = kwargs.get("zip_code", addr.zip_code)
                addr.prefecture = kwargs.get("pref", addr.prefecture)
                addr.city_ward_town = kwargs.get("city", addr.city_ward_town)
                addr.street_address = kwargs.get("street", addr.street_address)
                addr.building_name = kwargs.get("building", addr.building_name)
            else:
                new_addr = Address(
                    zip_code=kwargs.get("zip_code", ""),
                    prefecture=kwargs.get("pref", ""),
                    city_ward_town=kwargs.get("city", ""),
                    street_address=kwargs.get("street", ""),
                    building_name=kwargs.get("building", ""),
                )
                session.add(new_addr)
                session.flush()
                session.add(
                    H_AddressHistory(
                        heir_id=heir.id, address_id=new_addr.id, is_current_address=True
                    )
                )

        if "phone_contacts" in kwargs or "email_contacts" in kwargs:
            session.query(H_ContactLink).filter(
                H_ContactLink.heir_id == heir_id
            ).delete()
            
            if "phone_contacts" in kwargs:
                for c_data in kwargs["phone_contacts"]:
                    val = c_data.get("value")
                    if val:
                        nc = Contact(value=val, type="PHONE", sub_type="Primary")
                        session.add(nc)
                        session.flush()
                        session.add(H_ContactLink(heir_id=heir.id, contact_id=nc.id))
            
            if "email_contacts" in kwargs:
                for c_data in kwargs["email_contacts"]:
                    val = c_data.get("value")
                    if val:
                        nc = Contact(value=val, type="EMAIL", sub_type="Primary")
                        session.add(nc)
                        session.flush()
                        session.add(H_ContactLink(heir_id=heir.id, contact_id=nc.id))

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Update Heir Error: {e}")
        return False
    finally:
        session.close()


def delete_heir(heir_id: int) -> bool:
    session = get_db_session()
    try:
        heir = session.query(Heir).get(heir_id)
        if heir:
            session.delete(heir)
            session.commit()
            return True
        return False
    finally:
        session.close()

def sync_heir_list(deceased_id: int, heir_data_list: List[Dict[str, Any]]) -> Dict[str, int]:
    session = get_db_session()
    result = {"added": 0, "updated": 0, "deleted": 0}
    
    try:
        existing_heirs = session.query(Heir).filter(Heir.deceased_id == deceased_id).all()
        existing_ids = {h.id for h in existing_heirs}
        
        incoming_ids = set()
        
        for data in heir_data_list:
            h_id = data.get("id")
            
            full_name = data.get("name", "").strip().replace("　", " ")
            parts = full_name.split(" ", 1)
            lname = parts[0]
            fname = parts[1] if len(parts) > 1 else ""
            rel = data.get("relationship", "")
            role_flg = True if data.get("role") == "契約者" else False
            
            dob = data.get("dob")
            if hasattr(dob, 'date'): dob = dob.date()
            if pd.isnull(dob): dob = None

            if h_id and h_id in existing_ids:
                incoming_ids.add(h_id)
                target = session.query(Heir).get(h_id)
                target.name_last = lname
                target.name_first = fname
                target.relationship_type = rel
                target.date_of_birth = dob
                target.is_contracting_party = role_flg
                result["updated"] += 1
            else:
                if not lname: continue
                new_h = Heir(
                    deceased_id=deceased_id,
                    name_last=lname,
                    name_first=fname,
                    relationship_type=rel,
                    date_of_birth=dob,
                    is_contracting_party=role_flg
                )
                session.add(new_h)
                result["added"] += 1
        
        ids_to_delete = existing_ids - incoming_ids
        if ids_to_delete:
            session.query(Heir).filter(Heir.id.in_(ids_to_delete)).delete(synchronize_session=False)
            result["deleted"] = len(ids_to_delete)
            
        session.commit()
        return result

    except Exception as e:
        session.rollback()
        logger.error(f"Sync Heir List Error: {e}")
        raise e
    finally:
        session.close()


def search_zip_by_address_api(address: str) -> Optional[str]:
    if not address:
        return None
    try:
        res = requests.get(
            "http://geoapi.heartrails.com/api/json",
            params={"method": "suggest", "matching": "like", "keyword": address},
            timeout=5,
        )
        data = res.json()
        if data and data.get("response") and data["response"].get("location"):
            p = data["response"]["location"][0].get("postal")
            if p:
                return f"{p[:3]}-{p[3:]}"
        return None
    except Exception:
        return None


def search_address_by_zip_api(zip_code: str) -> Optional[dict]:
    if not zip_code:
        return None
    try:
        res = requests.get(
            f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zip_code.replace('-', '')}",
            timeout=5,
        )
        data = res.json()
        if data and data.get("results"):
            r = data["results"][0]
            return {
                "prefecture": r["address1"],
                "city_ward_town": r["address2"],
                "street_address": r["address3"],
            }
        return {}
    except:
        return None