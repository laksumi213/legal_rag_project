# src/legal_system/ui/components/cases/basic_info.py

import streamlit as st
import pandas as pd
import unicodedata
import re
from sqlalchemy.orm import joinedload
from datetime import date
import time

from legal_system.models.tables import Case, Deceased, Heir, Address, H_AddressHistory, H_ContactLink, Contact
from src.services.deceased_service import (
    update_heir, update_deceased, add_heir, delete_heir, 
    get_address_info, get_contact_info, delete_case_and_all_related_data,
    sync_heir_list, search_zip_by_address_api
)
from src.utils.date_utils import convert_seireki_to_wareki
from src.legal_system.ui.utils.scroll_helper import maintain_scroll_position


def _get_date_input(label, current_value, key=None):
    """
    日付入力ヘルパー（Noneハンドリング & 和暦表示 & key対応）
    """
    val = st.date_input(label, value=current_value if current_value else None, format="YYYY/MM/DD", key=key)
    if val:
        wareki = convert_seireki_to_wareki(val)
        st.caption(f"📅 和暦: **{wareki}**")
    else:
        st.caption("📅 和暦: (日付未設定)")
    return val

def _normalize_kanji_numeric(text: str) -> str:
    """
    漢数字の丁目などを算用数字に変換する (APIヒット率向上用)
    例: 仙川町三丁目 -> 仙川町3丁目
    """
    if not text: return ""
    res = text
    trans_map = {
        '一': '1', '二': '2', '三': '3', '四': '4', '五': '5',
        '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'
    }
    # "○丁目" のパターンを探して置換
    for kanji, num in trans_map.items():
        res = res.replace(f"{kanji}丁目", f"{num}丁目")
    
    return res

def _clean_town_name(text: str) -> str:
    """
    API検索用に、市区町村名から「丁目」「番地」以降をカットして
    最もヒットしやすい「町域」だけの文字列にする
    例: "調布市仙川町三丁目" -> "調布市仙川町"
    """
    if not text: return ""
    
    # 1. NFKC正規化 (全角英数→半角など)
    s = unicodedata.normalize("NFKC", text)
    s = s.replace(" ", "").replace("　", "")
    
    # 2. 「丁目」以降をカット
    # 漢数字(一～十)＋丁目、または数字＋丁目のパターンを検知
    match = re.search(r'([0-9０-９一二三四五六七八九十]+丁目)', s)
    if match:
        # マッチした箇所の直前までを切り出す
        idx = match.start()
        s = s[:idx]
    
    # 3. 万が一「番地」「番」などが残っていたらそこもカット
    match_ban = re.search(r'([0-9]+(番地|番))', s)
    if match_ban:
        idx = match_ban.start()
        s = s[:idx]
        
    return s

def _zip_search_callback(target_prefix):
    """
    住所から郵便番号を検索してSessionStateを更新するコールバック
    
    【修正版ロジック】
    HeartRails Geo APIの特性に合わせ、「都道府県 + 市区町村(町域のみ)」の
    最も確実なパターンのみで検索を実行する。
    """
    # 現在の入力値を取得
    pref = st.session_state.get(f"{target_prefix}pref", "").strip()
    city = st.session_state.get(f"{target_prefix}city", "").strip()
    
    if not (pref or city):
        st.toast("⚠️ 都道府県または市区町村を入力してください", icon="⚠️")
        return

    # 町域名の抽出 (丁目・番地カット)
    clean_city = _clean_town_name(city)
    
    # 検索クエリ作成 (都道府県 + 純粋な町名)
    query = f"{pref}{clean_city}"
    
    # 検索実行
    found_zip = search_zip_by_address_api(query)
    
    if found_zip:
        st.session_state[f"{target_prefix}zip"] = found_zip
        st.toast(f"郵便番号を補完しました: {found_zip}\n(検索語: {query})", icon="📮")
    else:
        st.toast(f"見つかりませんでした。\n検索語: {query}", icon="🚫")

def render_basic_info(session, case_id: int):
    """
    基本情報（依頼者・被相続人・相続人）の編集画面を描画する
    """
    # スクロール位置維持のJavaScriptを注入
    maintain_scroll_position()
    
    # 案件削除Expanderの状態をセッションで管理
    if 'danger_zone_expanded' not in st.session_state:
        st.session_state.danger_zone_expanded = False

    def _toggle_danger_zone():
        st.session_state.danger_zone_expanded = not st.session_state.danger_zone_expanded

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
    
    contractor = None
    if deceased and deceased.heirs:
        contractor = next((h for h in deceased.heirs if h.is_contracting_party), None)
        if not contractor:
            contractor = deceased.heirs[0]

    with st.container(border=True):
        if contractor:
            c_addr = get_address_info("heir", contractor.id)
            c_conts = get_contact_info("heir", contractor.id)
            c_phone = next((c["value"] for c in c_conts if c["type"]=="PHONE"), "")
            c_email = next((c["value"] for c in c_conts if c["type"]=="EMAIL"), "")

            # 初期値をSessionStateにセット（初回のみ）
            keys_map = {
                "c_zip": c_addr.get("zip_code", ""),
                "c_pref": c_addr.get("prefecture", ""),
                "c_city": c_addr.get("city_ward_town", ""),
                "c_street": c_addr.get("street_address", ""),
                "c_bldg": c_addr.get("building_name", "")
            }
            for k, v in keys_map.items():
                if k not in st.session_state:
                    st.session_state[k] = v

            col1, col2 = st.columns(2)
            with col1:
                new_c_name = st.text_input("氏名", value=f"{contractor.name_last}　{contractor.name_first}")
                new_c_kana = st.text_input("フリガナ", value=f"{contractor.name_last_kana or ''}　{contractor.name_first_kana or ''}")
                new_c_rel = st.text_input("続柄", value=contractor.relationship_type)
                new_c_dob = _get_date_input("生年月日", contractor.date_of_birth, key="contractor_dob")

            with col2:
                new_c_phone = st.text_input("電話番号", value=c_phone)
                new_c_email = st.text_input("メールアドレス", value=c_email)
                
                st.markdown("---")
                st.caption("現住所")
                
                c1, c2_ = st.columns([1, 2])
                new_c_zip = c1.text_input("郵便番号", key="c_zip")
                c1.button("住所から検索", key="btn_search_c_zip", on_click=_zip_search_callback, args=("c_",), help="住所から郵便番号を検索します")
                
                new_c_pref = c2_.text_input("都道府県", key="c_pref")
                new_c_city = st.text_input("市区町村", key="c_city")
                new_c_street = st.text_input("番地", key="c_street")
                new_c_bldg = st.text_input("建物名", key="c_bldg")

            if st.button("💾 依頼者情報を更新", key="save_contractor", type="primary"):
                parts = new_c_name.replace("　", " ").split(" ", 1)
                k_parts = new_c_kana.replace("　", " ").split(" ", 1)
                
                case.client_name = new_c_name
                case.client_name_kana = new_c_kana
                
                success = update_heir(
                    contractor.id,
                    name=new_c_name,
                    rel=new_c_rel,
                    kana_last=k_parts[0],
                    kana_first=k_parts[1] if len(k_parts) > 1 else "",
                    dob=new_c_dob,
                    zip_code=st.session_state.c_zip, 
                    pref=st.session_state.c_pref, 
                    city=st.session_state.c_city,
                    street=st.session_state.c_street, 
                    building=st.session_state.c_bldg,
                    phone_contacts=[{"value": new_c_phone}] if new_c_phone else [],
                    email_contacts=[{"value": new_c_email}] if new_c_email else []
                )
                
                if success:
                    session.commit()
                    st.toast("更新しました", icon="✅")
                    
                    # ★重要: 更新成功時は、古いセッション値を削除して強制リロード
                    for k in keys_map.keys():
                        if k in st.session_state:
                            del st.session_state[k]
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("更新に失敗しました")

        else:
            st.warning("相続人が登録されていません。下のリストから追加してください。")

    # ---------------------------------------------------------
    # 2. 被相続人 情報
    # ---------------------------------------------------------
    st.subheader("🙏 被相続人（故人）情報")
    with st.container(border=True):
        if deceased:
            d_addr = get_address_info("deceased", deceased.id)
            
            keys_map_d = {
                "d_zip": d_addr.get("zip_code", ""),
                "d_pref": d_addr.get("prefecture", ""),
                "d_city": d_addr.get("city_ward_town", ""),
                "d_street": d_addr.get("street_address", ""),
                "d_bldg": d_addr.get("building_name", "")
            }
            for k, v in keys_map_d.items():
                if k not in st.session_state:
                    st.session_state[k] = v

            d1, d2 = st.columns(2)
            with d1:
                new_d_name = st.text_input("被相続人 氏名", value=f"{deceased.name_last}　{deceased.name_first}")
                new_d_kana = st.text_input("被相続人 フリガナ", value=f"{deceased.name_last_kana or ''}　{deceased.name_first_kana or ''}")
                
                new_d_dob = _get_date_input("生年月日", deceased.date_of_birth, key="deceased_dob")
                new_d_dod = _get_date_input("死亡日（相続開始日）", deceased.date_of_death, key="deceased_dod")
                
                new_d_honseki = st.text_input("本籍地", value=deceased.hometown or "")

            with d2:
                st.markdown("**最後の住所**")
                
                dd1, dd2 = st.columns([1, 2])
                new_d_zip = dd1.text_input("郵便番号 (故)", key="d_zip")
                dd1.button("住所から検索", key="btn_search_d_zip", on_click=_zip_search_callback, args=("d_",), help="都道府県・市区町村（町名まで）を使って郵便番号を検索します")
                
                new_d_pref = dd2.text_input("都道府県 (故)", key="d_pref")
                new_d_city = st.text_input("市区町村 (故)", key="d_city")
                new_d_street = st.text_input("番地 (故)", key="d_street")
                new_d_bldg = st.text_input("建物名 (故)", key="d_bldg")

            if st.button("💾 被相続人情報を更新", key="save_deceased"):
                d_parts = new_d_name.replace("　", " ").split(" ", 1)
                dk_parts = new_d_kana.replace("　", " ").split(" ", 1)
                
                success = update_deceased(
                    deceased.id,
                    name_last=d_parts[0],
                    name_first=d_parts[1] if len(d_parts) > 1 else "",
                    kana_last=dk_parts[0],
                    kana_first=dk_parts[1] if len(dk_parts) > 1 else "",
                    dob=new_d_dob,
                    dod=new_d_dod,
                    hometown=new_d_honseki,
                    last_zip_code=st.session_state.d_zip,
                    last_pref=st.session_state.d_pref,
                    last_city=st.session_state.d_city,
                    last_street=st.session_state.d_street,
                    last_building=st.session_state.d_bldg
                )
                
                if success:
                    st.toast("更新しました", icon="✅")
                    # ★重要: 更新成功時は、古いセッション値を削除して強制リロード
                    for k in keys_map_d.keys():
                        if k in st.session_state:
                            del st.session_state[k]
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("更新に失敗しました")

    # ---------------------------------------------------------
    # 3. 相続人リスト (編集可能テーブル)
    # ---------------------------------------------------------
    st.subheader("👪 相続人・関係者リスト")
    
    if deceased:
        current_heirs_data = []
        if deceased.heirs:
            for h in deceased.heirs:
                role = "契約者" if h.is_contracting_party else "相続人"
                current_heirs_data.append({
                    "id": h.id, 
                    "name": f"{h.name_last} {h.name_first}".strip(),
                    "relationship": h.relationship_type,
                    "dob": h.date_of_birth,
                    "role": role
                })
        
        df_heirs = pd.DataFrame(current_heirs_data)
        
        if df_heirs.empty:
            df_heirs = pd.DataFrame(columns=["id", "name", "relationship", "dob", "role"])

        st.info("👇 下の表を直接編集できます。行の追加・削除も可能です。")
        
        edited_df = st.data_editor(
            df_heirs,
            column_config={
                "id": None, 
                "name": st.column_config.TextColumn("氏名 (全角スペース区切り)", required=True, width="medium"),
                "relationship": st.column_config.TextColumn("続柄", required=True, width="small"),
                "dob": st.column_config.DateColumn("生年月日", format="YYYY/MM/DD"),
                "role": st.column_config.SelectboxColumn("役割", options=["相続人", "契約者"], required=True, width="small")
            },
            num_rows="dynamic", 
            use_container_width=True,
            key="heir_list_editor",
            hide_index=True
        )

        if st.button("💾 リストの変更を保存", type="primary"):
            try:
                data_to_sync = edited_df.to_dict(orient="records")
                result = sync_heir_list(deceased.id, data_to_sync)
                
                msg = []
                if result['added']: msg.append(f"{result['added']}名追加")
                if result['updated']: msg.append(f"{result['updated']}名更新")
                if result['deleted']: msg.append(f"{result['deleted']}名削除")
                
                final_msg = "、".join(msg) if msg else "変更はありません"
                st.success(f"保存しました ({final_msg})")
                
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"保存中にエラーが発生しました: {e}")

    # ---------------------------------------------------------
    # 4. 案件削除 (Danger Zone)
    # ---------------------------------------------------------
    st.divider()
    # Expanderの状態をst.session_stateで制御
    with st.expander("🗑️ 案件の削除 (Danger Zone)", expanded=st.session_state.danger_zone_expanded):
        st.warning("この操作は取り消せません。案件に関する全てのデータ（資産、履歴、ファイル）が削除されます。")
        
        # チェックボックスの状態もセッションで管理
        if 'delete_confirmed' not in st.session_state:
            st.session_state.delete_confirmed = False

        def _confirm_delete_and_keep_expander_open():
            # チェックボックスの状態を更新し、Expanderを開いたままにする
            st.session_state.delete_confirmed = st.session_state.confirm_checkbox
            st.session_state.danger_zone_expanded = True

        st.checkbox(
            "削除を確認しました",
            key="confirm_checkbox",
            value=st.session_state.delete_confirmed,
            on_change=_confirm_delete_and_keep_expander_open
        )

        if st.session_state.delete_confirmed:
            if st.button("案件を完全に削除する", type="primary"):
                if delete_case_and_all_related_data(case.case_number):
                    # 削除成功時は状態をリセット
                    st.session_state.danger_zone_expanded = False
                    st.session_state.delete_confirmed = False
                    st.success("削除しました。Homeに戻ります。")
                    st.session_state["selected_case_id"] = None
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("削除に失敗しました")
