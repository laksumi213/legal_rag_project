# 開発計画書

## 1. 概要

本計画は、以下の2つの機能改善を目的とします。

1.  **残高証明書の自動AI解析:** 書類アップロード時に、ボタン操作なしでAI解析を自動実行します。
2.  **多機能PDFビューアの実装:** ページ切り替えと拡大・縮小が可能な共通PDFビューアを導入し、既存の画面に適用します。

## 2. タスク詳細

### タスク1: 残高証明書の自動AI解析

*   **対象ファイル:** [`src/legal_system/ui/pages/08_残高証明書_読取.py`](src/legal_system/ui/pages/08_残高証明書_読取.py)
*   **変更内容:**
    1.  ファイルアップロードを検知後、`st.session_state` を使用してファイルが未処理であることを確認します。
    2.  `st.button` によるトリガーを廃止し、`analyze_balance_cert_with_ai` 関数を自動的に呼び出します。
    3.  処理中は `st.spinner` を表示し、ユーザーに進捗をフィードバックします。
    4.  解析完了後、結果を `st.session_state` に格納し、再描画時の重複実行を防ぎます。

### タスク2: 多機能PDFビューアの実装

#### A. 残高証明書読取画面への適用

*   **対象ファイル:** [`src/legal_system/ui/pages/08_残高証明書_読取.py`](src/legal_system/ui/pages/08_残高証明書_読取.py)
*   **変更内容:**
    1.  共通ビューアコンポーネント `render_enhanced_document_viewer` をインポートします。
    2.  既存の `st.image` を使用した簡易プレビュー部分を、`render_enhanced_document_viewer` の呼び出しに置き換えます。
    3.  ビューアにファイルデータ (`file_bytes`) とファイルタイプを渡し、一意のキー (`key_prefix`) を設定します。

#### B. 銀行ナレッジ検索画面への適用

*   **対象ファイル:** [`src/legal_system/ui/pages/01_案件詳細_統合管理.py`](src/legal_system/ui/pages/01_案件詳細_統合管理.py)
*   **変更内容:**
    1.  共通ビューアコンポーネント `render_enhanced_document_viewer` をインポートします。
    2.  「銀行RAG・ナレッジ」タブ内の過去書類表示ロジックを修正します。
    3.  `st.expander` 内の `st.image` による複数ページ表示部分を、`render_enhanced_document_viewer` の呼び出しに置き換えます。
    4.  各書類に対して、ループ内で一意の `key_prefix` を生成し、ビューアの状態が衝突しないようにします。

## 3. フロー図 (Mermaid)

```mermaid
graph TD
    subgraph Task 1: 自動AI解析
        A[ファイルアップロード] --> B{ファイルは新規か？};
        B -- Yes --> C[AI解析実行 (Spinner表示)];
        C --> D[結果をSession Stateに保存];
        B -- No --> E[処理をスキップ];
    end

    subgraph Task 2: PDFビューア導入
        F[残高証明書画面] --> G[共通ビューア呼び出し];
        H[銀行ナレッジ画面] --> I[共通ビューア呼び出し];
        G & I --> J[多機能ビューア表示<br>- ページ送り<br>- 拡大/縮小];
    end
```

## 4. Todoリスト

最終的な実装タスクリストは以下の通りです。

-   [ ] `08_残高証明書_読取.py`: AI解析の自動実行ロジックを実装
-   [ ] `08_残高証明書_読取.py`: 既存のプレビューを共通PDFビューアに置換
-   [ ] `01_案件詳細_統合管理.py`: 過去書類のプレビューを共通PDFビューアに置換

上記計画をご確認ください。承認いただけましたら、実装のため `💻 Code` モードに切り替えます。