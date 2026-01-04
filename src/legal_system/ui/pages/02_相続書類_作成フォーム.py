import os
import sys
from io import BytesIO

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# --- パス解決 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.append(SRC_DIR)

# DBモジュールのインポート
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case

# ページ設定
st.set_page_config(
    page_title="相続書類作成 | 相続業務支援システム", page_icon="📄", layout="wide"
)

# フォント登録
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass


def main():
    st.title("🖨️ 書類自動作成")

    # DB接続
    db = DatabaseManager()
    session = db._get_session()

    # ---------------------------------------------------------
    # 1. 案件選択 (セッション連携機能付き)
    # ---------------------------------------------------------
    try:
        cases = session.query(Case).all()
    except Exception as e:
        st.error(f"DBエラー: {e}")
        return

    if not cases:
        st.warning("⚠️ 案件データが1件もありません。")
        st.info(
            "まずはサイドバーの「99_口座情報_入力」から、案件(G番号)と口座情報を登録してください。"
        )
        return

    # 選択肢リスト作成
    # key: 表示名 (例: "G0001: 山田太郎"), value: case_id (DBのID)
    case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
    options_keys = list(case_options.keys())

    # --- セッションから前回の選択状態を復元 ---
    default_index = 0
    if "current_case_id" in st.session_state:
        # 保存されているIDを持つ選択肢を探す
        current_id = st.session_state["current_case_id"]
        for i, key in enumerate(options_keys):
            if case_options[key] == current_id:
                default_index = i
                break

    # セレクトボックス表示
    selected_label = st.selectbox(
        "📂 作業対象の案件を選択",
        options=options_keys,
        index=default_index,
        key="case_selector",
    )

    # 選択されたらセッションに保存（他の画面でも使えるようにする）
    if selected_label:
        selected_case_id = case_options[selected_label]
        st.session_state["current_case_id"] = selected_case_id

        # 案件オブジェクトの取得
        target_case = session.query(Case).filter_by(case_id=selected_case_id).first()

        # 被相続人情報の表示
        deceased_name = (
            target_case.deceased_ref.name_last if target_case.deceased_ref else "未登録"
        )
        st.caption(f"被相続人: {deceased_name} 様 の手続き書類を作成します。")

    # ---------------------------------------------------------
    # 2. 提出先銀行の選択
    # ---------------------------------------------------------
    # この案件に紐付いている資産(FinancialAsset)を取得
    assets = target_case.financial_assets
    if not assets:
        st.warning(
            f"⚠️ 案件 {target_case.case_number} には口座情報が登録されていません。"
        )
        if st.button("➡️ 口座入力画面へ移動して登録する"):
            st.switch_page("pages/99_口座情報_入力.py")
        return

    # 銀行単位でまとめる
    bank_asset_map = {}
    for asset in assets:
        b_name = asset.bank_ref.bank_name if asset.bank_ref else "不明な銀行"
        if b_name not in bank_asset_map:
            bank_asset_map[b_name] = []
        bank_asset_map[b_name].append(asset)

    st.divider()
    selected_bank_name = st.radio(
        "提出先の金融機関", list(bank_asset_map.keys()), horizontal=True
    )

    if not selected_bank_name:
        return

    # 対象口座の確認表示
    target_assets = bank_asset_map[selected_bank_name]
    with st.expander(
        f"確認: {selected_bank_name} の対象口座 ({len(target_assets)}件)",
        expanded=False,
    ):
        for a in target_assets:
            br = a.branch_ref.branch_name if a.branch_ref else "支店不明"
            num = a.account_number if a.account_number else "番号不明"
            atype = a.account_type_ref.type_name if a.account_type_ref else ""
            st.text(f"・{br} {atype} {num}")

    # ---------------------------------------------------------
    # 3. 書類雛形の選択
    # ---------------------------------------------------------
    files = db.get_all_files()
    if not files:
        st.error("雛形ファイルがありません。管理者に連絡してください。")
        return

    # テンプレートPDFのみをフィルタリング
    file_opts = {f["filename"]: f["hash"] for f in files}

    st.divider()
    col_temp, col_btn = st.columns([3, 1])

    with col_temp:
        selected_file_name = st.selectbox(
            "使用するテンプレート", list(file_opts.keys())
        )

    with col_btn:
        st.write("")  # スペース調整
        st.write("")
        if st.button("🚀 PDF作成", type="primary", use_container_width=True):
            # --- PDF生成ロジック (変更なし) ---
            file_hash = file_opts[selected_file_name]
            deceased = target_case.deceased_ref

            data_map = {
                "{case_number}": target_case.case_number,
                "{deceased_name}": f"{deceased.name_last} {deceased.name_first}"
                if deceased
                else "",
                "{death_date}": str(deceased.date_of_death)
                if deceased and deceased.date_of_death
                else "",
                "{bank_name}": selected_bank_name,
            }

            for i, asset in enumerate(target_assets):
                idx = i + 1
                br_name = asset.branch_ref.branch_name if asset.branch_ref else ""
                ac_type = (
                    asset.account_type_ref.type_name if asset.account_type_ref else ""
                )
                ac_num = asset.account_number
                data_map[f"{{branch_{idx}}}"] = br_name
                data_map[f"{{type_{idx}}}"] = ac_type
                data_map[f"{{number_{idx}}}"] = ac_num

            try:
                coords = db.get_coordinates_by_hash(file_hash)

                TEMPLATE_DIR = os.path.join(ROOT_DIR, "data", "templates")
                template_path = os.path.join(TEMPLATE_DIR, selected_file_name)

                if not os.path.exists(template_path):
                    st.error(f"ファイルが見つかりません: {template_path}")
                    return

                output = PdfWriter()
                input_pdf = PdfReader(template_path)

                for i, page in enumerate(input_pdf.pages):
                    page_num = i + 1
                    page_coords = [c for c in coords if c["page"] == page_num]

                    if page_coords:
                        packet = BytesIO()
                        width = float(page.mediabox.width)
                        height = float(page.mediabox.height)
                        can = canvas.Canvas(packet, pagesize=(width, height))

                        for c in page_coords:
                            print_text = c["value"]
                            if str(print_text).startswith("{") and str(
                                print_text
                            ).endswith("}"):
                                if print_text in data_map:
                                    print_text = data_map[print_text]

                            font_name = (
                                "IPAexG" if os.path.exists(FONT_PATH) else "Helvetica"
                            )
                            can.setFont(font_name, c["font_size"])
                            if c["color"] == "red":
                                can.setFillColorRGB(1, 0, 0)
                            else:
                                can.setFillColorRGB(0, 0, 0)

                            # Y座標補正
                            can.drawString(
                                c["x"], float(height) - c["y"], str(print_text)
                            )

                        can.save()
                        packet.seek(0)
                        overlay = PdfReader(packet)
                        page.merge_page(overlay.pages[0])

                    output.add_page(page)

                out_stream = BytesIO()
                output.write(out_stream)

                st.success(f"作成完了: {selected_file_name}")
                st.download_button(
                    label="📥 PDFダウンロード",
                    data=out_stream,
                    file_name=f"作成済_{target_case.client_name}_{selected_bank_name}.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error(f"作成エラー: {e}")
            finally:
                session.close()


if __name__ == "__main__":
    main()
