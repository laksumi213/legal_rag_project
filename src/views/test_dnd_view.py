# src/views/test_dnd_view.py

import datetime
import json
import logging

from flet import (
    Alignment,
    Column,
    Container,
    CrossAxisAlignment,
    FilePicker,
    Icon,
    Icons,
    ListView,
    MainAxisAlignment,
    Page,
    SnackBar,
    Text,
    border,
)

logger = logging.getLogger(__name__)


class TestDnDView(Column):
    """
    Flet v0.80.5 準拠: ネイティブD&Dテストビュー。
    Tkinterを使用せず、Fletのウィンドウイベントで Finder からのドロップを捕捉します。
    """

    def __init__(self, page: Page):
        super().__init__()
        self.main_page = page
        self.expand = True
        self.spacing = 20

        # --- 1. FilePickerの初期化 (オーバーレイ専用) ---
        # 規約: インスタンス作成後にハンドラを代入する
        self.file_picker = FilePicker()
        self.file_picker.on_result = self.on_file_result

        # 規約: page.overlay.append() を使用 (controlsリストへの混入禁止)
        if self.file_picker not in self.main_page.overlay:
            self.main_page.overlay.append(self.file_picker)

        # 規約: デスクトップ版の外部ドロップはウィンドウイベントで監視
        self.main_page.on_window_event = self.handle_window_event

        # --- 2. UIコンポーネントの定義 ---
        self.log_list = ListView(expand=True, spacing=5)

        # ドロップターゲット領域 (デザインを強化)
        self.drop_zone = Container(
            content=Column(
                [
                    Icon(Icons.UPLOAD_FILE_ROUNDED, size=64, color="primary"),
                    Text("Finderからファイルをここにドロップ", size=20, weight="bold"),
                    Text(
                        "またはクリックしてファイルを選択", size=14, color="secondary"
                    ),
                ],
                alignment=MainAxisAlignment.CENTER,
                horizontal_alignment=CrossAxisAlignment.CENTER,
            ),
            border_radius=20,
            border=border.all(2, "outlineVariant"),
            bgcolor="surfaceVariant",  # テーマカラーを使用
            padding=40,
            alignment=Alignment(0, 0),
            expand=True,
            on_click=self.on_click_drop_zone,  # 非同期呼び出し
            on_hover=self.handle_hover,
        )

        # 画面レイアウトの構築
        self.controls = [
            Text("Flet ネイティブ・ドラッグ＆ドロップ", size=28, weight="bold"),
            self.drop_zone,
            Text("イベント履歴:", size=16, weight="bold"),
            Container(
                content=self.log_list,
                expand=True,
                border_radius=10,
                bgcolor="surface",
                padding=10,
                border=border.all(1, "outlineVariant"),
            ),
        ]

    def did_mount(self):
        """同期ライフサイクルメソッド: UI描画確定後に1度だけ更新"""
        self._add_log("システム準備完了: macOS Finder からの入力を待機中...")
        self.main_page.update()

    # --- イベントハンドラ ---

    async def on_click_drop_zone(self, e):
        """クリック時にファイルピッカーを起動 (非同期 await 必須)"""
        try:
            # 非同期アプリモードでは await が必要
            await self.file_picker.pick_files(allow_multiple=True)
        except Exception as ex:
            logger.error(f"FilePicker error: {ex}")

    def on_file_result(self, e):
        """FilePicker選択結果の処理"""
        if e.files:
            msg = f"選択完了: {len(e.files)} 件のファイル"
            self._add_log(msg)
            self._show_notification(msg)

    async def handle_window_event(self, e):
        """
        macOS Finder等からの外部ドロップイベントを捕捉
        Flet v0.80.5 Desktop版では e.data に JSON が届く
        """
        if e.data:
            try:
                event_data = json.loads(e.data)
                if event_data.get("event_type") == "drop":
                    files = event_data.get("files", [])
                    msg = f"外部ドロップ検知: {len(files)} 件のファイル"
                    self._add_log(msg)
                    for f in files:
                        self._add_log(f" -> Path: {f}")
                    self._show_notification(msg)
            except:
                if e.data == "drop":
                    self._add_log("外部ドロップイベントを検知しました")

    def handle_hover(self, e):
        """マウスホバー時の視覚効果"""
        self.drop_zone.bgcolor = (
            "primaryContainer" if e.data == "true" else "surfaceVariant"
        )
        self.update()

    def _add_log(self, message: str):
        """ログリストに時刻付きで追加"""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_list.controls.insert(0, Text(f"[{now}] {message}", size=12))
        self.update()

    def _show_notification(self, message: str):
        """規約指定の SnackBar 表示構文"""
        self.main_page.show_dialog(SnackBar(content=Text(message)))
        self.main_page.update()
