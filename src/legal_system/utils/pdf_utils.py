import io
import os
from typing import List, Dict, Any

import fitz  # PyMuPDF
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# フォント設定 (97_書式座標登録ツール.py から移植)
# BASE_DIR の計算は、pdf_utils.py がどこに配置されるかに依存するため調整
# utils ディレクトリが src/legal_system/utils にあると仮定
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception as e:
    print(f"フォントの登録に失敗しました: {e}")

def apply_coordinates_to_pdf(original_pdf_bytes: bytes, coordinates: List[Dict[str, Any]]) -> io.BytesIO:
    """
    元のPDFバイナリデータと座標リストを受け取り、座標を適用した新しいPDFバイナリデータを返す。

    Args:
        original_pdf_bytes (bytes): 元のPDFファイルのバイナリデータ。
        coordinates (List[Dict[str, Any]]): 適用する座標情報のリスト。
                                          各辞書は `{"x": float, "y": float, "page": int, "value": str, "font_size": float, "color": str}` を含む。

    Returns:
        io.BytesIO: 座標が適用された新しいPDFファイルのバイナリデータストリーム。
    """
    reader = PdfReader(io.BytesIO(original_pdf_bytes))
    output_pdf = PdfWriter()

    # ページごとに処理
    for i, page_obj in enumerate(reader.pages):
        page_num = i + 1

        # このページの座標データのみ抽出
        page_coords = [c for c in coordinates if c.get("page") == page_num]

        if page_coords:
            packet_page = io.BytesIO()
            pw = float(page_obj.mediabox.width) # ページの幅 (pt)
            ph = float(page_obj.mediabox.height) # ページの高さ (pt)

            can_page = canvas.Canvas(packet_page, pagesize=(pw, ph))

            for coord in page_coords:
                val = coord.get("value")
                if not val: # 値がなければスキップ
                    continue

                x = float(coord.get("x"))
                y = float(coord.get("y"))
                f_size = float(coord.get("font_size", 10))
                clr = coord.get("color", "black")

                # 色設定
                c_obj = red if clr == "red" else black
                can_page.setFillColor(c_obj)
                can_page.setStrokeColor(c_obj)

                # 座標変換 (画像クリック(左上) -> PDF(左下))
                # 97_書式座標登録ツール.py のロジックを参考に、
                # X, Y は画像ピクセル座標と仮定し、PDFポイント座標に変換する
                # ただし、元のツールでは preview_scale を使っていたが、ここではPDF自体に描画するため
                # 直接的なピクセルtoポイント変換ではなく、ページサイズを基準にする。
                # 重要なのは、登録されている X, Y が「画像上のピクセル」であるという前提をどう扱うか。
                # ここでは、PDFの幅と高さに対するピクセル座標の比率を使用する簡易的なアプローチを取る。
                # 理想的には、登録時にPDFのポイント座標で保存するか、画像変換時のDPI情報を保持すべき。
                # 一旦、登録されているX,Yは「PDF上のpt単位の座標」として扱い、Streamlit_image_coordinates の動作に合わせる。
                # -> Streamlit_image_coordinates の x,y は表示されている画像のピクセル座標。これをPDFのpt単位に変換する必要がある。
                #    97_書式座標登録ツール.py では img_w_px, img_h_px を使っていたが、ここではそれがない。
                #    一時的に「登録されたX,YがPDFのポイント座標に近く、左下原点に変換する」という前提で進める。

                # Streamlit Image Coordinates は左上原点 (0,0)
                # ReportLab の drawString は左下原点 (0,0)
                # PDFの高さからクリックされたY座標を引くことでY座標を変換する
                draw_x = x # float(x) # 既にfloat
                draw_y_base = ph - y # float(y) # 既にfloat

                if str(val).startswith("RECT:"):
                    try:
                        dims = val.replace("RECT:", "").split("x")
                        w_pt = float(dims[0])
                        h_pt = float(dims[1])
                        rect_y = draw_y_base - h_pt # ReportLabは矩形の左下を指定
                        can_page.setLineWidth(1) # 線の太さ。font_sizeを流用していたが、一旦固定。
                        can_page.rect(draw_x, rect_y, w_pt, h_pt, stroke=1, fill=0)
                    except Exception as e:
                        print(f"矩形描画エラー: {e}")
                else:
                    if "IPAexG" in pdfmetrics.getRegisteredFontNames():
                        can_page.setFont("IPAexG", f_size)
                    else:
                        can_page.setFont("Helvetica", f_size) # フォントがない場合のフォールバック
                    text_y = draw_y_base - (f_size * 0.8) # テキストのベースライン調整
                    can_page.drawString(draw_x, text_y, str(val))
            can_page.save()
            packet_page.seek(0)
            overlay = PdfReader(packet_page)
            page_obj.merge_page(overlay.pages[0])

        output_pdf.add_page(page_obj)

    out_stream = io.BytesIO()
    output_pdf.write(out_stream)
    out_stream.seek(0)
    return out_stream

def extract_region_from_pdf_page(page: fitz.Page, x: float, y: float, width_pt: float, height_pt: float, dpi: int = 200) -> Image.Image:
    """
    Extracts a region from a PDF page as a PIL Image.

    Args:
        page (fitz.Page): The PyMuPDF page object.
        x (float): The x-coordinate of the top-left corner of the region in PDF points.
        y (float): The y-coordinate of the top-left corner of the region in PDF points.
        width_pt (float): The width of the region in PDF points.
        height_pt (float): The height of the region in PDF points.
        dpi (int): The DPI to render the PDF page at for image extraction.

    Returns:
        Image.Image: A PIL Image object of the extracted region.
    """
    # PDFページを画像にレンダリング
    # get_pixmapのmatrixを調整して、指定したDPIでレンダリングする
    matrix = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=matrix)
    img = Image.open(io.BytesIO(pix.tobytes()))

    # PDFポイント座標を画像ピクセル座標に変換
    # fitz.Rect(x, y, x + width_pt, y + height_pt) はPDFの左下原点
    # PIL Imageは左上原点なのでY座標を反転させる
    # pdf_height_pt = page.rect.height

    # PDFの座標系 (左下原点) から画像(PIL: 左上原点)への変換を考慮
    # pixmapのサイズを取得
    img_width_px, img_height_px = pix.width, pix.height

    # PDFポイントからピクセルへのスケーリングファクタ
    scale_x = img_width_px / page.rect.width
    scale_y = img_height_px / page.rect.height

    # 領域のPDF座標 (左下原点) をPILのピクセル座標 (左上原点) に変換
    # x_px, y_px は領域の左上ピクセル座標
    x_px = int(x * scale_x)
    y_px = int((page.rect.height - (y + height_pt)) * scale_y)
    width_px = int(width_pt * scale_x)
    height_px = int(height_pt * scale_y)

    # 確実に画像サイズ内に収まるように調整
    x_px = max(0, x_px)
    y_px = max(0, y_px)
    width_px = min(width_px, img_width_px - x_px)
    height_px = min(height_px, img_height_px - y_px)
    
    # 領域をクロップ
    cropped_img = img.crop((x_px, y_px, x_px + width_px, y_px + height_px))
    
    return cropped_img

def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 200) -> List[Image.Image]:
    """
    PDFのバイナリデータをページの画像のリストに変換する。

    Args:
        pdf_bytes (bytes): PDFファイルのバイナリデータ。
        dpi (int): 画像の解像度 (dots per inch)。

    Returns:
        List[Image.Image]: 各ページをレンダリングしたPIL Imageオブジェクトのリスト。
    """
    images = []
    try:
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            
            # get_pixmapのmatrixを調整して、指定したDPIでレンダリングする
            matrix = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=matrix)
            
            img = Image.open(io.BytesIO(pix.tobytes()))
            images.append(img)
            
        pdf_document.close()
    except Exception as e:
        print(f"PDFから画像への変換中にエラーが発生しました: {e}")

    return images
