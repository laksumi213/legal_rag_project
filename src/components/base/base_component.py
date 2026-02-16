# src/components/base/base_component.py
import asyncio

from flet import Container, SnackBar, Text


class AppComponent(Container):
    """
    全てのUIコンポーネントの基底クラス。
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def did_mount(self):
        """マウント時の共通処理"""
        pass

    def notify(self, message: str, error: bool = False):
        """共通通知メソッド"""
        if self.page:
            self.page.show_dialog(
                SnackBar(content=Text(message), bgcolor="error" if error else None)
            )
            self.page.update()

    def run_task(self, coro):
        """
        非同期タスク実行ヘルパー。
        Fletのpage.run_taskは引数仕様が厳格なため、
        より柔軟なasyncio.create_taskを直接使用してタスクをスケジュールします。
        """
        return asyncio.create_task(coro)
