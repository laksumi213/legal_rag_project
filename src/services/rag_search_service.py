# src/services/rag_search_service.py
import os
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import FileRegistry, BankMaster

class RagSearchService:
    """
    銀行手続き・過去ドキュメント検索サービス
    """
    def __init__(self):
        self.db = DatabaseManager()
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def search_bank_rules(self, query: str) -> str:
        """
        銀行マスタ・規定（JSON/CSV）から手続き情報を回答する (Gemini RAG)
        """
        # 簡易実装: BankMasterテーブルの remarks や JSONルールを検索
        # 本来はVectorStoreを使うが、ここではSQLのLIKE検索とLLM回答生成を組み合わせる例
        session = self.db._get_session()
        try:
            # 1. キーワードに関連する銀行を特定
            banks = session.query(BankMaster).filter(BankMaster.bank_name.contains(query)).all()
            
            context_text = ""
            for b in banks:
                context_text += f"""
                【銀行名: {b.bank_name}】
                - 印鑑証明期限: {b.seal_cert_limit}
                - 本人確認: {b.id_verify_rule}
                - 備考: {b.remarks}
                """
            
            # 2. LLMで回答生成
            prompt = ChatPromptTemplate.from_template("""
            あなたは行政書士事務所のアシスタントです。
            以下の銀行データベース情報を基に、ユーザーの質問に答えてください。
            情報がない場合は「データベースに登録がありません」と答えてください。

            【データベース情報】
            {context}

            質問: {question}
            """)
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({"context": context_text, "question": query})
            
        finally:
            session.close()

    def search_past_documents(self, query: str) -> List[Dict]:
        """
        過去の提出書類（個人情報含む）をメタデータ検索する
        ※ セキュリティのため、AIには中身を渡さず、ファイル名と種別で検索してヒットさせる
        """
        session = self.db._get_session()
        try:
            # ファイル名、銀行名、書類種別で検索
            # 例: "三菱UFJ 残高証明" -> 三菱UFJの残高証明ファイルを検索
            keywords = query.split()
            base_query = session.query(FileRegistry)
            
            for k in keywords:
                term = f"%{k}%"
                base_query = base_query.filter(
                    (FileRegistry.filename.ilike(term)) | 
                    (FileRegistry.doc_type.ilike(term))
                )
            
            results = base_query.order_by(FileRegistry.registered_at.desc()).limit(10).all()
            
            return [
                {
                    "filename": f.filename,
                    "doc_type": f.doc_type,
                    "case_id": f.case_id,
                    "registered_at": f.registered_at.strftime('%Y-%m-%d'),
                    # 実際のパスは隠蔽し、ダウンロード時に解決
                    "file_hash": f.file_hash 
                }
                for f in results
            ]
        finally:
            session.close()