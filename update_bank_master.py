# File: update_bank_master.py

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3

# SSL警告を非表示にする（ローカル開発用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 設定エリア (絶対パス化)
# ==========================================
ROOT_DIR = Path(__file__).parent.absolute()
BASE_DIR = ROOT_DIR / "data" / "zengin"
BRANCH_DIR = BASE_DIR / "branches"
STATE_FILE = BASE_DIR / "last_updated.json"

# API & URL
REPO_API_URL = (
    "https://api.github.com/repos/zengin-code/source-data/commits?path=data&per_page=1"
)
BANKS_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/banks.json"
)
BRANCH_BASE_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/branches/"
)


def download_data(progress_callback=None):
    print(f"🚀 [Start] データ保存先を確認: {BASE_DIR}")

    # フォルダ作成
    os.makedirs(BRANCH_DIR, exist_ok=True)

    # 1. 銀行一覧
    if progress_callback:
        progress_callback(0, 100, "銀行一覧を取得中...")

    try:
        # verify=False でSSLエラーを回避
        print(f"connecting to {BANKS_URL} ...")
        resp = requests.get(BANKS_URL, timeout=15, verify=False)
        resp.raise_for_status()
        banks = resp.json()

        with open(BASE_DIR / "banks.json", "w", encoding="utf-8") as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)

        print(f"✅ 銀行マスタ保存完了: {len(banks)}件")

    except Exception as e:
        print(f"❌ 銀行一覧の取得に失敗: {e}")
        return False, None

    # 2. 支店データ
    total_banks = len(banks)
    print(f"🔄 支店データ取得開始: 対象 {total_banks} 行")

    success_count = 0
    # 全件取得（エラーが出ても止まらないようにする）
    for i, bank_code in enumerate(list(banks.keys())):
        branch_url = f"{BRANCH_BASE_URL}{bank_code}.json"
        save_path = BRANCH_DIR / f"{bank_code}.json"

        try:
            r = requests.get(branch_url, timeout=10, verify=False)
            if r.status_code == 200:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f, ensure_ascii=False, indent=2)
                success_count += 1

            # プログレスバー更新 (10件に1回更新で負荷軽減)
            if i % 10 == 0 and progress_callback:
                progress_callback(i + 1, total_banks, f"支店データ取得中: {bank_code}")

            # サーバー負荷軽減のためのスリープ
            time.sleep(0.01)

        except Exception:
            # 個別の失敗は無視して続行
            pass

    print(f"✅ 全ダウンロード完了 (成功: {success_count}件)")
    return True, banks


# --- 以下の関数は変更なし ---
def get_remote_last_commit_date():
    try:
        resp = requests.get(REPO_API_URL, timeout=10, verify=False)
        if resp.status_code == 200:
            return resp.json()[0]["commit"]["committer"]["date"]
    except:
        pass
    return None


def load_local_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_commit_date": ""}


def save_local_state(commit_date):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "last_commit_date": commit_date,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    download_data()
