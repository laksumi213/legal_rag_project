# src/legal_system/ui/components/case_search.py

import streamlit as st
from st_keyup import st_keyup
from src.services.search_service import search_cases_enhanced
# ★追加: JSヘルパーのインポート
from src.legal_system.ui.utils.js_helper import enable_keyboard_shortcuts

def render_case_search(session) -> int:
    """
    案件検索バーを描画し、選択された案件IDを返す。
    未選択の場合は None を返す。
    """
    # 検索バー
    search_query = st_keyup(
        "🔍 案件を検索 ⌨️ ショートカット: [Alt+S] 検索 | [Alt+O] フォルダを開く | [Alt+K] Kintone連携", 
        placeholder="案件番号、氏名、電話番号で検索...",
        key="case_search_bar",
        debounce=300
    )
    
    # ★追加: コンポーネント描画後にJSを実行 (オートフォーカス & ショートカット有効化)
    # これにより、検索バーが表示されると同時にフォーカス制御が機能します
    enable_keyboard_shortcuts(search_keyword="案件番号")

    filtered_cases = search_cases_enhanced(session, search_query)
    
    # 現在の選択状態
    target_case_id = st.session_state.get("selected_case_id")

    # 検索結果が1件だけの場合の自動選択ロジック
    if search_query:
        if len(filtered_cases) == 1:
            auto_target = filtered_cases[0].case_id
            if target_case_id != auto_target:
                st.session_state["selected_case_id"] = auto_target
                st.rerun()
                
        # 検索結果の表示
        if filtered_cases:
            st.caption(f"検索結果: {len(filtered_cases)}件")
            # ボタンのスタイル調整（左寄せ）
            st.markdown("""<style>div[data-testid="stButton"] button { text-align: left; display: block; width: 100%; }</style>""", unsafe_allow_html=True)
            
            for c in filtered_cases:
                d_name = "未登録"
                if c.deceased_ref:
                    d_name = f"{c.deceased_ref.name_last} {c.deceased_ref.name_first}"
                
                label_text = f"【{c.case_number}】 {c.client_name} 様 (被相続人: {d_name})"
                btn_type = "primary" if target_case_id == c.case_id else "secondary"
                
                if st.button(label_text, key=f"sel_{c.case_id}", use_container_width=True, type=btn_type):
                    st.session_state["selected_case_id"] = c.case_id
                    st.rerun()
            st.divider()
        else:
            st.warning("該当する案件は見つかりませんでした。")
    
    # 検索なし＆結果あり＆未選択 の場合、先頭をデフォルト選択（オプション）
    if not target_case_id and filtered_cases and not search_query:
        # デフォルトでは最新の案件を選択状態にする
        target_case_id = filtered_cases[0].case_id
        st.session_state["selected_case_id"] = target_case_id

    return target_case_id