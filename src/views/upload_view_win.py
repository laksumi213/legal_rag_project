# src/views/upload_view_win.py
import shutil
from typing import Any

from flet import Column, Icon, Icons, ListTile, ListView, ProgressBar, Text

from components.base.base_component import AppComponent
from components.controls.app_dropzone_win import AppDropzoneWin  # Win用部品
from core.config import Config


class UploadViewWin(AppComponent):
    """
    Windows検証用画面 (flet-dropzone使用)
    """

    def __init__(self):
        super().__init__(expand=True)
        self.padding = 30
        self.upload_dir = Config.DATA_DIR / "uploads"
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.dropzone = AppDropzoneWin(on_drop_callback=self._process_uploaded_file)
        self.file_list = ListView(expand=True, spacing=10)
        self.progress = ProgressBar(visible=False)
        self.status_text = Text("", color="secondary")

        self.content = Column(
            [
                Text("書類取込 (Windows版)", size=28, weight="bold"),
                Text("flet-dropzoneライブラリを使用した実装です。", color="secondary"),
                self.dropzone,
                self.progress,
                self.status_text,
                Text("履歴", size=20, weight="bold"),
                self.file_list,
            ],
            spacing=20,
        )

    async def _process_uploaded_file(self, file_event: Any):
        self.progress.visible = True
        self.status_text.value = f"アップロード中: {file_event.name}..."
        self.update()

        try:
            # Win版ライブラリの場合、pathが取れることが多い
            file_path = getattr(file_event, "path", None)
            save_path = self.upload_dir / file_event.name

            if file_path:
                shutil.copy2(file_path, save_path)
                msg = f"保存完了: {save_path.name}"
            else:
                # ライブラリ仕様によるフォールバックが必要な場合あり
                msg = "ファイルのパスが取得できませんでした (Webモード等)"

            self.file_list.controls.insert(
                0,
                ListTile(
                    leading=Icon(Icons.INSERT_DRIVE_FILE, color="blue"),
                    title=Text(file_event.name),
                    subtitle=Text(f"保存先: {save_path}"),
                    trailing=Icon(Icons.CHECK_CIRCLE, color="green"),
                ),
            )
            self.notify(msg)

        except Exception as e:
            self.notify(f"エラー: {e}", error=True)
        finally:
            self.progress.visible = False
            self.status_text.value = ""
            self.update()
