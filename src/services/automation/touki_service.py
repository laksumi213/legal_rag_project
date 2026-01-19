# src/services/automation/touki_service.py

import os
import re
import time
import logging
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
logger = logging.getLogger(__name__)

# 定数定義
LOGIN_URL = 'https://www.touki.or.jp/TeikyoUketsuke/'

class ToukiService:
    """
    登記情報提供サービスの自動操作を行うサービスクラス (完全版)
    """
    def __init__(self) -> None:
        # 環境変数から認証情報を取得
        self.user_id = os.getenv("TOUKI_USER_ID", "dummy_user") # .envに設定推奨
        self.password = os.getenv("TOUKI_PASSWORD", "dummy_pass")
        self.headless = True # GUIなしで実行するかどうか

    def _get_driver(self):
        """Chrome WebDriverの初期化と設定"""
        options = Options()
        if self.headless:
            options.add_argument("--headless") # ヘッドレスモード
        
        # Docker/サーバー環境向け安定化オプション
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # ユーザーエージェント設定 (Bot判定回避のため)
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        try:
            if ChromeDriverManager:
                service = ChromeService(ChromeDriverManager().install())
            else:
                # webdriver_managerがない場合はパス指定などを検討（今回は必須とする）
                service = ChromeService()
            
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            logger.error(f"WebDriverの起動に失敗しました: {e}")
            raise Exception("ブラウザの起動に失敗しました。Chromeがインストールされているか確認してください。")

    def _to_zenkaku(self, text: str) -> str:
        """半角文字を全角文字に変換する"""
        if not text:
            return ""
        return text.translate(str.maketrans(
            '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ ',
            '０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝～　'
        ))

    def _process_address_efficiently(self, address_string: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """住所文字列を都道府県、市区町村・町域、番地・号に分割・正規化する"""
        if not address_string:
            return None, None, None

        # 1. 都道府県の抽出
        pref_pattern = r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)'
        match = re.match(pref_pattern + r'(.+)', address_string)
        if not match:
            return None, None, None

        prefectures = match.group(1)
        buf = match.group(2).strip()

        # 2. 町域と番地の分割 (丁目または数値で判定)
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
        """市区町村部分を抽出"""
        match = re.match(r'^(.+?[郡市区町村])', address_without_pref)
        if match:
            return match.group(1)
        return address_without_pref

    def _login(self, driver) -> bool:
        """ログイン処理"""
        try:
            driver.get(LOGIN_URL)
            
            # すでにログイン済みかチェック
            if "TeikyoUketsuke" in driver.current_url and "Menu" in driver.title:
                return True

            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "userId")))
            
            # 入力
            driver.find_element(By.ID, 'userId').send_keys(self.user_id)
            driver.find_element(By.ID, 'password').send_keys(self.password)
            
            # ログインボタンクリック
            login_btn = driver.find_element(By.XPATH, "//button[contains(@class, 'CForwardLong')]")
            login_btn.click()

            # 多重ログイン確認 (強制ログイン)
            try:
                force_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), '強制ログイン')]"))
                )
                force_btn.click()
            except TimeoutException:
                pass 

            # メニュー画面待機
            WebDriverWait(driver, 15).until(EC.url_contains("TeikyoUketsuke"))
            return True
            
        except Exception as e:
            logger.error(f"Touki Login Error: {e}")
            return False

    def request_real_estate(self, address: str, target_type: str = '土地') -> str:
        """不動産（土地・建物）の請求を行うメインメソッド"""
        driver = None
        try:
            driver = self._get_driver()
            
            # ログイン
            if not self._login(driver):
                return "ログインに失敗しました。ID/PWを確認してください。"

            # 1. 不動産請求メニューへ
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "不動産請求"))).click()
            
            # 2. 住所解析
            pref, town, blk = self._process_address_efficiently(address)
            if not pref:
                return f"住所の解析に失敗しました: {address}"

            # 3. 種別選択
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "fuShozaiTypeTOCHI")))
            if target_type == '建物':
                driver.find_element(By.ID, "fuShozaiTypeTATEMONO").click()
            else:
                driver.find_element(By.ID, "fuShozaiTypeTOCHI").click()

            # 4. 住所入力 (直接入力モード)
            pref_select = Select(driver.find_element(By.NAME, "todofukenShozai"))
            pref_select.select_by_visible_text(pref)
            
            # 直接入力タブへ切り替え
            driver.find_element(By.NAME, "fuShozaiChokusetuNyuryoku").click()
            
            # フィールド待機
            WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.NAME, "chibanKuiki")))

            # 入力
            driver.find_element(By.NAME, 'chibanKuiki').clear()
            driver.find_element(By.NAME, 'chibanKuiki').send_keys(town)
            
            driver.find_element(By.NAME, 'chibanKaoku').clear()
            driver.find_element(By.NAME, 'chibanKaoku').send_keys(blk)

            # 5. 共同担保目録: 有
            try:
                kyotan = driver.find_element(By.ID, "fuKyodoTanpoYES")
                if kyotan.is_displayed():
                    kyotan.click()
            except:
                pass

            # 6. 確定ボタン (実際にはここでクリックすると課金画面へ進むため、デモモードでは寸止め推奨)
            # confirm_btn = driver.find_element(By.XPATH, "//button[contains(text(), '確定')]")
            # confirm_btn.click()
            
            # スクリーンショットを撮るなどの処理も可能
            # driver.save_screenshot("touki_result.png")

            return f"✅ 「{address}」({target_type}) の検索準備が完了しました。\n(※デモ版のため課金確定ボタンは押していません)"

        except Exception as e:
            logger.error(f"Automation Error: {e}")
            return f"自動操作中にエラーが発生しました: {e}"
        finally:
            if driver:
                driver.quit()

    def request_commercial(self, name: str, address: str) -> str:
        """商業・法人請求を行う"""
        driver = None
        try:
            driver = self._get_driver()
            
            if not self._login(driver):
                return "ログインに失敗しました。"

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "商業・法人"))).click()
            
            pref_pattern = r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)'
            match = re.match(pref_pattern + r'(.+)', address)
            if not match:
                return f"住所解析エラー: {address}"

            pref = match.group(1)
            municipality = self._extract_municipality(match.group(2).strip())
            municipality_zenkaku = self._to_zenkaku(municipality)

            # 都道府県選択
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "shTodofukenShozaiA1")))
            Select(driver.find_element(By.ID, "shTodofukenShozaiA1")).select_by_visible_text(pref)
            
            time.sleep(0.5)
            
            # 直接入力モード
            driver.find_element(By.ID, "shShozaiChokusetuNyuryokuA1").click()
            
            # 入力
            driver.find_element(By.ID, "shChibanKuiki1").send_keys(municipality_zenkaku)
            driver.find_element(By.ID, "shShogoMeisyo").send_keys(name)
            
            # 検索実行
            # driver.find_element(By.XPATH, "//button[contains(@onclick, 'shBtnForward')]").click()

            return f"✅ 法人「{name}」の検索準備が完了しました。\n(※デモ版のため確定ボタンは押していません)"

        except Exception as e:
            return f"エラー: {e}"
        finally:
            if driver:
                driver.quit()

# シングルトンインスタンスを作成
touki_service = ToukiService()