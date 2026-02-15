# src/chains/bank_procedure_chain.py

import logging
from typing import Any, Dict, Optional

import pandas as pd
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from legal_system.core.ai_factory import AIFactory

logger = logging.getLogger(__name__)


class BankMasterRetriever:
    """
    銀行マスタCSVから特定の銀行情報を検索するクラス
    """

    def __init__(self, csv_path: str):
        try:
            # CSV読み込み。文字化け防止のためencoding指定推奨（状況に合わせて cp932 or utf-8）
            self.df = pd.read_csv(csv_path, encoding="utf-8")
            # 銀行名の揺らぎ吸収のため空白除去
            self.df["銀行名"] = self.df["銀行名"].astype(str).str.strip()
        except FileNotFoundError:
            logger.error(f"銀行マスタファイルが見つかりません: {csv_path}")
            # エラー時も動作するように空のDataFrameを作成
            self.df = pd.DataFrame(
                columns=[
                    "銀行名",
                    "印鑑証明期限",
                    "代理人本人確認書類",
                    "振込ルール",
                    "備考",
                ]
            )
        except Exception as e:
            logger.error(f"CSV読み込みエラー: {e}")
            self.df = pd.DataFrame()

    def get_bank_info(self, query: str) -> Optional[Dict[str, Any]]:
        """
        ユーザーの質問文から対象銀行を特定し、マスタ情報を辞書形式で返す
        """
        if not query or self.df.empty:
            return None

        # 単純なキーワードマッチング（実務ではより高度なEntity抽出も検討可）
        for bank_name in self.df["銀行名"]:
            if bank_name in query:
                try:
                    row = self.df[self.df["銀行名"] == bank_name].iloc[0]
                    return row.fillna("特になし").to_dict()
                except IndexError:
                    continue
        return None


def create_inheritance_chain(
    rules_path: str = "data/company_rules.txt",  # パスは環境に合わせて調整してください
    master_path: str = "data/bank_master.csv",
):
    """
    相続手続きRAGチェーンを作成して返す関数
    """

    # 1. 共通ルールの読み込み
    try:
        loader = TextLoader(rules_path, encoding="utf-8")
        docs = loader.load()
        general_rules = "\n".join([d.page_content for d in docs])
    except Exception as e:
        logger.warning(f"共通ルールファイル読み込み失敗: {e}")
        general_rules = "（共通ルール読み込みエラー）"

    # 2. マスタ検索インスタンス
    master_retriever = BankMasterRetriever(master_path)

    # 3. LLMの初期化 (Factory経由でキーローテーション)
    llm = AIFactory.create_model(temperature=0.0)

    # 4. プロンプト定義
    # ここで「ゆうちょ」等の他行ルールを除外する強い指示を与えます
    template_str = """
    あなたは行政書士法人の実務支援AIです。
    ユーザーの質問に対し、以下の情報源を組み合わせて回答を作成してください。

    【情報源の優先順位】
    1. **対象銀行マスタ情報 (最優先)**: 期限や支払方法は必ずこれに従うこと。
    2. **共通業務ルール**: マスタに記載がない事項について参照すること。

    【対象銀行マスタ情報】
    {specific_rules}

    【共通業務ルール（参考）】
    {general_rules}

    【回答作成の厳格なルール】
    1. **対象銀行の特定**: 今回の手続き対象は「{target_bank_name}」です。
    2. **情報の除外**: 共通ルール内に含まれる**「{target_bank_name}」以外の銀行（特にゆうちょ銀行など）に関する記述は完全に無視**してください。
       - 例: 対象が「みずほ銀行」の場合、ゆうちょ銀行の「スプレッドシート」や「会社通帳からの引落とし」の記述は絶対に回答に含めないでください。
    3. **支払方法**: マスタ情報の「振込/引落」に従ってください。
       - 「振込」の場合 → 「経理へ依頼（Kintone経理アプリ）」と案内。
       - 「引落」の場合 → 指定された管理シート等を案内。
    4. **証明書の期限**: マスタ情報の「印鑑証明期限」を正として回答してください（共通ルールの6ヶ月という記述で上書きしないこと）。

    【出力フォーマット】
    - 結論のみを箇条書きで記載。
    - 挨拶や前置きは不要。
    
    質問: {question}
    """

    prompt = ChatPromptTemplate.from_template(template_str)

    # 5. チェーン実行用関数
    def run_chain(inputs: Dict[str, Any]) -> str:
        question = inputs.get("question", "")

        # 銀行情報の取得
        bank_info = master_retriever.get_bank_info(question)

        if bank_info:
            target_bank_name = bank_info.get("銀行名", "指定なし")
            # マスタ情報を文字列化してプロンプトに埋め込む
            specific_rules_str = (
                f"- 銀行名: {target_bank_name}\n"
                f"- 印鑑証明期限: {bank_info.get('印鑑証明期限', '規定なし')}\n"
                f"- 本人確認書類: {bank_info.get('代理人本人確認書類', '規定なし')}\n"
                f"- 支払方法(振込/引落): {bank_info.get('振込ルール', '規定なし')}\n"
                f"- 備考: {bank_info.get('備考', '')}"
            )
        else:
            target_bank_name = "特定できない銀行"
            specific_rules_str = (
                "（マスタに該当する銀行が見つかりません。共通ルールのみを参照します）"
            )

        # チェーン構築
        chain = prompt | llm | StrOutputParser()

        try:
            return chain.invoke(
                {
                    "general_rules": general_rules,
                    "specific_rules": specific_rules_str,
                    "target_bank_name": target_bank_name,
                    "question": question,
                }
            )
        except Exception as e:
            logger.error(f"チェーン実行エラー: {e}")
            return "システムエラーが発生しました。"

    return run_chain
