from pathlib import Path

# ==========================================
# プロジェクト構成定義
# ==========================================

# 1. pyproject.toml (Rye設定)
PYPROJECT_TOML = """[project]
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
    "pandas>=2.2.0",
    "openpyxl>=3.1.2",
]
readme = "README.md"
requires-python = ">= 3.12"

[tool.rye]
managed = true
dev-dependencies = []

[tool.rye.scripts]
start = { cmd = "python src/legal_rag_system/main.py" }
"""

# 2. .env (環境変数テンプレート)
DOT_ENV = """# Google API Keys (カンマ区切りで複数指定可能)
GOOGLE_API_KEYS=AIzaSy_KEY1,AIzaSy_KEY2,AIzaSy_KEY3

# アプリケーション設定
APP_ENV=development
"""

# 3. src/legal_rag_system/main.py (起動ランチャー)
MAIN_PY = """
import os
import sys
import subprocess
from pathlib import Path

def main():
    \"\"\"
    アプリケーションの起動エントリーポイント
    Ryeなどの環境下でStreamlitを正しくサブプロセスとして起動します。
    \"\"\"
    # 現在のファイルのディレクトリを取得
    current_dir = Path(__file__).parent.absolute()
    
    # UIファイル(app.py)のパスを特定
    app_path = current_dir / "ui" / "app.py"
    
    print(f"🚀 Legal RAG System を起動します...")
    print(f"📂 UI Path: {app_path}")

    # streamlit run コマンドを構築
    # sys.executable を使うことで、現在の仮想環境(Rye)のPythonを使用する
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    
    # 追加の引数があれば渡す
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        # サブプロセスとしてStreamlitを実行
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\\n🛑 システムを終了します。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
"""

# 4. src/legal_rag_system/core/config.py (定数管理)
CORE_CONFIG_PY = """
import os
from pathlib import Path

# --- パス設定 ---
# src/legal_rag_system/core/config.py から見てプロジェクトルート(4階層上)を特定
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# データベース保存先
DB_DIR_CHROMA = BASE_DIR / "db" / "chroma" / "local_rag_db"
DB_FILE_SQLITE = BASE_DIR / "db" / "sql" / "audit_log.db"

# データ一時保存先
DATA_DIR_TEMPLATES = BASE_DIR / "data" / "templates"

# --- AIモデル設定 ---
# Google Gemini (最新モデル指定)
GOOGLE_MODEL_NAME = "models/gemini-2.5-flash-lite"

# Local Ollama (日本語対応モデル推奨)
OLLAMA_MODEL_NAME = "elyza:jp8b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Embeddingモデル (ローカル実行用)
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
"""

# 5. src/legal_rag_system/core/database.py (SQLite管理)
CORE_DATABASE_PY = """
import sqlite3
import getpass
from datetime import datetime
from typing import Dict, Any, Optional
from .config import DB_FILE_SQLITE

class DatabaseManager:
    \"\"\"
    SQLiteを使用した監査ログとユーザー管理を行うクラス
    PCのログイン情報と連携し、誰が何をしたかを記録します。
    \"\"\"

    def __init__(self):
        \"\"\"データベース接続の初期化とテーブル作成\"\"\"
        # ディレクトリがない場合は作成
        DB_FILE_SQLITE.parent.mkdir(parents=True, exist_ok=True)
        
        # SQLite接続 (check_same_thread=FalseはStreamlitのマルチスレッド対策)
        self.conn = sqlite3.connect(str(DB_FILE_SQLITE), check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        \"\"\"必要なテーブルが存在しない場合に作成する\"\"\"
        cur = self.conn.cursor()
        
        # ユーザー管理テーブル
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS users (
                pc_username TEXT PRIMARY KEY,
                display_name TEXT,
                department TEXT,
                updated_at TEXT
            )
        \"\"\")
        
        # 監査ログテーブル
        cur.execute(\"\"\"
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id TEXT,
                action_type TEXT,
                target TEXT,
                details TEXT
            )
        \"\"\")
        self.conn.commit()

    def get_current_user_info(self) -> Dict[str, str]:
        \"\"\"
        PCのログインユーザー名を取得し、DB登録情報を返す
        未登録の場合は自動的に初期レコードを作成して返す
        \"\"\"
        pc_user = getpass.getuser()
        cur = self.conn.cursor()
        
        cur.execute("SELECT display_name, department FROM users WHERE pc_username = ?", (pc_user,))
        res = cur.fetchone()
        
        if res:
            return {"id": pc_user, "name": res[0], "dept": res[1]}
        else:
            # 未登録ユーザーの初期化
            default_name = f"{pc_user}(未登録)"
            default_dept = "所属未定"
            self.register_user(pc_user, default_name, default_dept)
            return {"id": pc_user, "name": default_name, "dept": default_dept}

    def register_user(self, pc_username: str, display_name: str, department: str):
        \"\"\"ユーザー情報の登録・更新\"\"\"
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(\"\"\"
            INSERT OR REPLACE INTO users (pc_username, display_name, department, updated_at)
            VALUES (?, ?, ?, ?)
        \"\"\", (pc_username, display_name, department, now))
        self.conn.commit()

    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        \"\"\"
        操作ログを記録する
        Args:
            user_id: 操作したユーザーID
            action: 操作の種類 (SEARCH, UPLOAD, etc.)
            target: 操作対象 (ファイル名, クエリなど)
            details: 詳細情報
        \"\"\"
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cur.execute(\"\"\"
            INSERT INTO audit_logs (timestamp, user_id, action_type, target, details)
            VALUES (?, ?, ?, ?, ?)
        \"\"\", (now, user_id, action, target, details))
        self.conn.commit()
"""

# 6. src/legal_rag_system/core/ocr_engine.py (OCR処理)
CORE_OCR_PY = """
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
# pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def extract_text_from_scanned_pdf(file_bytes: bytes) -> str:
    \"\"\"
    画像化されたPDF(スキャンデータ)からテキストを抽出する。
    pdf2image で画像に変換し、pytesseract でOCRを実行する。
    \"\"\"
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
            full_text += f"\\n--- Page {i+1} (OCR Result) ---\\n{text}"
            
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return f"OCR処理中にエラーが発生しました: {str(e)}"
        
    return full_text
"""

# 7. src/legal_rag_system/core/ai_factory.py (ハイブリッドAI + フォールバック)
CORE_AI_FACTORY_PY = """
import os
import streamlit as st
from typing import List, Optional

# LangChain関連
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel

# 設定読み込み
from .config import (
    GOOGLE_MODEL_NAME, 
    OLLAMA_MODEL_NAME, 
    OLLAMA_BASE_URL, 
    EMBEDDING_MODEL_NAME,
    DB_DIR_CHROMA
)

class AIFactory:
    \"\"\"
    AIモデル(LLM)と検索エンジン(VectorStore)の生成を担当するファクトリクラス
    Cloud(Gemini)とLocal(Ollama)の切り替えロジックを集約。
    \"\"\"

    @staticmethod
    @st.cache_resource
    def get_vector_store():
        \"\"\"
        VectorStore(Chroma)の初期化。
        Cloud/Localモードに関わらず、Embeddingは常にローカル(HuggingFace)で行う。
        \"\"\"
        # 埋め込みモデルの準備 (CPU実行)
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"}
        )

        # ディレクトリ作成
        DB_DIR_CHROMA.mkdir(parents=True, exist_ok=True)

        # VectorStoreロード
        vector_store = Chroma(
            persist_directory=str(DB_DIR_CHROMA),
            embedding_function=embeddings,
            collection_name="agent_documents"
        )
        return vector_store

    @staticmethod
    def get_llm(mode: str) -> Optional[BaseChatModel]:
        \"\"\"
        指定されたモードに基づいて適切なLLMインスタンスを返す。
        
        Args:
            mode (str): 'cloud' (Gemini) または 'local' (Ollama)
            
        Returns:
            BaseChatModel: LangChainのChatModelインスタンス
        \"\"\"
        
        if mode == "cloud":
            # --- Cloud (Gemini) ---
            # 環境変数からAPIキーリストを取得 (カンマ区切り対応)
            keys_str = os.getenv("GOOGLE_API_KEYS", "")
            api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

            if not api_keys:
                st.error("⚠️ .env に GOOGLE_API_KEYS が設定されていません。")
                return None

            # 各APIキーごとにLLMインスタンスを作成
            llm_instances = [
                ChatGoogleGenerativeAI(
                    model=GOOGLE_MODEL_NAME,
                    google_api_key=k,
                    temperature=0,  # 実務用のためランダム性を排除
                    convert_system_message_to_human=True,
                    max_retries=1   # フォールバックを早めるためリトライ回数は減らす
                )
                for k in api_keys
            ]

            # フォールバックチェーンの構築
            # 1つ目のキーがだめなら2つ目...という動作を実現
            if len(llm_instances) > 1:
                llm_cloud = llm_instances[0].with_fallbacks(llm_instances[1:])
            else:
                llm_cloud = llm_instances[0]
                
            return llm_cloud

        else:
            # --- Local (Ollama) ---
            # 機密情報対応モード
            return ChatOllama(
                model=OLLAMA_MODEL_NAME,
                temperature=0,
                base_url=OLLAMA_BASE_URL
            )
"""

# 8. src/legal_rag_system/ui/app.py (Streamlit UI本体)
UI_APP_PY = """
import streamlit as st
import os
import sys
from io import BytesIO

# プロジェクトルートへのパス解決 (Pythonパスを通す)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# コアモジュールのインポート
from legal_rag_system.core.database import DatabaseManager
from legal_rag_system.core.ai_factory import AIFactory
from legal_rag_system.core.ocr_engine import extract_text_from_scanned_pdf

# LangChain関連
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ==========================================
# 初期化処理
# ==========================================
st.set_page_config(page_title="行政書士DX System", layout="wide", page_icon="⚖️")

# DBマネージャー初期化
db_manager = DatabaseManager()
current_user = db_manager.get_current_user_info()

# ==========================================
# ロジック関数
# ==========================================

def run_rag_search(query: str, mode_label: str, llm):
    \"\"\"検索と回答生成を実行する\"\"\"
    if not llm:
        return "AIモデルの初期化に失敗しました。"

    # 1. 検索 (VectorStore)
    vector_store = AIFactory.get_vector_store()
    try:
        # 上位4件を取得
        docs = vector_store.similarity_search(query, k=4)
        context = "\\n\\n".join([d.page_content for d in docs])
        
        # ログ記録 (PIIが含まれる可能性があるため注意が必要だが監査上記録)
        db_manager.log_action(
            current_user["id"], "SEARCH", f"Mode:{mode_label}", f"Query len: {len(query)}"
        )
    except Exception as e:
        return f"検索システムエラー: {e}"

    # 2. 回答生成 (LLM)
    # システムプロンプト: 代理人としての振る舞いを定義
    system_prompt = \"\"\"
    あなたは行政書士法人の業務システムです。回答対象は「行政書士補助者」です。
    以下の【参照資料(スキャンデータ)】に基づき、質問に答えてください。
    
    【重要ルール】
    1. **申請主体は「代表行政書士（代理人）」です**。
       本人申請の手順ではなく、「代理人が行う場合」の手順・書類を回答してください。
    2. 必須確認事項:
       - 委任状（実印・捨印の要否）
       - 代理人本人確認書類（補助者証など）
       - 印鑑証明書の有効期限
    3. OCR特有の誤字（例: "戸箱" -> "戸籍"）は文脈から補正してください。
    \"\"\"

    template = f\"\"\"
    {system_prompt}

    【参照資料】
    {{context}}
    
    【質問】
    {{question}}
    \"\"\"

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()

    try:
        return chain.invoke({"context": context, "question": query})
    except Exception as e:
        return f"回答生成エラー ({mode_label}): {str(e)}"

def process_file_upload(file_obj):
    \"\"\"PDFアップロード・OCR・学習処理\"\"\"
    file_bytes = file_obj.read()
    filename = file_obj.name
    text = ""

    # 1. テキスト抽出 (pypdf)
    try:
        pdf = PdfReader(BytesIO(file_bytes))
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t
    except Exception:
        pass

    # 2. OCRフォールバック (文字数が極端に少ない場合は画像PDFとみなす)
    if len(text.strip()) < 50:
        with st.spinner(f"📷 画像PDFを検知: {filename} - OCR処理を実行中..."):
            text = extract_text_from_scanned_pdf(file_bytes)

    if not text.strip():
        return False, "文字情報を抽出できませんでした。"

    # 3. チャンク分割と保存
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = splitter.split_text(text)
    
    # メタデータ付与
    metadatas = [{"source": filename, "type": "manual"} for _ in chunks]
    
    # DBへの保存
    vector_store = AIFactory.get_vector_store()
    vector_store.add_texts(chunks, metadatas=metadatas)

    db_manager.log_action(current_user["id"], "UPLOAD", filename, "Success")
    return True, f"学習完了: {len(chunks)}チャンクを登録しました。"

# ==========================================
# UIメイン構成
# ==========================================
def main():
    # --- サイドバー ---
    with st.sidebar:
        st.title("⚖️ 業務メニュー")
        st.info(f"👤 Login: **{current_user['name']}**")
        st.caption(f"所属: {current_user['dept']}")
        
        with st.expander("ユーザー情報更新"):
            new_name = st.text_input("表示名", value=current_user['name'])
            new_dept = st.text_input("所属", value=current_user['dept'])
            if st.button("更新"):
                db_manager.register_user(current_user['id'], new_name, new_dept)
                st.success("更新しました。再読み込みしてください。")

        st.divider()
        st.subheader("🤖 AIモード選択")
        
        ai_mode = st.radio(
            "処理モード:",
            ("☁️ Cloud (Gemini)", "🔒 Secure (Local)"),
            index=0,
            help="個人情報を含む場合は必ずSecureモードを選択してください"
        )
        
        if "Cloud" in ai_mode:
            mode_label = "CLOUD"
            llm = AIFactory.get_llm("cloud")
            st.info("🚀 **高速・高機能**\\n一般手続の確認用。\\n※個人情報入力禁止")
        else:
            mode_label = "LOCAL"
            llm = AIFactory.get_llm("local")
            st.warning("🛡️ **機密保護 (Ollama)**\\nオフライン処理。\\n書類作成・個別案件用。")

    # --- メインエリア ---
    tab1, tab2 = st.tabs(["💬 実務Q&A (代理人)", "📥 資料学習 (OCR)"])

    # Tab 1: チャット
    with tab1:
        st.subheader(f"代理人手続検索システム ({mode_label})")
        
        # 警告バナー
        if mode_label == "LOCAL":
            st.error("【機密モード中】データは外部に送信されません。安心して個人情報を扱えます。")
        else:
            st.success("【クラウドモード中】Google Gemini 2.5 を使用中。個人情報は入力しないでください。")

        # チャット履歴の表示
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.write(m["content"])

        # 入力フォーム
        if prompt := st.chat_input("例: A銀行の解約で、代理人が行く場合の必要書類は？"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("条項・手引きを確認中..."):
                    response = run_rag_search(prompt, mode_label, llm)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

    # Tab 2: アップロード
    with tab2:
        st.subheader("📂 銀行手引き・マニュアル登録")
        st.caption("アップロードされたPDFはOCR処理され、ローカルのデータベースに保存されます。")
        
        uploaded_files = st.file_uploader("PDFファイルをドラッグ＆ドロップ", accept_multiple_files=True, type="pdf")
        
        if uploaded_files and st.button("学習開始"):
            progress_bar = st.progress(0)
            for i, f in enumerate(uploaded_files):
                success, msg = process_file_upload(f)
                if success:
                    st.toast(f"✅ {f.name}: {msg}")
                else:
                    st.error(f"❌ {f.name}: {msg}")
                progress_bar.progress((i + 1) / len(uploaded_files))
            st.success("全ファイルの処理が完了しました。")

if __name__ == "__main__":
    main()
"""

# ==========================================
# ファイル生成ロジック
# ==========================================


def create_project_structure():
    """定義された内容に基づいてディレクトリとファイルを作成する"""
    base_dir = Path.cwd()
    print(f"📂 プロジェクト作成先: {base_dir}")

    # ファイルマッピング (パス: コンテンツ)
    files = {
        "pyproject.toml": PYPROJECT_TOML,
        ".env": DOT_ENV,
        "src/legal_rag_system/__init__.py": "",
        "src/legal_rag_system/main.py": MAIN_PY,
        "src/legal_rag_system/core/__init__.py": "",
        "src/legal_rag_system/core/config.py": CORE_CONFIG_PY,
        "src/legal_rag_system/core/database.py": CORE_DATABASE_PY,
        "src/legal_rag_system/core/ocr_engine.py": CORE_OCR_PY,
        "src/legal_rag_system/core/ai_factory.py": CORE_AI_FACTORY_PY,
        "src/legal_rag_system/ui/__init__.py": "",
        "src/legal_rag_system/ui/app.py": UI_APP_PY,
        "db/chroma/.keep": "",
        "db/sql/.keep": "",
        "data/templates/.keep": "",
    }

    for path_str, content in files.items():
        file_path = base_dir / path_str

        # ディレクトリ作成
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # ファイル書き込み
        if content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            print(f"✅ Created: {path_str}")
        else:
            # 空ファイル作成 (.keepなど)
            file_path.touch()
            print(f"✅ Created: {path_str}")

    print("\n🎉 プロジェクトの自動生成が完了しました！")
    print("\n【次のステップ】")
    print("1. システム要件のインストール:")
    print("   - Windows: Tesseract-OCR, Poppler をインストールしパスを通す")
    print("   - Mac: brew install tesseract poppler")
    print("   - Ollama: 公式サイトからインストールし、'ollama pull elyza:jp8b' を実行")
    print("\n2. ライブラリの同期 (Rye):")
    print("   $ rye sync")
    print("\n3. アプリケーションの起動:")
    print("   $ rye run start")


if __name__ == "__main__":
    create_project_structure()
