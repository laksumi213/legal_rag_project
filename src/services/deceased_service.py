# src/services/deceased_service.py

import datetime
import logging
import re
from typing import Any, Dict, List, Optional, Set

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
# ★追加: 異体字展開ロジック (名寄せ強化)
# ==========================================
def _expand_name_variants(name: str) -> Set[str]:
    """
    入力された氏名に対し、一般的な異体字（旧字・俗字）の組み合わせを展開して返す。
    例: "宮崎" -> {"宮崎", "宮﨑"}
    """
    if not name:
        return set()

    # ベースの正規化（スペース除去）
    clean_base = name.replace(" ", "").replace("　", "")
    candidates = {clean_base}

    # 異体字マップ (必要に応じて追加してください)
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

    # 各文字について異体字があれば候補を増殖させる
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
    """
    属性検索（名寄せ）
    - 異体字対応 (宮崎⇔宮﨑)
    - 姓名分離検索 (Deceasedテーブル対応)
    - スペース無視検索
    """
    session = get_db_session()
    results = []
    
    # 検索キーのログ出力 (デバッグ用)
    logger.info(f"🔎 FindCase Search: Num={case_number}, Client={client_name}, Dec={deceased_name}")

    try:
        query = session.query(Case).outerjoin(Case.deceased_ref)
        conditions = []

        # 1. 案件番号検索
        if case_number:
            c_num = case_number.strip()
            conditions.append(Case.case_number.ilike(f"%{c_num}%"))

        # 2. 依頼者名検索 (Case.client_name: 氏名結合文字列)
        if client_name:
            c_variants = _expand_name_variants(client_name)
            if c_variants:
                # DB側のスペースを除去したカラムと比較
                db_client_clean = func.replace(func.replace(Case.client_name, ' ', ''), '　', '')
                variant_conditions = [db_client_clean.contains(v) for v in c_variants]
                conditions.append(or_(*variant_conditions))

        # 3. 被相続人名検索 (Deceased: 姓・名 分離カラム)
        # ★ここを強化: 入力文字列を姓と名に分割して、それぞれで異体字マッチをかける
        if deceased_name:
            # 入力文字列をスペースで分割 ("宮崎 修武" -> ["宮崎", "修武"])
            parts = deceased_name.replace("　", " ").split(" ")
            parts = [p for p in parts if p] # 空要素削除

            if len(parts) >= 2:
                # 姓と名が分かれている場合 -> 姓マッチ AND 名マッチ
                last_input = parts[0]   # "宮崎"
                first_input = "".join(parts[1:]) # "修武"
                
                last_variants = _expand_name_variants(last_input)   # {"宮崎", "宮﨑"}
                first_variants = _expand_name_variants(first_input) # {"修武"}

                # 姓のいずれかに一致
                last_cond = or_(*[Deceased.name_last.contains(v) for v in last_variants])
                # 名のいずれかに一致
                first_cond = or_(*[Deceased.name_first.contains(v) for v in first_variants])
                
                # (姓マッチ AND 名マッチ) を条件に追加
                conditions.append(and_(last_cond, first_cond))
                
                logger.info(f"   -> Split Search: Last={last_variants}, First={first_variants}")

            else:
                # スペースがない場合 ("宮崎修武") -> 結合カラムで検索、または片方検索
                d_variants = _expand_name_variants(deceased_name)
                
                # DB上で結合した仮想カラム
                full_name_db = Deceased.name_last + Deceased.name_first
                full_name_clean = func.replace(func.replace(full_name_db, ' ', ''), '　', '')
                
                # 結合名 OR 姓のみ OR 名のみ
                v_conds = []
                for v in d_variants:
                    v_conds.append(full_name_clean.contains(v))
                    v_conds.append(Deceased.name_last.contains(v)) # 苗字だけ入力された場合用
                
                conditions.append(or_(*v_conds))

        if not conditions:
            return []

        # いずれかの条件にヒットするものを取得
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
    """手動登録画面からの案件登録処理"""
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
    """
    案件とその関連データを削除する。
    IncomingNoteBuffer等の外部キー制約があるデータを先に削除する。
    """
    session = get_db_session()
    try:
        case = session.query(Case).filter(Case.case_number == case_number).first()
        if case:
            # ★追加: 外部キー制約回避のため、先に関連するIncomingNoteBufferを削除
            session.query(IncomingNoteBuffer).filter(
                IncomingNoteBuffer.linked_case_id == case.case_id
            ).delete(synchronize_session=False)

            # 案件本体の削除 (cascade設定により紐づくDeceased等は自動削除される想定)
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

        # ★追加: 本籍地
        if "hometown" in kwargs:
            d.hometown = kwargs["hometown"]

        if kwargs.get("dob"):
            d.date_of_birth = parse_all_flexible_date(kwargs["dob"])
        if kwargs.get("dod"):
            d.date_of_death = parse_all_flexible_date(kwargs["dod"])

        if (
            kwargs.get("last_pref")
            or kwargs.get("last_city")
            or kwargs.get("last_street")
        ):
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
                    zip_code=kwargs.get("last_zip_code"),
                    prefecture=kwargs.get("last_pref"),
                    city_ward_town=kwargs.get("last_city"),
                    street_address=kwargs.get("last_street"),
                    building_name=kwargs.get("last_building"),
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

        new_heir = Heir(
            deceased_id=deceased_id,
            name_last=lname,
            name_first=fname,
            name_last_kana=kwargs.get("kana_last"),
            name_first_kana=kwargs.get("kana_first"),
            relationship_type=rel,
            is_contracting_party=kwargs.get("is_contracting_party", False),
        )
        session.add(new_heir)
        session.flush()
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

        if kwargs.get("dob"):
            heir.date_of_birth = parse_all_flexible_date(kwargs["dob"])

        if kwargs.get("pref") or kwargs.get("city"):
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
                addr.street_address = kwargs.get("street", "")
                addr.building_name = kwargs.get("building", "")
            else:
                new_addr = Address(
                    zip_code=kwargs.get("zip_code"),
                    prefecture=kwargs.get("pref"),
                    city_ward_town=kwargs.get("city"),
                    street_address=kwargs.get("street"),
                    building_name=kwargs.get("building"),
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


# ==========================================
# 5. 住所・郵便番号検索API
# ==========================================
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