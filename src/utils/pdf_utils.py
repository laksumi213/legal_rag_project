# src/utils/pdf_utils.py
import io
from typing import Any, Dict, List

import fitz  # PyMuPDF
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from core.config import Config

# フォント設定
# src/core/config.py の BASE_DIR を使用して堅牢にパス解決
FONT_PATH = Config.DATA_DIR / "fonts" / "ipaexg.ttf"


def _register_font():
    """フォント登録を安全に行う"""
    try:
        if FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont("IPAexG", str(FONT_PATH)))
            return True
    except Exception as e:
        print(f"フォント登録エラー: {e}")
    return False


# モジュール読み込み時に登録試行
_font_available = _register_font()


def apply_coordinates_to_pdf(
    original_pdf_bytes: bytes, coordinates: List[Dict[str, Any]]
) -> io.BytesIO:
    """
    PDFバイナリと座標リストを受け取り、文字/図形を書き込んだPDFを返す。
    """
    reader = PdfReader(io.BytesIO(original_pdf_bytes))
    output_pdf = PdfWriter()

    for i, page_obj in enumerate(reader.pages):
        page_num = i + 1
        page_coords = [c for c in coordinates if c.get("page") == page_num]

        if page_coords:
            # ページサイズ取得 (Point単位)
            pw = float(page_obj.mediabox.width)
            ph = float(page_obj.mediabox.height)

            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=(pw, ph))

            for coord in page_coords:
                val = coord.get("value")
                if not val:
                    continue

                x = float(coord.get("x", 0))
                y = float(coord.get("y", 0))
                f_size = float(coord.get("font_size", 10))
                clr_str = coord.get("color", "black")

                # ReportLabの色設定
                c_obj = red if clr_str == "red" else black
                can.setFillColor(c_obj)
                can.setStrokeColor(c_obj)

                # 座標変換: 左上原点(Streamlit/Flet) -> 左下原点(PDF)
                # ※登録ツールの仕様に合わせて調整が必要。
                # ここでは「登録値がPDF上のPoint座標(左上基準)である」と仮定して変換
                draw_x = x
                draw_y = ph - y

                # 矩形 (RECT:WxH) の場合
                if str(val).startswith("RECT:"):
                    try:
                        dims = val.replace("RECT:", "").split("x")
                        w_pt = float(dims[0])
                        h_pt = float(dims[1])
                        # 矩形は左下が基準
                        rect_y = draw_y - h_pt
                        can.setLineWidth(1)
                        can.rect(draw_x, rect_y, w_pt, h_pt, stroke=1, fill=0)
                    except Exception as e:
                        print(f"矩形描画エラー: {e}")
                else:
                    # テキスト描画
                    font_name = "IPAexG" if _font_available else "Helvetica"
                    can.setFont(font_name, f_size)

                    # ベースライン調整 (簡易)
                    text_y = draw_y - (f_size * 0.8)
                    can.drawString(draw_x, text_y, str(val))

            can.save()
            packet.seek(0)

            # オーバーレイ合成
            overlay_pdf = PdfReader(packet)
            if len(overlay_pdf.pages) > 0:
                page_obj.merge_page(overlay_pdf.pages[0])

        output_pdf.add_page(page_obj)

    out_stream = io.BytesIO()
    output_pdf.write(out_stream)
    out_stream.seek(0)
    return out_stream


def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[Image.Image]:
    """
    PDFバイナリをPIL画像のリストに変換 (プレビュー用)
    """
    images = []
    try:
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page in pdf_doc:
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.open(io.BytesIO(pix.tobytes()))
            images.append(img)
        pdf_doc.close()
    except Exception as e:
        print(f"PDF画像変換エラー: {e}")
    return images
