# src/legal_system/ui/components/cases/registry_acquisition.py

import os
import re
import streamlit as st
from sqlalchemy.orm import joinedload
from src.legal_system.models.tables import Case, Address, H_AddressHistory, RealEstateAsset

# サービスのインポート (利用可能な場合のみ)
try:
    from src.services.automation.touki_service import touki_service
except ImportError:
    touki_service = None

def get_probable_prefectures(session, case_id: int) -> list[str]:
    """
    案件データから「関係しそうな都道府県」を推論してリストアップするヘルパー
    """
    prefs = set()
    case = session.query(Case).get(case_id)
    if not case: return []
    
    # 1. 被相続人の最後の住所
    if case.deceased_ref and case.deceased_ref.last_address_id:
        addr = session.query(Address).get(case.deceased_ref.last_address_id)
        if addr and addr.prefecture: prefs.add(addr.prefecture)
    
    # 2. 相続人の住所
    if case.deceased_ref and case.deceased_ref.heirs:
        for h in case.deceased_ref.heirs:
            link = session.query(H_AddressHistory).filter_by(heir_id=h.id, is_current_address=True).first()
            if link:
                addr = session.query(Address).get(link.address_id)
                if addr and addr.prefecture: prefs.add(addr.prefecture)
    
    # 3. 既に登録されている不動産の所在
    existing_assets = session.query(RealEstateAsset).filter_by(case_id=case_id).all()
    for a in existing_assets:
        m = re.match(r'(.{2,3}[都道府県])', a.location or "")
        if m: prefs.add(m.group(1))
        
    return list(prefs)

def update_touki_address_callback(new_address: str):
    """ボタンクリックで住所入力欄を更新するためのコールバック"""
    st.session_state["touki_target_address"] = new_address

def render_registry_acquisition(session, target_case_id: int):
    """
    登記情報取得ツールのメインレンダラー
    """
    st.subheader("🌐 登記情報取得ツール")

    # 環境チェック
    if os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER"):
        st.warning("⚠️ 現在Docker(サーバー)環境で実行中です。自動操作ブラウザは画面に表示されません（バックグラウンド実行）。")
    else:
        st.info("自動操作ブラウザを起動し、登記情報提供サービスで検索を行います。")

    if not touki_service:
        st.error("機能が無効です (src/services/automation/touki_service.py が見つかりません)")
        return

    # --- UI構成 ---
    category = st.radio("請求カテゴリ", ["土地・建物", "商業・法人"], horizontal=True)
    input_mode = "manual"
    
    # ステート初期化
    if "touki_target_address" not in st.session_state:
        st.session_state["touki_target_address"] = ""

    # 変数初期化
    corp_name = ""
    target_addr_input = ""
    current_addr_val = ""
    target_type_radio = "土地" # Default

    # ==========================
    # A. 商業・法人モード
    # ==========================
    if category == "商業・法人":
        corp_name = st.text_input("会社・法人名", placeholder="例: 株式会社チェスター")
        # 商業・法人用の住所入力欄 (Keyを分ける)
        target_addr_input = st.text_input("本店所在地", key="touki_target_address_corp", placeholder="都道府県 市区町村...")

    # ==========================
    # B. 土地・建物モード
    # ==========================
    else:
        target_type = "土地"
        input_mode = st.radio("入力方法", ["登録済み不動産から選択", "手動入力"], horizontal=True, key="touki_input_mode")
        
        # 1. 登録済みから選択
        if input_mode == "登録済み不動産から選択":
            assets = session.query(RealEstateAsset).filter_by(case_id=target_case_id).all()
            if not assets: 
                st.warning("登録された不動産がありません")
            else:
                # 選択肢の作成
                asset_options = {
                    f"【{a.property_type}】{a.location} {a.lot_number or a.house_number or ''}": a 
                    for a in assets
                }
                selected_label = st.selectbox("取得対象を選択", list(asset_options.keys()))
                
                if selected_label:
                    sel_asset = asset_options[selected_label]
                    base_addr = f"{sel_asset.location or ''}{sel_asset.lot_number or sel_asset.house_number or ''}"
                    
                    # 選択変更時にステートを更新
                    if "last_selected_asset_id" not in st.session_state:
                        st.session_state["last_selected_asset_id"] = None
                    
                    if st.session_state["last_selected_asset_id"] != sel_asset.id:
                        st.session_state["touki_target_address"] = base_addr
                        st.session_state["last_selected_asset_id"] = sel_asset.id
                        st.rerun()

                    # 種別の自動判定
                    if sel_asset.property_type in ["Building", "Condo"]: 
                        target_type = "建物"
                    st.caption(f"種別自動判定: {target_type}")

        # 2. 住所入力フォーム (共通)
        current_addr_val = st.text_input(
            "検索する所在・地番 (編集可)", 
            key="touki_target_address",
            placeholder="例: 東京都中央区銀座1丁目1-1"
        )

        # 都道府県補完アシスト
        if current_addr_val and not re.match(r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)', current_addr_val):
            st.warning("⚠️ 住所に都道府県が含まれていません。以下から選択して追加してください。")
            
            prob_prefs = get_probable_prefectures(session, target_case_id)
            if prob_prefs:
                cols = st.columns(len(prob_prefs))
                for idx, p in enumerate(prob_prefs):
                    cols[idx].button(
                        f"+ {p}", 
                        key=f"add_pref_{idx}",
                        on_click=update_touki_address_callback,
                        args=(f"{p}{current_addr_val}",)
                    )
            else:
                st.info("候補が見つかりません。手動で都道府県を入力してください。")

        target_type_radio = st.radio(
            "種別", 
            ["土地", "建物"], 
            index=0 if target_type == "土地" else 1, 
            horizontal=True
        )

    # ==========================
    # C. 実行ボタン
    # ==========================
    if st.button("🚀 登記情報を取得 (ブラウザ起動)", type="primary"):
        # 最終的な検索対象住所を決定
        final_addr = ""
        if category == "商業・法人":
            final_addr = st.session_state.get("touki_target_address_corp", "")
        else:
            final_addr = st.session_state.get("touki_target_address", "")

        if not final_addr:
            st.error("住所/所在が入力されていません")
        else:
            with st.spinner("自動操作中... (ブラウザが起動します)"):
                try:
                    msg = ""
                    if category == "商業・法人":
                        # 会社名と住所を渡す
                        msg = touki_service.request_commercial(corp_name, final_addr)
                    else:
                        # 住所と種別を渡す
                        msg = touki_service.request_real_estate(final_addr, target_type_radio)
                    
                    st.success(msg)
                except Exception as e:
                    # エラー詳細を表示
                    import traceback
                    st.error(f"エラーが発生しました: {e}")
                    st.text(traceback.format_exc())