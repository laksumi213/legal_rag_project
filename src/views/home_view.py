# src/views/home_view.py

import asyncio

from flet import (
    Column,
    Container,
    ElevatedButton,
    Icons,
    ListTile,
    ListView,
    Page,
    ProgressRing,
    Row,
    SnackBar,
    Text,
)

from database.manager import DatabaseManager


class HomeView(Column):
    def __init__(self, db: DatabaseManager, page: Page):
        super().__init__()
        self.db = db
        self.main_page = page
        self.expand = True
        self.spacing = 20

        self.loading_indicator = ProgressRing(visible=False, width=20, height=20)
        self.case_list = ListView(expand=True, spacing=10)
        self.refresh_button = ElevatedButton(
            "案件リストを更新",
            icon=Icons.REFRESH,
            on_click=self.load_cases_clicked,
            bgcolor="primary",
            color="onPrimary",
        )

        self.controls = [
            Text("案件概要・基本情報", size=28, weight="bold"),
            Row([self.refresh_button, self.loading_indicator]),
            Container(
                content=self.case_list,
                expand=True,
                border_radius=10,
                bgcolor="surfaceVariant",
                padding=10,
            ),
        ]

    def did_mount(self):
        """同期メソッドとして定義し、その中で非同期タスクをスケジュールする"""
        # ページ読み込み時に自動的にデータ取得を開始
        asyncio.create_task(self.load_cases_clicked(None))

    async def load_cases_clicked(self, e):
        """DBから案件リストを取得。"""
        self.refresh_button.disabled = True
        self.loading_indicator.visible = True
        self.update()

        try:
            cases = await asyncio.to_thread(self.db.fetch_all_cases_sync)
            self.case_list.controls.clear()
            if not cases:
                self.case_list.controls.append(
                    Text("案件が登録されていません", italic=True)
                )
            else:
                for case in cases:
                    self.case_list.controls.append(
                        ListTile(
                            leading=Icons.BUSINESS_CENTER,
                            title=Text(f"{case.case_number}: {case.client_name}"),
                            subtitle=Text(
                                f"登録日: {case.created_at.strftime('%Y/%m/%d')}"
                            ),
                        )
                    )
        except Exception as ex:
            # 修正: page.open -> page.snack_bar
            self.main_page.snack_bar = SnackBar(Text(f"読み込みエラー: {str(ex)}"))
            self.main_page.snack_bar.open = True
            self.main_page.update()
        finally:
            self.refresh_button.disabled = False
            self.loading_indicator.visible = False
            self.update()
