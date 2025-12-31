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
# メモリ（RAM）を最低でも 8GB〜16GB ほど消費
# OLLAMA_MODEL_NAME = "elyza:jp8b"
# バランス型。1bよりも賢く、8bよりも軽快。
# OLLAMA_MODEL_NAME = llama3.2:3b
# 軽量モデル
OLLAMA_MODEL_NAME = "llama3.2:1b"
OLLAMA_BASE_URL = "http://localhost:11434"

# Embeddingモデル (ローカル実行用)
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-large"
