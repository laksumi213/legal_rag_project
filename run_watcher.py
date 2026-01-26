# run_watcher.py

import logging
import os
import sys
import time
import threading

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

# --- サービスインポート ---
from legal_system.core.data_sync import DataSyncEngine
# ★追加: DBマネージャーをインポートしてプロフィールを取得できるようにする
from legal_system.core.database_manager import DatabaseManager
from services.gmail_watcher_service import GmailWatcherService

try:
    from services.scanner_service import ScannerService
except ImportError:
    ScannerService = None

# ==========================================
# ★ 設定: 監視ディレクトリ
# ==========================================

# 1. Kintone連携用 (Downloadsフォルダ)
WATCH_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# 2. スキャナー監視用 (NAS等)
def get_target_scan_folder():
    """
    ターゲットとなるスキャンフォルダのパスを特定する。
    OSのユーザー名ではなく、本システムのDB(プロフィール)に登録された名前を使用する。
    """
    try:
        # DBからユーザー情報を取得
        # (get_current_user_info内部で os.environ["USERNAME"] を使い、DBの users テーブルを検索します)
        db = DatabaseManager()
        user_info = db.get_current_user_info()
        
        # プロフィールの名前（例: "山田 太郎"）を使用
        target_name = user_info["name"]
        
        # 万が一取得できない場合はOSユーザー名をバックアップとして使用
        if not target_name:
             target_name = os.environ.get("USERNAME", "Unknown")
             
    except Exception as e:
        logger.warning(f"プロフィール取得エラー: {e}")
        target_name = os.environ.get("USERNAME", "Unknown")
    
    # NASルートパス
    nas_root = r"\\192.168.11.20\行政書士法人チェスター\08.その他\スキャン"
    target_path = os.path.join(nas_root, target_name)
    
    return target_path, target_name

# ==========================================
# 1. Kintone JSON 監視ハンドラ
# ==========================================
class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        self.syncer = DataSyncEngine()

    def _process(self, filepath):
        filename = os.path.basename(filepath)
        if (filename.startswith("G") or filename.startswith("NoNumber")) and filename.endswith(".json"):
            logger.info(f"📥 検知: {filename}")
            time.sleep(1.0) 
            for i in range(3):
                try:
                    if self.syncer.sync_from_kintone_json(filepath):
                        logger.info(f"✅ 取込成功: {filename}")
                        try:
                            os.remove(filepath)
                            logger.info(f"🗑️ 削除完了: {filename}")
                        except Exception as e:
                            logger.warning(f"⚠️ 削除失敗: {e}")
                        return
                    else:
                        time.sleep(1.0)
                except Exception:
                    time.sleep(1.0)
            logger.warning(f"⚠️ 取込スキップ: {filename}")

    def on_created(self, event):
        if event.is_directory: return
        self._process(event.src_path)

    def on_moved(self, event):
        if event.is_directory: return
        self._process(event.dest_path)

# ==========================================
# 2. スキャナー 監視ハンドラ
# ==========================================
class ScanHandler(FileSystemEventHandler):
    def __init__(self, inbox_path, processed_root): 
        self.service = None
        if ScannerService:
            self.service = ScannerService(inbox_path, processed_root)

    def _process(self, filepath):
        filename = os.path.basename(filepath)
        # 隠しファイルや一時ファイルは無視
        if filename.startswith(".") or filename.startswith("~$"):
            return

        # 拡張子チェック (画像も許可)
        valid_exts = (".pdf", ".jpg", ".jpeg", ".png")
        if filename.lower().endswith(valid_exts):
            logger.info(f"🖨️ スキャン検知: {filename}")
            try:
                self.service.process_file(filepath)
            except Exception as e:
                logger.error(f"❌ 処理中にエラーが発生しました: {e}")

    def on_created(self, event):
        if not self.service or event.is_directory: return
        self._process(event.src_path)
            
    def on_moved(self, event):
        if not self.service or event.is_directory: return
        self._process(event.dest_path)

# ==========================================
# 3. Gmail 監視ループ
# ==========================================
def run_gmail_watcher():
    logger.info("📧 Gmail監視スレッド起動")
    try:
        service = GmailWatcherService()
        if not service.service:
            logger.warning("⚠️ Gmail API無効 (token.json/credentials.jsonを確認)")
            return
    except Exception:
        return

    while True:
        try:
            service.poll_and_process()
            service.retry_linking_pending_notes()
        except Exception as e:
            logger.error(f"Gmail Error: {e}")
        time.sleep(1800)

# ==========================================
# メイン実行
# ==========================================
if __name__ == "__main__":
    logger.info(f"🚀 システム監視プロセス起動 (Ver 3.1 Profile-Linked)")

    # 1. Kintone監視 (Downloads)
    if not os.path.exists(WATCH_DIR):
        logger.warning(f"⚠️ ダウンロードフォルダが見つかりません: {WATCH_DIR}")
        WATCH_DIR = os.path.join(BASE_DIR, "data", "kintone_watch")
        os.makedirs(WATCH_DIR, exist_ok=True)
    
    logger.info(f"📂 Kintone監視パス: {WATCH_DIR}")

    # 2. スキャナー監視 (DBプロフィール連動)
    scan_dir, user_name = get_target_scan_folder()
    CASES_ROOT = os.path.join(BASE_DIR, "data", "cases") 

    logger.info(f"👤 DB登録名: {user_name}")
    logger.info(f"📡 スキャナー監視予定パス: {scan_dir}")

    observer = Observer()

    # Kintone監視登録
    json_handler = JsonHandler()
    observer.schedule(json_handler, WATCH_DIR, recursive=False)

    # スキャナー監視登録
    if ScannerService:
        if os.path.exists(scan_dir):
            # NASが見つかった場合
            scan_handler = ScanHandler(inbox_path=scan_dir, processed_root=CASES_ROOT)
            observer.schedule(scan_handler, scan_dir, recursive=False)
            logger.info(f"✅ スキャナー監視を開始しました (Target: {scan_dir})")
        else:
            # NASが見つからない場合 -> 代替フォルダを作成して監視
            logger.error(f"❌ 指定されたスキャンフォルダが見つかりません/アクセスできません。")
            
            # 代替フォルダ (プロジェクト内の data/scan_inbox)
            fallback_dir = os.path.join(BASE_DIR, "data", "scan_inbox")
            os.makedirs(fallback_dir, exist_ok=True)
            
            scan_handler = ScanHandler(inbox_path=fallback_dir, processed_root=CASES_ROOT)
            observer.schedule(scan_handler, fallback_dir, recursive=False)
            
            logger.warning(f"⚠️ 代わりにローカルテスト用フォルダを監視します: {fallback_dir}")
            logger.warning(f"   👉 ここにファイルを置いてテストしてください。")

    # Gmail監視スレッド開始
    gmail_thread = threading.Thread(target=run_gmail_watcher, daemon=True)
    gmail_thread.start()

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()