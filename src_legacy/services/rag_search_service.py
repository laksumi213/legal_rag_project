# src/services/rag_search_service.py
import os
from typing import List, Dict
from sqlalchemy import and_, or_
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_chroma import Chroma

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
        self.embeddings = AIFactory.get_embeddings()
        self.vector_store = AIFactory.get_vector_store()
        self.synonym_map = {
            "残証": "残高証明書",
            "戸籍": "戸籍謄本",
            "除籍": "除籍謄本",
        }


    def semantic_search_will_documents(self, query: str) -> str:
        """
        ChromaDBにインデックス化された遺言書ドキュメントに対してセマンティック検索を実行し、
        RAGによって質問に回答する。
        """
        retriever = self.vector_store.as_retriever()

        prompt = ChatPromptTemplate.from_messages([
            ("system", "あなたは行政書士事務所のアシスタントです。以下の提供されたコンテキスト情報のみに基づいて、ユーザーの遺言書に関する質問に答えてください。情報がない場合は「提供された情報からは回答できません」と答えてください。不正確な情報は生成しないでください。\n\n{context}"),
            ("human", "{question}"),
        ])

        rag_chain = (
            {"context": retriever | RunnableLambda(lambda docs: "\n\n".join([doc.page_content for doc in docs])), "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return rag_chain.invoke(query)

    def search_bank_rules(self, query: str) -> str:
        """
        銀行マスタ・規定（JSON/CSV）から手続き情報を回答する (Gemini RAG)
        """
        session = self.db._get_session()

        try:
            keywords = query.split()
            
            # クエリキーワードのいずれかを含む銀行をすべて候補とする
            bank_filters = [BankMaster.bank_name.ilike(f"%{k}%") for k in keywords]
            banks = session.query(BankMaster).filter(or_(*bank_filters)).all()
            
            context_text = ""
            if not banks:
                # 銀行が見つからなくても、LLMに回答を生成させてみる
                context_text = "関連する銀行の情報はデータベースにありません。"

            for b in banks:
                context_text += f"""
                【銀行名: {b.bank_name}】
                - 印鑑証明期限: {b.seal_cert_limit}
                - 本人確認: {b.id_verify_rule}
                - 備考: {b.remarks}
                """
            
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
            keywords = query.split()
            base_query = session.query(FileRegistry)
            
            and_conditions = []
            for k in keywords:
                # キーワード自体と、それが省略語であれば正式名称も検索対象に加える
                search_terms = {k}
                if k in self.synonym_map:
                    search_terms.add(self.synonym_map[k])
                
                or_conditions = []
                for term in search_terms:
                    like_term = f"%{term}%"
                    or_conditions.append(FileRegistry.filename.ilike(like_term))
                    or_conditions.append(FileRegistry.doc_type.ilike(like_term))
                
                and_conditions.append(or_(*or_conditions))

            if and_conditions:
                base_query = base_query.filter(and_(*and_conditions))

            results = base_query.order_by(FileRegistry.registered_at.desc()).limit(10).all()
            
            return [
                {
                    "filename": f.filename,
                    "doc_type": f.doc_type,
                    "case_id": f.case_id,
                    "registered_at": f.registered_at.strftime("%Y-%m-%d"),
                    "file_hash": f.file_hash
                }
                for f in results
            ]
        finally:
            session.close()
