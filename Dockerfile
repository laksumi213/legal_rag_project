# Dockerfile

# (1-3 手順は省略せず維持)
FROM python:3.12-slim
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

WORKDIR /app

# 3. 依存関係ファイルのコピー
COPY requirements.lock pyproject.toml README.md ./

# ★修正ポイント: editable install (-e .) を成功させるために src を先にコピー
COPY src ./src

# 依存ライブラリのインストール
RUN pip install --no-cache-dir -r requirements.lock

# 4. 残りのソースコード全体をコピー
COPY . .

ENV PYTHONUNBUFFERED=1
CMD ["python", "src/main.py"]