# src/services/automation/bank_automation_service.py
import logging
import os
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# WebDriverManager (Rye環境に存在すれば使用)
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

logger = logging.getLogger(__name__)


class BankAutomationService:
    """
    銀行手続き（解約・口座凍結）のSelenium自動操作サービス。
    src_legacy から法人格除外ロジックを移植。
    """

    def __init__(self) -> None:
        # Docker環境判定
        self.is_docker = os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER")
        self.headless = True if self.is_docker else False
        logger.info(f"🏦 BankAutomationService Init (Headless: {self.headless})")

    def _get_driver(self) -> webdriver.Chrome:
        """Chrome WebDriverを最適な設定で起動する"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
        else:
            # ローカル開発時はブラウザを表示し、終了後も残す設定
            options.add_experimental_option("detach", True)

        options.add_argument("--disable-blink-features=AutomationControlled")

        try:
            if ChromeDriverManager:
                service = ChromeService(ChromeDriverManager().install())
            else:
                service = ChromeService()

            driver = webdriver.Chrome(service=service, options=options)
            if not self.headless:
                driver.maximize_window()
            return driver
        except Exception as e:
            logger.error(f"❌ WebDriver起動エラー: {e}")
            raise RuntimeError(
                "ブラウザを起動できませんでした。Chromeのインストール状況を確認してください。"
            )

    def _remove_corporate_type(self, name: str) -> str:
        """商号から法人格（株式会社など）を除去"""
        if not name:
            return ""
        targets = ["株式会社", "有限会社", "合同会社", "（株）", "（有）", "(株)"]
        cleaned = name
        for t in targets:
            cleaned = cleaned.replace(t, "")
        return cleaned.strip().replace(" ", "").replace("　", "")

    def execute_mizuho_freeze(self, case_data: Any) -> str:
        """
        みずほ銀行の相続届サイトを起動する。
        将来的に src_legacy/tests/mizuhobank.py の自動入力ロジックをここに統合可能。
        """
        if not case_data:
            return "❌ 案件データがありません"

        driver = self._get_driver()
        try:
            # みずほ銀行 相続手続き受付サイト
            driver.get("https://inherit.m041.mizuhobank.co.jp/apply/applyConsent.php")

            # ページ読み込み待機
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "agree"))
            )

            # --- ここで case_data (被相続人名・住所等) を使った自動入力を行う ---
            # 現時点では、ブラウザを起動してユーザーに引き継ぐまでを行う

            logger.info(f"✅ みずほ銀行サイト起動成功: Case={case_data.case_number}")
            return (
                f"✅ みずほ銀行の入力を開始しました。案件: {case_data.client_name} 様"
            )
        except Exception as e:
            logger.error(f"❌ Selenium Error: {e}")
            if driver:
                driver.quit()
            return f"❌ 自動操作失敗: {e}"
