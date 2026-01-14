# src/legal_system/ui/Home.py

import os
import sys
import time

import streamlit as st
from dotenv import load_dotenv

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))

# Home.py から見て3つ上がプロジェクトのルート(ROOT)になります
# ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.abspath(os.path.join(current_dir, "../../../"))

# Pythonにプログラムの場所を教える(srcフォルダを追加)
src_path = os.path.abspath(os.path.join(current_dir, "../../"))
if src_path not in sys.path:
    sys.path.append(src_path)

from legal_system.core.database_manager import DatabaseManager

# 環境変数の読み込み
load_dotenv()

# ==========================================
# 1. アプリケーションの初期設定
# ==========================================
st.set_page_config(page_title="実務Q&A | 法務RAG", layout="wide", page_icon="⚖️")

# ==========================================
# 2. 起動時プリロード処理 (真っ白画面・フリーズ対策)
# ==========================================
# 画面が真っ白になるのを防ぐため、重いモジュールを読み込む前にタイトルを即座に表示します
if "is_initialized" not in st.session_state:
    st.title("💬 金融機関手続 Q&A")
    st.info("🚀 システムを起動しています。しばらくお待ちください...")

    # statusコンポーネントでロードの進捗を可視化します
    with st.status("📦 業務モジュールをロード中...", expanded=True) as status:
        # 重いライブラリをバックグラウンドでロード
        from legal_system.core.preload import warm_up_modules

        st.write("🔧 重いライブラリ（PDF/AI系）を展開しています...")
        warm_up_modules()

        st.write("🧠 AIエンジン（Gemini/Ollama）を準備中...")
        from legal_system.core.ai_factory import AIFactory

        st.write("🗄️ データベース接続を確認中...")
        db_manager = DatabaseManager()

        status.update(label="✅ 準備完了！", state="complete", expanded=False)

    st.session_state["is_initialized"] = True
    time.sleep(0.5)
    st.rerun()

# --- 初期化完了後の実体取得 ---
db_manager = DatabaseManager()
current_user = db_manager.get_current_user_info()

# AI関連のインポート（キャッシュされているため高速）
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from legal_system.core.ai_factory import AIFactory

# 銀行マスタ更新スクリプトのインポート
try:
    from update_bank_master import (
        download_data,
        get_remote_last_commit_date,
        load_local_state,
        save_local_state,
    )
except ImportError:
    get_remote_last_commit_date = None

# ==========================================
# 3. ヘルパー関数
# ==========================================


@st.cache_resource(ttl=60)
def check_update_status():
    """銀行データの更新が必要か判定"""
    if not get_remote_last_commit_date:
        return 2, "更新スクリプトが見つかりません"
    banks_path = os.path.join(ROOT_DIR, "data", "zengin", "banks.json")
    if not os.path.exists(banks_path):
        return 1, "銀行データが未取得です"
    remote = get_remote_last_commit_date()
    local = load_local_state().get("last_commit_date", "")
    if remote and remote != local:
        return 1, f"新着データがあります ({remote})"
    return 0, "最新の状態です"


def load_company_rules():
    """社内規定ファイルを読み込む"""
    path = os.path.join(ROOT_DIR, "data", "rules", "company_rules.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "規定ファイルが見つかりません。"


def run_rag_search(query, mode, llm):
    """RAGによる検索と回答生成"""
    vector_store = AIFactory.get_vector_store()
    docs = vector_store.similarity_search(query, k=4)
    context = "\n".join([d.page_content for d in docs])

    # 結論と箇条書きのみを求めるプロンプト
    prompt = ChatPromptTemplate.from_template(
        "結論と箇条書きのみで回答してください。挨拶は不要です。\n\n"
        "【社内ルール】\n{rules}\n\n"
        "【参照資料】\n{context}\n\n"
        "質問: {question}"
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {"rules": load_company_rules(), "context": context, "question": query}
    ), docs


# ==========================================
# 4. メイン UI
# ==========================================
def main():
    # --- サイドバー ---
    with st.sidebar:
        st.title("⚖️ 業務メニュー")
        
        # ユーザー情報の表示
        st.info(f"👤 **{current_user['name']}**")
        st.caption(f"所属: {current_user['dept']} | Tel: {current_user['phone']}")

        # ▼▼▼ ユーザー編集機能 (追加) ▼▼▼
        with st.expander("⚙️ プロフィール編集"):
            with st.form("user_profile_form"):
                new_name = st.text_input("表示名", value=current_user["name"])
                new_dept = st.text_input("所属部署", value=current_user["dept"])
                new_phone = st.text_input("内線/直通", value=current_user["phone"])
                
                submitted = st.form_submit_button("更新する")
                if submitted:
                    try:
                        db_manager.register_user(
                            windows_id=current_user["id"],
                            display_name=new_name,
                            department=new_dept,
                            phone=new_phone
                        )
                        st.success("更新しました！")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新エラー: {e}")
        # ▲▲▲ ここまで ▲▲▲

        st.divider()

        # 銀行データ更新セクション
        st.subheader("🏦 銀行マスタ管理")
        status_code, info = check_update_status()

        if status_code == 1:
            st.warning(f"💡 {info}")
        else:
            st.success(f"✅ {info}")

        # 強制更新ボタンを常駐
        if st.button("🔄 銀行データを強制更新", use_container_width=True):
            with st.status("🔄 銀行データを更新中...", expanded=True) as s:
                progress_bar = st.progress(0)

                def cb(cur, tot, msg):
                    progress_bar.progress(min(cur / tot, 1.0))

                download_data(progress_callback=cb)
                if get_remote_last_commit_date:
                    save_local_state(get_remote_last_commit_date())
                s.update(label="✅ 更新が完了しました！", state="complete")
            st.rerun()

    # --- メインチャットエリア ---
    st.title("💬 金融機関手続 Q&A")

    ai_mode = st.radio(
        "AIモード選択",
        ("☁️ Cloud (Gemini) - 一般用", "🔒 Secure (Local) - 個人情報用"),
        horizontal=True,
        label_visibility="collapsed",
    )

    # モードに応じたモデル取得
    mode_key = "cloud" if "Cloud" in ai_mode else "local"
    llm = AIFactory.get_llm(mode_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 履歴の表示
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # 質問入力
    if prompt := st.chat_input(
        "調べたい内容を入力してください（例：三菱UFJ銀行の印鑑証明書期限）"
    ):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response, docs = run_rag_search(prompt, mode_key, llm)
                st.write(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )


if __name__ == "__main__":
    main()