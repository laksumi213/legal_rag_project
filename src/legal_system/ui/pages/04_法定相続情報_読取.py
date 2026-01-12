# src/legal_system/ui/pages/04_法定相続情報_読取.py

import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st
from pdf2image import convert_from_bytes

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ocr_engine import analyze_legal_heir_document
from legal_system.models.tables import Address, Case, Deceased, Heir

st.set_page_config(page_title="法定相続情報 読取", page_icon="👪", layout="wide")


def main():
    st.title("👪 法定相続情報 読取・登録")
    st.caption(
        "「法定相続情報一覧図」をAI解析(オフライン)し、データベースへ登録します。"
    )

    db = DatabaseManager()
    session = db._get_session()

    # --- サイドバー: 設定 ---
    with st.sidebar:
        st.header("📂 対象案件")
        cases = session.query(Case).all()
        case_opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
        selected_case_label = st.selectbox("案件選択", list(case_opts.keys()))

        if not selected_case_label:
            st.warning("案件を選択してください")
            session.close()
            return

        current_case_id = case_opts[selected_case_label]
        st.divider()
        uploaded_file = st.file_uploader("PDFファイルをアップロード", type=["pdf"])

    # --- メインエリア ---
    if not uploaded_file:
        st.info(
            "👈 サイドバーから「法定相続情報一覧図(PDF)」をアップロードしてください。"
        )
        session.close()
        return

    # ファイル読込
    file_bytes = uploaded_file.read()

    # 画像変換（表示用）
    try:
        images = convert_from_bytes(file_bytes, dpi=200, fmt="jpeg")
        display_img = images[0]
    except Exception as e:
        st.error(f"画像変換エラー: {e}")
        session.close()
        return

    # --- 解析実行ボタン ---
    if "ocr_result" not in st.session_state:
        st.session_state["ocr_result"] = None

    col_btn, col_status = st.columns([1, 4])
    with col_btn:
        analyze_btn = st.button(
            "🔍 AI解析実行 (Local)", type="primary", use_container_width=True
        )

    if analyze_btn:
        with st.spinner("🤖 ローカルAIが画像を解析中... (PlladeOCR + Ollama)"):
            result = analyze_legal_heir_document(file_bytes)
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["ocr_result"] = result
                st.toast("✅ 解析完了しました！", icon="🎉")

    st.divider()

    # --- 2カラムレイアウト: 左(画像) / 右(編集フォーム) ---
    col_img, col_data = st.columns([1, 1.2])

    # 左側: 画像プレビュー
    with col_img:
        st.subheader("📄 原本プレビュー")
        st.image(display_img, use_container_width=True, caption="アップロードされたPDF")

    # 右側: データ編集 & 保存
    with col_data:
        st.subheader("📝 データ確認・編集")

        if st.session_state["ocr_result"]:
            data = st.session_state["ocr_result"]

            # 1. 被相続人 (Deceased)
            st.markdown("##### 1. 被相続人 (亡くなった方)")
            with st.container(border=True):
                d_info = data.get("deceased", {})
                d_name = st.text_input("氏名", value=d_info.get("name", ""))
                c1, c2 = st.columns(2)
                d_date = c1.text_input(
                    "死亡日",
                    value=d_info.get("death_date", ""),
                    help="YYYY-MM-DD形式推奨",
                )
                d_addr = st.text_input(
                    "最後の住所", value=d_info.get("last_address", "")
                )

            # 2. 相続人 (Heirs) - DataEditorでExcelライクに
            st.markdown("##### 2. 相続人一覧")
            heirs_raw = data.get("heirs", [])

            # DataFrame化して表示
            df_heirs = pd.DataFrame(heirs_raw)
            # カラム構成の定義
            column_config = {
                "name": st.column_config.TextColumn(
                    "氏名", required=True, width="medium"
                ),
                "relationship": st.column_config.SelectboxColumn(
                    "続柄",
                    options=[
                        "妻",
                        "夫",
                        "長男",
                        "二男",
                        "長女",
                        "二女",
                        "養子",
                        "兄弟姉妹",
                    ],
                    required=True,
                    width="small",
                ),
                "birth_date": st.column_config.TextColumn(
                    "生年月日", help="YYYY-MM-DD"
                ),
                "address": st.column_config.TextColumn("住所", width="large"),
            }

            # データがない場合の空枠作成
            if df_heirs.empty:
                df_heirs = pd.DataFrame(
                    columns=["name", "relationship", "birth_date", "address"]
                )

            edited_df = st.data_editor(
                df_heirs,
                column_config=column_config,
                num_rows="dynamic",  # 行追加・削除を許可
                use_container_width=True,
                key="heir_editor",
            )

            st.caption("※行を追加・削除・修正できます。")

            st.divider()

            # 3. 保存ボタン
            if st.button(
                "💾 データベースに保存・更新", type="primary", use_container_width=True
            ):
                try:
                    # DB保存ロジック
                    target_case = (
                        session.query(Case).filter_by(case_id=current_case_id).first()
                    )

                    # A. 被相続人のUpsert
                    deceased = target_case.deceased_ref
                    if not deceased:
                        deceased = Deceased(case_id=target_case.case_id)
                        session.add(deceased)

                    deceased.name_last = (
                        d_name.split(" ")[0] if " " in d_name else d_name
                    )
                    deceased.name_first = d_name.split(" ")[1] if " " in d_name else ""

                    # 日付変換トライ
                    try:
                        deceased.date_of_death = datetime.strptime(
                            d_date, "%Y-%m-%d"
                        ).date()
                    except:
                        pass  # エラー時は無視またはNone

                    # 住所登録 (簡易)
                    if d_addr:
                        new_addr = Address(prefecture="", street_address=d_addr)
                        session.add(new_addr)
                        session.flush()
                        deceased.last_address_id = new_addr.id

                    # B. 相続人の洗い替え (既存削除 -> 新規登録)
                    # ※実運用ではID維持のためにUpdateをかけるべきだが、ここでは簡易化のため洗い替え
                    for h in deceased.heirs:
                        session.delete(h)

                    for index, row in edited_df.iterrows():
                        if not row["name"]:
                            continue

                        full_name = row["name"]
                        lname = (
                            full_name.split(" ")[0] if " " in full_name else full_name
                        )
                        fname = full_name.split(" ")[1] if " " in full_name else ""

                        b_date = None
                        try:
                            b_date = datetime.strptime(
                                str(row["birth_date"]), "%Y-%m-%d"
                            ).date()
                        except:
                            pass

                        new_heir = Heir(
                            deceased=deceased,
                            name_last=lname,
                            name_first=fname,
                            relationship_type=row["relationship"],
                            date_of_birth=b_date,
                        )
                        session.add(new_heir)

                        # 住所
                        if row["address"]:
                            h_addr = Address(
                                prefecture="", street_address=row["address"]
                            )
                            session.add(h_addr)
                            session.flush()
                            # 中間テーブルへの登録が必要だが、models定義に合わせて簡易実装
                            # 実装済みの H_AddressHistory 等を経由する必要があります
                            # 今回はHeir作成までとします。

                    session.commit()
                    st.success(
                        f"✅ 案件「{target_case.client_name}」のデータを更新しました！"
                    )
                    st.balloons()

                except Exception as e:
                    session.rollback()
                    st.error(f"保存エラー: {e}")

        else:
            st.info("👈 左上のボタンから解析を実行してください。")

    session.close()


if __name__ == "__main__":
    main()
