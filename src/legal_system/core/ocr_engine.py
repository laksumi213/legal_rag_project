# src/legal_system/core/ocr_engine.py

"""
OCR処理エンジン・モジュール (Hybrid: Gemini Vision + PaddleOCR)
デフォルトではGemini Visionを使用し、環境が整っている場合のみPaddleOCRを補助的に使用します。
"""

import logging
import os
import base64
import tempfile
from typing import List, Dict, Any, Optional, Union

# PyMuPDF (fitz)
import fitz

# LangChain (Gemini用)
from langchain_core.messages import HumanMessage
from src.legal_system.core.ai_factory import AIFactory

# PaddleOCR / OpenCV (Optional - Import Errorを許容)
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

logger = logging.getLogger(__name__)


class OCREngine:
    """
    PaddleOCRを使用した帳票OCR取り込み機能を提供するクラス。
    ライブラリが不足している場合は、機能を無効化します（クラッシュさせない）。
    """

    def __init__(self, lang: str = "japan"):
        self.ocr = None
        self.is_available = False

        if cv2 is None or np is None:
            logger.warning("OpenCV (cv2) または numpy が見つかりません。Local OCRは無効化されます。")
        elif PaddleOCR is None:
            logger.warning("PaddleOCR が見つかりません。Local OCRは無効化されます。")
        else:
            try:
                # PaddleOCRの初期化 (GUIがない環境を想定して use_angle_cls=True)
                # show_log=False でログ出力を抑制
                self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
                self.is_available = True
            except Exception as e:
                logger.error(f"PaddleOCR init failed: {e}")

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDFファイルからテキストと座標情報を抽出する（Local OCR）。
        
        Returns:
            List[Dict]: 抽出結果のリスト。OCR不可の場合は空リスト。
        """
        if not self.is_available:
            return []

        results = []
        doc = None
        try:
            doc = fitz.open(pdf_path)
            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                pix = page.get_pixmap()
                
                # PyMuPDF -> OpenCV
                img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                
                if pix.n == 4:
                    img = img_array.reshape(pix.height, pix.width, 4)
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n == 3:
                    img = img_array.reshape(pix.height, pix.width, 3)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    img = img_array.reshape(pix.height, pix.width, pix.n)

                page_result = self.ocr.ocr(img, cls=True)
                
                if not page_result:
                    continue

                for line in page_result:
                    if not line: continue
                    for res in line:
                        # res format: [coords, [text, confidence]]
                        results.append({
                            "page": page_index + 1,
                            "coords": res[0],
                            "text": res[1][0],
                            "confidence": res[1][1]
                        })
        except Exception as e:
            logger.error(f"Local OCR Error: {e}")
            return []
        finally:
            if doc:
                doc.close()
            
        return results


# -----------------------------------------------------------------------------
# 外部公開関数 (Hybrid: Gemini優先)
# -----------------------------------------------------------------------------

def extract_text_with_gemini(file_bytes: bytes) -> str:
    """
    Gemini Vision APIを使用して、PDF/画像から全文テキストを抽出する。
    """
    try:
        # CloudモードのLLMを取得
        llm = AIFactory.get_llm("cloud", temperature=0.0)
        
        # PDFを画像リストに変換 (最初の2ページのみを対象として軽量化・高速化)
        # ※ pdf2image が必要
        try:
            from pdf2image import convert_from_bytes
            # dpi=150 は速度と精度のバランスが良い
            images = convert_from_bytes(file_bytes, dpi=150, first_page=1, last_page=2)
        except ImportError:
            logger.warning("pdf2image not found. Skipping Gemini Vision.")
            return ""
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            return ""

        if not images:
            return ""

        # メッセージ構築
        content_parts = [{"type": "text", "text": "この書類に書かれているすべての文字を、読み取れる順序で書き起こしてください。Markdownなどは不要で、テキストのみを出力してください。"}]
        
        for img in images:
            # メモリ上でJPEG変換
            buf = base64.BytesIO() if hasattr(base64, 'BytesIO') else __import__('io').BytesIO()
            img.save(buf, format="JPEG")
            b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
            
            content_parts.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{b64_data}"
            })

        msg = HumanMessage(content=content_parts)
        res = llm.invoke([msg])
        
        return res.content

    except Exception as e:
        logger.error(f"Gemini OCR Failed: {e}")
        return ""


def extract_text_from_scanned_pdf(file_input: Union[str, bytes]) -> str:
    """
    スキャンされたPDFからテキストを抽出する（Gemini優先）。
    
    Args:
        file_input (str | bytes): ファイルパス(str) または ファイル本体(bytes)
    
    Returns:
        str: 抽出されたテキスト全文
    """
    # 入力がパスならバイト列を読み込む
    file_bytes = None
    if isinstance(file_input, str):
        if os.path.exists(file_input):
            with open(file_input, "rb") as f:
                file_bytes = f.read()
    else:
        file_bytes = file_input

    if not file_bytes:
        return ""

    # 1. Gemini Vision を試行 (優先)
    logger.info("Attempting Gemini Vision for text extraction...")
    gemini_text = extract_text_with_gemini(file_bytes)
    if gemini_text and len(gemini_text.strip()) > 20: # ある程度読めたら採用
        logger.info("Used Gemini Vision for OCR.")
        return gemini_text

    # 2. Geminiがダメなら Local OCR (PaddleOCR) を試行
    logger.info("Gemini Vision failed or returned empty. Falling back to Local OCR (PaddleOCR)...")
    engine = OCREngine()
    if engine.is_available:
        # Local OCRはファイルパスが必要なため、一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            results = engine.process_pdf(tmp_path)
            full_text = "\n".join([r["text"] for r in results])
            if full_text:
                logger.info("Used PaddleOCR (Local) for OCR.")
                return full_text
        except Exception as e:
            logger.error(f"Local OCR failed: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return "" # どちらも失敗