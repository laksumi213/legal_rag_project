# file: src/legal_system/core/data_sync.py

import json
import logging
import os

# ★重要: ロジックを分散させず、サービス層に一元化する
from legal_system.services.kintone_sync_service import import_kintone_json

logger = logging.getLogger(__name__)


class DataSyncEngine:
    """
    Watcherからの呼び出しを受け付け、Service層へ処理を流すクラス。
    """

    def __init__(self):
        pass

    def sync_from_kintone_json(self, json_path: str) -> bool:
        """
        JSONファイルを読み込み、Service層を通じてDBへUpsertする。
        """
        if not os.path.exists(json_path):
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return False
        except Exception as e:
            logger.error(f"JSON読込エラー: {e}")
            return False

        try:
            logger.info(f"🔄 同期開始: {os.path.basename(json_path)}")

            # 手動取り込みと同じ関数を呼び出す
            # target_case_id=None にすると、JSON内の「顧客コード(G番号)」から自動で案件を特定/作成してくれる
            case_id = import_kintone_json(data, target_case_id=None)

            if case_id and case_id > 0:
                logger.info(f"✅ 同期成功 (Case ID: {case_id})")
                return True
            else:
                logger.warning("⚠️ 同期処理は完了しましたが、IDが返されませんでした。")
                return False

        except Exception as e:
            logger.error(f"❌ 同期エラー: {e}")
            return False
