# src/services/automation/touki_service.py

import os
import re
import time
import logging
import platform
from typing import Optional, Tuple

# Selenium 関連
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Webdriver Manager (ドライバ自動更新)
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定数定義
LOGIN_URL = 'https://www.touki.or.jp/TeikyoUketsuke/'

class ToukiService:
    """
    登記情報提供サービスの自動操作を行うサービスクラス (完全運用版)
    """
    def __init__(self) -> None:
        self.user_id = os.getenv("TOUKI_USER_ID", "dummy_user") 
        self.password = os.getenv("TOUKI_PASSWORD", "dummy_pass")
        
        # 環境判定: Docker内かどうか
        self.is_docker = os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER")
        
        # Dockerならヘッドレス必須、ローカルならGUI強制
        self.headless = True if self.is_docker else False
        
        logger.info(f"🚀 ToukiService Initialized. Headless: {self.headless}")

    def _get_driver(self):
        """Chrome WebDriverの初期化と設定"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
        else:
            # GUI表示を強制
            options.add_experimental_option("detach", True)
            options.add_argument("--window-position=0,0")
            options.add_argument("--window-size=1280,800")

        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

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
        """指定した要素が表示されクリック可能になるまで待機してクリックするヘルパー"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            logger.info(f"Clicked element: {value}")
        except Exception as e:
            logger.error(f"Click failed for {value}: {e}")
            raise

    def _to_zenkaku(self, text: str) -> str:
        if not text: return ""
        return text.translate(str.maketrans(
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ',
            '０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝～　'
        ))

    def _process_address_efficiently(self, address_string: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        if not address_string: return None, None, None
        pref_pattern = r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)'
        match = re.match(pref_pattern + r'(.+)', address_string)
        if not match: return None, None, None
        prefectures = match.group(1)
        buf = match.group(2).strip()
        buf_match = re.match(r'(.*丁目)(.*)', buf)
        if buf_match:
            town_name_raw = buf_match.group(1)
            block_raw = buf_match.group(2)
        else:
            split_match = re.search(r'\d', buf)
            if split_match:
                idx = split_match.start()
                town_name_raw = buf[:idx]
                block_raw = buf[idx:]
            else:
                town_name_raw = buf
                block_raw = ''
        town_name = self._to_zenkaku(town_name_raw.strip())
        block = self._to_zenkaku(block_raw.strip())
        return prefectures, town_name, block

    def _extract_municipality(self, address_without_pref: str) -> str:
        match = re.match(r'^(.+?[郡市区町村])', address_without_pref)
        if match: return match.group(1)
        return address_without_pref

    def _login(self, driver) -> bool:
        try:
            driver.get(LOGIN_URL)
            if "TeikyoUketsuke" in driver.current_url and "Menu" in driver.title:
                return True
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "userId")))
            driver.find_element(By.ID, 'userId').send_keys(self.user_id)
            driver.find_element(By.ID, 'password').send_keys(self.password)
            driver.find_element(By.XPATH, "//button[contains(@class, 'CForwardLong')]").click()
            try:
                force_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '強制ログイン')]")))
                force_btn.click()
            except TimeoutException: pass 
            WebDriverWait(driver, 15).until(EC.url_contains("TeikyoUketsuke"))
            time.sleep(1) 
            return True
        except Exception as e:
            logger.error(f"❌ Login Error: {e}")
            return False

    def request_real_estate(self, address: str, target_type: str = '土地') -> str:
        """不動産請求を実行し、確定ボタンをクリックする"""
        driver = None
        try:
            driver = self._get_driver()
            if not self._login(driver):
                return "❌ ログインに失敗しました。"

            # 不動産請求メニューへ遷移
            self._wait_and_click(driver, By.PARTIAL_LINK_TEXT, "不動産請求")
            
            # 住所解析
            pref, town, blk = self._process_address_efficiently(address)
            if not pref: return f"❌ 住所の解析に失敗しました: {address}"

            # 種別選択
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fuShozaiTypeTOCHI")))
            if target_type == '建物':
                driver.find_element(By.ID, "fuShozaiTypeTATEMONO").click()
            else:
                driver.find_element(By.ID, "fuShozaiTypeTOCHI").click()

            # 都道府県選択
            Select(driver.find_element(By.NAME, "todofukenShozai")).select_by_visible_text(pref)
            time.sleep(0.5)
            
            # 直接入力タブへ切り替え
            driver.find_element(By.NAME, "fuShozaiChokusetuNyuryoku").click()
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.NAME, "chibanKuiki")))
            
            # 市区町村・町域の入力 (入力漏れ対策として明示的にsend_keys)
            kuiki_input = driver.find_element(By.NAME, 'chibanKuiki')
            kuiki_input.clear()
            kuiki_input.send_keys(town) # ここで「市区町村」も含んだ文字列を入力
            
            # 地番・家屋番号の入力
            kaoku_input = driver.find_element(By.NAME, 'chibanKaoku')
            kaoku_input.clear()
            kaoku_input.send_keys(blk)

            # 共同担保目録のチェック
            try:
                kyotan = driver.find_element(By.ID, "fuKyodoTanpoYES")
                if kyotan.is_displayed(): kyotan.click()
            except: pass

            # ★修正点: 確定ボタンのクリック処理 (XPath変更 & wait_and_click使用)
            # 理由: ボタン要素自体にはテキストがなく、子要素のspanにテキストが含まれているため、
            # contains(text(), '確定') をspanに対して行う必要があります。
            confirm_xpath = "//button[contains(@class, 'CForward')]/span[contains(text(), '確定')]"
            self._wait_and_click(driver, By.XPATH, confirm_xpath)
            
            logger.info("✅ 確定ボタンをクリックしました。")

            time.sleep(3)
            return f"✅ 「{address}」({target_type}) の請求を確定しました。"

        except Exception as e:
            logger.error(f"❌ Automation Error: {e}")
            return f"エラーが発生しました: {e}"

    def request_commercial(self, name: str, address: str) -> str:
        """商業・法人請求を実行し、確定ボタンをクリックする"""
        driver = None
        try:
            # 1. メニュー遷移
            self._wait_and_click(By.PARTIAL_LINK_TEXT, "不動産請求")
            
            # 2. 住所解析
            pref, town, blk = self._process_address_efficiently(address)
            if not pref:
                raise ValueError(f"住所の解析に失敗しました: {address}")

            # 3. 入力画面表示待機
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fuShozaiTypeTOCHI")))
            
            if target_type == '建物':
                self._wait_and_click(By.ID, "fuShozaiTypeTATEMONO")
            else:
                self._wait_and_click(By.ID, "fuShozaiTypeTOCHI")

            # 4. 住所入力
            pref_select = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.NAME, "todofukenShozai")))
            Select(pref_select).select_by_visible_text(pref)
            
            self._wait_and_click(By.NAME, "fuShozaiChokusetuNyuryoku")
            
            # 直接入力フィールドが表示されるのを待機
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.NAME, "chibanKuiki")))

            self._wait_and_send_keys(By.NAME, 'chibanKuiki', town)
            self._wait_and_send_keys(By.NAME, 'chibanKaoku', blk)

            # 5. 共同担保目録: 有
            try:
                self._wait_and_click(By.ID, "fuKyodoTanpoYES", timeout=2)
            except:
                pass

            # 6. 確定
            confirm_xpath = "//button[contains(@class, 'CForward')]/span[contains(text(), '確定')]"
            self._wait_and_click(By.XPATH, confirm_xpath)
            
            # logger.info("✅ 法人請求の確定ボタンをクリックしました。")

            time.sleep(3)
            return f"✅ 法人「{name}」の請求直前まで画面を作成しました。"

        except Exception as e:
            logger.error(f"❌ Automation Error: {e}")
            return f"エラー: {e}"

touki_service = ToukiService()