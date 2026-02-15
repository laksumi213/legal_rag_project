# src/legal_system/ui/components/case_search.py

import streamlit as st
import streamlit.components.v1 as components

from legal_system.services.search_service import search_cases_enhanced


def render_case_search(session):
    """
    案件検索コンポーネント
    - 案件番号、依頼者名、被相続人名でのインクリメンタルサーチ
    - ショートカットキー (Alt+S) 対応: Deep DOM Access (On-Demand)
    """

    placeholder_text = "案件番号(G...), 依頼者名, 被相続人名..."
    label_text = "案件を検索 (Alt+S)"

    try:
        from st_keyup import st_keyup

        search_query = st_keyup(
            label_text,
            key="global_case_search",
            placeholder=placeholder_text,
            debounce=300,
        )
    except ImportError:
        search_query = st.text_input(
            label_text, placeholder="st_keyupがインストールされていません"
        )

    # ---------------------------------------------------------
    # JavaScript: Deep DOM Access & Focus Control (Alt+S)
    # キー押下時に探索するオンデマンド方式
    # ---------------------------------------------------------
    js_code = f"""
    <script>
    (function() {{
        const TARGET_LABEL = "{label_text}";
        const TARGET_PLACEHOLDER = "案件番号";

        // Deep Search Logic
        function deepQuerySelectorAll(selector, root) {{
            root = root || document;
            const results = [];
            try {{
                const found = root.querySelectorAll(selector);
                found.forEach(el => results.push(el));
            }} catch(e) {{}}

            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {{
                if (node.shadowRoot) {{
                    results.push(...deepQuerySelectorAll(selector, node.shadowRoot));
                }}
                if (node.tagName === 'IFRAME') {{
                    try {{
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) {{
                            results.push(...deepQuerySelectorAll(selector, innerDoc));
                        }}
                    }} catch(e) {{}}
                }}
            }}
            return results;
        }}

        function findTargetInput() {{
            // A. aria-label (st_keyup標準)
            let inputs = deepQuerySelectorAll(`input[aria-label="${{TARGET_LABEL}}"]`, window.parent.document);
            // B. placeholder (フォールバック)
            if (inputs.length === 0) {{
                inputs = deepQuerySelectorAll(`input[placeholder^="${{TARGET_PLACEHOLDER}}"]`, window.parent.document);
            }}
            return inputs.length > 0 ? inputs[0] : null;
        }}

        const HANDLER_NAME = '_legalSearchKeyHandler_v2';
        const doc = window.parent.document;

        // 既存ハンドラ削除
        if (window.parent[HANDLER_NAME]) {{
            doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
        }}

        // 新規ハンドラ登録
        window.parent[HANDLER_NAME] = function(e) {{
            // Alt + S
            if (e.altKey && e.code === 'KeyS') {{
                e.preventDefault(); 
                e.stopPropagation();
                
                // ★キーを押した瞬間に探索
                const inputEl = findTargetInput();
                if (inputEl) {{
                    inputEl.focus();
                    console.log("LegalApp: Focused search box via Alt+S");
                }} else {{
                    console.warn("LegalApp: Search box not found via Alt+S.");
                }}
            }}
        }};

        doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);
        console.log("LegalApp: Search Shortcut (Alt+S) registered (On-Demand).");

    }})();
    </script>
    """

    components.html(js_code, height=0, width=0)

    # ---------------------------------------------------------
    # 検索処理 (Python側)
    # ---------------------------------------------------------
    selected_case_id = None

    if search_query:
        clean_query = search_query.replace("　", " ").strip()

        if clean_query:
            cases = search_cases_enhanced(session, clean_query)

            if cases:
                # 1件ヒットなら自動選択
                if len(cases) == 1:
                    target_case = cases[0]
                    current_selected_id = st.session_state.get("selected_case_id")

                    if current_selected_id != target_case.case_id:
                        st.session_state["selected_case_id"] = target_case.case_id
                        st.toast(
                            f"案件を自動選択しました: {target_case.client_name} 様",
                            icon="🔍",
                        )
                        st.rerun()

                st.caption(f"検索結果: {len(cases)}件")

                options = {
                    c.case_id: (
                        f"【{c.case_number or '未番'}】"
                        + "　"
                        + (c.client_name.replace(" ", "　") if c.client_name else "")
                        + "　様"
                        + "　(被相続人:　"
                        + (
                            (
                                c.deceased_ref.name_last.replace(" ", "　")
                                if c.deceased_ref.name_last
                                else ""
                            )
                            + "　"
                            + (
                                c.deceased_ref.name_first.replace(" ", "　")
                                if c.deceased_ref.name_first
                                else ""
                            )
                        )
                        if c.deceased_ref
                        else "" + "　様）"
                    )
                    for c in cases
                }

                default_idx = 0
                current_id = st.session_state.get("selected_case_id")
                if current_id in options:
                    default_idx = list(options.keys()).index(current_id)

                selected_val = st.radio(
                    "検索結果を選択:",
                    options=list(options.keys()),
                    format_func=lambda x: options[x],
                    index=default_idx,
                    label_visibility="collapsed",
                    key="search_result_radio",
                )

                if selected_val:
                    # 検索結果が選択されたら、即座に案件を更新
                    if st.session_state.get("selected_case_id") != selected_val:
                        st.session_state["selected_case_id"] = selected_val
                        st.rerun()
            else:
                st.warning("該当する案件が見つかりません")

    return st.session_state.get("selected_case_id")
