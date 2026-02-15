# src/services/dispatch_service.py
from typing import Any, Dict

# 郵便番号検索サービスをインポート
from legal_system.services.deceased_service import search_zip_by_address_api


def determine_base_from_branch(branch_name: str) -> str:
    """
    紹介元支店名から担当拠点を自動判定するロジック
    """
    if not branch_name:
        return "未定"

    name = branch_name.replace("支店", "").strip()

    # マスタールール (本来はDBかJSONファイルで管理推奨)
    rules = {
        "横浜拠点": ["横浜", "川崎", "港南台", "鎌倉", "藤沢"],
        "新宿拠点": ["新宿", "中野", "杉並", "池袋"],
        "渋谷拠点": ["渋谷", "世田谷", "目黒"],
        "立川拠点": ["立川", "八王子", "町田"],
        "大宮拠点": ["大宮", "浦和", "川口"],
        "千葉拠点": ["千葉", "船橋", "柏"],
    }

    for base, keywords in rules.items():
        for kw in keywords:
            if kw in name:
                return base

    return "本店"  # デフォルト


def generate_kintone_json_payload(
    case_obj, deceased_obj, heir_obj, address_obj
) -> Dict[str, Any]:
    """
    DBオブジェクトからKintoneブックマークレット用のJSONを生成する
    """
    # 氏名結合
    c_name = f"{case_obj.client_name}".strip()
    c_kana = f"{case_obj.client_name_kana}".strip()

    d_name = ""
    d_kana = ""
    if deceased_obj:
        d_name = f"{deceased_obj.name_last}　{deceased_obj.name_first}".strip()
        # "None" 文字列が結合されないように修正
        d_kana_parts = []
        if deceased_obj.name_last_kana:
            d_kana_parts.append(deceased_obj.name_last_kana)
        if deceased_obj.name_first_kana:
            d_kana_parts.append(deceased_obj.name_first_kana)
        d_kana = "　".join(d_kana_parts)

    # 住所結合
    addr_full = ""
    zip_code = ""
    if address_obj:
        zip_code = address_obj.zip_code

        # "None" 文字列が結合されないように修正
        addr_parts = [
            address_obj.prefecture,
            address_obj.city_ward_town,
            address_obj.street_address,
        ]
        addr_full = "".join(p for p in addr_parts if p).strip()
        if address_obj.building_name:
            addr_full += f" {address_obj.building_name.strip()}"

        # 郵便番号がなければ住所から検索
        if not zip_code and addr_full:
            zip_code = search_zip_by_address_api(addr_full) or ""

    # 電話番号（Caseに保存されている紹介元電話番号も備考へ）
    ref_phone_note = ""
    if case_obj.referral_sec_phone:
        ref_phone_note = f"\n【紹介元TEL】{case_obj.referral_sec_phone}"

    return {
        "顧客コード_2": case_obj.case_number,
        "顧客名": c_name,
        "顧客名(ふりがな)": c_kana,
        "郵便番号": zip_code or "",
        "住所": addr_full.strip(),
        # 被相続人
        "被相続人名": d_name,
        "被相続人名（ふりがな）": d_kana,
        "相続開始日": str(deceased_obj.date_of_death)
        if deceased_obj and deceased_obj.date_of_death
        else "",
        # 紹介情報
        "SOL案件No.（日興）": case_obj.sol_case_number or "",
        "支店名（日興）": case_obj.referral_sec_branch_name or "",
        "担当者（日興）": case_obj.referral_sec_rep_name or "",
        "紹介日": str(case_obj.introduction_date) if case_obj.introduction_date else "",
        # 備考などに電話番号を入れる
        "備考": ref_phone_note,
    }
