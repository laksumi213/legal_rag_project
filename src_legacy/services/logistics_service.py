# src/services/logistics_service.py

import urllib.parse
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
        
        # Googleマップ用に出発地をURLエンコードしておく (スペース等は削除)
        clean_origin = origin_address.replace(" ", "").replace("　", "")
        origin_enc = urllib.parse.quote(clean_origin)

        # ★修正: URL形式を標準化し、文字化け対策を追加
        system_prompt = f"""
        あなたは、日本の公証実務に精通したロジスティクスAIです。
        ユーザーから提供された住所（{clean_origin}）を起点として、アクセスが良く**実在する**「公証役場」を2〜3箇所選定し、提案してください。

        【重要：情報の正確性と出力形式】
        1. **出典の厳守**:
           - 「日本公証人連合会」の公式リスト (https://www.koshonin.gr.jp/list) に掲載されている公証役場のみを提案してください。
           - 「我孫子」「流山」など、実在しない役場は絶対に提案しないでください。

        2. **文字化け・ハルシネーション防止**:
           - 住所や名称は正確に記述してください。
           - **不自然な記号の羅列（例: ॒॒॒॒...）や、無意味な空白の繰り返しは厳禁**です。標準的な日本語のみを使用してください。

        3. **地図リンクの生成**:
           - 以下のGoogleマップ公式パラメータ形式を使用してください。
           - 形式: `https://www.google.com/maps/dir/?api=1&origin={origin_enc}&destination=[公証役場の住所]`
           - destinationには、抽出した「公証役場の住所」をそのまま入れてください。

        【出力フォーマット】
        --------------------------------------------------
        ### 1. [公証役場名]
        - **住所**: [郵便番号] [都道府県市区町村...]
        - **最寄り駅**: [駅名] (徒歩〇分)
        - **アクセス**: [出発地からの移動ルート概要]
        - **地図**: [Googleマップでルートを見る](https://www.google.com/maps/dir/?api=1&origin={origin_enc}&destination=[公証役場の住所])
        --------------------------------------------------
        (これを2〜3件繰り返す)

        【選定理由】
        （なぜここを選んだかの理由）

        【注意点】
        （管轄や予約の必要性など）
        """

        user_message = f"検索起点: {clean_origin}"

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"input": user_message})
            
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            return f"AI検索エラーが発生しました: {e}"