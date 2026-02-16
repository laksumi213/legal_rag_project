# src/components/controls/app_dropzone_win.py
import asyncio
from typing import Any, Callable, Optional

from flet import (
    Alignment,
    Border,
    BorderSide,
    Column,
    Container,
    Icon,
    Icons,
    Stack,
    Text,
)
from flet_dropzone import Dropzone

from components.base.base_component import AppComponent


class AppDropzoneWin(AppComponent):
    """
    【Windowsテスト用】flet-dropzone ライブラリを使用するバージョン。
    Macでは動作しない可能性があります。
    """

    def __init__(
        self,
        on_drop_callback: Optional[Callable[[Any], None]] = None,
        height: int = 300,
    ):
        super().__init__()
        self.on_drop_callback = on_drop_callback

        # 1. Dropzone初期化 (引数なしで作成し、後でプロパティ設定)
        self.dropzone = Dropzone()
        self.dropzone.on_drop = self._handle_drop
        self.dropzone.on_hover = self._handle_hover
        self.dropzone.on_leave = self._handle_leave

        # 2. UIコンテナ
        self.ui_container = Container(
            content=Column(
                [
                    Icon(Icons.CLOUD_UPLOAD, size=64, color="primary"),
                    Text("【Windows用】ファイルをドロップ", size=20, weight="bold"),
                    Text("flet-dropzoneライブラリ使用", size=14, color="secondary"),
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
            bgcolor="surfaceVariant",  # 文字列で指定
            padding=20,
            alignment=Alignment(0, 0),
            height=height,
        )

        self.content = Stack([self.ui_container, self.dropzone])

    def _handle_hover(self, e):
        self.ui_container.bgcolor = "primaryContainer"
        self.ui_container.border = Border(
            top=BorderSide(2, "primary"),
            bottom=BorderSide(2, "primary"),
            left=BorderSide(2, "primary"),
            right=BorderSide(2, "primary"),
        )
        self.ui_container.update()

    def _handle_leave(self, e):
        self.ui_container.bgcolor = "surfaceVariant"
        self.ui_container.border = Border(
            top=BorderSide(2, "outlineVariant"),
            bottom=BorderSide(2, "outlineVariant"),
            left=BorderSide(2, "outlineVariant"),
            right=BorderSide(2, "outlineVariant"),
        )
        self.ui_container.update()

    async def _handle_drop(self, e: Any):
        self._handle_leave(None)
        if self.on_drop_callback:
            if asyncio.iscoroutinefunction(self.on_drop_callback):
                await self.on_drop_callback(e)
            else:
                self.on_drop_callback(e)
