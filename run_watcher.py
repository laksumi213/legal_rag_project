import os
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.data_sync import DataSyncEngine

# 監視対象フォルダ (ダウンロードフォルダなど)
# ※Windowsのダウンロードフォルダの例
WATCH_DIR = os.path.expanduser("~/Downloads")


class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        # ファイルが作成されたとき
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)

        # "G"で始まり ".json" で終わるファイルのみ対象 (例: G0001.json)
        if filename.startswith("G") and filename.endswith(".json"):
            print(f"📥 検知: {filename}")
            # ファイル書き込み完了まで少し待つ
            time.sleep(1)
            self.syncer.sync_from_kintone_json(event.src_path)


if __name__ == "__main__":
    print(f"👀 監視を開始しました: {WATCH_DIR}")
    print("   'Gxxxx.json' というファイルがダウンロードされると自動で取り込みます。")

    event_handler = JsonHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
