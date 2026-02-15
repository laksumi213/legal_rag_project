# src/legal_system/core/pdf_processor.py

import logging
import re
import unicodedata
from typing import Any, Dict

import fitz  # PyMuPDF
import numpy as np

from legal_system.core.ocr_engine import OCREngine

logger = logging.getLogger(__name__)


class ReferralSheetParser:
    """
    紹介連絡表（フォーマット固定）の解析クラス。
    テキスト抽出を試み、値が取れなければOCRへフォールバックするロジックを搭載。
    """

    def __init__(self):
        self.ocr_engine = OCREngine()

    def parse_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        PDFバイナリを受け取り、解析結果の辞書を返すメインメソッド。
        """
        # Step 1: まず高速なテキスト抽出(PyMuPDF)を試す
        raw_text_1 = self._extract_text_only(file_bytes)
        parsed_data_1 = self._process_text_to_data(raw_text_1)

        # Step 2: 判定ロジック
        # 顧客名などの主要項目が空の場合、テキスト抽出では「枠線（ラベル）」しか取れていないと判断し、
        # 強制的にOCR(画像解析)を実行する。
        if not parsed_data_1.get("client_name"):
            logger.info(
                "テキスト抽出で値が取得できないため、OCR(画像解析)を実行します。"
            )
            ocr_text = self._perform_ocr(file_bytes)

            # OCR結果で再パース
            parsed_data_2 = self._process_text_to_data(ocr_text)
            parsed_data_2["_debug_mode"] = "OCR_FALLBACK (Auto)"
            parsed_data_2["_debug_raw_text"] = ocr_text
            return parsed_data_2

        # テキスト抽出で成功していればそれを返す
        parsed_data_1["_debug_mode"] = "TEXT_LAYER (High Speed)"
        parsed_data_1["_debug_raw_text"] = raw_text_1
        return parsed_data_1

    def _process_text_to_data(self, raw_text: str) -> Dict[str, Any]:
        """テキスト正規化と正規表現抽出の共通処理"""
        # 正規化 (NFKC)
        norm_text = unicodedata.normalize("NFKC", raw_text)
        # 抽出実行
        return self._extract_fields_via_regex(norm_text)

    def _extract_text_only(self, file_bytes: bytes) -> str:
        """PyMuPDFによるテキスト抽出のみ"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _perform_ocr(self, file_bytes: bytes) -> str:
        """PyMuPDFで画像化 -> PaddleOCRで解析"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_ocr_text = []
        import cv2

        for page in doc:
            # 精度向上のためzoom=2.0で画像化
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_array = np.frombuffer(pix.samples, dtype=np.uint8)

            # PaddleOCR用にBGR変換
            if pix.n == 4:
                img = img_array.reshape(pix.height, pix.width, 4)
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = img_array.reshape(pix.height, pix.width, 3)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                img = img_array.reshape(pix.height, pix.width, pix.n)

            result = self.ocr_engine.ocr.ocr(img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    full_ocr_text.append(line[1][0])

        doc.close()
        # OCR結果は行ごとに分かれているため改行で結合
        return "\n".join(full_ocr_text)

    def _clean_name_spacing(self, text: str) -> str:
        """氏名のスペース整理"""
        if not text:
            return ""
        text = text.strip()
        text = re.sub(r"[\s　]{2,}", "###", text)
        text = re.sub(r"[\s　]", "", text)
        return text.replace("###", " ")

    def _extract_fields_via_regex(self, text: str) -> Dict[str, Any]:
        """正規表現による項目抽出"""
        data = {}

        # 被相続人情報の除外ロジック
        ignore_keywords = ["被相続人", "死亡日", "相続開始", "遺言信託"]
        target_text = text

        # 最も上にあるキーワードでカットする
        min_idx = len(text)
        cut_flag = False
        for kw in ignore_keywords:
            idx = text.find(kw)
            if idx != -1 and idx < min_idx:
                min_idx = idx
                cut_flag = True

        if cut_flag:
            target_text = text[:min_idx]

        # パターン定義
        patterns = {
            "client_name": r"顧客名(?:\([^)]*\))?[\s:：]*([^\n]+)",
            "client_name_kana": r"フリガナ(?:\([^)]*\))?[\s:：]*([^\n]+)",
            "referral_sec_branch_name": r"(?:支店|部店)名[\s:：]*([^\n]+)",
            "referral_sec_rep_name": r"担当(?:部店)?者名?[\s:：]*([^\n]+)",
            "sol_case_number": r"SOL案件No\.?[\s:：]*([A-Z0-9-]+)",
            "introduction_date": r"紹介日[\s:：]*(\d{4}[\s年/-]\d{1,2}[\s月/-]\d{1,2})",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, target_text)
            if match:
                val = match.group(1).strip()
                # ラベル自体を誤って拾ってしまうケースの除外 ("顧客名" という値が入っていたら空にする)
                if val in ["顧客名", "フリガナ", "住所", "支店名", "担当者名"]:
                    data[key] = ""
                else:
                    data[key] = self._clean_name_spacing(val) if "name" in key else val
            else:
                data[key] = ""

        # 電話番号の抽出
        phones = re.findall(r"[\d-]{10,13}", target_text)
        unique_phones = list(dict.fromkeys(phones))
        data["client_phone_1"] = unique_phones[0] if len(unique_phones) > 0 else ""
        data["client_phone_2"] = unique_phones[1] if len(unique_phones) > 1 else ""

        # 住所抽出
        addr_match = re.search(
            r"住所[\s:：]*([\s\S]+?)(?:\n\s*(?:ニーズ|電話|TEL|氏名|フリガナ)|$)",
            target_text,
        )
        if addr_match:
            data["client_address"] = addr_match.group(1).replace("\n", "").strip()
        else:
            data["client_address"] = ""

        return data


def analyze_referral_pdf(file_bytes: bytes) -> Dict[str, Any]:
    return ReferralSheetParser().parse_pdf(file_bytes)
