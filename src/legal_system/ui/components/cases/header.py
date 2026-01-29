# 案件ヘッダー
# src/legal_system/ui/components/cases/header.py
import streamlit as st
from src.services.folder_service import find_case_folder, open_local_folder
from src.services.deceased_service import update_case_folder_path

def render_case_header(case):
    """
    案件のタイトル、Kintoneリンク、フォルダ操作を表示するヘッダー部分
    """
    if not case:
        return

    st.title(f"{case.case_number}: {case.client_name} 様")
    
    with st.container(border=True):
        st.caption("🚀 クイックアクセス")
        qc1, qc2 = st.columns([1, 2], gap="large")
        
        # 左: Kintoneボタン
        with qc1:
            if case.kintone_record_id:
                url = f"https://chester-tax.cybozu.com/k/242/show#record={case.kintone_record_id}"
                st.link_button("🔗 Kintoneで開く", url, type="primary", use_container_width=True)
            else:
                st.button("🔗 Kintone連携なし", disabled=True, use_container_width=True)
        
        # 右: フォルダパス & 自動検索機能
        with qc2:
            path_val = case.folder_path or ""
            c_p, c_act = st.columns([3, 2])
            new_path = c_p.text_input("フォルダパス", value=path_val, label_visibility="collapsed", placeholder="フォルダパス")
            
            c_open, c_search = c_act.columns(2)
            
            if c_open.button("📂 開く", use_container_width=True):
                if new_path:
                    open_local_folder(new_path)
                    if new_path != path_val: update_case_folder_path(case.case_id, new_path)
            
            if c_search.button("🔍 自動検索", use_container_width=True):
                q = case.case_number if case.case_number.startswith("G") else case.client_name.replace(" ", "")
                with st.spinner("検索中..."):
                    found = find_case_folder(q)
                    if found:
                        update_case_folder_path(case.case_id, found)
                        st.success("発見!")
                        time.sleep(0.5); st.rerun()
                    else:
                        st.warning("なし")
            
            if new_path != path_val: update_case_folder_path(case.case_id, new_path)