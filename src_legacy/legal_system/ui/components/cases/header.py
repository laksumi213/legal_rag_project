# src/legal_system/ui/components/cases/header.py

import logging
import os
import time

import streamlit as st
import streamlit.components.v1 as components
from legal_system.models.tables import Case

from services.deceased_service import update_case_folder_path
from services.folder_service import (
    find_all_case_folders,
    open_local_folder,
)

logger = logging.getLogger(__name__)


def _search_folder_callback(case_number: str, client_name: str, result_key: str):
    """
    検索ボタン押下時のコールバック。
    検索を実行し、結果（リスト）をSession Stateに格納する。
    """
    # 検索キーワード決定 (G番号優先)
    q = (
        case_number
        if case_number and case_number.startswith("G")
        else client_name.replace(" ", "")
    )
    st.session_state[result_key] = []  # 既存の結果をクリア

    try:
        logger.info(f"フォルダ検索実行: キーワード='{q}'")
        hits = find_all_case_folders(q)
        st.session_state[result_key] = hits

        if not hits:
            logger.warning(f"フォルダ検索: 該当なし。キーワード='{q}'")
            st.warning(f"'{q}' に一致するフォルダは見つかりませんでした。", icon="⚠️")
        elif len(hits) == 1:
            logger.info(f"フォルダ検索: 1件ヒット。パス='{hits[0]}'")
            st.toast("1件見つかりました", icon="✅")
        else:
            logger.info(f"フォルダ検索: {len(hits)}件ヒット。")
            st.toast(
                f"{len(hits)}件の候補が見つかりました。選択してください。", icon="📋"
            )

    except Exception as e:
        logger.error(f"フォルダ検索中にエラーが発生: {e}", exc_info=True)
        st.error(
            "フォルダ検索中に予期せぬエラーが発生しました。詳細はログを確認してください。"
        )
        st.session_state[result_key] = []


def render_case_header(case: Case):
    """
    案件詳細画面の共通ヘッダーを表示するコンポーネント
    """
    if not case:
        st.error("案件データが選択されていません")
        return

    # ---------------------------------------------------------
    # JavaScript: ショートカットキー制御 (Alt+K, Alt+O)
    # ---------------------------------------------------------
    js_shortcuts = """
    <script>
    (function() {
        function deepQuerySelectorAll(selector, root) {
            root = root || document;
            const results = [];
            try {
                const found = root.querySelectorAll(selector);
                found.forEach(el => results.push(el));
            } catch(e) {}
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
                if (node.shadowRoot) results.push(...deepQuerySelectorAll(selector, node.shadowRoot));
                if (node.tagName === 'IFRAME') {
                    try {
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) results.push(...deepQuerySelectorAll(selector, innerDoc));
                    } catch(e) {}
                }
            }
            return results;
        }

        function findElementByKeywords(keywords) {
            const selector = 'button, a, div[role="button"], [data-testid="stButton"] button, [data-testid="stLinkButton"] a';
            const candidates = deepQuerySelectorAll(selector, window.parent.document);
            for (let el of candidates) {
                const fullText = (el.innerText || "" + el.getAttribute("aria-label") || "" + el.getAttribute("title") || "").toLowerCase();
                if (keywords.some(kw => fullText.includes(kw.toLowerCase()))) return el;
            }
            return null;
        }

        const handleKeydown = function(e) {
            if (!e.altKey) return;
            if (e.code === 'KeyK') {
                const el = findElementByKeywords(["Kintoneで開く", "Kintone連携"]);
                if (el) { e.preventDefault(); el.click(); }
            }
            if (e.code === 'KeyO') {
                const el = findElementByKeywords(["📂 フォルダを開く", "フォルダを開く"]);
                if (el) { e.preventDefault(); el.click(); }
            }
        };

        const HANDLER_NAME = '_legalAppHeaderKeyHandler_v4';
        const doc = window.parent.document;
        if (window.parent[HANDLER_NAME]) doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
        window.parent[HANDLER_NAME] = handleKeydown;
        doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);
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
            case_num = case.case_number or "案件番号未定"
            client_name = case.client_name or "顧客名未設定"
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
                st.link_button(
                    "🚀 Kintoneで開く", url, type="primary", use_container_width=True
                )
            else:
                st.button("未連携", disabled=True, use_container_width=True)

        st.divider()

        b1, b2, b3, b4 = st.columns([1, 1, 3, 1.2], gap="small")
        with b1:
            mgr_name = case.manager.name if case.manager else "未割当"
            st.info(f"👮 担当: **{mgr_name}**")
        with b2:
            opr_name = case.operator.name if case.operator else "未割当"
            st.info(f"👩‍💻 実務: **{opr_name}**")

        # --- フォルダパス入力エリア ---
        with b3:
            current_path = case.folder_path or ""
            input_key = f"header_folder_path_input_{case.case_id}"
            result_key = f"search_res_{case.case_id}"  # 検索結果を格納するキー

            # --- 検索結果のハンドリング (単一ヒット時の自動反映) ---
            # st.text_inputの前にSession Stateを更新する必要がある
            if (
                result_key in st.session_state
                and len(st.session_state[result_key]) == 1
            ):
                found_path = st.session_state[result_key][0]
                # DBとUIのsession_stateを両方更新
                update_case_folder_path(case.case_id, found_path)
                st.session_state[input_key] = found_path
                del st.session_state[result_key]
                st.rerun()  # UI更新のため再実行

            # --- フォルダパス入力エリア ---
            current_path = case.folder_path or ""

            # Session State 初期化 (DB値優先)
            if input_key not in st.session_state:
                st.session_state[input_key] = current_path

            # 手入力欄 (value引数なし)
            new_path = st.text_input(
                "📂 案件フォルダパス",
                label_visibility="collapsed",
                placeholder="フォルダパス (\\\\server\\...)",
                key=input_key,
            )

            # 手入力更新の検知
            if (
                new_path != current_path
                and "search_candidates_key" not in st.session_state
            ):
                # 候補選択中でない場合のみ即時更新
                update_case_folder_path(case.case_id, new_path)
                st.toast("フォルダパスを更新しました")
                time.sleep(0.5)
                st.rerun()

        # --- 検索 & 開くボタン ---
        with b4:
            c_open, c_search = st.columns([1, 1], gap="small")

            with c_open:
                if st.button(
                    "📂 フォルダを開く",
                    key=f"btn_open_{case.case_id}",
                    use_container_width=True,
                    help="Alt+O",
                ):
                    path_to_open = st.session_state.get(input_key, current_path)
                    if path_to_open:
                        if os.path.exists(path_to_open):
                            open_local_folder(path_to_open)
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
                    args=(case.case_number, case.client_name, result_key),
                )

        # ---------------------------------------------------------
        # 検索結果のハンドリング (複数ヒット時の選択UI) - このブロックは単一ヒット処理の後に来る
        # ---------------------------------------------------------
        if result_key in st.session_state and len(st.session_state[result_key]) > 1:
            hits = st.session_state[result_key]

            st.info(
                f"💡 {len(hits)} 件のフォルダが見つかりました。正しいものを選択してください。"
            )

            # パスを短く表示するための加工（親フォルダ名 + フォルダ名）
            options_map = {}
            for h in hits:
                parts = h.split(os.sep)
                label = os.sep.join(parts[-2:]) if len(parts) > 1 else h
                options_map[label] = h

            selected_label = st.radio(
                "候補一覧", list(options_map.keys()), key="folder_candidate_radio"
            )

            c_confirm, c_cancel = st.columns([1, 4])
            if c_confirm.button("✅ 確定", key="btn_confirm_folder"):
                final_path = options_map[selected_label]
                update_case_folder_path(case.case_id, final_path)
                st.session_state[input_key] = final_path  # 選択後もUIを更新
                del st.session_state[result_key]
                st.success("パスを更新しました")
                time.sleep(0.5)
                st.rerun()

            if c_cancel.button("キャンセル", key="btn_cancel_folder"):
                del st.session_state[result_key]
                st.rerun()
