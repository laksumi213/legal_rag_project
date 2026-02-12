# run_watcher.py (Ver 4.8 - 完全統合・ユーザーフォルダ対応版)

import logging
import os
import sys
import time
import threading
import traceback
from pathlib import Path
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv() 

# ==========================================
# 1. ログ設定
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
# 2. 監視ライブラリの設定
# ==========================================
try:
    from watchdog.observers.polling import PollingObserver as Observer
    logger.info("ℹ️ Windows 互換モード (PollingObserver) で起動します。")
except ImportError:
    from watchdog.observers import Observer

from watchdog.events import FileSystemEventHandler

# ==========================================
# 3. パス解決 & モジュールインポート
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

os.environ["IS_WATCHER_PROCESS"] = "true"

try:
    from legal_system.core.data_sync import DataSyncEngine
    from legal_system.core.database_manager import DatabaseManager
    from services.gmail_watcher_service import GmailWatcherService
    from services.scanner_service import ScannerService
    logger.info("✅ 必要なモジュールをロードしました。")
except ImportError as e:
    logger.error(f"❌ モジュールのインポートに失敗しました: {e}")
    sys.exit(1)

# ==========================================
# 4. フォルダパス設定関数
# ==========================================
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
    """
    NASのスキャンフォルダ + ユーザー名フォルダ を特定する
    """
    nas_root = r"\\192.168.11.20\行政書士法人チェスター\08.その他\スキャン"
    
    # ユーザー名（プロフィール名）の取得
    target_name = "Unknown"
    try:
        db = DatabaseManager()
        user_info = db.get_current_user_info()
        target_name = user_info.get("name", "Unknown") 
        if not target_name or target_name == "Unknown":
            target_name = os.environ.get("USERNAME", "Guest")
    except:
        target_name = os.environ.get("USERNAME", "Guest")

    target_path = os.path.join(nas_root, target_name)
    
    if not os.path.exists(target_path):
        if os.path.exists(nas_root):
            try:
                os.makedirs(target_path, exist_ok=True)
                logger.info(f"📁 ユーザーフォルダを作成: {target_path}")
            except: pass
        else:
            # NAS自体がなければローカルフォールバック
            target_path = os.path.join(BASE_DIR, "data", "scan_inbox")
            os.makedirs(target_path, exist_ok=True)
            
    return target_path, target_name

# ==========================================
# 5. イベントハンドラー基底クラス
# ==========================================
class DebouncedEventHandler(FileSystemEventHandler):
    def __init__(self, cooldown=5.0):
        super().__init__()
        self._processed_cache = {} 
        self._cooldown = cooldown

    def _should_process(self, filepath):
        current_time = time.time()
        filename = os.path.basename(filepath)
        if filename.startswith((".", "~$")): return False
        if filename.lower().endswith((".tmp", ".crdownload", ".part", ".lock", ".ds_store", "thumbs.db")): return False

        if filepath in self._processed_cache:
            last_time = self._processed_cache[filepath]
            if current_time - last_time < self._cooldown: return False
        
        self._processed_cache[filepath] = current_time
        if len(self._processed_cache) > 1000:
            self._processed_cache = {k:v for k,v in self._processed_cache.items() if current_time - v < self._cooldown}
        return True

# ==========================================
# 6. ハンドラー実装: ダウンロードフォルダ
# ==========================================
class DownloadsHandler(DebouncedEventHandler):
    def __init__(self):
        super().__init__()
        self.syncer = DataSyncEngine()
        cases_root = os.path.join(BASE_DIR, "data", "cases")
        self.scanner = ScannerService(inbox_path=WATCH_DIR_DOWNLOADS, processed_root=cases_root) if ScannerService else None

    def _process(self, filepath):
        if not os.path.exists(filepath) or not self._should_process(filepath): return
        filename = os.path.basename(filepath)
        fn_lower = filename.lower()
        
        # A. JSON (Kintone同期)
        if fn_lower.endswith(".json"):
            keywords = ["g", "nonumber", "record", "kintone", "案件", "顧客"]
            if any(kw in fn_lower for kw in keywords):
                logger.info(f"🔍 [DL] JSON検知: {filename}")
                time.sleep(1.0)
                try:
                    if self.syncer.sync_from_kintone_json(filepath):
                        logger.info(f"   ✅ 同期成功"); os.remove(filepath)
                except Exception as e: logger.error(f"   ❌ 同期エラー: {e}")
            return

        # B. PDF/Image (請求書等)
        valid_doc_exts = (".pdf", ".jpg", ".jpeg", ".png")
        if fn_lower.endswith(valid_doc_exts):
            target_keywords = ["請求", "invoice", "bill", "payment", "領収", "見積", "納品", "g", "案件", "顧客"]
            if any(kw in fn_lower for kw in target_keywords):
                logger.info(f"🔍 [DL] 書類検知: {filename}")
                time.sleep(2.0)
                if self.scanner:
                    try: self.scanner.process_file(filepath)
                    except Exception as e: logger.error(f"   ❌ 解析エラー: {e}")

    def on_created(self, event):
        if not event.is_directory: self._process(event.src_path)
    def on_modified(self, event):
        if not event.is_directory: self._process(event.src_path)

# ==========================================
# 7. ハンドラー実装: スキャンフォルダ (NAS)
# ==========================================
class ScanHandler(DebouncedEventHandler):
    def __init__(self, inbox_path, processed_root): 
        super().__init__()
        self.inbox_path = inbox_path
        self.syncer = DataSyncEngine()
        self.service = ScannerService(inbox_path, processed_root) if ScannerService else None

    def _process(self, filepath):
        if not os.path.exists(filepath) or not self._should_process(filepath): return
        filename = os.path.basename(filepath)
        fn_lower = filename.lower()
        
        # A. 書類画像
        if fn_lower.endswith((".pdf", ".jpg", ".jpeg", ".png")):
            logger.info(f"🔍 [Scan] 書類検知: {filepath}")
            time.sleep(2.0)
            if self.service:
                try: self.service.process_file(filepath)
                except Exception as e: logger.error(f"   ❌ 解析エラー: {e}")
        
        # B. JSON
        elif fn_lower.endswith(".json"):
            logger.info(f"🔍 [Scan] JSON検知: {filepath}")
            time.sleep(1.0)
            try:
                if self.syncer.sync_from_kintone_json(filepath):
                    logger.info(f"   ✅ 同期成功"); os.remove(filepath)
            except Exception as e: logger.error(f"   ❌ 同期エラー: {e}")

    def on_created(self, event):
        if not event.is_directory: self._process(event.src_path)
    def on_modified(self, event):
        if not event.is_directory: self._process(event.src_path)

# ==========================================
# 8. ハンドラー実装: RAG (Zドライブ)
# ==========================================
Z_DRIVE_PATH = Path("Z:/")
class WillRAGSourceHandler(DebouncedEventHandler):
    def __init__(self):
        super().__init__(cooldown=30.0)
        self.scanner_service = ScannerService() if ScannerService else None

    def _is_will_document(self, filepath: Path) -> bool:
        filename = filepath.name.lower()
        if filepath.suffix.lower() not in [".docx", ".pdf"]: return False
        try:
            current_path = filepath.parent
            while current_path != current_path.parent and current_path != Z_DRIVE_PATH.parent:
                if "遺言" in current_path.name:
                    if "遺言書" in filename or "公正証書" in filename: return True
                current_path = current_path.parent
        except: pass
        return False

    def _process(self, filepath: Path):
        if not self._should_process(str(filepath)) or not filepath.exists(): return
        if not self._is_will_document(filepath): return

        logger.info(f"🔍 [Will RAG] 検知: {filepath.name}")
        time.sleep(5.0)
        if self.scanner_service:
            try: self.scanner_service.ingest_will_for_rag(filepath)
            except Exception as e: logger.error(f"   ❌ RAGエラー: {e}")

    def on_created(self, event):
        if not event.is_directory: self._process(Path(event.src_path))
    def on_modified(self, event):
        if not event.is_directory: self._process(Path(event.src_path))

# ==========================================
# 9. 手動監視 (再帰的ポーリング)
# ==========================================
def manual_poll_recursive(handler, directory, interval=5, label="Unknown"):
    """
    サブフォルダの中まで全探索する手動監視 (ポーリング)
    """
    logger.info(f"🚀 [手動監視:{label}] 起動 -> {directory}")
    seen_files = set()
    
    # 初期状態
    try:
        if os.path.exists(directory):
            for root, _, files in os.walk(directory):
                for f in files: seen_files.add(os.path.join(root, f))
    except: pass

    while True:
        try:
            time.sleep(interval)
            if not os.path.exists(directory): continue

            current_files = set()
            for root, _, files in os.walk(directory):
                for f in files: current_files.add(os.path.join(root, f))

            new_files = current_files - seen_files
            if new_files:
                logger.info(f"🔔 [手動監視:{label}] {len(new_files)}件の新規ファイルを検知")
                for filepath in new_files:
                    if os.path.exists(filepath): handler._process(filepath)
            
            seen_files = current_files
        except Exception as e:
            logger.error(f"❌ [手動監視:{label}] エラー: {e}")
            time.sleep(30)

# ==========================================
# 10. Gmail監視
# ==========================================
def run_gmail_watcher():
    logger.info("📧 Gmail監視スレッド起動")
    try:
        service = GmailWatcherService()
        if not service.service: return
        while True:
            try:
                service.poll_and_process()
                service.retry_linking_pending_notes()
            except: pass
            time.sleep(600)
    except: pass

# ==========================================
# Main
# ==========================================
if __name__ == "__main__":
    print("\n")
    logger.info("==========================================")
    logger.info("🚀 監視プロセス Ver 4.8 (Integrated Final)")
    logger.info("==========================================")

    observer = Observer()
    CASES_ROOT = os.path.join(BASE_DIR, "data", "cases") 

    # A. Downloads
    if os.path.exists(WATCH_DIR_DOWNLOADS):
        dl_handler = DownloadsHandler()
        observer.schedule(dl_handler, WATCH_DIR_DOWNLOADS, recursive=False)
        threading.Thread(target=manual_poll_recursive, args=(dl_handler, WATCH_DIR_DOWNLOADS, 5, "DL"), daemon=True).start()
        logger.info(f"✅ DL監視: {WATCH_DIR_DOWNLOADS}")

    # B. Scan (User Folder)
    scan_dir, user_name = get_target_scan_folder()
    if os.path.exists(scan_dir):
        logger.info(f"👤 監視対象ユーザー: {user_name}")
        scan_handler = ScanHandler(inbox_path=scan_dir, processed_root=CASES_ROOT)
        observer.schedule(scan_handler, scan_dir, recursive=True)
        threading.Thread(target=manual_poll_recursive, args=(scan_handler, scan_dir, 5, "NAS"), daemon=True).start()
        logger.info(f"✅ NAS監視: {scan_dir}")

    # C. RAG (Z Drive)
    if Z_DRIVE_PATH.exists():
        rag_handler = WillRAGSourceHandler()
        observer.schedule(rag_handler, str(Z_DRIVE_PATH), recursive=True)
        logger.info(f"✅ RAG監視(Zドライブ): {Z_DRIVE_PATH}")

    # D. Gmail
    threading.Thread(target=run_gmail_watcher, daemon=True).start()

    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()