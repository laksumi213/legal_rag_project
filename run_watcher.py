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

# --- 既存サービスのインポート ---
from legal_system.core.data_sync import DataSyncEngine
from services.gmail_watcher_service import GmailWatcherService

# --- ★新規サービスのインポート ---
try:
    from services.scanner_service import ScannerService
except ImportError:
    ScannerService = None
    logger.warning("⚠️ ScannerService が見つかりません。スキャナー監視機能はスキップされます。")

# ==========================================
# ★ 設定: 監視ディレクトリ (動的設定)
# ==========================================

# 1. Kintone連携用 (各PCのダウンロードフォルダを自動取得)
#    Windowsなら "C:\Users\{ユーザー名}\Downloads" になります
WATCH_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

# 2. スキャナー監視用 (テスト用)
#    ユーザー名を自動取得して監視フォルダを決定
def get_target_scan_folder():
    """スキャン監視フォルダの特定（ユーザー名対応）"""
    # .envで指定があればそれを優先、なければログインユーザー名を使用
    target_name = os.getenv("TARGET_USER_NAME")
    if not target_name:
        try:
            target_name = os.getlogin()
        except:
            target_name = os.environ.get("USERNAME", "Unknown")
    
    # NASパス + ユーザー名
    # 実際のNASパスに合わせて修正してください
    nas_root = r"\\192.168.11.20\行政書士法人チェスター\08.その他\スキャン"
    target_path = os.path.join(nas_root, target_name)
    return target_path, target_name

# ==========================================
# 1. Kintone JSON 監視ハンドラ
# ==========================================
class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        time.sleep(2)
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        if event.is_directory: return
        filename = os.path.basename(event.src_path)
        
        # ダウンロードフォルダは他のファイルも多いため、厳密にフィルタリング
        # "G"で始まり ".json" で終わるファイルのみ反応
        if filename.startswith("G") and filename.endswith(".json"):
            logger.info(f"📥 連携JSONを検知: {filename}")
            
            # ダウンロード完了待ち (ブラウザの書き込み完了を待つ)
            time.sleep(1.0) 
            
            # ファイルロック対策のリトライループ
            for i in range(5):
                try:
                    if self.syncer.sync_from_kintone_json(event.src_path):
                        logger.info(f"✅ DB同期完了: {filename}")
                        
                        # 成功したら、未紐付けメモの再チェックを実行
                        try:
                            gmail_svc = GmailWatcherService()
                            if gmail_svc.service:
                                gmail_svc.retry_linking_pending_notes()
                        except: pass
                        
                        # 【修正】処理済みファイルは自動削除する
                        try:
                            os.remove(event.src_path)
                            logger.info(f"🗑️ 処理済みファイルを削除しました: {filename}")
                        except Exception as e:
                            logger.warning(f"⚠️ ファイル削除に失敗しました（動作には影響ありません）: {e}")
                        
                        break # 成功したらループを抜ける
                    else:
                        # まだ書き込み途中などでJSONとして壊れている場合
                        time.sleep(1.0)
                except Exception as e:
                    # ロックされている場合など
                    time.sleep(1.0)
            else:
                # ループを抜けてしまった場合（失敗）
                logger.warning(f"⚠️ 同期スキップ (ファイルロックまたは形式エラー): {filename}")
                # 失敗したファイルは削除せず残す（確認用）

# ==========================================
# 2. スキャナー PDF 監視ハンドラ
# ==========================================
class ScanHandler(FileSystemEventHandler):
    def __init__(self, inbox_path, processed_root): 
        self.service = None
        if ScannerService:
            self.service = ScannerService(inbox_path, processed_root)

    def on_created(self, event):
        if not self.service: return
        if event.is_directory: return
        
        filename = os.path.basename(event.src_path)
        if filename.lower().endswith(".pdf"):
            logger.info(f"🖨️ スキャン検知: {filename}")
            self.service.process_file(event.src_path)

# ==========================================
# 3. Gmail 監視ループ
# ==========================================
def run_gmail_watcher():
    logger.info("📧 Gmail監視スレッドを開始します...")
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
            service.poll_and_process()
            service.retry_linking_pending_notes()
        except Exception as e:
            logger.error(f"Gmail Watcher Loop Error: {e}")
        time.sleep(1800)

# ==========================================
# メイン実行ブロック
# ==========================================
if __name__ == "__main__":
    logger.info(f"🚀 システム監視プロセス起動")

    # 1. Kintone監視設定 (ダウンロードフォルダ)
    #    os.path.expanduser("~") でユーザーフォルダを自動取得
    #    WATCH_DIR は冒頭で定義済み
    if not os.path.exists(WATCH_DIR):
        logger.warning(f"⚠️ ダウンロードフォルダが見つかりません: {WATCH_DIR}")
        # 見つからない場合はカレントディレクトリ配下を作成して代用
        WATCH_DIR = os.path.join(BASE_DIR, "data", "kintone_watch")
        os.makedirs(WATCH_DIR, exist_ok=True)
    
    logger.info(f"📂 Kintone監視ターゲット (Downloads): {WATCH_DIR}")

    # 2. スキャナー監視設定 (NAS)
    scan_dir, user_name = get_target_scan_folder()
    
    # 案件フォルダのルート (移動先)
    CASES_ROOT = os.path.join(BASE_DIR, "data", "cases") 
    # 本番運用時は: CASES_ROOT = r"\\192.168.11.20\行政書士法人チェスター\01.個別ＪＯＢ"

    # A. Gmail監視開始
    gmail_thread = threading.Thread(target=run_gmail_watcher, daemon=True)
    gmail_thread.start()

    # B. フォルダ監視開始
    observer = Observer()

    # Kintone JSON監視登録
    json_handler = JsonHandler()
    observer.schedule(json_handler, WATCH_DIR, recursive=False)

    # スキャナー監視登録
    if ScannerService:
        if os.path.exists(scan_dir):
            scan_handler = ScanHandler(inbox_path=scan_dir, processed_root=CASES_ROOT)
            observer.schedule(scan_handler, scan_dir, recursive=False)
            logger.info(f"📂 スキャナー監視ターゲット: {scan_dir}")
        else:
            logger.warning(f"⚠️ スキャンフォルダが見つかりません: {scan_dir}")
            logger.warning(f"   (ユーザー名 '{user_name}' のフォルダがNASにあるか確認してください)")

    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 監視を停止します。")
        observer.stop()
    
    observer.join()