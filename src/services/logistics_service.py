# src/services/logistics_service.py

from datetime import datetime
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from legal_system.core.ai_factory import AIFactory

class LogisticsService:
    """
    公証役場へのアクセスや選定アドバイスを行うAIサービス
    """
    def __init__(self):
        # 事実性を重視するため temperature=0.0
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def consult_nearest_notaries(self, origin_address: str) -> str:
        """
        指定された住所に基づき、アクセスの良い公証役場を提案する
        """
        today_str = datetime.now().strftime("%Y-%m-%d")

        # ★ここが「Gem」の中身に相当します
        # ユーザー様が検証された「高精度ファクトベースAI」のプロンプトを適用
        system_prompt = f"""
        あなたは、信頼性の高い情報を提示できる高精度なファクトベースAIです。
        ユーザーから提供された住所（{origin_address}）を起点として、アクセスが良く信頼性の高い「公証役場」を2〜3箇所選定し、提案してください。

        【厳守ルール】
        1. わからない/未確認は「わからない」と明言すること。無理な推測は禁止。
        2. 推測を含む場合は「推測ですが」と明示すること。
        3. 現在日付（{today_str} JST）を認識し、回答に明記すること。
        4. 根拠/出典（公証人連合会や法務局の管轄情報など）を可能な限り添付すること。
        5. 専門的知見が必要な場合は「専門家に確認」と明記すること。
        
        【出力フォーマット】
        ご提示いただいた住所（{origin_address}）に基づき...

        【結論】
        （推奨する公証役場リスト：名称、最寄り駅、所要時間目安）

        【根拠】
        （移動ルートの詳細、なぜそこが便利なのかの理由）

        【注意点・例外】
        （管轄の問題や、出張作成時の注意点など）

        【出典】
        （参照した情報源）

        【確実性: 高/中/低】
        """

        user_message = f"検索対象の住所: {origin_address}"

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}")
            ])
            
            chain = prompt | self.llm
            # inputにも住所を渡していますが、system_prompt内にも埋め込んで強化しています
            response = chain.invoke({"input": user_message})
            
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            return f"AI検索エラーが発生しました: {e}"