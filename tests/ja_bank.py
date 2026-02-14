### JA
### 協議書がないと、相続人それぞれの自署・捺印が必要な点に注意！！
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from zengin import BankSearch
# from convert_to_wareki import convert_to_wareki2
from datetime import datetime
import jaconv
import re
import os.path


class JaBank(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.customer = None
        self.page = GlobalValues.my_page

    def build(self):
        pass

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

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
        try:
            self.close_dlg(self)
        except:
            pass
        # dt = re.findall('[0-9]+', convert_to_wareki2(e))
        # pdf = PdfCreate("A3")
        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || t1.building AS 住所,
                t1.deathday AS 死亡日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "5060"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "5060"
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        sql = ('''
            SELECT
                t1.username1 || " " || t1.username2 AS 相続人,
                t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || t1.building AS 住所,
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
        self.heir_offer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        pdf = PdfCreate("A4")

        pdf.draw_string(110, 222, self.customer['住所'], 8)
        pdf.draw_string(110, 210, self.customer['被相続人'], 12)

        pdf.draw_string(110, 199, self.heir_offer['住所'], 8)
        pdf.draw_string(110, 187, self.heir_offer['相続人'], 12)

        pdf.draw_string(91, 164, '✓', 12)

        pdf.draw_string(58, 141, self.customer['被相続人'], 12)

        death_day = re.findall(r'\d+', self.customer['死亡日'])
        pdf.draw_string(39, 135, death_day[0])
        pdf.draw_string(61, 135, death_day[1])
        pdf.draw_string(78, 135, death_day[2])

        pdf.draw_string(36, 124, '✓', 12)
        pdf.draw_string(36, 118, '✓', 12)
        pdf.draw_string(36, 112, '✓', 12)

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書', 'JA_相続税申告等のための取引状況証明依頼書(残高証明書)'),
                     os.path.dirname(__file__) + "/pdf/JA_相続税申告等のための取引状況証明依頼書(残高証明書).pdf", page=1, open_bool=True)

    ### 相続届
    # def inheritance_notification(self):
    #     create_date = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'))
    #     self.page.dialog = ft.AlertDialog(
    #         open=True,
    #         modal=True,
    #         title=ft.Text('銀行の手続き'),
    #         content=ft.Column(
    #             [
    #                 create_date,
    #                 ft.VerticalDivider(),
    #             ],
    #             height=80,
    #         ),
    #         actions=[ft.ElevatedButton(text="OK", autofocus=True,
    #                                    on_click=lambda e: self.inheritance_notification_create(create_date.value)),
    #                  ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
    #         actions_alignment=ft.MainAxisAlignment.END,
    #     )
    #     self.page.update()

    # def inheritance_notification_create(self, e):
    def inheritance_notification(self):
        # self.close_dlg(self)
        # dt = re.findall('[0-9]+', convert_to_wareki2(e))
        # dt = re.findall('[0-9]+', e)
        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || t1.building AS 被相続人_住所,
                t1.deathday AS 死亡日,
                t1.birthday AS 生年月日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "5060"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "5060"
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        sql = ('''
            SELECT
                username1_hurigana || "  " || username2_hurigana AS 相続人_かな,
                username1 || "  " || username2 AS 相続人,
                prefectures || municipalities || townarea || house_number || building AS 相続人_住所
            FROM heir
            WHERE code = ?
            AND (situation = " " or situation = "")
        ''')
        heir_s = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
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
                AND jba_code = "5060"
            )
        ''')
        heir_offer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        ### 記入用紙
        # 町田様式の場合、位置修正
        x = 2
        y = -3.7

        pdf = PdfCreate("A3", 'portrait')
        if self.customer[0]['支店名'] == '忠生':
            pdf.draw_string(x + 35, y + 182, "町田市", 10)

        pdf.draw_string(x + 100, y + 180, self.customer[0]['被相続人_住所'], 8)
        pdf.draw_string(x + 100, y + 175, self.customer[0]['被相続人'], 10)
        # pdf.draw_string(x + 100, y + 175, '浅野　幸雄', 10)
        pdf.draw_string(x + 114, y + 170, str(re.findall(r'\d+', self.customer[0]['死亡日'])[0]).zfill(4), 8)
        pdf.draw_string(x + 125, y + 170, str(re.findall(r'\d+', self.customer[0]['死亡日'])[1]).zfill(2), 8)
        pdf.draw_string(x + 133, y + 170, str(re.findall(r'\d+', self.customer[0]['死亡日'])[2]).zfill(2), 8)

        # pdf.draw_string(x + 96, y + 96, heir_offer['相続人'], 10)
        pdf.draw_string(x + 93, y + 99, '相続手続支援センター町田有限責任事業組合　組合員', 4.5)
        pdf.draw_string(x + 93, y + 96, '株式会社プロフィット・ワン　職務執行者　大貫利一', 4.5)
        pdf.draw_string(x + 29, y + 49, '〇', 15)

        for i, customer in enumerate(self.customer):
            pdf.draw_string(x + 160, y + 175 - i * 6.7, f"{customer['支店名']}支店", 8)
            if '普通' in customer['種類']:
                pdf.draw_string(x + 178, y + 175 - i * 6.7, "普通貯金", 8)
            pdf.draw_string(x + 195, y + 175 - i * 6.7, str(customer['口座番号']).zfill(7), 8)
            pdf.draw_string(x + 213, y + 175 - i * 6.7, heir_offer['相続人'], 8)
            pdf.draw_string(x + 236, y + 175 - i * 6.7, '〇')
            pdf.draw_string(x + 258, y + 175 - i * 6.7, '全額')

        banks = [(bank_name, bank_code) for bank_name, bank_code in
                    BankSearch.bank_search(code=str(heir_offer['銀行コード']).zfill(4))][0]
        print('banks:', banks)
        pdf.draw_string(x + 180, y + 111, banks[0])

        if banks[1] != '9900':
            branches = [(branch_code, branch_name) for branch_code, branch_name in
                        BankSearch.branch_search(bank_code=str(heir_offer['銀行コード']).zfill(4),
                                             code=str(heir_offer['支店コード']).zfill(3))][0]
        else:
            branches = BankSearch.branch_search(bank_code=str(heir_offer['銀行コード']).zfill(4),
                                                code=f"{str(heir_offer['支店コード']).zfill(5)}-{str(heir_offer['口座番号']).zfill(7)}")
        print('branches:', branches)
        pdf.draw_string(x + 243, y + 111, branches[1])

        if '普通' in heir_offer['種類']:
            pdf.draw_string(x + 178.5, y + 104.5, '〇', 12)
        elif '当座' in heir_offer['種類']:
            pdf.draw_string(x + 185, y + 104.5, '〇', 12)
        elif '定期' in heir_offer['種類']:
            pdf.draw_string(x + 200, y,  104.5, '〇', 12)
        else:
            pdf.draw_string(x + 193.7, y + 104.5, '〇', 12)

        pdf.draw_string(x + 230, y + 104, heir_offer['相続人'], 8)
        # pdf.draw_string(x + 230, y + 104, '浅野　道', 8)
        pdf.draw_string(x + 230, y + 107, jaconv.hira2kata(heir_offer['相続人_ふりがな']), 6)
        pdf.draw_string(x + 180, y + 98, str(heir_offer['口座番号']).zfill(7))
        pdf.draw_string(x + 230, y + 98, '全額')

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'JA_相続手続依頼書'),
                     os.path.dirname(__file__) + "/pdf/JA_相続手続依頼書_町田.pdf", page=1, open_bool=True)


        # ### 記入例
        # pdf = PdfCreate("A3", 'portrait')
        # pdf.draw_string(65, 200, '＜記入例＞', 20, '#FF0000')
        #
        # # 日付は空欄
        # pdf.draw_string(126, 190, '空欄', 12, '#FF0000')
        # # pdf.draw_string(120, 187, str(dt[0]).zfill(4), 8)
        # # pdf.draw_string(131, 187, str(dt[1]).zfill(2), 8)
        # # pdf.draw_string(138, 187, str(dt[2]).zfill(2), 8)
        #
        # i = 0
        # x = 0
        # for heir in heir_s:
        #     pdf.draw_string(34 + x, 166 - i * 15.6, '〇', 10, '#FF0000')
        #     pdf.draw_string(42 + x, 161 - i * 15.6, heir['相続人_住所'], 6, '#FF0000')
        #     pdf.draw_string(42 + x, 156 - i * 15.6, heir['相続人'], 8, '#FF0000')
        #     pdf.draw_string(78 + x, 151 - i * 15.6, '〇', 30, '#FF0000')
        #     if i == 4:
        #         i = 0
        #         x = 57
        #     else:
        #         i += 1

        # pdf.draw_string(36, 164, "代理人", 6)
        # pdf.draw_string(42, 161, "東京都町田市森野一丁目22番5号", 6)
        # pdf.draw_string(42, 156, "相続手続支援センター町田有限責任事業組合　組合員", 6)
        # pdf.draw_string(42, 151, "株式会社プロフィット・ワン　職務執行者　大貫利一", 6)

        # pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'JA_相続手続依頼書（記入例）'),
        #              "./pdf/JA_相続手続依頼書.pdf", page=1, open_bool=True)

        ### 死亡届
        pdf = PdfCreate("A4")
        if self.customer[0]['支店名'] == '忠生':
            pdf.draw_string(30, 252, "町田市", 10)
        pdf.draw_string(114, 243, self.customer[0]['被相続人_住所'], 8)
        pdf.draw_string(114, 232, self.customer[0]['被相続人'], 10)
        # pdf.draw_string(114, 232, '浅野　幸雄', 10)
        pdf.draw_string(114, 220, self.customer[0]['生年月日'])
        pdf.draw_string(114, 204, '東京都町田市森野一丁目22番5号')
        pdf.draw_string(114, 197, '相続手続支援センター町田有限責任事業組合　組合員', 7)
        pdf.draw_string(114, 193, '株式会社プロフィット・ワン　職務執行者　大貫利一', 7)
        pdf.draw_string(125, 182, '042-710-6178')
        pdf.draw_string(86, 186.5, '代理人')
        pdf.draw_string(66, 160, str(re.findall(r'\d+', self.customer[0]['死亡日'])[0]).zfill(4))
        pdf.draw_string(89, 160, str(re.findall(r'\d+', self.customer[0]['死亡日'])[1]).zfill(2))
        pdf.draw_string(104, 160, str(re.findall(r'\d+', self.customer[0]['死亡日'])[2]).zfill(2))
        pdf.pdf_save(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'JA_死亡届'),
            "./pdf/JA_死亡届.pdf", page=1, open_bool=True)


def main(page: ft.Page):
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = JaBank()
    page.add(cl)
    # cl.inheritance_notification()
    # cl.balance_certificate()
    cl.balance_certificate_create(cl)


if __name__ == '__main__':
    GlobalValues.code = "2409008"
    ft.app(target=main)

    # cl = JaBank()
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