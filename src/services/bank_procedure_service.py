# src/services/bank_procedure_service.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

# プロジェクト内の新構成モジュールをインポート
from database.manager import DatabaseManager
from models.tables import Case, Deceased, FinancialAsset
from utils.pdf_utils import apply_coordinates_to_pdf


@dataclass(frozen=True)
class GeneratedPdf:
    filename: str
    pdf_bytes: bytes


class BankProcedureService:
    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        # シングルトンの DatabaseManager を取得
        self.db = db or DatabaseManager()

    def generate_mizuho_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        """みずほ銀行の残高証明書PDFを生成"""
        with self.db.get_session() as session:
            case = session.get(
                Case,
                case_id,
                options=[
                    joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
                ],
            )
            if case is None or case.deceased_ref is None:
                raise ValueError("案件情報（被相続人）が見つかりません")

            asset = session.scalar(
                select(FinancialAsset)
                .options(
                    joinedload(FinancialAsset.bank_ref),
                    joinedload(FinancialAsset.branch_ref),
                    joinedload(FinancialAsset.account_type_ref),
                )
                .filter(
                    FinancialAsset.id == financial_asset_id,
                    FinancialAsset.case_id == case_id,
                )
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
                "作成日": created_on.strftime("%Y/%m/%d")
                if isinstance(created_on, date)
                else str(created_on),
                "死亡日": case.deceased_ref.date_of_death.strftime("%Y/%m/%d")
                if case.deceased_ref.date_of_death
                else "",
            }

            coords = _mizuho_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"みずほ銀行_残高証明_{case.case_number}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())

    def generate_yucho_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        """ゆうちょ銀行の残高証明書PDFを生成"""
        with self.db.get_session() as session:
            case = session.get(Case, case_id, options=[joinedload(Case.deceased_ref)])
            asset = session.get(
                FinancialAsset,
                financial_asset_id,
                options=[joinedload(FinancialAsset.branch_ref)],
            )

            replacement_map: Dict[str, str] = {
                "被相続人氏名": f"{case.deceased_ref.name_last or ''} {case.deceased_ref.name_first or ''}".strip(),
                "作成日": created_on.strftime("%Y/%m/%d")
                if isinstance(created_on, date)
                else str(created_on),
            }

            coords = _yucho_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"ゆうちょ銀行_残高証明_{case.case_number}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())

    def generate_mufg_balance_certificate_pdf(
        self,
        case_id: int,
        financial_asset_id: int,
        template_path: str,
        created_on: date,
    ) -> GeneratedPdf:
        """三菱UFJ銀行の残高証明書PDFを生成"""
        with self.db.get_session() as session:
            case = session.get(Case, case_id, options=[joinedload(Case.deceased_ref)])
            asset = session.get(
                FinancialAsset,
                financial_asset_id,
                options=[
                    joinedload(FinancialAsset.branch_ref),
                    joinedload(FinancialAsset.account_type_ref),
                ],
            )

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
                "作成日": created_on.strftime("%Y/%m/%d")
                if isinstance(created_on, date)
                else str(created_on),
            }

            coords = _mufg_balance_certificate_coordinates(replacement_map)
            original_pdf_bytes = Path(template_path).read_bytes()
            out_stream = apply_coordinates_to_pdf(original_pdf_bytes, coords)

            filename = f"三菱UFJ銀行_残高証明_{case.case_number}.pdf"
            return GeneratedPdf(filename=filename, pdf_bytes=out_stream.getvalue())


# ---------------------------------------------------------
# 座標定義ヘルパー (src_legacy より移植・整理)
# ---------------------------------------------------------
def _mizuho_balance_certificate_coordinates(
    replacement_map: Dict[str, str],
) -> List[Dict[str, Any]]:
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
) -> List[Dict[str, Any]]:
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
) -> List[Dict[str, Any]]:
    coords = [
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
            "x": 150.0,
            "y": 235.0,
            "value": replacement_map.get("被相続人氏名", ""),
            "font_size": 12.0,
            "color": "black",
        },
        {
            "page": 1,
            "x": 35.0,
            "y": 215.0,
            "value": replacement_map.get("支店名", ""),
            "font_size": 11.0,
            "color": "black",
        },
    ]
    return coords


def _ja_balance_certificate_coordinates(
    replacement_map: Dict[str, str],
) -> List[Dict[str, Any]]:
    return [
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
            "y": 187.0,
            "value": replacement_map.get("相続人氏名", ""),
            "font_size": 12.0,
            "color": "black",
        },
    ]
