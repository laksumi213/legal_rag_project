# src/legal_system/ui/components/cases/registry_acquisition.py

import json
import os
import re

import pandas as pd
import streamlit as st
from legal_system.models.tables import Address, Case, H_AddressHistory, RealEstateAsset

# サービスのインポート (利用可能な場合のみ)
try:
    from services.automation.touki_service import touki_service
except ImportError:
    touki_service = None

# ==========================================
# 定数・パス設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/legal_system/ui/components/cases -> src -> root
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
)
DATA_RULES_DIR = os.path.join(ROOT_DIR, "data", "rules")
RECIPIENTS_FILE = os.path.join(DATA_RULES_DIR, "donation_recipients.json")

# ==========================================
# ヘルパー関数
# ==========================================


def get_probable_prefectures(session, case_id: int) -> list[str]:
    """
    案件データから「関係しそうな都道府県」を推論してリストアップするヘルパー
    """
    prefs = set()
    case = session.query(Case).get(case_id)
    if not case:
        return []

    # 1. 被相続人の最後の住所
    if case.deceased_ref and case.deceased_ref.last_address_id:
        addr = session.query(Address).get(case.deceased_ref.last_address_id)
        if addr and addr.prefecture:
            prefs.add(addr.prefecture)

    # 2. 相続人の住所
    if case.deceased_ref and case.deceased_ref.heirs:
        for h in case.deceased_ref.heirs:
            link = (
                session.query(H_AddressHistory)
                .filter_by(heir_id=h.id, is_current_address=True)
                .first()
            )
            if link:
                addr = session.query(Address).get(link.address_id)
                if addr and addr.prefecture:
                    prefs.add(addr.prefecture)

    # 3. 既に登録されている不動産の所在
    existing_assets = session.query(RealEstateAsset).filter_by(case_id=case_id).all()
    for a in existing_assets:
        m = re.match(r"(.{2,3}[都道府県])", a.location or "")
        if m:
            prefs.add(m.group(1))

    return list(prefs)


def update_touki_address_callback(new_address: str):
    """ボタンクリックで住所入力欄を更新するためのコールバック"""
    st.session_state["touki_target_address"] = new_address


def load_donation_recipients() -> list[dict]:
    """寄付先リストをJSONから読み込む（なければデフォルト作成）"""
    if not os.path.exists(RECIPIENTS_FILE):
        # デフォルトデータ
        default_data = [
            {"name": "日本赤十字社", "address": "東京都港区芝大門一丁目１番３号"},
            {"name": "日本ユニセフ協会", "address": "東京都港区高輪四丁目６番１２号"},
            {
                "name": "国境なき医師団日本",
                "address": "東京都世田谷区若林二丁目３０番９号",
            },
            {"name": "あしなが育英会", "address": "東京都千代田区平河町二丁目７番５号"},
            {"name": "日本財団", "address": "東京都港区赤坂一丁目２番２号"},
            {"name": "がん研究会", "address": "東京都江東区有明三丁目８番３１号"},
        ]
        try:
            os.makedirs(DATA_RULES_DIR, exist_ok=True)
            with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            return default_data
        except:
            return []

    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_donation_recipients(data: list[dict]):
    """寄付先リストをJSONに保存"""
    os.makedirs(DATA_RULES_DIR, exist_ok=True)
    with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==========================================
# メインレンダラー
# ==========================================
def render_registry_acquisition(session, target_case_id: int):
    """
    登記情報取得ツールのメインレンダラー
    """
    st.subheader("🌐 登記情報取得ツール")

    # 環境チェック
    if os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER"):
        st.warning(
            "⚠️ 現在Docker(サーバー)環境で実行中です。自動操作ブラウザは画面に表示されません（バックグラウンド実行）。"
        )
    else:
        st.info("自動操作ブラウザを起動し、登記情報提供サービスで検索を行います。")

    if not touki_service:
        st.error(
            "機能が無効です (src/services/automation/touki_service.py が見つかりません)"
        )
        return

    # --- UI構成 ---
    category = st.radio("請求カテゴリ", ["土地・建物", "商業・法人"], horizontal=True)

    # ステート初期化 (エラー回避のため)
    if "touki_target_address" not in st.session_state:
        st.session_state["touki_target_address"] = ""
    if "touki_target_address_corp" not in st.session_state:
        st.session_state["touki_target_address_corp"] = ""
    if "touki_corp_name" not in st.session_state:
        st.session_state["touki_corp_name"] = ""

    # ==========================
    # A. 商業・法人モード (寄付先対応)
    # ==========================
    if category == "商業・法人":
        # 1. リストデータのロード
        recipients_list = load_donation_recipients()
        recipients_map = {r["name"]: r["address"] for r in recipients_list}

        # 2. 入力モード選択
        col_mode, col_blank = st.columns([2, 1])
        with col_mode:
            input_method = st.radio(
                "入力方法", ["手動入力", "寄付先リストから選択"], horizontal=True
            )

        # 3. リスト選択 & 値の同期ロジック
        if input_method == "寄付先リストから選択":
            if not recipients_map:
                st.warning(
                    "登録されている寄付先がありません。下の「リスト管理」から追加してください。"
                )
            else:
                # 選択ボックス
                current_selection = st.selectbox(
                    "団体を選択",
                    list(recipients_map.keys()),
                    key="sel_donation_recipient",
                )

                # --- ロジック: 選択変更 or 初期表示時の自動反映 ---
                # 前回の選択状態を保存しておく変数を初期化
                if "last_donation_selection" not in st.session_state:
                    st.session_state["last_donation_selection"] = None

                # 「今回選択された値が前回と違う」 または 「入力欄が空（初期状態）」 の場合に値をセット
                fields_empty = (not st.session_state.get("touki_corp_name")) and (
                    not st.session_state.get("touki_target_address_corp")
                )
                selection_changed = (
                    current_selection != st.session_state["last_donation_selection"]
                )

                if selection_changed or fields_empty:
                    # マップから該当情報を取得してセッションステート(入力欄)を更新
                    if current_selection in recipients_map:
                        st.session_state["touki_corp_name"] = current_selection
                        st.session_state["touki_target_address_corp"] = recipients_map[
                            current_selection
                        ]

                    # 変更を記録
                    st.session_state["last_donation_selection"] = current_selection

                    # ※ ここで on_change コールバックを使わず、描画の直前で値を更新することで
                    #   スムーズに下の text_input に反映させ、不要なリロード（スクロール飛び）を防ぐ

        # 4. 入力フォーム
        # セッションステートとバインドされているため、上のロジックで更新された値が即座に表示される
        st.text_input(
            "会社・法人名", key="touki_corp_name", placeholder="例: 株式会社チェスター"
        )

        st.text_input(
            "本店所在地",
            key="touki_target_address_corp",
            placeholder="都道府県 市区町村...",
        )

        # 5. リスト管理機能 (CRUD)
        with st.expander("⚙️ 寄付先リストの管理 (追加・編集・削除)"):
            st.caption("よく使う寄付先などをここに登録しておくと便利です。")

            # DataFrame化して編集可能にする
            df_recipients = pd.DataFrame(recipients_list)

            edited_df = st.data_editor(
                df_recipients,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn("法人・団体名", required=True),
                    "address": st.column_config.TextColumn(
                        "所在地", required=True, width="large"
                    ),
                },
                key="editor_donation_list",
            )

            if st.button("💾 リストを更新して保存", key="btn_save_recipients"):
                # DataFrame -> List[Dict]
                new_data = edited_df.to_dict(orient="records")
                # 空行削除
                clean_data = [d for d in new_data if d.get("name") and d.get("address")]

                save_donation_recipients(clean_data)
                st.toast("リストを更新しました！", icon="✅")
                import time

                time.sleep(1)
                st.rerun()

    # ==========================
    # B. 土地・建物モード
    # ==========================
    else:
        target_type = "土地"
        input_mode = st.radio(
            "入力方法",
            ["登録済み不動産から選択", "手動入力"],
            horizontal=True,
            key="touki_input_mode",
        )

        # 1. 登録済みから選択
        if input_mode == "登録済み不動産から選択":
            assets = (
                session.query(RealEstateAsset).filter_by(case_id=target_case_id).all()
            )
            if not assets:
                st.warning("登録された不動産がありません")
            else:
                # 選択肢の作成
                asset_options = {
                    f"【{a.property_type}】{a.location} {a.lot_number or a.house_number or ''}": a
                    for a in assets
                }
                selected_label = st.selectbox(
                    "取得対象を選択", list(asset_options.keys())
                )

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
            placeholder="例: 東京都中央区銀座1丁目1-1",
        )

        # 都道府県補完アシスト
        if current_addr_val and not re.match(
            r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", current_addr_val
        ):
            st.warning(
                "⚠️ 住所に都道府県が含まれていません。以下から選択して追加してください。"
            )

            prob_prefs = get_probable_prefectures(session, target_case_id)
            if prob_prefs:
                cols = st.columns(len(prob_prefs))
                for idx, p in enumerate(prob_prefs):
                    cols[idx].button(
                        f"+ {p}",
                        key=f"add_pref_{idx}",
                        on_click=update_touki_address_callback,
                        args=(f"{p}{current_addr_val}",),
                    )
            else:
                st.info("候補が見つかりません。手動で都道府県を入力してください。")

        target_type_radio = st.radio(
            "種別",
            ["土地", "建物"],
            index=0 if target_type == "土地" else 1,
            horizontal=True,
        )

    # ==========================
    # C. 実行ボタン
    # ==========================
    st.divider()
    if st.button(
        "🚀 登記情報を取得 (ブラウザ起動)", type="primary", use_container_width=True
    ):
        # 最終的な検索対象住所を決定
        final_addr = ""
        final_name = ""

        if category == "商業・法人":
            # セッションステートから値を取得 (バインドされているため)
            final_name = st.session_state.get("touki_corp_name", "")
            final_addr = st.session_state.get("touki_target_address_corp", "")

            if not final_name:
                st.error("会社・法人名が入力されていません")
                return
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
                        msg = touki_service.request_commercial(final_name, final_addr)
                    else:
                        # 住所と種別を渡す
                        msg = touki_service.request_real_estate(
                            final_addr, target_type_radio
                        )

                    st.success(msg)
                except Exception as e:
                    # エラー詳細を表示
                    import traceback

                    st.error(f"エラーが発生しました: {e}")
                    st.text(traceback.format_exc())
