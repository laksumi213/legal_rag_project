from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import joinedload

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import Case, Deceased, FinancialAsset
from src.legal_system.utils.pdf_utils import apply_coordinates_to_pdf


@dataclass(frozen=True)
class GeneratedPdf:
    filename: str
    pdf_bytes: bytes


class BankProcedureService:
    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self._db = db or DatabaseManager()

    def generate_mizuho_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        session = self._db._get_session()
        try:
            case = session.get(
                Case,
                case_id,
                options=[
                    joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
                ],
            )
            if case is None or case.deceased_ref is None:
                raise ValueError("案件情報（被相続人）が見つかりません")

            asset = (
                session.query(FinancialAsset)
                .options(
                    joinedload(FinancialAsset.bank_ref),
                    joinedload(FinancialAsset.branch_ref),
                    joinedload(FinancialAsset.account_type_ref),
                )
                .filter(
                    FinancialAsset.id == financial_asset_id,
                    FinancialAsset.case_id == case_id,
                )
                .first()
            )
            if asset is None:
                raise ValueError("対象口座が見つかりません")

            representative_heir = next(
                (h for h in (case.deceased_ref.heirs or []) if h.is_contracting_party),
                None,
            )
            if representative_heir is None and (case.deceased_ref.heirs or []):
                representative_heir = case.deceased_ref.heirs[0]

            replacement_map: Dict[str, str] = {
                "被相続人氏名": f"{case.deceased_ref.name_last or ''} {case.deceased_ref.name_first or ''}".strip(),
                "相続人氏名": (
                    f"{representative_heir.name_last or ''} {representative_heir.name_first or ''}".strip()
                    if representative_heir
                    else ""
                ),
                "支店名": asset.branch_ref.branch_name if asset.branch_ref else "",
                "口座番号": asset.account_number or "",
                "作成日": created_on.strftime("%Y/%m/%d"),
                "死亡日": case.deceased_ref.date_of_death.strftime("%Y/%m/%d")
                if case.deceased_ref.date_of_death
                else "",
            }

            coords = _mizuho_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"みずほ銀行_残高証明_{case.case_number}_{created_on.strftime('%Y%m%d')}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())
        finally:
            session.close()

    def generate_yucho_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        session = self._db._get_session()
        try:
            case = session.get(
                Case,
                case_id,
                options=[
                    joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
                ],
            )
            if case is None or case.deceased_ref is None:
                raise ValueError("案件情報（被相続人）が見つかりません")

            asset = (
                session.query(FinancialAsset)
                .options(
                    joinedload(FinancialAsset.bank_ref),
                    joinedload(FinancialAsset.branch_ref),
                    joinedload(FinancialAsset.account_type_ref),
                )
                .filter(
                    FinancialAsset.id == financial_asset_id,
                    FinancialAsset.case_id == case_id,
                )
                .first()
            )
            if asset is None:
                raise ValueError("対象口座が見つかりません")

            replacement_map: Dict[str, str] = {
                "被相続人氏名": f"{case.deceased_ref.name_last or ''} {case.deceased_ref.name_first or ''}".strip(),
                "支店名": asset.branch_ref.branch_name if asset.branch_ref else "",
                "口座番号": asset.account_number or "",
                "作成日": created_on.strftime("%Y/%m/%d"),
            }

            coords = _yucho_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"ゆうちょ銀行_残高証明_{case.case_number}_{created_on.strftime('%Y%m%d')}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())
        finally:
            session.close()

    def generate_mufg_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        session = self._db._get_session()
        try:
            case = session.get(
                Case,
                case_id,
                options=[
                    joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
                ],
            )
            if case is None or case.deceased_ref is None:
                raise ValueError("案件情報（被相続人）が見つかりません")

            asset = (
                session.query(FinancialAsset)
                .options(
                    joinedload(FinancialAsset.bank_ref),
                    joinedload(FinancialAsset.branch_ref),
                    joinedload(FinancialAsset.account_type_ref),
                )
                .filter(
                    FinancialAsset.id == financial_asset_id,
                    FinancialAsset.case_id == case_id,
                )
                .first()
            )
            if asset is None:
                raise ValueError("対象口座が見つかりません")

            replacement_map: Dict[str, str] = {
                "被相続人氏名": f"{case.deceased_ref.name_last or ''} {case.deceased_ref.name_first or ''}".strip(),
                "支店名": asset.branch_ref.branch_name if asset.branch_ref else "",
                "支店コード": asset.branch_ref.branch_code.zfill(3)
                if asset.branch_ref and asset.branch_ref.branch_code
                else "",
                "口座番号": asset.account_number or "",
                "口座種別": asset.account_type_ref.type_name
                if asset.account_type_ref
                else "普通",
                "作成日": created_on.strftime("%Y/%m/%d"),
            }

            coords = _mufg_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"三菱UFJ銀行_残高証明_{case.case_number}_{created_on.strftime('%Y%m%d')}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())
        finally:
            session.close()

    def generate_ja_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        session = self._db._get_session()
        try:
            case = session.get(
                Case,
                case_id,
                options=[
                    joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
                ],
            )
            if case is None or case.deceased_ref is None:
                raise ValueError("案件情報（被相続人）が見つかりません")

            asset = (
                session.query(FinancialAsset)
                .options(
                    joinedload(FinancialAsset.bank_ref),
                    joinedload(FinancialAsset.branch_ref),
                    joinedload(FinancialAsset.account_type_ref),
                )
                .filter(
                    FinancialAsset.id == financial_asset_id,
                    FinancialAsset.case_id == case_id,
                )
                .first()
            )
            if asset is None:
                raise ValueError("対象口座が見つかりません")

            representative_heir = next(
                (h for h in (case.deceased_ref.heirs or []) if h.is_contracting_party),
                None,
            )
            if representative_heir is None and (case.deceased_ref.heirs or []):
                representative_heir = case.deceased_ref.heirs[0]

            replacement_map: Dict[str, str] = {
                "被相続人氏名": f"{case.deceased_ref.name_last or ''} {case.deceased_ref.name_first or ''}".strip(),
                "被相続人住所": "",
                "相続人氏名": (
                    f"{representative_heir.name_last or ''} {representative_heir.name_first or ''}".strip()
                    if representative_heir
                    else ""
                ),
                "相続人住所": "",
                "死亡日": case.deceased_ref.date_of_death.strftime("%Y/%m/%d")
                if case.deceased_ref.date_of_death
                else "",
            }

            coords = _ja_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"JA銀行_残高証明_{case.case_number}_{created_on.strftime('%Y%m%d')}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())
        finally:
            session.close()


def _mizuho_balance_certificate_coordinates(
    replacement_map: Dict[str, str],
) -> List[Dict[str, object]]:
    return [
        {
            "page": 1,
            "x": 148.0,
            "y": 277.0,
            "value": replacement_map.get("被相続人氏名", ""),
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 87.0,
            "y": 267.0,
            "value": "✓",
            "font_size": 14.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 89.0,
            "y": 115.0,
            "value": "✓",
            "font_size": 12.0,
            "color": "black",
        },
    ]


def _yucho_balance_certificate_coordinates(
    replacement_map: Dict[str, str],
) -> List[Dict[str, object]]:
    return [
        {
            "page": 1,
            "x": 60.0,
            "y": 120.0,
            "value": replacement_map.get("被相続人氏名", ""),
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 60.0,
            "y": 140.0,
            "value": replacement_map.get("作成日", ""),
            "font_size": 10.0,
            "color": "black",
        },
    ]


def _mufg_balance_certificate_coordinates(
    replacement_map: Dict[str, str],
) -> List[Dict[str, object]]:
    coords = [
        {
            "page": 1,
            "x": 30.0,
            "y": 265.5,
            "value": "194",
            "font_size": 8.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 46.0,
            "y": 265.5,
            "value": "0022",
            "font_size": 8.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 47.5,
            "y": 260.0,
            "value": "〇",
            "font_size": 15.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 31.0,
            "y": 257.0,
            "value": "東京",
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 65.0,
            "y": 257.0,
            "value": "町田市",
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 31.0,
            "y": 248.0,
            "value": "森野一丁目22番5号",
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 135.0,
            "y": 258.0,
            "value": "042",
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 135.0,
            "y": 250.0,
            "value": "710",
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 156.0,
            "y": 250.0,
            "value": "6178",
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 31.0,
            "y": 240.0,
            "value": "相続手続支援センター町田有限責任事業組合　組合員",
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 31.0,
            "y": 235.0,
            "value": "株式会社プロフィット・ワン　職務執行者　大貫利一",
            "font_size": 10.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 150.0,
            "y": 235.0,
            "value": replacement_map.get("被相続人氏名", ""),
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 22.0,
            "y": 53.0,
            "value": "✓",
            "font_size": 8.0,
            "color": "black",
        },
    ]

    branch_code = replacement_map.get("支店コード", "")
    if branch_code:
        coords.extend(
            [
                {
                    "page": 1,
                    "x": 9.0,
                    "y": 215.0,
                    "value": branch_code[0] if len(branch_code) > 0 else "",
                    "font_size": 11.0,
                    "color": "black",
                },
                {
                    "page": 1,
                    "x": 16.0,
                    "y": 215.0,
                    "value": branch_code[1] if len(branch_code) > 1 else "",
                    "font_size": 11.0,
                    "color": "black",
                },
                {
                    "page": 1,
                    "x": 24.0,
                    "y": 215.0,
                    "value": branch_code[2] if len(branch_code) > 2 else "",
                    "font_size": 11.0,
                    "color": "black",
                },
            ]
        )

    coords.append(
        {
            "page": 1,
            "x": 35.0,
            "y": 215.0,
            "value": replacement_map.get("支店名", ""),
            "font_size": 11.0,
            "color": "black",
        }
    )

    account_type = replacement_map.get("口座種別", "")
    if "普通" in account_type:
        coords.append(
            {
                "page": 1,
                "x": 72.0,
                "y": 217.0,
                "value": "✓",
                "font_size": 8.0,
                "color": "black",
            }
        )
    else:
        coords.append(
            {
                "page": 1,
                "x": 72.0,
                "y": 214.0,
                "value": "✓",
                "font_size": 8.0,
                "color": "black",
            }
        )
        coords.append(
            {
                "page": 1,
                "x": 85.0,
                "y": 214.5,
                "value": account_type.replace("預金", ""),
                "font_size": 8.0,
                "color": "black",
            }
        )

    account_number = replacement_map.get("口座番号", "").zfill(7)
    x_positions = [114.0, 122.0, 130.0, 138.0, 145.5, 153.0, 161.0]
    for i, digit in enumerate(account_number[:7]):
        coords.append(
            {
                "page": 1,
                "x": x_positions[i],
                "y": 215.0,
                "value": digit,
                "font_size": 11.0,
                "color": "black",
            }
        )

    coords.append(
        {
            "page": 1,
            "x": 192.0,
            "y": 215.0,
            "value": "1",
            "font_size": 11.0,
            "color": "black",
        }
    )

    return coords


def _ja_balance_certificate_coordinates(
    replacement_map: Dict[str, str],
) -> List[Dict[str, object]]:
    coords = [
        {
            "page": 1,
            "x": 110.0,
            "y": 222.0,
            "value": replacement_map.get("被相続人住所", ""),
            "font_size": 8.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 110.0,
            "y": 210.0,
            "value": replacement_map.get("被相続人氏名", ""),
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 110.0,
            "y": 199.0,
            "value": replacement_map.get("相続人住所", ""),
            "font_size": 8.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 110.0,
            "y": 187.0,
            "value": replacement_map.get("相続人氏名", ""),
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 91.0,
            "y": 164.0,
            "value": "✓",
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 58.0,
            "y": 141.0,
            "value": replacement_map.get("被相続人氏名", ""),
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 36.0,
            "y": 124.0,
            "value": "✓",
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 36.0,
            "y": 118.0,
            "value": "✓",
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 36.0,
            "y": 112.0,
            "value": "✓",
            "font_size": 12.0,
            "color": "black",
        },
    ]

    death_date_parts = replacement_map.get("死亡日", "").split("/")
    if len(death_date_parts) == 3:
        coords.extend(
            [
                {
                    "page": 1,
                    "x": 39.0,
                    "y": 135.0,
                    "value": death_date_parts[0],
                    "font_size": 10.0,
                    "color": "black",
                },
                {
                    "page": 1,
                    "x": 61.0,
                    "y": 135.0,
                    "value": death_date_parts[1],
                    "font_size": 10.0,
                    "color": "black",
                },
                {
                    "page": 1,
                    "x": 78.0,
                    "y": 135.0,
                    "value": death_date_parts[2],
                    "font_size": 10.0,
                    "color": "black",
                },
            ]
        )

    return coords
