# run_watcher.py

import logging
import os
import sys
import time
import threading  # ★追加

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

# Watcherプロセス環境フラグ
os.environ["IS_WATCHER_PROCESS"] = "true"

from legal_system.core.data_sync import DataSyncEngine
# ★追加: Gmail監視サービス
from services.gmail_watcher_service import GmailWatcherService

WATCH_DIR = os.path.join(BASE_DIR, "data", "kintone_watch")

# --- 1. 既存のファイル監視ハンドラ ---
class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        time.sleep(2)
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        if filename.startswith("G") and filename.endswith(".json"):
            logger.info(f"📥 連携JSONを検知: {filename}")
            time.sleep(1.5)
            if self.syncer.sync_from_kintone_json(event.src_path):
                logger.info(f"✅ DB同期完了: {filename}")
                # ★追加: 新規案件が入ったので、未紐付けメモの再チェックを行う
                # (簡易的にGmailサービスのメソッドを呼ぶ)
                try:
                    gmail_svc = GmailWatcherService()
                    gmail_svc.retry_linking_pending_notes()
                except:
                    pass
            else:
                logger.error(f"❌ 同期失敗: {filename}")

# --- 2. 新規: Gmail監視ループ ---
def run_gmail_watcher():
    """Gmailを定期監視するスレッド関数"""
    logger.info("📧 Gmail監視スレッドを開始します...")
    
    # サービスの初期化 (クレデンシャルがない場合はログを出して終了しないように注意)
    try:
        service = GmailWatcherService()
        if not service.service:
            logger.warning("⚠️ Gmail APIが無効なため、メール監視はスキップします。")
            return
    except Exception as e:
        logger.error(f"Gmail Service Init Error: {e}")
        return

    while True:
        try:
            # 新着メールの確認
            service.poll_and_process()
            
            # 定期的に「未紐付けメモ」の再チェックも行う (例: 5回に1回など頻度は調整可)
            service.retry_linking_pending_notes()
            
        except Exception as e:
            logger.error(f"Gmail Watcher Loop Error: {e}")
        
        # 30分待機 (API制限考慮)
        time.sleep(1800)

if __name__ == "__main__":
    # ディレクトリ作成
    if not os.path.exists(WATCH_DIR):
        os.makedirs(WATCH_DIR, exist_ok=True)

    logger.info(f"🚀 システム監視プロセス起動")

    # A. Gmail監視を別スレッドで開始
    gmail_thread = threading.Thread(target=run_gmail_watcher, daemon=True)
    gmail_thread.start()

    # B. フォルダ監視を開始 (メインスレッド)
    logger.info(f"👀 フォルダ監視開始: {WATCH_DIR}")
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