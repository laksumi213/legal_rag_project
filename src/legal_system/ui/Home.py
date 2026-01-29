# src/legal_system/ui/Home.py

import os
import sys
import threading
import time
import subprocess
import streamlit as st
from sqlalchemy.orm import joinedload
from sqlalchemy import desc

# 自動更新ライブラリ
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# ==========================================
# 1. パス解決 & 環境設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/legal_system/ui/Home.py (current_dir) -> ui -> legal_system -> src -> ROOT (3階層上)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(ROOT_DIR, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(
    page_title="案件統合管理ホーム", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. Watcher（監視プロセス）起動ロジック
# ==========================================

@st.cache_resource
def get_shared_state():
    """スレッド間で状態を共有するためのコンテナ"""
    return {"services_ready": False, "watcher_started": False}

def launch_watcher_process():
    """run_watcher.py を起動する（コンソールは統合）"""
    watcher_path = os.path.join(ROOT_DIR, "run_watcher.py")
    python_exe = sys.executable
    
    if not os.path.exists(watcher_path):
        return False, f"ファイルが見つかりません: {watcher_path} (ROOT: {ROOT_DIR})"

    try:
        # Windowsで黒い画面を別に出さない設定
        subprocess.Popen(
            [python_exe, "-u", str(watcher_path)], 
            cwd=str(ROOT_DIR),
            close_fds=True
        )
        return True, "起動成功 (ログはターミナルを確認)"
    except Exception as e:
        return False, str(e)

def background_loader():
    """バックグラウンド読込スレッド"""
    try:
        from src.legal_system.core.preload import warm_up_modules
        warm_up_modules()
        
        state = get_shared_state()
        state["services_ready"] = True

        # 自動起動の試行
        if not state.get("watcher_started"):
            success, msg = launch_watcher_process()
            if success:
                state["watcher_started"] = True
                print(f"✨ [Watcher Auto-Start] SUCCESS: {msg}")
            else:
                print(f"⚠️ [Watcher Auto-Start] FAILED: {msg}")
    except Exception as e: 
        print(f"Background loader error: {e}")

if "bg_thread_started" not in st.session_state:
    t = threading.Thread(target=background_loader, daemon=True)
    t.start()
    st.session_state["bg_thread_started"] = True

# ==========================================
# 4. コンポーネントのインポート
# ==========================================
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir, FileRegistry, IncomingNoteBuffer, AuditLog
from src.legal_system.ui.components.sidebar import render_sidebar
from src.legal_system.ui.components.case_search import render_case_search
from src.legal_system.ui.components.inbox import render_inbox
from src.legal_system.ui.components.cases.header import render_case_header

@st.cache_resource(show_spinner=False)
def get_gmail_service_silent():
    try:
        from src.services.gmail_watcher_service import GmailWatcherService
        return GmailWatcherService()
    except Exception: return None

@st.cache_resource(show_spinner=False)
def get_scanner_service_silent():
    try:
        from src.services.scanner_service import ScannerService
        return ScannerService()
    except Exception: return None

# ==========================================
# ★追加: 通知レンダリング関数
# ==========================================
def render_notifications(session):
    """
    ヘッダーに表示する通知・ステータスエリア
    """
    # 1. 未処理件数のカウント
    pending_files = session.query(FileRegistry).filter_by(status="PENDING").count()
    pending_notes = session.query(IncomingNoteBuffer).filter_by(status="PENDING").count()
    total_pending = pending_files + pending_notes
    
    # 2. 直近のアクションログ (過去5件)
    recent_actions = session.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(5).all()

    state = get_shared_state()
    
    with st.expander("🛠️ システム通知 & 監視ステータス", expanded=bool(total_pending > 0)):
        col_stat, col_noti, col_log = st.columns([1, 1.5, 2])
        
        # --- ステータス ---
        with col_stat:
            st.markdown("##### 🟢 監視プロセス")
            status_text = "稼働中" if state["watcher_started"] else "停止中"
            st.caption(f"状態: **{status_text}**")
            if st.button("🚀 監視を再起動", use_container_width=True):
                success, msg = launch_watcher_process()
                if success:
                    state["watcher_started"] = True
                    st.success(f"再起動: {msg}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"失敗: {msg}")

        # --- 通知 (Pending) ---
        with col_noti:
            st.markdown(f"##### 🔴 要確認 ({total_pending}件)")
            if total_pending == 0:
                st.caption("✅ すべて処理済みです")
            else:
                # ★修正: ボタンでページ遷移できるように変更
                if pending_files > 0:
                    if st.button(f"📄 スキャン書類: {pending_files} 件 (AI処理へ)", type="primary", use_container_width=True):
                        st.switch_page("pages/00_AI受信トレイ.py")
                
                if pending_notes > 0:
                    st.warning(f"✉️ Gmailメモ: **{pending_notes}** 件")
                    st.caption("※Gmailメモはこの画面下部の「受信トレイ」を確認してください")

        # --- アクションログ ---
        with col_log:
            st.markdown("##### 🔵 直近のアクション")
            if recent_actions:
                for log in recent_actions:
                    t_str = log.timestamp.strftime('%H:%M')
                    target = log.target[:15] + "..." if len(log.target or "") > 15 else log.target
                    st.text(f"[{t_str}] {log.action_type}: {target}")
            else:
                st.caption("履歴なし")

# ==========================================
# 5. メインアプリ処理
# ==========================================
def main():
    # 自動更新設定 (30秒)
    if st_autorefresh:
        st_autorefresh(interval=30000, limit=None, key="global_auto_refresh")

    db = DatabaseManager()
    session = db._get_session()
    current_user_info = db.get_current_user_info()

    # 1. サイドバー
    menu = render_sidebar(db, current_user_info)

    # 2. 通知エリア (New!)
    render_notifications(session)

    # 3. 受信トレイ (承認アクションの場)
    state = get_shared_state()
    if state["services_ready"]:
        gmail_svc = get_gmail_service_silent()
        scanner_svc = get_scanner_service_silent()
        if gmail_svc:
            render_inbox(session, gmail_service=gmail_svc, scanner_service=scanner_svc)
    else:
        st.caption("⏳ 連携サービス準備中...")

    st.divider()

    # 4. 案件検索
    target_case_id = render_case_search(session)
    if not target_case_id:
        st.info("👈 上記で案件を検索・選択してください。")
        session.close()
        return

    # データロード
    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.manager), joinedload(Case.operator)
    ).get(target_case_id)

    if not current_case:
        st.error("データなし")
        session.close()
        return

    render_case_header(current_case)

    # 6. コンテンツ表示 (Lazy Loading)
    if menu == "🏠 案件概要・基本情報":
        from src.legal_system.ui.components.cases.basic_info import render_basic_info
        from src.legal_system.ui.components.cases.dashboard_widgets import (
            render_manager_assignment, render_sol_info, render_kintone_tool, render_contact_logs
        )
        render_basic_info(session, target_case_id)
        st.divider(); render_manager_assignment(session, current_case)
        st.divider(); render_sol_info(session, current_case)
        st.divider(); render_kintone_tool(target_case_id)
        render_contact_logs(session, target_case_id)

    elif menu == "🏦 銀行口座 登録":
        from src.legal_system.ui.components.cases.asset_list import render_bank_account_list
        render_bank_account_list(session, target_case_id)

    elif menu == "🏘️ 不動産 登録":
        from src.legal_system.ui.components.cases.nayose_registration import render_nayose_registration
        render_nayose_registration(session, target_case_id)

    elif menu == "🌐 登記情報取得":
        from src.legal_system.ui.components.cases.registry_acquisition import render_registry_acquisition
        render_registry_acquisition(session, target_case_id)

    elif menu == "🖨️ 宛名ラベル作成":
        from src.legal_system.ui.components.label_printer_ui import render_label_printer
        render_label_printer(session, current_case, current_user_info)

    elif menu == "📈 証券・その他資産" or menu == "✅ タスク管理":
        st.info(f"メニュー: {menu} は準備中です。")

    session.close()

if __name__ == "__main__":
    main()