# src/main.py
import sys
from pathlib import Path

# インポートパスの解決
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import asyncio
import logging

import flet
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
)

# 各種モジュールのインポート
from core.config import Config
from database.manager import DatabaseManager
from utils.repomix_runner import run_repomix_sync
from views.case_detail_view import CaseDetailView
from views.case_list_view import CaseListView

# ビュー（画面）のインポート
from views.home_view import HomeView
from views.upload_view import UploadView as UploadViewMac  # Mac用 (Native D&D)
from views.upload_view_win import UploadViewWin  # Win用 (flet-dropzone)

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


class AppShell(Row):
    """
    アプリケーション全体の骨格。
    サイドバーでMac用/Windows用のアップロード機能を切り替え可能にします。
    """

    def __init__(self, page: Page, db: DatabaseManager):
        super().__init__(expand=True, spacing=0)
        self.main_page = page
        self.db = db
        self.content_area = Container(expand=True, padding=0)

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
                # OS別のテスト用メニュー
                NavigationRailDestination(
                    icon=Icons.APPLE, selected_icon=Icons.APPLE, label="書類取込(Mac)"
                ),
                NavigationRailDestination(
                    icon=Icons.WINDOW, selected_icon=Icons.WINDOW, label="書類取込(Win)"
                ),
                NavigationRailDestination(
                    icon=Icons.FOLDER_OPEN_OUTLINED,
                    selected_icon=Icons.FOLDER_OPEN,
                    label="案件管理",
                ),
                NavigationRailDestination(
                    icon=Icons.SETTINGS_OUTLINED,
                    selected_icon=Icons.SETTINGS,
                    label="設定",
                ),
            ],
            on_change=self.handle_nav_change,
        )
        self.controls = [self.rail, VerticalDivider(width=1), self.content_area]

    def handle_nav_change(self, e):
        idx = e.control.selected_index
        if idx == 0:
            self.set_view("home")
        elif idx == 1:
            self.set_view("upload_mac")
        elif idx == 2:
            self.set_view("upload_win")
        elif idx == 3:
            self.set_view("case_list")
        elif idx == 4:
            self.set_view("settings")

    def set_view(self, view_name: str, params: dict = None):
        """指定されたビュー名に基づいてコンテンツエリアを更新"""
        if view_name == "home":
            self.content_area.content = HomeView()
        elif view_name == "upload_mac":
            self.content_area.content = UploadViewMac()  # Mac用 Native D&D版
        elif view_name == "upload_win":
            self.content_area.content = UploadViewWin()  # Windows用 flet-dropzone版
        elif view_name == "case_list":
            view = CaseListView()
            view.on_case_select = lambda cid: self.set_view(
                "case_detail", {"case_id": cid}
            )
            self.content_area.content = view
        elif view_name == "case_detail":
            case_id = params.get("case_id")
            self.content_area.content = CaseDetailView(case_id)
        elif view_name == "settings":
            self.content_area.content = Container(
                content=Text("設定画面は準備中です", size=20), padding=50
            )

        self.main_page.update()  # Flet v0.80.5 同期更新


async def main(page: Page):
    # 1. ページ初期設定
    Config.validate_environment()
    page.title = Config.APP_TITLE
    page.theme_mode = ThemeMode.LIGHT
    page.theme = Theme(color_scheme_seed="#d33682", use_material3=True)
    page.window_width = 1300
    page.window_height = 900

    # ★修正ポイント: page.overlayへの代入(= [])を削除。
    # Flet v0.80.5では overlay は読み取り専用プロパティのため、初期化不要。

    # 2. DB初期化
    db_manager = DatabaseManager()

    # 3. UI構築
    shell = AppShell(page, db_manager)
    page.add(shell)
    shell.set_view("home")

    # 4. スタートアップタスク
    async def run_startup_tasks():
        # DBテーブル作成
        await asyncio.to_thread(db_manager.create_tables)
        logger.info("✅ DB準備完了")

        # Repomix自動実行 (ソースコード集約)
        success = await asyncio.to_thread(run_repomix_sync)
        if success:
            page.show_dialog(
                SnackBar(content=Text("🚀 コード集約(Repomix)が完了しました"))
            )
            page.update()

    asyncio.create_task(run_startup_tasks())


if __name__ == "__main__":
    # Flet v0.80.5 準拠の起動方式
    flet.run(main)
