# src/legal_system/core/ocr_engine.py

"""
OCR処理エンジン・モジュール (Hybrid: Gemini Vision + PaddleOCR)
デフォルトではGemini Visionを使用し、環境が整っている場合のみPaddleOCRを補助的に使用します。
"""

import base64
import logging
import os
import tempfile
from typing import Any, Dict, List, Union

# PyMuPDF (fitz)
import fitz

# LangChain (Gemini用)
from langchain_core.messages import HumanMessage

# Pillow for Image processing
from PIL import Image

from legal_system.core.ai_factory import AIFactory

# ユーティリティ関数
from legal_system.utils.pdf_utils import extract_region_from_pdf_page

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
            logger.warning(
                "OpenCV (cv2) または numpy が見つかりません。Local OCRは無効化されます。"
            )
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

    def _pil_to_cv2(self, pil_image: Image.Image) -> np.ndarray:
        """
        PIL Image を OpenCV の numpy array (BGR) に変換する。
        """
        if cv2 is None or np is None:
            raise RuntimeError(
                "OpenCV and numpy must be available for image conversion."
            )

        # PIL Image を NumPy 配列に変換 (RGB)
        img_np = np.array(pil_image)
        # RGB から BGR に変換 (OpenCVの標準フォーマット)
        return cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

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
                    if not line:
                        continue
                    for res in line:
                        # res format: [coords, [text, confidence]]
                        results.append(
                            {
                                "page": page_index + 1,
                                "coords": res[0],
                                "text": res[1][0],
                                "confidence": res[1][1],
                            }
                        )
        except Exception as e:
            logger.error(f"Local OCR Error: {e}")
            return []
        finally:
            if doc:
                doc.close()

        return results

    def process_pdf_region(
        self, pdf_bytes: bytes, coordinates: List[Dict[str, Any]], dpi: int = 200
    ) -> List[Dict[str, Any]]:
        """
        PDFバイナリデータと座標リスト（矩形領域）を受け取り、指定された領域のみOCRを実行する。

        Args:
            pdf_bytes (bytes): 元のPDFファイルのバイナリデータ。
            coordinates (List[Dict[str, Any]]): 適用する座標情報のリスト。
                                              `{"x": float, "y": float, "page": int, "value": "RECT:WxH"}` の形式のものを想定。
            dpi (int): OCRに渡す画像のDPI。

        Returns:
            List[Dict]: 抽出結果のリスト。
        """
        if not self.is_available:
            logger.warning("OCR Engine is not available. Skipping region OCR.")
            return []

        results = []
        doc = None
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")

            for coord in coordinates:
                if not str(coord.get("value", "")).startswith("RECT:"):
                    continue  # 矩形座標ではない場合はスキップ

                page_num = coord.get("page")
                if page_num is None or page_num <= 0 or page_num > len(doc):
                    logger.warning(
                        f"Invalid page number {page_num} for coordinate: {coord}"
                    )
                    continue

                page_obj = doc.load_page(page_num - 1)  # fitzは0-indexed

                # 座標情報の解析
                x = float(coord.get("x", 0))
                y = float(coord.get("y", 0))
                dims_str = str(coord["value"]).replace("RECT:", "").split("x")
                width_pt = float(dims_str[0])
                height_pt = float(dims_str[1])

                # 指定領域の画像を抽出
                region_image = extract_region_from_pdf_page(
                    page_obj, x, y, width_pt, height_pt, dpi=dpi
                )

                if region_image:
                    # PIL ImageをOpenCV形式に変換
                    cv2_image = self._pil_to_cv2(region_image)

                    # PaddleOCRでOCR実行
                    page_result = self.ocr.ocr(cv2_image, cls=True)

                    if page_result and page_result[0]:
                        for line in page_result[0]:
                            if not line:
                                continue
                            # 座標は抽出画像内での相対座標になるため、元のPDF座標に変換する必要がある
                            # ただし、OCR結果のcoordsは抽出された画像内での座標
                            # ここでは便宜的にOCRで抽出されたテキストのみを返す
                            # より詳細な統合が必要な場合は、ここで座標変換ロジックを追加する
                            results.append(
                                {
                                    "page": page_num,
                                    "text": line[1][0],
                                    "confidence": line[1][1],
                                }
                            )
        except Exception as e:
            logger.error(f"Region OCR Error: {e}")
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
        content_parts = [
            {
                "type": "text",
                "text": "この書類に書かれているすべての文字を、読み取れる順序で書き起こしてください。Markdownなどは不要で、テキストのみを出力してください。",
            }
        ]

        for img in images:
            # メモリ上でJPEG変換
            buf = (
                base64.BytesIO()
                if hasattr(base64, "BytesIO")
                else __import__("io").BytesIO()
            )
            img.save(buf, format="JPEG")
            b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")

            content_parts.append(
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{b64_data}"}
            )

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
    if gemini_text and len(gemini_text.strip()) > 20:  # ある程度読めたら採用
        logger.info("Used Gemini Vision for OCR.")
        return gemini_text

    # 2. Geminiがダメなら Local OCR (PaddleOCR) を試行
    logger.info(
        "Gemini Vision failed or returned empty. Falling back to Local OCR (PaddleOCR)..."
    )
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

    return ""  # どちらも失敗
