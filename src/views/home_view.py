# src/views/home_view.py
import asyncio

from flet import (
    ButtonStyle,
    Card,
    Column,
    Container,
    Control,
    CrossAxisAlignment,
    ElevatedButton,
    FontWeight,
    Icon,
    Icons,
    ProgressRing,
    Row,
    Text,
)
from services.case_service import CaseService

from components.base.base_component import AppComponent


class HomeView(AppComponent):
    def __init__(self):
        super().__init__(expand=True)
        self.case_service = CaseService()
        self.padding = 30

        # ローディング表示用
        self.loading = ProgressRing(visible=True)
        self.stats_row = Row(visible=False)

        self.content = Column(
            controls=[
                self._build_header(),
                self.loading,
                self.stats_row,
                Text(
                    "クイックアクション",
                    size=20,
                    weight=FontWeight.BOLD,
                    color="primary",
                ),
                self._build_actions_row(),
            ],
            scroll="auto",
            spacing=20,
        )

    def did_mount(self):
        # データロード開始
        self.run_task(self._load_data())

    def _build_header(self) -> Control:
        return Column(
            [
                Text("遺産承継・遺言作成支援システム", size=32, weight=FontWeight.BOLD),
                Text("本日の業務概要とステータス", size=16, color="secondary"),
            ]
        )

    def _build_stat_card(
        self, title: str, value: str, icon: str, color: str
    ) -> Control:
        return Card(
            content=Container(
                content=Column(
                    [
                        Icon(icon, color=color, size=30),
                        Text(value, size=40, weight=FontWeight.BOLD, color=color),
                        Text(title, size=14, color="onSurfaceVariant"),
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                ),
                padding=20,
                width=150,
                height=150,
                bgcolor="surfaceVariant",
            )
        )

    def _build_actions_row(self) -> Control:
        return Row(
            controls=[
                ElevatedButton(
                    "新規案件登録",
                    icon=Icons.ADD,
                    style=ButtonStyle(padding=20),
                    on_click=lambda e: self.notify("機能実装中です"),
                ),
                ElevatedButton(
                    "顧客検索",
                    icon=Icons.SEARCH,
                    style=ButtonStyle(padding=20),
                    on_click=lambda e: self.notify("検索機能実装中です"),
                ),
            ]
        )

    async def _load_data(self):
        """DBからデータを非同期で取得"""
        try:
            # 重い処理はスレッドに逃がす
            stats = await asyncio.to_thread(self.case_service.get_dashboard_summary)

            # UI構築
            self.stats_row.controls = [
                self._build_stat_card(
                    "進行中の案件",
                    str(stats.get("active", 0)),
                    Icons.PENDING_ACTIONS,
                    "blue",
                ),
                self._build_stat_card(
                    "完了案件", str(stats.get("completed", 0)), Icons.TASK_ALT, "green"
                ),
                self._build_stat_card(
                    "アラート", str(stats.get("warning", 0)), Icons.WARNING_AMBER, "red"
                ),
            ]

            self.loading.visible = False
            self.stats_row.visible = True
            self.update()

        except Exception as e:
            self.notify(f"データ取得エラー: {e}", error=True)
            self.loading.visible = False
            self.update()
