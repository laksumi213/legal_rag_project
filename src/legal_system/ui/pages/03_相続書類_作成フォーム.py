# src/legal_system/ui/pages/02_相続書類_作成フォーム.py

import os
import sys
from io import BytesIO

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# パス解決
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, FileRegistry

# フォント設定
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(
    page_title="書類作成・管理 | 相続業務支援", page_icon="📄", layout="wide"
)


# ==========================================
# データ置換ロジック
# ==========================================
def create_replacement_map(case_data):
    """
    データベースの案件情報(Case)から、置換用の辞書を作成する
    """
    map_dict = {}

    # 基本情報
    map_dict["{case_number}"] = case_data.case_number
    map_dict["{client_name}"] = case_data.client_name

    # 被相続人情報
    if case_data.deceased_ref:
        d = case_data.deceased_ref
        full_name = f"{d.name_last} {d.name_first}".strip()
        map_dict["{deceased_name}"] = full_name
        map_dict["{deceased_name_last}"] = d.name_last or ""
        map_dict["{deceased_name_first}"] = d.name_first or ""

        if d.date_of_death:
            map_dict["{death_date}"] = d.date_of_death.strftime("%Y年%m月%d日")
            map_dict["{death_year_seireki}"] = str(d.date_of_death.year)
            if d.date_of_death.year >= 2019:
                map_dict["{death_year_wareki}"] = f"令和{d.date_of_death.year - 2018}"
            else:
                map_dict["{death_year_wareki}"] = str(d.date_of_death.year)
            map_dict["{death_month}"] = str(d.date_of_death.month)
            map_dict["{death_day}"] = str(d.date_of_death.day)

    # 相続人情報 (簡易実装: 1人目を取得)
    if case_data.deceased_ref and case_data.deceased_ref.heirs:
        h = case_data.deceased_ref.heirs[0]
        full_name_h = f"{h.name_last} {h.name_first}".strip()
        map_dict["{heir_name}"] = full_name_h
        map_dict["{heir_name_last}"] = h.name_last or ""
        map_dict["{heir_name_first}"] = h.name_first or ""

        map_dict["{heir_address}"] = "（住所未登録）"
        map_dict["{heir_pref}"] = ""
        map_dict["{heir_city}"] = ""
        map_dict["{heir_street}"] = ""
        map_dict["{heir_building}"] = ""

    return map_dict


def generate_pdf(template_path, coords, replacement_map):
    """
    テンプレートPDFに、座標データと置換マップを使って文字を埋め込む
    """
    try:
        reader = PdfReader(template_path)
        output = PdfWriter()

        # 画像DPI(200) -> PDF DPI(72) の変換比率
        # 登録ツールが dpi=200 で画像化しているため固定
        SCALE_FACTOR = 72.0 / 200.0

        for i, page_obj in enumerate(reader.pages):
            page_num = i + 1
            page_coords = [c for c in coords if c["page"] == page_num]

            if page_coords:
                packet = BytesIO()
                pw = float(page_obj.mediabox.width)
                ph = float(page_obj.mediabox.height)
                can = canvas.Canvas(packet, pagesize=(pw, ph))

                for c in page_coords:
                    raw_val = c["value"]
                    text_to_draw = replacement_map.get(raw_val, raw_val)
                    if not text_to_draw:
                        continue

                    # 座標変換: 画像ピクセル -> PDFポイント
                    draw_x = c["x"] * SCALE_FACTOR

                    # Y座標変換:
                    # 1. 画像(上原点) -> PDF(下原点)に反転: ph - (y * scale)
                    # これで「文字のTop」のY座標が求まる
                    top_y = ph - (c["y"] * SCALE_FACTOR)

                    c_obj = red if c["color"] == "red" else black
                    can.setStrokeColor(c_obj)
                    can.setFillColor(c_obj)

                    font_sz = float(c["font_size"])

                    if str(text_to_draw).startswith("RECT:"):
                        try:
                            dims = text_to_draw.replace("RECT:", "").split("x")
                            w_pt, h_pt = float(dims[0]), float(dims[1])
                            # RECTの場合、top_yから下に四角形を描く
                            can.rect(draw_x, top_y - h_pt, w_pt, h_pt, stroke=1, fill=0)
                        except:
                            pass
                    else:
                        # テキストの場合
                        # ReportLabのdrawStringは「ベースライン(左下)」を指定する
                        # 登録ツールは「左上」を指定している
                        # -> ベースラインは Top より「フォントサイズ分」下にある
                        # さらに日本語フォント(IPAexG)はベースラインが低めなので、少し多めに下げる

                        baseline_y = top_y - (
                            font_sz * 0.9
                        )  # ★補正値: 0.9〜1.0くらいが目安

                        can.setFont("IPAexG", font_sz)
                        can.drawString(draw_x, baseline_y, str(text_to_draw))

                can.save()
                packet.seek(0)
                overlay = PdfReader(packet)
                page_obj.merge_page(overlay.pages[0])

            output.add_page(page_obj)

        out_stream = BytesIO()
        output.write(out_stream)
        return out_stream

    except Exception as e:
        st.error(f"PDF生成エラー: {e}")
        return None


# ==========================================
# メイン画面ロジック
# ==========================================
def render_creation_tab(db, session):
    st.subheader("🖨️ 書類自動作成")

    # 案件選択
    cases = session.query(Case).all()
    if not cases:
        st.warning("案件データがありません。")
        return

    case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}

    default_idx = 0
    if "current_case_id" in st.session_state:
        cid = st.session_state["current_case_id"]
        keys = list(case_options.keys())
        for i, k in enumerate(keys):
            if case_options[k] == cid:
                default_idx = i
                break

    selected_label = st.selectbox(
        "📂 案件選択", list(case_options.keys()), index=default_idx
    )

    if selected_label:
        cid = case_options[selected_label]
        st.session_state["current_case_id"] = cid
        target_case = session.query(Case).filter_by(case_id=cid).first()

        d_name = (
            target_case.deceased_ref.name_last
            + " "
            + target_case.deceased_ref.name_first
            if target_case.deceased_ref
            else "未登録"
        )
        st.info(f"被相続人: **{d_name}**")

        st.divider()

        # テンプレート選択
        files = (
            session.query(FileRegistry)
            .filter(FileRegistry.filename.like("%.pdf"))
            .all()
        )

        if not files:
            st.warning("テンプレート(PDF)が登録されていません。")
            return

        file_opts = {f.filename: f.file_hash for f in files}
        selected_file_name = st.selectbox(
            "使用するテンプレート", list(file_opts.keys())
        )

        if selected_file_name:
            target_hash = file_opts[selected_file_name]

            # 作成ボタン
            if st.button("🚀 PDFを作成する", type="primary"):
                coords = db.get_coordinates_by_hash(target_hash)
                if not coords:
                    st.error(
                        "このファイルには座標データが登録されていません。「書式座標登録ツール」で設定してください。"
                    )
                else:
                    template_path = os.path.join(
                        ROOT_DIR, "data", "templates", selected_file_name
                    )

                    if not os.path.exists(template_path):
                        st.error(
                            f"テンプレートファイルが見つかりません: {template_path}"
                        )
                    else:
                        replace_map = create_replacement_map(target_case)
                        pdf_data = generate_pdf(template_path, coords, replace_map)

                        if pdf_data:
                            st.success("✅ 作成完了！")
                            st.download_button(
                                label="📥 作成されたPDFをダウンロード",
                                data=pdf_data,
                                file_name=f"作成済_{selected_file_name}",
                                mime="application/pdf",
                            )


def main():
    st.title("📑 書類作成・データ管理")

    db = DatabaseManager()
    session = db._get_session()

    tab1, tab2, tab3 = st.tabs(["🖨️ 書類作成", "📥 雛形登録 (OCR)", "🗑️ データ管理"])

    with tab1:
        render_creation_tab(db, session)

    with tab2:
        from legal_system.ui.components.admin_tools import render_upload_tab

        render_upload_tab(db)

    with tab3:
        from legal_system.ui.components.admin_tools import render_management_tab

        render_management_tab(db)

    session.close()


if __name__ == "__main__":
    main()
