# src/legal_system/ui/components/sidebar.py

import os

import streamlit as st

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)

# マスタ更新スクリプトのインポート
try:
    from update_bank_master import (
        download_data,
        get_remote_last_commit_date,
        load_local_state,
        save_local_state,
    )

    HAS_UPDATE_SCRIPT = True
except ImportError:
    HAS_UPDATE_SCRIPT = False


# ★最適化: ttlを3600秒(1時間)に延長し、st.cache_dataに変更して高速化
@st.cache_data(ttl=3600, show_spinner=False)
def check_update_status_cached():
    """外部API(GitHub)への問い合わせ結果を長時間キャッシュする"""
    if not HAS_UPDATE_SCRIPT:
        return 2, "更新スクリプトなし"

    banks_path = os.path.join(ROOT_DIR, "data", "zengin", "banks.json")
    if not os.path.exists(banks_path):
        return 1, "銀行データ未取得"

    try:
        # ここで外部通信が発生する
        remote = get_remote_last_commit_date()
        local = load_local_state().get("last_commit_date", "")
        if remote and remote != local:
            return 1, f"更新あり ({remote[:10]})"
        return 0, "最新"
    except Exception:
        return 0, "確認不可"


def render_sidebar(db, current_user_info: dict) -> str:
    with st.sidebar:
        # ========================================
        # 1. 作業メニュー
        # ========================================
        st.title("🗂️ 業務メニュー")
        # st.info(f"👤 **{current_user_info['name']}**")
        # st.divider()

        if "current_menu" not in st.session_state:
            st.session_state["current_menu"] = "🏠 案件概要・基本情報"

        # st.markdown(
        #     "<p style='font-size: 1.1rem; font-weight: bold; margin-bottom: -10px;'>作業メニュー</p>",
        #     unsafe_allow_html=True
        # )

        menu_options = [
            "🏠 案件概要・基本情報",
            "🏦 銀行口座 登録",
            "📈 証券・その他資産",
            "🏘️ 不動産 登録",
            "🌐 登記情報取得",
            "🖨️ 宛名ラベル作成",
            "✅ タスク管理",
            "📊 進捗ダッシュボード",
        ]

        try:
            default_index = menu_options.index(st.session_state["current_menu"])
        except ValueError:
            default_index = 0

        menu = st.radio(
            "作業メニュー",
            menu_options,
            index=default_index,
            key="menu_radio",
            label_visibility="collapsed",
        )

        if menu != st.session_state["current_menu"]:
            st.session_state["current_menu"] = menu
            st.rerun()

        st.divider()

        # ========================================
        # 2. 業務設定・プロフィール
        # ========================================
        st.title("👤プロフィール")
        # st.info(f"👤 **{current_user_info['name']}**")
        st.caption(f"氏名:  **{current_user_info['name']}**")
        st.caption(
            f"所属: **{current_user_info['dept']} | Tel: {current_user_info['phone']}**"
        )

        with st.expander("⚙️ プロフィール編集"):
            with st.form("user_profile_form"):
                new_name = st.text_input("表示名", value=current_user_info["name"])
                new_dept = st.text_input("所属部署", value=current_user_info["dept"])
                new_phone = st.text_input("内線/直通", value=current_user_info["phone"])
                if st.form_submit_button("更新"):
                    db.register_user(
                        current_user_info["id"], new_name, new_dept, new_phone
                    )
                    st.success("更新しました")
                    st.rerun()

        st.divider()

        # ========================================
        # 3. 銀行マスタ管理 (キャッシュ利用)
        # ========================================
        st.subheader("🏦 銀行マスタ")
        # キャッシュされた関数を呼び出す（通信が発生しないので一瞬で終わる）
        status_code, info = check_update_status_cached()
        if status_code == 1:
            st.warning(f"💡 {info}")
        else:
            st.caption(f"✅ {info}")

        if st.button("🔄 マスタ強制更新", use_container_width=True):
            if HAS_UPDATE_SCRIPT:
                with st.status("更新中...") as s:
                    download_data()
                    save_local_state(get_remote_last_commit_date())
                    st.cache_data.clear()  # 更新後はキャッシュをクリア
                    s.update(label="完了！", state="complete")
                st.rerun()

    return menu
