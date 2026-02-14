###
import flet as ft
from globalvalues import GlobalValues
from web_operation import Web
from pdf_create import PdfCreate
from zengin import BankSearch
from convert_to_wareki import convert_to_wareki2
from datetime import datetime
import jaconv
import re
import os
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


class PaypayBank(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.customer = None
        self.page = GlobalValues.my_page
        self.proc = Web()
        sql = (f'''
            SELECT  t1.folder_s_path AS フォルダパス,
                    t1.zipcode AS 郵便番号,
                    t1.prefectures AS 都道府県,
                    t1.municipalities AS 市区町村,
                    t1.house_number AS 番地,
                    t1.building AS 建物,
                    t1.prefectures || t1.municipalities || t1.townarea || t1.house_number AS 住所,
                    t1.username1 || " " || t1.username2 AS 氏名,
                    t1.username1 AS 氏名1,
                    t1.username2 AS 氏名2,
                    t1.username1_hurigana || " " || t1.username2_hurigana AS ふりがな,
                    t1.username1_hurigana AS ふりがな1,
                    t1.username2_hurigana AS ふりがな2,
                    t1.birthday AS 生年月日,
                    t1.deathday AS 死亡日,
                    t1.maiden_name AS 旧姓,
                    t1.maiden_name_huri AS 旧姓ふりがな,
                    t2.branch_code AS 店番号,
                    t2.bank_number AS 口座番号,
                    t2.deposit_type AS 種類,
                    t3.bank_branch_name AS 支店名,
                    (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数
            FROM    customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                    INNER JOIN bank_branch AS t3
                    ON t2.jba_code = t3.jba_code
                    AND t3.jba_code = "0033"
            WHERE   
                    t1.code = "{GlobalValues.code}"
        ''')
        self.customer = GlobalValues.get_db(sql,  row_factory=True)[0]
        print('customer:', GlobalValues.get_db(sql)[0])

        sql = ('''
            SELECT  username1 || " " || username2 AS 氏名,
                    username1_hurigana || " " || username2_hurigana AS 氏名ふりがな,
                    relationship AS 続柄,
                    zipcode AS 郵便番号,
                    prefectures || municipalities || townarea || house_number || building AS 住所,
                    contact_phone AS 携帯,
                    contact_home AS 自宅,
                    birthday AS 生年月日,
                    offer AS 申出人
            FROM    heir
            WHERE   code = ?
            AND     situation = ""
        ''')
        self.heir = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print('heir:', GlobalValues.get_db(sql, tuple([GlobalValues.code])))

    def build(self):
        pass

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    ### 口座凍結
    def account_freezing(self):
        self.account_freezing_create(self)

    def account_freezing_create(self, _):
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', dt_now)
        self.proc.web_open('https://login.paypay-bank.co.jp/gyomu/inquiry/InquiryFormG18.html')
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OK').send_keys(self.customer['死亡日'])
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OP').send_keys(self.customer['氏名'])
        self.proc.driver.find_element(By.ID, '00N6F00000YX9ON').send_keys(jaconv.hira2kata(self.customer['ふりがな']))
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OI').send_keys(self.customer['生年月日'])
        self.proc.driver.find_element(By.ID, 'postCode').send_keys(self.customer['郵便番号'].replace('-', ''))
        self.proc.driver.find_element(By.ID, 'postCodeBtn').click()
        sleep(.5)
        self.proc.driver.find_element(By.ID, 'address').send_keys(self.customer['番地'])
        self.proc.driver.find_element(By.ID, 'otherAddress').send_keys(self.customer['建物'])
        self.proc.driver.find_element(By.ID, '00N6F00000H3ITZ').send_keys(str(self.customer['店番号']).zfill(3))
        self.proc.driver.find_element(By.ID, '00N6F00000H3ITe').send_keys(str(self.customer['口座番号']).zfill(7))
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[11]/div/ul/li[3]/label/span').click()
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[12]/div/ul/li[3]/label/span').click()
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OU').send_keys('大貫　利一')
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OS').send_keys('オオヌキ　トシカズ')
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OV').send_keys('042-710-6178')
        self.proc.driver.find_element(By.ID, '00N6F00000YX9OT').send_keys('t-morimati@tax-info.jp')
        self.proc.driver.find_element(By.ID, 'mailAdress02').send_keys('t-morimati@tax-info.jp')
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[20]/div/ul/li[2]/label/span').click()
        self.proc.driver.find_element(By.ID, 'postCode02').send_keys('1940022')
        self.proc.driver.find_element(By.ID, 'postCodeBtn02 ').click()
        sleep(.5)
        self.proc.driver.find_element(By.ID, 'address02').send_keys('一丁目22番5号')
        self.proc.driver.find_element(By.ID, 'otherAddress02').send_keys('町田310五十子ビル3階')
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[25]/div/ul/li[1]/label/span').click()
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[28]/div/ul/li[1]/label/span').click()
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[29]/div/ul/li[1]/label/span').click()
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[30]/div/ul/li[2]/label/span').click()
        self.proc.driver.find_element(By.XPATH, '//*[@id="contents"]/div/div[31]/div/ul/li[1]/label/span').click()
        self.proc.driver.find_element(By.ID, 'submit').click()

        # pdf = PdfCreate("A4")
        # pdf.draw_string(61, 168, '✓', 8)
        # pdf.pdf_save(os.path.join(self.customer['フォルダパス'], ''),
        #              os.path.dirname(__file__) + "/pdf/.pdf", page=1, open_bool=False)
        #
        # pdf.pdf_marge(
        #     os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表'),
        #     os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表1'),
        #     os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表2'),
        #     os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表3')
        # )

    # 残高証明書
    def balance_certificate(self):
        create_date = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'))
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('銀行の手続き'),
            content=ft.Column(
                [
                    create_date,
                    ft.VerticalDivider(),
                ],
                height=80,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True,
                                       on_click=lambda e: self.balance_certificate_create(create_date.value)),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def balance_certificate_create(self, e):
        self.close_dlg(self)
        dt = re.findall('[0-9]+', convert_to_wareki2(e))
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
                AND t2.jba_code = "0005"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "0005"
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        # sql = (f'''
        #     SELECT
        #         t1.username1 || " " || t1.username2 AS 相続人,
        #         t2.heir_bank_id AS heir_bank_id,
        #         t2.heir_id AS heir_id,
        #         (SELECT bank_name FROM bank WHERE jba_code = t2.jba_code) AS 銀行名,
        #         t2.jba_code AS 銀行コード,
        #         t2.branch_code AS 支店コード,
        #         t2.bank_number AS 口座番号,
        #         t2.subjects AS 種類,
        #         (SELECT bank_branch_name FROM bank_branch WHERE bank_branch_code = t2.branch_code) AS 支店名,
        #         t1.username1_hurigana || " " || t1.username2_hurigana AS 相続人_ふりがな
        #     FROM heir_bank AS t2
        #         INNER JOIN heir AS t1
        #         ON t1.heir_id = t2.heir_id
        #     WHERE t2.bank_customer_id = (
        #         SELECT bank_customer_id
        #         FROM bank_customer
        #         WHERE code = ?
        #         AND jba_code = "5060"
        #     )
        # ''')

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
                AND jba_code = "5060"
            )
        ''')
        heir_offer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        banks = [(bank_name, bank_code) for bank_name, bank_code in
                 BankSearch.bank_search(code=str(heir_offer['銀行コード']).zfill(4))][0]
        print('banks:', banks)

        branches = [(branch_code, branch_name) for branch_code, branch_name in
                    BankSearch.branch_search(bank_code=str(heir_offer['銀行コード']).zfill(4),
                                             code=str(heir_offer['支店コード']).zfill(3))][0]
        print('branches:', branches)

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
        pdf.draw_string(31, 240, '相続手続支援センター町田有限責任事業組合組合員')
        pdf.draw_string(31, 235, '株式会社プロフィット・ワン 職務執行者　大貫利一')

        ### 証明日 ###
        deathday = re.findall('[0-9]+', convert_to_wareki2(self.customer[0]["死亡日"]))
        pdf.draw_string(40, (102), str(deathday[0]).zfill(2)[0], 12)
        pdf.draw_string(46, (102), str(deathday[0]).zfill(2)[1], 12)
        pdf.draw_string(58, (102), str(deathday[1]).zfill(2)[0], 12)
        pdf.draw_string(65, (102), str(deathday[1]).zfill(2)[1], 12)
        pdf.draw_string(77, (102), str(deathday[2]).zfill(2)[0], 12)
        pdf.draw_string(82, (102), str(deathday[2]).zfill(2)[1], 12)

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '〇〇'),
                     os.path.dirname(__file__) + "/pdf/〇〇.pdf", page=1, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書'),
            os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書1'),
            os.path.join(self.customer[0]['フォルダパス'], '三菱UFJ_残高証明書依頼書2')
        )

    ### 相続届
    def inheritance_notification(self):
        create_date = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'))
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('銀行の手続き'),
            content=ft.Column(
                [
                    create_date,
                    ft.VerticalDivider(),
                ],
                height=80,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True,
                                       on_click=lambda e: self.inheritance_notification_create(create_date.value)),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def inheritance_notification_create(self, e):
        self.close_dlg(self)
        # dt = re.findall('[0-9]+', convert_to_wareki2(e))
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
                AND t2.jba_code = "0005"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "0005"
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '〇〇'),
                     os.path.dirname(__file__) + "/pdf/〇〇.pdf", page=1, open_bool=True)


def main(page: ft.Page):
    GlobalValues.code = "E00287"
    # page.scrollTo = "always"
    # page.scroll = 'AUTO'
    # page.window_width = 1930
    # page.window_height = 1080 - 50
    # page.window_center()
    # page.window_minimizable = True
    # page.window_maximizable = True
    # page.window_resizable = True
    # GlobalValues.my_page = page
    # cl = Mufg()
    # page.add(cl)
    # cl.balance_certificate()


if __name__ == '__main__':
    # ft.app(target=main)
    GlobalValues.code = "E00328"
    cl = PaypayBank()
    cl.account_freezing()
    # cl.balance_certificate()
    # cl.inheritance_notification()

    # pdf = PdfCreate()
    # pdf.pdf_marge(
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf',
    #                  'きらぼし銀行_相続手続依頼書'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf',
    #                  'きらぼし銀行_相続手続依頼書1'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf',
    #                  'きらぼし銀行_相続手続依頼書2'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf',
    #                  'きらぼし銀行_相続手続依頼書3'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf',
    #                  'きらぼし銀行_相続手続依頼書4'),
    # )