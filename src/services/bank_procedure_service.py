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
