This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.streamlit/
  config.toml
data/
  db/
    chroma/
      local_rag_db/
        d50e1e10-53e2-4aea-ac5d-95f27e67e86d/
          data_level0.bin
          header.bin
          length.bin
          link_lists.bin
        chroma.sqlite3
      .keep
    sql/
      .keep
      legal_system.db
  fonts/
    ipaexg.ttf
  rules/
    bank_master.csv
    company_rules.md
  templates/
    .keep
  legal_system.db
src/
  chains/
    bank_procedure_chain.py
  legal_system/
    core/
      __init__.py
      ai_factory.py
      config.py
      data_sync.py
      database_manager.py
      engines.py
      ocr_engine.py
    models/
      __init__.py
      base.py
      tables.py
    tools/
      __init__.py
      coord_tool.py
    ui/
      pages/
        01_銀行手続要件_確認フォーム.py
        02_相続書類_作成フォーム.py
        99_預貯金口座入力フォーム.py
      __init__.py
      Home.py
    __init__.py
    main.py
  legal.egg-info/
    dependency_links.txt
    PKG-INFO
    requires.txt
    SOURCES.txt
    top_level.txt
  __init__.py
.gitignore
.python-version
bank_master.json
create_rule_master.py
export_code.py
pyproject.toml
README.md
register_existing_templates.py
requirements-dev.lock
requirements.lock
requirements.txt
run_watcher.py
update_bank_master.py
```

# Files

## File: .streamlit/config.toml
```toml
[theme]
# ベースとなるテーマ（"light" または "dark"）
base = "light"

# メインのアクセントカラー（ボタンなど）
primaryColor = "#d33682"

# 背景色
backgroundColor = "#ffffff"

# サイドバーなどの背景色
secondaryBackgroundColor = "#f0f2f6"

# 文字色
textColor = "#262730"

# フォント
font = "sans serif"
```

## File: src/chains/bank_procedure_chain.py
```python
# src/chains/bank_procedure_chain.py

import logging
from typing import Any, Dict, Optional

import pandas as pd
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.ai_factory import AIFactory

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
```

## File: src/legal_system/core/engines.py
```python
# src/legal_system/core/engines.py

import gzip
import os
import time
from typing import Optional

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Google Gemini / LangChain 関連
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 設定読み込み
from src.legal_system.core.config import Config, KeyManager


class BankRepository:
    """
    銀行マスタCSVの読み込みと検索を担当
    """

    def __init__(self, csv_path: str):
        # CSV読み込み時も圧縮やエンコーディングの問題を回避するロジックを使用
        self.df = self._load_csv_safe(csv_path)

    def _load_csv_safe(self, path: str) -> pd.DataFrame:
        """CSVファイルを安全に読み込む（GZIP対応 / エンコーディング自動判別）"""
        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            # GZIP判定
            is_gzipped = False
            with open(path, "rb") as f:
                header = f.read(2)
                if header == b"\x1f\x8b":
                    is_gzipped = True

            # Pandasで読み込み
            if is_gzipped:
                try:
                    return pd.read_csv(
                        path, compression="gzip", encoding="utf-8"
                    ).fillna("")
                except UnicodeDecodeError:
                    return pd.read_csv(
                        path, compression="gzip", encoding="cp932"
                    ).fillna("")
            else:
                try:
                    return pd.read_csv(path, encoding="utf-8").fillna("")
                except UnicodeDecodeError:
                    return pd.read_csv(path, encoding="cp932").fillna("")

        except Exception as e:
            print(f"CSV読み込み警告: {e}")
            return pd.DataFrame()  # エラー時は空のDFを返す

    def search(self, query: str) -> Optional[dict]:
        """クエリ内の銀行名を特定し、行データを辞書として返す"""
        if self.df.empty:
            return None

        for _, row in self.df.iterrows():
            bank_name = str(row.get("銀行名", ""))
            if bank_name and bank_name in query:
                return row.to_dict()
        return None

    def format_rule(self, row: dict) -> str:
        """LLMへの注入用にフォーマット"""
        return f"""
        【特定された銀行の必須ルール (最優先適用)】
        - 銀行名: {row.get("銀行名")}
        - 印鑑証明期限: {row.get("印鑑証明期限")}
        - 代理人本人確認: {row.get("代理人本人確認書類")}
        - 手数料支払: {row.get("振込ルール")}
        - 備考: {row.get("備考")}
        """


class RAGEngine:
    """
    Google Gemini + キーローテーション対応エンジン
    ファイルのGZIP圧縮/文字コードズレを自動吸収する機能付き
    """

    def __init__(self, rules_path: str, bank_repo: BankRepository):
        self.bank_repo = bank_repo
        self.rules_path = rules_path
        self.vector_store = None  # 遅延初期化
        self.embeddings = None
        self.llm = None

        # 初回のクライアント構築
        self._refresh_client()

    def _refresh_client(self):
        """APIキーを取得してクライアントを再生成"""
        try:
            new_key = KeyManager.get_next_key()

            # Embeddingsモデル更新
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=Config.EMBEDDING_MODEL, google_api_key=new_key
            )

            # LLMモデル更新
            self.llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                google_api_key=new_key,
                convert_system_message_to_human=True,
            )

            # ベクトルストア構築（または更新）
            if self.vector_store is None:
                self.vector_store = self._build_vector_store(self.rules_path)
            else:
                self.vector_store.embeddings = self.embeddings

        except Exception as e:
            print(f"クライアント初期化エラー: {e}")
            # エラー発生時もNoneのままにしておき、ask時に再トライさせるかエラーを返す

    def _read_file_safe(self, path: str) -> str:
        """
        ファイルを安全に読み込むヘルパー関数
        - GZIP圧縮されていれば自動解凍
        - UTF-8 で失敗したら CP932 (Shift-JIS) を試行
        """
        if not os.path.exists(path):
            return ""

        content_bytes = b""

        # 1. バイナリとして読み込み、GZIPヘッダー(1f 8b)をチェック
        with open(path, "rb") as f:
            raw_data = f.read()
            if raw_data.startswith(b"\x1f\x8b"):
                # GZIP解凍
                content_bytes = gzip.decompress(raw_data)
            else:
                content_bytes = raw_data

        # 2. 文字コード判別 (utf-8 -> cp932)
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content_bytes.decode("cp932")
            except UnicodeDecodeError:
                # それでもだめならエラー無視で強引に読む
                return content_bytes.decode("utf-8", errors="ignore")

    def _build_vector_store(self, path: str) -> FAISS:
        """ベクトルストア構築"""
        # 安全な読み込み関数を使用
        text = self._read_file_safe(path)

        if not text:
            # ファイルが空、または読めない場合はダミーデータで落ちないようにする
            text = "共通ルールファイルが読み込めませんでした。"

        headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
        docs = splitter.split_text(text)

        if not docs:
            # 分割結果が空の場合のガード
            from langchain_core.documents import Document

            docs = [Document(page_content="ルール情報なし")]

        return FAISS.from_documents(docs, self.embeddings)

    def ask(self, user_query: str, retry_count=0) -> str:
        """質問への回答（自動リトライ機能付き）"""
        if not self.llm:
            return "AIエンジンの初期化に失敗しています。APIキー設定を確認してください。"

        try:
            return self._execute_chain(user_query)
        except Exception as e:
            error_msg = str(e)
            # 429 (Resource Exhausted) などのエラー判定
            if "429" in error_msg or "Resource has been exhausted" in error_msg:
                if retry_count < 3:
                    print(
                        f"⚠️ API制限検知。キーを切り替えてリトライします... ({retry_count + 1}/3)"
                    )
                    self._refresh_client()
                    time.sleep(1)
                    return self.ask(user_query, retry_count + 1)

            return f"エラーが発生しました: {error_msg}"

    def _execute_chain(self, user_query: str) -> str:
        """実際のChain実行処理"""
        # STEP 1: CSV検索
        bank_data = self.bank_repo.search(user_query)
        bank_context = ""
        if bank_data:
            bank_context = self.bank_repo.format_rule(bank_data)

        # STEP 2: ベクトル検索
        enhanced_query = f"{user_query} 代理人 行政書士 手続き"
        docs = self.vector_store.similarity_search(enhanced_query, k=4)
        rule_context = "\n\n".join([d.page_content for d in docs])

        # STEP 3: プロンプト構築
        system_prompt = """
        あなたは行政書士法人の実務支援AIです。
        
        # 行動指針
        1. **結論ファースト**: 挨拶不要。箇条書きで簡潔に答える。
        2. **代理人視点**: 「行政書士（代理人）」の手続きのみ回答する。
        3. **優先順位**: 【銀行別ルール】を最優先する。
        4. **リンク表示**: ゆうちょ銀行や参照ファイルの指示がある場合はURLを表示する。
        
        # 参照情報
        ## 共通業務ルール
        {rule_context}
        
        ## 銀行別ルール (Override)
        {bank_context}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{question}")]
        )

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke(
            {
                "rule_context": rule_context,
                "bank_context": bank_context,
                "question": user_query,
            }
        )
```

## File: src/legal_system/ui/pages/01_銀行手続要件_確認フォーム.py
```python
import json
import os
import sys
from typing import Any, Dict, List, Optional

import streamlit as st

# --- パス解決 (srcフォルダへのパスを通す) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.append(SRC_DIR)

# 定数設定 (プロジェクトルート直下の data/bank_master.json)
DATA_FILE = os.path.join(ROOT_DIR, "bank_master.json")

# ページ設定
st.set_page_config(
    page_title="銀行手続要件確認 | 相続業務支援システム", page_icon="🏦", layout="wide"
)


def load_bank_master() -> List[Dict[str, Any]]:
    """銀行マスタJSONを読み込む"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error("データの形式が不正です。管理者に連絡してください。")
        return []


def display_agent_warning() -> None:
    """行政書士補助者向けの注意喚起"""
    st.warning(
        "【重要】この画面は「行政書士が代理人として行う場合」の要件を表示しています。\n"
        "相続人本人が窓口に行く場合とは必要書類が異なるため、必ず委任状の要件を確認してください。",
        icon="⚠️",
    )


def main() -> None:
    st.title("🏦 銀行手続要件・必要書類確認")
    st.caption("各銀行の「代理人手続き」に関する特記事項を確認します。")

    display_agent_warning()

    # データのロード
    banks: List[Dict[str, Any]] = load_bank_master()

    if not banks:
        st.error(
            f"⚠️ 銀行データファイル（bank_master.json）が見つかりません。\n"
            f"参照パス: {DATA_FILE}\n\n"
            "以下の手順を実行してください：\n"
            "1. プロジェクトルートで `python update_bank_master.py` を実行"
        )
        return

    # 銀行選択セレクトボックス
    bank_names: List[str] = [b["bank_name"] for b in banks]
    selected_bank_name: Optional[str] = st.selectbox(
        "確認したい金融機関を選択してください",
        options=bank_names,
        index=None,
        placeholder="銀行を選択...",
    )

    if selected_bank_name:
        # 選択された銀行データを取得
        selected_data: Optional[Dict[str, Any]] = next(
            (b for b in banks if b["bank_name"] == selected_bank_name), None
        )

        if selected_data:
            st.divider()

            # メイン情報の表示
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"📂 {selected_data['bank_name']} の手続要件")
                st.info(f"区分: {selected_data.get('procedure_type', '不明')}")

                st.markdown("#### 📄 必要書類リスト")
                for doc in selected_data.get("required_documents", []):
                    # 代理人特有の書類は太字で強調
                    if "委任状" in doc or "印鑑証明" in doc or "行政書士" in doc:
                        st.markdown(f"- **{doc}** 👈 Check")
                    else:
                        st.markdown(f"- {doc}")

            with col2:
                st.markdown("#### 💡 代理人特記事項")
                st.caption(selected_data.get("notes", "特記事項なし"))

                st.markdown("#### ↩️ 原本還付の方針")
                st.success(selected_data.get("original_return_policy", "要確認"))

            # 補助者向けのアクションガイド
            st.divider()
            st.markdown("### 👩‍💼 補助者アクション")

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                st.info("書類作成へ進みますか？")
                if st.button(f"➡️ {selected_bank_name}用 書類作成画面へ"):
                    st.switch_page("pages/02_相続書類_作成.py")

            with c_act2:
                st.info("支店コードを調べますか？")
                if st.button("➡️ 支店検索・口座入力画面へ"):
                    st.switch_page("pages/99_口座情報_入力.py")


if __name__ == "__main__":
    main()
```

## File: src/legal_system/ui/pages/02_相続書類_作成フォーム.py
```python
import os
import sys
from io import BytesIO

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# --- パス解決 ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.append(SRC_DIR)

# DBモジュールのインポート
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case

# ページ設定
st.set_page_config(
    page_title="相続書類作成 | 相続業務支援システム", page_icon="📄", layout="wide"
)

# フォント登録
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass


def main():
    st.title("🖨️ 書類自動作成")

    # DB接続
    db = DatabaseManager()
    session = db._get_session()

    # ---------------------------------------------------------
    # 1. 案件選択 (セッション連携機能付き)
    # ---------------------------------------------------------
    try:
        cases = session.query(Case).all()
    except Exception as e:
        st.error(f"DBエラー: {e}")
        return

    if not cases:
        st.warning("⚠️ 案件データが1件もありません。")
        st.info(
            "まずはサイドバーの「99_口座情報_入力」から、案件(G番号)と口座情報を登録してください。"
        )
        return

    # 選択肢リスト作成
    # key: 表示名 (例: "G0001: 山田太郎"), value: case_id (DBのID)
    case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
    options_keys = list(case_options.keys())

    # --- セッションから前回の選択状態を復元 ---
    default_index = 0
    if "current_case_id" in st.session_state:
        # 保存されているIDを持つ選択肢を探す
        current_id = st.session_state["current_case_id"]
        for i, key in enumerate(options_keys):
            if case_options[key] == current_id:
                default_index = i
                break

    # セレクトボックス表示
    selected_label = st.selectbox(
        "📂 作業対象の案件を選択",
        options=options_keys,
        index=default_index,
        key="case_selector",
    )

    # 選択されたらセッションに保存（他の画面でも使えるようにする）
    if selected_label:
        selected_case_id = case_options[selected_label]
        st.session_state["current_case_id"] = selected_case_id

        # 案件オブジェクトの取得
        target_case = session.query(Case).filter_by(case_id=selected_case_id).first()

        # 被相続人情報の表示
        deceased_name = (
            target_case.deceased_ref.name_last if target_case.deceased_ref else "未登録"
        )
        st.caption(f"被相続人: {deceased_name} 様 の手続き書類を作成します。")

    # ---------------------------------------------------------
    # 2. 提出先銀行の選択
    # ---------------------------------------------------------
    # この案件に紐付いている資産(FinancialAsset)を取得
    assets = target_case.financial_assets
    if not assets:
        st.warning(
            f"⚠️ 案件 {target_case.case_number} には口座情報が登録されていません。"
        )
        if st.button("➡️ 口座入力画面へ移動して登録する"):
            st.switch_page("pages/99_口座情報_入力.py")
        return

    # 銀行単位でまとめる
    bank_asset_map = {}
    for asset in assets:
        b_name = asset.bank_ref.bank_name if asset.bank_ref else "不明な銀行"
        if b_name not in bank_asset_map:
            bank_asset_map[b_name] = []
        bank_asset_map[b_name].append(asset)

    st.divider()
    selected_bank_name = st.radio(
        "提出先の金融機関", list(bank_asset_map.keys()), horizontal=True
    )

    if not selected_bank_name:
        return

    # 対象口座の確認表示
    target_assets = bank_asset_map[selected_bank_name]
    with st.expander(
        f"確認: {selected_bank_name} の対象口座 ({len(target_assets)}件)",
        expanded=False,
    ):
        for a in target_assets:
            br = a.branch_ref.branch_name if a.branch_ref else "支店不明"
            num = a.account_number if a.account_number else "番号不明"
            atype = a.account_type_ref.type_name if a.account_type_ref else ""
            st.text(f"・{br} {atype} {num}")

    # ---------------------------------------------------------
    # 3. 書類雛形の選択
    # ---------------------------------------------------------
    files = db.get_all_files()
    if not files:
        st.error("雛形ファイルがありません。管理者に連絡してください。")
        return

    # テンプレートPDFのみをフィルタリング
    file_opts = {f["filename"]: f["hash"] for f in files}

    st.divider()
    col_temp, col_btn = st.columns([3, 1])

    with col_temp:
        selected_file_name = st.selectbox(
            "使用するテンプレート", list(file_opts.keys())
        )

    with col_btn:
        st.write("")  # スペース調整
        st.write("")
        if st.button("🚀 PDF作成", type="primary", use_container_width=True):
            # --- PDF生成ロジック (変更なし) ---
            file_hash = file_opts[selected_file_name]
            deceased = target_case.deceased_ref

            data_map = {
                "{case_number}": target_case.case_number,
                "{deceased_name}": f"{deceased.name_last} {deceased.name_first}"
                if deceased
                else "",
                "{death_date}": str(deceased.date_of_death)
                if deceased and deceased.date_of_death
                else "",
                "{bank_name}": selected_bank_name,
            }

            for i, asset in enumerate(target_assets):
                idx = i + 1
                br_name = asset.branch_ref.branch_name if asset.branch_ref else ""
                ac_type = (
                    asset.account_type_ref.type_name if asset.account_type_ref else ""
                )
                ac_num = asset.account_number
                data_map[f"{{branch_{idx}}}"] = br_name
                data_map[f"{{type_{idx}}}"] = ac_type
                data_map[f"{{number_{idx}}}"] = ac_num

            try:
                coords = db.get_coordinates_by_hash(file_hash)

                TEMPLATE_DIR = os.path.join(ROOT_DIR, "data", "templates")
                template_path = os.path.join(TEMPLATE_DIR, selected_file_name)

                if not os.path.exists(template_path):
                    st.error(f"ファイルが見つかりません: {template_path}")
                    return

                output = PdfWriter()
                input_pdf = PdfReader(template_path)

                for i, page in enumerate(input_pdf.pages):
                    page_num = i + 1
                    page_coords = [c for c in coords if c["page"] == page_num]

                    if page_coords:
                        packet = BytesIO()
                        width = float(page.mediabox.width)
                        height = float(page.mediabox.height)
                        can = canvas.Canvas(packet, pagesize=(width, height))

                        for c in page_coords:
                            print_text = c["value"]
                            if str(print_text).startswith("{") and str(
                                print_text
                            ).endswith("}"):
                                if print_text in data_map:
                                    print_text = data_map[print_text]

                            font_name = (
                                "IPAexG" if os.path.exists(FONT_PATH) else "Helvetica"
                            )
                            can.setFont(font_name, c["font_size"])
                            if c["color"] == "red":
                                can.setFillColorRGB(1, 0, 0)
                            else:
                                can.setFillColorRGB(0, 0, 0)

                            # Y座標補正
                            can.drawString(
                                c["x"], float(height) - c["y"], str(print_text)
                            )

                        can.save()
                        packet.seek(0)
                        overlay = PdfReader(packet)
                        page.merge_page(overlay.pages[0])

                    output.add_page(page)

                out_stream = BytesIO()
                output.write(out_stream)

                st.success(f"作成完了: {selected_file_name}")
                st.download_button(
                    label="📥 PDFダウンロード",
                    data=out_stream,
                    file_name=f"作成済_{target_case.client_name}_{selected_bank_name}.pdf",
                    mime="application/pdf",
                )

            except Exception as e:
                st.error(f"作成エラー: {e}")
            finally:
                session.close()


if __name__ == "__main__":
    main()
```

## File: src/legal_system/ui/pages/99_預貯金口座入力フォーム.py
```python
import json
import os
import sys

import streamlit as st

# --- パス解決 ---
# このファイルの場所: src/legal_system/ui/pages/99_預貯金口座入力フォーム.py
# ROOT_DIR: プロジェクトルート
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    AccountTypeMaster,
    BankMaster,
    BranchMaster,
    Case,
    FinancialAsset,
)

# --- Zengin-Code のローカルキャッシュパス ---
DATA_DIR = os.path.join(ROOT_DIR, "data", "zengin")


# ★修正: キャッシュ(st.cache_data)を削除しました。
# JSONの読み込みは十分に高速であり、ファイル更新を即座に反映させるためです。
def get_bank_master():
    """ローカルのJSONファイルから銀行マスタ(Zengin)を読み込む"""
    json_path = os.path.join(DATA_DIR, "banks.json")

    # デバッグ用: パスが合っているか確認したい場合は以下のコメントを外す
    # print(f"Looking for banks at: {json_path}")

    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading banks.json: {e}")
        return {}


# ★修正: こちらもキャッシュを削除、またはTTLを設定
def get_branch_master(bank_code):
    """ローカルのJSONファイルから支店マスタを読み込む"""
    json_path = os.path.join(DATA_DIR, "branches", f"{bank_code}.json")
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def ensure_master_records(
    session, bank_name, bank_code, branch_name, branch_code, type_name
):
    """マスタテーブルに存在しなければ作成するヘルパー関数"""
    # 1. 銀行マスタ
    bank = session.query(BankMaster).filter_by(bank_code=bank_code).first()
    if not bank:
        bank = BankMaster(bank_name=bank_name, bank_code=bank_code)
        session.add(bank)
        session.flush()

    # 2. 支店マスタ
    branch = None
    if branch_code:
        branch = (
            session.query(BranchMaster)
            .filter_by(bank_id=bank.id, branch_code=branch_code)
            .first()
        )
        if not branch:
            branch = BranchMaster(
                bank_id=bank.id, branch_name=branch_name, branch_code=branch_code
            )
            session.add(branch)
            session.flush()

    # 3. 口座種別マスタ
    ac_type = session.query(AccountTypeMaster).filter_by(type_name=type_name).first()
    if not ac_type:
        ac_type = AccountTypeMaster(type_name=type_name)
        session.add(ac_type)
        session.flush()

    return bank, branch, ac_type


def main():
    st.set_page_config(page_title="口座情報入力", page_icon="🏦", layout="centered")
    st.title("🏦 預貯金口座 入力ツール")
    st.caption(
        "案件ごとの口座情報を登録します。ここで登録したデータが書類作成に使用されます。"
    )

    # 1. 銀行選択
    banks = get_bank_master()

    if not banks:
        st.error(
            "⚠️ 銀行データ(Zengin)が見つかりません。Home画面の「更新」ボタンを押してください。"
        )
        # デバッグ用にパスを表示
        st.caption(f"参照パス: {os.path.join(DATA_DIR, 'banks.json')}")
        return

    # 銀行リスト作成 (辞書型かリスト型かで処理を分ける)
    if isinstance(banks, dict):
        bank_list = [f"{v['name']} ({k})" for k, v in banks.items()]
    else:
        # 想定外のフォーマットの場合のガード
        bank_list = []

    selected_bank_str = st.selectbox(
        "銀行名", options=[""] + bank_list, placeholder="銀行名を入力または選択..."
    )

    # 2. 支店選択
    selected_branch_str = ""
    bank_code = ""
    bank_name = ""

    if selected_bank_str:
        # 文字列 "三菱UFJ銀行 (0005)" からコードと名前を抽出
        try:
            # 右側の括弧内のコードを取得
            bank_code = selected_bank_str.split("(")[-1].replace(")", "")
            # コード部分を除いた名前を取得
            bank_name = selected_bank_str.replace(f"({bank_code})", "").strip()

            branches = get_branch_master(bank_code)
            if branches:
                branch_list = [f"{v['name']} ({k})" for k, v in branches.items()]
                selected_branch_str = st.selectbox("支店名", options=[""] + branch_list)
            else:
                st.warning("支店データがありません（手入力してください）")
                selected_branch_str = st.text_input("支店名 (手入力)")
        except Exception:
            st.error("銀行名のパースに失敗しました")

    # 3. 口座詳細入力
    c1, c2 = st.columns(2)
    account_type = c1.selectbox("預金種別", ["普通", "定期", "当座", "貯蓄", "その他"])
    account_num = c2.text_input("口座番号 (7桁)", max_chars=7)

    holder_name = st.text_input("口座名義人 (カタカナ)", placeholder="ヤマダ タロウ")

    # 案件番号入力
    case_number = st.text_input(
        "案件番号 (G番号)", value="G0001", help="既存の案件番号を入力してください"
    )

    st.divider()

    if st.button("💾 データを確定する", type="primary"):
        if not (bank_name and case_number):
            st.error("銀行名と案件番号は必須です。")
            return

        # 支店情報のパース
        branch_name = ""
        branch_code = "000"

        if selected_branch_str:
            if "(" in selected_branch_str and ")" in selected_branch_str:
                try:
                    branch_code = selected_branch_str.split("(")[-1].replace(")", "")
                    branch_name = selected_branch_str.replace(
                        f"({branch_code})", ""
                    ).strip()
                except:
                    branch_name = selected_branch_str
            else:
                branch_name = selected_branch_str

        try:
            db = DatabaseManager()
            session = db._get_session()

            # 1. 案件の確保
            case = session.query(Case).filter_by(case_number=case_number).first()
            if not case:
                # 案件がない場合は簡易作成
                case = Case(case_number=case_number, client_name=f"案件{case_number}")
                session.add(case)
                session.flush()

            # 2. マスタの確保
            bank_obj, branch_obj, type_obj = ensure_master_records(
                session, bank_name, bank_code, branch_name, branch_code, account_type
            )

            # 3. 資産データの登録
            new_asset = FinancialAsset(
                case_id=case.case_id,
                bank_id=bank_obj.id,
                branch_id=branch_obj.id if branch_obj else None,
                account_type_id=type_obj.id,
                account_number=account_num,
                status=f"名義:{holder_name}",
            )
            session.add(new_asset)
            session.commit()

            st.success(f"✅ {bank_name} {branch_name} の口座情報を登録しました！")
            # 完了後、セッションを閉じる
            session.close()

        except Exception as e:
            st.error(f"DB保存エラー: {e}")
            return


if __name__ == "__main__":
    main()
```

## File: requirements.txt
```
# 📂 遺言・遺産整理業務支援システム 要件定義書 (Ver 1.0)

## 1. プロジェクト概要
* **目的:** 遺言書作成および遺産整理業務の効率化。
* **コアコンセプト:** 「個人情報の完全オフライン管理」と「生成AIによる業務支援」のハイブリッド構成。
* **利用規模:** 本社20名で開始、将来的には全拠点100名以上（年間1000件規模）。

## 2. 技術スタック選定
以下のライブラリ・ツールを標準とする。

| カテゴリ | 技術名 | 選定理由 |
| :--- | :--- | :--- |
| **言語** | **Python 3.10+** | AI/データ処理のエコシステムが最強であるため。 |
| **アプリFW** | **Streamlit** | 社内Webアプリ化が高速。各PCへのインストール不要。 |
| **DB** | **PostgreSQL** | 100人規模の同時接続・排他制御に耐える堅牢性（無料）。 |
| **ORM** | **SQLAlchemy** | DB操作の抽象化。保守性向上のため必須。 |
| **OCR** | **PaddleOCR** | 金融機関書類（日本語・罫線あり）の認識精度が高いため。 |
| **生成AI** | **Google Gemini API** | マニュアル検索、文書案作成用。(google-generativeai) |
| **PDF処理** | **PyMuPDF (fitz)** | PDFの読み込み、加工用。 |

## 3. システムアーキテクチャ
物理的なデータ保管場所と、外部AIへのデータフローを厳密に分離する。

* **サーバー構成:** オンプレミス（社内）サーバー1台にDockerコンテナ等でDBとアプリをホスト。
* **クライアント:** 社員PCのブラウザからイントラネット経由でアクセス。
* **ネットワーク分離:**
    * **Zone A (Secure/Local):** PostgreSQL, OCR処理, 個人情報（氏名, 口座番号）の保存。インターネットへは出さない。
    * **Zone B (Cloud/AI):** Gemini API。ここには「匿名化されたテキスト」と「マニュアル」のみ送信する。

## 4. 機能要件

### A. 顧客・案件管理機能
* 顧客情報（被相続人、相続人）のCRUD処理。
* PostgreSQLを使用し、排他制御を行う。

### B. 帳票OCR取り込み機能
* Streamlit画面から画像/PDFをアップロード。
* PaddleOCRでテキスト化。
* OCR結果と元画像を並べて表示し、人間が修正してDB保存するUI。

### C. 生成AI支援機能（RAG/Drafting）
* **マスキング処理:** 相談内容をGeminiに投げる前に、正規表現等で個人情報（氏名、住所、電話番号、口座番号）をプレースホルダ（例: `[NAME_A]`, `[BANK_ID]`）に置換するロジックを実装すること。
* **マニュアル検索:** 社内規定や金融機関手続きマニュアルをベクトル化、またはコンテキストとして渡し、質問に回答させる。

### D. バックアップ機能
* `pg_dump` を使用し、毎日深夜にDBのダンプファイルを作成。
* 外部ストレージ（NAS等）への転送スクリプト。

## 5. データベース設計指針（ER図イメージ）
* **usersテーブル:** 社員アカウント管理（権限管理用）。
* **customersテーブル:** 顧客基本情報。
* **mattersテーブル:** 案件情報（遺言作成、遺産整理など）。
* **documentsテーブル:** OCR読み取り結果、生成された文書データ。ファイルパス管理。

## 6. セキュリティ・コンプライアンス規定
* **原則:** 顧客のPII（個人特定情報）は、いかなる場合もGemini APIのエンドポイントへ送信してはならない。
* **API設定:** Gemini API利用時は、学習データとして利用されない設定（Enterprise利用またはオプトアウト設定）を確認する。
```

## File: data/db/chroma/.keep
```

```

## File: data/db/sql/.keep
```

```

## File: data/rules/company_rules.md
```markdown
# 弊社（行政書士法人）共通業務ルール
## 回答のスタイル
- 挨拶や前置き（「ご案内します」等）は一切不要。結論と箇条書きのみで出力すること。
- 語尾は「です・ます」調だが、簡潔にすること。
- 申請主体は不要（自明のため省略）。
- 証明日はすべて「被相続人の死亡日」を記載すること。（法定相続情報一覧図で確認）
- 既経過利息証明の必要有無：定期預金の口座があれば必ず「必要」とする。
- 取引明細の申請：税申告案件のみ必要。税理士へ有無と期間を確認するよう案内すること。
- 残高証明書の申請提出書類：
  1. 法定相続情報一覧図
  2. 委任状（代表相続人のみ）
  3. 印鑑証明書（代表相続人と弊社分）
  4. 履歴事項証明（弊社分）
  5. 弊社代表の行政書士証票と運転免許証のコピー [参照ファイル](https://example.cybozu.com/k/123/edit)

## 申請書類の共通仕様
- **申請書への押印**: 弊社の「実印（代表印）」を使用する。（認印は不可）
- **戸籍書類**: 原則として「法定相続情報一覧図」の原本還付請求付き提出とする。
  - ※急ぎで一覧図がない場合のみ「被相続人の出生〜死亡の除籍謄本＋相続人の現在戸籍」とする。
- **印鑑証明書**: 
  - 顧客（相続人）のものと、弊社（代理人）のものが必要。
  - 有効期限は銀行の規定に従うが、指定がない場合は「6ヶ月以内」のものを準備する。

## 手数料の支払い
- 原則として「銀行振込」を選択する。（相続人口座からの引落しは選択しない）
- 振込手続きは経理へ依頼すること。
- **経理依頼URL**: [Kintone経理アプリ](https://example.cybozu.com/k/123/edit) （ここから申請レコードを作成）

## ゆうちょ銀行特有のルール
- ゆうちょ銀行の残高証明手数料は、窓口支払ではなく「会社通帳からの引落とし」となる。
- **【必須表示】ゆうちょ銀行の残高証明書は、回答の最後に必ず以下のリンクを表示**:
  - [ゆうちょ引落管理スプレッドシート](https://example.cybozu.com/k/123/edit)
```

## File: data/templates/.keep
```

```

## File: src/legal_system/core/__init__.py
```python

```

## File: src/legal_system/core/ai_factory.py
```python
# src/legal_system/core/ai_factory.py

import os
import random
from typing import Any

from langchain_chroma import Chroma

# LangChain / Google Generative AI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# ★修正: 変数直接ではなく Config クラスをインポートします
from .config import Config


class AIFactory:
    """
    AIモデル（LLM）、Embeddings、VectorStoreのインスタンス生成を一元管理するファクトリークラス。
    APIキーのローテーション機能を含みます。
    """

    @staticmethod
    def _get_api_key() -> str:
        """
        利用可能なAPIキーを取得します。
        Home.py等で既に環境変数がセットされていればそれを使用し、
        なければConfigリストからランダムに取得してセットします。
        """
        # 1. 既に環境変数にセットされている場合（優先）
        env_key = os.getenv("GOOGLE_API_KEY")
        if env_key:
            return env_key

        # 2. 未セットの場合、Configから取得してセットする (ローテーション)
        if Config.GOOGLE_API_KEYS:
            selected_key = random.choice(Config.GOOGLE_API_KEYS)
            os.environ["GOOGLE_API_KEY"] = selected_key
            return selected_key

        raise ValueError(
            "❌ 有効な Google API Key が見つかりません。.env を確認してください。"
        )

    @classmethod
    def get_llm(cls, mode: str = "cloud") -> Any:
        """
        指定されたモードに応じたLLMインスタンスを返します。
        """
        api_key = cls._get_api_key()

        # ★修正: Config.GOOGLE_MODEL_NAME としてクラス変数にアクセス
        return ChatGoogleGenerativeAI(
            model=Config.GOOGLE_MODEL_NAME,
            google_api_key=api_key,
            temperature=Config.TEMPERATURE,
            convert_system_message_to_human=True,
        )

    @classmethod
    def get_embeddings(cls) -> Any:
        """
        埋め込みモデル（Embeddings）を返します。
        """
        api_key = cls._get_api_key()
        # ★修正: Config.EMBEDDING_MODEL を使用
        return GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL, google_api_key=api_key
        )

    @classmethod
    def get_vector_store(cls) -> Chroma:
        """
        永続化されたChromaベクトルストアのインスタンスを返します。
        """
        embeddings = cls.get_embeddings()

        # ディレクトリ作成 (念のため)
        if not Config.VECTOR_STORE_PATH.exists():
            os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)

        return Chroma(
            persist_directory=str(Config.VECTOR_STORE_PATH),
            embedding_function=embeddings,
        )
```

## File: src/legal_system/core/data_sync.py
```python
# src/legal_system/core/data_sync.py

import json

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir


class DataSyncEngine:
    def __init__(self):
        self.db = DatabaseManager()

    def sync_from_kintone_json(self, json_path: str):
        """Bookmarkletから落ちてきたJSONをSQLiteに同期"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = self.db._get_session()
        try:
            # 1. 案件 (Case) のUpsert
            case_num = data.get("case_number")
            if not case_num:
                return

            case = session.query(Case).filter_by(case_number=case_num).first()
            if not case:
                case = Case(case_number=case_num)
                session.add(case)
                session.flush()  # ID確定

            # 2. 被相続人情報の更新
            d_info = data.get("deceased", {})
            if d_info:
                # 既存があれば取得、なければ作成
                deceased = case.deceased_ref
                if not deceased:
                    deceased = Deceased(case_id=case.case_id)
                    session.add(deceased)

                # 値のセット
                deceased.name_last = d_info.get("name_last", "")
                deceased.name_first = d_info.get("name_first", "")
                # ... 日付変換などは適宜 ...

            # 3. 相続人の更新 (一旦全削除して入れ直すのが安全)
            if "heirs" in data:
                # 既存の相続人を削除
                for h in case.deceased_ref.heirs:
                    session.delete(h)

                # 再登録
                for h_data in data["heirs"]:
                    heir = Heir(
                        deceased_id=case.deceased_ref.id,
                        name_last=h_data.get("name_last", ""),
                        name_first=h_data.get("name_first", ""),
                        relationship_type=h_data.get("relation", ""),
                    )
                    session.add(heir)

            session.commit()
            print(f"✅ Synced Case: {case_num}")

        except Exception as e:
            session.rollback()
            print(f"❌ Sync Error: {e}")
        finally:
            session.close()
```

## File: src/legal_system/core/ocr_engine.py
```python
import logging
from io import BytesIO
from typing import Optional

# 外部ライブラリ
try:
    import pytesseract
    from pdf2image import convert_from_bytes
except ImportError:
    # 依存関係が不足している場合のエラーハンドリング用
    pytesseract = None
    convert_from_bytes = None

# ロガー設定
logger = logging.getLogger(__name__)

# Windowsの場合のTesseractパス設定例 (必要に応じてコメントアウトを解除してパスを指定)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_scanned_pdf(file_bytes: bytes) -> str:
    """
    画像化されたPDF(スキャンデータ)からテキストを抽出する。
    pdf2image で画像に変換し、pytesseract でOCRを実行する。
    """
    if not pytesseract or not convert_from_bytes:
        return "Error: OCRライブラリ(pytesseract, pdf2image)がインストールされていません。"

    full_text = ""
    try:
        # PDFを画像のリストに変換 (dpi=300推奨)
        # fmt="jpeg" で処理を高速化
        images = convert_from_bytes(file_bytes, dpi=300, fmt="jpeg")
        
        for i, img in enumerate(images):
            # 日本語(jpn)と英語(eng)のハイブリッドOCR
            text = pytesseract.image_to_string(img, lang='jpn+eng')
            
            # ページ区切りを明確にする
            full_text += f"\n--- Page {i+1} (OCR Result) ---\n{text}"
            
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return f"OCR処理中にエラーが発生しました: {str(e)}"
        
    return full_text
```

## File: src/legal_system/models/__init__.py
```python

```

## File: src/legal_system/models/base.py
```python

```

## File: src/legal_system/tools/__init__.py
```python
def hello() -> str:
    return "Hello from legal-rag-system!"
```

## File: src/legal_system/tools/coord_tool.py
```python
# src/legal_system/tools/coord_tool.py

import hashlib
import os
import sys
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from pdf2image import convert_from_bytes
from PIL import ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from streamlit_image_coordinates import streamlit_image_coordinates

# パス解決
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(BASE_DIR)

from legal_system.core.database_manager import DatabaseManager

# フォント設定
FONT_PATH = os.path.join(BASE_DIR, "data", "fonts", "ipaexg.ttf")
try:
    pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(layout="wide", page_title="座標登録ツール (DB連携対応版)")
st.title("📍 PDF座標 登録 & 編集ツール")

db = DatabaseManager()
user_info = db.get_current_user_info()


# ==========================================
# 0. ヘルパー関数 & プリセット
# ==========================================
def calculate_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def get_wareki(dt):
    if dt.year >= 2019:
        return f"令和{dt.year - 2018}"
    return str(dt.year)


def split_phone_number(phone_str):
    parts = ["", "", ""]
    if phone_str:
        phone_str = phone_str.replace("ー", "-").replace("−", "-")
        splits = phone_str.split("-")
        for i in range(min(len(splits), 3)):
            parts[i] = splits[i]
    return parts


user_phone_parts = split_phone_number(user_info.get("phone", ""))

COMPANY_INFO = {
    "zip1": "100",
    "zip2": "0001",
    "address": "東京都千代田区千代田1-1",
    "name": "行政書士法人未来",
    "rep_name": "行政書士 山田 太郎",
}
today = datetime.now()
wareki_year = get_wareki(today)

PRESETS = {
    "（選択なし）": {"label": "", "val": ""},
    "----- ★DB連携用タグ (自動差込)★ -----": {"label": "", "val": ""},
    "{被相続人 氏名}": {
        "label": "被相続人氏名",
        "val": "{deceased_name}",
        "desc": "DBから被相続人名を自動取得",
    },
    "{被相続人 死亡日}": {
        "label": "被相続人死亡日",
        "val": "{death_date}",
        "desc": "DBから死亡日を自動取得",
    },
    "{相続人 氏名}": {
        "label": "相続人氏名",
        "val": "{heir_name}",
        "desc": "DBから相続人名を自動取得",
    },
    "{相続人 住所}": {
        "label": "相続人住所",
        "val": "{heir_address}",
        "desc": "DBから住所を自動取得",
    },
    "----- 図形・記号 -----": {"label": "", "val": ""},
    "四角形枠 (サイズ指定)": {
        "label": "枠線",
        "val": "RECT:30x30",
        "desc": "RECT:幅x高さ (pt単位)",
    },
    "数字「1」": {"label": "数字1", "val": "1", "size": 11},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14},
    "----- 日付関連 (固定値) -----": {"label": "", "val": ""},
    "今日 (令和〇年)": {"label": "記入日_和暦年", "val": wareki_year},
    "今日 (20XX年)": {"label": "記入日_西暦年", "val": str(today.year)},
    "----- 担当者・会社 (固定値) -----": {"label": "", "val": ""},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]},
    "代理人 (肩書)": {"label": "代理人肩書", "val": "代理人"},
    "電話番号 (市外局番)": {"label": "担当者TEL_1", "val": user_phone_parts[0]},
    "電話番号 (市内局番)": {"label": "担当者TEL_2", "val": user_phone_parts[1]},
    "電話番号 (加入者)": {"label": "担当者TEL_3", "val": user_phone_parts[2]},
    "会社郵便番号 (3桁)": {"label": "会社郵便番号1", "val": COMPANY_INFO["zip1"]},
    "会社郵便番号 (4桁)": {"label": "会社郵便番号2", "val": COMPANY_INFO["zip2"]},
    "会社住所": {"label": "会社住所", "val": COMPANY_INFO["address"]},
    "代表者名": {"label": "代表者名", "val": COMPANY_INFO["rep_name"]},
    "相続人 代理人": {"label": "相続人代理人署名", "val": "相続人 相続 花子 代理人"},
}

# セッション初期化
if "last_x" not in st.session_state:
    st.session_state["last_x"] = 0
if "last_y" not in st.session_state:
    st.session_state["last_y"] = 0
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1

if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 10.5
if "input_color" not in st.session_state:
    st.session_state["input_color"] = "black"
if "input_desc" not in st.session_state:
    st.session_state["input_desc"] = ""

# ==========================================
# 1. サイドバー: ファイル管理エリア
# ==========================================
with st.sidebar:
    st.header("📂 対象ファイル")
    uploaded_file = st.file_uploader("帳票PDFをアップロード", type="pdf")

    file_hash = None
    existing_coords = []
    df_existing = pd.DataFrame()

    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_hash = calculate_hash(file_bytes)
        st.caption(f"File ID: {file_hash[:8]}...")

        # データベースから座標を取得
        existing_coords = db.get_coordinates_by_hash(file_hash)
        if existing_coords:
            df_existing = pd.DataFrame(existing_coords)

        st.success(f"登録済み: {len(existing_coords)} 件")
    else:
        st.warning(
            "左記でファイルをアップロードしてください。\n(再編集の場合も同じファイルをアップロードが必要です)"
        )

    st.divider()
    st.header("⚙️ 設定")

    def on_def_size_change():
        st.session_state["input_size"] = st.session_state["def_font_size_key"]

    def_font_size = st.number_input(
        "基本フォントサイズ (pt)",
        4.0,
        72.0,
        10.5,
        step=0.5,
        key="def_font_size_key",
        on_change=on_def_size_change,
    )

# ==========================================
# 2. メインエリア
# ==========================================
col_img, col_ctrl = st.columns([1.8, 1.2])

if not uploaded_file:
    st.info("👈 サイドバーからPDFをアップロードしてください。")
    st.stop()

# --- プレビュー用準備 ---
reader = PdfReader(BytesIO(file_bytes))
# 1ページ目のサイズを取得 (Point単位)
media_box = reader.pages[0].mediabox
pdf_w_pt = float(media_box.width)
pdf_h_pt = float(media_box.height)

images = convert_from_bytes(file_bytes)
total_pages = len(images)
img_w_px, img_h_px = images[0].size
# プレビュー拡大率
preview_scale = img_h_px / pdf_h_pt


# データ更新用コールバック関数
def on_data_editor_change():
    changes = st.session_state["editor"]
    if changes["edited_rows"]:
        for idx, row_changes in changes["edited_rows"].items():
            target_id = df_existing.iloc[int(idx)]["id"]
            db.update_coordinate_direct(int(target_id), row_changes)
        st.toast("✅ 変更を保存しました")

    if changes["deleted_rows"]:
        for idx in changes["deleted_rows"]:
            target_id = df_existing.iloc[int(idx)]["id"]
            db.delete_coordinate(int(target_id))
        st.toast("🗑️ 削除しました")


# --- 右カラム: 入力 & リスト編集 ---
with col_ctrl:
    st.subheader("2. 設定と登録")

    # プリセット選択
    def on_preset():
        sel = st.session_state["preset_sel"]
        if sel and PRESETS[sel]["val"]:
            p = PRESETS[sel]
            st.session_state["input_label"] = p["label"]
            st.session_state["input_val"] = p["val"]
            if "size" in p:
                st.session_state["input_size"] = float(p["size"])
            if "desc" in p:
                st.session_state["input_desc"] = p["desc"]

    st.selectbox(
        "⚡️ プリセット", list(PRESETS.keys()), key="preset_sel", on_change=on_preset
    )

    # 入力フォーム
    c1, c2 = st.columns([2, 1])
    label_in = c1.text_input(
        "項目名 (必須)", key="input_label", placeholder="例: 被相続人氏名"
    )
    val_in = c2.text_input(
        "テスト値",
        key="input_val",
        help="矩形: 'RECT:幅x高さ', DB連携: '{deceased_name}'",
    )

    c3, c4 = st.columns(2)
    size_in = c3.number_input(
        "サイズ(pt)", 0.5, 100.0, key="input_size", step=0.5, format="%.1f"
    )
    color_in = c4.selectbox("色", ["black", "red"], key="input_color")

    desc_in = st.text_input("備考", key="input_desc")

    st.write(
        f"📍 座標: X={st.session_state['last_x']} / Y={st.session_state['last_y']} (P.{st.session_state['current_page']})"
    )

    if st.button("💾 新規登録 / 上書き保存", type="primary"):
        if not label_in:
            st.error("項目名は必須です")
        elif st.session_state["last_x"] == 0:
            st.error("左の画像をクリックして位置を決めてください")
        else:
            success = db.register_coordinate(
                file_hash=file_hash,
                label=label_in,
                x=st.session_state["last_x"],
                y=st.session_state["last_y"],
                page_number=st.session_state["current_page"],
                description=desc_in,
                font_size=size_in,
                color=color_in,
                test_value=val_in,
            )
            if success:
                st.toast(f"✅ 「{label_in}」を登録しました！")
                import time

                time.sleep(0.5)
                st.rerun()

    st.divider()

    # ▼▼▼ 登録済みリスト (width='stretch'対応) ▼▼▼
    st.subheader("📋 登録済みリスト (直接修正可)")
    if not df_existing.empty:
        column_order = [
            "label",
            "x",
            "y",
            "page",
            "font_size",
            "color",
            "value",
            "desc",
            "id",
        ]
        # 存在するカラムのみフィルタリング
        df_display = df_existing[[c for c in column_order if c in df_existing.columns]]

        st.data_editor(
            df_display,
            column_config={
                "id": None,
                "label": st.column_config.TextColumn("項目名", width="medium"),
                "x": st.column_config.NumberColumn("X", format="%.1f", step=0.1),
                "y": st.column_config.NumberColumn("Y", format="%.1f", step=0.1),
                "page": st.column_config.NumberColumn("頁", width="small"),
                "font_size": st.column_config.NumberColumn(
                    "pt", width="small", format="%.1f", step=0.5
                ),
                "color": st.column_config.SelectboxColumn(
                    "色", options=["black", "red"], width="small"
                ),
                "value": st.column_config.TextColumn("値/RECT", width="medium"),
                "desc": st.column_config.TextColumn("備考", width="large"),
            },
            hide_index=True,
            width="stretch",  # use_container_width=True の代わり
            key="editor",
            num_rows="dynamic",
            on_change=on_data_editor_change,
        )
    else:
        st.info("まだ登録データはありません")

    # ▼▼▼ PDF作成ロジック (リスト下の配置 & 全件出力) ▼▼▼
    st.divider()
    st.subheader("🖨️ PDF作成 (登録済み全件出力)")

    if st.button("現在のリスト内容でPDFを作成"):
        if df_existing.empty:
            st.error("登録されたデータがありません。先に座標を登録してください。")
        else:
            try:
                # ベースPDFの読み込み
                packet = BytesIO()
                # ReportLabキャンバス作成
                can = canvas.Canvas(packet, pagesize=(pdf_w_pt, pdf_h_pt))

                # 登録済みデータを全件ループ
                for index, row in df_existing.iterrows():
                    # ページ番号が違う場合はスキップ（今回は簡易的に1ページずつ出力ではなく、全ページマージする前提）
                    # 実際にはページごとにCanvasを分けるか、ページ移動が必要だが、
                    # 簡易実装として「座標があるページに移動して描く」方式をとる

                    target_page = int(row["page"])
                    val = row["value"]
                    x = float(row["x"])
                    y = float(row["y"])
                    f_size = float(row["font_size"])
                    clr = row["color"]

                    # ページ設定 (ReportLabはページ概念が少し特殊なので、今回は
                    # シンプルに「全ページ処理するPDFWriter」側で合成する方式をとるため
                    # ここではページごとにCanvasを作るのが正しいが、
                    # 簡易的に「ページごとにPDFを作って合成」するループにする)
                    pass

                # --- 修正版PDF生成ロジック (ページ対応) ---
                output = PdfWriter()

                # 1ページずつ処理
                for i, page_obj in enumerate(reader.pages):
                    page_num = i + 1

                    # このページの座標データのみ抽出
                    page_coords = df_existing[df_existing["page"] == page_num]

                    if not page_coords.empty:
                        # このページ用のオーバーレイPDFを作成
                        packet_page = BytesIO()
                        # ページサイズ取得
                        pw = float(page_obj.mediabox.width)
                        ph = float(page_obj.mediabox.height)

                        can_page = canvas.Canvas(packet_page, pagesize=(pw, ph))

                        # 描画ループ
                        for _, row in page_coords.iterrows():
                            val = row["value"]
                            if not val:
                                continue  # 値がなければスキップ

                            x = float(row["x"])
                            y = float(row["y"])
                            f_size = float(row["font_size"])

                            # 色設定
                            c_obj = red if row["color"] == "red" else black
                            can_page.setFillColor(c_obj)
                            can_page.setStrokeColor(c_obj)

                            # 座標変換 (画像クリック(左上) -> PDF(左下))
                            # 登録されているX,Yは「画像上のピクセル」
                            # ここでPDF上のポイントに変換する必要がある
                            # preview_scale = img_h_px / pdf_h_pt なので
                            # pdf_pt = img_px / preview_scale

                            # ★重要: DBの座標はクリック時のもの(Pixel相当)
                            # ここで再計算する
                            # 厳密にはページごとにサイズが違う可能性もあるが、今回は1ページ目の比率を使用

                            scale_x = pw / img_w_px
                            scale_y = ph / img_h_px

                            draw_x = x * scale_x
                            draw_y_base = ph - (y * scale_y)

                            if str(val).startswith("RECT:"):
                                try:
                                    dims = val.replace("RECT:", "").split("x")
                                    w_pt = float(dims[0])
                                    h_pt = float(dims[1])
                                    rect_y = draw_y_base - h_pt
                                    can_page.setLineWidth(f_size)
                                    can_page.rect(
                                        draw_x, rect_y, w_pt, h_pt, stroke=1, fill=0
                                    )
                                except:
                                    pass
                            else:
                                can_page.setFont("IPAexG", f_size)
                                text_y = draw_y_base - (f_size * 0.8)
                                can_page.drawString(draw_x, text_y, str(val))

                        can_page.save()
                        packet_page.seek(0)
                        overlay = PdfReader(packet_page)
                        page_obj.merge_page(overlay.pages[0])

                    output.add_page(page_obj)

                # 出力
                out_stream = BytesIO()
                output.write(out_stream)

                st.success("PDF作成完了！")
                st.download_button(
                    label="📥 作成したPDFをダウンロード",
                    data=out_stream,
                    file_name="filled_result.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF作成中にエラーが発生しました: {e}")
                st.exception(e)  # 詳細エラー表示

# --- 左カラム: 画像プレビュー ---
with col_img:
    st.subheader("1. 座標指定")

    new_page = st.number_input(
        "ページ", 1, total_pages, st.session_state["current_page"]
    )
    if new_page != st.session_state["current_page"]:
        st.session_state["current_page"] = new_page
        st.rerun()

    bg_image = images[st.session_state["current_page"] - 1].copy()
    draw = ImageDraw.Draw(bg_image)

    def draw_on_image(draw_obj, x, y, val, size_pt, color_name):
        color_rgba = (255, 0, 0, 255) if color_name == "red" else (0, 0, 0, 255)
        if not val:
            return

        if str(val).startswith("RECT:"):
            try:
                dims = val.replace("RECT:", "").split("x")
                w_pt = float(dims[0])
                h_pt = float(dims[1])
                w_px = w_pt * preview_scale
                h_px = h_pt * preview_scale
                line_width = int(max(1, size_pt * (preview_scale / 2)))
                draw_obj.rectangle(
                    [x, y, x + w_px, y + h_px], outline=color_rgba, width=line_width
                )
            except:
                pass
        else:
            try:
                px_size = size_pt * preview_scale
                font = ImageFont.truetype(FONT_PATH, int(px_size))
                draw_obj.text((x, y), str(val), font=font, fill=color_rgba)
            except:
                pass

    # A. 入力中のプレビュー
    if val_in:
        draw_on_image(
            draw,
            st.session_state["last_x"],
            st.session_state["last_y"],
            val_in,
            size_in,
            color_in,
        )
        if not str(val_in).startswith("RECT:"):
            try:
                px_size = size_in * preview_scale
                font = ImageFont.truetype(FONT_PATH, int(px_size))
                bbox = draw.textbbox(
                    (st.session_state["last_x"], st.session_state["last_y"]),
                    val_in,
                    font=font,
                )
                draw.rectangle(bbox, outline="blue", width=2)
            except:
                pass

    # B. 登録済みデータのプレビュー
    current_page_coords = [
        c for c in existing_coords if c["page"] == st.session_state["current_page"]
    ]
    for c in current_page_coords:
        draw_on_image(draw, c["x"], c["y"], c["value"], c["font_size"], c["color"])

    # 座標取得
    value = streamlit_image_coordinates(
        bg_image, key=f"canvas_p{st.session_state['current_page']}"
    )
    if value:
        if (
            value["x"] != st.session_state["last_x"]
            or value["y"] != st.session_state["last_y"]
        ):
            st.session_state["last_x"] = value["x"]
            st.session_state["last_y"] = value["y"]
            st.rerun()
```

## File: src/legal_system/ui/__init__.py
```python

```

## File: src/legal_system/ui/Home.py
```python
# src/legal_system/ui/Home.py

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# プロジェクトルートへのパス解決 (update_bank_master読み込み用)
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(ROOT_DIR)

# LangChain関連
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# PDFプレビュー用
try:
    from pdf2image import convert_from_bytes
except ImportError:
    convert_from_bytes = None

# 自作モジュール
from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ocr_engine import extract_text_from_scanned_pdf

# 更新スクリプトの関数をインポート
try:
    from update_bank_master import (
        download_data,
        get_remote_last_commit_date,
        load_local_state,
        save_local_state,
    )
except ImportError:
    get_remote_last_commit_date = None

load_dotenv()

# ==========================================
# 2. アプリケーションの初期設定
# ==========================================
st.set_page_config(page_title="書士業務システム | ホーム", layout="wide", page_icon="⚖️")

# DBマネージャーの初期化
db_manager = DatabaseManager()
current_user = db_manager.get_current_user_info()


# ==========================================
# 更新チェック機能 (キャッシュ化)
# ==========================================
# ★修正: キャッシュ時間を短くし、ファイル実在チェックを追加
@st.cache_resource(ttl=60)
def check_update_status():
    """
    更新があるかチェックする関数
    戻り値: (status_code, message/date)
    status_code: 0=最新/オフライン, 1=更新あり, 2=エラー
    """
    if not get_remote_last_commit_date:
        return 2, "更新スクリプトなし"

    # ★追加: データファイルが物理的に存在するかチェック
    banks_path = os.path.join(ROOT_DIR, "data", "zengin", "banks.json")
    if not os.path.exists(banks_path):
        return 1, "データ未取得 (ファイルなし)"

    # 1. リモート確認 (タイムアウト付きで安全に)
    remote_date = get_remote_last_commit_date()
    if not remote_date:
        return 0, "オフライン (更新チェック不可)"

    # 2. ローカル確認
    local_state = load_local_state()
    local_date = local_state.get("last_commit_date", "")

    # 3. 比較
    if remote_date != local_date:
        return 1, remote_date  # 更新あり！日付を返す

    return 0, "最新です"


# ==========================================
# 3. 業務ルール・マスタ読み込み関数
# ==========================================
def load_company_rules():
    """全社共通の業務ルールを読み込む"""
    rule_path = os.path.join(ROOT_DIR, "data", "rules", "company_rules.txt")

    if os.path.exists(rule_path):
        try:
            with open(rule_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(rule_path, "r", encoding="cp932") as f:
                    return f.read()
            except Exception:
                return "（読込失敗：文字コード不明）"
        except Exception:
            return "（読込失敗）"
    return "（ファイルなし）"


def get_bank_specific_info(query: str):
    """銀行固有ルールをCSVから取得"""
    csv_path = os.path.join(ROOT_DIR, "data", "rules", "bank_master.csv")

    if not os.path.exists(csv_path):
        return ""

    df = None
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding="cp932")
        except Exception:
            return ""
    except Exception:
        return ""

    if df is None:
        return ""

    try:
        info_text = ""
        for index, row in df.iterrows():
            bank_name = str(row.get("銀行名", ""))
            if bank_name and bank_name in query:
                info_text += f"""
                【{bank_name} 個別ルール】
                - 印鑑証明書の期限: {row.get("印鑑証明期限", "規定なし")}
                - 代理人本人確認書類: {row.get("代理人本人確認書類", "規定なし")}
                - 手数料支払方法: {row.get("振込ルール", "規定なし")}
                - 特記事項: {row.get("備考", "")}
                """
        return info_text
    except Exception:
        return ""


# ==========================================
# 4. ヘルパー関数 (ロジック & UI操作)
# ==========================================
def js_scroll_to_bottom():
    """画面最下部へスクロール"""
    js = """
    <script>
        var mainParams = window.parent.document.querySelector('section.main');
        if (mainParams) {
            mainParams.scrollTo({ top: mainParams.scrollHeight, behavior: 'smooth' });
        }
    </script>
    """
    components.html(js, height=0)


def js_focus_chat_input():
    """チャット入力欄にフォーカス"""
    js = """
    <script>
        setTimeout(function() {
            const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (textArea) { textArea.focus(); }
        }, 500);
    </script>
    """
    components.html(js, height=0)


def calculate_file_hash(file_bytes: bytes) -> str:
    """ファイルのMD5ハッシュ値を計算"""
    return hashlib.md5(file_bytes).hexdigest()


def analyze_document_info(text_content: str, llm):
    """ドキュメントから「ファイル名」「銀行名」「書類種別」を抽出する"""
    if not text_content:
        return {"filename": "", "bank_name": "", "doc_type": ""}

    prompt = """
    以下のドキュメント冒頭を読み、3つの情報をJSON形式で出力してください。
    
    1. filename: {金融機関名}_{書類名}
    2. bank_name: 金融機関名 (特定できなければ"その他")
    3. doc_type: 以下のいずれかを選択
       - "手引き": 手続きガイド、マニュアル、要領
       - "残高証明": 残高証明書発行依頼書
       - "相続届": 相続届、解約依頼書、名義変更届
       - "委任状": 委任状
       - "その他": 上記以外
    
    【ドキュメント冒頭】
    """ + text_content[:1500]

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return {"filename": "解析失敗", "bank_name": "その他", "doc_type": "その他"}


def extract_text_safe(file_bytes: bytes) -> str:
    """PDFからテキスト抽出 (pypdf -> OCR)"""
    text = ""
    try:
        pdf = PdfReader(BytesIO(file_bytes))
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t
    except:
        pass
    if len(text.strip()) < 50:
        text = extract_text_from_scanned_pdf(file_bytes)
    return text


def filter_docs_by_bank_metadata(query: str, docs: list) -> list:
    """銀行名キーワードによる検索結果のフィルタリング"""
    bank_keywords = {
        "ゆうちょ": "ゆうちょ",
        "郵貯": "ゆうちょ",
        "じぶん": "じぶん",
        "au": "じぶん",
        "三菱": "三菱",
        "UFJ": "三菱",
        "みずほ": "みずほ",
        "三井": "三井",
        "SMBC": "三井",
        "りそな": "りそな",
        "横浜": "横浜",
        "千葉": "千葉",
    }

    target_key = None
    for key, required_str in bank_keywords.items():
        if key in query:
            target_key = required_str
            break

    if not target_key:
        return docs

    filtered_docs = []
    for d in docs:
        bank_meta = d.metadata.get("bank_name", "")
        filename = d.metadata.get("source", "")

        if target_key in bank_meta or target_key in filename:
            filtered_docs.append(d)

    return filtered_docs if filtered_docs else []


def run_rag_search(query: str, mode_label: str, llm):
    """RAG検索実行関数"""
    if not llm:
        return "AIモデルの初期化に失敗しました。", []

    # 1. ルール読込
    company_rules = load_company_rules()
    bank_specifics = get_bank_specific_info(query)

    # 2. 検索
    vector_store = AIFactory.get_vector_store()
    try:
        docs = vector_store.similarity_search(query, k=10)
        docs = filter_docs_by_bank_metadata(query, docs)
        docs = docs[:4]

        context = "\n\n".join([d.page_content for d in docs]) if docs else ""
        if not docs:
            context = "（関連する資料は見つかりませんでした）"

        db_manager.log_action(
            current_user["id"], "SEARCH", f"Mode:{mode_label}", f"Query: {query}"
        )
    except Exception as e:
        return f"検索エラー: {e}", []

    # 3. 回答生成
    system_prompt = f"""
    あなたは行政書士法人の業務システムです。回答対象は「行政書士補助者」です。
    【社内ルール】と【銀行マスタ】を**最優先**し、【参照資料】で補完して回答してください。
    
    【社内ルール】{company_rules}
    【銀行情報】{bank_specifics}
    
    【基本】
    1. 申請主体は「代表行政書士（代理人）」
    2. 挨拶不要。結論から記述。
    3. OCR誤字は補正して解釈。
    """
    template = f"""{system_prompt}\n【参照資料】{{context}}\n【質問】{{question}}"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()

    try:
        answer = chain.invoke({"context": context, "question": query})
        return answer, docs
    except Exception as e:
        return f"生成エラー: {str(e)}", []


# ==========================================
# 5. UIメイン構成
# ==========================================
def main():
    # --- サイドバー (ユーザー情報 & 更新) ---
    with st.sidebar:
        st.title("⚖️ 業務メニュー")
        st.info(f"👤 **{current_user['name']}**")
        st.caption(f"所属: {current_user['dept']}")
        if current_user["phone"]:
            st.caption(f"TEL: {current_user['phone']}")

        with st.expander("ユーザー情報更新"):
            new_name = st.text_input("表示名", value=current_user["name"])
            new_dept = st.text_input("所属", value=current_user["dept"])
            new_phone = st.text_input("電話番号", value=current_user["phone"])

            if st.button("更新"):
                db_manager.register_user(
                    current_user["id"], new_name, new_dept, new_phone
                )
                st.success("更新しました。再読み込みしてください。")

        st.divider()

        # ▼▼▼ 自動更新チェック機能 (UIプログレス対応版) ▼▼▼
        st.subheader("🔄 マスタデータ管理")

        # 起動時にチェック
        status, info = check_update_status()

        if status == 1:
            st.warning(f"⚠️ {info}")  # メッセージを表示

            if st.button("今すぐ更新して取り込む"):
                # --- Streamlitのプログレスバーを定義 ---
                progress_text = "データをダウンロード中..."
                my_bar = st.progress(0, text=progress_text)

                # --- コールバック関数 ---
                def update_progress(current, total, message):
                    percent = current / total if total > 0 else 0
                    if percent > 1.0:
                        percent = 1.0
                    my_bar.progress(percent, text=f"{message} ({current}/{total})")

                # --- 実行 ---
                success, _ = download_data(progress_callback=update_progress)

                if success:
                    my_bar.progress(1.0, text="完了しました！")
                    # 現在の日付を保存
                    if get_remote_last_commit_date:
                        remote_date = (
                            get_remote_last_commit_date() or datetime.now().isoformat()
                        )
                        save_local_state(remote_date)
                    st.success("更新完了！アプリをリロードします。")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("更新に失敗しました。ネット接続を確認してください。")
        elif status == 0:
            st.caption(f"✅ {info}")
            # 強制更新ボタン（念のため）
            if st.button("強制再取得"):
                # --- Streamlitのプログレスバーを定義 ---
                progress_text = "データを強制ダウンロード中..."
                my_bar = st.progress(0, text=progress_text)

                def update_progress(current, total, message):
                    percent = current / total if total > 0 else 0
                    if percent > 1.0:
                        percent = 1.0
                    my_bar.progress(percent, text=f"{message} ({current}/{total})")

                success, _ = download_data(progress_callback=update_progress)
                if success:
                    my_bar.progress(1.0, text="完了")
                    if get_remote_last_commit_date:
                        remote_date = (
                            get_remote_last_commit_date() or datetime.now().isoformat()
                        )
                        save_local_state(remote_date)
                    st.success("完了。リロードします。")
                    time.sleep(1)
                    st.rerun()
        else:
            st.caption("⚠️ 更新機能無効")
        # ▲▲▲ ここまで ▲▲▲

        st.divider()
        st.subheader("🤖 AIモード選択")
        ai_mode = st.radio(
            "処理モード:", ("☁️ Cloud (Gemini)", "🔒 Secure (Local)"), index=0
        )

        if "Cloud" in ai_mode:
            mode_label = "CLOUD"
            llm = AIFactory.get_llm("cloud")
            st.info("🚀 **高速・高機能**\n一般手続用。個人情報入力禁止。")
        else:
            mode_label = "LOCAL"
            llm = AIFactory.get_llm("local")
            st.warning("🛡️ **機密保護**\nオフライン処理。機密書類用。")

    # --- メインエリア ---
    tab1, tab2, tab3 = st.tabs(["💬 実務Q&A", "📥 資料学習 (OCR)", "🗑️ データ管理"])

    # --- Tab 1: チャット ---
    with tab1:
        st.subheader(f"金融機関手続のAI検索 ({mode_label})")
        js_focus_chat_input()

        if mode_label == "LOCAL":
            st.error("【機密モード】データは外部送信されません。")
        else:
            st.success("【クラウドモード】Gemini 2.5 使用中。")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.write(m["content"])
                if m.get("source_docs"):
                    with st.expander("📚 参照した雛形・資料をダウンロード"):
                        seen_paths = set()
                        for doc in m["source_docs"]:
                            path = doc.metadata.get("path")
                            name = doc.metadata.get("source", "不明なファイル")
                            bank = doc.metadata.get("bank_name", "")
                            dtype = doc.metadata.get("doc_type", "")

                            label_parts = [f"📥 {name}"]
                            if bank:
                                label_parts.append(f"({bank})")
                            if dtype:
                                label_parts.append(f"[{dtype}]")
                            label = " ".join(label_parts)

                            if path and os.path.exists(path) and path not in seen_paths:
                                seen_paths.add(path)
                                with open(path, "rb") as f:
                                    st.download_button(
                                        label=label,
                                        data=f,
                                        file_name=os.path.basename(path),
                                        mime="application/pdf",
                                        key=f"dl_{os.path.basename(path)}_{time.time()}",
                                    )

        if prompt := st.chat_input("質問を入力..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("社内ルール・手引きを確認中..."):
                    response, source_docs = run_rag_search(prompt, mode_label, llm)
                    st.write(response)

                    if source_docs:
                        with st.expander(
                            "📚 参照した雛形・資料をダウンロード", expanded=True
                        ):
                            seen_paths = set()
                            for doc in source_docs:
                                path = doc.metadata.get("path")
                                name = doc.metadata.get("source", "不明なファイル")
                                bank = doc.metadata.get("bank_name", "")
                                dtype = doc.metadata.get("doc_type", "")

                                label_parts = [f"📥 {name}"]
                                if bank:
                                    label_parts.append(f"({bank})")
                                if dtype:
                                    label_parts.append(f"[{dtype}]")
                                label = " ".join(label_parts)

                                if (
                                    path
                                    and os.path.exists(path)
                                    and path not in seen_paths
                                ):
                                    seen_paths.add(path)
                                    with open(path, "rb") as f:
                                        st.download_button(
                                            label=label,
                                            data=f,
                                            file_name=os.path.basename(path),
                                            mime="application/pdf",
                                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                            "source_docs": source_docs,
                        }
                    )

    # --- Tab 2: アップロード ---
    with tab2:
        st.subheader("📂 雛形・記入例の登録")
        st.caption("重複チェック・タグ付け機能付き。PDFを解析し登録します。")

        s_norm, s_sec = st.tabs(["🟦 一般雛形", "🟥 記入例 (機密)"])

        # 2-A. 一般
        with s_norm:
            st.info("個人情報を含まない手引き等")

            # === 【追加】案件紐付け選択エリア ===
            session = db_manager._get_session()
            target_case_id = None
            try:
                from legal_system.models.tables import Case

                cases = session.query(Case).all()
                # 選択肢: None(共通) + 各案件
                case_opts = {"（全案件共通の雛形として登録）": None}
                for c in cases:
                    case_opts[f"{c.case_number}: {c.client_name}"] = c.case_id

                selected_case_label = st.selectbox(
                    "紐付ける案件 (任意)",
                    list(case_opts.keys()),
                    help="特定の案件専用の資料であれば案件を選択してください。テンプレートの場合は「共通」のままにしてください。",
                )
                target_case_id = case_opts[selected_case_label]
            finally:
                session.close()
            # =====================================

            files_n = st.file_uploader(
                "PDFアップロード (一般)", accept_multiple_files=True, key="up_n"
            )

            if files_n and st.button("🔍 クラウド解析", key="btn_n"):
                st.session_state.upload_stage = []
                llm_cloud = AIFactory.get_llm("cloud")

                for f in files_n:
                    fb = f.read()
                    f_hash = calculate_file_hash(fb)
                    if db_manager.is_file_registered(f_hash):
                        st.warning(f"⚠️ {f.name} は既に登録されています。")
                        continue

                    text = extract_text_safe(fb)
                    meta = (
                        analyze_document_info(text, llm_cloud)
                        if text
                        else {
                            "filename": f.name,
                            "bank_name": "その他",
                            "doc_type": "その他",
                        }
                    )

                    st.session_state.upload_stage.append(
                        {
                            "old": f.name,
                            "new": meta.get("filename", f.name),
                            "bank_name": meta.get("bank_name", "その他"),
                            "doc_type": meta.get("doc_type", "その他"),
                            "data": fb,
                            "text": text,
                            "type": "general",
                            "hash": f_hash,
                            "case_id": target_case_id,  # 選択された案件IDを保持
                        }
                    )

                if st.session_state.upload_stage:
                    st.rerun()
                else:
                    st.info("新規登録対象はありません。")

        # 2-B. 機密
        with s_sec:
            st.warning("個人情報を含む書類 (ローカル処理)")
            # こちらも同様に案件紐付けを追加
            session = db_manager._get_session()
            target_case_id_sec = None
            try:
                from legal_system.models.tables import Case

                cases = session.query(Case).all()
                case_opts = {"（全案件共通の雛形として登録）": None}
                for c in cases:
                    case_opts[f"{c.case_number}: {c.client_name}"] = c.case_id

                selected_case_label_sec = st.selectbox(
                    "紐付ける案件 (任意)",
                    list(case_opts.keys()),
                    key="sec_case_sel",
                    help="特定の案件専用の資料であれば案件を選択してください。",
                )
                target_case_id_sec = case_opts[selected_case_label_sec]
            finally:
                session.close()

            file_s = st.file_uploader(
                "PDFアップロード (機密)", accept_multiple_files=False, key="up_s"
            )

            if file_s:
                fb_s = file_s.read()
                f_hash = calculate_file_hash(fb_s)

                if db_manager.is_file_registered(f_hash):
                    st.error(f"⛔ {file_s.name} は既に登録済みです。")
                else:
                    if convert_from_bytes:
                        try:
                            images = convert_from_bytes(fb_s, first_page=1, last_page=1)
                            if images:
                                st.image(images[0], caption="プレビュー", width=400)
                                js_scroll_to_bottom()
                        except:
                            pass

                    check = st.checkbox(
                        "機密書類であることを確認しました", key="check_s"
                    )
                    if check:
                        js_scroll_to_bottom()

                    if check and st.button("🔒 ローカル解析", key="btn_s"):
                        st.session_state.upload_stage = []
                        llm_local = AIFactory.get_llm("local")

                        with st.spinner("解析中..."):
                            text_s = extract_text_safe(fb_s)
                            meta = (
                                analyze_document_info(text_s, llm_local)
                                if text_s
                                else {
                                    "filename": file_s.name,
                                    "bank_name": "その他",
                                    "doc_type": "その他",
                                }
                            )
                            if "記入例" not in meta["filename"]:
                                meta["filename"] += "_記入例"

                            st.session_state.upload_stage.append(
                                {
                                    "old": file_s.name,
                                    "new": meta.get("filename", file_s.name),
                                    "bank_name": meta.get("bank_name", "その他"),
                                    "doc_type": meta.get("doc_type", "その他"),
                                    "data": fb_s,
                                    "text": text_s,
                                    "type": "secure",
                                    "hash": f_hash,
                                    "case_id": target_case_id_sec,  # 案件IDを保持
                                }
                            )
                        st.rerun()

        # 2-C. 保存処理
        if st.session_state.get("upload_stage"):
            st.divider()
            st.subheader("💾 登録確認")
            with st.form("save_form"):
                configs = []
                st.caption("登録名、銀行名タグ、書類種別を確認してください。")

                for i, item in enumerate(st.session_state.upload_stage):
                    c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                    c1.text(item["old"])
                    new_name = c2.text_input("登録名", value=item["new"], key=f"fn_{i}")
                    new_bank = c3.text_input(
                        "銀行タグ", value=item["bank_name"], key=f"bk_{i}"
                    )

                    current_type = item.get("doc_type", "その他")
                    type_options = [
                        "手引き",
                        "残高証明",
                        "取引明細",
                        "顧客勘定元帳",
                        "相続届",
                        "その他",
                    ]
                    idx = (
                        type_options.index(current_type)
                        if current_type in type_options
                        else 4
                    )
                    new_type = c4.selectbox(
                        "種別", type_options, index=idx, key=f"dt_{i}"
                    )

                    configs.append(
                        {
                            **item,
                            "name": new_name,
                            "bank_name": new_bank,
                            "doc_type": new_type,
                        }
                    )

                if st.form_submit_button("✅ 登録実行"):
                    vector_store = AIFactory.get_vector_store()
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=800, chunk_overlap=100
                    )
                    cnt = 0
                    today = datetime.now().strftime("%Y%m%d")

                    templates_dir = os.path.join(ROOT_DIR, "data", "templates")
                    os.makedirs(templates_dir, exist_ok=True)

                    for c in configs:
                        fname = f"{c['name']}_{today}.pdf"
                        save_path = os.path.join(templates_dir, fname)

                        with open(save_path, "wb") as f:
                            f.write(c["data"])

                        # 【修正】case_idを渡して登録
                        db_manager.register_file_hash(
                            c["hash"], fname, c["doc_type"], case_id=c.get("case_id")
                        )

                        enriched_text = f"【ファイル名】{fname}\n【銀行名】{c['bank_name']}\n【書類種別】{c['doc_type']}\n\n{c['text']}"
                        chunks = splitter.split_text(enriched_text)

                        metadatas = [
                            {
                                "source": fname,
                                "path": save_path,
                                "security_level": c["type"],
                                "bank_name": c["bank_name"],
                                "doc_type": c["doc_type"],
                            }
                            for _ in chunks
                        ]

                        vector_store.add_texts(chunks, metadatas=metadatas)
                        cnt += 1

                    st.success(f"{cnt}件登録しました！")
                    st.session_state.upload_stage = []

    # --- Tab 3: データ管理 ---
    with tab3:
        st.subheader("🗑️ 登録済みファイルの管理")
        files = db_manager.get_all_files()

        if not files:
            st.info("登録されているファイルはありません。")
        else:
            df_files = pd.DataFrame(files)
            # 【修正】カラムに「案件」を追加
            df_files.columns = [
                "ファイル名",
                "登録日時",
                "ハッシュ値",
                "書類種別",
                "案件",
                "doc_type_raw",  # 隠しカラム (キー用)
                "uploaded_at_raw",  # 隠しカラム (ソート用)
            ]
            st.dataframe(
                df_files[["登録日時", "案件", "書類種別", "ファイル名"]],
                use_container_width=True,
            )

            st.divider()
            st.warning("【削除エリア】")
            selected_file = st.selectbox(
                "削除するファイルを選択", [f["filename"] for f in files]
            )

            if st.button("選択したファイルを完全に削除する"):
                templates_dir = os.path.join(ROOT_DIR, "data", "templates")
                target_path = os.path.join(templates_dir, selected_file)

                if os.path.exists(target_path):
                    os.remove(target_path)

                db_manager.delete_file_registry(selected_file)
                st.success(f"{selected_file} を削除しました。再登録してください。")
                time.sleep(1)
                st.rerun()


if __name__ == "__main__":
    main()
```

## File: src/legal_system/__init__.py
```python

```

## File: src/legal.egg-info/dependency_links.txt
```

```

## File: src/__init__.py
```python

```

## File: .python-version
```
3.12.4
```

## File: bank_master.json
```json
[
    {
        "bank_name": "三菱UFJ銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "遺産分割協議書（実印押印）",
            "相続人全員の印鑑証明書（6ヶ月以内）",
            "被相続人の出生から死亡までの連続した戸籍謄本",
            "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
            "【代理人】行政書士証票のコピー（原本照合済）",
            "【代理人】委任状（銀行所定様式または実印押印のある任意様式）"
        ],
        "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
        "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）"
    },
    {
        "bank_name": "ゆうちょ銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "相続確認表（Web入力可）",
            "貯金等相続手続請求書（代理人による署名・実印）",
            "【代理人】特定事務任用カード（提示のみ）",
            "【代理人】委任状（実印押印必須）"
        ],
        "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
        "original_return_policy": "原則として原本還付可。コピーの提出が必要。"
    },
    {
        "bank_name": "三井住友銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "相続手続依頼書（代理人署名）",
            "【代理人】実印および印鑑証明書（6ヶ月以内）",
            "【代理人】行政書士証票または識別カード",
            "被相続人の全戸籍（出生〜死亡）"
        ],
        "notes": "※Web予約をしてからの来店が推奨される。",
        "original_return_policy": "原本還付可"
    }
]
```

## File: create_rule_master.py
```python
import json
from typing import Any, Dict, List

# プロジェクトルートに作成される手続要件マスタ
DATA_FILE: str = "bank_master.json"


def create_initial_bank_data() -> List[Dict[str, Any]]:
    """
    行政書士業務に特化した銀行マスタデータの初期セットを生成する。
    """
    banks = [
        {
            "bank_name": "三菱UFJ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "遺産分割協議書（実印押印）",
                "相続人全員の印鑑証明書（6ヶ月以内）",
                "被相続人の出生から死亡までの連続した戸籍謄本",
                "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
                "【代理人】行政書士証票のコピー（原本照合済）",
                "【代理人】委任状（銀行所定様式または実印押印のある任意様式）",
            ],
            "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
            "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）",
        },
        {
            "bank_name": "ゆうちょ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続確認表（Web入力可）",
                "貯金等相続手続請求書（代理人による署名・実印）",
                "【代理人】特定事務任用カード（提示のみ）",
                "【代理人】委任状（実印押印必須）",
            ],
            "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
            "original_return_policy": "原則として原本還付可。コピーの提出が必要。",
        },
        {
            "bank_name": "三井住友銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続手続依頼書（代理人署名）",
                "【代理人】実印および印鑑証明書（6ヶ月以内）",
                "【代理人】行政書士証票または識別カード",
                "被相続人の全戸籍（出生〜死亡）",
            ],
            "notes": "※Web予約をしてからの来店が推奨される。",
            "original_return_policy": "原本還付可",
        },
    ]
    return banks


def save_bank_master(data: List[Dict[str, Any]]) -> None:
    try:
        # プロジェクトルートに保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 成功: '{DATA_FILE}' を作成しました。")
        print("   これで『01_銀行手続要件_確認』ページが動作します。")
    except IOError as e:
        print(f"❌ エラー: ファイルの書き込みに失敗しました。詳細: {e}")


if __name__ == "__main__":
    bank_data = create_initial_bank_data()
    save_bank_master(bank_data)
```

## File: export_code.py
```python
import subprocess


def run_repomix():
    print("🚀 ソースコードの集約を開始します...")

    # Repomixを実行するコマンド
    # --style markdown : Geminiが読みやすいマークダウン形式で出力
    # --ignore "**/*.json,**/*.lock" : 不要なファイルを除外（必要に応じて追加）
    command = "npx -y repomix --style markdown"

    try:
        # コマンドを実行
        # shell=True はWindows/Mac両対応のため
        subprocess.run(command, shell=True, check=True)

        print("\n✅ 完了しました！")
        print("📁 'repomix-output.md' というファイルが作成されています。")
        print("🤖 これをGeminiにアップロードしてください。")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    run_repomix()
```

## File: README.md
```markdown
# legal-rag-project

Describe your project here.
```

## File: register_existing_templates.py
```python
import hashlib
import os
import sys

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager


def calculate_file_hash(file_path: str) -> str:
    """ファイルのMD5ハッシュを計算"""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return hashlib.md5(file_bytes).hexdigest()


def main():
    print("🚀 既存テンプレートのDB登録を開始します...")

    # パス設定
    base_dir = os.getcwd()
    template_dir = os.path.join(base_dir, "data", "templates")

    if not os.path.exists(template_dir):
        print(f"❌ フォルダが見つかりません: {template_dir}")
        return

    # DB接続
    db = DatabaseManager()

    # 登録処理
    files = [f for f in os.listdir(template_dir) if f.lower().endswith(".pdf")]
    count = 0

    print(f"📂 対象フォルダ: {template_dir}")
    print(f"📄 PDFファイル数: {len(files)}")

    for filename in files:
        file_path = os.path.join(template_dir, filename)
        file_hash = calculate_file_hash(file_path)

        # 既に登録済みかチェック
        if db.is_file_registered(file_hash):
            print(f"SKIP (登録済): {filename}")
            continue

        # 簡易的な種別判定 (ファイル名から推測)
        doc_type = "その他"
        if "残高証明" in filename:
            doc_type = "残高証明"
        elif "相続届" in filename or "手続" in filename:
            doc_type = "相続届"
        elif "委任状" in filename:
            doc_type = "委任状"

        # DBへ登録
        db.register_file_hash(file_hash=file_hash, filename=filename, doc_type=doc_type)
        print(f"✅ REGISTERED: {filename} ({doc_type})")
        count += 1

    print("------------------------------------------------")
    print(f"🎉 完了しました。新規登録: {count} 件")
    print("画面をリロードして確認してください。")


if __name__ == "__main__":
    main()
```

## File: run_watcher.py
```python
import os
import sys
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.data_sync import DataSyncEngine

# 監視対象フォルダ (ダウンロードフォルダなど)
# ※Windowsのダウンロードフォルダの例
WATCH_DIR = os.path.expanduser("~/Downloads")


class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        # ファイルが作成されたとき
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)

        # "G"で始まり ".json" で終わるファイルのみ対象 (例: G0001.json)
        if filename.startswith("G") and filename.endswith(".json"):
            print(f"📥 検知: {filename}")
            # ファイル書き込み完了まで少し待つ
            time.sleep(1)
            self.syncer.sync_from_kintone_json(event.src_path)


if __name__ == "__main__":
    print(f"👀 監視を開始しました: {WATCH_DIR}")
    print("   'Gxxxx.json' というファイルがダウンロードされると自動で取り込みます。")

    event_handler = JsonHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

## File: update_bank_master.py
```python
# File: update_bank_master.py

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3

# SSL警告を非表示にする（ローカル開発用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 設定エリア (絶対パス化)
# ==========================================
ROOT_DIR = Path(__file__).parent.absolute()
BASE_DIR = ROOT_DIR / "data" / "zengin"
BRANCH_DIR = BASE_DIR / "branches"
STATE_FILE = BASE_DIR / "last_updated.json"

# API & URL
REPO_API_URL = (
    "https://api.github.com/repos/zengin-code/source-data/commits?path=data&per_page=1"
)
BANKS_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/banks.json"
)
BRANCH_BASE_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/branches/"
)


def download_data(progress_callback=None):
    print(f"🚀 [Start] データ保存先を確認: {BASE_DIR}")

    # フォルダ作成
    os.makedirs(BRANCH_DIR, exist_ok=True)

    # 1. 銀行一覧
    if progress_callback:
        progress_callback(0, 100, "銀行一覧を取得中...")

    try:
        # verify=False でSSLエラーを回避
        print(f"connecting to {BANKS_URL} ...")
        resp = requests.get(BANKS_URL, timeout=15, verify=False)
        resp.raise_for_status()
        banks = resp.json()

        with open(BASE_DIR / "banks.json", "w", encoding="utf-8") as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)

        print(f"✅ 銀行マスタ保存完了: {len(banks)}件")

    except Exception as e:
        print(f"❌ 銀行一覧の取得に失敗: {e}")
        return False, None

    # 2. 支店データ
    total_banks = len(banks)
    print(f"🔄 支店データ取得開始: 対象 {total_banks} 行")

    success_count = 0
    # 全件取得（エラーが出ても止まらないようにする）
    for i, bank_code in enumerate(list(banks.keys())):
        branch_url = f"{BRANCH_BASE_URL}{bank_code}.json"
        save_path = BRANCH_DIR / f"{bank_code}.json"

        try:
            r = requests.get(branch_url, timeout=10, verify=False)
            if r.status_code == 200:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f, ensure_ascii=False, indent=2)
                success_count += 1

            # プログレスバー更新 (10件に1回更新で負荷軽減)
            if i % 10 == 0 and progress_callback:
                progress_callback(i + 1, total_banks, f"支店データ取得中: {bank_code}")

            # サーバー負荷軽減のためのスリープ
            time.sleep(0.01)

        except Exception:
            # 個別の失敗は無視して続行
            pass

    print(f"✅ 全ダウンロード完了 (成功: {success_count}件)")
    return True, banks


# --- 以下の関数は変更なし ---
def get_remote_last_commit_date():
    try:
        resp = requests.get(REPO_API_URL, timeout=10, verify=False)
        if resp.status_code == 200:
            return resp.json()[0]["commit"]["committer"]["date"]
    except:
        pass
    return None


def load_local_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_commit_date": ""}


def save_local_state(commit_date):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "last_commit_date": commit_date,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    download_data()
```

## File: src/legal_system/core/config.py
```python
# src/legal_system/core/config.py

import os
import random
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# ==========================================
# 1. パス設定 (モジュールレベル定数)
# ==========================================
# プロジェクトルートの特定
# このファイル(config.py)は src/legal_system/core/ にあるため
# parents[0]=core, parents[1]=legal_system, parents[2]=src, parents[3]=ROOT
BASE_DIR = Path(__file__).resolve().parents[3]

# データディレクトリ (data/)
DATA_DIR = BASE_DIR / "data"

# データベース保存先
DB_DIR_CHROMA = DATA_DIR / "db" / "chroma" / "local_rag_db"
DB_FILE_SQLITE = DATA_DIR / "db" / "sql" / "legal_system.db"

# データ一時保存先
DATA_DIR_TEMPLATES = DATA_DIR / "templates"
VECTOR_STORE_PATH = DB_DIR_CHROMA

# 銀行RAGシステム用パス設定
RULES_DIR = DATA_DIR / "rules"
BANK_MASTER_PATH = RULES_DIR / "bank_master.csv"
COMPANY_RULES_PATH = RULES_DIR / "company_rules.txt"


# ==========================================
# 2. 設定管理クラス (Config)
# ==========================================
class Config:
    """
    システム全体の設定定数を管理するクラス。
    すべての設定値はこのクラスを経由してアクセスします (例: Config.GOOGLE_MODEL_NAME)。
    """

    # --- パス設定のラップ (ここがエラー原因でした) ---
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR

    # ★追加: DatabaseManagerが参照するための定義
    DB_FILE_SQLITE = DB_FILE_SQLITE

    # その他パス
    BANK_MASTER_PATH = BANK_MASTER_PATH
    COMPANY_RULES_PATH = COMPANY_RULES_PATH
    VECTOR_STORE_PATH = VECTOR_STORE_PATH
    TEMPLATES_DIR = DATA_DIR_TEMPLATES

    # --- AIモデル設定 ---
    # Gemini モデル名
    GOOGLE_MODEL_NAME = "models/gemini-2.5-flash-lite"

    # RAG用設定
    MODEL_NAME = "gemini-2.5-flash-lite"  # engines.py互換用
    EMBEDDING_MODEL = "models/embedding-001"
    TEMPERATURE = 0.0

    # APIキー管理
    _keys_str = os.getenv("GOOGLE_API_KEYS", "")
    GOOGLE_API_KEYS: List[str] = [k.strip() for k in _keys_str.split(",") if k.strip()]

    # リストが空で、単一のキーがある場合はそれを使用
    if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
        GOOGLE_API_KEYS = [os.getenv("GOOGLE_API_KEY")]

    @classmethod
    def validate_paths(cls) -> None:
        """必須ファイルの存在確認"""
        # ディレクトリ作成
        if not cls.DATA_DIR.exists():
            os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not cls.TEMPLATES_DIR.exists():
            os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)

        # ファイルチェック（存在しなくても起動はさせるがログに残す等）
        missing = []
        if (
            not cls.BANK_MASTER_PATH.exists()
            and cls.BANK_MASTER_PATH.name != "bank_master.csv"
        ):
            missing.append(str(cls.BANK_MASTER_PATH))

        if missing:
            print(f"⚠️ 一部の設定ファイルが見つかりません: {missing}")


# ==========================================
# 3. キー管理クラス (KeyManager)
# ==========================================
class KeyManager:
    """
    APIキーの取得とローテーションを管理するクラス
    Engines.py 等から呼び出されます。
    """

    @staticmethod
    def get_next_key() -> str:
        """
        利用可能なAPIキーを Config から取得して返します。
        複数ある場合はランダムに選択します（簡易ローテーション）。
        """
        keys = Config.GOOGLE_API_KEYS

        if not keys:
            # 環境変数を再確認
            env_key = os.getenv("GOOGLE_API_KEY")
            if env_key:
                return env_key
            raise ValueError(
                "❌ 有効な Google API Key が見つかりません。.env または環境変数を確認してください。"
            )

        return random.choice(keys)
```

## File: src/legal_system/core/database_manager.py
```python
# File: src/legal_system/core/database_manager.py

import getpass
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import scoped_session, sessionmaker

# テーブル定義のインポート
from src.legal_system.models.tables import (
    AuditLog,
    Base,
    Case,
    Coordinate,
    FileRegistry,
    User,
)

# Configのインポート
from .config import Config


class DatabaseManager:
    """
    システムのデータベース操作を一元管理するクラス
    """

    def __init__(self):
        # DBパスの解決
        self.db_path = str(Config.DB_FILE_SQLITE)

        # ディレクトリ作成
        db_dir = os.path.dirname(self.db_path)
        os.makedirs(db_dir, exist_ok=True)

        # SQLiteエンジン作成
        self.engine = create_engine(
            f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False}
        )

        # テーブル作成 (既存の場合はスキップ、変更がある場合はALTERが必要だが今回は再作成推奨)
        Base.metadata.create_all(self.engine)

        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def _get_session(self):
        return self.Session()

    # ---------------------------------------------------------
    # ユーザー管理
    # ---------------------------------------------------------
    def get_current_user_info(self) -> Dict[str, str]:
        pc_user = getpass.getuser()
        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=pc_user).first()
            if user:
                return {
                    "id": user.windows_id,
                    "name": user.name,
                    "dept": user.department if user.department else "",
                    "phone": user.phone if user.phone else "",
                }
            else:
                default_name = f"{pc_user}(未登録)"
                default_dept = "所属未定"
                new_user = User(
                    windows_id=pc_user,
                    name=default_name,
                    department=default_dept,
                    role="Operator",
                )
                session.add(new_user)
                session.commit()
                return {
                    "id": pc_user,
                    "name": default_name,
                    "dept": default_dept,
                    "phone": "",
                }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {"id": pc_user, "name": pc_user, "dept": "Error", "phone": ""}
        finally:
            session.close()

    def register_user(
        self, windows_id: str, display_name: str, department: str, phone: str
    ):
        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=windows_id).first()
            if user:
                user.name = display_name
                user.department = department
                user.phone = phone
                user.updated_at = datetime.now()
            else:
                user = User(
                    windows_id=windows_id,
                    name=display_name,
                    department=department,
                    phone=phone,
                    role="Operator",
                )
                session.add(user)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---------------------------------------------------------
    # ログ管理
    # ---------------------------------------------------------
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        session = self._get_session()
        try:
            db_user = session.query(User).filter_by(windows_id=user_id).first()
            u_id = db_user.id if db_user else None
            log = AuditLog(
                user_id=u_id,
                action_type=action,
                target=target,
                details=details,
                timestamp=datetime.now(),
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---------------------------------------------------------
    # ファイル管理（修正箇所: case_id引数を追加）
    # ---------------------------------------------------------
    def is_file_registered(self, file_hash: str) -> bool:
        session = self._get_session()
        try:
            exists = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            return exists is not None
        finally:
            session.close()

    def register_file_hash(
        self,
        file_hash: str,
        filename: str,
        doc_type: str = "その他",
        case_id: Optional[int] = None,  # ← ★ここが不足していました
    ):
        """ファイルの登録情報を保存・更新"""
        session = self._get_session()
        try:
            file_reg = (
                session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            )
            if file_reg:
                file_reg.filename = filename
                file_reg.doc_type = doc_type
                # case_id が指定されている場合のみ更新（紐付け解除ロジックが必要なら別途考慮）
                if case_id is not None:
                    file_reg.case_id = case_id
                file_reg.registered_at = datetime.now()
            else:
                file_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=filename,
                    doc_type=doc_type,
                    case_id=case_id,
                    registered_at=datetime.now(),
                )
                session.add(file_reg)
            session.commit()
        except Exception as e:
            print(f"Error registering file: {e}")
            session.rollback()
        finally:
            session.close()

    def get_all_files(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            results = (
                session.query(FileRegistry, Case)
                .outerjoin(Case, FileRegistry.case_id == Case.case_id)
                .order_by(desc(FileRegistry.registered_at))
                .all()
            )
            output = []
            for f, c in results:
                case_label = f"{c.case_number}" if c else "（共通雛形）"
                output.append(
                    {
                        "filename": f.filename,
                        "date": f.registered_at.strftime("%Y-%m-%d %H:%M:%S")
                        if f.registered_at
                        else "",
                        "hash": f.file_hash,
                        "type": f.doc_type if f.doc_type else "その他",
                        "case": case_label,
                        "doc_type": f.doc_type,
                        "uploaded_at": f.registered_at,
                    }
                )
            return output
        finally:
            session.close()

    def delete_file_registry(self, filename: str):
        session = self._get_session()
        try:
            session.query(FileRegistry).filter_by(filename=filename).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---------------------------------------------------------
    # 座標管理
    # ---------------------------------------------------------
    def register_coordinate(
        self,
        file_hash,
        label,
        x,
        y,
        page_number=1,
        description="",
        font_size=10,
        color="black",
        test_value="",
    ):
        session = self._get_session()
        try:
            coord = (
                session.query(Coordinate)
                .filter_by(file_hash=file_hash, label=label)
                .first()
            )
            if not coord:
                coord = Coordinate(file_hash=file_hash, label=label)
                session.add(coord)

            coord.x_point = x
            coord.y_point = y
            coord.page_number = page_number
            coord.description = description
            coord.font_size = font_size
            coord.color = color
            coord.value = test_value
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def get_coordinates_by_hash(self, file_hash: str) -> List[Dict]:
        session = self._get_session()
        try:
            coords = session.query(Coordinate).filter_by(file_hash=file_hash).all()
            return [
                {
                    "id": c.id,
                    "label": c.label,
                    "x": c.x_point,
                    "y": c.y_point,
                    "page": c.page_number,
                    "desc": c.description,
                    "font_size": c.font_size,
                    "color": c.color,
                    "value": c.value,
                }
                for c in coords
            ]
        finally:
            session.close()

    def update_coordinate_direct(self, coord_id: int, updates: Dict):
        session = self._get_session()
        try:
            coord = session.query(Coordinate).filter_by(id=coord_id).first()
            if coord:
                for k, v in updates.items():
                    if k == "x":
                        coord.x_point = v
                    elif k == "y":
                        coord.y_point = v
                    elif k == "desc":
                        coord.description = v
                    elif hasattr(coord, k):
                        setattr(coord, k, v)
                    # 簡易実装のため一部省略、必要なら詳細マッピングを追加
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def delete_coordinate(self, coordinate_id: int):
        session = self._get_session()
        try:
            session.query(Coordinate).filter_by(id=coordinate_id).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
```

## File: src/legal_system/models/tables.py
```python
# ファイル名: src/legal_system/models/tables.py

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

# ==========================================
# 0. データベース基盤設定 (Base Definition)
# ==========================================
Base = declarative_base()

# ==========================================
# 1. 共通マスタ (Core Master Data)
# ==========================================


class User(Base):
    """
    ユーザー・担当者マスタ
    RAGシステムの「利用者」と、業務システムの「担当者」を兼ねます。
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # RAGのpc_username と 業務のwindows_id を統合
    windows_id = Column(String, unique=True, nullable=False, comment="PCログインID")
    name = Column(String, nullable=False, comment="表示名")
    role = Column(String, default="Operator", comment="権限: Manager/Operator")

    # --- RAG用拡張カラム ---
    department = Column(String, nullable=True, comment="所属部署")
    phone = Column(String, nullable=True, comment="内線・連絡先")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class BankMaster(Base):
    """
    銀行マスタ
    業務管理の「振込先」と、RAGの「検索対象」を兼ねます。
    """

    __tablename__ = "bank_master"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    bank_code = Column(String, nullable=False)

    # --- RAG検索用拡張 (CSVの内容をDB化) ---
    seal_cert_limit = Column(String, comment="印鑑証明期限")  # 例: 3ヶ月以内
    id_verify_rule = Column(String, comment="本人確認書類")  # 例: 原本提示
    transfer_rule = Column(String, comment="振込ルール")  # 例: 引落しのみ
    remarks = Column(Text, comment="特記事項")  # RAGが参照する備考

    __table_args__ = (
        UniqueConstraint("bank_name", name="_bank_name_uc"),
        UniqueConstraint("bank_code", name="_bank_code_uc"),
    )

    # リレーションシップ定義
    branches = relationship(
        "BranchMaster", back_populates="bank_ref", cascade="all, delete-orphan"
    )
    financial_assets = relationship("FinancialAsset", back_populates="bank_ref")
    aliases = relationship(
        "BankAlias", back_populates="bank_ref", cascade="all, delete-orphan"
    )

    # RAGのファイルとも紐付け (銀行ごとの手引き等)
    rag_files = relationship("FileRegistry", back_populates="bank_ref")


class BankAlias(Base):
    """
    銀行名ゆらぎ吸収用テーブル
    OCRやAIが「三菱UFJ」「MUFG」などを同一視するために使用します。
    """

    __tablename__ = "bank_aliases"

    id = Column(Integer, primary_key=True, index=True)
    alias_name = Column(String, unique=True, index=True, nullable=False)
    bank_id = Column(
        Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False
    )

    bank_ref = relationship("BankMaster", back_populates="aliases")


class BranchMaster(Base):
    """支店マスタ"""

    __tablename__ = "branch_master"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(
        Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False
    )
    branch_name = Column(String, nullable=False)
    branch_code = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("bank_id", "branch_code", name="_bank_branch_code_uc"),
    )

    bank_ref = relationship("BankMaster", back_populates="branches")
    financial_assets = relationship("FinancialAsset", back_populates="branch_ref")


class AccountTypeMaster(Base):
    """口座種類マスタ (普通、定期、当座など)"""

    __tablename__ = "account_type_master"

    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String, unique=True, nullable=False)

    financial_assets = relationship("FinancialAsset", back_populates="account_type_ref")


class DocumentType(Base):
    """書類種別マスタ (戸籍謄本、印鑑証明書など)"""

    __tablename__ = "document_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class ShippingMethod(Base):
    """郵送方法マスタ (簡易書留、レターパックなど)"""

    __tablename__ = "shipping_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tracking_base_url = Column(String, nullable=False)
    estimated_days = Column(Integer)


class SubmissionDocType(Base):
    """提出書類種別マスタ"""

    __tablename__ = "submission_doc_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


# ==========================================
# 2. RAGシステム用テーブル (Knowledge Base)
# ==========================================


class AuditLog(Base):
    """
    AI検索・操作ログ
    「誰が」「いつ」「何を検索したか」を記録します。
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)

    # Userテーブルと紐付けることで、担当者ごとの利用履歴を管理
    user_id = Column(Integer, ForeignKey("users.id"))

    action_type = Column(String)  # SEARCH, UPLOAD, DELETE
    target = Column(String)  # ファイル名や検索クエリ
    details = Column(Text)  # 詳細内容

    user = relationship("User")


class FileRegistry(Base):
    """
    RAG雛形ファイルの管理テーブル
    VectorStore (ChromaDB) 上のデータと物理ファイルを紐付けます。
    """

    __tablename__ = "file_registry"

    file_hash = Column(String, primary_key=True)  # MD5ハッシュ (重複防止)
    filename = Column(String, nullable=False)

    # 銀行マスタと紐付けることで、銀行ごとの書類検索を高速化
    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=True)

    # 【追加】案件(Case)との紐付け (NULL許容 = 共通テンプレート)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)

    doc_type = Column(String, default="その他")  # 手引き, 委任状, 残高証明...
    registered_at = Column(DateTime, default=datetime.now)
    security_level = Column(String, default="general")  # general / secure

    # 物理ファイルのパス (相対パス推奨)
    file_path = Column(String)

    # 登録者
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    bank_ref = relationship("BankMaster", back_populates="rag_files")

    # 【追加】案件リレーション
    case_ref = relationship("Case")
    registrar = relationship("User")


# ==========================================
# 3. 個人情報管理テーブル (Contacts & Addresses)
# ==========================================


class Address(Base):
    """住所マスタ"""

    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    zip_code = Column(String)
    prefecture = Column(String, nullable=False)
    city_ward_town = Column(String)
    street_address = Column(String, nullable=False)
    building_name = Column(String)

    deceased_history = relationship(
        "D_AddressHistory", back_populates="address", cascade="all, delete-orphan"
    )
    heir_history = relationship(
        "H_AddressHistory", back_populates="address", cascade="all, delete-orphan"
    )


class Contact(Base):
    """連絡先マスタ (電話、メール)"""

    __tablename__ = "contact"
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    type = Column(String, nullable=False)  # PHONE, EMAIL
    sub_type = Column(String)


class Deceased(Base):
    """被相続人 (亡くなった方)"""

    __tablename__ = "deceased"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, unique=True)
    name_last = Column(String)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    hometown = Column(String)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    relationship_type = Column(String)
    last_address_id = Column(Integer, ForeignKey("address.id"))

    heirs = relationship(
        "Heir", back_populates="deceased", cascade="all, delete-orphan"
    )
    address_links = relationship(
        "D_AddressHistory", back_populates="deceased", cascade="all, delete-orphan"
    )
    contact_links = relationship(
        "D_ContactLink", back_populates="deceased", cascade="all, delete-orphan"
    )
    case = relationship("Case", back_populates="deceased_ref")
    last_address = relationship("Address", foreign_keys=[last_address_id])


class Heir(Base):
    """相続人"""

    __tablename__ = "heirs"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    name_last = Column(String, nullable=False)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    hometown = Column(String)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)  # 代襲相続などの場合用
    relationship_type = Column(String)
    is_contracting_party = Column(Boolean, default=False)

    deceased = relationship("Deceased", back_populates="heirs")
    address_links = relationship(
        "H_AddressHistory", back_populates="heir", cascade="all, delete-orphan"
    )
    contact_links = relationship(
        "H_ContactLink", back_populates="heir", cascade="all, delete-orphan"
    )


# --- リンクテーブル群 (中間テーブル) ---


class D_AddressHistory(Base):
    __tablename__ = "d_address_history"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_last_address = Column(Boolean, nullable=False, default=False)
    deceased = relationship("Deceased", back_populates="address_links")
    address = relationship("Address", back_populates="deceased_history")


class H_AddressHistory(Base):
    __tablename__ = "h_address_history"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_current_address = Column(Boolean, nullable=False, default=False)
    heir = relationship("Heir", back_populates="address_links")
    address = relationship("Address", back_populates="heir_history")


class D_ContactLink(Base):
    __tablename__ = "d_contact_link"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    deceased = relationship("Deceased", back_populates="contact_links")
    contact = relationship("Contact")


class H_ContactLink(Base):
    __tablename__ = "h_contact_link"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    heir = relationship("Heir", back_populates="contact_links")
    contact = relationship("Contact")


# ==========================================
# 4. 案件ハブテーブル (Core Case Management)
# ==========================================


class CaseStatus(Base):
    """案件ステータス (受任、調査中、完了など)"""

    __tablename__ = "case_statuses"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    order_num = Column(Integer)


class Case(Base):
    """相続案件テーブル"""

    __tablename__ = "cases"
    case_id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)  # G0001
    folder_path = Column(String)
    client_name = Column(String, nullable=False)
    client_name_kana = Column(String)

    manager_id = Column(Integer, ForeignKey("users.id"))
    operator_id = Column(Integer, ForeignKey("users.id"))
    current_status_id = Column(Integer, ForeignKey("case_statuses.id"))

    # 金額・契約情報
    fee_contract_amount = Column(Float, default=0.0)
    deposit_required_amount = Column(Float, default=0.0)
    deposit_paid_amount = Column(Float, default=0.0)
    is_paid_in_full = Column(Boolean, default=False)
    certs_of_seal_count = Column(Integer, default=0)
    power_of_attorney_count = Column(Integer, default=0)

    # 日付関連
    date_of_death = Column(Date)
    interview_date = Column(DateTime)
    contract_date = Column(Date)
    tax_deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

    # 紹介情報・SOL連携
    sol_case_number = Column(String, nullable=True, comment="SOL案件No")
    introduction_date = Column(Date, nullable=True, comment="紹介日")
    referral_sec_branch_name = Column(String, nullable=True, comment="証券会社支店名")
    referral_sec_rep_name = Column(String, nullable=True, comment="証券会社担当者名")
    consent_date = Column(Date, nullable=True, comment="同意書日付")

    # リレーション定義
    manager = relationship("User", foreign_keys=[manager_id])
    operator = relationship("User", foreign_keys=[operator_id])
    status_ref = relationship("CaseStatus")

    deceased_ref = relationship(
        "Deceased", back_populates="case", uselist=False, cascade="all, delete-orphan"
    )
    financial_assets = relationship(
        "FinancialAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    real_estates = relationship(
        "RealEstateAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task", back_populates="case_ref", cascade="all, delete-orphan"
    )
    expenses = relationship(
        "Expense", back_populates="case_ref", cascade="all, delete-orphan"
    )
    submitted_docs = relationship(
        "CaseSubmissionDoc", back_populates="case_ref", cascade="all, delete-orphan"
    )
    contact_logs = relationship(
        "ContactLog", back_populates="case_ref", cascade="all, delete-orphan"
    )
    insurance_assets = relationship(
        "InsuranceAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    other_assets = relationship(
        "OtherAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    liabilities = relationship(
        "Liability", back_populates="case_ref", cascade="all, delete-orphan"
    )
    contact_points = relationship(
        "CaseContactPoint", back_populates="case_ref", cascade="all, delete-orphan"
    )


class CaseContactPoint(Base):
    """案件ごとの連絡窓口"""

    __tablename__ = "case_contact_points"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_person_name = Column(String)
    relationship_to_client = Column(String)
    address_id = Column(Integer, ForeignKey("address.id"))
    contact_id = Column(Integer, ForeignKey("contact.id"))

    is_primary_contact = Column(Boolean, default=False)
    is_primary_mail_send_destination = Column(Boolean, default=False)

    case_ref = relationship("Case", back_populates="contact_points")
    address_ref = relationship("Address")
    contact_ref = relationship("Contact")


# ==========================================
# 5. タスク管理 (Task Management)
# ==========================================


class TaskTemplate(Base):
    """タスク雛形"""

    __tablename__ = "task_templates"
    template_id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    default_due_days = Column(Integer, default=1)
    is_manager_task = Column(Boolean, default=False)
    depends_on_template_id = Column(Integer, ForeignKey("task_templates.template_id"))

    depends_on = relationship("TaskTemplate", remote_side=[template_id])


class Task(Base):
    """実行タスク"""

    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    template_id = Column(Integer, ForeignKey("task_templates.template_id"))
    description = Column(String, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)

    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    template_ref = relationship("TaskTemplate")
    document_logs = relationship(
        "TaskDocumentLog", back_populates="task_ref", cascade="all, delete-orphan"
    )
    case_ref = relationship("Case", back_populates="tasks")


class TaskDocumentLog(Base):
    """書類郵送ログ"""

    __tablename__ = "task_document_logs"
    log_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    shipping_method_id = Column(
        Integer, ForeignKey("shipping_methods.id"), nullable=False
    )
    sent_date = Column(DateTime, nullable=False)
    sent_to = Column(String, nullable=False)
    tracking_number = Column(String, unique=True)
    is_returned = Column(Boolean, default=False)

    document_type = relationship("DocumentType")
    shipping_method = relationship("ShippingMethod")
    task_ref = relationship("Task", back_populates="document_logs")


# ==========================================
# 6. 財産・トランザクション詳細テーブル
# ==========================================


class FinancialAsset(Base):
    """金融資産 (預貯金)"""

    __tablename__ = "financial_asset"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(
        Integer, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False
    )
    asset_type = Column(String, default="BANK")

    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch_master.id"))
    account_type_id = Column(
        Integer, ForeignKey("account_type_master.id"), nullable=True
    )

    account_number = Column(String)
    balance = Column(Float, default=0.0)
    status = Column(String, default="未確認")

    case_ref = relationship("Case", back_populates="financial_assets")
    bank_ref = relationship("BankMaster", back_populates="financial_assets")
    branch_ref = relationship("BranchMaster", back_populates="financial_assets")
    account_type_ref = relationship(
        "AccountTypeMaster", back_populates="financial_assets"
    )


class RealEstateAsset(Base):
    """不動産資産"""

    __tablename__ = "real_estate_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)

    property_type = Column(
        String, default="Land"
    )  # Land(土地) / Building(建物) / Condo(区分所有)

    # 登記簿上の表示
    location = Column(String, comment="所在")
    lot_number = Column(String, comment="地番")
    land_category = Column(String, comment="地目")
    land_area = Column(Float, comment="地積")
    house_number = Column(String, comment="家屋番号")
    structure = Column(String, comment="構造")
    floor_area = Column(String, comment="床面積")

    ownership_share = Column(String, nullable=True, comment="被相続人の持分")

    registry_pdf_path = Column(String, nullable=True, comment="登記情報PDFパス")
    registry_image_path = Column(String, nullable=True, comment="Word貼付用画像パス")

    case_ref = relationship("Case", back_populates="real_estates")


class InsuranceAsset(Base):
    """保険資産"""

    __tablename__ = "insurance_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    insurance_company = Column(String)
    policy_number = Column(String)
    estimated_value = Column(Float)

    case_ref = relationship("Case", back_populates="insurance_assets")


class OtherAsset(Base):
    """その他の資産 (株式、自動車など)"""

    __tablename__ = "other_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    estimated_value = Column(Float)

    case_ref = relationship("Case", back_populates="other_assets")


class Liability(Base):
    """負債・葬儀費用"""

    __tablename__ = "liability"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    is_debt = Column(Boolean, nullable=False, default=True)
    description = Column(String)
    amount = Column(Float, nullable=False)
    is_funeral_cost = Column(Boolean, nullable=False, default=False)

    case_ref = relationship("Case", back_populates="liabilities")


class Expense(Base):
    """立替経費"""

    __tablename__ = "expenses"
    expense_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    amount = Column(Float, nullable=False)
    expense_date = Column(Date)

    case_ref = relationship("Case", back_populates="expenses")


class ContactLog(Base):
    """対応履歴 (電話メモなど)"""

    __tablename__ = "contact_logs"
    log_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_content = Column(String, nullable=False)
    is_thank_you_payment = Column(Boolean, default=False)

    case_ref = relationship("Case", back_populates="contact_logs")


class CaseSubmissionDoc(Base):
    """提出書類管理"""

    __tablename__ = "case_submission_docs"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)

    case_ref = relationship("Case", back_populates="submitted_docs")


class Coordinate(Base):
    """PDF印字用の座標データモデル"""

    __tablename__ = "coordinates"

    id = Column(Integer, primary_key=True, index=True)

    # どのファイルの座標かを識別するためのID (ファイルのMD5ハッシュ) 【新規追加】
    file_hash = Column(
        String, index=True, nullable=False, comment="ファイル識別ハッシュ"
    )

    label = Column(String, nullable=False, comment="項目名")
    x_point = Column(Float, nullable=False, comment="X座標")
    y_point = Column(Float, nullable=False, comment="Y座標")
    page_number = Column(Integer, default=1, comment="ページ番号")

    font_size = Column(Integer, default=10, comment="フォントサイズ")
    color = Column(String, default="black", comment="文字色")

    value = Column(String, nullable=True, comment="テスト値")
    description = Column(String, nullable=True, comment="備考")


# ==========================================
# 7. 遺言作成業務テーブル (Will Creation - Future)
# ==========================================


class WillCase(Base):
    """
    遺言作成案件テーブル (将来拡張用)
    相続案件(Case)とは別に管理します。
    """

    __tablename__ = "will_cases"

    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)  # 例: W0001

    # 遺言者情報 (生存顧客のためDeceasedとは区別)
    testator_name = Column(String, nullable=False)
    testator_birth = Column(Date)
    testator_address_id = Column(Integer, ForeignKey("address.id"))

    # 担当者リンク
    manager_id = Column(Integer, ForeignKey("users.id"))

    # 遺言の種類
    will_type = Column(String, default="公正証書", comment="公正証書/自筆証書")
    status = Column(
        String, default="ヒアリング中", comment="起案中/公証役場調整中/完了"
    )

    # 公証役場情報
    notary_office_name = Column(String, nullable=True)
    draft_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 財産配分 (既存のAsset構造とは別に、配分ロジックを持つ)
    allocations = relationship("WillAllocation", back_populates="will_case")


class WillAllocation(Base):
    """
    遺言による財産配分テーブル
    「誰に」「何を」「どれだけ」渡すかを定義します。
    """

    __tablename__ = "will_allocations"

    id = Column(Integer, primary_key=True)
    will_id = Column(Integer, ForeignKey("will_cases.id"), nullable=False)

    # 財産の内容 (テキストで柔軟に記述)
    asset_description = Column(String, nullable=False, comment="例: ○○銀行の預金全額")

    # 受取人 (Beneficiary)
    beneficiary_name = Column(String, nullable=False)
    relationship_to_testator = Column(String, comment="続柄: 妻, 長男, 孫...")

    # 配分詳細
    percentage = Column(Float, nullable=True, comment="割合指定の場合 (例: 0.5)")

    will_case = relationship("WillCase", back_populates="allocations")
```

## File: src/legal_system/main.py
```python
# ファイルパス: src/legal_system/main.py

import subprocess
import sys
from pathlib import Path


def main():
    """
    Streamlitアプリとフォルダ監視(Watcher)を同時に起動するランチャー
    """
    current_dir = Path(__file__).parent.absolute()
    app_path = current_dir / "ui" / "Home.py"

    # プロジェクトルートにある run_watcher.py のパス
    # src/legal_system/main.py -> src/legal_system -> src -> root
    root_dir = current_dir.parent.parent
    watcher_path = root_dir / "run_watcher.py"

    print("🚀 Legal RAG System を起動します...")

    # 1. 監視プロセスをバックグラウンドで起動
    watcher_process = None
    if watcher_path.exists():
        print("👀 フォルダ監視(Watcher)を開始します...")
        watcher_process = subprocess.Popen([sys.executable, str(watcher_path)])
    else:
        print("⚠️ run_watcher.py が見つからないため、監視機能はスキップします。")

    # 2. Streamlitをメインプロセスとして起動 (これが終わるまで待機)
    print(f"📂 UI起動: {app_path}")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 システムを終了します。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        # アプリが終了したら、監視プロセスも終了させる
        if watcher_process:
            print("🛑 監視プロセスを停止中...")
            watcher_process.terminate()
            watcher_process.wait()
            print("✅ 完了")


if __name__ == "__main__":
    main()
```

## File: src/legal.egg-info/top_level.txt
```
__init__
legal_system
```

## File: src/legal.egg-info/PKG-INFO
```
Metadata-Version: 2.4
Name: legal
Version: 0.1.0
Summary: Administrative Scrivener RAG System
Author-email: Admin <admin@example.com>
Requires-Python: >=3.12
Description-Content-Type: text/markdown
Requires-Dist: streamlit>=1.32.0
Requires-Dist: langchain>=0.1.0
Requires-Dist: langchain-community>=0.0.20
Requires-Dist: langchain-core>=0.1.25
Requires-Dist: langchain-google-genai>=0.0.9
Requires-Dist: langchain-huggingface>=0.0.1
Requires-Dist: langchain-chroma>=0.1.0
Requires-Dist: chromadb>=0.4.24
Requires-Dist: pypdf>=4.0.1
Requires-Dist: pdf2image>=1.17.0
Requires-Dist: pytesseract>=0.3.10
Requires-Dist: python-dotenv>=1.0.1
Requires-Dist: pandas>=2.3.3
Requires-Dist: openpyxl>=3.1.2
Requires-Dist: sentence-transformers>=5.2.0
Requires-Dist: numpy<2.0
Requires-Dist: streamlit-image-coordinates>=0.4.0
Requires-Dist: reportlab>=4.4.7
Requires-Dist: watchdog>=6.0.0

# legal-rag-project

Describe your project here.
```

## File: src/legal.egg-info/requires.txt
```
streamlit>=1.32.0
langchain>=0.1.0
langchain-community>=0.0.20
langchain-core>=0.1.25
langchain-google-genai>=0.0.9
langchain-huggingface>=0.0.1
langchain-chroma>=0.1.0
chromadb>=0.4.24
pypdf>=4.0.1
pdf2image>=1.17.0
pytesseract>=0.3.10
python-dotenv>=1.0.1
pandas>=2.3.3
openpyxl>=3.1.2
sentence-transformers>=5.2.0
numpy<2.0
streamlit-image-coordinates>=0.4.0
reportlab>=4.4.7
watchdog>=6.0.0
```

## File: src/legal.egg-info/SOURCES.txt
```
README.md
pyproject.toml
src/__init__.py
src/legal.egg-info/PKG-INFO
src/legal.egg-info/SOURCES.txt
src/legal.egg-info/dependency_links.txt
src/legal.egg-info/requires.txt
src/legal.egg-info/top_level.txt
src/legal_system/__init__.py
src/legal_system/main.py
src/legal_system/core/__init__.py
src/legal_system/core/ai_factory.py
src/legal_system/core/config.py
src/legal_system/core/data_sync.py
src/legal_system/core/database_manager.py
src/legal_system/core/ocr_engine.py
src/legal_system/models/__init__.py
src/legal_system/models/base.py
src/legal_system/models/tables.py
src/legal_system/tools/__init__.py
src/legal_system/tools/bank_input.py
src/legal_system/tools/coord_tool.py
src/legal_system/ui/__init__.py
src/legal_system/ui/app.py
```

## File: .gitignore
```
# --- Python & Rye ---
__pycache__/
*.pyc
.venv/
.rye/

# --- 環境変数 & 機密情報 (絶対にGitにあげない) ---
.env
.streamlit/secrets.toml

# --- データベース & ログ ---
# 監査ログやベクターDBはローカルで生成されるため除外
db/sql/*.db
db/chroma/
*.log

# --- 生成されたファイル・アップロードデータ ---
# テンプレートPDFやアップロードされた一時ファイル
data/templates/*.pdf
data/uploads/
data/generated/
data/zengin

# ※フォントファイル(ipaexg.ttf)などはアプリの動作に必要なので
#   除外せず、Gitに含めるのが一般的です

# --- AI Context / Repomix ---
# ソースコードをまとめたファイルは除外
repomix-output.*
all_code_context.txt

# --- IDE / エディタ ---
.vscode/
.idea/

# --- Python Testing / Caching ---
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage

# --- OS ---
.DS_Store
Thumbs.db

bootstrap.py
```

## File: pyproject.toml
```toml
[project]
name = "legal"
version = "0.1.0"
description = "Administrative Scrivener RAG System"
authors = [
    { name = "Admin", email = "admin@example.com" }
]
dependencies = [
    "streamlit>=1.32.0",
    "langchain>=0.1.0",
    "langchain-community>=0.0.20",
    "langchain-core>=0.1.25",
    "langchain-google-genai>=0.0.9",
    "langchain-huggingface>=0.0.1",
    "langchain-chroma>=0.1.0",
    "chromadb>=0.4.24",
    "pypdf>=4.0.1",
    "pdf2image>=1.17.0",
    "pytesseract>=0.3.10",
    "python-dotenv>=1.0.1",
    "pandas>=2.3.3",
    "openpyxl>=3.1.2",
    "sentence-transformers>=5.2.0",
    "numpy<2.0",
    "streamlit-image-coordinates>=0.4.0",
    "reportlab>=4.4.7",
    "watchdog>=6.0.0",
]
readme = "README.md"
requires-python = ">= 3.12"

[tool.rye]
managed = true
dev-dependencies = []

[tool.rye.scripts]
start = "rye run python src/legal_system/main.py"
pdf = "rye run streamlit run src/legal_system/tools/coord_tool.py"
exp = "rye run python export_code.py"
```

## File: requirements-dev.lock
```
# generated by rye
# use `rye lock` or `rye sync` to update this lockfile
#
# last locked with the following flags:
#   pre: false
#   features: []
#   all-features: false
#   with-sources: false
#   generate-hashes: false
#   universal: false

-e file:.
aiohappyeyeballs==2.6.1
    # via aiohttp
aiohttp==3.13.2
    # via langchain-community
aiosignal==1.4.0
    # via aiohttp
altair==6.0.0
    # via streamlit
annotated-types==0.7.0
    # via pydantic
anyio==4.12.0
    # via google-genai
    # via httpx
    # via watchfiles
attrs==25.4.0
    # via aiohttp
    # via jsonschema
    # via referencing
backoff==2.2.1
    # via posthog
bcrypt==5.0.0
    # via chromadb
blinker==1.9.0
    # via streamlit
build==1.3.0
    # via chromadb
cachetools==6.2.4
    # via google-auth
    # via streamlit
certifi==2025.11.12
    # via httpcore
    # via httpx
    # via kubernetes
    # via requests
charset-normalizer==3.4.4
    # via reportlab
    # via requests
chromadb==1.4.0
    # via langchain-chroma
    # via legal
click==8.3.1
    # via streamlit
    # via typer
    # via uvicorn
coloredlogs==15.0.1
    # via onnxruntime
dataclasses-json==0.6.7
    # via langchain-community
distro==1.9.0
    # via google-genai
    # via posthog
durationpy==0.10
    # via kubernetes
et-xmlfile==2.0.0
    # via openpyxl
filelock==3.20.1
    # via huggingface-hub
    # via torch
    # via transformers
filetype==1.2.0
    # via langchain-google-genai
flatbuffers==25.12.19
    # via onnxruntime
frozenlist==1.8.0
    # via aiohttp
    # via aiosignal
fsspec==2025.12.0
    # via huggingface-hub
    # via torch
gitdb==4.0.12
    # via gitpython
gitpython==3.1.45
    # via streamlit
google-auth==2.45.0
    # via google-genai
    # via kubernetes
google-genai==1.56.0
    # via langchain-google-genai
googleapis-common-protos==1.72.0
    # via opentelemetry-exporter-otlp-proto-grpc
greenlet==3.3.0
    # via sqlalchemy
grpcio==1.76.0
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
h11==0.16.0
    # via httpcore
    # via uvicorn
hf-xet==1.2.0
    # via huggingface-hub
httpcore==1.0.9
    # via httpx
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via chromadb
    # via google-genai
    # via langgraph-sdk
    # via langsmith
httpx-sse==0.4.3
    # via langchain-community
huggingface-hub==0.36.0
    # via langchain-huggingface
    # via sentence-transformers
    # via tokenizers
    # via transformers
humanfriendly==10.0
    # via coloredlogs
idna==3.11
    # via anyio
    # via httpx
    # via requests
    # via yarl
importlib-metadata==8.7.1
    # via opentelemetry-api
importlib-resources==6.5.2
    # via chromadb
jinja2==3.1.6
    # via altair
    # via pydeck
    # via torch
joblib==1.5.3
    # via scikit-learn
jsonpatch==1.33
    # via langchain-core
jsonpointer==3.0.0
    # via jsonpatch
jsonschema==4.25.1
    # via altair
    # via chromadb
jsonschema-specifications==2025.9.1
    # via jsonschema
kubernetes==34.1.0
    # via chromadb
langchain==1.2.0
    # via legal
langchain-chroma==1.1.0
    # via legal
langchain-classic==1.0.1
    # via langchain-community
langchain-community==0.4.1
    # via legal
langchain-core==1.2.5
    # via langchain
    # via langchain-chroma
    # via langchain-classic
    # via langchain-community
    # via langchain-google-genai
    # via langchain-huggingface
    # via langchain-text-splitters
    # via langgraph
    # via langgraph-checkpoint
    # via langgraph-prebuilt
    # via legal
langchain-google-genai==4.1.2
    # via legal
langchain-huggingface==1.2.0
    # via legal
langchain-text-splitters==1.1.0
    # via langchain-classic
langgraph==1.0.5
    # via langchain
langgraph-checkpoint==3.0.1
    # via langgraph
    # via langgraph-prebuilt
langgraph-prebuilt==1.0.5
    # via langgraph
langgraph-sdk==0.3.1
    # via langgraph
langsmith==0.5.2
    # via langchain-classic
    # via langchain-community
    # via langchain-core
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==3.26.2
    # via dataclasses-json
mdurl==0.1.2
    # via markdown-it-py
mmh3==5.2.0
    # via chromadb
mpmath==1.3.0
    # via sympy
multidict==6.7.0
    # via aiohttp
    # via yarl
mypy-extensions==1.1.0
    # via typing-inspect
narwhals==2.14.0
    # via altair
networkx==3.6.1
    # via torch
numpy==1.26.4
    # via chromadb
    # via langchain-chroma
    # via langchain-community
    # via legal
    # via onnxruntime
    # via pandas
    # via pydeck
    # via scikit-learn
    # via scipy
    # via streamlit
    # via transformers
oauthlib==3.3.1
    # via requests-oauthlib
onnxruntime==1.23.2
    # via chromadb
openpyxl==3.1.5
    # via legal
opentelemetry-api==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
opentelemetry-exporter-otlp-proto-common==1.39.1
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-otlp-proto-grpc==1.39.1
    # via chromadb
opentelemetry-proto==1.39.1
    # via opentelemetry-exporter-otlp-proto-common
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-sdk==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-semantic-conventions==0.60b1
    # via opentelemetry-sdk
orjson==3.11.5
    # via chromadb
    # via langgraph-sdk
    # via langsmith
ormsgpack==1.12.1
    # via langgraph-checkpoint
overrides==7.7.0
    # via chromadb
packaging==25.0
    # via altair
    # via build
    # via huggingface-hub
    # via langchain-core
    # via langsmith
    # via marshmallow
    # via onnxruntime
    # via pytesseract
    # via streamlit
    # via transformers
pandas==2.3.3
    # via legal
    # via streamlit
pdf2image==1.17.0
    # via legal
pillow==12.0.0
    # via pdf2image
    # via pytesseract
    # via reportlab
    # via streamlit
posthog==5.4.0
    # via chromadb
propcache==0.4.1
    # via aiohttp
    # via yarl
protobuf==6.33.2
    # via googleapis-common-protos
    # via onnxruntime
    # via opentelemetry-proto
    # via streamlit
pyarrow==22.0.0
    # via streamlit
pyasn1==0.6.1
    # via pyasn1-modules
    # via rsa
pyasn1-modules==0.4.2
    # via google-auth
pybase64==1.4.3
    # via chromadb
pydantic==2.12.5
    # via chromadb
    # via google-genai
    # via langchain
    # via langchain-classic
    # via langchain-core
    # via langchain-google-genai
    # via langgraph
    # via langsmith
    # via pydantic-settings
pydantic-core==2.41.5
    # via pydantic
pydantic-settings==2.12.0
    # via langchain-community
pydeck==0.9.1
    # via streamlit
pygments==2.19.2
    # via rich
pypdf==6.5.0
    # via legal
pypika==0.48.9
    # via chromadb
pyproject-hooks==1.2.0
    # via build
pytesseract==0.3.13
    # via legal
python-dateutil==2.9.0.post0
    # via kubernetes
    # via pandas
    # via posthog
python-dotenv==1.2.1
    # via legal
    # via pydantic-settings
    # via uvicorn
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via chromadb
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langchain-core
    # via transformers
    # via uvicorn
referencing==0.37.0
    # via jsonschema
    # via jsonschema-specifications
regex==2025.11.3
    # via transformers
reportlab==4.4.7
    # via legal
requests==2.32.5
    # via google-auth
    # via google-genai
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langsmith
    # via posthog
    # via requests-oauthlib
    # via requests-toolbelt
    # via streamlit
    # via transformers
requests-oauthlib==2.0.0
    # via kubernetes
requests-toolbelt==1.0.0
    # via langsmith
rich==14.2.0
    # via chromadb
    # via typer
rpds-py==0.30.0
    # via jsonschema
    # via referencing
rsa==4.9.1
    # via google-auth
safetensors==0.7.0
    # via transformers
scikit-learn==1.8.0
    # via sentence-transformers
scipy==1.16.3
    # via scikit-learn
    # via sentence-transformers
sentence-transformers==5.2.0
    # via legal
shellingham==1.5.4
    # via typer
six==1.17.0
    # via kubernetes
    # via posthog
    # via python-dateutil
smmap==5.0.2
    # via gitdb
sniffio==1.3.1
    # via google-genai
sqlalchemy==2.0.45
    # via langchain-classic
    # via langchain-community
streamlit==1.52.2
    # via legal
    # via streamlit-image-coordinates
streamlit-image-coordinates==0.4.0
    # via legal
sympy==1.14.0
    # via onnxruntime
    # via torch
tenacity==9.1.2
    # via chromadb
    # via google-genai
    # via langchain-community
    # via langchain-core
    # via streamlit
threadpoolctl==3.6.0
    # via scikit-learn
tokenizers==0.22.1
    # via chromadb
    # via langchain-huggingface
    # via transformers
toml==0.10.2
    # via streamlit
torch==2.2.2
    # via sentence-transformers
tornado==6.5.4
    # via streamlit
tqdm==4.67.1
    # via chromadb
    # via huggingface-hub
    # via sentence-transformers
    # via transformers
transformers==4.57.3
    # via sentence-transformers
typer==0.21.0
    # via chromadb
typing-extensions==4.15.0
    # via aiosignal
    # via altair
    # via anyio
    # via chromadb
    # via google-genai
    # via grpcio
    # via huggingface-hub
    # via langchain-core
    # via opentelemetry-api
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
    # via pydantic
    # via pydantic-core
    # via referencing
    # via sentence-transformers
    # via sqlalchemy
    # via streamlit
    # via torch
    # via typer
    # via typing-inspect
    # via typing-inspection
typing-inspect==0.9.0
    # via dataclasses-json
typing-inspection==0.4.2
    # via pydantic
    # via pydantic-settings
tzdata==2025.3
    # via pandas
urllib3==2.3.0
    # via kubernetes
    # via requests
uuid-utils==0.12.0
    # via langchain-core
    # via langsmith
uvicorn==0.40.0
    # via chromadb
uvloop==0.22.1
    # via uvicorn
watchdog==6.0.0
    # via legal
watchfiles==1.1.1
    # via uvicorn
websocket-client==1.9.0
    # via kubernetes
websockets==15.0.1
    # via google-genai
    # via uvicorn
xxhash==3.6.0
    # via langgraph
yarl==1.22.0
    # via aiohttp
zipp==3.23.0
    # via importlib-metadata
zstandard==0.25.0
    # via langsmith
```

## File: requirements.lock
```
# generated by rye
# use `rye lock` or `rye sync` to update this lockfile
#
# last locked with the following flags:
#   pre: false
#   features: []
#   all-features: false
#   with-sources: false
#   generate-hashes: false
#   universal: false

-e file:.
aiohappyeyeballs==2.6.1
    # via aiohttp
aiohttp==3.13.2
    # via langchain-community
aiosignal==1.4.0
    # via aiohttp
altair==6.0.0
    # via streamlit
annotated-types==0.7.0
    # via pydantic
anyio==4.12.0
    # via google-genai
    # via httpx
    # via watchfiles
attrs==25.4.0
    # via aiohttp
    # via jsonschema
    # via referencing
backoff==2.2.1
    # via posthog
bcrypt==5.0.0
    # via chromadb
blinker==1.9.0
    # via streamlit
build==1.3.0
    # via chromadb
cachetools==6.2.4
    # via google-auth
    # via streamlit
certifi==2025.11.12
    # via httpcore
    # via httpx
    # via kubernetes
    # via requests
charset-normalizer==3.4.4
    # via reportlab
    # via requests
chromadb==1.4.0
    # via langchain-chroma
    # via legal
click==8.3.1
    # via streamlit
    # via typer
    # via uvicorn
coloredlogs==15.0.1
    # via onnxruntime
dataclasses-json==0.6.7
    # via langchain-community
distro==1.9.0
    # via google-genai
    # via posthog
durationpy==0.10
    # via kubernetes
et-xmlfile==2.0.0
    # via openpyxl
filelock==3.20.1
    # via huggingface-hub
    # via torch
    # via transformers
filetype==1.2.0
    # via langchain-google-genai
flatbuffers==25.12.19
    # via onnxruntime
frozenlist==1.8.0
    # via aiohttp
    # via aiosignal
fsspec==2025.12.0
    # via huggingface-hub
    # via torch
gitdb==4.0.12
    # via gitpython
gitpython==3.1.45
    # via streamlit
google-auth==2.45.0
    # via google-genai
    # via kubernetes
google-genai==1.56.0
    # via langchain-google-genai
googleapis-common-protos==1.72.0
    # via opentelemetry-exporter-otlp-proto-grpc
greenlet==3.3.0
    # via sqlalchemy
grpcio==1.76.0
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
h11==0.16.0
    # via httpcore
    # via uvicorn
hf-xet==1.2.0
    # via huggingface-hub
httpcore==1.0.9
    # via httpx
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via chromadb
    # via google-genai
    # via langgraph-sdk
    # via langsmith
httpx-sse==0.4.3
    # via langchain-community
huggingface-hub==0.36.0
    # via langchain-huggingface
    # via sentence-transformers
    # via tokenizers
    # via transformers
humanfriendly==10.0
    # via coloredlogs
idna==3.11
    # via anyio
    # via httpx
    # via requests
    # via yarl
importlib-metadata==8.7.1
    # via opentelemetry-api
importlib-resources==6.5.2
    # via chromadb
jinja2==3.1.6
    # via altair
    # via pydeck
    # via torch
joblib==1.5.3
    # via scikit-learn
jsonpatch==1.33
    # via langchain-core
jsonpointer==3.0.0
    # via jsonpatch
jsonschema==4.25.1
    # via altair
    # via chromadb
jsonschema-specifications==2025.9.1
    # via jsonschema
kubernetes==34.1.0
    # via chromadb
langchain==1.2.0
    # via legal
langchain-chroma==1.1.0
    # via legal
langchain-classic==1.0.1
    # via langchain-community
langchain-community==0.4.1
    # via legal
langchain-core==1.2.5
    # via langchain
    # via langchain-chroma
    # via langchain-classic
    # via langchain-community
    # via langchain-google-genai
    # via langchain-huggingface
    # via langchain-text-splitters
    # via langgraph
    # via langgraph-checkpoint
    # via langgraph-prebuilt
    # via legal
langchain-google-genai==4.1.2
    # via legal
langchain-huggingface==1.2.0
    # via legal
langchain-text-splitters==1.1.0
    # via langchain-classic
langgraph==1.0.5
    # via langchain
langgraph-checkpoint==3.0.1
    # via langgraph
    # via langgraph-prebuilt
langgraph-prebuilt==1.0.5
    # via langgraph
langgraph-sdk==0.3.1
    # via langgraph
langsmith==0.5.2
    # via langchain-classic
    # via langchain-community
    # via langchain-core
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==3.26.2
    # via dataclasses-json
mdurl==0.1.2
    # via markdown-it-py
mmh3==5.2.0
    # via chromadb
mpmath==1.3.0
    # via sympy
multidict==6.7.0
    # via aiohttp
    # via yarl
mypy-extensions==1.1.0
    # via typing-inspect
narwhals==2.14.0
    # via altair
networkx==3.6.1
    # via torch
numpy==1.26.4
    # via chromadb
    # via langchain-chroma
    # via langchain-community
    # via legal
    # via onnxruntime
    # via pandas
    # via pydeck
    # via scikit-learn
    # via scipy
    # via streamlit
    # via transformers
oauthlib==3.3.1
    # via requests-oauthlib
onnxruntime==1.23.2
    # via chromadb
openpyxl==3.1.5
    # via legal
opentelemetry-api==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
opentelemetry-exporter-otlp-proto-common==1.39.1
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-otlp-proto-grpc==1.39.1
    # via chromadb
opentelemetry-proto==1.39.1
    # via opentelemetry-exporter-otlp-proto-common
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-sdk==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-semantic-conventions==0.60b1
    # via opentelemetry-sdk
orjson==3.11.5
    # via chromadb
    # via langgraph-sdk
    # via langsmith
ormsgpack==1.12.1
    # via langgraph-checkpoint
overrides==7.7.0
    # via chromadb
packaging==25.0
    # via altair
    # via build
    # via huggingface-hub
    # via langchain-core
    # via langsmith
    # via marshmallow
    # via onnxruntime
    # via pytesseract
    # via streamlit
    # via transformers
pandas==2.3.3
    # via legal
    # via streamlit
pdf2image==1.17.0
    # via legal
pillow==12.0.0
    # via pdf2image
    # via pytesseract
    # via reportlab
    # via streamlit
posthog==5.4.0
    # via chromadb
propcache==0.4.1
    # via aiohttp
    # via yarl
protobuf==6.33.2
    # via googleapis-common-protos
    # via onnxruntime
    # via opentelemetry-proto
    # via streamlit
pyarrow==22.0.0
    # via streamlit
pyasn1==0.6.1
    # via pyasn1-modules
    # via rsa
pyasn1-modules==0.4.2
    # via google-auth
pybase64==1.4.3
    # via chromadb
pydantic==2.12.5
    # via chromadb
    # via google-genai
    # via langchain
    # via langchain-classic
    # via langchain-core
    # via langchain-google-genai
    # via langgraph
    # via langsmith
    # via pydantic-settings
pydantic-core==2.41.5
    # via pydantic
pydantic-settings==2.12.0
    # via langchain-community
pydeck==0.9.1
    # via streamlit
pygments==2.19.2
    # via rich
pypdf==6.5.0
    # via legal
pypika==0.48.9
    # via chromadb
pyproject-hooks==1.2.0
    # via build
pytesseract==0.3.13
    # via legal
python-dateutil==2.9.0.post0
    # via kubernetes
    # via pandas
    # via posthog
python-dotenv==1.2.1
    # via legal
    # via pydantic-settings
    # via uvicorn
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via chromadb
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langchain-core
    # via transformers
    # via uvicorn
referencing==0.37.0
    # via jsonschema
    # via jsonschema-specifications
regex==2025.11.3
    # via transformers
reportlab==4.4.7
    # via legal
requests==2.32.5
    # via google-auth
    # via google-genai
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langsmith
    # via posthog
    # via requests-oauthlib
    # via requests-toolbelt
    # via streamlit
    # via transformers
requests-oauthlib==2.0.0
    # via kubernetes
requests-toolbelt==1.0.0
    # via langsmith
rich==14.2.0
    # via chromadb
    # via typer
rpds-py==0.30.0
    # via jsonschema
    # via referencing
rsa==4.9.1
    # via google-auth
safetensors==0.7.0
    # via transformers
scikit-learn==1.8.0
    # via sentence-transformers
scipy==1.16.3
    # via scikit-learn
    # via sentence-transformers
sentence-transformers==5.2.0
    # via legal
shellingham==1.5.4
    # via typer
six==1.17.0
    # via kubernetes
    # via posthog
    # via python-dateutil
smmap==5.0.2
    # via gitdb
sniffio==1.3.1
    # via google-genai
sqlalchemy==2.0.45
    # via langchain-classic
    # via langchain-community
streamlit==1.52.2
    # via legal
    # via streamlit-image-coordinates
streamlit-image-coordinates==0.4.0
    # via legal
sympy==1.14.0
    # via onnxruntime
    # via torch
tenacity==9.1.2
    # via chromadb
    # via google-genai
    # via langchain-community
    # via langchain-core
    # via streamlit
threadpoolctl==3.6.0
    # via scikit-learn
tokenizers==0.22.1
    # via chromadb
    # via langchain-huggingface
    # via transformers
toml==0.10.2
    # via streamlit
torch==2.2.2
    # via sentence-transformers
tornado==6.5.4
    # via streamlit
tqdm==4.67.1
    # via chromadb
    # via huggingface-hub
    # via sentence-transformers
    # via transformers
transformers==4.57.3
    # via sentence-transformers
typer==0.21.0
    # via chromadb
typing-extensions==4.15.0
    # via aiosignal
    # via altair
    # via anyio
    # via chromadb
    # via google-genai
    # via grpcio
    # via huggingface-hub
    # via langchain-core
    # via opentelemetry-api
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
    # via pydantic
    # via pydantic-core
    # via referencing
    # via sentence-transformers
    # via sqlalchemy
    # via streamlit
    # via torch
    # via typer
    # via typing-inspect
    # via typing-inspection
typing-inspect==0.9.0
    # via dataclasses-json
typing-inspection==0.4.2
    # via pydantic
    # via pydantic-settings
tzdata==2025.3
    # via pandas
urllib3==2.3.0
    # via kubernetes
    # via requests
uuid-utils==0.12.0
    # via langchain-core
    # via langsmith
uvicorn==0.40.0
    # via chromadb
uvloop==0.22.1
    # via uvicorn
watchdog==6.0.0
    # via legal
watchfiles==1.1.1
    # via uvicorn
websocket-client==1.9.0
    # via kubernetes
websockets==15.0.1
    # via google-genai
    # via uvicorn
xxhash==3.6.0
    # via langgraph
yarl==1.22.0
    # via aiohttp
zipp==3.23.0
    # via importlib-metadata
zstandard==0.25.0
    # via langsmith
```
