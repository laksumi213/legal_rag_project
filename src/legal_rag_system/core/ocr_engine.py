import logging
from io import BytesIO
from typing import Optional

# 外部ライブラリ
try:
    import pytesseract
    from pdf2image import convert_from_bytes
except ImportError:
    # 依存関係が不足している場合のエラーハンドリング用
    pytesseract = None
    convert_from_bytes = None

# ロガー設定
logger = logging.getLogger(__name__)

# Windowsの場合のTesseractパス設定例 (必要に応じてコメントアウトを解除してパスを指定)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_scanned_pdf(file_bytes: bytes) -> str:
    """
    画像化されたPDF(スキャンデータ)からテキストを抽出する。
    pdf2image で画像に変換し、pytesseract でOCRを実行する。
    """
    if not pytesseract or not convert_from_bytes:
        return "Error: OCRライブラリ(pytesseract, pdf2image)がインストールされていません。"

    full_text = ""
    try:
        # PDFを画像のリストに変換 (dpi=300推奨)
        # fmt="jpeg" で処理を高速化
        images = convert_from_bytes(file_bytes, dpi=300, fmt="jpeg")
        
        for i, img in enumerate(images):
            # 日本語(jpn)と英語(eng)のハイブリッドOCR
            text = pytesseract.image_to_string(img, lang='jpn+eng')
            
            # ページ区切りを明確にする
            full_text += f"\n--- Page {i+1} (OCR Result) ---\n{text}"
            
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return f"OCR処理中にエラーが発生しました: {str(e)}"
        
    return full_text
