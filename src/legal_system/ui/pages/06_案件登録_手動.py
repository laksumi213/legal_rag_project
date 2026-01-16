# src/legal_system/ui/pages/06_案件登録_手動.py

import json
import os
import sys
import time
from datetime import datetime

import pandas as pd
import streamlit as st

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, User
from services.deceased_service import get_next_case_number_service
from services.kintone_sync_service import import_kintone_json


def main():
    st.set_page_config(page_title="新規案件 手動登録", page_icon="✍️", layout="wide")
    st.title("✍️ 新規案件 登録センター")

    db = DatabaseManager()
    session = db._get_session()

    # --- 1. Kintone取込エリア (デモの主役) ---
    st.markdown("### 📥 Kintoneデータ取込 (推奨)")
    st.info("Kintoneの「案件詳細画面」でブックマークレットを実行し、コピーされたJSONをここに貼り付けてください。")

    # レイアウト分割: 左(入力) / 右(結果プレビュー)
    col_json, col_preview = st.columns([1, 1], gap="medium")

    with col_json:
        with st.container(border=True):
            st.subheader("1. JSON貼り付け")
            json_text = st.text_area(
                "JSONデータ",
                height=250,
                placeholder='{"顧客コード": "Gxxxx", ...}',
                help="KintoneからコピーしたJSONをそのまま貼り付けてください"
            )

            if st.button("🚀 取り込んで登録・更新", type="primary", use_container_width=True):
                if not json_text.strip():
                    st.error("⚠️ データが空です")
                else:
                    try:
                        # 1. JSONパース
                        data = json.loads(json_text)

                        # 2. 取込実行
                        with st.spinner("データベースに登録中..."):
                            case_id = import_kintone_json(data)

                        if case_id > 0:
                            # 3. 成功フラグを立ててリロード
                            st.session_state["last_imported_case_id"] = case_id
                            st.session_state["import_success_msg"] = f"✅ 取込成功！ 案件ID: {case_id}"
                            st.rerun()
                        else:
                            st.error("❌ 取込に失敗しました。必須項目(顧客コード等)を確認してください。")

                    except json.JSONDecodeError:
                        st.error("❌ JSON形式として正しくありません。")
                    except Exception as e:
                        st.error(f"❌ システムエラー: {e}")

    # --- 結果プレビュー表示 (右カラム) ---
    with col_preview:
        # セッションにIDがあれば表示する
        if "last_imported_case_id" in st.session_state:
            cid = st.session_state["last_imported_case_id"]
            
            # 成功メッセージがあれば表示して消す（1回だけ表示）
            if "import_success_msg" in st.session_state:
                st.toast(st.session_state["import_success_msg"], icon="🎉")
                st.success(st.session_state["import_success_msg"])
                del st.session_state["import_success_msg"]

            # DBから再取得して表示
            case = session.query(Case).get(cid)
            if case:
                with st.container(border=True):
                    st.subheader(f"🎉 登録完了: {case.client_name} 様")
                    
                    # 基本情報
                    st.markdown(f"**案件番号:** `{case.case_number}`")
                    
                    if case.deceased_ref:
                        d_name = f"{case.deceased_ref.name_last} {case.deceased_ref.name_first}"
                        st.markdown(f"**被相続人:** {d_name}")
                    
                    st.divider()

                    # 家族構成（相続人）テーブル
                    st.markdown("###### 📋 登録された関係者リスト")
                    
                    if case.deceased_ref and case.deceased_ref.heirs:
                        heirs_data = []
                        for h in case.deceased_ref.heirs:
                            heirs_data.append({
                                "氏名": f"{h.name_last} {h.name_first}",
                                "続柄": h.relationship_type,
                                "契約者": "〇" if h.is_contracting_party else "-"
                            })
                        
                        df = pd.DataFrame(heirs_data)
                        st.dataframe(
                            df, 
                            use_container_width=True, 
                            hide_index=True,
                            column_config={
                                "氏名": st.column_config.TextColumn("氏名", width="medium"),
                                "続柄": st.column_config.TextColumn("続柄", width="small"),
                                "契約者": st.column_config.TextColumn("契約者", width="small")
                            }
                        )
                    else:
                        st.warning("⚠️ 相続人データが登録されていません")
            else:
                st.error("⚠️ 登録されたはずのデータが見つかりません。")
        else:
            # 待機中の表示
            with st.container(border=True):
                st.info("👈 左側にJSONを貼り付けて登録すると、ここに結果が表示されます。")
                st.caption("デモ用: 準備されたJSONを貼り付けてボタンを押してください。")

    st.divider()

    # --- 2. 手動入力フォーム (バックアップ用) ---
    with st.expander("手動でゼロから入力する場合"):
        users = session.query(User).all()
        user_options = {"未定": None}
        for u in users:
            user_options[u.name] = u.id

        c1, c2, c3 = st.columns(3)
        default_case_num = get_next_case_number_service()
        case_num = c1.text_input("案件番号 (仮4桁 or G番号)", value=default_case_num)
        
        # ユーザー選択（KeyError対策）
        mgr_idx = 0
        opr_idx = 0
        
        manager_name = c2.selectbox("担当者1 (進捗)", list(user_options.keys()), index=mgr_idx)
        operator_name = c3.selectbox("担当者2 (実務)", list(user_options.keys()), index=opr_idx)

        col_name1, col_name2 = st.columns(2)
        name_last = col_name1.text_input("氏名 (姓)")
        name_first = col_name2.text_input("氏名 (名)")

        # (中略: 手動登録のロジックは必要に応じて維持)
        if st.button("手動登録を実行"):
            st.warning("JSON取込を推奨します。手動登録ロジックはデモ範囲外です。")

    session.close()

if __name__ == "__main__":
    main()