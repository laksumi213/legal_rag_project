# file: run_watcher.py
import logging
import os
import sys
import time

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# パス解決
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# WatcherプロセスではStreamlit環境ではないことを明示するためのフラグ
os.environ["IS_WATCHER_PROCESS"] = "true"

from legal_system.core.data_sync import DataSyncEngine

# ★修正ポイント: コンテナ内でも確実に見えるデータフォルダを監視対象にする
WATCH_DIR = os.path.join(BASE_DIR, "data", "kintone_watch")


class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        time.sleep(2)
        # DataSyncEngine内でDB接続が行われる
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)

        if filename.startswith("G") and filename.endswith(".json"):
            logger.info(f"📥 連携JSONを検知: {filename}")
            # ファイルの書き込み完了を待機
            time.sleep(1.5)
            success = self.syncer.sync_from_kintone_json(event.src_path)
            if success:
                logger.info(f"✅ DB同期完了: {filename}")
                # 処理済みファイルは削除または移動すると良いが、今回はログ出力のみ
            else:
                logger.error(f"❌ 同期失敗: {filename}")


if __name__ == "__main__":
    # ★修正ポイント: フォルダが存在しない場合は自動作成する
    if not os.path.exists(WATCH_DIR):
        logger.info(f"監視ディレクトリを作成します: {WATCH_DIR}")
        os.makedirs(WATCH_DIR, exist_ok=True)

    logger.info(f"🚀 監視開始: {WATCH_DIR}")
    logger.info("G番号(Gxxxx.json)のファイルをこのフォルダに置くと、自動で取り込まれます。")

    event_handler = JsonHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 監視を停止します。")
        observer.stop()
    observer.join()