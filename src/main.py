# src/main.py

import asyncio
import logging
import subprocess

from flet import (
    Container,
    Icons,
    NavigationRail,
    NavigationRailDestination,
    Page,
    Row,
    SnackBar,
    Text,
    Theme,
    ThemeMode,
    VerticalDivider,
    run,
)

from core.config import Config
from database.manager import DatabaseManager
from views.home_view import HomeView

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AppShell:
    """
    NavigationRailを備えたメインウィンドウシェル。
    """

    def __init__(self, page: Page, db: DatabaseManager):
        self.page = page
        self.db = db
        self.content_area = Container(expand=True, padding=20)
        self.rail = NavigationRail(
            selected_index=0,
            label_type="all",
            min_width=100,
            min_extended_width=200,
            bgcolor="surfaceVariant",
            destinations=[
                NavigationRailDestination(
                    icon=Icons.HOME_OUTLINED, selected_icon=Icons.HOME, label="ホーム"
                ),
                NavigationRailDestination(
                    icon=Icons.FOLDER_OPEN_OUTLINED,
                    selected_icon=Icons.FOLDER_OPEN,
                    label="書類管理",
                ),
                NavigationRailDestination(
                    icon=Icons.SETTINGS_OUTLINED,
                    selected_icon=Icons.SETTINGS,
                    label="設定",
                ),
            ],
            on_change=self.handle_nav_change,
        )

    def build(self) -> Row:
        return Row(
            [self.rail, VerticalDivider(width=1), self.content_area],
            expand=True,
            spacing=0,
        )

    async def handle_nav_change(self, e):
        idx = e.control.selected_index
        if idx == 0:
            await self.set_view("home")
        else:
            # 修正: page.open -> page.snack_bar
            self.page.snack_bar = SnackBar(content=Text("この画面は開発中です"))
            self.page.snack_bar.open = True
            self.page.update()

    async def set_view(self, view_name: str):
        if view_name == "home":
            self.content_area.content = HomeView(self.db, self.page)
        self.page.update()


def run_code_aggregation_sync():
    """ソースコードを集約して repomix-output.md を生成します。"""
    logger.info("🚀 ソースコードの集約を開始します...")
    command = "npx -y repomix --style markdown"
    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=Config.BASE_DIR,
            capture_output=True,
            text=True,
        )
        logger.info("✅ ソースコードの集約が完了しました")
        return True
    except Exception as e:
        logger.error(f"❌ コード集約失敗: {e}")
        return False


async def main(page: Page):
    Config.validate_environment()
    page.title = Config.APP_TITLE
    page.window_width = 1300
    page.window_height = 900
    page.theme_mode = ThemeMode.LIGHT
    page.theme = Theme(color_scheme_seed="#d33682", use_material3=True)

    db_manager = DatabaseManager()
    shell = AppShell(page, db_manager)
    page.add(shell.build())
    await shell.set_view("home")

    async def run_bg_tasks():
        # 1. データベーステーブル作成
        try:
            await asyncio.to_thread(db_manager.create_tables)
            logger.info("✅ DB準備完了")
        except Exception as e:
            logger.error(f"❌ DB接続エラー: {e}")

        # 2. ソースコード集約実行
        if await asyncio.to_thread(run_code_aggregation_sync):
            # 修正: page.open -> page.snack_bar
            page.snack_bar = SnackBar(content=Text("コードの最新集約が完了しました。"))
            page.snack_bar.open = True
            page.update()

    asyncio.create_task(run_bg_tasks())


if __name__ == "__main__":
    run(main)
