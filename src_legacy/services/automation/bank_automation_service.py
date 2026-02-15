# src/services/automation/bank_automation_service.py

import logging
import os
import re
import time
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from legal_system.utils.retry_decorator import retry_with_backoff

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BankAutomationService:
    """
    銀行手続き自動化の共通基盤サービスクラス
    ToukiServiceのWebDriver起動・リトライ・法人格除外ロジックを継承
    """

    def __init__(self) -> None:
        self.is_docker = os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER")
        self.headless = True if self.is_docker else False
        logger.info(f"🏦 BankAutomationService Initialized. Headless: {self.headless}")

    def _get_driver(self):
        """Chrome WebDriverの初期化と設定（ToukiServiceから継承）"""
        options = Options()

        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_experimental_option("detach", True)
            options.add_argument("--window-position=0,0")
            options.add_argument("--window-size=1280,800")

        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

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
            logger.error(f"❌ WebDriverの起動に失敗しました: {e}")
            raise Exception(f"ブラウザ起動エラー: {e}")

    def _wait_and_click(self, driver, by, value, timeout=10):
        """指定した要素が表示されクリック可能になるまで待機してクリック"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            logger.info(f"Clicked element: {value}")
        except Exception as e:
            logger.error(f"Click failed for {value}: {e}")
            raise

    def _wait_and_send_keys(self, driver, by, value, text, timeout=10):
        """指定した要素が表示されるまで待機してテキストを入力"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            element.clear()
            element.send_keys(text)
            logger.info(f"Sent keys to {value}")
        except Exception as e:
            logger.error(f"Send keys failed for {value}: {e}")
            raise

    def _to_zenkaku(self, text: str) -> str:
        """半角を全角に変換"""
        if not text:
            return ""
        return text.translate(
            str.maketrans(
                "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ",
                "０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！"＃＄％＆'（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝～　",
            )
        )

    def _remove_corporate_type(self, name: str) -> str:
        """
        商号から法人格（株式会社など）を除去し、スペースも削除する
        例: 株式会社並木管財 -> 並木管財
        （ToukiServiceから継承）
        """
        if not name:
            return ""
        targets = [
            "株式会社",
            "有限会社",
            "合同会社",
            "合名会社",
            "合資会社",
            "一般社団法人",
            "一般財団法人",
            "公益社団法人",
            "公益財団法人",
            "特定非営利活動法人",
            "医療法人",
            "学校法人",
            "宗教法人",
            "社会福祉法人",
            "相互会社",
            "ＮＰＯ法人",
            "（株）",
            "（有）",
            "（同）",
            "（名）",
            "（資）",
            "(株)",
            "(有)",
            "(同)",
            "(名)",
            "(資)",
        ]
        cleaned_name = name
        for t in targets:
            cleaned_name = cleaned_name.replace(t, "")
        return cleaned_name.replace(" ", "").replace("　", "").strip()

    @retry_with_backoff(max_retries=3, backoff_factor=2.0)
    def execute_mizuho_account_freeze(
        self,
        deceased_name: str,
        deceased_address: str,
        branch_name: str,
        account_number: str,
    ) -> dict:
        """
        みずほ銀行の口座凍結（相続届）をSeleniumで実行
        tests/mizuhobank.pyの既存ロジックを移植予定
        """
        logger.info(f"🏦 みずほ銀行 口座凍結開始: {deceased_name}")
        driver = None
        try:
            driver = self._get_driver()
            
            # TODO: tests/mizuhobank.pyのSelenium操作ロジックを移植
            # 1. みずほ銀行の相続手続きページにアクセス
            # 2. 被相続人情報（氏名・住所）を入力
            # 3. 支店名・口座番号を入力
            # 4. 申請完了まで自動操作
            
            logger.warning("⚠️ みずほ銀行のSelenium実装は次ステップで対応します")
            return {
                "status": "pending",
                "message": "Selenium実装は次ステップで対応",
                "bank": "みずほ銀行",
            }
        except Exception as e:
            logger.error(f"❌ みずほ銀行 口座凍結エラー: {e}")
            raise
        finally:
            if driver:
                driver.quit()

    @retry_with_backoff(max_retries=3, backoff_factor=2.0)
    def execute_yucho_inheritance_confirmation(
        self,
        deceased_name: str,
        deceased_address: str,
        account_number: str,
    ) -> dict:
        """
        ゆうちょ銀行の相続確認表をSeleniumで実行
        tests/jp_bank.py（またはnomura.py）の既存ロジックを移植予定
        """
        logger.info(f"🏦 ゆうちょ銀行 相続確認表開始: {deceased_name}")
        driver = None
        try:
            driver = self._get_driver()
            
            # TODO: tests/jp_bank.py or nomura.pyのSelenium操作ロジックを移植
            # 1. ゆうちょ銀行の相続手続きページにアクセス
            # 2. 被相続人情報を入力
            # 3. 口座番号を入力
            # 4. 申請完了まで自動操作
            
            logger.warning("⚠️ ゆうちょ銀行のSelenium実装は次ステップで対応します")
            return {
                "status": "pending",
                "message": "Selenium実装は次ステップで対応",
                "bank": "ゆうちょ銀行",
            }
        except Exception as e:
            logger.error(f"❌ ゆうちょ銀行 相続確認表エラー: {e}")
            raise
        finally:
            if driver:
                driver.quit()
