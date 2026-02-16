# src/views/upload_view.py
import asyncio
import shutil
from typing import Any

from flet import (
    Alignment,
    Border,
    BorderSide,
    Column,
    Container,
    FilePicker,
    Icon,
    Icons,
    ListTile,
    ListView,
    ProgressBar,
    Text,
)

from components.base.base_component import AppComponent
from core.config import Config


class UploadView(AppComponent):
    """
    Mac / Native D&D 対応版
    Flet v0.80.5 規約準拠: イベント型の直接インポートを回避
    """

    def __init__(self):
        super().__init__(expand=True)
        self.padding = 30
        self.upload_dir = Config.DATA_DIR / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # クリック選択用 (引数なしで初期化し、プロパティ代入)
        self.file_picker = FilePicker()
        self.file_picker.on_result = self._handle_picker

        self.ui_zone = Container(
            content=Column(
                [
                    Icon(Icons.CLOUD_UPLOAD, size=64, color="primary"),
                    Text(
                        "【Mac用】ファイルをウィンドウにドロップ",
                        size=20,
                        weight="bold",
                    ),
                    Text("またはここをクリックして選択", size=14, color="secondary"),
                ],
                alignment="center",
                horizontal_alignment="center",
            ),
            border=Border(
                top=BorderSide(2, "outlineVariant"),
                bottom=BorderSide(2, "outlineVariant"),
                left=BorderSide(2, "outlineVariant"),
                right=BorderSide(2, "outlineVariant"),
            ),
            border_radius=10,
            bgcolor="surfaceVariant",
            padding=20,
            alignment=Alignment(0, 0),
            height=300,
            on_click=lambda _: self.file_picker.pick_files(allow_multiple=True),
        )

        self.file_list = ListView(expand=True, spacing=10)
        self.progress = ProgressBar(visible=False)
        self.status_text = Text("", color="secondary")

        self.content = Column(
            [
                Text("書類取込 (Mac/Native)", size=28, weight="bold"),
                Text("ウィンドウ全体へのドロップを受け付けます。", color="secondary"),
                self.ui_zone,
                self.progress,
                self.status_text,
                Text("履歴", size=20, weight="bold"),
                self.file_list,
            ],
            spacing=20,
        )

    def did_mount(self):
        """ページ全体のドロップイベントを登録"""
        if self.page:
            if self.file_picker not in self.page.overlay:
                self.page.overlay.append(self.file_picker)
            self.page.on_file_drop = self._handle_native_drop
            self.page.update()

    def will_unmount(self):
        if self.page:
            self.page.on_file_drop = None

    async def _handle_native_drop(self, e: Any):
        """ウィンドウへのドロップハンドラ (型指定なし)"""
        self.ui_zone.bgcolor = "primaryContainer"
        self.ui_zone.update()
        await asyncio.sleep(0.2)
        self.ui_zone.bgcolor = "surfaceVariant"
        self.ui_zone.update()

        if hasattr(e, "files") and e.files:
            for f in e.files:
                await self._process_file(f)

    def _handle_picker(self, e: Any):
        """ファイルピッカーのハンドラ"""
        if hasattr(e, "files") and e.files:
            for f in e.files:
                asyncio.create_task(self._process_file(f))

    async def _process_file(self, file_obj: Any):
        self.progress.visible = True
        self.status_text.value = f"処理中: {file_obj.name}..."
        self.update()
        try:
            file_path = getattr(file_obj, "path", None)
            save_path = self.upload_dir / file_obj.name
            if file_path:
                shutil.copy2(file_path, save_path)
                msg = f"保存完了: {save_path.name}"
                self.file_list.controls.insert(
                    0,
                    ListTile(
                        leading=Icon(Icons.INSERT_DRIVE_FILE, color="blue"),
                        title=Text(file_obj.name),
                        trailing=Icon(Icons.CHECK_CIRCLE, color="green"),
                    ),
                )
                self.notify(msg)
            else:
                self.notify("パス取得失敗", error=True)
        except Exception as ex:
            self.notify(f"エラー: {ex}", error=True)
        finally:
            self.progress.visible = False
            self.status_text.value = ""
            self.update()
