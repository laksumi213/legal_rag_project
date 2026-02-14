### 野村證券
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from convert_to_wareki import convert_to_wareki2
from datetime import datetime
import jaconv
import re
import os.path


class Nomura(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.bank_number_heir = None
        self.trading_shop_code_heir = None
        self.trading_shop_name_heir = None
        self.trading_shop_name = None
        self.bank_number = None
        self.trading_shop_code = None
        self.customer = None
        self.page = GlobalValues.my_page

    def build(self):
        pass

    def close_dlg(self, _):
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

        pdf = PdfCreate("A4")
        pdf.draw_string(61, 168, '✓', 8)
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表5'),
                     "./pdf/ゆうちょ_相続確認表.pdf", page=8, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表1'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表2'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表3')
        )

    # 残高証明書
    def balance_certificate(self):
        self.trading_shop_name = ft.TextField(label='取引店名', autofocus=True)
        self.trading_shop_code = ft.TextField(label='取引店コード', hint_text='3桁の数字')
        self.bank_number = ft.TextField(label='口座番号', hint_text='7桁の数字')
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('残高証明書の申請'),
            content=ft.Column(
                [
                    self.trading_shop_name,
                    self.trading_shop_code,
                    self.bank_number
                ],
                height=200,
            ),
            actions=[ft.ElevatedButton("OK", on_click=self.balance_certificate_create),
                     ft.ElevatedButton("キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        ### test
        # self.trading_shop_name.value = '池袋'
        # self.trading_shop_code.value = '960'
        # self.bank_number.value = '1911058'
        ### test
        self.page.update()

    def balance_certificate_create(self, _):
        self.close_dlg(self)
        dt_now = datetime.now().strftime('%Y/%m/%d')
        pdf = PdfCreate("A4")
        sql = ('''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.deathday AS 死亡日,
                t1.birthday AS 生年月日,
                t2.branch_code AS 店番号,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名,
                t2.branch_code AS 支店コード
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "0005"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "0005"
            WHERE t1.code = ?
        ''')

        try:
            self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        except Exception as e:
            print(e)
        # if self.customer == []:
            sql = (f'''
               SELECT
                   t1.folder_s_path AS フォルダパス,
                   t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                   t1.username1 || "  " || t1.username2 AS 被相続人,
                   t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || t1.building AS 被相続人住所,
                   t1.deathday AS 死亡日,
                   t1.birthday AS 生年月日,
                   (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
                   t4.username1 || "  " || t4.username2 AS 相続人,
                   t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな
               FROM customer AS t1
                   INNER JOIN heir AS t4
                   ON t4.code = t1.code
                   AND t4.code = "{GlobalValues.code}"
               WHERE t1.code = "{GlobalValues.code}"
            ''')
            self.customer = GlobalValues.get_db(sql, row_factory=True)[0]
            print('self.customer:', GlobalValues.get_db(sql, row_factory=False)[0])

        pdf.draw_string(147, 220, dt_now[0:4])
        pdf.draw_string(170, 220, dt_now[5:7])
        pdf.draw_string(183, 220, dt_now[8:])

        pdf.draw_string(62, 204, self.customer['被相続人'], 12)
        pdf.draw_string(62, 214, jaconv.hira2hkata(self.customer['被相続人_かな']), 12)

        birthday = re.findall('[0-9]+', self.customer['生年月日'])
        ad = convert_to_wareki2(self.customer['生年月日'])[0:2]
        if ad == '大正':
            pdf.draw_string(47, 195, '✓', 8)
        elif ad == '昭和':
            pdf.draw_string(47, 189.5, '✓', 8)
        elif ad == '平成':
            pdf.draw_string(59.5, 195, '✓', 8)
        elif ad == '令和':
            pdf.draw_string(59.5, 189.5, '✓', 8)

        pdf.draw_string(74, 192, re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[0], 8)
        pdf.draw_string(85, 192, birthday[1], 8)
        pdf.draw_string(97, 192, birthday[2], 8)

        deathday = re.findall('[0-9]+', self.customer['死亡日'])
        pdf.draw_string(150, 192, deathday[0], 8)
        pdf.draw_string(168, 192, deathday[1], 8)
        pdf.draw_string(182, 192, deathday[2], 8)

        # if '支店' in self.customer['支店名']:
        #     pdf.draw_string(62, 172, self.customer['支店名'].replace('支店', ''), 12)
        #     pdf.draw_string(101.5, 169.5, '〇', 12)

        if self.trading_shop_name.value:
            pdf.draw_string(62, 172, self.trading_shop_name.value.replace('支店', ''), 12)
            pdf.draw_string(113, 172, str(self.trading_shop_code.value)[0], 12)
            pdf.draw_string(120, 172, str(self.trading_shop_code.value)[1], 12)
            pdf.draw_string(129, 172, str(self.trading_shop_code.value)[2], 12)

        if self.bank_number.value:
            pdf.draw_string(137, 172, str(self.bank_number.value)[0], 12)
            pdf.draw_string(146, 172, str(self.bank_number.value)[1], 12)
            pdf.draw_string(155, 172, str(self.bank_number.value)[2], 12)
            pdf.draw_string(163, 172, str(self.bank_number.value)[3], 12)
            pdf.draw_string(171, 172, str(self.bank_number.value)[4], 12)
            pdf.draw_string(179, 172, str(self.bank_number.value)[5], 12)
            pdf.draw_string(188, 172, str(self.bank_number.value)[6], 12)

        pdf.draw_string(60, 85, '194', 8)
        pdf.draw_string(76, 85, '0022', 8)
        pdf.draw_string(60, 80, '東京都町田市森野一丁目22番5号　町田310五十子ビル3階')
        pdf.draw_string(57, 67, '相続手続支援センター町田有限責任事業組合組合員', 6)
        pdf.draw_string(57, 64, '株式会社プロフィット・ワン　職務執行者　大貫利一', 6)
        pdf.draw_string(67, 74, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲｸﾐｱｲｲﾝ', 5)
        pdf.draw_string(67, 71.5, 'ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 5)
        pdf.draw_string(149, 69, '042')
        pdf.draw_string(167, 69, '710')
        pdf.draw_string(183, 69, '6178')

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], "金融機関手続", "残高証明書", "申請書", '野村證券_残高証明書作成依頼書'),
                     os.path.dirname(__file__) + r"/pdf/野村證券_残高証明書作成依頼書.pdf", page=1, open_bool=True)

        # 野村證券_残高証明書_原本返却依頼書
        pdf = PdfCreate("A4")
        pdf.draw_string(121, 206, dt_now[0:4])
        pdf.draw_string(140, 206, dt_now[5:7])
        pdf.draw_string(155, 206, dt_now[8:])
        pdf.draw_string(131, 194, self.customer['被相続人'])
        pdf.draw_string(74, 181, '194')
        pdf.draw_string(95, 181, '0022')
        pdf.draw_string(81, 165, '東京都町田市森野一丁目22番5号')
        pdf.draw_string(81, 154, '町田310五十子ビル3階')

        pdf.draw_string(81, 138, '相続手続支援センター町田　担当：堀池')
        pdf.draw_string(96, 116, '080-4800-3208')

        # pdf.draw_string(81, 138, '相続手続支援センター町田　担当：森町')
        # pdf.draw_string(96, 116, '042-710-6178')

        # pdf.draw_string(81, 144, '相続手続支援センター町田有限責任事業組合組合員',8)
        # pdf.draw_string(81, 138, '株式会社プロフィット・ワン　職務執行者　大貫利一',8)
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], "金融機関手続", "残高証明書",
                                  "申請書", '野村證券_残高証明書_原本返却依頼書'),
                     os.path.dirname(__file__) + r"/pdf/野村證券_残高証明書_原本返却依頼書.pdf", page=1, open_bool=True)

        # 野村證券_残証申請_封筒宛名ラベル
        pdf = PdfCreate("A4")
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], "金融機関手続", "残高証明書",
                                  "申請書", '野村證券_残証申請_封筒宛名ラベル'),
                     os.path.dirname(__file__) + r"/pdf/野村證券_残証申請_封筒宛名ラベル.pdf", page=1, open_bool=True)

        # pdf.pdf_marge(
        #     os.path.join(self.customer['被相続人']['フォルダパス'], '三菱UFJ_残高証明書依頼書'),
        #     os.path.join(self.customer['被相続人']['フォルダパス'], '三菱UFJ_残高証明書依頼書1'),
        #     os.path.join(self.customer['被相続人']['フォルダパス'], '三菱UFJ_残高証明書依頼書2')
        # )

    ### 相続届
    def inheritance_notification(self):
        self.trading_shop_name = ft.TextField(label='被相続人　取引店名', autofocus=True)
        self.trading_shop_code = ft.TextField(label='被相続人　取引店コード', hint_text='3桁の数字')
        self.bank_number = ft.TextField(label='被相続人　口座番号', hint_text='7桁の数字')

        self.trading_shop_name_heir = ft.TextField(label='相続人　取引店名', autofocus=True)
        self.trading_shop_code_heir = ft.TextField(label='相続人　取引店コード', hint_text='3桁の数字')
        self.bank_number_heir = ft.TextField(label='相続人　口座番号', hint_text='7桁の数字')

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('野村證券　解約届'),
            content=ft.Column(
                [
                    self.trading_shop_name,
                    self.trading_shop_code,
                    self.bank_number,
                    ft.VerticalDivider(),
                    ft.VerticalDivider(),
                    self.trading_shop_name_heir,
                    self.trading_shop_code_heir,
                    self.bank_number_heir
                ],
                height=500,
            ),
            actions=[ft.ElevatedButton("OK", on_click=self.inheritance_notification_create),
                     ft.ElevatedButton("キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        ### 被相続人口座情報 ###
        self.trading_shop_name.value = '町田'
        self.trading_shop_code.value = '208'
        self.bank_number.value = '2425327'

        ## 相続人口座情報 ###
        self.trading_shop_name_heir.value = ''
        self.trading_shop_code_heir.value = ''
        self.bank_number_heir.value = ''

        self.page.update()

    def inheritance_notification_create(self, _):
        self.close_dlg(self)

        dt_now = re.findall(r'\d+', datetime.now().strftime('%Y/%m/%d'))
        sql = ('''
            SELECT
                folder_s_path AS フォルダパス,
                username1_hurigana || "  " || username2_hurigana AS 氏名ふりがな,
                username1 || "  " || username2 AS 氏名,
                deathday AS 死亡日,
                birthday AS 生年月日,
                prefectures || municipalities || townarea || house_number || building AS 住所
            FROM customer
            WHERE code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        pdf = PdfCreate("A3", 'landscape')
        pdf.draw_string(30, 168.5, dt_now[0])
        pdf.draw_string(46, 168.5, dt_now[1])
        pdf.draw_string(56, 168.5, dt_now[2])
        pdf.draw_string(20, 162, self.customer['住所'])
        pdf.draw_string(27, 154.5, jaconv.hira2kata(self.customer['氏名ふりがな']), 7)
        pdf.draw_string(27, 149, self.customer['氏名'])
        deathday = re.findall(r'\d+', self.customer['死亡日'])
        pdf.draw_string(30, 142, deathday[0])
        pdf.draw_string(46, 142, deathday[1])
        pdf.draw_string(56, 142, deathday[2])
        birthday = re.findall(r'\d+', convert_to_wareki2(self.customer['生年月日']))
        if convert_to_wareki2(self.customer['生年月日'])[:2] == '大正':
            pdf.draw_string(79, 154.5, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '平成':
            pdf.draw_string(90, 154.5, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '昭和':
            pdf.draw_string(79, 151, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '令和':
            pdf.draw_string(90, 151, '✓', 8)
        pdf.draw_string(106, 153, birthday[0])
        pdf.draw_string(118, 153, birthday[1])
        pdf.draw_string(130, 153, birthday[2])
        pdf.draw_string(68, 142, str(self.trading_shop_name.value).replace('支店', ''), 6)
        pdf.draw_string(96, 142, str(self.trading_shop_code.value).zfill(3)[0])
        pdf.draw_string(100.5, 142, str(self.trading_shop_code.value).zfill(3)[1])
        pdf.draw_string(105, 142, str(self.trading_shop_code.value).zfill(3)[2])
        pdf.draw_string(110, 142, str(self.bank_number.value).zfill(7)[0])
        pdf.draw_string(114.5, 142, str(self.bank_number.value).zfill(7)[1])
        pdf.draw_string(119, 142, str(self.bank_number.value).zfill(7)[2])
        # pdf.draw_string(71, 142, str(self.trading_shop_name).replace('支店', ''))
        pdf.draw_string(96, 142, str(self.trading_shop_code.value).zfill(3)[0])
        pdf.draw_string(100.5, 142, str(self.trading_shop_code.value).zfill(3)[1])
        pdf.draw_string(105, 142, str(self.trading_shop_code.value).zfill(3)[2])
        pdf.draw_string(110, 142, str(self.bank_number.value).zfill(7)[0])
        pdf.draw_string(114.5, 142, str(self.bank_number.value).zfill(7)[1])
        pdf.draw_string(119, 142, str(self.bank_number.value).zfill(7)[2])
        pdf.draw_string(123.5, 142, str(self.bank_number.value).zfill(7)[3])
        pdf.draw_string(128, 142, str(self.bank_number.value).zfill(7)[4])
        pdf.draw_string(132.5, 142, str(self.bank_number.value).zfill(7)[5])
        pdf.draw_string(137, 142, str(self.bank_number.value).zfill(7)[6])
        pdf.draw_string(8, 126, f'故　{self.customer["氏名"]}　相続手続き代理人', 6)
        pdf.draw_string(8, 123, '相続手続支援センター町田有限責任事業組合', 6)
        pdf.draw_string(8, 120, '組合員　株式会社プロフィット・ワン', 6)
        pdf.draw_string(8, 117, '職務執行者　大貫利一', 6)
        pdf.draw_string(63.5, 113.5, '✓', 9)
        pdf.draw_string(11.5, 50, '✓', 10)
        # 受取人
        sql = ('''
            SELECT
                username1_hurigana || "  " || username2_hurigana AS 氏名ふりがな,
                username1 || "  " || username2 AS 氏名,
                birthday AS 生年月日,
                prefectures || municipalities || townarea || house_number AS 住所,
                building AS 建物名
            FROM heir
            WHERE code = ?
            AND offer = 1
        ''')
        self.heir = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])
        pdf.draw_string(169, 190, self.heir['住所'], 9)
        pdf.draw_string(169, 185, self.heir['建物名'], 9)
        pdf.draw_string(178, 180, jaconv.hira2kata(self.heir['氏名ふりがな']), 7)
        pdf.draw_string(178, 175, self.heir['氏名'])
        pdf.draw_string(213, 175, self.trading_shop_name_heir.value, 6)
        birthday_heir = re.findall(r'\d+', convert_to_wareki2(self.heir['生年月日']))
        if convert_to_wareki2(self.heir['生年月日'])[:2] == '大正':
            pdf.draw_string(239, 187, '✓', 8)
        elif convert_to_wareki2(self.heir['生年月日'])[:2] == '平成':
            pdf.draw_string(250, 187, '✓', 8)
        elif convert_to_wareki2(self.heir['生年月日'])[:2] == '昭和':
            pdf.draw_string(239, 184, '✓', 8)
        elif convert_to_wareki2(self.heir['生年月日'])[:2] == '令和':
            pdf.draw_string(250, 184, '✓', 8)
        pdf.draw_string(262, 185, birthday_heir[0])
        pdf.draw_string(271.5, 185, birthday_heir[1])
        pdf.draw_string(281.5, 185, birthday_heir[2])
        pdf.draw_string(239, 174, str(self.trading_shop_code_heir.value).zfill(3)[0])
        pdf.draw_string(243.5, 174, str(self.trading_shop_code_heir.value).zfill(3)[1])
        pdf.draw_string(247.5, 174, str(self.trading_shop_code_heir.value).zfill(3)[2])
        pdf.draw_string(252, 174, str(self.bank_number_heir.value).zfill(7)[0])
        pdf.draw_string(256, 174, str(self.bank_number_heir.value).zfill(7)[1])
        pdf.draw_string(260.5, 174, str(self.bank_number_heir.value).zfill(7)[2])
        pdf.draw_string(264.5, 174, str(self.bank_number_heir.value).zfill(7)[3])
        pdf.draw_string(269, 174, str(self.bank_number_heir.value).zfill(7)[4])
        pdf.draw_string(273.5, 174, str(self.bank_number_heir.value).zfill(7)[5])
        pdf.draw_string(277.5, 174, str(self.bank_number_heir.value).zfill(7)[6])
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], '野村證券_解約届1'),
                     os.path.dirname(__file__) + r"/pdf/野村證券_解約届.pdf", page=1, open_bool=False)

        pdf = PdfCreate("A3", 'landscape')
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], '野村證券_解約届2'),
                     os.path.dirname(__file__) + r"/pdf/野村證券_解約届.pdf", page=2, open_bool=False)

        os.makedirs(os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書'), exist_ok=True)
        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書', '野村證券_解約届'),
            os.path.join(self.customer['フォルダパス'], '野村證券_解約届1'),
            os.path.join(self.customer['フォルダパス'], '野村證券_解約届2')
        )


def main(page: ft.Page):
    GlobalValues.code = "2411005"
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = Nomura()
    page.add(cl)
    cl.balance_certificate()
    # cl.inheritance_notification()


if __name__ == '__main__':
    ft.app(target=main)
    # GlobalValues.code = "2409001"
    # cl = Nomura()
    # cl.inheritance_notification_create()
