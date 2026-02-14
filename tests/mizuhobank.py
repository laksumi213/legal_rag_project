### みずほ銀行
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from web_operation import Web
# from convert_to_wareki import convert_to_wareki2
from zengin import BankSearch
# from gincode import Gincode
from datetime import datetime
import jaconv
import mojimoji
import re
import os.path
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
# from selenium.webdriver.support.ui import Select
# import signal


class Mizuhobank(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.bw = None
        self.service = None
        self.options = None
        self.t_receiving = None
        self.dd_receiving1 = None
        self.dd_receiving2 = None
        self.dd_receiving3 = None
        self.foreign_nationality = None
        self.dd_foreign_nationality1 = None
        self.dd_foreign_nationality2 = None
        self.rg_t_foreign_nationality = None
        self.t_foreign_nationality = None
        self.rg_north_korea = None
        self.t_north_korea = None
        self.customer = None
        self.page = GlobalValues.my_page
        self.proc = Web()

    def build(self):
        pass

    def close_dlg(self, _):
        self.page.dialog.open = False
        self.page.update()

    def rg_t_foreign_nationality_change(self, _):
        if not self.dd_foreign_nationality1.visible:
            self.dd_foreign_nationality1.visible = True
            self.dd_foreign_nationality2.visible = True
            self.dd_foreign_nationality1.focus()
        else:
            self.dd_foreign_nationality1.visible = False
            self.dd_foreign_nationality2.visible = False

        self.dd_foreign_nationality1.update()
        self.dd_foreign_nationality2.update()

    ### 口座凍結
    def account_freezing(self):
        # 携帯電話番号の入力と画像認証
        self.page = GlobalValues.my_page
        self.proc.web_open('https://inherit.m041.mizuhobank.co.jp/apply/applyConsent.php')
        self.bw = self.proc.driver
        # self.options = webdriver.ChromeOptions()
        # self.service = ChromeService(executable_path=os.path.join(os.path.dirname(__file__), "chromedriver.exe"))
        # self.options.add_argument('--disable-gpu')  # GPUハードウェアアクセラレーションを無効
        # self.options.add_argument('--ignore-certificate-errors')  # SSL認証(この接続ではプライバシーが保護されません)を無効
        # self.options.add_argument('--disable-logging')
        # self.options.add_argument('--log-level=3')
        # self.options.add_experimental_option("excludeSwitches", ['enable-automation', 'enable-logging'])
        # # self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        # self.bw = webdriver.Chrome(service=self.service, options=self.options)
        # self.bw.maximize_window()
        # self.bw.implicitly_wait(3)
        # self.bw.get('https://inherit.m041.mizuhobank.co.jp/apply/applyConsent.php')
        # sleep(3)
        self.bw.find_element(By.NAME, 'agree').click()
        self.bw.find_element(By.ID, 'telNum1').send_keys('080')
        self.bw.find_element(By.ID, 'telNum2').send_keys('8897')
        self.bw.find_element(By.ID, 'telNum3').send_keys('4708')

        self.t_discussed_document = ft.Text('遺産分割協議書')
        self.rg_discussed_document = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.t_will = ft.Text('遺言書')
        self.rg_will = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('みずほ銀行の口座凍結手続き'),
            content=ft.Column(
                [
                    self.t_discussed_document,
                    self.rg_discussed_document,
                    ft.VerticalDivider(),
                    self.t_will,
                    self.rg_will,
                ],
                height=150,
            ),
            actions=[ft.ElevatedButton("OK", on_click=self.account_freezing_create1, autofocus=True),
                     ft.ElevatedButton("キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def account_freezing_create1(self, _):
        self.close_dlg(self)
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('口座凍結手続き'),
            content=ft.Column(
                [
                    ft.Text('「相続発生情報入力画面を表示後」にOKボタンをクリックしてください。'),
                ],
                height=30,
            ),
            actions=[ft.ElevatedButton("OK", on_click=self.account_freezing_create2, autofocus=True)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def account_freezing_create2(self, _):
        self.close_dlg(self)
        self.bw.minimize_window()
        self.bw.maximize_window()
        sql = ('''
            SELECT
                 folder_s_path AS フォルダパス,
                 zipcode AS 被相続人_郵便番号,
                 prefectures AS 被相続人_都道府県,
                 municipalities AS 被相続人_市区町村,
                 townarea || house_number || building AS 被相続人_住所,
                 username1_hurigana AS 被相続人_かな1,
                 username2_hurigana AS 被相続人_かな2,
                 username1 AS 被相続人1,
                 username2 AS 被相続人2,
                 birthday AS 生年月日,
                 deathday AS 死亡日,
                 (SELECT zipcode FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_郵便番号,
                 (SELECT prefectures FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_都道府県,
                 (SELECT municipalities FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_町域名,
                 (SELECT townarea || house_number || building FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_住所,
                 (SELECT username1_hurigana FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_ふりがな1,
                 (SELECT username2_hurigana FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_ふりがな2,
                 (SELECT username1 FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_氏名1,
                 (SELECT username2 FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 依頼者_氏名2,
                 (SELECT contact_phone FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 連絡先_携帯,
                 (SELECT contact_home FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 連絡先_自宅,
                 (SELECT relationship FROM heir WHERE customer.code = heir.code AND heir.offer = 1) AS 続柄,
                 maiden_name AS 旧姓,
                 maiden_name_huri AS 旧姓_ふりがな
            FROM customer 
            WHERE code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        sql = ('''
            SELECT
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0001"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
            WHERE t1.code = ?
        ''')
        self.customer_bank = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        sql = ('''
            SELECT relationship
            FROM heir
            WHERE code = ?
        ''')
        self.heirs = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        self.bw.find_element(By.ID, 'hisozokujinSeikana').send_keys(jaconv.hira2kata(self.customer['被相続人_かな1']))
        self.bw.find_element(By.ID, 'hisozokujinmeikana').send_keys(jaconv.hira2kata(self.customer['被相続人_かな2']))
        self.bw.find_element(By.ID, 'hisozokujinSeikaji').send_keys(self.customer['被相続人1'])
        self.bw.find_element(By.ID, 'hisozokujinmeikaji').send_keys(self.customer['被相続人2'])
        self.bw.find_element(By.ID, 'zipCode1').send_keys(self.customer['被相続人_郵便番号'][0:3])
        self.bw.find_element(By.ID, 'zipCode2').send_keys(self.customer['被相続人_郵便番号'][4:])
        self.bw.find_element(By.ID, 'searchaddr').click()
        sleep(.5)
        self.bw.find_element(By.ID, 'address2').send_keys(jaconv.h2z(self.customer['被相続人_住所'].replace('-', '－'), digit=True))
        self.bw.find_element(By.XPATH, '//*[@id="birthday_swRadioset"]/label[1]').click()
        sleep(.5)
        self.bw.find_element(By.ID, 'adLivingDate_y').send_keys(re.findall(r'\d+', self.customer['生年月日'])[0])
        self.bw.find_element(By.ID, 'adLivingDate_m').send_keys(re.findall(r'\d+', self.customer['生年月日'])[1])
        self.bw.find_element(By.ID, 'adLivingDate_d').send_keys(re.findall(r'\d+', self.customer['生年月日'])[2])
        self.bw.find_element(By.XPATH, '//*[@id="deathday_swRadioset"]/label[1]').click()
        sleep(.5)
        self.bw.find_element(By.ID, 'adDeathDate_y').send_keys(re.findall(r'\d+', self.customer['死亡日'])[0])
        self.bw.find_element(By.ID, 'adDeathDate_m').send_keys(re.findall(r'\d+', self.customer['死亡日'])[1])
        self.bw.find_element(By.ID, 'adDeathDate_d').send_keys(re.findall(r'\d+', self.customer['死亡日'])[2])
        self.bw.find_element(By.ID, 'tenbanNo').send_keys(str(self.customer_bank['店番号']).zfill(3))
        self.bw.find_element(By.XPATH, '//*[@id="kamoku-button"]/span[2]').click()
        sleep(.5)
        if '普通' in self.customer_bank['種類']:
            self.bw.find_element(By.ID, 'ui-id-20').click()
        elif '定期' in self.customer_bank['種類']:
            self.bw.find_element(By.ID, 'ui-id-23').click()
        elif '当座' in self.customer_bank['種類']:
            self.bw.find_element(By.ID, 'ui-id-21').click()
        elif '貯蓄' in self.customer_bank['種類']:
            self.bw.find_element(By.ID, 'ui-id-22').click()
        sleep(.5)
        self.bw.find_element(By.ID, 'acntNumIn').send_keys(self.customer_bank['口座番号'])
        self.bw.find_element(By.ID, 'offerLastkana').send_keys('ソウゾクテツヅキシエンセンターマチダ')
        self.bw.find_element(By.ID, 'offerFirstkana').send_keys('モリマチ　ツバサ')
        self.bw.find_element(By.ID, 'offerLastkanji').send_keys('相続手続支援センター町田')
        self.bw.find_element(By.ID, 'offerFirstkanji').send_keys('森町　翼')
        self.bw.find_element(By.XPATH, '//*[@id="decedentRelationship-button"]/span[2]').click()
        self.bw.find_element(By.ID, 'ui-id-26').click()
        self.bw.find_element(By.ID, 'heirsOther').send_keys('代理人')
        self.bw.find_element(By.ID, 'offerorZipCode1').send_keys('194')
        self.bw.find_element(By.ID, 'offerorZipCode2').send_keys('0022')
        self.bw.find_element(By.ID, 'offerorSearchaddr').click()
        sleep(.5)
        self.bw.find_element(By.ID, 'offerorAddress2').send_keys(jaconv.h2z('一丁目22番5号　町田310五十子ビル3Ｆ', digit=True))
        self.bw.find_element(By.ID, 'homePhoneNumber1').send_keys('042')
        self.bw.find_element(By.ID, 'homePhoneNumber2').send_keys('710')
        self.bw.find_element(By.ID, 'homePhoneNumber3').send_keys('6178')
        self.bw.find_element(By.ID, 'representLastkana').send_keys(jaconv.hira2kata(self.customer['依頼者_ふりがな1']))
        self.bw.find_element(By.ID, 'representFirstkana').send_keys(jaconv.hira2kata(self.customer['依頼者_ふりがな2']))
        self.bw.find_element(By.ID, 'representLastkanji').send_keys(self.customer['依頼者_氏名1'])
        self.bw.find_element(By.ID, 'representFirstkanji').send_keys(self.customer['依頼者_氏名2'])
        self.bw.find_element(By.XPATH, '//*[@id="representativeRelationship-button"]').click()
        if self.customer['続柄'] == '夫':
            self.bw.find_element(By.XPATH, '//*[@id="ui-id-33"]').click()
        elif self.customer['続柄'] == '妻':
            self.bw.find_element(By.XPATH, '//*[@id="ui-id-34"]').click()
        elif '男' in self.customer['続柄'] or '女' in self.customer['続柄']:
            self.bw.find_element(By.XPATH, '//*[@id="ui-id-35"]').click()
        else:
            self.bw.find_element(By.XPATH, '//*[@id="ui-id-36"]').click()
            self.bw.find_element(By.ID, 'representativeRelationshipOther').send_keys(self.customer['続柄'])

        if self.customer['被相続人_住所'] == self.customer['依頼者_住所']:
            self.bw.find_element(By.XPATH, '//*[@id="sameAsDecedentArea"]/div[1]/label').click()
        else:
            self.bw.find_element(By.ID, 'representativeZipCode1').send_keys(self.customer['依頼者_郵便番号'][0:3])
            self.bw.find_element(By.ID, 'representativeZipCode2').send_keys(self.customer['依頼者_郵便番号'][4:])
            self.bw.find_element(By.ID, 'representativeSearchaddr').click()
            sleep(.5)
            self.bw.find_element(By.ID, 'representativeAddress2').send_keys(jaconv.h2z(self.customer['依頼者_住所'].replace('-', '－'), digit=True))

        if not self.customer['連絡先_携帯'] == "":
            self.bw.find_element(By.ID, 'representativePhoneNumber1').send_keys(
                re.findall(r'\d+', self.customer['連絡先_携帯'])[0])
            self.bw.find_element(By.ID, 'representativePhoneNumber2').send_keys(
                re.findall(r'\d+', self.customer['連絡先_携帯'])[1])
            self.bw.find_element(By.ID, 'representativePhoneNumber3').send_keys(
                re.findall(r'\d+', self.customer['連絡先_携帯'])[2])
        if not self.customer['連絡先_自宅'] == "":
            self.bw.find_element(By.ID, 'repHomePhoneNumber1').send_keys(
                re.findall(r'\d+', self.customer['連絡先_自宅'])[0])
            self.bw.find_element(By.ID, 'repHomePhoneNumber2').send_keys(
                re.findall(r'\d+', self.customer['連絡先_自宅'])[1])
            self.bw.find_element(By.ID, 'repHomePhoneNumber3').send_keys(
                re.findall(r'\d+', self.customer['連絡先_自宅'])[2])

        spouse = 0
        children = 0
        parents = 0
        grandparent = 0 # 利用していない
        brother_sister = 0
        for heir in self.heirs:
            if heir[0] == '妻' or heir[0] == '夫':
                self.bw.find_element(By.XPATH, '//*[@id="haigushaChoshuRadioset"]/label[1]').click()
                spouse += 1
            elif '男' in heir[0] or '女' in heir[0]:
                self.bw.find_element(By.XPATH, '//*[@id="childrenChoshuRadioset"]/label[1]/span[1]').click()
                children += 1
            elif heir[0] == '父' or heir[0] == '夫':
                self.bw.find_element(By.XPATH, '//*[@id="grandparentsChoshuRadioset"]/label[1]').click()
                parents += 1
            elif '兄弟' in heir[0] or '姉妹' in heir[0]:
                self.bw.find_element(By.XPATH, '//*[@id="brotherAndSisterChoshuRadioset"]/label[1]/span[1]').click()
                brother_sister += 1

        # 両親：
        if spouse == 0:
            self.bw.find_element(By.XPATH, '//*[@id="haigushaChoshuRadioset"]/label[2]').click()

        # 祖父母：
        if children == 0:
            self.bw.find_element(By.XPATH, '//*[@id="childrenChoshuRadioset"]/label[2]').click()
        else:
            self.bw.find_element(By.ID, 'childrensChoshu').send_keys(children)

        # 兄弟姉妹：
        if parents == 0:
            self.bw.find_element(By.XPATH, '//*[@id="parentsChoshuRadioset"]/label[2]').click()
        if grandparent == 0:
            self.bw.find_element(By.XPATH, '//*[@id="grandparentsChoshuRadioset"]/label[2]/span[1]').click()
        if brother_sister == 0:
            self.bw.find_element(By.XPATH, '//*[@id="brotherAndSisterChoshuRadioset"]/label[2]').click()

        # 遺言書：
        if self.t_will.value == '有':
            self.bw.find_element(By.XPATH, '//*[@id="testamentChoshuRadioset"]/label[1]').click()
        else:
            self.bw.find_element(By.XPATH, '//*[@id="testamentChoshuRadioset"]/label[2]').click()

        # 遺産分割協議書：
        if self.rg_discussed_document.value == '有':
            self.bw.find_element(By.XPATH, '//*[@id="heritageChoshuRadioset"]/label[1]').click()
        else:
            self.bw.find_element(By.XPATH, '//*[@id="heritageChoshuRadioset"]/label[2]').click()

        # 相続人さま間の意見の相違：
        self.bw.find_element(By.XPATH, '//*[@id="troubleChoshuRadioset"]/label[2]').click()

        # 相続人さまへの連絡：
        self.bw.find_element(By.XPATH, '//*[@id="contactChoshuRadioset"]/label[1]').click()

        # ⑥郵便物送付先情報について
        self.bw.find_element(By.XPATH, '//*[@id="mailingAddress-button"]/span[2]').click()
        sleep(.5)
        self.bw.find_element(By.ID, 'ui-id-38').click()


    # 残高証明書
    def balance_certificate(self):
        self.dt_now = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'), autofocus=True)

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('みずほ銀行の手続き'),
            content=ft.Column(
                [
                    self.dt_now,
                ],
                height=100,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True, on_click=self.balance_certificate_create),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def balance_certificate_create(self, _):
        self.close_dlg(self)
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', convert_to_wareki2(self.dt_now))
        pdf = PdfCreate("A4")
        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0001"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        sql = ('''
            SELECT  username1 || " " || username2 AS 氏名,
                    username1_hurigana || " " || username2_hurigana AS 氏名ふりがな,
                    relationship AS 続柄,
                    zipcode AS 郵便番号,
                    prefectures || municipalities || townarea || house_number || building AS 住所,
                    contact_phone AS 携帯,
                    contact_home AS 自宅,
                    birthday AS 生年月日
            FROM    heir
            WHERE   code = ?
            AND     situation = ""
            AND     offer = 1
        ''')
        self.heir = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print('heir:', GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        # 日付
        # pdf.draw_string(163, 278, self.dt_now.value[2:4])
        # pdf.draw_string(177, 278, self.dt_now.value[5:7])
        # pdf.draw_string(188, 278, self.dt_now.value[8:])

        # pdf.draw_string(101, 264, self.customer[0][2])
        pdf.draw_string(148, 277, self.customer[0][2])

        # pdf.draw_string(121, 252, '〇', 14)
        pdf.draw_string(87, 267, '✓', 14)

        pdf.draw_string(112, 267, '相続人代理人')
        # pdf.draw_string(134, 252, '代理人')

        pdf.draw_string(111, 260, '194', 10)
        # pdf.draw_string(108, 247, '194', 8)
        pdf.draw_string(127, 260, '0022', 10)
        # pdf.draw_string(127, 247, '0022', 8)
        pdf.draw_string(107, 255, '東京都町田市森野一丁目22番5号', 10)
        # pdf.draw_string(104, 242, '東京都町田市森野一丁目22番5号', 8)
        # pdf.draw_string(104, 238, '町田310五十子ビル3F', 8)
        pdf.draw_string(107, 246, f'相続人　{self.heir["氏名"]}', 8)
        # pdf.draw_string(104, 230, f'相続人　{self.heir["氏名"]}', 8)
        pdf.draw_string(107, 242, '相続手続支援センター町田有限責任事業組合　組合員', 8)
        # pdf.draw_string(104, 227, '相続手続支援センター町田有限責任事業組合　組合員', 8)
        pdf.draw_string(107, 238, '株式会社プロフィット・ワン　職務執行者　大貫利一', 8)
        # pdf.draw_string(104, 224, '株式会社プロフィット・ワン　職務執行者　大貫利一', 8)
        pdf.draw_string(116, 234, '042', 8)
        # pdf.draw_string(114, 215, '042', 8)
        pdf.draw_string(131, 234, '710', 8)
        # pdf.draw_string(130, 215, '710', 8)
        pdf.draw_string(148, 234, '6178', 8)
        # pdf.draw_string(150, 215, '6178', 8)

        pdf.draw_string(18, 211, '✓', 12)
        # pdf.draw_string(27, 195, '✓', 8)

        pdf.draw_string(63, 211, '1', 12)
        # pdf.draw_string(74, 194, '1')

        # pdf.draw_string(85, 208, self.customer['支店名'], 8)

        deathday = re.findall('[0-9]+', self.customer[0]['死亡日'])
        pdf.draw_string(32, 154.5, deathday[0])
        # pdf.draw_string(79, 123.5, deathday[0])
        pdf.draw_string(55, 154.5, deathday[1])
        # pdf.draw_string(104, 123.5, deathday[1])
        pdf.draw_string(72, 154.5, deathday[2])
        # pdf.draw_string(123, 123.5, deathday[2])

        # 支店名
        buf = ''
        for i, customer in enumerate(self.customer):
            if buf != customer['支店名']:
                pdf.draw_string(85 + i * 37, 209.5, customer['支店名'])
            buf = customer['支店名']

        # 現金払い
        pdf.draw_string(89, 115, '✓', 12)
        # pdf.draw_string(101.5, 115.5, '✓')

        os.makedirs(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書'), exist_ok=True)
        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書', 'みずほ銀行_残高証明書'),
                     os.path.dirname(__file__) + r"/pdf/みずほ銀行_残高証明書.pdf", page=1, open_bool=True)

        # pdf.pdf_marge(
        #     os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書'),
        #     os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書1'),
        #     os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書2')
        # )

    ### 相続届
    def inheritance_notification(self):
        self.t_north_korea = ft.Text('相続人に北朝鮮の在住者の有無')
        self.rg_north_korea = ft.RadioGroup(
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
            value='無',
        )

        sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND situation = ""'
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))

        self.t_foreign_nationality = ft.Text('非居住者または外国籍の有無')
        self.rg_t_foreign_nationality = ft.RadioGroup(
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
            value='無',
            on_change=self.rg_t_foreign_nationality_change,
        )
        self.dd_foreign_nationality1 = ft.Dropdown(label='氏名選択', visible=False)
        self.dd_foreign_nationality2 = ft.Dropdown(label='氏名選択', visible=False)
        [self.dd_foreign_nationality1.options.append(ft.dropdown.Option(record[0])) for record in records]
        [self.dd_foreign_nationality2.options.append(ft.dropdown.Option(record[0])) for record in records]

        # self.t_receiving = ft.Text('受取者')
        # self.dd_receiving1 = ft.Dropdown(label='1人目の受取者選択')
        # self.dd_receiving2 = ft.Dropdown(label='2人目の受取者選択')
        # self.dd_receiving3 = ft.Dropdown(label='3人目の受取者選択')
        # [self.dd_receiving1.options.append(ft.dropdown.Option(record[0])) for record in records]
        # [self.dd_receiving2.options.append(ft.dropdown.Option(record[0])) for record in records]
        # [self.dd_receiving3.options.append(ft.dropdown.Option(record[0])) for record in records]
        # sql = ('''
        #     SELECT
        #         username1 || " " || username2,
        #         heir_bank.jba_code,
        #         heir_bank.branch_code,
        #         heir_bank.bank_number,
        #         heir_bank.subjects
        #     FROM heir
        #         INNER JOIN heir_bank
        #         ON heir.heir_id = heir_bank.heir_id
        #         AND heir_bank.jba_code = "0001"
        #     WHERE code = ?
        # ''')
        # # sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND '
        # records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        # for i, record in enumerate(records):
        #     pass

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('みずほ銀行の手続き'),
            content=ft.Column(
                [
                    self.t_north_korea,
                    self.rg_north_korea,
                    ft.VerticalDivider(),
                    self.t_foreign_nationality,
                    self.rg_t_foreign_nationality,
                    self.dd_foreign_nationality1,
                    self.dd_foreign_nationality2,
                    # ft.VerticalDivider(),
                    # self.t_receiving,
                    # self.dd_receiving1,
                    # self.dd_receiving2,
                    # self.dd_receiving3,
                ],
                height=280,
                # height=500,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True, on_click=self.inheritance_notification_create),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def inheritance_notification_create(self, _):
        self.close_dlg(self)
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', dt_now)
        pdf = PdfCreate("A3", 'landscape')
        sql = (f'''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名,
                (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
                t4.username1 || "  " || t4.username2 AS 相続人,
                t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0001"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "0001"
                        INNER JOIN heir AS t4
                        ON t4.code = t1.code
                        AND t4.code = "{GlobalValues.code}"
                        AND t4.offer = 1
            WHERE t1.code = "{GlobalValues.code}"
        ''')
        self.customer = GlobalValues.get_db(sql, row_factory=True)[0]
        print(GlobalValues.get_db(sql[0]))

        # お届け日
        # pdf.draw_string(119, 175, f'{str(dt[0])[2:4]}', 7)
        # pdf.draw_string(126.5, 175, f'{str(dt[1])}', 7)
        # pdf.draw_string(133.5, 175, f'{str(dt[2])}', 7)

        # フリガナ
        pdf.draw_string(45, 169, jaconv.hira2kata(self.customer["被相続人_かな"]))

        # 氏名
        pdf.draw_string(45, 159, self.customer["被相続人"])

        # 相続手続依頼人の代表者
        pdf.draw_string(169, 186, '✓')
        pdf.draw_string(170, 180,
                        f'{mojimoji.zen_to_han(jaconv.hira2kata(self.customer["相続人かな"]))} ﾎｶ{int(self.customer["相続人数"])-1}ﾆﾝ ﾀﾞｲﾘﾆﾝ', 5)
        pdf.draw_string(170, 178, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲｸﾐｱｲｲﾝ', 4.5)
        pdf.draw_string(170, 176, 'ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄ・ﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 4.5)

        pdf.draw_string(170, 168, f'{self.customer["相続人"]}　他{int(self.customer["相続人数"])-1}人　代理人', 6)
        pdf.draw_string(170, 165, '相続手続支援センター町田有限責任事業組合', 5)
        pdf.draw_string(170, 162, '組合員　株式会社プロフィット・ワン', 5.5)
        pdf.draw_string(170, 159, '職務執行者　大貫　利一', 6)

        pdf.draw_string(212, 187, '194', 8)
        pdf.draw_string(226, 187, '0022', 8)

        pdf.draw_string(214, 177, '東京')
        pdf.draw_string(226.2, 178.5, '〇')
        pdf.draw_string(237, 177, '町田市')
        pdf.draw_string(214, 170, '森野一丁目22番5号')

        pdf.draw_string(230, 156, '042', 8)
        pdf.draw_string(243, 156, '710', 8)
        pdf.draw_string(257, 156, '6178', 8)

        pdf.draw_string(242, 49, '✓') if self.rg_north_korea == '有' else pdf.draw_string(263, 49, '✓')

        if self.rg_t_foreign_nationality.value == '有':
            pdf.draw_string(241.5, 43, '✓')

            if self.dd_foreign_nationality1.value != "":
                sql = (f'''
                    SELECT
                        username1 || " " || username2 AS 氏名,
                        username1_hurigana || " " || username2_hurigana AS ふりがな,
                        prefectures || municipalities || townarea || house_number AS 住所,
                        building AS 建物名
                    FROM heir
                    WHERE username1 || " " || username2 = "{self.dd_foreign_nationality1.value}"
                ''')
                self.foreign_nationality = GlobalValues.get_db(sql, row_factory=True)[0]
                pdf.draw_string(170, 28, f'{self.foreign_nationality["氏名"]}({jaconv.hira2kata(self.foreign_nationality["ふりがな"])})', 8)
                pdf.draw_string(212, 30, self.foreign_nationality["住所"], 8)
                pdf.draw_string(212, 26, self.foreign_nationality["建物名"], 8)

            if self.dd_foreign_nationality2.value != "":
                sql = (f'''
                    SELECT
                        username1 || " " || username2 AS 氏名,
                        username1_hurigana || " " || username2_hurigana AS ふりがな,
                        prefectures || municipalities || townarea || house_number AS 住所,
                        building AS 建物名
                    FROM heir
                    WHERE username1 || " " || username2 = "{self.dd_foreign_nationality2.value}"
                ''')
                self.foreign_nationality = GlobalValues.get_db(sql, row_factory=True)[0]
                pdf.draw_string(170, 17, f'{self.foreign_nationality["氏名"]}({self.foreign_nationality["ふりがな"]})', 8)
                pdf.draw_string(212, 19, self.foreign_nationality["住所"], 8)
                pdf.draw_string(212, 15, self.foreign_nationality["建物名"], 8)
        else:
            pdf.draw_string(263, 43, '✓')

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'みずほ銀行_相続届1'),
                     os.path.dirname(__file__) + "/pdf/みずほ銀行_相続届.pdf", page=1, open_bool=False)

        ### 裏面
        pdf = PdfCreate("A3", 'landscape')
        # sql = (f'''
        #     SELECT
        #         t1.branch_code AS 店番号,
        #         t1.bank_number AS 口座番号,
        #         t1.deposit_type AS 種類,
        #         t2.bank_name AS 支店名
        #     FROM bank_customer t1
        #         INNER JOIN bank AS t2
        #         ON t1.jba_code = t2.jba_code
        #         AND t1.jba_code = "0001"
        #     WHERE t1.code = ?
        # ''')

        ### 5 預金等の取り扱い方法
        sql = ('''
            SELECT
                t1.branch_code AS 店番号,
                t1.bank_number AS 口座番号,
                t1.deposit_type AS 種類
            FROM bank_customer t1
            WHERE t1.code = ?
            AND jba_code = "0001"
        ''')
        bunk_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))

        for i, bunk_record in enumerate(bunk_records):
            print(i, bunk_record, end='\n\n')
            if bunk_record[2] == '普通預金':
                pdf.draw_string(39, 181 - i * 17.1, '✓', 8)
            elif bunk_record[2] == '当座預金':
                pdf.draw_string(47, 181 - i * 17.1, '✓', 8)
            elif '貯蓄' in bunk_record[2]:
                pdf.draw_string(55, 181 - i * 17.1, '✓', 8)
            elif bunk_record[2] == '定期預金':
                pdf.draw_string(63, 181 - i * 17.1, '✓', 8)
            elif bunk_record[2] == '外貨預金':
                pdf.draw_string(71, 181 - i * 17.1, '✓', 8)
            elif bunk_record[2] == '外貨定期':
                pdf.draw_string(84, 181 - i * 17.1, '✓', 8)
            elif bunk_record[2] == 'カードローン':
                pdf.draw_string(97, 181 - i * 17.1, '✓', 8)
            elif bunk_record[2] == 'その他':
                pdf.draw_string(111, 181 - i * 17.1, '✓', 8)

            pdf.draw_string(60, 175 - i * 17.1, bunk_record[0], 8)
            pdf.draw_string(77, 175 - i * 17.1, bunk_record[1], 8)
            pdf.draw_string(39, 169 - i * 16.7, '✓', 8)

        ### 6 貸金庫

        ### 7 投資信託・債権

        ### 8 受取方法
        sql = ('''
            SELECT 
                username1 || " " || username2,
                heir_bank.jba_code,
                heir_bank.branch_code,
                heir_bank.bank_number,
                heir_bank.subjects,
                username1_hurigana || " " || username2_hurigana
            FROM heir 
                INNER JOIN heir_bank 
                ON heir.heir_id = heir_bank.heir_id 
                    INNER JOIN bank_customer 
                    ON bank_customer.bank_customer_id = heir_bank.bank_customer_id
                    AND bank_customer.jba_code = "0001"
            WHERE heir.code = ?
        ''')
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        print('records:', records)

        ### 弊社に入金
        # pdf.draw_string(163.5, 94, '✓')
        # pdf.draw_string(175, 59, "ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞ", 5)
        # pdf.draw_string(168, 57.5, "ﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ", 5)
        # pdf.draw_string(168, 56, "ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ", 5)
        # pdf.draw_string(168, 54, "相続手続支援センター町田", 5)
        # pdf.draw_string(168, 52, "有限責任事業組合　組合員", 5)
        # pdf.draw_string(168, 50, "株式会社プロフィット・ワン", 5)
        # pdf.draw_string(168, 48, "職務執行者　大貫利一", 5)
        # pdf.draw_string(202.5, 53, '✓')
        # pdf.draw_string(205, 48, "多摩")
        # pdf.draw_string(237, 56.5, "町田")
        # pdf.draw_string(235, 50, '✓')
        # pdf.draw_string(252.5, 48, "0008035")

        ### お客様に入金
        if records[0][0] is not None:
            # pdf.draw_string(163.5, 94, '✓')
            if len(records) == 1:
            # if records[0][5] == 1:
                pdf.draw_string(163.5, 94, '✓')
            else:
                pdf.draw_string(163.5, 81, '✓')

            for i, record in enumerate(records):
                pdf.draw_string(172, 55 - i * 17, jaconv.hira2kata(record[5]), 8)
                pdf.draw_string(172, 50 - i * 17, record[0])
                banks = BankSearch.bank_search(code=str(record[1]).zfill(4))
                for bank_name, bank_code in banks:
                    if bank_name == 'みずほ':
                        pdf.draw_string(202.5, 57 - i * 17, '✓')
                    else:
                        pdf.draw_string(202.5, 53 - i * 17, '✓')
                        pdf.draw_string(205, 48 - i * 17, bank_name.replace('銀行', ''))
                            # pdf.draw_string(205, 48, Gincode.get_gincode(bank_code)[3])
                    branches = BankSearch.branch_search(bank_code=bank_code, code=str(record[2]).zfill(3))

                    if bank_code == '9900':
                        pdf.draw_string(235, 50 - i * 17, '✓')
                        pdf.draw_string(252.5, 48 - i * 17, str(record[3]).zfill(7)[:7])

                    else:
                        branch_name = [branch_name for branch_code, branch_name in branches]
                        pdf.draw_string(237, 56.5 - i * 17, branch_name[0])
                        if '普通' in record[4]:
                            pdf.draw_string(235, 50 - i * 17, '✓')
                        elif '当座' in record[4]:
                            pdf.draw_string(243, 50 - i * 17, '✓')
                        elif '貯蓄' in record[4]:
                            pdf.draw_string(235, 47.5 - i * 17, '✓')
                        else:
                            pdf.draw_string(243, 47.5 - i * 17, '✓')
                        pdf.draw_string(252.5, 48 - i * 17, str(record[3]).zfill(7))

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'みずほ銀行_相続届2'),
                     os.path.dirname(__file__) + "/pdf/みずほ銀行_相続届.pdf", page=2, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書', 'みずほ銀行_相続届'),
            os.path.join(self.customer['フォルダパス'], 'みずほ銀行_相続届1'),
            os.path.join(self.customer['フォルダパス'], 'みずほ銀行_相続届2')
        )

    # 送付書類明細表
    def submission_item_create(self):
        self.tf_x = ft.TextField(label="X調整値", value="0", hint_text="右に調整はプラス値、左はマイナス値")
        self.tf_y = ft.TextField(label="Y調整値", value="0", hint_text="上に調整はプラス値、下はマイナス値")

        self.t_will = ft.Text('遺言書の有無')
        self.rg_will = ft.RadioGroup(
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
            value='無',
        )

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('みずほ銀行_送付書類明細表を作成'),
            content=ft.Column(
                [
                    self.tf_x,
                    self.tf_y,
                    self.t_will,
                    self.rg_will,
                ],
                height=400,
                width=50
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True, on_click=self.submission_item),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def submission_item(self, _):
        self.close_dlg(self)
        sql = (f'''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名,
                (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
                t4.username1 || "  " || t4.username2 AS 相続人,
                t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0001"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "0001"
                        INNER JOIN heir AS t4
                        ON t4.code = t1.code
                        AND t4.code = "{GlobalValues.code}"
                        AND t4.offer = 1
            WHERE t1.code = "{GlobalValues.code}"
        ''')
        self.customer = GlobalValues.get_db(sql, row_factory=True)[0]
        print(GlobalValues.get_db(sql[0]))
        pdf = PdfCreate("A4")
        if self.rg_will.value == '無':
            pdf.draw_string(115, 240, "〇", 16)
        else:
            pdf.draw_string(129, 240, "〇", 16)
        pdf.draw_string(149.8, 222, "〇")
        pdf.draw_string(51, 217, "194")
        pdf.draw_string(69, 217, "0022")
        pdf.draw_string(32, 210, "東京都町田市森野一丁目22番5号")
        pdf.draw_string(32, 198, "相続手続支援センター町田有限責任事業組合　組合員　株式会社プロフィット・ワン　職務執行者　大貫利一", 9)
        pdf.draw_string(124, 204, "042")
        pdf.draw_string(146, 204, "710")
        pdf.draw_string(167, 204, "6178")
        pdf.draw_string(22, 139, "✓", 12)
        pdf.draw_string(22, 124, "✓", 12)
        pdf.draw_string(22, 112.5, "✓", 12)
        pdf.draw_string(115, 87, "〇")
        pdf.draw_string(115, 68, "〇")
        pdf.draw_string(115, 62, "〇")
        pdf.draw_string(115, 43, "〇")
        pdf.draw_string(115, 36.5, "〇")
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書', 'みずほ_送付書類明細表'),
                     os.path.dirname(__file__) + "/pdf/みずほ_送付書類明細表.pdf", page=1, open_bool=True)


def main(page: ft.Page):
    GlobalValues.code = "E00343"
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = Mizuhobank()
    page.add(cl)
    # cl.account_freezing()
    # cl.account_freezing_create('')
    # cl.balance_certificate()
    cl.inheritance_notification()
    # cl.submission_item_create()


if __name__ == '__main__':
    ft.app(target=main)
    # GlobalValues.code = "E00246"
    # cl = Mizuhobank()
    # cl.balance_certificate()
    # cl.inheritance_notification()
