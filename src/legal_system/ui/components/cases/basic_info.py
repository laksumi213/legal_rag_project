# src/legal_system/ui/components/cases/basic_info.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import joinedload
from datetime import date

from legal_system.models.tables import Case, Deceased, Heir, Address, H_AddressHistory, H_ContactLink, Contact
from src.services.deceased_service import (
    update_heir, update_deceased, add_heir, delete_heir, 
    get_address_info, get_contact_info, delete_case_and_all_related_data,
    sync_heir_list
)
from src.utils.date_utils import convert_seireki_to_wareki

def _get_date_input(label, current_value, key=None):
    """
    日付入力ヘルパー（Noneハンドリング & key対応）
    DuplicateElementIdエラーを防ぐため、呼び出し元でkeyを指定可能に変更
    """
    return st.date_input(label, value=current_value if current_value else None, format="YYYY/MM/DD", key=key)

def render_basic_info(session, case_id: int):
    """
    基本情報（依頼者・被相続人・相続人）の編集画面を描画する
    """
    # データをリロード（最新状態を取得）
    case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.deceased_ref).joinedload(Deceased.last_address)
    ).get(case_id)

    if not case:
        st.error("案件データが見つかりません。")
        return

    deceased = case.deceased_ref
    
    # ---------------------------------------------------------
    # 1. 依頼者（契約者）情報
    # ---------------------------------------------------------
    st.subheader("👤 依頼者（契約者）情報")
    
    # 契約者を特定（いなければ先頭の相続人）
    contractor = None
    if deceased and deceased.heirs:
        contractor = next((h for h in deceased.heirs if h.is_contracting_party), None)
        if not contractor:
            contractor = deceased.heirs[0]

    with st.container(border=True):
        if contractor:
            # 連絡先・住所の取得
            c_addr = get_address_info("heir", contractor.id)
            c_conts = get_contact_info("heir", contractor.id)
            c_phone = next((c["value"] for c in c_conts if c["type"]=="PHONE"), "")
            c_email = next((c["value"] for c in c_conts if c["type"]=="EMAIL"), "")

            col1, col2 = st.columns(2)
            with col1:
                new_c_name = st.text_input("氏名", value=f"{contractor.name_last}　{contractor.name_first}")
                new_c_kana = st.text_input("フリガナ", value=f"{contractor.name_last_kana or ''}　{contractor.name_first_kana or ''}")
                new_c_rel = st.text_input("続柄", value=contractor.relationship_type)
                # ★修正: keyを追加
                new_c_dob = _get_date_input("生年月日", contractor.date_of_birth, key="contractor_dob")

            with col2:
                new_c_phone = st.text_input("電話番号", value=c_phone)
                new_c_email = st.text_input("メールアドレス", value=c_email)
                
                # 住所入力
                c1, c2_ = st.columns([1, 2])
                new_c_zip = c1.text_input("郵便番号", value=c_addr.get("zip_code", ""))
                new_c_pref = c2_.text_input("都道府県", value=c_addr.get("prefecture", ""))
                new_c_city = st.text_input("市区町村", value=c_addr.get("city_ward_town", ""))
                new_c_street = st.text_input("番地", value=c_addr.get("street_address", ""))
                new_c_bldg = st.text_input("建物名", value=c_addr.get("building_name", ""))

            if st.button("💾 依頼者情報を更新", key="save_contractor", type="primary"):
                # 氏名分割
                parts = new_c_name.replace("　", " ").split(" ", 1)
                k_parts = new_c_kana.replace("　", " ").split(" ", 1)
                
                # ケース名の更新
                case.client_name = new_c_name
                case.client_name_kana = new_c_kana
                
                # 相続人テーブルの更新
                update_heir(
                    contractor.id,
                    name=new_c_name,
                    rel=new_c_rel,
                    kana_last=k_parts[0],
                    kana_first=k_parts[1] if len(k_parts) > 1 else "",
                    dob=new_c_dob,
                    # 住所
                    zip_code=new_c_zip, pref=new_c_pref, city=new_c_city,
                    street=new_c_street, building=new_c_bldg,
                    # 連絡先
                    phone_contacts=[{"value": new_c_phone}] if new_c_phone else [],
                    email_contacts=[{"value": new_c_email}] if new_c_email else []
                )
                session.commit()
                st.toast("更新しました", icon="✅")
                st.rerun()
        else:
            st.warning("相続人が登録されていません。下のリストから追加してください。")

    # ---------------------------------------------------------
    # 2. 被相続人 情報
    # ---------------------------------------------------------
    st.subheader("🙏 被相続人（故人）情報")
    with st.container(border=True):
        if deceased:
            d_addr = get_address_info("deceased", deceased.id)
            
            d1, d2 = st.columns(2)
            with d1:
                new_d_name = st.text_input("被相続人 氏名", value=f"{deceased.name_last}　{deceased.name_first}")
                new_d_kana = st.text_input("被相続人 フリガナ", value=f"{deceased.name_last_kana or ''}　{deceased.name_first_kana or ''}")
                # ★修正: keyを追加
                new_d_dob = _get_date_input("生年月日", deceased.date_of_birth, key="deceased_dob")
                # ★修正: keyを追加
                new_d_dod = _get_date_input("死亡日（相続開始日）", deceased.date_of_death, key="deceased_dod")
                new_d_honseki = st.text_input("本籍地", value=deceased.hometown or "")

            with d2:
                st.markdown("**最後の住所**")
                dd1, dd2 = st.columns([1, 2])
                new_d_zip = dd1.text_input("郵便番号 (故)", value=d_addr.get("zip_code", ""))
                new_d_pref = dd2.text_input("都道府県 (故)", value=d_addr.get("prefecture", ""))
                new_d_city = st.text_input("市区町村 (故)", value=d_addr.get("city_ward_town", ""))
                new_d_street = st.text_input("番地 (故)", value=d_addr.get("street_address", ""))
                new_d_bldg = st.text_input("建物名 (故)", value=d_addr.get("building_name", ""))

            if st.button("💾 被相続人情報を更新", key="save_deceased"):
                d_parts = new_d_name.replace("　", " ").split(" ", 1)
                dk_parts = new_d_kana.replace("　", " ").split(" ", 1)
                
                update_deceased(
                    deceased.id,
                    name_last=d_parts[0],
                    name_first=d_parts[1] if len(d_parts) > 1 else "",
                    kana_last=dk_parts[0],
                    kana_first=dk_parts[1] if len(dk_parts) > 1 else "",
                    dob=new_d_dob,
                    dod=new_d_dod,
                    hometown=new_d_honseki,
                    # 住所
                    last_zip_code=new_d_zip,
                    last_pref=new_d_pref,
                    last_city=new_d_city,
                    last_street=new_d_street,
                    last_building=new_d_bldg
                )
                st.toast("更新しました", icon="✅")
                st.rerun()

    # ---------------------------------------------------------
    # 3. 相続人リスト (編集可能テーブル)
    # ---------------------------------------------------------
    st.subheader("👪 相続人・関係者リスト")
    
    if deceased:
        # DBからデータを取得して辞書リストへ変換
        current_heirs_data = []
        if deceased.heirs:
            for h in deceased.heirs:
                role = "契約者" if h.is_contracting_party else "相続人"
                current_heirs_data.append({
                    "id": h.id, # 編集用キー
                    "name": f"{h.name_last} {h.name_first}".strip(),
                    "relationship": h.relationship_type,
                    "dob": h.date_of_birth,
                    "role": role
                })
        
        # DataFrame作成
        df_heirs = pd.DataFrame(current_heirs_data)
        
        # 空の場合のスキーマ定義
        if df_heirs.empty:
            df_heirs = pd.DataFrame(columns=["id", "name", "relationship", "dob", "role"])

        # ★ st.data_editor で編集可能にする
        st.info("👇 下の表を直接編集できます。行の追加・削除も可能です。")
        
        edited_df = st.data_editor(
            df_heirs,
            column_config={
                "id": None, # IDは非表示
                "name": st.column_config.TextColumn("氏名 (全角スペース区切り)", required=True, width="medium"),
                "relationship": st.column_config.TextColumn("続柄", required=True, width="small"),
                "dob": st.column_config.DateColumn("生年月日", format="YYYY/MM/DD"),
                "role": st.column_config.SelectboxColumn("役割", options=["相続人", "契約者"], required=True, width="small")
            },
            num_rows="dynamic", # 行追加・削除を許可
            use_container_width=True,
            key="heir_list_editor",
            hide_index=True
        )

        # 保存ボタン (一括同期)
        if st.button("💾 リストの変更を保存", type="primary"):
            try:
                # DataFrameを辞書リストに変換
                # 日付型(NaT)の処理などは sync_heir_list 内で行う
                data_to_sync = edited_df.to_dict(orient="records")
                
                # サービス層で同期実行
                result = sync_heir_list(deceased.id, data_to_sync)
                
                msg = []
                if result['added']: msg.append(f"{result['added']}名追加")
                if result['updated']: msg.append(f"{result['updated']}名更新")
                if result['deleted']: msg.append(f"{result['deleted']}名削除")
                
                final_msg = "、".join(msg) if msg else "変更はありません"
                st.success(f"保存しました ({final_msg})")
                
                # 完了後にリロード
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"保存中にエラーが発生しました: {e}")

    # ---------------------------------------------------------
    # 4. 案件削除 (Danger Zone)
    # ---------------------------------------------------------
    st.divider()
    with st.expander("🗑️ 案件の削除 (Danger Zone)"):
        st.warning("この操作は取り消せません。案件に関する全てのデータ（資産、履歴、ファイル）が削除されます。")
        if st.checkbox("削除を確認しました"):
            if st.button("案件を完全に削除する", type="primary"):
                if delete_case_and_all_related_data(case.case_number):
                    st.success("削除しました。Homeに戻ります。")
                    st.session_state["selected_case_id"] = None
                    import time
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("削除に失敗しました")