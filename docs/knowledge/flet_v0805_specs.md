# Flet v0.80.5 準拠：プロジェクト専用技術リファレンス

このドキュメントは、Flet v0.80.5 以降の仕様変更および本プロジェクト固有のコーディング規約を定義するものです。AIはこのルールを最優先で遵守する必要があります。

## 1. 根本的な変更：非同期APIの同期化
Flet v0.80.0以降、主要なUI操作メソッドが「非同期（awaitが必要なもの）」から「同期（awaitが不要なもの）」へ変更されました。

### 同期的に記述すべき主要メソッド（await禁止）
* `page.add()` : 以前の `add_async` は廃止されました。awaitなしで呼び出してください。
* `page.update()` : 以前の `update_async` は廃止されました。awaitなしで呼び出してください。
* `control.update()` : すべてのUIコントロールの更新は同期的に実行します。
* `page.open()` / `page.close()` : ダイアログ操作全般（SnackBarは下記の特定構文を優先）。

### 非同期のまま残る処理
* ネットワーク通信、データベース操作（SQLAlchemy）、外部プロセス実行など。
* これらは `await asyncio.to_thread()` で実行し、UIスレッドをブロックしないようにしてください。

## 2. コントロール設計の現代化
### UserControl の廃止
* `UserControl` クラスは完全に廃止されました。
* **推奨**: `Column`, `Row`, `Container` などの既存コントロールを直接継承してクラスを定義します。

```python
class MyView(Column):
    def __init__(self, page: Page):
        super().__init__()
        self.main_page = page  # self.pageの衝突を避けるため main_page という変数名を使用
        self.controls = [Text("Hello")]

ライフサイクルの定義
did_mount は同期メソッド def did_mount(self): として定義してください。

内部で非同期タスク（初期データのロードなど）を開始したい場合は、asyncio.create_task() を使用してください。

3. UIコンポーネントの特定構文
通知 (SnackBar)
以下の特定のメソッドと構文を使用して通知を表示してください。

Python
# 必須構文
page.show_dialog(SnackBar(content=Text("メッセージ内容")))
page.update()
オーバーレイと非表示コントロール (FilePicker等)
重要: FilePicker 等は __init__ で on_result 等の引数を取ると TypeError になります。

インスタンス作成後にプロパティへ代入し、page.overlay.append() で登録してください。

Python
# 正しい実装手順
self.file_picker = FilePicker()
self.file_picker.on_result = self.on_result # プロパティ代入（必須）
page.overlay.append(self.file_picker)       # オーバーレイ登録（必須）
page.update()
4. プロジェクト構造とインポート
インポートの制限
インポートパスには src ディレクトリを含めないでください。

イベントクラスの制限: FilePickerResultEvent 等を flet から直接インポートするとエラーになるため、イベント引数の型指定は避けてください。

パス解決の原則
アセットへのパスは src/core/config.py の BASE_DIR からの相対パスで指定してください。

sys._MEIPASS を常に優先するパス解決ロジックを維持してください。


---

### 次にすべきこと
1.  **カスタム指示の上書き**: Geminiの設定画面で上記セクションを更新し、保存してください。
2.  **ナレッジファイルの更新**: `flet_v0805_specs.md` を上記内容で上書きし、Gemの「知識（Knowledge）」に再アップロードしてください。
3.  **動作確認**: `rye run start` を実行し、今度は `TypeError` なしで D&D テスト画面が開くことを確認してください。

無事に起動しましたら、**「PostgreSQLのデータ移行スクリプト（scripts/migrate_postgres_data.py）」** の作成に移りましょうか？