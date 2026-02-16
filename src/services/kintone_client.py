import json
import logging

import requests

from legal_system.utils.retry_decorator import retry_with_backoff

logger = logging.getLogger(__name__)


class KintoneClient:
    def __init__(self, subdomain="chester-tax", api_token=None):
        # 案件管理アプリID (ソースコードより特定)
        self.app_id = "242"
        self.base_url = f"https://{subdomain}.cybozu.com/k/v1"
        self.headers = {
            "X-Cybozu-API-Token": api_token,  # .envなどで管理推奨
            "Content-Type": "application/json",
        }

    @retry_with_backoff(
        max_retries=3,
        backoff_factor=2.0,
        exceptions=(requests.RequestException, requests.HTTPError),
        log_to_audit=True,
    )
    def update_financial_asset(self, record_id, bank_name, balance, date_acquired):
        """
        指定されたレコードの「＜金融機関＞」テーブルに、資産情報を追加・更新する
        """
        # 1. 現在のレコード情報を取得（既存の行を消さないため）
        get_url = f"{self.base_url}/record.json?app={self.app_id}&id={record_id}"
        resp = requests.get(get_url, headers=self.headers, timeout=10)

        if resp.status_code != 200:
            raise requests.HTTPError(f"Kintone Get Error: {resp.text}")

        current_record = resp.json().get("record", {})
        current_table = current_record.get("テーブル_0", {}).get("value", [])

        # 2. 同じ銀行が既にあるかチェック (あれば更新、なければ追加)
        target_row_index = -1
        for i, row in enumerate(current_table):
            existing_bank = row["value"]["文字列__1行__11"]["value"]
            # 部分一致などで判定（例: "三菱UFJ" が含まれていれば）
            if bank_name in existing_bank or existing_bank in bank_name:
                target_row_index = i
                break

        # 3. 行データの作成
        new_row_data = {
            "value": {
                "文字列__1行__11": {"value": bank_name},  # 銀行名
                "残高_0": {"value": str(balance)},  # 残高 (数値も文字列で送る)
                "日付_7": {"value": date_acquired},  # 残証取得日 (YYYY-MM-DD)
            }
        }

        if target_row_index >= 0:
            # 更新: 既存の行を上書き
            logger.info(f"Kintone更新: {bank_name} の情報を上書きします。")
            current_table[target_row_index] = new_row_data
        else:
            # 新規追加
            logger.info(f"Kintone追加: {bank_name} を行末に追加します。")
            current_table.append(new_row_data)

        # 4. 書き戻し (PUT)
        payload = {
            "app": self.app_id,
            "id": record_id,
            "record": {"テーブル_0": {"value": current_table}},
        }

        put_url = f"{self.base_url}/record.json"
        put_resp = requests.put(
            put_url, headers=self.headers, data=json.dumps(payload), timeout=10
        )

        if put_resp.status_code != 200:
            raise requests.HTTPError(f"Kintone Put Error: {put_resp.text}")

        logger.info("✅ Kintoneへの書き戻し成功")
        return True
