# src/legal_system/ui/pages/01_案件詳細_統合管理.py

import os
import sys
import threading
import time
import pyperclip  # クリップボード用
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy.orm import joinedload
from st_keyup import st_keyup

# ==========================================
# 1. パス解決 & 環境設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
src_dir = os.path.join(ROOT_DIR, "src")

if src_dir not in sys.path:
    sys.path.append(src_dir)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(
    page_title="高度案件管理 (AI支援)", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. モジュールインポート
# ==========================================
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address, Case, Deceased, H_AddressHistory, H_ContactLink, Heir
)
from services.folder_service import open_local_folder, find_case_folder
from services.deceased_service import update_case_folder_path

# ★新機能サービスのインポート
try:
    from services.logistics_service import LogisticsService
    from services.rag_search_service import RagSearchService
    # 共通コンポーネントのインポート
    from legal_system.ui.components.document_viewer import render_enhanced_document_viewer
except ImportError:
    st.error("新機能サービス(logistics_service, rag_search_service)が見つかりません。src/services/に配置してください。")
    LogisticsService = None
    RagSearchService = None

# ==========================================
# 4. ヘルパー関数 & JS
# ==========================================
def run_background_warmup():
    if "modules_warmed_up" in st.session_state: return
    try:
        from legal_system.core.preload import warm_up_modules
        warm_up_modules()
        st.session_state["modules_warmed_up"] = True
    except: pass

if "warmup_thread_started" not in st.session_state:
    t = threading.Thread(target=run_background_warmup, daemon=True)
    t.start()
    st.session_state["warmup_thread_started"] = True

# 検索（案件選択）ロジック
def search_cases_simple(session, keyword: str):
    base_query = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    )
    if not keyword:
        return base_query.order_by(Case.created_at.desc()).limit(10).all()

    clean_key = f"%{keyword.strip()}%"
    return base_query.filter(
        Case.case_number.ilike(clean_key) | 
        Case.client_name.ilike(clean_key)
    ).limit(10).all()

# ==========================================
# 5. メイン処理 (Main)
# ==========================================
def main():
    db = DatabaseManager()
    session = db._get_session()
    current_user_info = db.get_current_user_info()

    # --- サイドバー構成 ---
    with st.sidebar:
        st.title("🧠 高度AI支援メニュー")
        st.info(f"担当: {current_user_info['name']}")
        st.caption("※基本情報の編集や口座登録は「Home」画面で行ってください。")
        
        st.divider()
        
        # 簡易案件検索 (Homeで選択した案件を引き継ぐが、ここでも切り替え可能にする)
        st.subheader("📂 対象案件切替")
        search_query = st.text_input("案件番号/氏名で検索", key="side_search")
        
        # 1. まず検索条件で案件を取得
        filtered_cases = search_cases_simple(session, search_query)
        
        # ==========================================
        # ★修正: 選択中の案件をリストに強制追加するロジック
        # ==========================================
        current_id = st.session_state.get("selected_case_id")
        
        if current_id:
            # 現在の検索結果リストの中に、選択中の案件が含まれているかチェック
            is_included = any(c.case_id == current_id for c in filtered_cases)
            
            if not is_included:
                # 含まれていない場合（過去の案件など）、DBから取得してリストの先頭に追加する
                target_case_obj = session.query(Case).get(current_id)
                if target_case_obj:
                    filtered_cases.insert(0, target_case_obj)

        # 選択肢辞書の作成
        case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in filtered_cases}
        
        # セッションから選択状態を復元（インデックス特定）
        index = 0
        if current_id in case_options.values():
            keys = list(case_options.keys())
            vals = list(case_options.values())
            index = vals.index(current_id)
            
        selected_label = st.selectbox("選択", list(case_options.keys()), index=index)
        
        # 選択されたらIDを更新
        if selected_label:
            st.session_state["selected_case_id"] = case_options[selected_label]

    # --- メインエリア ---
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning("👈 サイドバーまたはHome画面で案件を選択してください。")
        session.close()
        return

    # 案件データ取得
    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).get(target_case_id)

    if not current_case:
        st.error("案件データが見つかりません")
        session.close(); return

    # --- ヘッダー情報 (Read-only) ---
    d_name = "未登録"
    if current_case.deceased_ref:
        d_name = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}"

    st.title(f"AI支援モード: {current_case.client_name} 様")
    st.caption(f"案件番号: {current_case.case_number} | 被相続人: {d_name}")
    
    # -------------------------------------------------------------
    # ★修正: クイックリンク (常時表示 & 両方表示)
    # -------------------------------------------------------------
    with st.container(border=True):
        col_link, col_folder = st.columns([1, 3], gap="medium")
        
        # 1. Kintoneボタン
        with col_link:
            if current_case.kintone_record_id:
                url = f"https://chester-tax.cybozu.com/k/242/show#record={current_case.kintone_record_id}"
                st.link_button("🔗 Kintoneを開く", url, use_container_width=True)
            else:
                st.button("🔗 連携なし", disabled=True, use_container_width=True)
        
        # 2. フォルダパス操作 (表示・編集・開く)
        with col_folder:
            path_val = current_case.folder_path or ""
            c_input, c_btn = st.columns([4, 1])
            
            new_path = c_input.text_input(
                "フォルダパス", 
                value=path_val, 
                label_visibility="collapsed", 
                placeholder="フォルダパス (\\\\server\\...)"
            )
            
            if c_btn.button("📂 開く", use_container_width=True):
                if new_path:
                    open_local_folder(new_path)
                    # 変更があれば保存
                    if new_path != path_val:
                        update_case_folder_path(target_case_id, new_path)
                        st.rerun()
                else:
                    st.warning("パス未入力")
            
            # Enterキー等で確定した場合の保存
            if new_path != path_val:
                update_case_folder_path(target_case_id, new_path)

    st.divider()

    # =========================================================
    # ★機能別タブ構成 (AI特化)
    # =========================================================
    tab_notary, tab_rag = st.tabs([
        "⚖️ 公証役場・アクセス (Logistics)", 
        "📚 銀行RAG・ナレッジ (Knowledge)"
    ])

    # ---------------------------------------------------------
    # タブ1: 公証役場検索 (AIアドバイス版)
    # ---------------------------------------------------------
    with tab_notary:
        st.subheader("⚖️ 公証役場アクセス・選定支援")
        st.caption("Geminiが住所から最寄りの公証役場を推論し、アクセス方法を提案します。")
        
        # 1. 検索起点の住所取得（DBから）
        origin_address = ""
        if current_case.deceased_ref and current_case.deceased_ref.heirs:
            contractor = next((h for h in current_case.deceased_ref.heirs if h.is_contracting_party), None)
            if contractor:
                addr_link = session.query(H_AddressHistory).filter_by(heir_id=contractor.id, is_current_address=True).first()
                if addr_link:
                    addr_obj = session.query(Address).get(addr_link.address_id)
                    if addr_obj:
                        origin_address = f"{addr_obj.prefecture}{addr_obj.city_ward_town}{addr_obj.street_address}"

        # 2. 入力フォーム
        col_in, col_btn = st.columns([3, 1])
        target_addr = col_in.text_input("検索起点（依頼者住所など）", value=origin_address, key="notary_search_addr")
        
        if col_btn.button("🔍 AIに相談する", type="primary", key="btn_ask_notary"):
            if not target_addr:
                st.error("住所が入力されていません")
            elif not LogisticsService:
                st.error("LogisticsService がロードされていません")
            else:
                with st.spinner("AIが経路と公証役場を調査中..."):
                    logistics = LogisticsService()
                    ai_response = logistics.consult_nearest_notaries(target_addr)
                    st.session_state["notary_advice"] = ai_response

        # 3. 結果表示エリア
        if "notary_advice" in st.session_state:
            st.divider()
            c_res_head, c_res_copy = st.columns([4, 1])
            c_res_head.markdown("##### 🤖 AIからの提案")
            if c_res_copy.button("📋 コピー"):
                try:
                    pyperclip.copy(st.session_state["notary_advice"])
                    st.toast("コピーしました", icon="✅")
                except:
                    st.warning("ローカル環境外ではコピーできません")

            st.markdown(
                f"""
                <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid #d33682;">
                    {st.session_state["notary_advice"]}
                </div>
                """, 
                unsafe_allow_html=True
            )

    # ---------------------------------------------------------
    # タブ2: 銀行RAG・ナレッジ検索
    # ---------------------------------------------------------
    with tab_rag:
        st.subheader("📚 銀行手続・ナレッジ検索")
        st.caption("社内規定、銀行マスタ、および過去の提出書類から検索します。")

        rag_service = RagSearchService() if RagSearchService else None
        
        if not rag_service:
            st.error("RAGサービスが利用できません。")
        else:
            # 検索ボックス
            query = st.text_input("質問・検索キーワード", placeholder="例: 三菱UFJの残高証明に必要な書類は？ / 鈴木一郎の戸籍")
            
            col_knowledge, col_docs = st.columns([1, 1])
            
            if query:
                # 1. 知識検索 (LLM回答)
                with col_knowledge:
                    st.markdown("##### 🤖 AI回答 (規定・マスタ)")
                    with st.spinner("規定を検索中..."):
                        answer = rag_service.search_bank_rules(query)
                        st.info(answer)

                # 2. 過去書類検索 (ファイル一覧)
                with col_docs:
                    st.markdown("##### 📄 関連する過去書類 (個人情報含む)")
                    docs = rag_service.search_past_documents(query)
                    
                    if docs:
                        for doc in docs:
                            with st.expander(f"📄 {doc['filename']}"):
                                st.caption(f"登録日: {doc['registered_at']} | 種別: {doc['doc_type']}")
                                
                                # --- 多機能PDFビューア表示 ---
                                pdf_path = os.path.join(ROOT_DIR, "data", "demo_bank_docs", doc['filename'])
                                if os.path.exists(pdf_path):
                                    try:
                                        with open(pdf_path, "rb") as f:
                                            pdf_bytes = f.read()
                                        
                                        # 共通ビューアを呼び出す
                                        render_enhanced_document_viewer(
                                            file_bytes=pdf_bytes,
                                            file_type="application/pdf",
                                            # ファイルごとにユニークなキーを設定
                                            key_prefix=f"rag_viewer_{doc['filename']}"
                                        )
                                    except Exception as e:
                                        st.error(f"プレビュー生成中にエラーが発生しました: {e}")
                                else:
                                    st.warning(f"ファイルが見つかりません: {doc['filename']}")
                    else:
                        st.caption("該当する過去書類は見つかりませんでした。")

    session.close()

if __name__ == "__main__":
    main()