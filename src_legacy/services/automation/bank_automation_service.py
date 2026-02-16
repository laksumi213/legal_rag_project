# src/services/automation/bank_automation_service.py
import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)


class BankAutomationService:
    """銀行手続き（解約・口座凍結）のSelenium自動操作サービス"""

    def __init__(self):
        self.is_docker = os.path.exists("/.dockerenv")

    def _get_driver(self):
        options = Options()
        if self.is_docker:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        else:
            options.add_experimental_option("detach", True)

        return webdriver.Chrome(options=options)

    def execute_mizuho_freeze(self, case_data: Any) -> str:
        """みずほ銀行の相続届・口座凍結サイトを自動入力 (サンプル実装)"""
        driver = self._get_driver()
        try:
            driver.get("https://inherit.m041.mizuhobank.co.jp/apply/applyConsent.php")
            # 本来はここで case_data を使って DOM 操作を行います
            time.sleep(3)
            return "✅ みずほ銀行の入力画面を起動しました。内容を確認してください。"
        except Exception as e:
            logger.error(f"Selenium Error: {e}")
            return f"❌ 自動操作エラー: {e}"
