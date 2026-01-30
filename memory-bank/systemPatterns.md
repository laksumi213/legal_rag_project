# System Patterns

## 1. モジュール構成 (高レベル)
- **`src/legal_system/ui/`**: StreamlitアプリケーションのUIコンポーネントとページ
- **`src/services/`**: ビジネスロジック、データ処理、外部連携サービス
- **`src/legal_system/models/`**: データベースモデル、スキーマ定義
- **`src/legal_system/core/`**: アプリケーションのコア機能（設定、データベース管理、AI/OCRエンジンなど）
- **`data/`**: データベースファイル、設定ファイル、テンプレート、一時ファイルなど
- **`scripts/`**: 開発・運用をサポートするユーティリティスクリプト

## 2. データフロー
1. **UIからの入力**: Streamlit UIを通じてユーザーが情報を入力。
2. **サービス層での処理**: `src/services/` 内の各サービス（例: `case_service.py`, `deceased_service.py`）が入力データを処理、検証、ビジネスロジックを適用。
3. **データベース操作**: `src/legal_system/models/` で定義されたモデルと `src/legal_system/core/database_manager.py` を通じてデータベース（例: `chroma.sqlite3`, `sql/.keep` から推測されるRDB）と連携し、データの永続化・取得を行う。
4. **外部連携**: 必要な場合、Kintone (`kintone_client.py`, `kintone_sync_service.py`) やGmail (`gmail_watcher_service.py`) などの外部サービスと連携。
5. **AI/OCR処理**: `src/legal_system/core/ocr_engine.py`, `src/legal_system/core/ai_processor.py` を使用し、ドキュメントからの情報抽出やAIによるアドバイス生成。
6. **UIへの出力**: 処理結果をUIに表示。

## 3. データベースパターン
- **リレーショナルデータベース**: `src/legal_system/models/tables.py` や `data/db/sql/.keep` から、案件情報、相続人情報、財産情報などの構造化データの管理に利用されていると推測。
- **ベクトルデータベース (ChromaDB)**: `data/db/chroma/local_rag_db/` の存在から、RAG (Retrieval Augmented Generation) のためのドキュメント埋め込みやセマンティック検索に利用されていると推測。

## 4. 認証・認可
(現状不明 - 今後の分析で特定)

## 5. エラーハンドリング・ロギング
(現状不明 - 今後の分析で特定)

## 6. ドキュメント処理パターン
- `src/legal_system/core/pdf_processor.py`: PDFファイルの処理。
- `src/legal_system/core/ocr_engine.py`: OCRによる画像・PDFからのテキスト抽出。
- `src/services/scanner_service.py`: スキャナー連携またはスキャンデータの処理。
- `src/legal_system/ui/components/document_viewer.py`: UIでのドキュメント表示。