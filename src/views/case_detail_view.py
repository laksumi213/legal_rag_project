# src/views/case_detail_view.py
import asyncio
import base64
import datetime
import os
from typing import Optional  # ★追加: Optionalを明示的にインポート

from flet import (
    Alignment,
    Card,
    Colors,
    Column,
    Container,
    Divider,
    Dropdown,
    ElevatedButton,
    FilePicker,
    FontWeight,
    Icon,
    Icons,
    Image,
    ProgressBar,
    Row,
    ScrollMode,
    Text,
    border,
    dropdown,
)

from components.base.base_component import AppComponent
from core.config import Config
from services.automation.bank_automation_service import BankAutomationService
from services.bank_procedure_service import BankProcedureService, GeneratedPdf
from services.case_service import CaseService
from utils.pdf_utils import convert_pdf_to_images


class CaseDetailView(AppComponent):
    def __init__(self, case_id: int):
        super().__init__(expand=True)
        self.case_id = case_id
        self.case_service = CaseService()
        self.padding = 30

        # 状態管理
        self.current_pdf: Optional[GeneratedPdf] = None
        self.case_data = None

        # UI部品の初期化
        self.title_text = Text(
            "案件詳細を読み込み中...", size=28, weight=FontWeight.BOLD
        )
        self.loading_bar = ProgressBar(visible=True)
        self.bank_selector = Dropdown(label="対象銀行を選択", width=300)
        self.template_selector = Dropdown(label="テンプレートを選択", width=400)
        self.asset_list = Column(spacing=10)  # ★セイウチ演算子エラーを解消済み

        self.preview_image = Image(
            visible=False, border_radius=10, fit="contain", height=500
        )
        self.preview_container = Container(
            content=self.preview_image,
            alignment=Alignment(0, 0),
            visible=False,
            border=border.all(1, Colors.OUTLINE_VARIANT),
            border_radius=10,
            padding=10,
        )

        self.file_picker = FilePicker(on_result=self._handle_save_result)
        self.btn_download = ElevatedButton(
            "名前を付けて保存",
            icon=Icons.DOWNLOAD,
            visible=False,
            on_click=lambda _: self.file_picker.save_file(
                file_name=self.current_pdf.filename
                if self.current_pdf
                else "output.pdf"
            ),
        )

        # レイアウト構築
        self.content = Column(
            [
                self.title_text,
                self.loading_bar,
                Divider(),
                Row(
                    [
                        Icon(Icons.AUTO_FIX_HIGH, color=Colors.PRIMARY),
                        Text("帳票作成・自動化", size=20, weight=FontWeight.BOLD),
                    ]
                ),
                Row(
                    [
                        self.bank_selector,
                        self.template_selector,
                        ElevatedButton(
                            "PDF生成・プレビュー",
                            icon=Icons.PICTURE_AS_PDF,
                            on_click=self._handle_generate_pdf,
                        ),
                        self.btn_download,
                        ElevatedButton(
                            "ブラウザ自動操作 (解約)",
                            icon=Icons.OPEN_IN_BROWSER,
                            bgcolor=Colors.ORANGE_700,
                            color=Colors.WHITE,
                            on_click=self._handle_bank_automation,
                        ),
                    ],
                    spacing=20,
                ),
                self.preview_container,
                Divider(),
                Text("資産情報一覧", size=18, weight=FontWeight.BOLD),
                self.asset_list,
            ],
            scroll=ScrollMode.AUTO,
            spacing=20,
        )

    def did_mount(self):
        # FilePicker登録 (Flet v0.80.5 準拠)
        if self.file_picker not in self.page.overlay:
            self.page.overlay.append(self.file_picker)
            self.page.update()
        self.run_task(self._load_case_details())

    async def _load_case_details(self):
        self.case_data = await asyncio.to_thread(
            self.case_service.get_case_detail, self.case_id
        )
        if not self.case_data:
            self.notify("案件が見つかりませんでした", error=True)
            return

        self.title_text.value = (
            f"{self.case_data.case_number}: {self.case_data.client_name} 様"
        )
        self.asset_list.controls.clear()
        self.bank_selector.options.clear()

        for asset in self.case_data.financial_assets or []:
            bank_name = asset.bank_ref.bank_name if asset.bank_ref else "不明"
            self.asset_list.controls.append(
                Card(
                    content=Container(
                        padding=15,
                        content=Row(
                            [
                                Icon(Icons.ACCOUNT_BALANCE, color=Colors.BLUE_400),
                                Column(
                                    [
                                        Text(
                                            f"{bank_name} ({asset.account_number})",
                                            weight="bold",
                                        ),
                                        Text(
                                            f"残高: ¥{int(asset.balance or 0):,}",
                                            color=Colors.SECONDARY,
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    )
                )
            )
            self.bank_selector.options.append(
                dropdown.Option(str(asset.id), f"{bank_name} ({asset.account_number})")
            )

        template_dir = Config.DATA_DIR / "templates"
        if template_dir.exists():
            files = [f for f in os.listdir(template_dir) if f.lower().endswith(".pdf")]
            self.template_selector.options = [dropdown.Option(f, f) for f in files]

        self.loading_bar.visible = False
        self.update()

    async def _handle_generate_pdf(self, e):
        if not self.bank_selector.value or not self.template_selector.value:
            self.notify("銀行とテンプレートを選択してください", error=True)
            return
        self.loading_bar.visible = True
        self.update()
        try:
            svc = BankProcedureService()
            template_path = str(
                Config.DATA_DIR / "templates" / self.template_selector.value
            )
            # 現在の日付を使用
            result = await asyncio.to_thread(
                svc.generate_mizuho_balance_certificate_pdf,
                case_id=self.case_id,
                financial_asset_id=int(self.bank_selector.value),
                template_path=template_path,
                created_on=datetime.date.today(),
            )
            self.current_pdf = result
            # プレビュー生成 (pdf_utils)
            images = await asyncio.to_thread(
                convert_pdf_to_images, result.pdf_bytes, dpi=100
            )
            if images:
                from io import BytesIO

                buffered = BytesIO()
                images[0].save(buffered, format="PNG")
                self.preview_image.src_base64 = base64.b64encode(
                    buffered.getvalue()
                ).decode()
                self.preview_image.visible = True
                self.preview_container.visible = True
                self.btn_download.visible = True
            self.notify(f"PDFプレビュー準備完了: {result.filename}")
        except Exception as ex:
            self.notify(f"エラー: {ex}", error=True)
        finally:
            self.loading_bar.visible = False
            self.update()

    async def _handle_bank_automation(self, e):
        """Seleniumを別スレッドで起動して銀行解約サイトへ飛ばす"""
        self.notify("自動操作ブラウザを起動しています...")
        svc = BankAutomationService()
        # 重い外部プロセス実行は asyncio.to_thread で実行
        msg = await asyncio.to_thread(svc.execute_mizuho_freeze, self.case_data)
        self.notify(msg)

    def _handle_save_result(self, e):
        if e.path and self.current_pdf:
            try:
                with open(e.path, "wb") as f:
                    f.write(self.current_pdf.pdf_bytes)
                self.notify(f"保存しました: {e.path}")
            except Exception as ex:
                self.notify(f"保存エラー: {ex}", error=True)
