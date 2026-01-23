# src/legal_system/ui/pages/01_案件登録_手動.py

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
from legal_system.models.tables import Case, User, Deceased, Heir
from services.deceased_service import (
    get_next_case_number_service, 
    add_new_case_for_client_registration,
    is_case_number_duplicate,
    get_case_id_by_deceased_id
)
from services.kintone_sync_service import import_kintone_json


def main():
    st.set_page_config(page_title="新規案件 手動登録", page_icon="✍️", layout="wide")
    st.title("✍️ 新規案件 登録センター")

    db = DatabaseManager()
    session = db._get_session()

    # --- 1. Kintoneデータ取込エリア (JSON) ---
    st.markdown("### 📥 Kintoneデータ取込 (推奨)")
    st.info("Kintoneの「案件詳細画面」でブックマークレットを実行し、コピーされたJSONを貼り付けてください。")

    col_json, col_preview = st.columns([1, 1], gap="medium")

    with col_json:
        with st.container(border=True):
            st.subheader("1. JSON貼り付け")
            json_text = st.text_area(
                "JSONデータ",
                height=150,
                placeholder='{"顧客コード": "Gxxxx", ...}',
                help="KintoneからコピーしたJSONをそのまま貼り付けてください"
            )

            if st.button("🚀 取り込んで登録・更新", type="primary", use_container_width=True):
                if not json_text.strip():
                    st.error("⚠️ データが空です")
                else:
                    try:
                        data = json.loads(json_text)
                        
                        # ==========================================
                        # ★修正: 電話番号・メールアドレスの除外処理
                        # ==========================================
                        # Kintone上のデータが担当者や紹介元のものである場合があるため、
                        # 意図しない混入を防ぐためにここでは取り込み対象外とします。
                        data.pop("TEL", None)
                        data.pop("メールアドレス", None)

                        # ==========================================
                        # ★修正: 顧客コードが空の場合の自動採番ロジック
                        # ==========================================
                        # JSON内のコードを確認
                        raw_code = data.get("顧客コード", "") or data.get("顧客コード_2", "")
                        
                        if not raw_code:
                            # コードが空なら、自動で仮番号(1001...)を取得して埋め込む
                            temp_num = get_next_case_number_service()
                            data["顧客コード_2"] = temp_num # import_kintone_json はこれを見る
                            
                            # ユーザーへのフィードバック
                            st.toast(f"ℹ️ 顧客コードが空のため、仮番号「{temp_num}」を発行して登録します。", icon="🔢")
                            time.sleep(0.5)

                        # JSON取込実行
                        with st.spinner("データベースに登録中..."):
                            # target_case_id=None (新規判定) で実行
                            case_id = import_kintone_json(data)

                        if case_id > 0:
                            st.session_state["last_imported_case_id"] = case_id
                            st.session_state["import_success_msg"] = f"✅ 取込成功！ 案件ID: {case_id}"
                            st.rerun()
                        else:
                            st.error("❌ 取込に失敗しました。データ形式を確認してください。")

                    except json.JSONDecodeError:
                        st.error("❌ JSON形式として正しくありません。")
                    except Exception as e:
                        st.error(f"❌ システムエラー: {e}")

    # --- 結果プレビュー表示 (右カラム) ---
    with col_preview:
        if "last_imported_case_id" in st.session_state:
            cid = st.session_state["last_imported_case_id"]
            
            if "import_success_msg" in st.session_state:
                st.toast(st.session_state["import_success_msg"], icon="🎉")
                st.success(st.session_state["import_success_msg"])
                del st.session_state["import_success_msg"]

            case = session.query(Case).get(cid)
            if case:
                with st.container(border=True):
                    st.subheader(f"🎉 登録完了: {case.client_name} 様")
                    st.markdown(f"**案件番号:** `{case.case_number}`")
                    
                    if case.deceased_ref:
                        d_name = f"{case.deceased_ref.name_last} {case.deceased_ref.name_first}"
                        st.markdown(f"**被相続人:** {d_name}")
                    
                    st.divider()
                    st.markdown("###### 📋 登録された関係者リスト")
                    if case.deceased_ref and case.deceased_ref.heirs:
                        heirs_data = []
                        for h in case.deceased_ref.heirs:
                            heirs_data.append({
                                "氏名": f"{h.name_last} {h.name_first}",
                                "続柄": h.relationship_type,
                                "契約者": "〇" if h.is_contracting_party else "-"
                            })
                        st.dataframe(pd.DataFrame(heirs_data), use_container_width=True, hide_index=True)
            else:
                st.error("⚠️ データが見つかりません。")
        else:
            with st.container(border=True):
                st.info("👈 左側にJSONを貼り付けるか、下のフォームから手動登録してください。")

    st.divider()

    # --- 2. 手動入力フォーム (受任前・仮登録用) ---
    st.markdown("### ✍️ 手動入力 (受任前・Kintone未登録)")
    st.caption("まだ顧客コード(G番号)がない場合、ここで仮番号を発行して登録できます。")

    with st.expander("手動登録フォームを開く", expanded=True):
        with st.form("manual_reg_form"):
            # ユーザー選択肢
            users = session.query(User).all()
            user_options = {"未定": None}
            for u in users:
                user_options[u.name] = u.id

            # 自動採番 (1000番台~)
            default_case_num = get_next_case_number_service()
            
            c_num, c_mgr, c_opr = st.columns(3)
            # 番号は編集可能にするが、重複チェックは後で行う
            input_case_num = c_num.text_input(
                "案件番号 (自動採番)", 
                value=default_case_num, 
                help="G番号が決まっていない場合はこのまま登録してください"
            )
            
            manager_name = c_mgr.selectbox("担当者1 (進捗)", list(user_options.keys()))
            operator_name = c_opr.selectbox("担当者2 (実務)", list(user_options.keys()))

            st.markdown("#### 依頼者 (相談者) 情報")
            col_name1, col_name2 = st.columns(2)
            c_lname = col_name1.text_input("氏名 (姓) ※必須")
            c_fname = col_name2.text_input("氏名 (名)")
            
            col_kana1, col_kana2 = st.columns(2)
            c_klname = col_kana1.text_input("フリガナ (姓)")
            c_kfname = col_kana2.text_input("フリガナ (名)")

            st.markdown("#### 住所・連絡先")
            az, ap = st.columns([1, 2])
            zip_val = az.text_input("郵便番号")
            pref_val = ap.text_input("都道府県")
            
            ac, as_ = st.columns(2)
            city_val = ac.text_input("市区町村")
            street_val = as_.text_input("番地")
            bldg_val = st.text_input("建物名")

            st.markdown("---")
            
            if st.form_submit_button("✅ 仮登録を実行", type="primary", use_container_width=True):
                # バリデーション
                if not input_case_num:
                    st.error("案件番号は必須です。")
                elif not c_lname:
                    st.error("依頼者の「姓」は必須です。")
                else:
                    # 重複チェック
                    if is_case_number_duplicate(input_case_num):
                        st.error(f"案件番号「{input_case_num}」は既に使用されています。別の番号を入力してください。")
                    else:
                        # 登録処理
                        full_name = f"{c_lname}　{c_fname}".strip()
                        
                        try:
                            # サービス層の関数を呼び出し
                            new_deceased_id = add_new_case_for_client_registration(
                                case_number=input_case_num,
                                name=full_name,
                                kana_last=c_klname,
                                kana_first=c_kfname,
                                manager_id=user_options[manager_name],
                                operator_id=user_options[operator_name],
                                folder_path="", # 仮登録時は空
                                zip_code=zip_val,
                                pref=pref_val,
                                city=city_val,
                                street=street_val,
                                building=bldg_val,
                                rel="本人",     # 仮: 本人として登録
                                hometown=""
                            )
                            
                            if new_deceased_id > 0:
                                # 成功したらセッションにIDを入れてリロード（プレビュー表示のため）
                                new_case_id = get_case_id_by_deceased_id(new_deceased_id)
                                
                                st.session_state["last_imported_case_id"] = new_case_id
                                st.session_state["import_success_msg"] = f"✅ 仮登録完了！ 案件番号: {input_case_num}"
                                st.rerun()
                            else:
                                st.error("登録処理に失敗しました。")
                                
                        except Exception as e:
                            st.error(f"システムエラー: {e}")

    session.close()

if __name__ == "__main__":
    main()