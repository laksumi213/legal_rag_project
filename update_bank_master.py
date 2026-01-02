# ファイルパス: update_bank_master.py

import json
import os
import time
from datetime import datetime

import requests

# ==========================================
# 設定エリア
# ==========================================
# データ保存先 (ルート直下の data/zengin フォルダ)
BASE_DIR = os.path.join("data", "zengin")
BRANCH_DIR = os.path.join(BASE_DIR, "branches")
STATE_FILE = os.path.join(BASE_DIR, "last_updated.json")

# Zengin-Code (GitHub) のAPIエンドポイント
REPO_API_URL = (
    "https://api.github.com/repos/zengin-code/source-data/commits?path=data&per_page=1"
)

# 生データ取得URL
BANKS_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/banks.json"
)
BRANCH_BASE_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/branches/"
)

# ==========================================
# 関数定義
# ==========================================


def get_remote_last_commit_date():
    """GitHub APIを使ってリモート(zengin-code)の最終更新日時を取得する"""
    print("🔍 GitHubの更新状況を確認中...")
    try:
        resp = requests.get(REPO_API_URL, timeout=10)

        if resp.status_code == 200:
            commit_data = resp.json()
            if commit_data and isinstance(commit_data, list):
                # ISO 8601形式の日付文字列 (例: "2023-10-01T12:00:00Z")
                commit_date = commit_data[0]["commit"]["committer"]["date"]
                return commit_date
        else:
            print(f"⚠️ API制限またはエラー (Status: {resp.status_code})")
    except Exception as e:
        print(f"⚠️ 通信エラー: {e}")

    return None


def load_local_state():
    """ローカルの前回更新情報を読み込む"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_commit_date": ""}


def save_local_state(commit_date):
    """更新完了後に日時を保存する"""
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


def download_data(progress_callback=None):
    """
    データを実際にダウンロードして保存する

    Args:
        progress_callback (callable, optional):
            進捗状況を通知するための関数。
            func(current_count, total_count, message) の形式で呼び出されます。
    """
    print("📥 データのダウンロードを開始します...")

    # フォルダがなければ作成
    os.makedirs(BRANCH_DIR, exist_ok=True)

    # 1. 銀行一覧 (banks.json)
    if progress_callback:
        progress_callback(0, 100, "銀行一覧を取得中...")

    print("   - 銀行一覧 (banks.json) を取得中...")
    try:
        resp = requests.get(BANKS_URL, timeout=10)
        resp.raise_for_status()
        banks = resp.json()

        # 保存
        with open(os.path.join(BASE_DIR, "banks.json"), "w", encoding="utf-8") as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ 銀行一覧の取得に失敗しました: {e}")
        return False, None

    # 2. 支店データ (全銀行分)
    total_banks = len(banks)
    print(f"   - 全 {total_banks} 銀行の支店データを取得します (数分かかります)...")

    success_count = 0

    # 銀行コード順に処理
    for i, bank_code in enumerate(banks.keys(), 1):
        branch_url = f"{BRANCH_BASE_URL}{bank_code}.json"
        save_path = os.path.join(BRANCH_DIR, f"{bank_code}.json")

        try:
            r = requests.get(branch_url, timeout=5)

            if r.status_code == 200:
                # 正常に取得できた場合のみ保存
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f, ensure_ascii=False, indent=2)
                success_count += 1
            elif r.status_code == 404:
                # 支店データが存在しない銀行は無視
                pass

            # GitHubへの負荷軽減のため、ごく短い待機を入れる
            time.sleep(0.05)

            # --- 進捗通知 (ここが変更点) ---
            # コールバック関数が渡されていれば実行 (Streamlitへの通知)
            if progress_callback:
                progress_callback(i, total_banks, f"支店データ取得中: {bank_code}")

            # ターミナル用出力
            progress = (i / total_banks) * 100
            print(f"\r     Progress: [{i}/{total_banks}] {progress:.1f}% 完了", end="")

        except Exception as e:
            # 個別の通信エラーはログに出して続行
            print(f"\n⚠️ 銀行コード {bank_code} の取得エラー: {e}")

    print(f"\n✅ ダウンロード完了 (取得成功: {success_count}件)")
    return True, banks


def main():
    print("========================================")
    print("🏦 銀行マスタ自動更新ツール")
    print("========================================")

    # 1. 保存先ディレクトリの確認
    if not os.path.exists(BASE_DIR):
        print(f"📁 初回起動: 保存先ディレクトリを作成します -> {BASE_DIR}")
        os.makedirs(BASE_DIR, exist_ok=True)

    # 2. 更新チェック
    remote_date = get_remote_last_commit_date()
    local_state = load_local_state()
    local_date = local_state.get("last_commit_date", "")

    print(f"📅 GitHub更新日: {remote_date if remote_date else '取得失敗'}")
    print(f"📅 前回更新日  : {local_date if local_date else 'データなし'}")

    # 3. 実行判定
    should_update = False

    if remote_date:
        if remote_date != local_date:
            print("🔄 新しいデータが見つかりました。更新を開始します。")
            should_update = True
        else:
            print("✨ データは最新です。更新の必要はありません。")
            return
    else:
        # API失敗時
        if not os.path.exists(os.path.join(BASE_DIR, "banks.json")):
            print(
                "⚠️ 更新確認に失敗しましたが、ローカルデータがないためダウンロードを試みます。"
            )
            should_update = True
        else:
            print(
                "⚠️ 更新確認に失敗しました。ローカルデータがあるため今回はスキップします。"
            )
            return

    # 4. 更新処理
    if should_update:
        # main実行時はコールバックなし
        success, _ = download_data()

        if success and remote_date:
            save_local_state(remote_date)
            print("🎉 マスタデータの同期が完了しました。")
            print(f"📂 保存場所: {os.path.abspath(BASE_DIR)}")
        elif success and not remote_date:
            # 日付なしでダウンロードだけ成功した場合
            save_local_state("unknown_date")
            print(
                "🎉 ダウンロードは完了しましたが、バージョン日付は取得できませんでした。"
            )
        else:
            print("❌ 更新処理中にエラーが発生しました。")


if __name__ == "__main__":
    main()
