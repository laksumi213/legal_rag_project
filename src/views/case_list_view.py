# src/views/case_list_view.py
import asyncio

from flet import (
    Colors,
    Column,
    Icon,
    Icons,
    ListTile,
    ListView,
    MainAxisAlignment,
    ProgressRing,
    Row,
    Text,
    TextField,
)

from components.base.base_component import AppComponent
from services.case_service import CaseService


class CaseListView(AppComponent):
    def __init__(self):
        super().__init__(expand=True)
        self.service = CaseService()
        self.padding = 20
        # main.pyから渡される遷移用コールバック
        self.on_case_select = None

        self.search_field = TextField(
            label="案件番号・氏名で検索",
            prefix_icon=Icons.SEARCH,
            on_submit=self._handle_search,
            expand=True,
        )
        self.loader = ProgressRing(visible=False, width=20, height=20)
        self.list_view = ListView(expand=True, spacing=10)

        self.content = Column(
            [
                Row(
                    [Text("案件管理", size=28, weight="bold"), self.loader],
                    alignment=MainAxisAlignment.START,
                ),
                self.search_field,
                self.list_view,
            ],
            spacing=20,
        )

    def did_mount(self):
        self.run_task(self._load_all_cases())

    async def _handle_search(self, e):
        await self._load_all_cases(e.control.value)

    async def _load_all_cases(self, query: str = ""):
        self.loader.visible = True
        self.list_view.controls.clear()
        self.update()

        try:
            cases = await asyncio.to_thread(self.service.get_all_cases)
            if query:
                q = query.lower()
                cases = [
                    c
                    for c in cases
                    if q in (c.case_number or "").lower()
                    or q in (c.client_name or "").lower()
                ]

            for c in cases:
                self.list_view.controls.append(
                    ListTile(
                        leading=Icon(Icons.FOLDER_OPEN, color=Colors.BLUE_400),
                        title=Text(f"{c.case_number}: {c.client_name} 様"),
                        trailing=Icon(Icons.CHEVRON_RIGHT),
                        # クリック時にコールバックを実行
                        on_click=lambda _, cid=c.case_id: self._on_click_item(cid),
                    )
                )
        except Exception as ex:
            self.notify(f"ロードエラー: {ex}", error=True)
        finally:
            self.loader.visible = False
            self.update()

    def _on_click_item(self, case_id: int):
        if self.on_case_select:
            self.on_case_select(case_id)
