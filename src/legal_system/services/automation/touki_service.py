# src/services/automation/touki_service.py

import logging
import os
import re
import time
from typing import Optional, Tuple

# Selenium 関連
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from legal_system.utils.retry_decorator import retry_with_backoff

# Webdriver Manager (ドライバ自動更新)
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定数定義
LOGIN_URL = "https://www.touki.or.jp/TeikyoUketsuke/"


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

    def _wait_and_send_keys(self, driver, by, value, text, timeout=10):
        """指定した要素が表示されるまで待機してテキストを入力するヘルパー"""
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
        if not text:
            return ""
        return text.translate(
            str.maketrans(
                "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ",
                "０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝～　",
            )
        )

    def _normalize_touki_input(self, text: str) -> str:
        """登記入力用に正規化（ヶ→ケなど）"""
        if not text:
            return ""
        return text.replace("ヶ", "ケ")

    def _remove_corporate_type(self, name: str) -> str:
        """
        商号から法人格（株式会社など）を除去し、スペースも削除する
        例: 株式会社並木管財 -> 並木管財
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

    def _process_address_efficiently(
        self, address_string: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """住所を 都道府県, 市区町村以下(町域), 番地 に分割"""
        if not address_string:
            return None, None, None

        pref_pattern = r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)"
        match = re.match(pref_pattern + r"(.+)", address_string)
        if not match:
            return None, None, None
        prefectures = match.group(1)
        buf = match.group(2).strip()

        match_num = re.search(r"\d", buf)
        if match_num:
            idx = match_num.start()
            town_name_raw = buf[:idx]
            block_raw = buf[idx:]
        else:
            town_name_raw = buf
            block_raw = ""

        town_name = self._to_zenkaku(town_name_raw.strip())
        block = self._to_zenkaku(block_raw.strip())
        return prefectures, town_name, block

    def _extract_municipality(self, address_without_pref: str) -> str:
        """
        都道府県を除いた住所から市区町村（政令市の区まで）を抽出する
        例: 千葉市中央区葛城 -> 千葉市中央区
        """
        if not address_without_pref:
            return ""

        # 特殊な市名（「市」を含む市）の先行判定
        special_cities = ["市川市", "市原市", "四日市市", "廿日市市", "野々市市"]
        for sc in special_cities:
            if address_without_pref.startswith(sc):
                return sc

        # 1. 政令指定都市 (例: 千葉市中央区)
        match = re.match(r"^(.+?市.+?区)", address_without_pref)
        if match:
            return match.group(1)

        # 2. 特別区 (例: 渋谷区)
        match = re.match(r"^(.+?区)", address_without_pref)
        if match:
            return match.group(1)

        # 3. 郡 (例: 印旛郡酒々井町)
        match = re.match(r"^(.+?郡.+?[町村])", address_without_pref)
        if match:
            return match.group(1)

        # 4. 通常の市町村 (例: 船橋市)
        match = re.match(r"^(.+?[市町村])", address_without_pref)
        if match:
            return match.group(1)

        return address_without_pref

    def _login(self, driver) -> bool:
        try:
            driver.get(LOGIN_URL)
            if "TeikyoUketsuke" in driver.current_url and "Menu" in driver.title:
                return True
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "userId"))
            )
            driver.find_element(By.ID, "userId").send_keys(self.user_id)
            driver.find_element(By.ID, "password").send_keys(self.password)
            driver.find_element(
                By.XPATH, "//button[contains(@class, 'CForwardLong')]"
            ).click()
            try:
                force_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[contains(text(), '強制ログイン')]")
                    )
                )
                force_btn.click()
            except TimeoutException:
                pass
            WebDriverWait(driver, 15).until(EC.url_contains("TeikyoUketsuke"))
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"❌ Login Error: {e}")
            return False

    @retry_with_backoff(
        max_retries=2,
        backoff_factor=3.0,
        exceptions=(TimeoutException, WebDriverException),
        log_to_audit=True,
    )
    def request_real_estate(self, address: str, target_type: str = "土地") -> str:
        """不動産請求を実行（リトライ対応版）"""
        address = self._normalize_touki_input(address)
        driver = None
        try:
            driver = self._get_driver()
            if not self._login(driver):
                raise WebDriverException("ログインに失敗しました")

            # メニュー
            self._wait_and_click(driver, By.XPATH, "//a[contains(@href, 'FUDOSAN')]")

            # 住所解析
            pref, town, blk = self._process_address_efficiently(address)
            if not pref:
                raise ValueError(f"住所の解析に失敗しました: {address}")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "fuShozaiTypeTOCHI"))
            )
            if target_type == "建物":
                driver.find_element(By.ID, "fuShozaiTypeTATEMONO").click()
            else:
                driver.find_element(By.ID, "fuShozaiTypeTOCHI").click()

            # 都道府県
            Select(
                driver.find_element(By.NAME, "todofukenShozai")
            ).select_by_visible_text(pref)
            time.sleep(0.5)

            # 直接入力タブ
            driver.find_element(By.NAME, "fuShozaiChokusetuNyuryoku").click()
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, "chibanKuiki"))
            )

            self._wait_and_send_keys(driver, By.NAME, "chibanKuiki", town)
            self._wait_and_send_keys(driver, By.NAME, "chibanKaoku", blk)

            try:
                kyotan = driver.find_element(By.ID, "fuKyodoTanpoYES")
                if kyotan.is_displayed():
                    kyotan.click()
            except:
                pass

            confirm_xpath = (
                "//button[contains(@class, 'CForward')]/span[contains(text(), '確定')]"
            )
            self._wait_and_click(driver, By.XPATH, confirm_xpath)

            time.sleep(3)
            return f"✅ 「{address}」({target_type}) の請求を確定しました。"
        finally:
            if driver:
                driver.quit()

    @retry_with_backoff(
        max_retries=2,
        backoff_factor=3.0,
        exceptions=(TimeoutException, WebDriverException),
        log_to_audit=True,
    )
    def request_commercial(self, name: str, address: str) -> str:
        """
        商業・法人請求を実行（リトライ対応版）
        - 商号：法人格除去、スペース削除
        - 住所：市区町村（区）まで入力
        - 検索実行 -> リスト選択 -> 確定
        """

        # 1. 商号クレンジング
        clean_name = self._remove_corporate_type(name)
        clean_name = self._to_zenkaku(clean_name)

        # 2. 住所処理 (正規化 -> 都道府県分離 -> 市区町村抽出)
        address = self._normalize_touki_input(address)
        pref, town, blk = self._process_address_efficiently(address)

        # 市区町村レベルまでカット (例: 千葉市中央区)
        addr_to_input = self._extract_municipality(town)

        driver = None
        try:
            driver = self._get_driver()
            if not self._login(driver):
                raise WebDriverException("ログインに失敗しました")

            # メニュー遷移
            try:
                self._wait_and_click(
                    driver, By.XPATH, "//a[contains(@href, 'SHOGYO_HOJIN_TOKIBO')]"
                )
            except TimeoutException:
                self._wait_and_click(driver, By.PARTIAL_LINK_TEXT, "商業・法人請求")

            time.sleep(1.5)

            # 商号・名称検索モード選択
            try:
                self._wait_and_click(driver, By.ID, "shSeikyuMethodSHOGO_KANJI")
                time.sleep(0.5)
            except:
                pass

            # 商号入力
            try:
                self._wait_and_send_keys(driver, By.ID, "shShogoMeisyo", clean_name)
            except TimeoutException:
                self._wait_and_send_keys(driver, By.NAME, "shogo", clean_name)

            # 住所入力
            if pref:
                # 都道府県選択 (JS強制)
                try:
                    pref_elem = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "shTodofukenShozaiA1"))
                    )
                    driver.execute_script(
                        """
                        var select = arguments[0];
                        var targetText = arguments[1];
                        for(var i=0; i<select.options.length; i++){
                            if(select.options[i].text === targetText){
                                select.selectedIndex = i;
                                select.dispatchEvent(new Event('change'));
                                break;
                            }
                        }
                    """,
                        pref_elem,
                        pref,
                    )
                    time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"都道府県選択失敗: {e}")

                # 直接入力チェック (JS強制)
                try:
                    direct_chk = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.ID, "shShozaiChokusetuNyuryokuA1")
                        )
                    )
                    if not direct_chk.is_selected():
                        driver.execute_script("arguments[0].click();", direct_chk)
                    time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"直接入力チェック失敗: {e}")

                # 市区町村入力 (有効化待ち)
                try:
                    input_field = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "shChibanKuiki1"))
                    )
                    input_field.clear()
                    input_field.send_keys(addr_to_input)
                    logger.info(f"Sent keys to shChibanKuiki1: {addr_to_input}")
                except Exception as e:
                    logger.warning(f"市区町村入力失敗: {e}")

            # 検索ボタンクリック
            try:
                search_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(., '検索')]")
                    )
                )
                search_btn.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"検索ボタンクリック失敗: {e}")

            # --- 検索結果リストでの選択処理 ---
            try:
                # 候補リストのラジオボタンを探す（IDなどで特定せず、テーブル内のラジオボタンを狙う）
                # 検索結果が表示されるまで少し待つ
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//table//input[@type='radio']")
                    )
                )

                # 最初のラジオボタンを選択
                # ※検索条件設定のラジオボタンを除外するため、結果テーブル（と思われる場所）を特定するか、
                # 単純に name="sentaku" 等の属性を持つものを探すのが一般的
                radios = driver.find_elements(
                    By.XPATH,
                    "//input[@type='radio' and not(@name='kensaku') and not(@name='matchingTypeShogo')]",
                )

                if radios:
                    # 見えている最初のラジオボタンをクリック
                    for r in radios:
                        if r.is_displayed() and r.is_enabled():
                            r.click()
                            logger.info("検索結果リストの1件目を選択しました。")
                            time.sleep(0.5)
                            break
            except TimeoutException:
                # リストが出ずに直接確定画面に行く場合もあるので、ここはエラーにしない
                pass
            except Exception as e:
                logger.warning(f"リスト選択処理で警告: {e}")

            # 最終確定ボタン (次へ/確定)
            confirm_xpath = (
                "//button[contains(@class, 'CForward')]/span[contains(text(), '確定')]"
            )
            try:
                self._wait_and_click(driver, By.XPATH, confirm_xpath, timeout=5)
                logger.info("確定ボタンをクリックしました。")
            except TimeoutException:
                return "⚠️ 検索は実行しましたが、確定ボタンが見つかりませんでした（候補選択が必要な可能性があります）。"

            time.sleep(3)
            return f"✅ 法人「{clean_name}」の所在地（{pref}{addr_to_input}）にて請求を確定しました。"

        finally:
            if driver:
                driver.quit()


touki_service = ToukiService()
