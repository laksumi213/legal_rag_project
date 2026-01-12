# file: src/legal_system/core/data_sync.py

import json
import logging
from typing import Any, Dict

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import BankMaster, Case, FinancialAsset

logger = logging.getLogger(__name__)


class DataSyncEngine:
    """
    外部データ（Kintone JSON等）とPostgreSQLの同期を管理するエンジン。
    """

    def __init__(self):
        self.db = DatabaseManager()

    def sync_from_kintone_json(self, json_path: str) -> bool:
        """
        JSONファイルを読み込み、PostgreSQLへUpsert処理を行う。
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"JSON読み込み失敗: {e}")
            return False

        session = self.db._get_session()
        try:
            # 1. 案件 (Case) の同期 - ビジネスID「G番号」をキーにする
            case_num = data.get("顧客コード_2") or data.get("case_number")
            if not case_num:
                logger.warning("案件番号(G番号)がないためスキップします。")
                return False

            case = session.query(Case).filter_by(case_number=case_num).first()
            if not case:
                case = Case(
                    case_number=case_num,
                    client_name=data.get("顧客名", "名称未設定"),
                    created_at=datetime.now(),
                )
                session.add(case)
                session.flush()  # IDを確定させる

            # 2. 資産データ (FinancialAsset) の Upsert
            # 同一案件内の「銀行名・支店名・口座番号」の組み合わせが一致すれば更新する
            assets_list = data.get("assets", [])  # JSON構造に合わせて調整
            for a in assets_list:
                self._upsert_financial_asset(session, case.case_id, a)

            session.commit()
            logger.info(f"✅ 同期完了: {case_num}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"❌ 同期エラー: {e}")
            return False
        finally:
            session.close()

    def _upsert_financial_asset(
        self, session, case_id: int, asset_data: Dict[str, Any]
    ):
        """
        PostgreSQLの機能を活用した資産情報のUpsert処理
        """
        # 銀行・支店IDの解決（簡易化のため名称一致で検索）
        bank = (
            session.query(BankMaster)
            .filter(BankMaster.bank_name == asset_data.get("bank_name"))
            .first()
        )
        if not bank:
            return

        # 既存レコードの確認
        existing_asset = (
            session.query(FinancialAsset)
            .filter(
                FinancialAsset.case_id == case_id,
                FinancialAsset.bank_id == bank.id,
                FinancialAsset.account_number == asset_data.get("account_number"),
            )
            .first()
        )

        if existing_asset:
            # 更新 (Update)
            existing_asset.balance = asset_data.get("balance", 0.0)
            existing_asset.status = asset_data.get("status", "更新あり")
        else:
            # 新規登録 (Insert)
            new_asset = FinancialAsset(
                case_id=case_id,
                bank_id=bank.id,
                account_number=asset_data.get("account_number"),
                balance=asset_data.get("balance", 0.0),
                status="新規取込",
            )
            session.add(new_asset)
