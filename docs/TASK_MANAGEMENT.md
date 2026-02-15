# タスク管理機能 実装ドキュメント

**実装日:** 2026-02-12  
**機能:** 案件に紐づく標準業務フローの自動生成と進捗管理

---

## 📋 概要

遺産整理BPOシステムにおける標準的な業務フローをタスクとして管理する機能です。案件ごとに9つの標準タスクを自動生成し、完了チェック、期限日変更、担当者変更をExcelライクなUIで操作できます。

---

## 🎯 主要機能

### 1. 標準タスクの自動生成
契約日を基準に、以下の9つの標準タスクを自動生成します：

| No. | タスク名 | 期限日 | 担当者 |
|-----|---------|--------|--------|
| 1 | 戸籍収集（出生～死亡） | 契約日+20日 | Operator |
| 2 | 相続関係説明図の作成 | 契約日+34日 | Operator |
| 3 | 金融資産・残高証明書の取得 | 契約日+70日 | Operator |
| 4 | 不動産・名寄帳/評価証明書の取得 | 契約日+34日 | Operator |
| 5 | 財産目録の作成・承認 | 契約日+75日 | **Manager** |
| 6 | 遺産分割協議書の作成 | 契約日+80日 | Operator |
| 7 | 遺産分割協議書の承認・実印押印 | 契約日+94日 | **Manager** |
| 8 | 金融機関への解約申請 | 契約日+114日 | Operator |
| 9 | 完了報告・報酬精算 | 契約日+120日 | **Manager** |

### 2. タスクの編集機能
- ✅ 完了チェック
- 📅 期限日の変更
- 👤 担当者の変更
- ⚖️ タスク重みの調整（進捗率計算用）

### 3. カスタムタスクの追加
標準タスク以外の独自タスクを追加可能

### 4. 進捗サマリー
- 総タスク数
- 完了タスク数
- 進捗率（重み付き）
- 期限超過タスク数

---

## 📁 実装ファイル

### バックエンド

#### 1. `scripts/seed_data.py`
タスクテンプレートの初期データ投入

```python
def seed_task_templates():
    """標準タスクテンプレートを投入する"""
    # 9つの標準タスクをTaskTemplateテーブルに登録
```

**実行方法:**
```bash
python scripts/seed_data.py
```

#### 2. `src/services/task_service.py`
タスク管理のビジネスロジック

**主要メソッド:**
- `initialize_tasks(case_id: int)` - 標準タスクの自動生成
- `get_tasks_by_case(case_id: int)` - タスク一覧取得
- `update_tasks_bulk(updates: list)` - タスク一括更新
- `add_custom_task(...)` - カスタムタスク追加
- `delete_task(task_id: int)` - タスク削除

**型定義:** 全メソッドに型ヒント付与済み

### フロントエンド

#### 3. `src/legal_system/ui/pages/12_タスク管理.py`
タスク管理UI

**機能:**
- `st.data_editor` によるExcelライクな編集
- タスク初期化ボタン
- 変更保存時の `st.rerun()` による画面更新
- 進捗サマリー表示
- カスタムタスク追加フォーム

### 統合

#### 4. `src/legal_system/ui/Home.py`
メニュー統合

```python
elif menu == "✅ タスク管理":
    from legal_system.ui.pages.タスク管理 import render_task_management
    st.session_state["selected_case_id"] = target_case_id
    render_task_management()
```

#### 5. `src/legal_system/ui/components/sidebar.py`
サイドバーメニューに「✅ タスク管理」を追加済み

---

## 🚀 セットアップ手順

### 1. データベースマイグレーション

Taskテーブルに`weight`カラムが追加されています：

```python
class Task(Base):
    # ... 既存カラム ...
    weight = Column(Float, default=1.0)  # タスクの重み（進捗率計算用）
```

**マイグレーション実行:**
```bash
# Alembicを使用している場合
alembic revision --autogenerate -m "Add weight column to Task table"
alembic upgrade head

# または、既存DBに直接追加
ALTER TABLE tasks ADD COLUMN weight FLOAT DEFAULT 1.0;
```

### 2. タスクテンプレートの投入

```bash
python scripts/seed_data.py
```

**出力例:**
```
🌱 初期データの投入を開始します...
  . 既存: 受任・調査中
  . 既存: 書類作成中
  ...
✅ ステータスマスタの投入が完了しました！

🌱 タスクテンプレートの投入を開始します...
  + 追加: 戸籍収集（出生～死亡） (20日, Operator)
  + 追加: 相続関係説明図の作成 (34日, Operator)
  ...
✅ タスクテンプレートの投入が完了しました！
```

### 3. 動作確認テスト

```bash
python tests/test_task_service.py
```

**テスト内容:**
1. タスク初期化テスト
2. タスク更新テスト
3. カスタムタスク追加テスト

---

## 💻 使用方法

### 1. アプリケーション起動

```bash
streamlit run src/legal_system/ui/Home.py
```

### 2. タスク管理画面へのアクセス

1. 案件検索で案件を選択
2. サイドバーから「✅ タスク管理」を選択
3. 初回は「🚀 標準タスクを初期化」ボタンをクリック

### 3. タスクの編集

1. データエディタで直接編集
   - 完了チェックボックスをクリック
   - 期限日をクリックしてカレンダーから選択
   - 担当者名を入力
   - 重みを調整（0.1～5.0）

2. 「💾 変更を保存」ボタンをクリック

3. 画面が自動更新され、進捗サマリーに反映

### 4. カスタムタスクの追加

1. 「➕ カスタムタスクを追加」を展開
2. タスク名、期限日、担当者、重みを入力
3. 「追加」ボタンをクリック

---

## 🔧 技術仕様

### データモデル

#### TaskTemplate（タスクテンプレート）
```python
template_id: int (PK)
description: str  # タスク名
default_due_days: int  # 契約日からの期限日数
is_manager_task: bool  # Manager担当フラグ
```

#### Task（タスク）
```python
task_id: int (PK)
case_id: int (FK)
template_id: int (FK, nullable)  # カスタムタスクはNone
description: str
due_date: datetime
is_completed: bool
assigned_user_id: int (FK)
weight: float  # 進捗率計算用の重み
last_updated_at: datetime
```

### 進捗率計算ロジック

```python
# 重み付き進捗率
total_weight = sum(task.weight for task in tasks)
completed_weight = sum(task.weight for task in tasks if task.is_completed)
progress_rate = (completed_weight / total_weight * 100) if total_weight > 0 else 0
```

### UI制約

- `st.data_editor` を使用したExcelライクな編集
- 編集後は `st.session_state` をクリアして `st.rerun()` で画面更新
- タスク名は編集不可（`disabled=True`）
- IDカラムも編集不可

---

## 📊 期待される効果

### 1. 業務標準化
- 標準的な業務フローを自動生成
- 担当者の経験に依存しない一貫した業務遂行

### 2. 進捗可視化
- リアルタイムで進捗率を確認
- 期限超過タスクを即座に把握

### 3. 業務効率化
- タスクの一括管理
- Excelライクな直感的な操作

### 4. データ連携
- 進捗ダッシュボード（提案3）との連携
- 重み付き進捗率の活用

---

## 🐛 トラブルシューティング

### Q1: タスクテンプレートが表示されない

**A:** `python scripts/seed_data.py` を実行してテンプレートを投入してください。

### Q2: タスク初期化ボタンが表示されない

**A:** 既にタスクが存在する案件です。タスク一覧が表示されているはずです。

### Q3: 担当者が「未割当」になる

**A:** 案件にmanager_idまたはoperator_idが設定されていない可能性があります。案件の基本情報を確認してください。

### Q4: 期限日が正しく計算されない

**A:** 案件の契約日（contract_date）が設定されているか確認してください。未設定の場合は今日の日付が基準になります。

---

## 🔄 今後の拡張予定

1. **タスク依存関係の実装**
   - TaskTemplateの`depends_on_template_id`を活用
   - 前工程完了後に次工程を自動開始

2. **タスク通知機能**
   - 期限3日前にアラート
   - 期限超過時の自動通知

3. **タスクテンプレートのカスタマイズ**
   - 案件種別ごとに異なるテンプレート
   - 事務所ごとのカスタマイズ

4. **タスク履歴の記録**
   - 完了日時の記録
   - 変更履歴の追跡

---

## 📝 変更履歴

### 2026-02-12
- 初回実装完了
- 標準タスク9件の定義
- タスク管理UI実装
- テストコード作成

---

## 👥 開発者向け情報

### コーディング規約

- 全関数に型ヒント付与
- docstringに日付を記載
- ログ出力は`logger`を使用
- エラーハンドリングは`try-except-finally`パターン

### テスト方針

- 単体テスト: 各サービスメソッドの動作確認
- 統合テスト: UI→サービス→DBの一連の流れ
- 手動テスト: 実際のStreamlitアプリでの動作確認

### デプロイ前チェックリスト

- [ ] `python scripts/seed_data.py` 実行済み
- [ ] `python tests/test_task_service.py` 全テスト成功
- [ ] Streamlitアプリで手動動作確認
- [ ] データベースマイグレーション実行済み
- [ ] 本番環境でのテストデータ作成

---

## 📞 サポート

問題が発生した場合は、以下の情報を添えてお問い合わせください：

1. エラーメッセージ
2. 実行したコマンド
3. データベースの状態（TaskTemplate、Taskテーブルのレコード数）
4. ログファイル

---

**実装者:** Cascade AI  
**レビュー:** 要確認  
**承認:** 未承認
