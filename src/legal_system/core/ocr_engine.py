# src/legal_system/core/ocr_engine.py

# ==========================================
# 【重要】循環参照エラー回避用 強力パッチ
try:
    import pydantic.v1
except ImportError:
    pass
# ==========================================

import logging
from typing import Any, Dict

try:
    import pytesseract
    from pdf2image import convert_from_bytes
    from PIL import Image, ImageEnhance
except ImportError:
    pytesseract = None
    convert_from_bytes = None
    Image = None

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .ai_factory import AIFactory

logger = logging.getLogger(__name__)


def preprocess_image_for_bottom(img, threshold=190):
    """
    【下半分専用】強力なノイズ除去
    担当者印や罫線のノイズを消すための処理。
    ※上半分（顧客情報）には使いません。
    """
    gray_img = img.convert("L")
    enhancer = ImageEnhance.Contrast(gray_img)
    high_contrast_img = enhancer.enhance(2.0)
    binarized_img = high_contrast_img.point(lambda x: 0 if x < threshold else 255, "1")
    return binarized_img


def extract_text_from_scanned_pdf(file_bytes: bytes) -> str:
    if not pytesseract or not convert_from_bytes:
        return "Error"
    try:
        images = convert_from_bytes(file_bytes, dpi=300, fmt="jpeg")
        full = ""
        for i, img in enumerate(images):
            full += pytesseract.image_to_string(img, lang="jpn+eng")
        return full
    except Exception as e:
        return str(e)


def analyze_legal_heir_document(file_bytes: bytes) -> Dict[str, Any]:
    # (変更なし)
    if not pytesseract or not convert_from_bytes:
        return {"error": "OCR不足"}
    try:
        images = convert_from_bytes(file_bytes, dpi=400, fmt="jpeg", grayscale=True)
        raw = pytesseract.image_to_string(images[0], lang="jpn", config="--psm 6")
        llm = AIFactory.get_llm(mode="local")
        prompt = ChatPromptTemplate.from_template("""法定相続情報解析... {ocr_text}""")
        chain = prompt | llm | JsonOutputParser()
        return chain.invoke({"ocr_text": raw})
    except Exception as e:
        return {"error": str(e)}


def analyze_referral_contact_sheet(file_bytes: bytes) -> Dict[str, Any]:
    """
    【ハイブリッドAI解析版（修正）】
    - TOP: 画像処理なし（素の画像）で読み取り精度を回復
    - BOTTOM: Geminiで高速処理
    """
    if not pytesseract or not convert_from_bytes:
        return {"error": "OCRライブラリがインストールされていません。"}

    try:
        # 1. 画像変換
        images = convert_from_bytes(file_bytes, dpi=400, fmt="jpeg")
        full_img = images[0]
        width, height = full_img.size

        # --- A. エリア定義 (必要最小限かつ確実な範囲) ---

        # 1. Top (顧客情報)
        # 上のタイトル「新規案件情報」を避け(0.22)、
        # 下の「紹介元情報」ヘッダー手前まで(0.43)を確保
        top_start = int(height * 0.25)
        top_end = int(height * 0.38)
        img_top_raw = full_img.crop((0, top_start, width, top_end))

        # 2. Bottom (担当者・SOL)
        table_top = int(height * 0.75)
        split_x = int(width * 0.65)

        img_left_raw = full_img.crop((0, table_top, split_x, height))
        img_right_raw = full_img.crop((split_x, table_top, width, height))

        # --- B. 前処理 ---

        # ★修正: TOPエリアは「加工なし」に戻す
        # 二値化すると薄い住所文字が消えるため、グレースケールのみにする
        img_top = img_top_raw.convert("L")

        # BOTTOMエリアは引き続きノイズ除去を適用（印鑑などに強いため）
        img_left = preprocess_image_for_bottom(img_left_raw, threshold=190)
        img_right = preprocess_image_for_bottom(img_right_raw, threshold=190)

        # OCR実行
        ocr_config = r"--psm 6 -c preserve_interword_spaces=1"

        text_top = pytesseract.image_to_string(img_top, lang="jpn", config=ocr_config)
        text_left = pytesseract.image_to_string(img_left, lang="jpn", config=ocr_config)
        text_right = pytesseract.image_to_string(
            img_right, lang="jpn", config=ocr_config
        )

    except Exception as e:
        logger.error(f"OCR Process Error: {e}")
        return {"error": f"OCR処理に失敗しました: {e}"}

    # --- C. ハイブリッドAI解析 ---
    try:
        # 1. TOPエリア (Local AI)
        llm_local = AIFactory.get_llm(mode="local")

        prompt_top = """
        あなたはデータ入力者です。OCR結果から以下の顧客情報をJSONで抽出してください。
        
        【OCRテキスト】
        {text}
        
        【抽出ルール】
        - 氏名: 「顧客名」欄。
        - フリガナ: 「フリガナ」欄。
        - 住所: 「住所」欄の内容をすべて結合する。途中で切れていても可能な限り拾うこと。
        - 電話: 携帯優先で抽出。
        
        【JSONフォーマット】
        {{
            "client_name": "",
            "client_name_kana": "",
            "client_address": "",
            "client_phone": ""
        }}
        """
        chain_top = (
            ChatPromptTemplate.from_template(prompt_top)
            | llm_local
            | JsonOutputParser()
        )

        # 2. BOTTOMエリア (Cloud Gemini)
        llm_cloud = AIFactory.get_llm(mode="cloud")

        prompt_bottom = """
        あなたはデータ入力者です。
        
        【左側テキスト】{text_left}
        【右側テキスト】{text_right}
        
        【抽出ルール】
        - 支店名: 「担当部店」の右。「FC2課」などは削除して「浦和」のみ。
        - 担当者名: 「担当者」の右。
        - SOL番号: 右側テキストにある5〜6桁の数字。
        - 日付: YYYY-MM-DD。
        
        【JSONフォーマット】
        {{
            "sol_case_number": "",
            "introduction_date": "",
            "referral_sec_branch_name": "",
            "referral_sec_rep_name": "",
            "consent_date": ""
        }}
        """
        chain_bottom = (
            ChatPromptTemplate.from_template(prompt_bottom)
            | llm_cloud
            | JsonOutputParser()
        )

        # 実行
        res_top = chain_top.invoke({"text": text_top})
        res_bottom = chain_bottom.invoke(
            {"text_left": text_left, "text_right": text_right}
        )

        # マージ
        final_result = {**res_top, **res_bottom}

        # デバッグ情報
        final_result["_debug_raw_text"] = (
            f"[TOP]\n{text_top}\n\n[LEFT]\n{text_left}\n\n[RIGHT]\n{text_right}"
        )
        final_result["_debug_images"] = {
            "top": img_top,
            "left": img_left,
            "right": img_right,
        }

        return final_result

    except Exception as e:
        logger.error(f"AI Parsing Error: {e}")
        return {
            "error": f"解析エラー: {e}",
            "_debug_raw_text": f"[TOP]\n{text_top}\n\n[LEFT]\n{text_left}\n\n[RIGHT]\n{text_right}",
        }
