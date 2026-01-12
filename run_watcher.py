# file: run_watcher.py
import logging
import os
import sys
import time

# ロギング設定 (Streamlit警告と区別するため)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# パス解決の最適化
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# WatcherプロセスではStreamlit環境ではないことを明示するためのフラグ
os.environ["IS_WATCHER_PROCESS"] = "true"

from legal_system.core.data_sync import DataSyncEngine

# Macのダウンロードフォルダを優先
WATCH_DIR = os.path.expanduser("~/Downloads")


class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        # DataSyncEngine内でDB接続が行われる
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)

        if filename.startswith("G") and filename.endswith(".json"):
            logger.info(f"📥 連携JSONを検知: {filename}")
            # ファイルの書き込み完了を待機（MacのDL処理は一瞬だが安全のため）
            time.sleep(1.5)
            success = self.syncer.sync_from_kintone_json(event.src_path)
            if success:
                logger.info(f"✅ DB同期完了: {filename}")
            else:
                logger.error(f"❌ 同期失敗: {filename}")


if __name__ == "__main__":
    if not os.path.exists(WATCH_DIR):
        logger.error(f"監視ディレクトリが存在しません: {WATCH_DIR}")
        sys.exit(1)

    logger.info(f"🚀 監視開始: {WATCH_DIR}")
    logger.info("G番号(Gxxxx.json)のファイルを自動でPostgreSQLへ取り込みます。")

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
