# ベースイメージ: Python 3.12 (軽量版)
FROM python:3.12-slim

# 1. OSレベルの依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 作業ディレクトリの設定
WORKDIR /app

# 3. 依存関係ファイルのコピーとインストール
# エラー回避のため、設定ファイル(pyproject.toml)と説明書(README.md)を先にコピーします
COPY requirements.lock pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.lock

# 4. ソースコード全体をコピー
COPY . .

# 5. 環境変数の設定 (Streamlit用)
ENV PYTHONUNBUFFERED=1

# 6. アプリケーションの起動コマンド
CMD ["python", "src/legal_system/main.py"]