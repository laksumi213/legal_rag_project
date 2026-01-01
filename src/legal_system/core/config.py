# src/legal_system/core/config.py
from pathlib import Path

# --- パス設定 ---
# プロジェクトルートの特定
# このファイル(config.py)は src/legal_system/core/ にあるため
# parents[0]=core, parents[1]=legal_system, parents[2]=src, parents[3]=ROOT
BASE_DIR = Path(__file__).resolve().parents[3]

# データディレクトリ (data/)
DATA_DIR = BASE_DIR / "data"

# データベース保存先
# data/db/chroma/local_rag_db
DB_DIR_CHROMA = DATA_DIR / "db" / "chroma" / "local_rag_db"
# data/db/sql/legal_system.db (audit_log.dbから名称変更した場合)
DB_FILE_SQLITE = DATA_DIR / "db" / "sql" / "legal_system.db"

# データ一時保存先 (data/templates)
DATA_DIR_TEMPLATES = DATA_DIR / "templates"

# --- AIモデル設定 ---
# Google Gemini (最新モデル指定)
GOOGLE_MODEL_NAME = "models/gemini-2.5-flash-lite"

# Local Ollama (日本語対応モデル推奨)
# メモリ（RAM）を最低でも 8GB〜16GB ほど消費
# OLLAMA_MODEL_NAME = "elyza:jp8b"
# バランス型。1bよりも賢く、8bよりも軽快。
# OLLAMA_MODEL_NAME = llama3.2:3b
# 軽量モデル
OLLAMA_MODEL_NAME = "llama3.2:1b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Embeddingモデル (ローカル実行用)
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
