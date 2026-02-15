# src/legal_system/core/ai_processor.py

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# プロジェクト内モジュール
from legal_system.core.ai_factory import AIFactory

# 追加した CaseSearchKeys をインポート
from legal_system.core.schemas import CaseSearchKeys, DocumentAnalysisResult

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parents[3]
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticDocumentProcessor:
    """
    自律型ドキュメント検証プロセッサ。
    """

    def __init__(self):
        self.provider_mode = os.getenv("AI_PROVIDER", "studio").lower()
        # 構造化出力のために temperature=0.0 を推奨
        self.llm = AIFactory.get_llm(mode=self.provider_mode, temperature=0.0)
        logger.info(f"AgenticProcessor Initialized. Mode: {self.provider_mode}")

    # --- 追加: 検索キー抽出 (予備解析) ---
    def extract_search_keys(self, file_bytes: bytes, mime_type: str) -> CaseSearchKeys:
        """
        書類から「氏名」や「日付」のみを抽出し、案件検索の手がかりにする。
        """
        import base64

        img_b64 = base64.b64encode(file_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{img_b64}"

        prompt = """
        この書類画像から、データベース検索の手がかりとなる「固有名詞」を抽出してください。
        
        # 抽出ルール
        1. **client_name**: 「相続人代表」「依頼者」「受取人」などの氏名があれば抽出。
        2. **deceased_name**: 「被相続人」「名義人（故人）」などの氏名があれば抽出。
        3. **date_hint**: 死亡日や書類作成日など、特定に役立ちそうな日付。
        4. 値が見つからない場合は null (None) にすること。
        """

        try:
            structured_llm = self.llm.with_structured_output(CaseSearchKeys)
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": image_url},
                    ]
                )
            ]
            return structured_llm.invoke(messages)
        except Exception as e:
            logger.error(f"Search key extraction failed: {e}")
            raise e

    # --- 既存: 詳細検証 (本解析) ---
    def _build_verification_prompt(self, kintone_context: Dict[str, Any]) -> str:
        context_str = json.dumps(kintone_context, ensure_ascii=False, indent=2)
        return f"""
        あなたは行政書士事務所の「シニア・ドキュメント・チェッカー」AIです。
        以下の「期待される正解データ（Kintone）」と「入力された書類画像」を比較し、厳格な監査を行ってください。

        ### 1. 期待される正解データ (Context)
        ```json
        {context_str}
        ```

        ### 2. あなたのタスク (Reasoning Process)
        1. **知覚**: 書類の種類を特定し、書かれている文字を読み取る。
        2. **推論**: 
           - 書類の記載内容（Actual）と、正解データ（Expected）を比較する。
           - 氏名、住所、日付、金額などの重要項目について「一致」「不一致」を判定する。
           - 多少の表記ゆれ（「1-1-1」と「1丁目1番1号」など）は、文脈判断で「一致」としてよいが、その理由は明記すること。
           - 有効期限切れや、必須項目の欠落がないかチェックする。
        3. **行動**: 結果を指定されたJSONフォーマット（DocumentAnalysisResult）で出力する。

        ### 3. 出力要件
        - 結論ファーストで、不備がある場合は `alerts` にリストアップすること。
        - 総合判定 (`overall_status`) は、一切の疑義がなければ "APPROVED"、軽微な確認事項があれば "WARNING"、書類違い等は "REJECTED" とすること。
        """

    def analyze_document(
        self, file_bytes: bytes, mime_type: str, kintone_data: Dict[str, Any]
    ) -> DocumentAnalysisResult:
        import base64

        img_b64 = base64.b64encode(file_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{img_b64}"

        system_instruction = self._build_verification_prompt(kintone_data)

        try:
            structured_llm = self.llm.with_structured_output(DocumentAnalysisResult)
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": system_instruction},
                        {"type": "image_url", "image_url": image_url},
                    ]
                )
            ]
            logger.info("🚀 Invoking AI Agent for reasoning...")
            return structured_llm.invoke(messages)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise e
