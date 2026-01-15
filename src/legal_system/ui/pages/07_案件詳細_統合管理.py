# src/legal_system/ui/pages/07_案件詳細_統合管理.py

import json
import os
import sys
import time
from datetime import datetime

import streamlit as st

# ==========================================
# 1. パス解決 & インポート
# ==========================================
# pages -> ui -> legal_system -> src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir, User, FinancialAsset, Address

# サービス層からのインポート
from services.folder_service import open_local_folder, find_case_folder
from services.deceased_service import (
    update_case_number, 
    delete_case_and_all_related_data,
    update_case_folder_path,
    update_case_assignment,
    
    # CRUD用関数
    update_deceased,
    add_heir,
    update_heir,
    delete_heir,
    get_address_info,
    get_contact_info
)
from services.kintone_sync_service import get_kintone_data_as_dict, import_kintone_json

# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(page_title="案件詳細・管理", page_icon="🗂️", layout="wide")

def main():
    db = DatabaseManager()
    session = db._get_session()

    # --- サイドバー: 案件選択 ---
    st.sidebar.title("🗂️ 案件切替")
    
    cases = session.query(Case).order_by(Case.created_at.desc()).all()
    if not cases:
        st.warning("案件が登録されていません。")
        session.close()
        return

    case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
    
    if "selected_case_id" not in st.session_state:
        st.session_state["selected_case_id"] = list(case_options.values())[0]

    current_ids = list(case_options.values())
    try:
        if st.session_state["selected_case_id"] not in current_ids:
             st.session_state["selected_case_id"] = current_ids[0]
        current_index = current_ids.index(st.session_state["selected_case_id"])
    except ValueError:
        current_index = 0

    selected_label = st.sidebar.selectbox(
        "対象案件を選択", 
        list(case_options.keys()), 
        index=current_index
    )
    
    case_id = case_options[selected_label]
    st.session_state["selected_case_id"] = case_id
    current_case = session.query(Case).filter_by(case_id=case_id).first()

    st.sidebar.divider()
    menu = st.sidebar.radio(
        "メニュー",
        ["🏠 案件概要・基本情報", "🏦 銀行口座 登録", "📈 証券・その他資産", "🏘️ 不動産 登録", "✅ タスク管理"],
    )

    if not current_case:
        st.error("案件データの取得に失敗しました。")
        session.close()
        return

    st.title(f"{current_case.case_number}: {current_case.client_name} 様")

    # ==========================================
    # A. 案件概要・基本情報
    # ==========================================
    if menu == "🏠 案件概要・基本情報":
        st.subheader("基本情報・操作")
        
        # --- 1. 担当者情報の編集 ---
        with st.container(border=True):
            st.markdown("##### 👥 担当者情報")
            users = session.query(User).all()
            user_map = {u.name: u.id for u in users}
            user_map["未定"] = None
            
            curr_mgr_name = next((u.name for u in users if u.id == current_case.manager_id), "未定")
            curr_opr_name = next((u.name for u in users if u.id == current_case.operator_id), "未定")
            
            col_mgr, col_opr, col_upd = st.columns([2, 2, 1])
            new_mgr = col_mgr.selectbox("担当者1 (進捗)", list(user_map.keys()), index=list(user_map.keys()).index(curr_mgr_name))
            new_opr = col_opr.selectbox("担当者2 (実務)", list(user_map.keys()), index=list(user_map.keys()).index(curr_opr_name))
            
            col_upd.write("")
            col_upd.write("") 
            if col_upd.button("担当更新", use_container_width=True):
                mgr_id = user_map[new_mgr]
                opr_id = user_map[new_opr]
                if update_case_assignment(case_id, mgr_id, opr_id):
                    st.toast("担当者情報を更新しました", icon="✅")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("更新に失敗しました")

        st.divider()

        # --- 1.5 紹介・SOL連携情報の編集 ---
        with st.expander("🤝 紹介・SOL連携情報 (日興証券など)"):
            with st.form("edit_sol_info"):
                c_sol1, c_sol2 = st.columns(2)
                new_sol_no = c_sol1.text_input("SOL案件番号", value=current_case.sol_case_number or "")
                
                curr_intro = current_case.introduction_date
                curr_cons = current_case.consent_date
                
                new_intro = c_sol2.date_input("紹介日", value=curr_intro if curr_intro else None)
                new_cons = c_sol1.date_input("同意書日付", value=curr_cons if curr_cons else None)
                
                c_br, c_rep = st.columns(2)
                new_branch = c_br.text_input("紹介元支店", value=current_case.referral_sec_branch_name or "")
                new_rep = c_rep.text_input("紹介元担当者", value=current_case.referral_sec_rep_name or "")
                
                if st.form_submit_button("連携情報を更新"):
                    current_case.sol_case_number = new_sol_no
                    current_case.introduction_date = new_intro
                    current_case.consent_date = new_cons
                    current_case.referral_sec_branch_name = new_branch
                    current_case.referral_sec_rep_name = new_rep
                    session.commit()
                    st.toast("更新しました", icon="✅")
                    time.sleep(0.5); st.rerun()

        st.divider()

        # --- 2. Kintone連携 & 削除 & 取込 ---
        col_kintone, col_delete = st.columns([1, 1])
        
        with col_kintone:
            st.info("📋 **Kintone連携**")
            
            # コピーボタン
            if st.button("Kintone用データをコピー", icon="📋", use_container_width=True):
                kintone_data = get_kintone_data_as_dict(case_id)
                if kintone_data:
                    json_str = json.dumps(kintone_data, ensure_ascii=False)
                    try:
                        import pyperclip
                        pyperclip.copy(json_str)
                        st.toast("クリップボードにコピーしました！", icon="✅")
                        st.success("Kintoneの編集画面でブックマークレットを実行してください。")
                    except ImportError:
                        st.error("❌ `pyperclip` がインストールされていません。")
                        st.code(json_str, language="json")
                    except Exception as e:
                        st.error(f"コピー失敗: {e}")
                        st.code(json_str, language="json")
                else:
                    st.error("データの取得に失敗しました。")

            # 取込機能 (Expander)
            with st.expander("📥 Kintoneデータを取り込んで上書きする"):
                st.warning("注意: 入力したJSONの内容で、この案件の「顧客情報」「被相続人情報」「担当者」などを上書きします。")
                json_input = st.text_area("JSONデータ貼り付け", height=100)
                if st.button("上書き実行", type="primary"):
                    if not json_input.strip():
                        st.error("データがありません")
                    else:
                        try:
                            data = json.loads(json_input)
                            res = import_kintone_json(data, target_case_id=case_id)
                            if res > 0:
                                st.success("更新しました！")
                                time.sleep(1); st.rerun()
                            else:
                                st.error("更新失敗")
                        except Exception as e:
                            st.error(f"エラー: {e}")

        with col_delete:
            st.error("🗑️ **案件削除**")
            with st.expander("削除メニューを開く"):
                st.warning("案件と関連データを**完全に削除**します。元に戻せません。")
                confirm_del = st.checkbox("上記を理解して削除します", key="del_confirm")
                
                if st.button("実行: 案件を削除する", type="primary", disabled=not confirm_del):
                    if delete_case_and_all_related_data(current_case.case_number):
                        st.toast("削除しました", icon="🗑️")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("削除に失敗しました。")

        st.divider()

        # --- 3. フォルダパス操作 ---
        st.warning("📂 **案件フォルダ設定**")
        current_path = current_case.folder_path or ""
        col_path_in, col_path_btn = st.columns([3, 1])
        
        new_path = col_path_in.text_input("フォルダパス", value=current_path, placeholder=r"\\192.168.11.20\...")
        if new_path != current_path:
            if update_case_folder_path(case_id, new_path):
                st.toast("フォルダパスを更新しました", icon="💾")
                time.sleep(0.5); st.rerun()

        with col_path_btn:
            if st.button("📂 フォルダを開く", use_container_width=True):
                if open_local_folder(new_path):
                    st.toast("サーバー側でフォルダを開きました", icon="🖥️")
                else:
                    st.error("フォルダを開けませんでした。パスを確認してください。")
            
            # ★修正: G番号優先の自動検索
            if st.button("🔍 フォルダ自動検索", use_container_width=True):
                search_query = ""
                # G番号があればそれを優先
                if current_case.case_number and current_case.case_number.startswith("G"):
                    search_query = current_case.case_number
                else:
                    # なければ氏名 (スペース除去)
                    search_query = current_case.client_name.replace(" ", "").replace("　", "")
                
                with st.spinner(f"「{search_query}」で検索中..."):
                    found = find_case_folder(search_query)
                    if found:
                        update_case_folder_path(case_id, found)
                        st.success(f"見つかりました: {found}")
                        time.sleep(1); st.rerun()
                    else:
                        st.warning(f"「{search_query}」で見つかりませんでした。")

        st.divider()

        # --- 4. 案件番号修正 ---
        with st.expander("✏️ 案件番号の修正 (G番号付与など)"):
            c_n1, c_n2 = st.columns([3, 1])
            new_num = c_n1.text_input("新しい案件番号", value=current_case.case_number)
            if c_n2.button("番号更新") and new_num != current_case.case_number:
                if update_case_number(case_id, new_num):
                    st.success("更新しました！")
                    time.sleep(1); st.rerun()
                else:
                    st.error("重複しています")

        st.divider()

        # ==========================================
        # 5. 被相続人・相続人 (CRUD)
        # ==========================================
        st.subheader("👤 家族・関係者情報")
        d = current_case.deceased_ref
        
        with st.container(border=True):
            c_d_title, c_d_edit = st.columns([4, 1])
            if d:
                c_d_title.markdown(f"#### 被相続人: {d.name_last} {d.name_first}")
            else:
                c_d_title.markdown("#### 被相続人: (未登録)")
            
            is_edit_deceased = c_d_edit.toggle("編集", key="toggle_dec_edit")
            
            if is_edit_deceased and d:
                with st.form("edit_deceased_form"):
                    # (フォーム内容は既存と同様なので省略せず記述)
                    cd1, cd2 = st.columns(2)
                    d_lname = cd1.text_input("氏 (姓)", value=d.name_last)
                    d_fname = cd2.text_input("名", value=d.name_first)
                    cd3, cd4 = st.columns(2)
                    d_klname = cd3.text_input("フリガナ (姓)", value=d.name_last_kana or "")
                    d_kfname = cd4.text_input("フリガナ (名)", value=d.name_first_kana or "")
                    cd5, cd6 = st.columns(2)
                    d_dod = cd5.date_input("死亡日", value=d.date_of_death if d.date_of_death else None)
                    d_dob = cd6.date_input("生年月日", value=d.date_of_birth if d.date_of_birth else None)
                    
                    d_addr_obj = session.query(Address).get(d.last_address_id) if d.last_address_id else None
                    st.markdown("---"); st.caption("最後の住所")
                    ca1, ca2 = st.columns(2)
                    d_zip = ca1.text_input("郵便番号", value=d_addr_obj.zip_code if d_addr_obj else "")
                    d_pref = ca2.text_input("都道府県", value=d_addr_obj.prefecture if d_addr_obj else "")
                    d_city = st.text_input("市区町村・番地", value=f"{d_addr_obj.city_ward_town or ''}{d_addr_obj.street_address or ''}" if d_addr_obj else "")
                    d_bldg = st.text_input("建物名", value=d_addr_obj.building_name if d_addr_obj else "")

                    if st.form_submit_button("保存する"):
                        update_deceased(
                            d.id,
                            name_last=d_lname, name_first=d_fname,
                            kana_last=d_klname, kana_first=d_kfname,
                            dod=str(d_dod) if d_dod else None, dob=str(d_dob) if d_dob else None,
                            last_zip_code=d_zip, last_pref=d_pref, last_city=d_city, last_street="", last_building=d_bldg
                        )
                        st.toast("更新しました", icon="💾"); time.sleep(1); st.rerun()
            else:
                if d:
                    st.write(f"**死亡日:** {d.date_of_death}　**生年月日:** {d.date_of_birth}")
                    if d.last_address_id:
                        addr = session.query(Address).get(d.last_address_id)
                        st.write(f"**住所:** 〒{addr.zip_code} {addr.prefecture} {addr.city_ward_town} {addr.street_address} {addr.building_name or ''}")
                else:
                    st.info("被相続人データが作成されていません。")

        st.markdown("#### 相続人・関係者リスト")
        if d and d.heirs:
            for h in d.heirs:
                with st.expander(f"{h.name_last} {h.name_first} ({h.relationship_type}) {'[契約者]' if h.is_contracting_party else ''}"):
                    with st.form(f"form_heir_{h.id}"):
                        c1, c2 = st.columns(2)
                        h_lname = c1.text_input("姓", value=h.name_last)
                        h_fname = c2.text_input("名", value=h.name_first)
                        c3, c4 = st.columns(2)
                        h_klname = c3.text_input("フリガナ(姓)", value=h.name_last_kana or "")
                        h_kfname = c4.text_input("フリガナ(名)", value=h.name_first_kana or "")
                        c5, c6 = st.columns(2)
                        h_rel = c5.text_input("続柄", value=h.relationship_type)
                        h_contract = c6.checkbox("契約者 (依頼主)", value=h.is_contracting_party)
                        
                        h_dob = st.date_input("生年月日", value=h.date_of_birth if h.date_of_birth else None, key=f"dob_{h.id}")
                        h_addr = get_address_info("heir", h.id)
                        h_contacts = get_contact_info("heir", h.id)
                        h_phone = next((c["value"] for c in h_contacts if c["type"]=="PHONE"), "")
                        
                        st.markdown("---")
                        az, ap = st.columns(2)
                        h_zip = az.text_input("郵便番号", value=h_addr.get("zip_code",""))
                        h_pref = ap.text_input("都道府県", value=h_addr.get("prefecture",""))
                        h_city = st.text_input("市区町村・番地", value=f"{h_addr.get('city_ward_town','')}{h_addr.get('street_address','')}")
                        h_bldg = st.text_input("建物名", value=h_addr.get("building_name",""))
                        h_tel = st.text_input("電話番号", value=h_phone)

                        c_upd, c_del = st.columns([4, 1])
                        if c_upd.form_submit_button("更新保存", type="primary"):
                            update_heir(
                                h.id,
                                name=f"{h_lname} {h_fname}",
                                rel=h_rel,
                                kana_last=h_klname, kana_first=h_kfname,
                                dob=str(h_dob) if h_dob else None,
                                zip_code=h_zip, pref=h_pref, city=h_city, street="", building=h_bldg,
                                phone_contacts=[{"value": h_tel}] if h_tel else []
                            )
                            h.is_contracting_party = h_contract
                            session.commit()
                            st.toast("更新しました", icon="✅"); time.sleep(1); st.rerun()

                    if st.button("この相続人を削除", key=f"del_heir_btn_{h.id}"):
                        delete_heir(h.id)
                        st.toast("削除しました", icon="🗑️"); time.sleep(1); st.rerun()
        else:
            st.info("登録されている相続人はおられません。")

        if d:
            with st.expander("➕ 相続人を新規追加する"):
                with st.form("add_heir_form"):
                    st.write("新規登録")
                    na1, na2 = st.columns(2)
                    new_lname = na1.text_input("姓")
                    new_fname = na2.text_input("名")
                    new_rel = st.text_input("続柄 (例: 長男)")
                    if st.form_submit_button("追加"):
                        if new_lname and new_rel:
                            add_heir(d.id, f"{new_lname} {new_fname}", new_rel)
                            st.toast("追加しました", icon="✅"); time.sleep(1); st.rerun()
                        else:
                            st.error("姓と続柄は必須です")
        else:
            st.warning("被相続人が登録されていないため、相続人を追加できません。")

    # ==========================================
    # B. 銀行口座登録
    # ==========================================
    elif menu == "🏦 銀行口座 登録":
        st.subheader("🏦 銀行・金融資産管理")
        assets = session.query(FinancialAsset).filter_by(case_id=case_id).all()
        if assets:
            st.write(f"登録済み: {len(assets)} 件")
            for a in assets:
                bank = a.bank_ref.bank_name if a.bank_ref else "不明"
                branch = a.branch_ref.branch_name if a.branch_ref else "-"
                with st.expander(f"{bank} {branch} : {a.account_number}"):
                    new_bal = st.number_input("残高", value=int(a.balance), key=f"bal_{a.id}")
                    new_stat = st.text_input("状況", value=a.status, key=f"stat_{a.id}")
                    if st.button("更新", key=f"upd_asset_{a.id}"):
                        a.balance = new_bal
                        a.status = new_stat
                        session.commit()
                        st.toast("更新しました")
        else:
            st.info("登録なし")
        st.info("※ 新規登録はサイドバーの「02_預貯金口座入力フォーム」をご利用ください")

    # ==========================================
    # C. その他
    # ==========================================
    else:
        st.subheader(menu)
        st.info("この機能は現在開発中です。")

    session.close()

if __name__ == "__main__":
    main()