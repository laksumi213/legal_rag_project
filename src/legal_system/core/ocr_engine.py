"""
OCR処理エンジン・モジュール
PaddleOCRおよびPyMuPDFを使用してPDFからテキストを抽出します。
"""

import logging
import numpy as np
import os
from typing import List, Dict, Any, Optional

# PyMuPDF (fitz) のインポート
import fitz

# PaddleOCR のインポート
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

# OpenCV (cv2) のインポートガード
# コンテナ環境でのインストール漏れに対応
try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)

class OCREngine:
    """
    PaddleOCRを使用した帳票OCR取り込み機能を提供するクラス。
    """

    def __init__(self, lang: str = "japan"):
        """
        OCRエンジンの初期化。
        
        Args:
            lang (str): 言語設定（デフォルトは日本語 'japan'）。
        """
        if cv2 is None:
            logger.error("OpenCV (cv2) がインストールされていません。")
        
        if PaddleOCR is None:
            logger.error("PaddleOCR がインストールされていません。")
            self.ocr = None
        else:
            # PaddleOCRの初期化 (GUIがない環境を想定して use_angle_cls=True)
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDFファイルからテキストと座標情報を抽出する。
        
        Args:
            pdf_path (str): PDFファイルのフルパス。
            
        Returns:
            List[Dict[str, Any]]: 認識結果のリスト。
        """
        if cv2 is None or self.ocr is None:
            raise RuntimeError("OCRエンジンの依存ライブラリ (OpenCV または PaddleOCR) が不足しています。")

        results = []
        doc = None
        try:
            doc = fitz.open(pdf_path)
            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                pix = page.get_pixmap()
                
                # PyMuPDFの画像をNumPy配列(OpenCV形式)に変換
                img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                
                # 画像のチャンネル数に合わせてリサイズ/変換
                if pix.n == 4:  # RGBA
                    img = img_array.reshape(pix.height, pix.width, 4)
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n == 3:  # RGB
                    img = img_array.reshape(pix.height, pix.width, 3)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    img = img_array.reshape(pix.height, pix.width, pix.n)

                # PaddleOCRで解析
                page_result = self.ocr.ocr(img, cls=True)
                
                if not page_result:
                    continue

                for line in page_result:
                    if not line:
                        continue
                    for res in line:
                        results.append({
                            "page": page_index + 1,
                            "coords": res[0],
                            "text": res[1][0],
                            "confidence": res[1][1]
                        })
        except Exception as e:
            logger.error(f"OCR処理中に予期せぬエラーが発生しました: {e}")
            raise e
        finally:
            if doc:
                doc.close()
            
        return results

# -----------------------------------------------------------------------------
# 重要: 外部(admin_tools.py)から関数として呼び出すためのエクスポート
# -----------------------------------------------------------------------------
def extract_text_from_scanned_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    既存のUIコンポーネントとの互換性を維持するためのラッパー関数。
    """
    engine = OCREngine()
    return engine.process_pdf(file_path)