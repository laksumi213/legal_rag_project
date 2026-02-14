### 埼玉りそな銀行
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from zengin import BankSearch
# from convert_to_wareki import convert_to_wareki2
from datetime import datetime
# import jaconv
import re
import os.path


class SaitamaResonaBank(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.heir = None
        self.customer = None
        self.page = GlobalValues.my_page

    def build(self):
        pass

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    ### 口座凍結
    @classmethod
    def account_freezing(cls):
        pass
        # account_freezing_create()

    def account_freezing_create(self, _):
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
                 maiden_name AS 旧姓,
                 maiden_name_huri AS 旧姓_ふりがな
            FROM customer 
            WHERE code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', dt_now)

        pdf = PdfCreate("A4")
        pdf.draw_string(61, 168, '✓', 8)
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], '埼玉りそな銀行_残高証明書依頼書'),
                     os.path.dirname(__file__) + "/pdf/埼玉りそな銀行_残高証明書依頼書.pdf", page=1, open_bool=True)

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
        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.maiden_name || "  " || t1.username2 AS 被相続人_旧姓,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0017"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "0017"
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

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
                AND jba_code = "0017"
            )
        ''')
        self.heir = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        banks = [(bank_name, bank_code) for bank_name, bank_code in
                 BankSearch.bank_search(code=str(self.heir['銀行コード']).zfill(4))][0]
        print('banks:', banks)

        branches = [(branch_code, branch_name) for branch_code, branch_name in
                    BankSearch.branch_search(bank_code=str(self.heir['銀行コード']).zfill(4),
                                             code=str(self.heir['支店コード']).zfill(3))][0]
        print('branches:', branches)

        pdf = PdfCreate("A4")
        dt = re.findall('[0-9]+', e)
        pdf.draw_string(58, 256.5, str(dt[0]).zfill(4))
        pdf.draw_string(75, 256.5, str(dt[1]).zfill(2))
        pdf.draw_string(88, 256.5, str(dt[2]).zfill(2))

        pdf.draw_string(25, 252, '194-0022')
        pdf.draw_string(69, 252.5, '042', 8)
        pdf.draw_string(78, 252.5, '710', 8)
        pdf.draw_string(89, 252.5, '6178', 8)

        pdf.draw_string(30, 243, '東京都町田市森野一丁目22番5号', 12)
        pdf.draw_string(30, 238, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 6)
        pdf.draw_string(30, 228.5, '相続手続支援センター町田有限責任事業組合　組合員', 8)
        pdf.draw_string(30, 224.5, '株式会社プロフィット・ワン　職務執行者　大貫利一', 8)

        pdf.draw_string(30, 210, self.customer[0]['被相続人'], 12)

        pdf.draw_string(17, 191.2, '〇', 12)
        pdf.draw_string(43, 185.5, self.heir['相続人'])

        pdf.draw_string(22, 165, '〇', 16)
        deathday = re.findall(r'\d+', self.customer[0]['死亡日'])
        pdf.draw_string(45, 166, deathday[0])
        pdf.draw_string(65, 166, deathday[1])
        pdf.draw_string(83, 166, deathday[2])

        pdf.draw_string(36, 145.5, 1, 20)
        for deposit_type in self.customer:
            print(deposit_type['種類'])
            if '定期' in deposit_type['種類']:
                pdf.draw_string(58, 142, '✓', 12)
                break

        pdf.draw_string(53, 76.5, '✓', 12)

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', '埼玉りそな銀行_残高証明書依頼書'),
                     os.path.dirname(__file__) + "/pdf/埼玉りそな銀行_残高証明書依頼書.pdf", page=1, open_bool=True)

        # 旧姓がある場合
        if self.customer[0]['被相続人_旧姓'] != '':
            pdf = PdfCreate("A4")
            dt = re.findall('[0-9]+', e)
            pdf.draw_string(58, 256.5, str(dt[0]).zfill(4))
            pdf.draw_string(75, 256.5, str(dt[1]).zfill(2))
            pdf.draw_string(88, 256.5, str(dt[2]).zfill(2))

            pdf.draw_string(25, 252, '194-0022')
            pdf.draw_string(69, 252.5, '042', 8)
            pdf.draw_string(78, 252.5, '710', 8)
            pdf.draw_string(89, 252.5, '6178', 8)

            pdf.draw_string(30, 243, '東京都町田市森野一丁目22番5号', 12)
            pdf.draw_string(30, 238,
                            'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ',
                            6)
            pdf.draw_string(30, 228.5, '相続手続支援センター町田有限責任事業組合　組合員', 8)
            pdf.draw_string(30, 224.5, '株式会社プロフィット・ワン　職務執行者　大貫利一', 8)

            pdf.draw_string(30, 210, self.customer[0]['被相続人_旧姓'], 12)

            pdf.draw_string(17, 191.2, '〇', 12)
            pdf.draw_string(43, 185.5, self.heir['相続人'])

            pdf.draw_string(22, 165, '〇', 16)
            deathday = re.findall(r'\d+', self.customer[0]['死亡日'])
            pdf.draw_string(45, 166, deathday[0])
            pdf.draw_string(65, 166, deathday[1])
            pdf.draw_string(83, 166, deathday[2])

            pdf.draw_string(36, 145.5, 1, 20)
            for deposit_type in self.customer:
                print(deposit_type['種類'])
                if '定期' in deposit_type['種類']:
                    pdf.draw_string(58, 142, '✓', 12)
                    break

            pdf.draw_string(53, 76.5, '✓', 12)

            pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',
                                      '埼玉りそな銀行_残高証明書依頼書_旧姓'),
                         os.path.dirname(__file__) + "/pdf/埼玉りそな銀行_残高証明書依頼書.pdf", page=1, open_bool=True)


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
                     "./pdf/〇〇.pdf", page=1, open_bool=True)


def main(page: ft.Page):
    GlobalValues.code = "E00316"
    # page.scrollTo = "always"
    # page.scroll = 'AUTO'
    # page.window_width = 1930
    # page.window_height = 1080 - 50
    # page.window_center()
    # page.window_minimizable = True
    # page.window_maximizable = True
    # page.window_resizable = True
    # GlobalValues.my_page = page
    cl = SaitamaResonaBank()
    page.add(cl)
    cl.balance_certificate()


if __name__ == '__main__':
    ft.app(target=main)
    # GlobalValues.code = "E00316"
    # cl = SaitamaResonaBank()
    # cl.balance_certificate()
    # cl.inheritance_notification()
