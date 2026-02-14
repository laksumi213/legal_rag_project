### 三菱UFJ銀行
import flet as ft
from globalvalues import GlobalValues
from zengin import BankSearch
from pdf_create import PdfCreate
from convert_to_wareki import convert_to_wareki2
from datetime import datetime
import jaconv
import mojimoji
import re
import os.path

from web_operation import Web


from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time


class Mufg(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.customer = None
        self.page = GlobalValues.my_page

    def build(self):
        pass

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    def account_freezing(self):
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

        self.tf_balance_certificate = ft.Text('残高証明書')
        self.rg_balance_certificate = ft.RadioGroup(
            value='有',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('三菱UFJ銀行の口座凍結手続き'),
            content=ft.Column(
                [
                    self.t_discussed_document,
                    self.rg_discussed_document,
                    ft.VerticalDivider(),
                    self.t_will,
                    self.rg_will,
                    ft.VerticalDivider(),
                    self.tf_balance_certificate,
                    self.rg_balance_certificate
                ],
                height=250,
            ),
            actions=[ft.ElevatedButton("OK", on_click=self.account_freezing_create1, autofocus=True),
                     ft.ElevatedButton("キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def account_freezing_create1(self, e):
        self.close_dlg(self)
        self.page.update()

        self.bw = webdriver.Chrome()
        self.bw.implicitly_wait(3)
        self.bw.get("https://sozoku.bk.mufg.jp/uketsuke/A010")
        self.bw.maximize_window()

        # 確認しました
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[2]/ul/li/label/span").click()
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[4]/ul/li/label/span").click()
        time.sleep(0.5)

        # 次へ
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/a[2]/span").click()

        # Eメールアドレス
        self.bw.find_element(By.ID, 'MailAddress').send_keys('t-morimati@tax-info.jp')
        self.bw.find_element(By.ID, 'MailAddressConfirmation').send_keys('t-morimati@tax-info.jp')

        # 次へ
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/nav/ul/li[2]/a/p").click()
        time.sleep(0.5)

        # 登録する
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/nav/ul/li[2]/a/p").click()

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('三菱UFJ銀行の口座凍結手続き'),
            content=ft.Column(
                [
                    ft.Text('「認証番号入力後」にOKボタンをクリックしてください。'),
                ],
                height=30,
            ),
            actions=[ft.ElevatedButton("OK", on_click=self.account_freezing_create2, autofocus=True)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def account_freezing_create2(self, _):
        self.close_dlg(self)
        self.page.update()
        # self.bw.maximize_window()

        sql = ('''
            SELECT
                 zipcode AS 被相続人_郵便番号,
                 prefectures AS 被相続人_都道府県,
                 municipalities AS 被相続人_市区町村,
                 house_number || building AS 被相続人_住所,
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
                 maiden_name AS 旧姓,
                 maiden_name_huri AS 旧姓_ふりがな,
                 (SELECT branch_code FROM bank_customer WHERE customer.code = bank_customer.code) AS 被相続人_支店コード
            FROM customer 
            WHERE code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]

        # 氏名
        self.bw.find_element(By.ID, 'InheriteeLastName').send_keys(self.customer["被相続人1"].replace('﨑', '崎'))
        self.bw.find_element(By.ID, 'InheriteeFirstName').send_keys(self.customer["被相続人2"])
        self.bw.find_element(By.ID, 'InheriteeLastNameKana').send_keys(jaconv.hira2kata(self.customer["被相続人_かな1"]))
        self.bw.find_element(By.ID, 'InheriteeFirstNameKana').send_keys(jaconv.hira2kata(self.customer["被相続人_かな2"]))

        # 国籍
        self.bw.find_element(By.ID, 'InheriteeNationality').send_keys('日本')

        # 住所
        self.bw.find_element(By.ID, 'InheriteeZipCode1').send_keys(re.findall('[0-9]+', self.customer["被相続人_郵便番号"])[0])
        self.bw.find_element(By.ID, 'InheriteeZipCode2').send_keys(re.findall('[0-9]+', self.customer["被相続人_郵便番号"])[1])
        # 郵便番号から調べる
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/div/form/div[4]/div/ul/li/dl/dd/input[3]").click()
        time.sleep(0.5)

        self.bw.find_element(By.ID, 'InheriteeAddress').send_keys(self.customer["被相続人_住所"])

        # 生年月日
        Select(self.bw.find_element(By.ID, "InheriteeBirthdayYear")).select_by_visible_text(
            re.findall('[0-9]+', self.customer["生年月日"])[0] + '年')
        Select(self.bw.find_element(By.ID, "InheriteeBirthdayMonth")).select_by_visible_text(
            f"{int(re.findall('[0-9]+', self.customer['生年月日'])[1])}月")
        Select(self.bw.find_element(By.ID, "InheriteeBirthdayDay")).select_by_visible_text(
            f"{int(re.findall('[0-9]+', self.customer['生年月日'])[2])}日")

        # 死亡日
        Select(self.bw.find_element(By.ID, "InheriteeDateOfDeathYear")).select_by_visible_text(
            re.findall('[0-9]+', self.customer['死亡日'])[0] + '年')
        Select(self.bw.find_element(By.ID, "InheriteeDateOfDeathMonth")).select_by_visible_text(
            f"{int(re.findall('[0-9]+', self.customer['死亡日'])[1])}月")
        Select(self.bw.find_element(By.ID, "InheriteeDateOfDeathDay")).select_by_visible_text(
            f"{int(re.findall('[0-9]+', self.customer['死亡日'])[2])}日")

        sql = ('''
            SELECT
                branch_code AS 被相続人_支店コード,
                bank_number AS 被相続人_口座番号,
                deposit_type AS 被相続人_口座種類,
                jba_code AS 被相続人_銀行コード
            FROM bank_customer
            WHERE 
                code = ?
            AND 
                jba_code = "0005"
        ''')
        # customer_bank = GlobalValues.get_db(sql, tuple([GlobalValues.code]), row_factory=True)
        customer_banks = GlobalValues.get_db(sql, tuple([GlobalValues.code]), row_factory=False)

        # bank_name, bank_code = list(BankSearch.bank_search(code=str(customer_bank[0]['被相続人_銀行コード']).zfill(4)))[0]
        # branch_code, branch_name = list(BankSearch.branch_search(bank_code=bank_code, code=str(customer_bank[0]['被相続人_支店コード']).zfill(3)))[0]

        for i, customer_bank in enumerate(customer_banks):
            num = str(i + 1)

            # bank_name, bank_code = list(BankSearch.bank_search(code=str(customer_bank[3]).zfill(4)))[0]
            branch_code, branch_name = list(BankSearch.branch_search(bank_code=str(customer_bank[3]).zfill(4), code=str(customer_bank[0]).zfill(3)))[0]

            # 2口座目を登録
            if i == 1:
                self.bw.find_element(By.XPATH, "/html/body/article/section/div/div/form/div[8]/h2/label/span[1]").click()

            # 3口座目を登録
            elif i == 2:
                self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[9]/h2/label').click()

            # 4口座目を登録
            elif i == 3:
                self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[10]/h2/label').click()

            # 5口座目を登録
            elif i == 4:
                self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[11]/h2/label').click()

            # 6口座目以降
            elif i == 5:
                self.bw.find_element(By.ID, "InheriteeAccountInfoOther").send_keys('')

            # 金融機関
            Select(self.bw.find_element(By.ID, 'InheriteeFinancialInstitution' + num)).select_by_visible_text(
                "三菱UFJ銀行（金融機関コード：0005）")
            time.sleep(0.5)

            # 店番
            self.bw.find_element(By.ID, 'InheriteeOfficeNumber' + num).send_keys(branch_code)

            # 店名
            self.bw.find_element(By.ID, 'InheriteeOfficeName' + num).send_keys(branch_name)

            # 科目
            if '普通' in customer_bank[2]:
                Select(self.bw.find_element(By.ID, "InheriteeAccountType" + num)).select_by_visible_text("普通預金（総合口座）")
            elif '定期' in customer_bank[2]:
                Select(self.bw.find_element(By.ID, "InheriteeAccountType" + num)).select_by_visible_text("定期預金")
            elif '貯蓄' in customer_bank[2]:
                Select(self.bw.find_element(By.ID, "InheriteeAccountType" + num)).select_by_visible_text("貯蓄預金")
            elif '当座' in customer_bank[2]:
                Select(self.bw.find_element(By.ID, "InheriteeAccountType" + num)).select_by_visible_text("当座預金")
            elif '外貨' in customer_bank[2]:
                Select(self.bw.find_element(By.ID, "InheriteeAccountType" + num)).select_by_visible_text("外貨預金")

            # 口座番号
            self.bw.find_element(By.ID, 'InheriteeAccountNumber' + num).send_keys(str(customer_bank[1]).zfill(7))

        # 次へ
        self.bw.find_element(By.XPATH, '//*[@id="form0"]/nav/ul/li[2]/a').click()
        time.sleep(0.5)

        # 姓名
        self.bw.find_element(By.ID, 'NotifierLastName').send_keys('堀池')
        self.bw.find_element(By.ID, 'NotifierFirstName').send_keys('千ひろ')
        self.bw.find_element(By.ID, 'NotifierLastNameKana').send_keys('ホリイケ')
        self.bw.find_element(By.ID, 'NotifierFirstNameKana').send_keys('チヒロ')
        # self.bw.find_element(By.ID, 'NotifierLastName').send_keys('森町')
        # self.bw.find_element(By.ID, 'NotifierFirstName').send_keys('翼')
        # self.bw.find_element(By.ID, 'NotifierLastNameKana').send_keys('モリマチ')
        # self.bw.find_element(By.ID, 'NotifierFirstNameKana').send_keys('ツバサ')

        # 住所
        # 上記以外をクリック
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[3]/ul/li/div/label[2]").click()
        time.sleep(0.5)
        self.bw.find_element(By.ID, 'NotifierZipCode1').send_keys('194')
        self.bw.find_element(By.ID, 'NotifierZipCode2').send_keys('0022')
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[4]/div/ul/li/dl/dd/input[3]").click()
        time.sleep(0.5)
        self.bw.find_element(By.ID, 'NotifierAddress').send_keys('1-22-5 町田310五十子ビル3階')

        # 電話番号
        self.bw.find_element(By.ID, 'NotifierPhoneNumber11').send_keys('080')
        self.bw.find_element(By.ID, 'NotifierPhoneNumber12').send_keys('4800')
        self.bw.find_element(By.ID, 'NotifierPhoneNumber13').send_keys('3208')
        # self.bw.find_element(By.ID, 'NotifierPhoneNumber11').send_keys('042')
        # self.bw.find_element(By.ID, 'NotifierPhoneNumber12').send_keys('710')
        # self.bw.find_element(By.ID, 'NotifierPhoneNumber13').send_keys('6178')

        # 電話番号種類
        Select(self.bw.find_element(By.ID, "NotifierPhoneType1")).select_by_visible_text("勤務先")

        # お亡くなりになられた方からみたご関係
        Select(self.bw.find_element(By.ID, "NotifierRelationship")).select_by_visible_text("その他")
        time.sleep(0.5)
        self.bw.find_element(By.ID, 'NotifierRelationshipOther').send_keys('代理人')

        # 次へ
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/nav/ul/li[2]/a/p").click()
        time.sleep(0.5)

        # 遺言書有無
        if self.rg_will.value == '有':
            self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[1]/ul/li/div/label[1]').click()
        else:
            self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[1]/ul/li/div/label[2]").click()
        time.sleep(0.5)

        # 遺産分割協議書
        if self.rg_discussed_document.value == '有':
            # 作成予定
            self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[3]/ul[2]/li/div/label[3]').click()
        else:
            # わからない
            self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[3]/ul[2]/li/div/label[4]").click()
        time.sleep(0.5)

        # 相続手続書類の郵送を希望する
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[6]/ul[2]/li/div/label[1]").click()
        time.sleep(0.5)

        # 郵送先
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/div[8]/ul[1]/li/div/label[2]").click()
        time.sleep(0.5)

        # 残高証明書
        if self.rg_balance_certificate.value == '有':
            self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[7]/ul[2]/li/div/label[1]').click()
        else:
            self.bw.find_element(By.XPATH, '//*[@id="form0"]/div[7]/ul[2]/li/div/label[2]').click()

        # 次へ
        self.bw.find_element(By.XPATH, "/html/body/article/section/div/form/nav/ul/li[2]/a/p").click()
        time.sleep(0.5)

    # 残高証明書
    def balance_certificate(self):
        self.dt_now = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'), autofocus=True)
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('三菱UFJ銀行の手続き'),
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
        # dt_now = datetime(datetime.now().year, datetime.now().month, 30).strftime('%Y/%m/%d')
        # dt_now = datetime.now().strftime('%Y/%m/%d')

        pdf = PdfCreate("A4")
        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.maiden_name AS 被相続人_旧姓,
                t1.username2 AS 被相続人_名,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0005"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
            WHERE t1.code = ?
        ''')
        # gv = GlobalValues()
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)

        # 日付
        if self.dt_now.value:
            dt = re.findall('[0-9]+', convert_to_wareki2(self.dt_now.value))
            pdf.draw_string(28, 275, str(dt[0]).zfill(2)[0], 11)
            pdf.draw_string(33, 275, str(dt[0]).zfill(2)[1], 11)
            pdf.draw_string(46, 275, str(dt[1]).zfill(2)[0], 11)
            pdf.draw_string(51, 275, str(dt[1]).zfill(2)[1], 11)
            pdf.draw_string(63, 275, str(dt[2]).zfill(2)[0], 11)
            pdf.draw_string(69, 275, str(dt[2]).zfill(2)[1], 11)

        pdf.draw_string(30, 265.5, '194', 8)
        pdf.draw_string(46, 265.5, '0022', 8)
        pdf.draw_string(47.5, 260, '〇', 15)
        pdf.draw_string(31, 257, '東京', 12)
        pdf.draw_string(65, 257, '町田市', 12)
        pdf.draw_string(31, 248, '森野一丁目22番5号', 12)
        pdf.draw_string(135, 258, '042', 10)
        pdf.draw_string(135, 250, '710', 10)
        pdf.draw_string(156, 250, '6178', 10)
        pdf.draw_string(31, 240, '相続手続支援センター町田有限責任事業組合　組合員')
        pdf.draw_string(31, 235, '株式会社プロフィット・ワン　職務執行者　大貫利一')

        # if self.customer[0]['被相続人_旧姓'] != '':
        #     pdf.draw_string(150, 238, self.customer[0]['被相続人'], 12)
        #     pdf.draw_string(150, 233, f"旧姓：{self.customer[0]['被相続人_旧姓']}　{self.customer[0]['被相続人_名']}", 12)
        #
        # else:
        #     pdf.draw_string(150, 235, self.customer[0]['被相続人'], 12)
        pdf.draw_string(150, 235, self.customer[0]['被相続人'], 12)

        ### 残高証明書 ###
        bool = 0
        rec_row = []
        for i, bank_apdfount_record in enumerate(self.customer):
            print(bank_apdfount_record["支店名"], bank_apdfount_record["口座番号"], bank_apdfount_record["種類"])
            pdf.draw_string(9, (215 - i * 7), str(bank_apdfount_record["店番号"]).zfill(3)[0], 11)
            pdf.draw_string(16, (215 - i * 7), str(bank_apdfount_record["店番号"]).zfill(3)[1], 11)
            pdf.draw_string(24, (215 - i * 7), str(bank_apdfount_record["店番号"]).zfill(3)[2], 11)

            pdf.draw_string(35, (215 - i * 7), bank_apdfount_record["支店名"], 11)

            if '普通' in bank_apdfount_record["種類"]:
                pdf.draw_string(72, (217 - i * 7), '✓', 8)
            else:
                pdf.draw_string(72, (214 - i * 7), '✓', 8)
                pdf.draw_string(85, (214.5 - i * 7), bank_apdfount_record["種類"].replace('預金', ''), 8)

            if '定期' in bank_apdfount_record["種類"]:
                bool = 1
                rec_row.append(i)

            pdf.draw_string(114, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[0], 11)
            pdf.draw_string(122, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[1], 11)
            pdf.draw_string(130, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[2], 11)
            pdf.draw_string(138, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[3], 11)
            pdf.draw_string(145.5, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[4], 11)
            pdf.draw_string(153, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[5], 11)
            pdf.draw_string(161, (215 - i * 7), str(bank_apdfount_record["口座番号"]).zfill(7)[6], 11)

            pdf.draw_string(192, (215 - i * 7), '1', 11)

        ### 経過利息 ###
        if bool == 1:
            deathday = re.findall('[0-9]+', convert_to_wareki2(self.customer[0]["死亡日"]))
            pdf.draw_string(40, 89, str(deathday[0]).zfill(2)[0], 12)
            pdf.draw_string(46, 89, str(deathday[0]).zfill(2)[1], 12)
            pdf.draw_string(58, 89, str(deathday[1]).zfill(2)[0], 12)
            pdf.draw_string(65, 89, str(deathday[1]).zfill(2)[1], 12)
            pdf.draw_string(77, 89, str(deathday[2]).zfill(2)[0], 12)
            pdf.draw_string(82, 89, str(deathday[2]).zfill(2)[1], 12)
            
        for i, rec in enumerate(rec_row):
            pdf.draw_string(9, (170 - i * 7), str(self.customer[rec]["店番号"]).zfill(3)[0], 11)
            pdf.draw_string(16, (170 - i * 7), str(self.customer[rec]["店番号"]).zfill(3)[1], 11)
            pdf.draw_string(24, (170 - i * 7), str(self.customer[rec]["店番号"]).zfill(3)[2], 11)

            pdf.draw_string(35, (170 - i * 7), self.customer[rec]["支店名"], 11)
            pdf.draw_string(80, (170 - i * 7), self.customer[rec]["種類"].replace('預金', ''), 11)

            pdf.draw_string(114, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[0], 11)
            pdf.draw_string(122, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[1], 11)
            pdf.draw_string(130, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[2], 11)
            pdf.draw_string(138, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[3], 11)
            pdf.draw_string(145.5, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[4], 11)
            pdf.draw_string(153, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[5], 11)
            pdf.draw_string(161, (170 - i * 7), str(self.customer[rec]["口座番号"]).zfill(7)[6], 11)

            pdf.draw_string(167, (172 - i * 7), '✓', 8)
            pdf.draw_string(194, (172 - i * 7), '1', 8)
            # bool = 0

        ### 証明日 ###
        deathday = re.findall('[0-9]+', convert_to_wareki2(self.customer[0]["死亡日"]))
        pdf.draw_string(40, (102), str(deathday[0]).zfill(2)[0], 12)
        pdf.draw_string(46, (102), str(deathday[0]).zfill(2)[1], 12)
        pdf.draw_string(58, (102), str(deathday[1]).zfill(2)[0], 12)
        pdf.draw_string(65, (102), str(deathday[1]).zfill(2)[1], 12)
        pdf.draw_string(77, (102), str(deathday[2]).zfill(2)[0], 12)
        pdf.draw_string(82, (102), str(deathday[2]).zfill(2)[1], 12)

        ### 受取方法 ###
        pdf.draw_string(22, 53, '✓', 8)
        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書1'),
                     os.path.dirname(__file__) + "/pdf/三菱UFJ_残高証明書依頼書.pdf", page=1, open_bool=False)

        # 書類2
        pdf = PdfCreate("A4")
        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書2'),
                     os.path.dirname(__file__) + "/pdf/三菱UFJ_残高証明書依頼書.pdf", page=2, open_bool=False)

        # 書類3
        pdf = PdfCreate("A4")
        pdf.draw_string(30, 265.5, '194', 8)
        pdf.draw_string(46, 265.5, '0022', 8)
        pdf.draw_string(47.5, 260, '〇', 16)
        pdf.draw_string(31, 257, '東京', 12)
        pdf.draw_string(65, 257, '町田市', 12)
        pdf.draw_string(31, 248, '森野一丁目22番5号', 12)
        pdf.draw_string(31, 240, '相続手続支援センター町田有限責任事業組合組合員', 10)
        pdf.draw_string(31, 235, '株式会社プロフィット・ワン 職務執行者　大貫利一', 10)
        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書3'),
                     os.path.dirname(__file__) + "/pdf/三菱UFJ_残高証明書依頼書.pdf", page=3, open_bool=False)

        os.makedirs(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書'), exist_ok=True)

        pdf.pdf_marge(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書', '三菱UFJ_残高証明書依頼書'),
            os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書1'),
            os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書2'),
            os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書3')
        )


    def inheritance_notification(self):
        self.dt_now = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'), autofocus=True)
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('三菱UFJ銀行の手続き'),
            content=ft.Column(
                [
                    self.dt_now,
                ],
                height=100,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True, on_click=self.inheritance_notification_create),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def inheritance_notification_create(self, _):
        self.close_dlg(self)
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', convert_to_wareki2(dt_now))
        dt = re.findall('[0-9]+', convert_to_wareki2(self.dt_now.value))

        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.prefectures || t1.municipalities || t1.townarea || t1.house_number AS 住所,
                t1.building AS 建物名,
                t1.birthday AS 生年月日,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名,
                t4.username1 || " " || t4.username2 AS 相続人,
                t4.username1_hurigana || " " || t4.username2_hurigana AS 相続人_かな
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0005"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                        INNER JOIN heir AS t4
                        ON t1.code = t4.code
                        AND t4.offer = 1
                        AND t4.situation = ""
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]), False))

        pdf = PdfCreate("A3")
        # 記入日
        pdf.draw_string(111, 197.5, convert_to_wareki2(self.dt_now.value)[0:2] + dt[0], 7)
        pdf.draw_string(123, 197.5, dt[1], 7)
        pdf.draw_string(133, 197.5, dt[2], 7)

        # 被相続人
        pdf.draw_string(27, 56, self.customer[0]['被相続人'].replace('﨑', '崎'), 12)
        pdf.draw_string(27, 46, self.customer[0]['被相続人'], 12)
        pdf.draw_string(73, 53, self.customer[0]['住所'], 8)
        pdf.draw_string(73, 47, self.customer[0]['建物名'], 8)

        dt_birthday = re.findall(r'\d+', convert_to_wareki2(self.customer[0]['生年月日']))
        wareki_birthday = convert_to_wareki2(self.customer[0]['生年月日'])[0:2]
        if wareki_birthday == '大正':
            pdf.draw_string(23.5, 35.2, '〇', 8)
        elif wareki_birthday == '昭和':
            pdf.draw_string(26.6, 35.2, '〇', 8)
        elif wareki_birthday == '平成':
            pdf.draw_string(30, 35.2, '〇', 8)
        elif wareki_birthday == '令和':
            pdf.draw_string(33.2, 35.2, '〇', 8)
        pdf.draw_string(40, 35.2, dt_birthday[0])
        pdf.draw_string(52, 35.2, dt_birthday[1])
        pdf.draw_string(63, 35.2, dt_birthday[2])

        dt_deathday = re.findall(r'\d+', convert_to_wareki2(self.customer[0]['死亡日']))
        wareki_deathday = convert_to_wareki2(self.customer[0]['死亡日'])[0:2]
        if wareki_deathday == '昭和':
            pdf.draw_string(89, 35.2, '〇', 8)
        elif wareki_deathday == '平成':
            pdf.draw_string(92.2, 35.2, '〇', 8)
        elif wareki_deathday == '令和':
            pdf.draw_string(95.5, 35.2, '〇', 8)
        pdf.draw_string(102, 35.2, dt_deathday[0])
        pdf.draw_string(115, 35.2, dt_deathday[1])
        pdf.draw_string(127, 35.2, dt_deathday[2])

        # 相続人代表者
        sql = 'SELECT COUNT(*) FROM heir WHERE code = ? AND situation = ""'
        heir_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
        pdf.draw_string(172, 186, f'ｿｳｿﾞｸﾆﾝ{mojimoji.zen_to_han(jaconv.hira2kata(self.customer[0]["相続人_かな"]))} ﾎｶ{heir_count - 1}ﾆﾝ ﾀﾞｲﾘﾆﾝ ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞ', 5)
        pdf.draw_string(156, 183.5, 'ﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄ・ﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 5)
        pdf.draw_string(156, 181, f'相続人　{self.customer[0]["相続人"]}　他{heir_count - 1}人　代理人', 6)
        pdf.draw_string(156, 178, '相続手続支援センター町田有限責任事業組合　組合員', 6)
        pdf.draw_string(156, 175, '株式会社プロフィット・ワン　職務執行者　大貫利一', 6)
        pdf.draw_string(220, 180, '042')
        pdf.draw_string(232, 180, '710')
        pdf.draw_string(248, 180, '6178')
        pdf.draw_string(163, 171, '194', 8)
        pdf.draw_string(173, 171, '0022', 8)
        pdf.draw_string(163, 165, '東京都町田市森野一丁目22番5号')

        # 海外の方
        pdf.draw_string(258, 158, '✓')
        pdf.draw_string(258, 152, '✓')

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '三菱UFJ_相続届1'),
                     os.path.dirname(__file__) + "/pdf/三菱UFJ_相続届.pdf", page=1, open_bool=False)

        pdf = PdfCreate("A3")
        # 円預金
        for i, customer in enumerate(self.customer):
            pdf.draw_string(13, 181 - i * 6.3, str(customer['店番号']).zfill(3))
            pdf.draw_string(26, 181 - i * 6.3, customer['支店名'], 8)
            if '普通' in customer['種類']:
                pdf.draw_string(53, 184 - i * 6.3, '✓')
            elif '定期' in customer['種類']:
                pdf.draw_string(65.5, 184 - i * 6.3, '✓')
            elif '貯蓄' in customer['種類']:
                pdf.draw_string(53, 181.5 - i * 6.3, '✓')
            pdf.draw_string(110, 181.5 - i * 6.3, str(customer['口座番号']).zfill(7))

        # 受取方法
        ## まとめてご入金
        pdf.draw_string(152, 174, '✓')

        sql = ('''
                    SELECT
                        t1.username1 || " " || t1.username2 AS 相続人,
                        t2.heir_bank_id AS heir_bank_id,
                        t2.heir_id AS heir_id,
                        t2.jba_code AS 銀行コード,
                        t2.branch_code AS 支店コード,
                        t2.bank_number AS 口座番号,
                        t2.subjects AS 種類,
                        t1.username1_hurigana || " " || t1.username2_hurigana AS 相続人_ふりがな
                    FROM heir_bank AS t2
                        INNER JOIN heir AS t1
                        ON t1.heir_id = t2.heir_id
                    WHERE t2.bank_customer_id = (
                        SELECT bank_customer_id
                        FROM bank_customer
                        WHERE code = ?
                        AND jba_code = "0005"
                    )
                ''')
        try:
            heir_offer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
            print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])
            banks = [(bank_name, bank_code) for bank_name, bank_code in
                     BankSearch.bank_search(code=str(heir_offer['銀行コード']).zfill(4))][0]
            print('banks:', banks)

            if banks[1] == '9900':
                branches = BankSearch.branch_search2(bank_code='9900', branch_code=f"{heir_offer['支店コード']}-{heir_offer['口座番号']}")

            else:
                branches = [(branch_code, branch_name) for branch_code, branch_name in
                            BankSearch.branch_search(bank_code=str(heir_offer['銀行コード']).zfill(4),
                                                     code=str(heir_offer['支店コード']).zfill(3))][0]
            print('branches:', branches)
            pdf.draw_string(195, 176, jaconv.hira2kata(heir_offer['相続人_ふりがな']), 8)
            pdf.draw_string(195, 172, heir_offer['相続人'])
            if banks[0] == '三菱ＵＦＪ銀行':
                pdf.draw_string(151.5, 164, '✓')
            else:
                pdf.draw_string(151.5, 160.5, '✓')
                pdf.draw_string(157, 161, banks[0], 8)

            pdf.draw_string(213, 161, branches[1])

            if banks[1] == '9900':
                # 店名カナ
                pdf.draw_string(213, 167, branches[4], 8)

                if '普通' in branches[2]:
                    pdf.draw_string(236, 163, '〇', 12)
                elif '当座' in branches[2]:
                    pdf.draw_string(236, 159.5, '〇', 12)
                elif '貯蓄' in branches[2]:
                    pdf.draw_string(244, 163, '〇', 12)

                pdf.draw_string(251, 161, str(branches[3]).zfill(7)[0], 12)
                pdf.draw_string(256, 161, str(branches[3]).zfill(7)[1], 12)
                pdf.draw_string(261, 161, str(branches[3]).zfill(7)[2], 12)
                pdf.draw_string(266, 161, str(branches[3]).zfill(7)[3], 12)
                pdf.draw_string(271, 161, str(branches[3]).zfill(7)[4], 12)
                pdf.draw_string(276, 161, str(branches[3]).zfill(7)[5], 12)
                pdf.draw_string(281, 161, str(branches[3]).zfill(7)[6], 12)

            else:
                if '普通' in heir_offer[6]:
                    pdf.draw_string(236, 163, '〇', 12)
                elif '当座' in heir_offer[6]:
                    pdf.draw_string(236, 159.5, '〇', 12)
                elif '貯蓄' in heir_offer[6]:
                    pdf.draw_string(244, 163, '〇', 12)
                pdf.draw_string(251, 161, str(heir_offer[5]).zfill(7)[0], 12)
                pdf.draw_string(256, 161, str(heir_offer[5]).zfill(7)[1], 12)
                pdf.draw_string(261, 161, str(heir_offer[5]).zfill(7)[2], 12)
                pdf.draw_string(266, 161, str(heir_offer[5]).zfill(7)[3], 12)
                pdf.draw_string(271, 161, str(heir_offer[5]).zfill(7)[4], 12)
                pdf.draw_string(276, 161, str(heir_offer[5]).zfill(7)[5], 12)
                pdf.draw_string(281, 161, str(heir_offer[5]).zfill(7)[6], 12)

        except Exception as e:
            print(e)
            pdf.draw_string(195, 177, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞ ﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ', 6)
            pdf.draw_string(195, 175, 'ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄ・ﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 6)
            pdf.draw_string(195, 172.5, '相続手続支援センター町田有限責任事業組合　組合員', 6)
            pdf.draw_string(195, 170, '株式会社プロフィット・ワン　職務執行者　大貫利一', 6)
            pdf.draw_string(152, 160.5, '✓')
            pdf.draw_string(157, 161, '多摩信用金庫', 8)
            pdf.draw_string(212, 161, '町田支店')
            pdf.draw_string(212, 167, 'ﾏﾁﾀﾞｼﾃﾝ', 8)
            pdf.draw_string(236, 163, '〇', 12)
            pdf.draw_string(251, 161, '0', 12)
            pdf.draw_string(256, 161, '0', 12)
            pdf.draw_string(261, 161, '0', 12)
            pdf.draw_string(266, 161, '8', 12)
            pdf.draw_string(271, 161, '0', 12)
            pdf.draw_string(276, 161, '3', 12)
            pdf.draw_string(281, 161, '5', 12)

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '三菱UFJ_相続届2'),
                     os.path.dirname(__file__) + "/pdf/三菱UFJ_相続届.pdf", page=2, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',
                         '三菱UFJ_相続届'),
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '三菱UFJ_相続届1'),
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',  '三菱UFJ_相続届2')
        )

        # 相続書類送付票
        pdf = PdfCreate("A4")
        pdf.draw_string(31, 238, self.customer[0]['被相続人'], 12)
        pdf.draw_string(31, 207, '相続手続支援センター町田有限責任事業組合　組合員')
        pdf.draw_string(31, 203, '株式会社プロフィット・ワン　職務執行者　大貫利一')
        pdf.draw_string(120, 197, '042')
        pdf.draw_string(142, 197, '710')
        pdf.draw_string(165, 197, '6178')
        pdf.draw_string(27.5, 155.5, '✓')
        pdf.draw_string(27.5, 138.5, '✓')
        pdf.draw_string(27.5, 130.5, '✓')
        pdf.draw_string(27.5, 121.5, '✓')
        pdf.draw_string(110.7, 138.5, '✓')
        pdf.draw_string(124, 138, '履歴事項全部証明書')
        # pdf.draw_string(110.7, 130.5, '✓')
        # pdf.draw_string(124, 130, '相続放棄申述受理証明書')
        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '三菱UFJ_相続書類送付票'),
                     os.path.dirname(__file__) + "/pdf/三菱UFJ_相続書類送付票.pdf", page=1, open_bool=True)


def main(page: ft.Page):
    GlobalValues.code = "2503022"
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = Mufg()
    page.add(cl)
    # cl.account_freezing()
    cl.balance_certificate()
    # cl.inheritance_notification()


if __name__ == '__main__':
    ft.app(target=main)
    # GlobalValues.code = "E00321"
    # cl = Mufg()
    # cl.account_freezing()
    # cl.balance_certificate()
    # cl.inheritance_notification()
