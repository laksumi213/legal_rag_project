# run_watcher.py

import logging
import os
import sys
import time
import threading
import traceback
from pathlib import Path
from dotenv import load_dotenv # NEW IMPORT

load_dotenv() # Load environment variables from .env file

# ==========================================
# ログ設定
# ==========================================
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watcher.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==========================================
# 監視設定
# ==========================================
try:
    from watchdog.observers.polling import PollingObserver as Observer
    logger.info("ℹ️ Windows 互換モード (PollingObserver) で起動します。")
except ImportError:
    from watchdog.observers import Observer
    logger.info("ℹ️ 標準モード (Observer) で起動します。")

from watchdog.events import FileSystemEventHandler

# パス解決
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

os.environ["IS_WATCHER_PROCESS"] = "true"

from legal_system.core.data_sync import DataSyncEngine
from legal_system.core.database_manager import DatabaseManager
from services.gmail_watcher_service import GmailWatcherService

# ScannerServiceのインポート
ScannerService = None
try:
    from services.scanner_service import ScannerService
    logger.info("✅ ScannerService モジュールをロードしました。")
except ImportError as e:
    logger.error(f"❌ ScannerService のインポートに失敗しました: {e}")
except Exception as e:
    logger.error(f"❌ ScannerService ロード中に予期せぬエラー: {e}")

def get_downloads_path():
    home = Path.home()
    candidates = [
        home / "Downloads",
        home / "OneDrive" / "Downloads",
        home / "OneDrive - 行政書士法人チェスター" / "Downloads",
    ]
    for path in candidates:
        if path.exists(): return str(path)
    return os.path.join(os.path.expanduser("~"), "Downloads")

WATCH_DIR_DOWNLOADS = get_downloads_path()

def get_target_scan_folder():
    """スキャン監視用フォルダを決定する"""
    try:
        db = DatabaseManager()
        user_info = db.get_current_user_info()
        target_name = user_info["name"]
        if not target_name: target_name = os.environ.get("USERNAME", "Unknown")
    except:
        target_name = os.environ.get("USERNAME", "Unknown")
    
    # NASパス (存在しなければローカルの data/scan_inbox を使用)
    nas_root = r"\\192.168.11.20\行政書士法人チェスター\08.その他\スキャン"
    if not os.path.exists(nas_root):
        nas_root = os.path.join(BASE_DIR, "data", "scan_inbox")
        os.makedirs(nas_root, exist_ok=True)

    target_path = os.path.join(nas_root, target_name)
    if not os.path.exists(target_path):
        try: os.makedirs(target_path, exist_ok=True)
        except: pass
            
    return target_path, target_name

# ==========================================
# ★追加: 重複防止機能付きハンドラ
# ==========================================
class DebouncedEventHandler(FileSystemEventHandler):
    """同じファイルのイベントが連続して発生した場合、指定時間内は無視する"""
    def __init__(self, cooldown=10.0): # クールダウンを10秒に延長
        super().__init__()
        self._processed_cache = {} # path -> timestamp
        self._cooldown = cooldown

    def _should_process(self, filepath):
        current_time = time.time()
        filename = os.path.basename(filepath)
        
        # 除外ファイル
        if filename.startswith(".") or filename.startswith("~$"):
            logger.info(f"   -> 無視 (システムファイル): {filename}")
            return False
        if filename.lower().endswith((".tmp", ".crdownload", ".part", ".lock")):
            logger.info(f"   -> 無視 (一時ファイル): {filename}")
            return False

        # クールダウン判定
        if filepath in self._processed_cache:
            last_time = self._processed_cache[filepath]
            if current_time - last_time < self._cooldown:
                logger.info(f"   -> 無視 (クールダウン中): {filename}")
                return False
        
        # 処理許可 & 時刻更新
        self._processed_cache[filepath] = current_time
        
        # キャッシュ掃除
        if len(self._processed_cache) > 1000:
            self._processed_cache = {k:v for k,v in self._processed_cache.items() if current_time - v < self._cooldown}
            
        return True

# ==========================================
# 1. Downloads Handler
# ==========================================
class DownloadsHandler(DebouncedEventHandler):
    def __init__(self):
        super().__init__()
        self.syncer = DataSyncEngine()
        cases_root = os.path.join(BASE_DIR, "data", "cases")
        self.scanner = ScannerService(inbox_path=WATCH_DIR_DOWNLOADS, processed_root=cases_root) if ScannerService else None
        logger.info("👀 DownloadsHandler 準備完了")

    def _process(self, filepath):
        if not self._should_process(filepath): return
        if not os.path.exists(filepath): return

        filename = os.path.basename(filepath)
        time.sleep(1.0) # 書き込み待ち

        # Kintone JSON
        if filename.lower().endswith(".json"):
            keywords = ["G", "NoNumber", "Record", "kintone", "案件", "顧客"]
            if any(kw in filename for kw in keywords):
                logger.info(f"🔍 [DL] Kintoneデータ検知: {filename}")
                try:
                    if self.syncer.sync_from_kintone_json(filepath):
                        logger.info(f"   ✅ 同期成功")
                        try: os.remove(filepath)
                        except: pass
                except Exception as e:
                    logger.error(f"   ❌ 同期エラー: {e}")
            return

        # 登記情報PDF
        if filename.lower().endswith(".pdf") and "不動産登記" in filename:
            logger.info(f"🔍 [DL] 登記情報検知: {filename}")
            if self.scanner:
                try: self.scanner.process_file(filepath)
                except Exception as e: logger.error(f"   ❌ スキャナー処理エラー: {e}")

    def on_created(self, event):
        if not event.is_directory: self._process(event.src_path)
    def on_moved(self, event):
        if not event.is_directory: self._process(event.dest_path)
    def on_modified(self, event):
        if not event.is_directory: self._process(event.src_path)

# ==========================================
# 2. Scan Handler
# ==========================================
class ScanHandler(DebouncedEventHandler):
    def __init__(self, inbox_path, processed_root): 
        super().__init__()
        self.inbox_path = inbox_path
        self.service = ScannerService(inbox_path, processed_root) if ScannerService else None
        if self.service:
            logger.info(f"👀 ScanHandler 準備完了 (監視先: {inbox_path})")

    def _process(self, filepath):
        if not self._should_process(filepath): return
        if not os.path.exists(filepath): return

        filename = os.path.basename(filepath)
        valid_exts = (".pdf", ".jpg", ".jpeg", ".png")
        
        if filename.lower().endswith(valid_exts):
            logger.info(f"🔍 [Scan] 書類検知: {filename}")
            time.sleep(2.0) # スキャナ書き込み待ち
            
            if self.service:
                logger.info(f"   🖨️ 解析開始 -> 受信トレイへ")
                try:
                    self.service.process_file(filepath)
                except Exception as e:
                    logger.error(f"   ❌ 解析エラー: {e}")
                    logger.error(traceback.format_exc())
        else:
            logger.info(f"   -> 無視 (対象外の拡張子): {filename}")

    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"H-CREATE: Event detected for {event.src_path}")
            self._process(event.src_path)
    def on_moved(self, event):
        if not event.is_directory:
            logger.info(f"H-MOVE: Event detected for {event.dest_path}")
            self._process(event.dest_path)
    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"H-MODIFY: Event detected for {event.src_path}")
            self._process(event.src_path)

# ==========================================
# 3. Will RAG Source Handler (新規追加)
# ==========================================
# Z Drive path for RAG
Z_DRIVE_PATH = Path("Z:/") # Assuming Z: is the drive letter

class WillRAGSourceHandler(DebouncedEventHandler):
    def __init__(self):
        super().__init__(cooldown=30.0) # Longer cooldown for RAG ingestion
        self.scanner_service = ScannerService() if ScannerService else None # Instantiate ScannerService
        logger.info("👀 WillRAGSourceHandler 準備完了")

    def _is_will_document(self, filepath: Path) -> bool:
        """
        ファイルが遺言書関連ドキュメント（文案または公正証書）であるか判定する。
        親ディレクトリに「遺言」が含まれ、かつファイル名に「遺言書」または「公正証書」が含まれるDOCX/PDFファイルを対象とする。
        """
        filename = filepath.name.lower()
        if filepath.suffix.lower() not in [".docx", ".pdf"]:
            return False

        # 親ディレクトリを遡って「遺言」を含むか確認
        current_path = filepath.parent
        while current_path != current_path.parent and current_path != Z_DRIVE_PATH.parent:
            if "遺言" in current_path.name:
                # ファイル名が「遺言書案文」または「公正証書」に関連するかをチェック
                if "遺言書" in filename or "公正証書" in filename:
                    return True
            current_path = current_path.parent
        return False

    def _process(self, filepath: Path):
        if not self._should_process(str(filepath)): return
        if not filepath.exists(): return

        # フォルダ名およびファイル名でフィルタリング
        if not self._is_will_document(filepath):
            logger.debug(f"🔍 [Will RAG] 遺言関連ファイルではないためスキップ: {filepath.name}")
            return

        logger.info(f"🔍 [Will RAG] 遺言関連ファイル検知: {filepath.name}")
        time.sleep(2.0) # ファイル書き込み待ち

        if self.scanner_service: # Ensure ScannerService is loaded
            try:
                # ScannerService に RAG 用の取り込みメソッドを呼び出す
                self.scanner_service.ingest_will_for_rag(filepath)
                logger.info(f"   📥 RAG取り込み処理を ScannerService に委譲: {filepath.name}")
            except Exception as e:
                logger.error(f"   ❌ RAG取り込みエラー: {e}")
                logger.error(traceback.format_exc())

    def on_created(self, event):
        if not event.is_directory: self._process(Path(event.src_path))
    def on_moved(self, event):
        if not event.is_directory: self._process(Path(event.dest_path))
    def on_modified(self, event):
        if not event.is_directory: self._process(Path(event.src_path))


# ==========================================
# Main
# ==========================================
def run_gmail_watcher():
    logger.info("📧 Gmail監視スレッド起動")
    try:
        service = GmailWatcherService()
        if not service.service: return
        while True:
            service.poll_and_process()
            service.retry_linking_pending_notes()
            time.sleep(600)
    except Exception as e:
        logger.error(f"Gmail Watcher Error: {e}")


def manual_poll_folder(handler, directory, interval=10):
    """
    watchdogが機能しないネットワークドライブ用のフォールバック手動ポーリング関数
    """
    logger.info(f"  -> 起動: 手動フォールバック監視 (間隔: {interval}秒)")
    
    # 初回のファイルリストを取得
    try:
        seen_files = set(os.listdir(directory))
    except FileNotFoundError:
        logger.error(f"[手動監視] 致命的エラー: 監視対象フォルダが見つかりません: {directory}")
        return

    while True:
        try:
            time.sleep(interval)
            current_files = set(os.listdir(directory))
            new_files = current_files - seen_files

            if new_files:
                logger.info(f"[手動監視] {len(new_files)}件の新規ファイルを検知")
                for filename in new_files:
                    filepath = os.path.join(directory, filename)
                    logger.info(f"  -> 手動検知: {filepath}")
                    # _processの中でDebounce処理が呼ばれるため、ここでは直接呼び出す
                    handler._process(filepath)
            
            seen_files = current_files

        except FileNotFoundError:
            logger.warning(f"[手動監視] 監視対象フォルダが見つかりません: {directory} (60秒後に再試行)")
            time.sleep(60)
        except Exception as e:
            logger.error(f"[手動監視] ポーリング中にエラー: {e}", exc_info=True)
            time.sleep(30)


if __name__ == "__main__":
    print("\n\n")
    logger.info("==========================================")
    logger.info("🚀 監視プロセス Ver 3.9.2 (Final Fix)")
    logger.info("==========================================")

    observer = Observer()
    CASES_ROOT = os.path.join(BASE_DIR, "data", "cases") 

    # Downloads
    if os.path.exists(WATCH_DIR_DOWNLOADS):
        observer.schedule(DownloadsHandler(), WATCH_DIR_DOWNLOADS, recursive=False)
        logger.info(f"✅ DL監視: {WATCH_DIR_DOWNLOADS}")

    # Scan
    scan_dir, user_name = get_target_scan_folder()
    if not os.path.exists(scan_dir):
        try: os.makedirs(scan_dir, exist_ok=True)
        except: pass

    if ScannerService and os.path.exists(scan_dir):
        scan_handler = ScanHandler(inbox_path=scan_dir, processed_root=CASES_ROOT)
        observer.schedule(scan_handler, scan_dir, recursive=False)
        logger.info(f"✅ [watchdog] Scan監視: {scan_dir}")

        # --- フォールバックの手動監視スレッドを開始 ---
        manual_poll_thread = threading.Thread(
            target=manual_poll_folder,
            args=(scan_handler, scan_dir),
            daemon=True
        )
        manual_poll_thread.start()
        logger.info(f"✅ [Fallback] 手動スキャン監視を開始しました。")

    # Z: Drive RAG watch
    if Z_DRIVE_PATH.exists():
        rag_will_handler = WillRAGSourceHandler()
        observer.schedule(rag_will_handler, str(Z_DRIVE_PATH), recursive=True) # Recursive for subfolders
        logger.info(f"✅ Z:ドライブ RAG監視: {Z_DRIVE_PATH} (遺言フォルダ内のみ)")
    else:
        logger.warning(f"⚠️ Z:ドライブ ({Z_DRIVE_PATH}) が見つかりません。RAG監視はスキップされます。")

    # Gmail
    t = threading.Thread(target=run_gmail_watcher, daemon=True)
    t.start()
    
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()