# src/legal_system/ui/pages/06_案件登録_手動.py

import os
import sys
import time
from datetime import datetime
import json

import streamlit as st

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, User
from services.folder_service import find_case_folder
from services.deceased_service import get_next_case_number_service
from services.kintone_sync_service import import_kintone_json

st.set_page_config(page_title="新規案件 手動登録", page_icon="✍️", layout="wide")

def main():
    st.title("✍️ 新規案件 手動登録")
    
    # Kintone取込エリア
    with st.expander("📂 Kintone JSONデータから取り込む (任意)", expanded=False):
        st.caption("KintoneからコピーしたJSONデータを貼り付けると、自動で登録・入力補助を行います。")
        json_text = st.text_area("JSONデータ", height=150)
        if st.button("JSONを取り込んで登録"):
            if not json_text.strip():
                st.error("データが空です")
            else:
                try:
                    data = json.loads(json_text)
                    case_id = import_kintone_json(data)
                    if case_id > 0:
                        st.success(f"取込成功！ 案件ID: {case_id}")
                        time.sleep(1)
                    else:
                        st.error("取込に失敗しました。")
                except json.JSONDecodeError:
                    st.error("JSON形式として正しくありません。")
                except Exception as e:
                    st.error(f"エラー: {e}")

    st.caption("紹介連絡票を使わず、手動で案件を作成します。")
    db = DatabaseManager()
    session = db._get_session()

    users = session.query(User).all()
    user_options = {"未定": None}
    for u in users:
        user_options[u.name] = u.id

    st.subheader("1. 案件基本情報")
    c1, c2, c3 = st.columns(3)
    default_case_num = get_next_case_number_service()
    case_num = c1.text_input("案件番号 (仮4桁 or G番号)", value=default_case_num)
    manager_name = c2.selectbox("担当者1 (進捗)", list(user_options.keys()), index=0)
    operator_name = c3.selectbox("担当者2 (実務)", list(user_options.keys()), index=0)

    st.subheader("2. 契約者（顧客）情報")
    col_name1, col_name2 = st.columns(2)
    name_last = col_name1.text_input("氏名 (姓)")
    name_first = col_name2.text_input("氏名 (名)")
    col_kana1, col_kana2 = st.columns(2)
    kana_last = col_kana1.text_input("フリガナ (姓)")
    kana_first = col_kana2.text_input("フリガナ (名)")

    # フォルダ検索
    st.subheader("3. サーバーフォルダ")
    if "auto_found_path" not in st.session_state:
        st.session_state["auto_found_path"] = ""

    col_path, col_btn = st.columns([3, 1])
    
    def on_search_click():
        # ★修正: G番号優先ロジック
        search_query = ""
        if case_num and case_num.startswith("G"):
            search_query = case_num
        else:
            search_query = f"{name_last}{name_first}".replace(" ", "").replace("　", "")
        
        if not search_query:
            st.toast("⚠️ 検索するキーワード（G番号または氏名）がありません", icon="⚠️")
            return
        
        with st.spinner(f"サーバー内を「{search_query}」で検索中..."):
            found = find_case_folder(search_query)
            if found:
                st.session_state["auto_found_path"] = found
                st.toast("✅ フォルダが見つかりました", icon="📂")
            else:
                st.toast("❌ フォルダが見つかりませんでした", icon="🤷‍♂️")

    col_btn.write(""); col_btn.write("") 
    if col_btn.button("🔍 自動検索", use_container_width=True):
        on_search_click()

    folder_path_input = col_path.text_input(
        "フォルダパス", 
        value=st.session_state["auto_found_path"],
        placeholder="\\192.168.11.20\..."
    )

    st.markdown("---")
    _, col_submit = st.columns([3, 1])
    
    if col_submit.button("💾 案件を登録する", type="primary", use_container_width=True):
        if not case_num or not name_last:
            st.error("「案件番号」と「氏名(姓)」は必須です。")
        else:
            try:
                existing = session.query(Case).filter_by(case_number=case_num).first()
                if existing:
                    st.error(f"案件番号 {case_num} は既に登録されています。")
                else:
                    client_name = f"{name_last} {name_first}".strip()
                    client_kana = f"{kana_last} {kana_first}".strip()
                    
                    new_case = Case(
                        case_number=case_num,
                        client_name=client_name,
                        client_name_kana=client_kana,
                        folder_path=folder_path_input,
                        manager_id=user_options[manager_name],
                        operator_id=user_options[operator_name],
                        created_at=datetime.now()
                    )
                    session.add(new_case)
                    session.commit()
                    
                    st.success(f"案件 {case_num} ({client_name}様) を登録しました！")
                    time.sleep(1.5)
                    st.session_state["auto_found_path"] = ""
                    st.rerun()
                    
            except Exception as e:
                session.rollback()
                st.error(f"登録エラー: {e}")
            finally:
                session.close()

if __name__ == "__main__":
    main()