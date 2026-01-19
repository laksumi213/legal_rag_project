# src/services/kintone_sync_service.py

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address,
    Case,
    Contact,
    Deceased,
    H_AddressHistory,
    H_ContactLink,
    Heir,
    User,
)
from src.utils.date_utils import parse_all_flexible_date

logger = logging.getLogger(__name__)


def get_kintone_data_as_dict(case_id: int) -> Optional[Dict[str, Any]]:
    """
    Kintoneブックマークレット（書き込み用）が期待する形式の辞書を作成する
    """
    db = DatabaseManager()
    session = db._get_session()

    try:
        case = session.query(Case).filter_by(case_id=case_id).first()
        if not case:
            return None

        # 案件情報の抽出
        # ... (既存の氏名などの抽出ロジック) ...

        # ★ここが重要: システム独自のデータをKintoneフィールドへマッピング
        # ブックマークレット側のフィールドコードに合わせてキーを設定します

        kintone_payload = {
            "顧客コード_2": case.case_number,  # 仮番号 or G番号
            "顧客名": case.client_name,
            "顧客名(ふりがな)": case.client_name_kana,
            # 紹介元情報 (今回追加)
            "SOL案件No.（日興）": case.sol_case_number,
            "支店名（日興）": case.referral_sec_branch_name,
            "担当者（日興）": case.referral_sec_rep_name,
            # ※Kintoneに電話番号フィールドがない場合、備考欄などに転記するか、
            #   あるいは「紹介元電話番号」というフィールドをKintone側に追加することを推奨します。
            #   ここでは一旦、備考などに含める例とします。
            "備考": f"【紹介元電話】{case.referral_sec_phone}"
            if case.referral_sec_phone
            else "",
            # 日付
            "紹介日": str(case.introduction_date) if case.introduction_date else "",
        }

        return kintone_payload

    except Exception as e:
        logger.error(f"Kintone data build error: {e}")
        return None
    finally:
        session.close()


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
        k_rec_id_raw = json_data.get("$id") or json_data.get("record_id")
        k_record_id = int(k_rec_id_raw) if k_rec_id_raw else None
        case_num = (
            json_data.get("顧客コード", "").strip()
            or json_data.get("顧客コード_2", "").strip()
        )

        client_name_raw = json_data.get("顧客名", "").replace("　", " ").strip()
        client_kana_raw = (
            json_data.get("顧客名(ふりがな)", "").replace("　", " ").strip()
        )

        deceased_name_raw = json_data.get("被相続人名", "").replace("　", " ").strip()
        deceased_kana_raw = (
            json_data.get("被相続人名（ふりがな）", "").replace("　", " ").strip()
        )

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
                created_at=datetime.now(),
            )
            session.add(case)
            session.flush()

        # 3. 案件情報の更新 (上書き)
        # レコード番号の保存
        if k_record_id:
            case.kintone_record_id = k_record_id

        case.client_name = client_name_raw
        case.client_name_kana = client_kana_raw
        case.sol_case_number = sol_no
        case.introduction_date = intro_date
        case.consent_date = consent_date

        # 紹介元情報
        case.referral_sec_branch_name = (
            json_data.get("支店名（日興）") or json_data.get("支店名（大和）") or ""
        )
        case.referral_sec_rep_name = (
            json_data.get("担当者（日興）") or json_data.get("担当者（大和）") or ""
        )

        # 担当者紐付け (名前の部分一致検索)
        if mgr_name:
            u = session.query(User).filter(User.name.contains(mgr_name)).first()
            if u:
                case.manager_id = u.id
        if opr_name:
            u = session.query(User).filter(User.name.contains(opr_name)).first()
            if u:
                case.operator_id = u.id

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
        contractor = (
            session.query(Heir)
            .filter(Heir.deceased_id == deceased.id, Heir.is_contracting_party == True)
            .first()
        )

        if not contractor:
            contractor = Heir(
                deceased_id=deceased.id,
                is_contracting_party=True,
                relationship_type="相談者",
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

        addr_link = (
            session.query(H_AddressHistory)
            .filter(
                H_AddressHistory.heir_id == contractor.id,
                H_AddressHistory.is_current_address == True,
            )
            .first()
        )

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
                zip_code=zip_code, prefecture=pref, street_address=street
            )
            session.add(new_addr)
            session.flush()
            session.add(
                H_AddressHistory(
                    heir_id=contractor.id,
                    address_id=new_addr.id,
                    is_current_address=True,
                )
            )

        # 7. 電話番号 (TEL) の取込
        # JSONの "TEL" キーから取得し、カンマ区切りなどで複数ある場合は分割して登録
        tel_str = json_data.get("TEL", "")
        if tel_str:
            # 既存の電話番号を一度クリアしてから再登録（完全同期）
            # H_ContactLink経由で紐付いているPHONEタイプのContactを削除
            existing_links = session.query(H_ContactLink).filter(
                H_ContactLink.heir_id == contractor.id
            ).all()
            
            for link in existing_links:
                contact = session.query(Contact).get(link.contact_id)
                if contact and contact.type == "PHONE":
                    session.delete(contact)
                    session.delete(link)
            
            # 新規登録
            # 全角数字やハイフンのゆらぎはそのまま保存するか、正規化するかは要件次第だが、
            # ここではカンマ区切りでの複数登録に対応
            tels = tel_str.replace("、", ",").split(",")
            for i, t in enumerate(tels):
                clean_tel = t.strip()
                if clean_tel:
                    c = Contact(
                        value=clean_tel,
                        type="PHONE",
                        sub_type="Primary" if i == 0 else "Secondary",
                    )
                    session.add(c)
                    session.flush()
                    session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))

        # 8. メールアドレス
        mail_str = json_data.get("メールアドレス", "")
        if mail_str:
             # 既存メール削除 (簡易)
            existing_links = session.query(H_ContactLink).filter(
                H_ContactLink.heir_id == contractor.id
            ).all()
            
            for link in existing_links:
                contact = session.query(Contact).get(link.contact_id)
                if contact and contact.type == "EMAIL":
                    session.delete(contact)
                    session.delete(link)

            c = Contact(value=mail_str.strip(), type="EMAIL", sub_type="Primary")
            session.add(c)
            session.flush()
            session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))

        session.commit()
        return case.case_id

    except Exception as e:
        session.rollback()
        logger.error(f"Import Error: {e}")
        return -1
    finally:
        session.close()