# src/legal_system/ui/components/cases/header.py

import streamlit as st
import streamlit.components.v1 as components
import time
import os
from sqlalchemy.orm import Session
from src.legal_system.models.tables import Case
from src.services.folder_service import open_local_folder, find_case_folder
from src.services.deceased_service import update_case_folder_path

def _search_folder_callback(case: Case, input_key: str):
    """
    検索ボタンが押されたときに実行されるコールバック関数
    """
    # 検索キーワード: G番号があればそれ、なければ氏名
    q = case.case_number if case.case_number and case.case_number.startswith("G") else case.client_name.replace(" ", "")
    
    # 検索実行
    found_path = find_case_folder(q)
    
    if found_path:
        # 1. DB更新
        update_case_folder_path(case.case_id, found_path)
        
        # 2. セッションステート（入力欄の中身）を更新
        st.session_state[input_key] = found_path
        
        st.toast(f"フォルダを発見しました: {found_path}", icon="📂")
    else:
        st.toast(f"フォルダが見つかりませんでした: {q}", icon="⚠️")

def render_case_header(case: Case):
    """
    案件詳細画面の共通ヘッダーを表示するコンポーネント
    - 案件番号、顧客名、ステータス
    - Kintoneへのリンクボタン (Alt+K)
    - フォルダパスの編集・自動検索・開くボタン (Alt+O)
    """
    if not case:
        st.error("案件データが選択されていません")
        return

    # ---------------------------------------------------------
    # JavaScript: ショートカットキー制御 (Alt+K, Alt+O)
    # キーを押した瞬間に全階層(Deep DOM)を探索する方式
    # ---------------------------------------------------------
    js_shortcuts = """
    <script>
    (function() {
        // ============================================================
        // 1. Deep DOM Search (再帰的にIframe/ShadowRootを探索)
        // ============================================================
        function deepQuerySelectorAll(selector, root) {
            root = root || document;
            const results = [];

            // 現在のルート内で検索
            try {
                const found = root.querySelectorAll(selector);
                found.forEach(el => results.push(el));
            } catch(e) {}

            // IframeやShadowRootの中へ潜る
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
                // Shadow DOM
                if (node.shadowRoot) {
                    results.push(...deepQuerySelectorAll(selector, node.shadowRoot));
                }
                // Iframe
                if (node.tagName === 'IFRAME') {
                    try {
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) {
                            results.push(...deepQuerySelectorAll(selector, innerDoc));
                        }
                    } catch(e) {
                        // Cross-origin iframe等は無視
                    }
                }
            }
            return results;
        }

        // ============================================================
        // 2. ターゲット特定ロジック (テキスト等で検索)
        // ============================================================
        function findElementByKeywords(keywords) {
            // ボタン、リンク、Streamlitボタンコンテナ
            const selector = 'button, a, div[role="button"], [data-testid="stButton"] button, [data-testid="stLinkButton"] a';
            
            // ★キーが押された瞬間に window.parent.document から全探索開始
            const candidates = deepQuerySelectorAll(selector, window.parent.document);
            
            for (let el of candidates) {
                // テキスト情報などを収集
                const textContent = (el.innerText || el.textContent || "").toLowerCase();
                const ariaLabel = (el.getAttribute("aria-label") || "").toLowerCase();
                const title = (el.getAttribute("title") || "").toLowerCase();
                
                const fullText = textContent + " " + ariaLabel + " " + title;

                // キーワードが含まれているかチェック
                if (keywords.some(kw => fullText.includes(kw.toLowerCase()))) {
                    return el;
                }
            }
            return null;
        }

        // ============================================================
        // 3. イベントハンドラ (keydown)
        // ============================================================
        const handleKeydown = function(e) {
            if (!e.altKey) return;

            // Alt + K (Kintone)
            if (e.code === 'KeyK') {
                const el = findElementByKeywords(["Kintoneで開く", "Kintone連携"]);
                if (el) {
                    e.preventDefault();
                    e.stopPropagation();
                    el.click();
                    console.log("LegalApp: Alt+K -> Kintone button clicked.");
                } else {
                    console.warn("LegalApp: Kintone button not found.");
                }
            }

            // Alt + O (Open Folder)
            if (e.code === 'KeyO') {
                // キーワードを「フォルダを開く」に限定して競合を回避
                const el = findElementByKeywords(["📂 フォルダを開く", "フォルダを開く"]);
                if (el) {
                    e.preventDefault();
                    e.stopPropagation();
                    el.click();
                    console.log("LegalApp: Alt+O -> Folder Open button clicked.");
                } else {
                    console.warn("LegalApp: Folder Open button not found.");
                }
            }
        };

        // ============================================================
        // 4. リスナー登録 (再登録対応)
        // ============================================================
        const HANDLER_NAME = '_legalAppHeaderKeyHandler_v3';
        const doc = window.parent.document;

        // 既存のリスナーがあれば削除して、重複実行を防ぐ
        if (window.parent[HANDLER_NAME]) {
            doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
        }

        // 新しいハンドラを登録
        window.parent[HANDLER_NAME] = handleKeydown;
        doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);

        console.log("LegalApp: Header Shortcuts (Alt+K, Alt+O) registered (Unique Button Name).");

    })();
    </script>
    """
    components.html(js_shortcuts, height=0, width=0)

    # ---------------------------------------------------------
    # UI コンポーネント
    # ---------------------------------------------------------
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1.5, 1.5], gap="medium")
        
        with c1:
            case_num = case.case_number or '案件番号未定'
            client_name = case.client_name or '顧客名未設定'
            st.markdown(f"### 🗂 {case_num}: {client_name} 様")
            if case.deceased_ref:
                d_last = case.deceased_ref.name_last or ""
                d_first = case.deceased_ref.name_first or ""
                d_date = case.deceased_ref.date_of_death or "不明"
                st.caption(f"被相続人: {d_last} {d_first} 様 (没年月日: {d_date})")

        with c2:
            raw_status = getattr(case, "status", None)
            current_status_label = "未着手"
            if raw_status:
                if hasattr(raw_status, "status_name"):
                    current_status_label = raw_status.status_name
                elif hasattr(raw_status, "name"):
                    current_status_label = raw_status.name
                else:
                    current_status_label = str(raw_status)
            st.metric("現在のステータス", current_status_label)

        with c3:
            st.write("☁️ **Kintone連携 (Alt+K)**")
            if case.kintone_record_id:
                url = f"https://chester-tax.cybozu.com/k/242/show#record={case.kintone_record_id}"
                st.link_button("🚀 Kintoneで開く", url, type="primary", use_container_width=True)
            else:
                st.button("未連携", disabled=True, use_container_width=True)

        st.divider()

        b1, b2, b3, b4 = st.columns([1, 1, 3, 1.2], gap="small")
        with b1:
            mgr_name = "未割当"
            if case.manager:
                mgr_name = case.manager.name if hasattr(case.manager, "name") else str(case.manager)
            st.info(f"👮 担当: **{mgr_name}**")
        with b2:
            opr_name = "未割当"
            if case.operator:
                opr_name = case.operator.name if hasattr(case.operator, "name") else str(case.operator)
            st.info(f"👩‍💻 実務: **{opr_name}**")

        with b3:
            current_path = case.folder_path or ""
            input_key = f"header_folder_path_input_{case.case_id}"
            new_path = st.text_input(
                "📂 案件フォルダパス", 
                value=current_path, 
                label_visibility="collapsed", 
                placeholder="フォルダパス (\\\\server\\...)",
                key=input_key 
            )
            if new_path != current_path:
                update_case_folder_path(case.case_id, new_path)
                st.toast(f"フォルダパスを更新しました")
                time.sleep(0.5)
                st.rerun()

        with b4:
            c_open, c_search = st.columns([1, 1], gap="small")
            with c_open:
                # ★修正: ボタン名をユニークに変更 ("📂 開く" -> "📂 フォルダを開く")
                if st.button("📂 フォルダを開く", key=f"btn_open_{case.case_id}", use_container_width=True, help="Alt+O"):
                    if new_path:
                        if os.path.exists(new_path):
                            open_local_folder(new_path)
                        else:
                            st.error("フォルダが見つかりません")
                    else:
                        st.warning("パスが未設定です")
            with c_search:
                st.button(
                    "🔍 検索", 
                    key=f"btn_search_{case.case_id}", 
                    use_container_width=True, 
                    help="サーバーから案件番号でフォルダを検索します",
                    on_click=_search_folder_callback,
                    args=(case, input_key)
                )