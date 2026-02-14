### ゆうちょ銀行

import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from convert_to_wareki import convert_to_wareki2
# from datetime import datetime
import jaconv
import re
import os.path
from pathlib import Path
# from zengin import BankSearch


class JpBank(ft.UserControl):
    @property
    def previous_body(self):
        return self._previous_body

    @previous_body.setter
    def previous_body(self, value):
        self._previous_body = value

    def __init__(self):
        super().__init__()
        self.residence_country1 = None
        self.residence_country2 = None
        self.residence_country3 = None
        self.residence_country4 = None
        self.residence_country5 = None
        self.residence_country6 = None
        self.img1 = None
        self.img2 = None
        self.img3 = None
        self.customer = None
        self.page = GlobalValues.my_page

    def build(self):
        pass

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()
        # [GlobalValues.body.controls.pop() for _ in range(len(GlobalValues.body.controls))]
        # GlobalValues.body.controls.append(self._previous_body)
        # GlobalValues.body.update()

    # ゆうちょ_貯金等照会書
    def account_freezing_normal(self):
        sql = ('''
            SELECT
                 folder_s_path AS フォルダパス,
                 zipcode AS 被相続人_郵便番号,
                 prefectures AS 被相続人_都道府県,
                 municipalities AS 被相続人_市区町村,
                 townarea || house_number || building AS 被相続人_住所,
                 old_address1 AS 旧住所1,
                 old_address2 AS 旧住所2,
                 old_address3 AS 旧住所3,
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
                 townarea AS 被相続人_都道府県
            FROM customer 
            WHERE code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]), False)[0])

        pdf = PdfCreate("A4")

        # 1 ご請求者
        pdf.draw_string(55.5, 240, 1, 12)
        pdf.draw_string(63, 240, 9, 12)
        pdf.draw_string(70, 240, 4, 12)
        pdf.draw_string(84, 240, 0, 12)
        pdf.draw_string(91, 240, 0, 12)
        pdf.draw_string(98, 240, 2, 12)
        pdf.draw_string(105, 240, 2, 12)
        pdf.draw_string(115, 240, '東京', 12)
        pdf.draw_string(131, 243.5, '✓', 12)
        pdf.draw_string(157, 240, '町田', 12)
        pdf.draw_string(175.5, 243.5, '✓', 12)
        pdf.draw_string(50, 226, '森野一丁目22番5号', 12)
        pdf.draw_string(50, 215, 'ソウゾクテツヅキシエンセンターマチダユウゲンセキニンジギョウクミアイ', 8)
        pdf.draw_string(50, 201, '相続手続支援センター町田有限責任事業組合', 12)
        pdf.draw_string(48.5, 188, 0, 12)
        pdf.draw_string(48.5 + 7, 188, 4, 12)
        pdf.draw_string(48.5 + 14, 188, 2, 12)
        pdf.draw_string(84, 188, 7, 12)
        pdf.draw_string(84 + 7, 188, 1, 12)
        pdf.draw_string(84 + 14, 188, 0, 12)
        pdf.draw_string(118.5, 188, 6, 12)
        pdf.draw_string(118.5 + 7, 188, 1, 12)
        pdf.draw_string(118.5 + 14, 188, 7, 12)
        pdf.draw_string(118.5 + 21, 188, 8, 12)
        pdf.draw_string(49, 172, '✓', 12)
        pdf.draw_string(72, 172, '相続人代理人', 12)
        pdf.draw_string(174, 178, '✓', 12)

        # 2 調査対象者
        pdf.draw_string(49, 143, f"{jaconv.hira2kata(self.customer['被相続人_かな1'])} {jaconv.hira2kata(self.customer['被相続人_かな2'])}")
        pdf.draw_string(49, 133, f"{self.customer['被相続人1']}  {self.customer['被相続人2']}", 12)
        pdf.draw_string(146, 143,
                        f"{jaconv.hira2kata(self.customer['旧姓_ふりがな'])} {jaconv.hira2kata(self.customer['被相続人_かな2'])}")
        pdf.draw_string(146, 133, f"{self.customer['旧姓']}  {self.customer['被相続人2']}", 12)
        pdf.draw_string(49, 120, '✓', 12)
        birthday = re.findall(r'\d+', self.customer['生年月日'])
        pdf.draw_string(135, 120, birthday[0][0], 12)
        pdf.draw_string(140, 120, birthday[0][1], 12)
        pdf.draw_string(146.5, 120, birthday[0][2], 12)
        pdf.draw_string(152, 120, birthday[0][3], 12)
        pdf.draw_string(163, 120, str(birthday[1]).zfill(2)[0], 12)
        pdf.draw_string(168.3, 120, str(birthday[1]).zfill(2)[1], 12)
        pdf.draw_string(180, 120, str(birthday[2]).zfill(2)[0], 12)
        pdf.draw_string(185, 120, str(birthday[2]).zfill(2)[1], 12)
        pdf.draw_string(53, 109, self.customer['被相続人_郵便番号'][0], 12)
        pdf.draw_string(58, 109, self.customer['被相続人_郵便番号'][1], 12)
        pdf.draw_string(63.2, 109, self.customer['被相続人_郵便番号'][2], 12)
        pdf.draw_string(75, 109, self.customer['被相続人_郵便番号'][4], 12)
        pdf.draw_string(80, 109, self.customer['被相続人_郵便番号'][5], 12)
        pdf.draw_string(85.3, 109, self.customer['被相続人_郵便番号'][6], 12)
        pdf.draw_string(91.5, 109, self.customer['被相続人_郵便番号'][7], 12)
        pdf.draw_string(49, 97, self.customer['被相続人_都道府県'][0:len(self.customer['被相続人_都道府県'])-1], 12)
        if self.customer['被相続人_都道府県'][-1] == '都':
            pdf.draw_string(68, 105, '✓', 12)
        elif self.customer['被相続人_都道府県'][-1] == '道':
            pdf.draw_string(77, 105, '✓', 12)
        elif self.customer['被相続人_都道府県'][-1] == '府':
            pdf.draw_string(68, 94, '✓', 12)
        elif self.customer['被相続人_都道府県'][-1] == '県':
            pdf.draw_string(77, 94, '✓', 12)
        pdf.draw_string(90, 97, self.customer['被相続人_住所'].replace(self.customer['被相続人_都道府県'], ''), 12)

        old_address1 = re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所1'])
        if old_address1 is not None:
            pdf.draw_string(49, 72, old_address1, 12)
            if old_address1[-1] == '都':
                pdf.draw_string(68, 75, '✓', 12)
            elif old_address1[-1] == '道':
                pdf.draw_string(77, 75, '✓', 12)
            elif old_address1[-1] == '府':
                pdf.draw_string(68, 69, '✓', 12)
            elif old_address1[-1] == '県':
                pdf.draw_string(77, 69, '✓', 12)

        pdf.draw_string(49, 61.5, '✓', 12)
        pdf.draw_string(71, 61.5, '✓', 12)
        pdf.draw_string(150, 61.5, '✓', 12)
        pdf.draw_string(49, 56, '✓', 12)
        pdf.draw_string(71, 56, '✓', 12)

        sql = ('''
            SELECT
                bank_number AS 口座番号,
                deposit_type AS 貯金等の種類
            FROM bank_customer
            WHERE code = ?
            AND jba_code = 9900
        ''')
        customer_banks = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]), False))
        for customer_bank in customer_banks:
            pdf.draw_string(63.5, 45, customer_bank['口座番号'][0])
            pdf.draw_string(69.5, 45, customer_bank['口座番号'][1])
            pdf.draw_string(75, 45, customer_bank['口座番号'][2])
            pdf.draw_string(81, 45, customer_bank['口座番号'][3])
            pdf.draw_string(86.5, 45, customer_bank['口座番号'][4])
            pdf.draw_string(107.5, 45, customer_bank['口座番号'][6])
            pdf.draw_string(112.5, 45, customer_bank['口座番号'][7])
            pdf.draw_string(118, 45, customer_bank['口座番号'][8])
            pdf.draw_string(123.5, 45, customer_bank['口座番号'][9])
            pdf.draw_string(129, 45, customer_bank['口座番号'][10])
            pdf.draw_string(135, 45, customer_bank['口座番号'][11])
            pdf.draw_string(140, 45, customer_bank['口座番号'][12])
            pdf.draw_string(145.5, 45, customer_bank['口座番号'][13])

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_貯金等照会書（通常）_1'),
                     os.path.dirname(__file__) + r"/pdf/ゆうちょ_貯金等照会書.pdf", page=1, open_bool=False)

        pdf = PdfCreate("A4")
        # 3 調査内容等
        deathday = re.findall(r'\d+', self.customer['死亡日'])
        # pdf.draw_string(23, 248, '✓', 12)   # 調査日不要
        pdf.draw_string(44, 271, '✓', 12)   # 調査日指定
        pdf.draw_string(81, 244.5, '相続のため', 12)
        pdf.draw_string(81, 271, '✓', 12)
        pdf.draw_string(132, 270, deathday[0][0], 12)
        pdf.draw_string(138, 270, deathday[0][1], 12)
        pdf.draw_string(144, 270, deathday[0][2], 12)
        pdf.draw_string(150, 270, deathday[0][3], 12)
        pdf.draw_string(162, 270, str(deathday[1]).zfill(2)[0], 12)
        pdf.draw_string(167, 270, str(deathday[1]).zfill(2)[1], 12)
        pdf.draw_string(179, 270, str(deathday[2]).zfill(2)[0], 12)
        pdf.draw_string(185, 270, str(deathday[2]).zfill(2)[1], 12)

        ### 残高証明書
        pdf.draw_string(86, 237, 1, 12)
        pdf.draw_string(82, 230, '✓', 12)
        pdf.draw_string(132, 229, deathday[0][0], 12)
        pdf.draw_string(138, 229, deathday[0][1], 12)
        pdf.draw_string(144, 229, deathday[0][2], 12)
        pdf.draw_string(150, 229, deathday[0][3], 12)
        pdf.draw_string(162, 229, str(deathday[1]).zfill(2)[0], 12)
        pdf.draw_string(167, 229, str(deathday[1]).zfill(2)[1], 12)
        pdf.draw_string(179, 229, str(deathday[2]).zfill(2)[0], 12)
        pdf.draw_string(185, 229, str(deathday[2]).zfill(2)[1], 12)

        for customer_bank in customer_banks:
            pdf.draw_string(91, 219, customer_bank['口座番号'][0])
            pdf.draw_string(97, 219, customer_bank['口座番号'][1])
            pdf.draw_string(103, 219, customer_bank['口座番号'][2])
            pdf.draw_string(108.5, 219, customer_bank['口座番号'][3])
            pdf.draw_string(114.5, 219, customer_bank['口座番号'][4])
            pdf.draw_string(138, 219, customer_bank['口座番号'][6])
            pdf.draw_string(143.5, 219, customer_bank['口座番号'][7])
            pdf.draw_string(150, 219, customer_bank['口座番号'][8])
            pdf.draw_string(155.5, 219, customer_bank['口座番号'][9])
            pdf.draw_string(161, 219, customer_bank['口座番号'][10])
            pdf.draw_string(167, 219, customer_bank['口座番号'][11])
            pdf.draw_string(173, 219, customer_bank['口座番号'][12])
            pdf.draw_string(178, 219, customer_bank['口座番号'][13])

        pdf.draw_string(81, 209, '✓', 12)

        # 4 その他
        pdf.draw_string(43, 175, '✓', 12)
        pdf.draw_string(100.3, 175, deathday[0][0], 12)
        pdf.draw_string(107, 175, deathday[0][1], 12)
        pdf.draw_string(113, 175, deathday[0][2], 12)
        pdf.draw_string(118.3, 175, deathday[0][3], 12)
        pdf.draw_string(130.2, 175, str(deathday[1]).zfill(2)[0], 12)
        pdf.draw_string(137, 175, str(deathday[1]).zfill(2)[1], 12)
        pdf.draw_string(149, 175, str(deathday[2]).zfill(2)[0], 12)
        pdf.draw_string(155, 175, str(deathday[2]).zfill(2)[1], 12)

        old_address2 = re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所2'])
        if old_address2 is not None:
            pdf.draw_string(50, 96, old_address2, 12)
            if old_address2[-1] == '都':
                pdf.draw_string(68, 100, '✓', 12)
            elif old_address2[-1] == '道':
                pdf.draw_string(77, 100, '✓', 12)
            elif old_address2[-1] == '府':
                pdf.draw_string(68, 95, '✓', 12)
            elif old_address2[-1] == '県':
                pdf.draw_string(77, 95, '✓', 12)

        old_address3 = re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所3'])
        if old_address3 is not None:
            pdf.draw_string(50, 72, old_address3, 12)
            if old_address3[-1] == '都':
                pdf.draw_string(68, 77, '✓', 12)
            elif old_address3[-1] == '道':
                pdf.draw_string(77, 77, '✓', 12)
            elif old_address3[-1] == '府':
                pdf.draw_string(68, 72, '✓', 12)
            elif old_address3[-1] == '県':
                pdf.draw_string(77, 72, '✓', 12)
                
        pdf.pdf_save(
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_貯金等照会書（通常）_2'),
            os.path.dirname(__file__) + r"/pdf/ゆうちょ_貯金等照会書.pdf", page=2, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書', 'ゆうちょ_貯金等照会書（通常）'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_貯金等照会書（通常）_1'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_貯金等照会書（通常）_2')
        )

    # ゆうちょ_貯金等照会書（相続）
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

        self.t_will_execution_person = ft.Text('遺言執行者')
        self.rg_will_execution_person = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.t_conciliation_or_judge = ft.Text('家庭裁判所による遺産分割調停又は審判')
        self.rg_conciliation_or_judge = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('ゆうちょ銀行の口座凍結手続き'),
            content=ft.Column(
                [
                    self.t_discussed_document,
                    self.rg_discussed_document,
                    ft.VerticalDivider(),
                    self.t_will,
                    self.rg_will,
                    # ft.VerticalDivider(),
                    # self.t_will_execution_person,
                    # self.rg_will_execution_person,
                    # ft.VerticalDivider(),
                    # self.t_conciliation_or_judge,
                    # self.rg_conciliation_or_judge,
                ],
                height=150,
                # height=300,
            ),
            actions=[ft.ElevatedButton(text="OK", on_click=self.account_freezing_create, autofocus=True),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    # １回目申し出
    def account_freezing_create(self, e):
        self.close_dlg(self)
        self.page.update()
        sql = ('''
            SELECT
                 folder_s_path AS フォルダパス,
                 zipcode AS 被相続人_郵便番号,
                 prefectures AS 被相続人_都道府県,
                 municipalities AS 被相続人_市区町村,
                 townarea || house_number || building AS 被相続人_住所,
                 old_address1 AS 旧住所1,
                 old_address2 AS 旧住所2,
                 old_address3 AS 旧住所3,
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

        pdf = PdfCreate("A4", 'landscape')
        pdf.draw_string(61, 168, '✓', 8)
        pdf.draw_string(61, 164, '✓', 8) if self.rg_will.value == '無' else pdf.draw_string(49, 164, '✓', 8)
        pdf.draw_string(61, 159, '✓', 8) if self.rg_discussed_document.value == '無' else pdf.draw_string(49, 159, '✓',
                                                                                                          8)
        pdf.draw_string(61, 155, '✓', 8)

        ### 住所
        # 郵便番号
        pdf.draw_string(42, 129, self.customer['被相続人_郵便番号'][0], 12)
        pdf.draw_string(48, 129, self.customer['被相続人_郵便番号'][1], 12)
        pdf.draw_string(54, 129, self.customer['被相続人_郵便番号'][2], 12)
        pdf.draw_string(63, 129, self.customer['被相続人_郵便番号'][4], 12)
        pdf.draw_string(69, 129, self.customer['被相続人_郵便番号'][5], 12)
        pdf.draw_string(75, 129, self.customer['被相続人_郵便番号'][6], 12)
        pdf.draw_string(81, 129, self.customer['被相続人_郵便番号'][7], 12)

        # 住所
        pdf.draw_string(91, 129, self.customer['被相続人_都道府県'][:len(self.customer['被相続人_都道府県']) - 1], 10)

        if self.customer['被相続人_都道府県'][-1] == '都':
            pdf.draw_string(106.5, 130, '〇')
        elif self.customer['被相続人_都道府県'][-1] == '道':
            pdf.draw_string(109.5, 130, '〇')
        elif self.customer['被相続人_都道府県'][-1] == '府':
            pdf.draw_string(106.5, 126.5, '〇')
        elif self.customer['被相続人_都道府県'][-1] == '県':
            pdf.draw_string(109.5, 126.5, '〇')

        pdf.draw_string(115, 129, self.customer['被相続人_市区町村'][:len(self.customer['被相続人_市区町村']) - 1])

        if self.customer['被相続人_市区町村'][-1] == '市':
            pdf.draw_string(134, 131, '〇')
        elif self.customer['被相続人_市区町村'][-1] == '区':
            pdf.draw_string(134, 128.5, '〇')
        elif self.customer['被相続人_市区町村'][-1] == '郡':
            pdf.draw_string(134, 126, '〇')

        pdf.draw_string(42, 119, self.customer['被相続人_住所'])

        # 氏名
        pdf.draw_string(42, 110, jaconv.hira2kata(self.customer['被相続人_かな1']), 12)
        pdf.draw_string(98, 110, jaconv.hira2kata(self.customer['被相続人_かな2']), 12)
        pdf.draw_string(42, 102, self.customer['被相続人1'], 12)
        pdf.draw_string(98, 102, self.customer['被相続人2'], 12)

        # 生年月日
        if convert_to_wareki2(self.customer['生年月日'])[:2] == '明治':
            pdf.draw_string(38.5, 94, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '大正':
            pdf.draw_string(44.5, 94, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '昭和':
            pdf.draw_string(51, 94, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '平成':
            pdf.draw_string(57, 94, '✓', 8)
        elif convert_to_wareki2(self.customer['生年月日'])[:2] == '令和':
            pdf.draw_string(63.5, 94, '✓', 8)

        pdf.draw_string(71, 93.5,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[0].zfill(2)[0], 12)
        pdf.draw_string(78, 93.5,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[0].zfill(2)[1], 12)
        pdf.draw_string(88.5, 93.5,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[1].zfill(2)[0], 12)
        pdf.draw_string(94.5, 93.5,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[1].zfill(2)[1], 12)
        pdf.draw_string(106.5, 93.5,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[2].zfill(2)[0], 12)
        pdf.draw_string(112.5, 93.5,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['生年月日']))[2].zfill(2)[1], 12)

        # 死亡日
        if convert_to_wareki2(self.customer['死亡日'])[:2] == '平成':
            pdf.draw_string(39, 87, '✓', 8)
        elif convert_to_wareki2(self.customer['死亡日'])[:2] == '令和':
            pdf.draw_string(53.5, 87, '✓', 8)

        pdf.draw_string(71, 87,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['死亡日']))[0].zfill(2)[0], 12)
        pdf.draw_string(78, 87,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['死亡日']))[0].zfill(2)[1], 12)
        pdf.draw_string(88.5, 87,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['死亡日']))[1].zfill(2)[0], 12)
        pdf.draw_string(94.5, 87,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['死亡日']))[1].zfill(2)[1], 12)
        pdf.draw_string(106.5, 87,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['死亡日']))[2].zfill(2)[0], 12)
        pdf.draw_string(112.5, 87,
                        re.findall('[0-9]+', convert_to_wareki2(self.customer['死亡日']))[2].zfill(2)[1], 12)

        ### 代表相続人
        pdf.draw_string(42, 70, self.customer['依頼者_郵便番号'][0], 12)
        pdf.draw_string(48, 70, self.customer['依頼者_郵便番号'][1], 12)
        pdf.draw_string(54, 70, self.customer['依頼者_郵便番号'][2], 12)
        pdf.draw_string(63, 70, self.customer['依頼者_郵便番号'][4], 12)
        pdf.draw_string(69, 70, self.customer['依頼者_郵便番号'][5], 12)
        pdf.draw_string(75, 70, self.customer['依頼者_郵便番号'][6], 12)
        pdf.draw_string(81, 70, self.customer['依頼者_郵便番号'][7], 12)

        pdf.draw_string(91, 70, self.customer['依頼者_都道府県'][:len(self.customer['依頼者_都道府県']) - 1], 10)
        if self.customer['依頼者_都道府県'][-1] == '都':
            pdf.draw_string(106.5, 71.5, '〇', 10)
        elif self.customer['依頼者_都道府県'][-1] == '道':
            pdf.draw_string(109.5, 71.5, '〇', 10)
        elif self.customer['依頼者_都道府県'][-1] == '府':
            pdf.draw_string(106.5, 68.5, '〇', 10)
        elif self.customer['依頼者_都道府県'][-1] == '県':
            pdf.draw_string(109.5, 68.5, '〇', 10)

        if not self.customer['依頼者_町域名'][-1] == '町':
            pdf.draw_string(113, 70, self.customer['依頼者_町域名'][:len(self.customer['依頼者_町域名']) - 1], 8)
        else:
            pdf.draw_string(113, 70, self.customer['依頼者_町域名'], 8)

        if self.customer['依頼者_町域名'][-1] == '市':
            pdf.draw_string(134, 73, '〇', 10)
        elif self.customer['依頼者_町域名'][-1] == '区':
            pdf.draw_string(134, 70, '〇', 10)
        elif self.customer['依頼者_町域名'][-1] == '郡':
            pdf.draw_string(134, 67, '〇', 10)

        pdf.draw_string(42, 61, self.customer['依頼者_住所'])

        # 氏名
        pdf.draw_string(42, 52, jaconv.hira2kata(self.customer['依頼者_ふりがな1']), 12)
        pdf.draw_string(98, 52, jaconv.hira2kata(self.customer['依頼者_ふりがな2']), 12)
        pdf.draw_string(42, 43, self.customer['依頼者_氏名1'], 12)
        pdf.draw_string(98, 43, self.customer['依頼者_氏名2'], 12)

        # 連絡先
        contact = re.findall('[0-9]+', self.customer['連絡先_携帯']) if self.customer[
                                                                            '連絡先_携帯'] != '' else re.findall(
            '[0-9]+', self.customer['連絡先_自宅'])
        # contact = str(contact).replace(r'\r', '')

        try:
            if len(contact[0]) == 4:
                pdf.draw_string(38, 35, contact[0][0])

            if len(contact[0]) >= 3:
                pdf.draw_string(43.5, 35, contact[0][-3])

            pdf.draw_string(48.5, 35, contact[0][-2])
            pdf.draw_string(53.5, 35, contact[0][-1])

            if len(contact[1]) == 4:
                pdf.draw_string(60, 35, contact[1][0])
                pdf.draw_string(65.5, 35, contact[1][-3])

            if len(contact[1]) >= 3:
                pdf.draw_string(65.5, 35, contact[1][-3])

            pdf.draw_string(70.5, 35, contact[1][-2])
            pdf.draw_string(75.5, 35, contact[1][-1])

            pdf.draw_string(82, 35, contact[2][0])
            pdf.draw_string(87.5, 35, contact[2][1])
            pdf.draw_string(92.5, 35, contact[2][2])
            pdf.draw_string(97.5, 35, contact[2][3])

            if (contact[0] == '050') or (contact[0] == '060') or (contact[0] == '070') or (contact[0] == '080') or (
                    contact[0] == '090'):
                pdf.draw_string(128, 35, '✓', 8)  # 携帯
            else:
                pdf.draw_string(103, 35, '✓', 8)  # 自宅
        except:
            pass

        # pdf.draw_string(114, 35, '✓')  # 勤務先

        ### 配偶者
        sql = 'SELECT EXISTS(SELECT * FROM heir WHERE code = ? AND(relationship = "妻" OR relationship = "夫"))'
        if GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0] == 1:
            sql = 'SELECT * FROM heir WHERE code = ? AND(relationship = "妻" OR relationship = "夫")'
            spouse = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]
            pdf.draw_string(95, 168, f'{spouse[2]}　{spouse[3]}', 12)

            spouse_deathday = spouse[9]
            if spouse[11] == '死亡':
                pdf.draw_string(80.5, 161.5, '✓', 8)
                if convert_to_wareki2(spouse[8])[:2] == '明治':
                    pdf.draw_string(102.5, 150, '✓', 8)
                    # pdf.draw_string(93.5, 150, '✓', 8)
                elif convert_to_wareki2(spouse[8])[:2] == '大正':
                    pdf.draw_string(111, 150, '✓', 8)
                    # pdf.draw_string(102.5, 150, '✓', 8)
                elif convert_to_wareki2(spouse[8])[:2] == '昭和':
                    pdf.draw_string(120, 150, '✓', 8)
                    # pdf.draw_string(111, 150, '✓', 8)
                elif convert_to_wareki2(spouse[8])[:2] == '平成':
                    pdf.draw_string(129, 150, '✓', 8)
                    # pdf.draw_string(120, 150, '✓', 8)
                elif convert_to_wareki2(spouse[8])[:2] == '令和':
                    pdf.draw_string(138, 150, '✓', 8)
                    # pdf.draw_string(129, 150, '✓', 8)
                wareki_spouse_deathday = convert_to_wareki2(spouse_deathday)
                pdf.draw_string(93, 145, re.findall('[0-9]+', wareki_spouse_deathday)[0].zfill(2)[0], 10)
                pdf.draw_string(97.5, 145, re.findall('[0-9]+', wareki_spouse_deathday)[0].zfill(2)[1], 10)
                pdf.draw_string(108.5, 145,
                                re.findall('[0-9]+', wareki_spouse_deathday)[1].zfill(2)[0], 10)
                pdf.draw_string(113, 145, re.findall('[0-9]+', wareki_spouse_deathday)[1].zfill(2)[1], 10)
                pdf.draw_string(124, 145, re.findall('[0-9]+', wareki_spouse_deathday)[2].zfill(2)[0], 10)
                pdf.draw_string(128.5, 145,
                                re.findall('[0-9]+', wareki_spouse_deathday)[2].zfill(2)[1], 10)
            elif spouse[11] == '海外居住':
                pdf.draw_string(96.5, 161.5, '✓', 10)
            elif spouse[11] == '相続放棄':
                pdf.draw_string(120, 161.5, '✓', 10)
            elif spouse[11] == '成年被後見人':
                pdf.draw_string(80.5, 156, '✓', 10)

        ### 子
        sql = 'SELECT EXISTS(SELECT * FROM heir WHERE code = ? AND(relationship LIKE "%女%" OR relationship LIKE "%男%") AND relationship NOT LIKE "%孫%")'
        if GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0] == 1:
            sql = 'SELECT * FROM heir WHERE code = ? AND(relationship LIKE "%女%" OR relationship LIKE "%男%") AND relationship NOT LIKE "%孫%"'
            try:
                childrens = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
                for i, children in enumerate(childrens):
                    if i == 0:
                        down_point = 0
                    else:
                        down_point -= 24
                    pdf.draw_string(164, (129 + down_point), f'{children[2]}　{children[3]}')

                    if children[11] == '死亡':
                        pdf.draw_string(151, (124.5 + down_point), '✓', 6)  # 死亡
                        children_deathday = convert_to_wareki2(children[8])
                        if children_deathday[0:2] == '明治':
                            pdf.draw_string(163, (116.5 + down_point), '✓', 6)  # 明治
                        elif children_deathday[0:2] == '大正':
                            pdf.draw_string(171, (116.5 + down_point), '✓', 6)  # 大正
                        elif children_deathday[0:2] == '昭和':
                            pdf.draw_string(179, (116.5 + down_point), '✓', 6)  # 昭和
                        elif children_deathday[0:2] == '平成':
                            pdf.draw_string(187, (116.5 + down_point), '✓', 6)  # 平成
                        elif children_deathday[0:2] == '令和':
                            pdf.draw_string(195, (116.5 + down_point), '✓', 6)  # 令和
                        children_deathday = re.findall('[0-9]+', children_deathday)
                        pdf.draw_string(163, (112 + down_point), str(children_deathday[0]).zfill(2)[0], 6)
                        pdf.draw_string(167, (112 + down_point), str(children_deathday[0]).zfill(2)[1], 6)
                        pdf.draw_string(176, (112 + down_point), str(children_deathday[1]).zfill(2)[0], 6)
                        pdf.draw_string(180.5, (112 + down_point), str(children_deathday[1]).zfill(2)[1], 6)
                        pdf.draw_string(189.5, (112 + down_point), str(children_deathday[2]).zfill(2)[0], 6)
                        pdf.draw_string(194.5, (112 + down_point), str(children_deathday[2]).zfill(2)[1], 6)
                    elif children[11] == '海外居住':
                        pdf.draw_string(173.5, (124.5 + down_point), '✓', 6)  # 海外居住
                    elif children[11] == '相続放棄':
                        pdf.draw_string(188.5, (124.5 + down_point), '✓', 6)  # 相続放棄
                    elif children[11] == '成年被後見人':
                        pdf.draw_string(151, (121 + down_point), '✓', 6)  # 成年被後見人
            except Exception as e:
                print(f"エラーが発生しました: {e}")

        ### 孫
        sql = 'SELECT EXISTS(SELECT * FROM heir WHERE code = ? AND relationship LIKE "%孫%" AND situation = "")'
        if GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0] == 1:
            sql = 'SELECT * FROM heir WHERE code = ? AND relationship LIKE "%孫%"'
            grandchilds = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
            for i, grandchild in enumerate(grandchilds):
                if i == 0:
                    down_point = 0
                else:
                    down_point -= 24
                pdf.draw_string(245, (129 + down_point), f'{grandchild[2]}　{grandchild[3]}')

        ### 父母
        sql = 'SELECT EXISTS(SELECT * FROM heir WHERE code = ? AND(relationship LIKE "%父%" OR relationship LIKE "%母%"))'
        if GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0] == 1:
            sql = 'SELECT * FROM heir WHERE code = ? AND(relationship LIKE "%父%" OR relationship LIKE "%母%") AND relationship not LIKE "%元%"'
            parents = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
            if not isinstance(parents, list):
                parents = list([parents])
            for parent in parents:
                if parent[10] == '父':
                    p = 0
                else:
                    p = 212 - 163.5

                pdf.draw_string(163 + p, 171.5, f'{parent[2]}　{parent[3]}', 10)
                if parent[11] == '死亡':
                    pdf.draw_string(151 + p, 167, '✓', 6)
                elif parent[11] == '海外居住':
                    pdf.draw_string(163 + p, 167, '✓', 6)
                elif parent[11] == '相続放棄':
                    pdf.draw_string(181 + p, 167, '✓', 6)
                elif parent[11] == '成年被後見人':
                    pdf.draw_string(151 + p, 163, '✓', 6)

                parent_birthday = convert_to_wareki2(parent[8])
                if parent_birthday[:2] == '明治':
                    pdf.draw_string(161.5 + p, 158, '✓', 6)
                elif parent_birthday[:2] == '大正':
                    pdf.draw_string(168.5 + p, 158, '✓', 6)
                elif parent_birthday[:2] == '昭和':
                    pdf.draw_string(175 + p, 158, '✓', 6)
                elif parent_birthday[:2] == '平成':
                    pdf.draw_string(182 + p, 158, '✓', 6)
                elif parent_birthday[:2] == '令和':
                    pdf.draw_string(189 + p, 158, '✓', 6)

                parent_birthday = re.findall('[0-9]+', parent_birthday)
                pdf.draw_string(161 + p, 154, str(parent_birthday[0]).zfill(2)[0], 8)
                pdf.draw_string(164 + p, 154, str(parent_birthday[0]).zfill(2)[1], 8)
                pdf.draw_string(172.5 + p, 154, str(parent_birthday[1]).zfill(2)[0], 8)
                pdf.draw_string(176.5 + p, 154, str(parent_birthday[1]).zfill(2)[1], 8)
                pdf.draw_string(185 + p, 154, str(parent_birthday[2]).zfill(2)[0], 8)
                pdf.draw_string(188.5 + p, 154, str(parent_birthday[2]).zfill(2)[1], 8)

                print('parent:', parent)
                if parent[11] == '死亡':
                    parent_deathday = convert_to_wareki2(parent[9])
                    if parent_deathday[:2] == '明治':
                        pdf.draw_string(161.5 + p, 150, '✓', 8)
                    elif parent_deathday[:2] == '大正':
                        pdf.draw_string(168.5 + p, 150, '✓', 8)
                    elif parent_deathday[:2] == '昭和':
                        pdf.draw_string(175 + p, 150, '✓', 8)
                    elif parent_deathday[:2] == '平成':
                        pdf.draw_string(182 + p, 150, '✓', 8)
                    elif parent_deathday[:2] == '令和':
                        pdf.draw_string(189 + p, 150, '✓', 8)
                    parent_deathday = re.findall('[0-9]+', parent_deathday)
                    print('parent_deathday:', parent_deathday)
                    pdf.draw_string(161 + p, 145.5, str(parent_deathday[0]).zfill(2)[0], 8)
                    pdf.draw_string(164 + p, 145.5, str(parent_deathday[0]).zfill(2)[1], 8)
                    pdf.draw_string(172.5 + p, 145.5, str(parent_deathday[1]).zfill(2)[0], 8)
                    pdf.draw_string(176.5 + p, 145.5, str(parent_deathday[1]).zfill(2)[1], 8)
                    pdf.draw_string(185 + p, 145.5, str(parent_deathday[2]).zfill(2)[0], 8)
                    pdf.draw_string(188.5 + p, 145.5, str(parent_deathday[2]).zfill(2)[1], 8)

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表1'),
                     os.path.dirname(__file__) + "/pdf/ゆうちょ_相続確認表.pdf", page=3, open_bool=False)

        ### 2ページ目
        pdf = PdfCreate("A4")

        ## 祖父・祖母

        ## 兄弟姉妹
        sql = 'SELECT EXISTS(SELECT * FROM heir WHERE code = ? AND(relationship LIKE "%兄弟%" OR relationship LIKE "%姉妹%"))'
        if GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0] == 1:
            sql = 'SELECT * FROM heir WHERE code = ? AND(relationship LIKE "%兄弟%" OR relationship LIKE "%姉妹%" OR relationship LIKE "%義%")'
            down_point = 0
            try:
                brother_sisters = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
                for i, brother_sister in enumerate(brother_sisters):
                    if i != 0:
                        down_point -= 24.2
                    pdf.draw_string(162, (173.5 + down_point), f'{brother_sister[2]}　{brother_sister[3]}')

                    if brother_sister[11] == '死亡':
                        pdf.draw_string(151, (168 + down_point), '✓', 6)  # 死亡
                        brother_sister_deathday = convert_to_wareki2(brother_sister[8])
                        if brother_sister_deathday[0:2] == '明治':
                            pdf.draw_string(160, (160 + down_point), '✓', 6)  # 明治
                        elif brother_sister_deathday[0:2] == '大正':
                            pdf.draw_string(168, (160 + down_point), '✓', 6)  # 大正
                        elif brother_sister_deathday[0:2] == '昭和':
                            pdf.draw_string(176, (160 + down_point), '✓', 6)  # 昭和
                        elif brother_sister_deathday[0:2] == '平成':
                            pdf.draw_string(184, (160 + down_point), '✓', 6)  # 平成
                        elif brother_sister_deathday[0:2] == '令和':
                            pdf.draw_string(192, (160 + down_point), '✓', 6)  # 令和
                        brother_sister_deathday = re.findall('[0-9]+', brother_sister_deathday)
                        pdf.draw_string(160, (155 + down_point), str(brother_sister_deathday[0]).zfill(2)[0], 6)
                        pdf.draw_string(164, (155 + down_point), str(brother_sister_deathday[0]).zfill(2)[1], 6)
                        pdf.draw_string(173, (155 + down_point), str(brother_sister_deathday[1]).zfill(2)[0], 6)
                        pdf.draw_string(177.5, (155 + down_point), str(brother_sister_deathday[1]).zfill(2)[1], 6)
                        pdf.draw_string(186.5, (155 + down_point), str(brother_sister_deathday[2]).zfill(2)[0], 6)
                        pdf.draw_string(191.5, (155 + down_point), str(brother_sister_deathday[2]).zfill(2)[1], 6)
                    elif brother_sister[11] == '海外居住':
                        pdf.draw_string(173.5, (168 + down_point), '✓', 6)  # 海外居住
                    elif brother_sister[11] == '相続放棄':
                        pdf.draw_string(188.5, (168 + down_point), '✓', 6)  # 相続放棄
                    elif brother_sister[11] == '成年被後見人':
                        pdf.draw_string(151, (164 + down_point), '✓', 6)  # 成年被後見人
            except Exception as e:
                print(f"エラーが発生しました: {e}")
                
               
        # pdf.draw_string(162, 172, )

        ## 姪甥

        ## 弊社内容
        pdf.draw_string(43, 72, '1')
        pdf.draw_string(49.5, 72, '9')
        pdf.draw_string(55, 72, '4')
        pdf.draw_string(62.5, 72, '0')
        pdf.draw_string(69, 72, '0')
        pdf.draw_string(74, 72, '2')
        pdf.draw_string(80, 72, '2')

        pdf.draw_string(90, 72, '東京')
        pdf.draw_string(108, 73.5, '〇')
        pdf.draw_string(118, 72, '町田')
        pdf.draw_string(138, 75, '〇')

        pdf.draw_string(43, 63, '森野一丁目22番5号')
        pdf.draw_string(40, 57, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ', 6)
        pdf.draw_string(40, 52, '相続手続支援センター町田', 8)
        pdf.draw_string(40, 48, '有限責任事業組合', 8)

        pdf.draw_string(103, 55, '0')
        pdf.draw_string(106.5, 55, '4')
        pdf.draw_string(110, 55, '2')
        pdf.draw_string(118, 55, '7')
        pdf.draw_string(121, 55, '1')
        pdf.draw_string(125, 55, '0')
        pdf.draw_string(130, 55, '6')
        pdf.draw_string(133, 55, '1')
        pdf.draw_string(136.5, 55, '7')
        pdf.draw_string(140, 55, '8')

        pdf.draw_string(113, 48.5, '✓')
        pdf.draw_string(106.5, 38, '✓')
        pdf.draw_string(106.5, 28, '✓')

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表2'),
                     os.path.dirname(__file__) + "/pdf/ゆうちょ_相続確認表.pdf", page=4, open_bool=False)

        # 3ページ目
        pdf = PdfCreate("A4")
        sql = ('''
            SELECT
                bank_number AS 口座番号,
                deposit_type AS 貯金等の種類
            FROM bank_customer
            WHERE code = ?
            AND jba_code = 9900
        ''')
        customer_banks = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        for i, customer_bank in enumerate(customer_banks):
            pdf.draw_string(20, (130.5 - i * 10.5), customer_bank["貯金等の種類"].replace('郵便', ''))
            pdf.draw_string(46, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[0].zfill(5)[0])
            pdf.draw_string(52, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[0].zfill(5)[1])
            pdf.draw_string(58, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[0].zfill(5)[2])
            pdf.draw_string(64, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[0].zfill(5)[3])
            pdf.draw_string(70, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[0].zfill(5)[4])

            pdf.draw_string(78, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[0])
            pdf.draw_string(84, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[1])
            pdf.draw_string(90, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[2])
            pdf.draw_string(96, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[3])
            pdf.draw_string(102, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[4])
            pdf.draw_string(108, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[5])
            pdf.draw_string(114, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[6])
            pdf.draw_string(120, (130.5 - i * 10.5), str(customer_bank["口座番号"]).split('-')[1].zfill(8)[7])

        # 投資信託の有無
        pdf.draw_string(46, 48, '✓', 6)

        # 記号番号不明の調査
        pdf.draw_string(46, 39.5, '✓', 6)

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表3'),
                     os.path.dirname(__file__) + "/pdf/ゆうちょ_相続確認表.pdf", page=5, open_bool=False)

        # 4ページ目 貯金等照会書
        pdf = PdfCreate("A4")
        pdf.draw_string(53, 225, '相続手続支援センター町田　有限責任事業組合', 12)

        pdf.draw_string(19.5, 201, '✓', 8)
        pdf.draw_string(51, 167,
                        f'{jaconv.hira2kata(self.customer["被相続人_かな1"])}　{jaconv.hira2kata(self.customer["被相続人_かな2"])}')
        pdf.draw_string(51, 154, f'{self.customer["被相続人1"]}　{self.customer["被相続人2"]}', 12)

        # 旧姓
        pdf.draw_string(143, 167, jaconv.hira2kata(self.customer["旧姓_ふりがな"]))
        pdf.draw_string(143, 154, self.customer["旧姓"], 12)
        # if not self.customer['旧姓'] == '':
        #     pdf.draw_string(143, 167, jaconv.hira2kata(self.customer['旧姓_ふりがな']))
        #     pdf.draw_string(143, 154, self.customer['旧姓'], 12)

        pdf.draw_string(49, 144, '✓', 8)
        customer_birthday = re.findall('[0-9]+', self.customer["生年月日"])
        pdf.draw_string(136, 144, customer_birthday[0][0])
        pdf.draw_string(141, 144, customer_birthday[0][1])
        pdf.draw_string(147.5, 144, customer_birthday[0][2])
        pdf.draw_string(152, 144, customer_birthday[0][3])
        pdf.draw_string(164, 144, str(customer_birthday[1]).zfill(2)[0])
        pdf.draw_string(169, 144, str(customer_birthday[1]).zfill(2)[1])
        pdf.draw_string(181, 144, str(customer_birthday[2]).zfill(2)[0])
        pdf.draw_string(186, 144, str(customer_birthday[2]).zfill(2)[1])

        # 郵便番号
        customer_zipcode = re.findall('[0-9]+', self.customer["被相続人_郵便番号"])
        pdf.draw_string(53, 132.5, customer_zipcode[0][0])
        pdf.draw_string(58, 132.5, customer_zipcode[0][1])
        pdf.draw_string(64, 132.5, customer_zipcode[0][2])
        pdf.draw_string(75, 132.5, customer_zipcode[1][0])
        pdf.draw_string(81, 132.5, customer_zipcode[1][1])
        pdf.draw_string(87, 132.5, customer_zipcode[1][2])
        pdf.draw_string(92, 132.5, customer_zipcode[1][3])

        # 連絡先

        # 住所
        pdf.draw_string(49, 122, self.customer["被相続人_都道府県"][:len(self.customer["被相続人_都道府県"]) - 1], 12)
        if self.customer["被相続人_都道府県"][-1] == '都':
            pdf.draw_string(69, 124, '✓')
        elif self.customer["被相続人_都道府県"][-1] == '道':
            pdf.draw_string(78, 124, '✓')
        elif self.customer["被相続人_都道府県"][-1] == '府':
            pdf.draw_string(69, 118, '✓')
        elif self.customer["被相続人_都道府県"][-1] == '県':
            pdf.draw_string(78, 118, '✓')
        pdf.draw_string(92, 122, self.customer['被相続人_市区町村'] + self.customer['被相続人_住所'], 12)

        # 旧住所
        if self.customer['旧住所1']:
            prefectures = re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所1']).group()
            city = self.customer['旧住所1'].replace(prefectures, '')
            pdf.draw_string(49, 96, prefectures[0:len(prefectures)-1], 12)
            if prefectures[-1] == '都':
                pdf.draw_string(69, 99, '✓')
            elif prefectures[-1] == '道':
                pdf.draw_string(78, 99, '✓')
            elif prefectures[-1] == '府':
                pdf.draw_string(69, 93.5, '✓')
            elif prefectures[-1] == '県':
                pdf.draw_string(78, 93.5, '✓')
            pdf.draw_string(92, 96, city, 12)

        if self.customer['旧住所2']:
            pdf.draw_string(49, 69,
                            re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所2']).group(), 12)
            pdf.draw_string(92, 69, str(self.customer['旧住所2']).replace(
                re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所1']).group(), ''), 12)

        if self.customer['旧住所3']:
            pdf.draw_string(49, 45,
                            re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所3']).group(), 12)
            pdf.draw_string(92, 45, str(self.customer['旧住所2']).replace(
                re.match('東京都|北海道|(?:京都|大阪)府|.{2,3}県', self.customer['旧住所3']).group(), ''), 12)
        # if self.customer[15] == '-':
        #     pdf.draw_string(92, 122, self.customer[12] + self.customer[13] + self.customer[14], 12)
        # else:
        #     pdf.draw_string(92, 122,
        #                   self.customer[12] + self.customer[13] + self.customer[14] + self.customer[15], 12)

        # 調査対象項目
        pdf.draw_string(49, 37, '✓')
        pdf.draw_string(72, 37, '✓')
        pdf.draw_string(151, 37, '✓')
        pdf.draw_string(49, 30.5, '✓')
        pdf.draw_string(72, 30.5, '✓')
        pdf.draw_string(93, 30.5, '✓') #その他
        pdf.draw_string(115, 31.5, '財形、積立')

        # その他届出住所
        # sql = 'SELECT EXISTS(SELECT * FROM customer WHERE code_a = ? AND other_notification_address1 != "-")'
        # if cur.execute(sql, code).fetchall()[0] == 1:
        #     pass

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表4'),
                     os.path.dirname(__file__) + "/pdf/ゆうちょ_相続確認表.pdf", page=7, open_bool=False)

        # 5ページ目
        pdf = PdfCreate("A4")
        pdf.draw_string(45, 264, '✓', 8)
        pdf.draw_string(83, 264, '✓', 8)

        customer_deathday = re.findall('[0-9]+', self.customer['死亡日'])
        pdf.draw_string(133, 263, customer_deathday[0][0])
        pdf.draw_string(138, 263, customer_deathday[0][1])
        pdf.draw_string(144, 263, customer_deathday[0][2])
        pdf.draw_string(150, 263, customer_deathday[0][3])
        pdf.draw_string(162, 263, str(customer_deathday[1]).zfill(2)[0])
        pdf.draw_string(168, 263, str(customer_deathday[1]).zfill(2)[1])
        pdf.draw_string(179, 263, str(customer_deathday[2]).zfill(2)[0])
        pdf.draw_string(185, 263, str(customer_deathday[2]).zfill(2)[1])
        pdf.draw_string(83, 238, '相続のため')
        pdf.draw_string(22, 207, '✓', 12)
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表5'),
                     os.path.dirname(__file__) + "/pdf/ゆうちょ_相続確認表.pdf", page=8, open_bool=False)

        os.makedirs(os.path.join(self.customer['フォルダパス'], '金融機関手続', '解約申請書'),
                    exist_ok=True)

        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], '金融機関手続', '残高証明書', '申請書', 'ゆうちょ_相続確認表'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表1'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表2'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表3')
        )

        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], '金融機関手続', '残高証明書', '申請書', 'ゆうちょ_貯金等照会書'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表4'),
            os.path.join(self.customer['フォルダパス'], 'ゆうちょ_相続確認表5')
        )

    # 残高証明書
    def balance_certificate(self):
        sql = (f'''
            SELECT
                t1.folder_s_path AS フォルダパス,
                t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                t1.username1 || "  " || t1.username2 AS 被相続人,
                t1.birthday AS 生年月日,
                t1.deathday AS 死亡日,
                t1.zipcode AS 郵便番号,
                t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || " " || t1.building AS 住所,
                t2.jba_code AS 銀行コード,
                t2.branch_code AS 支店コード,
                t2.bank_number AS 口座番号,
                t2.deposit_type AS 種類,
                t3.bank_branch_name AS 支店名,
                (SELECT username1 || "  " || username2 FROM heir WHERE code = "{GlobalValues.code}") AS 相続人,
                (SELECT username1_hurigana || "  " || username2_hurigana FROM heir WHERE code = "{GlobalValues.code}") AS 相続人_かな
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "9900"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        pdf = PdfCreate("A4")

        for p in range(1, 3, 1):
            # 請求者
            pdf.draw_string(50, 273, '194')
            pdf.draw_string(69, 273, '0022')
            pdf.draw_string(35, 262, '東京都町田市森野一丁目22番5号', 12)
            # pdf.draw_string(35, 255.5, f"{jaconv.hira2hkata(self.customer[0]['被相続人_かな'])} ｿｳｿﾞｸﾆﾝ {jaconv.hira2hkata(self.customer[0]['相続人_かな'])} ﾀﾞｲﾘﾆﾝ", 6)
            # pdf.draw_string(35, 253, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ', 6)
            pdf.draw_string(35, 254, f"{jaconv.hira2hkata(self.customer[0]['被相続人_かな'])} ｿｳｿﾞｸﾆﾝ {jaconv.hira2hkata(self.customer[0]['相続人_かな'])} ﾀﾞｲﾘﾆﾝ ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ", 8)
            pdf.draw_string(35, 248, f"{self.customer[0]['被相続人']}　相続人　{self.customer[0]['相続人']}　代理人", 10)
            pdf.draw_string(35, 243, "相続手続支援センター町田有限責任事業組合", 10)
            pdf.draw_string(44.5, 234, '〇', 22)
            pdf.draw_string(80, 235, '042', 12)
            pdf.draw_string(100, 235, '710', 12)
            pdf.draw_string(121, 235, '6178', 12)
            pdf.draw_string(145, 225, '✓', 12)
            pdf.draw_string(165, 225, '相続人代理人', 12)

            # 取引内容
            postal_code = re.findall(r'\d+', self.customer[0]['郵便番号'])
            pdf.draw_string(50, 209.5, postal_code[0])
            pdf.draw_string(69, 209.5, postal_code[1])
            pdf.draw_string(35, 203.5, self.customer[0]['住所'], 12)
            pdf.draw_string(35, 195.5, jaconv.hira2kata(self.customer[0]['被相続人_かな']))
            pdf.draw_string(35, 188, self.customer[0]['被相続人'], 12)
            birthday = re.findall(r'\d+', convert_to_wareki2(self.customer[0]['生年月日']))
            if convert_to_wareki2(self.customer[0]['生年月日'])[:2] == '令和':
                pdf.draw_string(34, 178, '✓', 12)
            elif convert_to_wareki2(self.customer[0]['生年月日'])[:2] == '昭和':
                pdf.draw_string(34, 171, '✓', 12)
            elif convert_to_wareki2(self.customer[0]['生年月日'])[:2] == '大正':
                pdf.draw_string(49, 178, '✓', 12)
            elif convert_to_wareki2(self.customer[0]['生年月日'])[:2] == '平成':
                pdf.draw_string(49, 171, '✓', 12)
            pdf.draw_string(68, 174, birthday[0], 12)
            pdf.draw_string(86, 174, birthday[1], 12)
            pdf.draw_string(102, 174, birthday[2], 12)
            deathday = re.findall(r'\d+', convert_to_wareki2(self.customer[0]['死亡日']))
            pdf.draw_string(148, 174, f"{convert_to_wareki2(self.customer[0]['死亡日'])[:2]}{deathday[0]}", 12)
            pdf.draw_string(174, 174, deathday[1], 12)
            pdf.draw_string(190, 174, deathday[2], 12)

            # 対象口座
            before = ''
            for i, bank in enumerate(self.customer):
                print('bank:', bank['口座番号'], bank['種類'])
                # pdf.draw_string(37, 143 - i * 9.5, bank['種類'].replace('郵便', ''), 12)
                if before != bank['口座番号']:
                    pdf.draw_string(34, 146 - i * 9.5, '✓', 12)
                    pdf.draw_string(67, 142 - i * 9.5, re.findall(r'\d+', bank['口座番号'])[0])
                    pdf.draw_string(109, 142 - i * 9.5, re.findall(r'\d+', bank['口座番号'])[1])
                    before = bank['口座番号']

            # 証明書枚数
            pdf.draw_string(50, 102, 1, 12)

            os.makedirs(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書',),
                        exist_ok=True)

            pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書',
                                      f'ゆうちょ銀行_残高証明書{p}'),
                         os.path.dirname(__file__) + r"/pdf/ゆうちょ_残高証明書請求書.pdf", page=p, open_bool=False)

        # pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書',
        #                           'ゆうちょ銀行_残高証明書2'),
        #              os.path.dirname(__file__) + r"/pdf/ゆうちょ_残高証明書請求書.pdf", page=2, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書', 'ゆうちょ銀行_残高証明書請求書'),
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書', 'ゆうちょ銀行_残高証明書1'),
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書', 'ゆうちょ銀行_残高証明書2')
        )

        self.img1 = ft.Image(
            src=os.path.dirname(__file__) + r'\png\ゆうちょ残高証明書申請書（記入例）.png',
            width=600,
            height=900,
            fit=ft.ImageFit.CONTAIN,
        )
        self.img2 = ft.Image(
            src=os.path.dirname(__file__) + r'\png\ゆうちょ貯金入出金照会申請書（記入例）.png',
            width=600,
            height=900,
            fit=ft.ImageFit.CONTAIN,
        )

        # from pdf2image import convert_from_path
        # sql = 'SELECT folder_s_path FROM customer WHERE code = ?'
        # path = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
        # file_pdf = os.path.join(path, '戸籍・法定相続情報一覧図', '法定相続情報.pdf')
        # poppler_dir = r"\poppler-23.10.0\Library\bin"
        # os.environ["Path"] += os.pathsep + os.environ['OneDrive'] + poppler_dir
        # pages = convert_from_path(file_pdf, 200)
        # for i, page in enumerate(pages):
        #     file_name = os.path.splitext(os.path.basename(file_pdf))[0] + ".png"
        #     export_file = os.path.join(os.path.dirname(file_pdf), file_name)
        #     page.save(str(export_file), "PNG")
        #
        # self.img3 = ft.Image(
        #     src=export_file,
        #     width=600,
        #     height=900,
        #     fit=ft.ImageFit.CONTAIN,
        # )

        # self.page.dialog = ft.AlertDialog(
        #     open=True,
        #     modal=True,
        #     # title=ft.Text('ゆうちょ銀行の口座凍結手続き'),
        #     content=ft.Column(
        #         [
        #             ft.Row([self.img1, self.img2]),
        #         ],
        #         height=1000,
        #     ),
        #     actions=[ft.ElevatedButton(text="OK", on_click=self.close_dlg, autofocus=True)],
        #     actions_alignment=ft.MainAxisAlignment.END,
        # )
        # self.page.update()

    def rg_t_foreign_nationality_change(self, _):
        if not self.dd_foreign_nationality1.visible:
            self.residence_country1.visible = True
            self.residence_country2.visible = True
            self.residence_country3.visible = True
            self.residence_country4.visible = True
            self.residence_country5.visible = True
            self.residence_country6.visible = True
            self.residence_country1.focus()
        else:
            self.residence_country1.visible = False
            self.residence_country2.visible = False
            self.residence_country3.visible = False
            self.residence_country4.visible = False
            self.residence_country5.visible = False
            self.residence_country6.visible = False

        self.dd_foreign_nationality1.update()
        self.dd_foreign_nationality2.update()

    def inheritance_notification(self):
        self.tf_x = ft.TextField(label="X調整値", value="0", hint_text="右に調整はプラス値、左はマイナス値")
        self.tf_y = ft.TextField(label="Y調整値", value="0", hint_text="上に調整はプラス値、下はマイナス値")

        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)
        self.page.update()
        self.b_file_select = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.FILE_OPEN),
                    # ft.Text(value="ゆうちょ相続手続請求書ファイル選択"),
                ]
            ),
            on_click=self.show_file_picker,
            # on_click=self.show_pick_folder,
        )
        self.result = ft.TextField(label='ゆうちょ相続手続請求書ファイル選択', multiline=True)

        self.t_foreign_nationality = ft.Text('非居住者または外国籍の有無')
        self.rg_t_foreign_nationality = ft.RadioGroup(
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
            value='無',
            on_change=self.rg_t_foreign_nationality_change,
        )

        # sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND situation = ""'
        # records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        self.residence_country1 = ft.TextField(label='居住国1', hint_text='中国など')
        self.residence_country2 = ft.TextField(label='居住国2', hint_text='中国など')
        self.residence_country3 = ft.TextField(label='居住国3', hint_text='中国など')
        self.residence_country4 = ft.TextField(label='居住国4', hint_text='中国など')
        self.residence_country5 = ft.TextField(label='居住国5', hint_text='中国など')
        self.residence_country6 = ft.TextField(label='居住国6', hint_text='中国など')
        # self.dd_foreign_nationality1 = ft.Dropdown(label='氏名選択', visible=False)
        # self.dd_foreign_nationality2 = ft.Dropdown(label='氏名選択', visible=False)
        # [self.dd_foreign_nationality1.options.append(ft.dropdown.Option(record[0])) for record in records]
        # [self.dd_foreign_nationality2.options.append(ft.dropdown.Option(record[0])) for record in records]

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('ゆうちょ銀行の手続き'),
            content=ft.Column(
                [
                    self.tf_x,
                    self.tf_y,
                    ft.Row([self.result, self.b_file_select]),
                    self.t_foreign_nationality,
                    self.rg_t_foreign_nationality,
                    self.residence_country1,
                    self.residence_country2,
                    self.residence_country3,
                    self.residence_country4,
                    self.residence_country5,
                    self.residence_country6,
                ],
                height=800,
                width=400
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True, on_click=self.inheritance_notification_create_web),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    # WEB様式版
    def inheritance_notification_create_web(self, _):
        self.close_dlg(self)
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', dt_now)
        pdf = PdfCreate('A4', 'landscape')
        sql = (f'''
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
                (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
                t4.username1 || "  " || t4.username2 AS 相続人,
                t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな,
                t1.prefectures AS 都道府県,
                t1.municipalities AS 市区町村,
                t1.townarea AS 町域名,
                t1.house_number AS 番地,
                t1.building AS 建物名,
                t4.zipcode AS 郵便番号,
                t4.prefectures || t4.municipalities || t4.townarea || t4.house_number AS 相続人住所,
                t4.building AS 相続人住所_建物名,
                t4.contact_home AS 自宅電話,
                t4.contact_phone AS 携帯電話,
                t4.birthday AS 相続人_生年月日,
                t4.heir_id AS 代表相続人ID
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "9900"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                        INNER JOIN heir AS t4
                        ON t4.code = t1.code
                        AND t4.code = "{GlobalValues.code}"
                        AND t4.situation = ""
                        AND t4.offer = 1
            WHERE t1.code = "{GlobalValues.code}"
        ''')
        self.customer = GlobalValues.get_db(sql, row_factory=True)
        print(GlobalValues.get_db(sql))

        # sql = ('''
        #     SELECT  heir_id,
        #             jba_code,
        #             branch_code AS 記号番号,
        #             bank_number AS 口座番号,
        #             subjects AS 種類
        #     FROM    heir_bank
        #     WHERE   heir_id = ?
        #     AND     subjects = "通常郵便貯金"
        # ''')
        # self.heir_bank = GlobalValues.get_db(sql, tuple([self.customer[0]['代表相続人ID']]), row_factory=True)
        # print(GlobalValues.get_db(sql, tuple([self.customer[0]['代表相続人ID']])))

        sql = (f'''
            SELECT
                t1.username1 || " " || t1.username2 AS 氏名,
                t2.heir_id,
                t2.jba_code,
                t2.branch_code AS 記号番号,
                t2.bank_number AS 口座番号,
                t2.subjects AS 種類
            FROM heir_bank AS t2
                INNER JOIN heir AS t1
                ON t1.heir_id = t2.heir_id
            WHERE t2.bank_customer_id = (
                SELECT bank_customer_id 
                FROM bank_customer 
                WHERE code = "{GlobalValues.code}" 
                AND jba_code = (SELECT jba_code FROM bank WHERE bank_name = ?)
            )
        ''')
        self.heir_bank = GlobalValues.get_db(sql, tuple(['ゆうちょ銀行']), row_factory=True)
        print('self.heir_bank:', GlobalValues.get_db(sql, tuple(['ゆうちょ銀行'])))

        # 死亡日
        deathday = convert_to_wareki2(self.customer[0]["死亡日"])
        if deathday[0:2] == '平成':
            pdf.draw_string(37 + int(self.tf_x.value), (178 + int(self.tf_y.value)), "✓")
        elif deathday[0:2] == '令和':
            pdf.draw_string(49 + int(self.tf_x.value), (178 + int(self.tf_y.value)), "✓")

        # 年
        deathday_year = str(re.findall(r'\d+', deathday)[0]).zfill(2)
        pdf.draw_string(53.8 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_year[0])
        pdf.draw_string(59.4 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_year[1])

        # 月
        deathday_month = str(re.findall(r'\d+', deathday)[1]).zfill(2)
        pdf.draw_string(70 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_month[0])
        pdf.draw_string(75 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_month[1])

        # 日
        deathday_day = str(re.findall(r'\d+', deathday)[2]).zfill(2)
        pdf.draw_string(85.3 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_day[0])
        pdf.draw_string(89.5 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_day[1])

        # 住所
        pdf.draw_string(32 + int(self.tf_x.value), (170 + int(self.tf_y.value)),
                        self.customer[0]["都道府県"][:len(self.customer[0]["都道府県"]) - 1])
        if self.customer[0]["都道府県"][-1] == '都':
            pdf.draw_string(56.4 + int(self.tf_x.value), (172 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["都道府県"][-1] == '道':
            pdf.draw_string(59.8 + int(self.tf_x.value), (172 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["都道府県"][-1] == '府':
            pdf.draw_string(56.4 + int(self.tf_x.value), (168 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["都道府県"][-1] == '県':
            pdf.draw_string(59.8 + int(self.tf_x.value), (168 + int(self.tf_y.value)), '〇')

        pdf.draw_string(67.4 + int(self.tf_x.value), (170 + int(self.tf_y.value)),
                        self.customer[0]["市区町村"][:len(self.customer[0]["市区町村"]) - 1])
        if self.customer[0]["市区町村"][-1] == '市':
            pdf.draw_string(95.6 + int(self.tf_x.value), (171.8 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["市区町村"][-1] == '区':
            pdf.draw_string(95.6 + int(self.tf_x.value), (169.5 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["市区町村"][-1] == '郡':
            pdf.draw_string(95.6 + int(self.tf_x.value), (166.7 + int(self.tf_y.value)), '〇')

        # pdf.draw_string(32 + int(self.tf_x.value), (162 + int(self.tf_y.value)),
        #                 self.customer[0]['町域名'] + self.customer[0]['番地'] + "　" + self.customer[0]['建物名'], 8)
        pdf.draw_string(32 + int(self.tf_x.value), (164 + int(self.tf_y.value)),
                        self.customer[0]['町域名'] + self.customer[0]['番地'], 8)
        pdf.draw_string(32 + int(self.tf_x.value), (160 + int(self.tf_y.value)),
                        self.customer[0]['建物名'], 8)

        # 氏名
        pdf.draw_string(116 + int(self.tf_x.value), (168 + int(self.tf_y.value)), self.customer[0]['被相続人'], 12)

        # フリガナ
        pdf.draw_string(116 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)),
                        jaconv.hira2kata(self.customer[0]['被相続人_かな']), 8)

        # 生年月日
        birthday = convert_to_wareki2(self.customer[0]['生年月日'])
        if birthday[0:2] == '明治':
            pdf.draw_string(114 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), "✓")  # 明治
        elif birthday[0:2] == '大正':
            pdf.draw_string(121 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), "✓")  # 大正
        elif birthday[0:2] == '昭和':
            pdf.draw_string(129 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), "✓")  # 昭和
        elif birthday[0:2] == '令和':
            pass

        # 年
        birthday_year = str(re.findall(r'\d+', birthday)[0]).zfill(2)
        pdf.draw_string(145.5 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_year[0])
        pdf.draw_string(149.9 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_year[1])

        # 月
        birthday_month = str(re.findall(r'\d+', birthday)[1]).zfill(2)
        pdf.draw_string(158.5 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_month[0])
        pdf.draw_string(162.5 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_month[1])

        # 日
        birthday_day = str(re.findall(r'\d+', birthday)[2]).zfill(2)
        pdf.draw_string(171.5 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_day[0])
        pdf.draw_string(175.5 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_day[1])

        # 郵便番号
        zipcode = self.customer[0]['郵便番号']
        pdf.draw_string(33 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[0])
        pdf.draw_string(40 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[1])
        pdf.draw_string(46 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[2])
        pdf.draw_string(55 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[4])
        pdf.draw_string(60.5 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[5])
        pdf.draw_string(66.5 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[6])
        pdf.draw_string(72.5 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[7])

        # 住所
        pdf.draw_string(83 + int(self.tf_x.value), (152 + int(self.tf_y.value)), self.customer[0]['相続人住所'])

        # フリガナ
        pdf.draw_string(31 + int(self.tf_x.value), 144 + int(self.tf_y.value),
                        jaconv.hira2kata(self.customer[0]['相続人かな']))

        # 氏名
        pdf.draw_string(31 + int(self.tf_x.value), 134 + int(self.tf_y.value), self.customer[0]['相続人'])

        # 電話番号
        contact = re.findall('[0-9]+', self.customer[0]['自宅電話'])
        if contact == []:
            contact = re.findall('[0-9]+', self.customer[0]['携帯電話'])

        if contact != []:
            pdf.draw_string(121 + int(self.tf_x.value), (139 + int(self.tf_y.value)), contact[0])
            pdf.draw_string(142 + int(self.tf_x.value), (139 + int(self.tf_y.value)), contact[1])
            pdf.draw_string(167 + int(self.tf_x.value), (139 + int(self.tf_y.value)), contact[2])

        # 生年月日
        heir_birthday = convert_to_wareki2(self.customer[0]['相続人_生年月日'])
        if heir_birthday[0:2] == '明治':
            pdf.draw_string(113 + int(self.tf_x.value), (129.5 + int(self.tf_y.value)), "✓", 8)  # 明治
        elif heir_birthday[0:2] == '大正':
            pdf.draw_string(121 + int(self.tf_x.value), (129.5 + int(self.tf_y.value)), "✓", 8)  # 大正
        elif heir_birthday[0:2] == '昭和':
            pdf.draw_string(129 + int(self.tf_x.value), (129.5 + int(self.tf_y.value)), "✓", 8)  # 昭和
        elif heir_birthday[0:2] == '令和':
            pass

        # 年
        heir_birthday_year = str(re.findall(r'\d+', heir_birthday)[0]).zfill(2)
        pdf.draw_string(146 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_year[0])
        pdf.draw_string(149.9 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_year[1])

        # 月
        heir_birthday_month = str(re.findall(r'\d+', heir_birthday)[1]).zfill(2)
        pdf.draw_string(158.5 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_month[0])
        pdf.draw_string(162.5 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_month[1])

        # 日
        heir_birthday_day = str(re.findall(r'\d+', heir_birthday)[2]).zfill(2)
        pdf.draw_string(171.5 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_day[0])
        pdf.draw_string(175.5 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_day[1])

        ### 代表相続人以外の相続人
        heir_offer_id = self.customer[0]['代表相続人ID']
        sql = (f'''
            SELECT 
                prefectures || municipalities || townarea || house_number AS 相続人住所,
                building AS 建物名,
                username1 || "  " || username2 AS 相続人
            FROM heir
            WHERE heir_id != {heir_offer_id}
            AND code = "{GlobalValues.code}"
            AND situation = ""
            AND offer != 1
        ''')
        records = GlobalValues.get_db(sql)
        for i, record in enumerate(records):
            print('record:', record)
            print('len(record[0]):', len(record[0]))
            if i == 0:
                # pdf.draw_string(31 + int(self.tf_x.value), (123 + int(self.tf_y.value)), record[0], 8)
                if len(record[0]) > 17:
                    pdf.draw_string(31 + int(self.tf_x.value), (116 + int(self.tf_y.value)), record[0][:17], 8)
                    pdf.draw_string(31 + int(self.tf_x.value), (110 + int(self.tf_y.value)), record[0][17:], 8)
                else:
                    pdf.draw_string(31 + int(self.tf_x.value), (116 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (103 + int(self.tf_y.value)), record[2], 8)
            elif i == 1:
                # pdf.draw_string(31 + int(self.tf_x.value), (95 + int(self.tf_y.value)), record[0], 8)
                if len(record[0]) > 17:
                    pdf.draw_string(31 + int(self.tf_x.value), (89 + int(self.tf_y.value)), record[0][:17], 8)
                    pdf.draw_string(31 + int(self.tf_x.value), (83 + int(self.tf_y.value)), record[0][17:], 8)
                else:
                    pdf.draw_string(31 + int(self.tf_x.value), (89 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (74 + int(self.tf_y.value)), record[2], 8)
            elif i == 2:
                # pdf.draw_string(31 + int(self.tf_x.value), (69 + int(self.tf_y.value)), record[0], 8)
                if len(record[0]) > 17:
                    pdf.draw_string(31 + int(self.tf_x.value), (61 + int(self.tf_y.value)), record[0][:17], 8)
                    pdf.draw_string(31 + int(self.tf_x.value), (55 + int(self.tf_y.value)), record[0][17:], 8)
                else:
                    pdf.draw_string(31 + int(self.tf_x.value), (61 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (48 + int(self.tf_y.value)), record[2], 8)
            elif i == 3:
                # pdf.draw_string(115 + int(self.tf_x.value), (123 + int(self.tf_y.value)), record[0], 8)
                if len(record[0]) > 17:
                    pdf.draw_string(115 + int(self.tf_x.value), (116 + int(self.tf_y.value)), record[0][:17], 8)
                    pdf.draw_string(115 + int(self.tf_x.value), (110 + int(self.tf_y.value)), record[0][17:], 8)
                else:
                    pdf.draw_string(115 + int(self.tf_x.value), (116 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(115 + int(self.tf_x.value), (103 + int(self.tf_y.value)), record[2], 8)
            elif i == 4:
                # pdf.draw_string(115 + int(self.tf_x.value), (95 + int(self.tf_y.value)), record[0], 8)
                if len(record[0]) > 17:
                    pdf.draw_string(115 + int(self.tf_x.value), (89 + int(self.tf_y.value)), record[0][:17], 8)
                    pdf.draw_string(115 + int(self.tf_x.value), (83 + int(self.tf_y.value)), record[0][17:], 8)
                else:
                    pdf.draw_string(115 + int(self.tf_x.value), (89 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(115 + int(self.tf_x.value), (74 + int(self.tf_y.value)), record[2], 8)
            elif i == 5:
                # pdf.draw_string(115 + int(self.tf_x.value), (69 + int(self.tf_y.value)), record[0], 8)
                if len(record[0]) > 17:
                    pdf.draw_string(115 + int(self.tf_x.value), (61 + int(self.tf_y.value)), record[0][:17], 8)
                    pdf.draw_string(115 + int(self.tf_x.value), (55 + int(self.tf_y.value)), record[0][17:], 8)
                else:
                    pdf.draw_string(115 + int(self.tf_x.value), (61 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(115 + int(self.tf_x.value), (48 + int(self.tf_y.value)), record[2], 8)

        ### 遺産整理受任者
        pdf.draw_string(42 + int(self.tf_x.value), (41 + int(self.tf_y.value)), '✓')
        pdf.draw_string(33 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '1')
        pdf.draw_string(40 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '9')
        pdf.draw_string(46 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '4')
        pdf.draw_string(55 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '0')
        pdf.draw_string(60.5 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '0')
        pdf.draw_string(66.5 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '2')
        pdf.draw_string(72.5 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '2')
        pdf.draw_string(89.5 + int(self.tf_x.value), (32 + int(self.tf_y.value)), '東京都町田市森野一丁目22番5号', 12)
        pdf.draw_string(33 + int(self.tf_x.value), (25 + int(self.tf_y.value)),
                        '相続手続支援センター町田有限責任事業組合', 8)
        pdf.draw_string(118 + int(self.tf_x.value), (25 + int(self.tf_y.value)), '042', 8)
        pdf.draw_string(136 + int(self.tf_x.value), (25 + int(self.tf_y.value)), '710', 8)
        pdf.draw_string(153 + int(self.tf_x.value), (25 + int(self.tf_y.value)), '6178', 8)

        ### 貯金等の明細
        sql = ('''
            SELECT DISTINCT
                bank_number
            FROM bank_customer
            WHERE code = ?
            AND jba_code = 9900
        ''')
        bunk_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        for i, record in enumerate(bunk_records):
            symbol = re.findall(r'\d+', str(record[0]))[0].zfill(5)  # 記号
            number = re.findall(r'\d+', str(record[0]))[1].zfill(8)  # 番号
            pdf.draw_string(213 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[0])
            pdf.draw_string(217.5 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[1])
            pdf.draw_string(222 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[2])
            pdf.draw_string(226 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[3])
            pdf.draw_string(230 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[4])

            pdf.draw_string(237 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[0])
            pdf.draw_string(241 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[1])
            pdf.draw_string(244.5 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[2])
            pdf.draw_string(249 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[3])
            pdf.draw_string(253.5 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[4])
            pdf.draw_string(258 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[5])
            pdf.draw_string(262 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[6])
            pdf.draw_string(267 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[7])

        # 外国人有無
        # いない
        if self.rg_t_foreign_nationality.value == '無':
            pdf.draw_string(189 + int(self.tf_x.value), (77 + int(self.tf_y.value)), '✓')
        # いる
        else:
            pdf.draw_string(190 + int(self.tf_x.value), (84 + int(self.tf_y.value)), '✓')
            pdf.draw_string(209 + int(self.tf_x.value), (79 + int(self.tf_y.value)), self.residence_country1.value)
            pdf.draw_string(240 + int(self.tf_x.value), (79 + int(self.tf_y.value)), self.residence_country2.value)
            pdf.draw_string(268 + int(self.tf_x.value), (79 + int(self.tf_y.value)), self.residence_country3.value)
            pdf.draw_string(209 + int(self.tf_x.value), (72 + int(self.tf_y.value)), self.residence_country4.value)
            pdf.draw_string(240 + int(self.tf_x.value), (72 + int(self.tf_y.value)), self.residence_country5.value)
            pdf.draw_string(268 + int(self.tf_x.value), (72 + int(self.tf_y.value)), self.residence_country6.value)

        # 振込口座
        if self.heir_bank == []:
            pass
        else:
            pdf.draw_string(209 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                            f'{str(self.heir_bank[0]["記号番号"]).zfill(3)[1:2]}', 14)
            pdf.draw_string(215.5 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                            f'{str(self.heir_bank[0]["記号番号"]).zfill(3)[2:3]}', 14)
            pdf.draw_string(221.5 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                            f'{str(self.heir_bank[0]["記号番号"]).zfill(3)[3:4]}', 14)

            try:
                pdf.draw_string(240.5 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[0:1]}', 14)
                pdf.draw_string(246.5 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[1:2]}', 14)
                pdf.draw_string(252.5 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[2:3]}', 14)
                pdf.draw_string(259 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[3:4]}', 14)
                pdf.draw_string(265 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[4:5]}', 14)
                pdf.draw_string(271 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[5:6]}', 14)
                pdf.draw_string(277 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[6:7]}', 14)
                pdf.draw_string(284 + int(self.tf_x.value), (50.5 + int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[7:8]}', 14)
            except Exception as e:
                print(e)

            # 氏名
            pdf.draw_string(204 + int(self.tf_x.value), (35 + int(self.tf_y.value)), f'{self.heir_bank[0]["氏名"]}',
                            14)

            # フリガナ
            pdf.draw_string(204 + int(self.tf_x.value), (44.5 + int(self.tf_y.value)),
                            f'{jaconv.hira2kata(self.customer[0]["相続人かな"])}', 8)

        os.makedirs(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書'), exist_ok=True)
        pdf.pdf_save(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'ゆうちょ銀行_相続届'),
            os.path.dirname(__file__) + "/pdf/ゆうちょ_相続手続請求書.pdf", page=1, open_bool=True)


    def inheritance_notification_create(self, _):
        self.close_dlg(self)
        # dt_now = datetime.now().strftime('%Y/%m/%d')
        # dt = re.findall('[0-9]+', dt_now)
        pdf = PdfCreate('A4', 'landscape')

        # sql = (f'''
        #     SELECT
        #         customer.folder_s_path AS フォルダパス,
        #         customer.username1_hurigana || "  " || customer.username2_hurigana AS 被相続人_かな,
        #         customer.username1 || "  " || customer.username2 AS 被相続人,
        #         customer.deathday AS 死亡日,
        #         customer.birthday AS 生年月日,
        #         customer.zipcode AS 郵便番号,
        #         customer.prefectures AS 都道府県,
        #         customer.municipalities AS 市区町村,
        #         customer.townarea AS 町域名,
        #         customer.house_number AS 番地,
        #         customer.building AS 建物名,
        #         heir.zipcode AS 郵便番号,
        #         heir.prefectures || heir.municipalities || heir.townarea || heir.house_number AS 相続人住所,
        #         heir.username1_hurigana || "  " || heir.username2_hurigana AS 相続人かな,
        #         heir.username1 || "  " || heir.username2 AS 相続人,
        #         heir.contact_home AS 自宅電話,
        #         heir.contact_phone AS 携帯電話,
        #         heir.birthday AS 相続人_生年月日,
        #         heir_bank.branch_code AS 振込先支店コード,
        #         heir_bank.bank_number AS 振込先口座番号,
        #         bank_customer.branch_code AS 解約支店コード,
        #         bank_customer.bank_number AS 解約口座番号,
        #         heir_bank.heir_id AS 代表相続人ID
        #     FROM heir
        #         INNER JOIN heir_bank
        #         ON heir_bank.bank_customer_id = bank_customer.bank_customer_id
        #             INNER JOIN bank_customer
        #             ON heir.code = bank_customer.code
        #             AND bank_customer.code = "{GlobalValues.code}"
        #             AND bank_customer.jba_code = 9900
        #                 INNER JOIN customer
        #     WHERE heir.heir_id = heir_bank.heir_id
        # ''')

        sql = (f'''
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
                (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
                t4.username1 || "  " || t4.username2 AS 相続人,
                t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな,
                t1.prefectures AS 都道府県,
                t1.municipalities AS 市区町村,
                t1.townarea AS 町域名,
                t1.house_number AS 番地,
                t1.building AS 建物名,
                t4.zipcode AS 郵便番号,
                t4.prefectures || t4.municipalities || t4.townarea || t4.house_number AS 相続人住所,
                t4.building AS 相続人住所_建物名,
                t4.contact_home AS 自宅電話,
                t4.contact_phone AS 携帯電話,
                t4.birthday AS 相続人_生年月日,
                t4.heir_id AS 代表相続人ID
            FROM customer AS t1
                INNER JOIN bank_customer AS t2
                ON t1.code = t2.code
                AND t2.jba_code = "9900"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "9900"
                        INNER JOIN heir AS t4
                        ON t4.code = t1.code
                        AND t4.code = "{GlobalValues.code}"
                        AND t4.situation = ""
                        AND t4.offer = 1
            WHERE t1.code = "{GlobalValues.code}"
        ''')
        self.customer = GlobalValues.get_db(sql, row_factory=True)
        print(GlobalValues.get_db(sql))

        # sql = ('''
        #     SELECT  heir_id,
        #             jba_code,
        #             branch_code AS 記号番号,
        #             bank_number AS 口座番号,
        #             subjects AS 種類
        #     FROM    heir_bank
        #     WHERE   heir_id = ?
        #     AND     subjects = "通常郵便貯金"
        # ''')

        sql = (f'''
            SELECT
                t2.heir_id,
                t2.jba_code,
                t2.branch_code AS 記号番号,
                t2.bank_number AS 口座番号,
                t2.subjects AS 種類
            FROM heir_bank AS t2
                INNER JOIN heir AS t1
                ON t1.heir_id = t2.heir_id
            WHERE t2.bank_customer_id = (
                SELECT bank_customer_id 
                FROM bank_customer 
                WHERE code = "{GlobalValues.code}" 
                AND jba_code = (SELECT jba_code FROM bank WHERE bank_name = ?)
            )
        ''')
        self.heir_bank = GlobalValues.get_db(sql, tuple(['ゆうちょ銀行']), row_factory=True)
        print('self.heir_bank:', GlobalValues.get_db(sql, tuple(['ゆうちょ銀行'])))

        # sql = (f'''
        #     SELECT
        #         heir.zipcode AS 郵便番号,
        #         heir.prefectures || heir.municipalities || heir.townarea || heir.house_number AS 相続人住所,
        #         heir.username1_hurigana || "  " || heir.username2_hurigana AS 相続人かな,
        #         heir.username1 || "  " || heir.username2 AS 相続人,
        #         heir.contact_home AS 自宅電話,
        #         heir.contact_phone AS 携帯電話,
        #         heir.birthday AS 相続人_生年月日
        #     FROM heir
        #         INNER JOIN heir_bank
        #         ON heir_id = (SELECT heir_id FROM heir WHERE code = "{GlobalValues.code}")
        #     WHERE heir.code = "{GlobalValues.code}"
        #     AND heir.situation = ""
        # ''')
        # self.customer_offer = GlobalValues.get_db(sql, row_factory=True)

        # 死亡日
        deathday = convert_to_wareki2(self.customer[0]["死亡日"])
        if deathday[0:2] == '平成':
            pdf.draw_string(37 + int(self.tf_x.value), (178 + int(self.tf_y.value)), "✓")
        elif deathday[0:2] == '令和':
            pdf.draw_string(49 + int(self.tf_x.value), (178 + int(self.tf_y.value)), "✓")

        # 年
        deathday_year = str(re.findall(r'\d+', deathday)[0]).zfill(2)
        pdf.draw_string(53.8 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_year[0])
        pdf.draw_string(59.4 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_year[1])

        # 月
        deathday_month = str(re.findall(r'\d+', deathday)[1]).zfill(2)
        pdf.draw_string(70 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_month[0])
        pdf.draw_string(75 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_month[1])

        # 日
        deathday_day = str(re.findall(r'\d+', deathday)[2]).zfill(2)
        pdf.draw_string(85.3 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_day[0])
        pdf.draw_string(89.5 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)), deathday_day[1])

        # 住所
        pdf.draw_string(32 + int(self.tf_x.value), (170 + int(self.tf_y.value)),
                        self.customer[0]["都道府県"][:len(self.customer[0]["都道府県"]) - 1])
        if self.customer[0]["都道府県"][-1] == '都':
            pdf.draw_string(56.4 + int(self.tf_x.value), (172 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["都道府県"][-1] == '道':
            pdf.draw_string(59.8 + int(self.tf_x.value), (172 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["都道府県"][-1] == '府':
            pdf.draw_string(56.4 + int(self.tf_x.value), (168 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["都道府県"][-1] == '県':
            pdf.draw_string(59.8 + int(self.tf_x.value), (168 + int(self.tf_y.value)), '〇')

        pdf.draw_string(67.4 + int(self.tf_x.value), (170 + int(self.tf_y.value)),
                        self.customer[0]["市区町村"][:len(self.customer[0]["市区町村"]) - 1])
        if self.customer[0]["市区町村"][-1] == '市':
            pdf.draw_string(95.6 + int(self.tf_x.value), (171.8 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["市区町村"][-1] == '区':
            pdf.draw_string(95.6 + int(self.tf_x.value), (169.5 + int(self.tf_y.value)), '〇')
        elif self.customer[0]["市区町村"][-1] == '郡':
            pdf.draw_string(95.6 + int(self.tf_x.value), (166.7 + int(self.tf_y.value)), '〇')

        pdf.draw_string(32 + int(self.tf_x.value), (162 + int(self.tf_y.value)),
                        self.customer[0]['町域名'] + self.customer[0]['番地'] + self.customer[0]['建物名'], 8)

        # 氏名
        pdf.draw_string(116 + int(self.tf_x.value), (168 + int(self.tf_y.value)), self.customer[0]['被相続人'], 12)

        # フリガナ
        pdf.draw_string(116 + int(self.tf_x.value), (177.5 + int(self.tf_y.value)),
                        jaconv.hira2kata(self.customer[0]['被相続人_かな']), 8)

        # 生年月日
        birthday = convert_to_wareki2(self.customer[0]['生年月日'])
        if birthday[0:2] == '明治':
            pdf.draw_string(115 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), "✓")  # 明治
        elif birthday[0:2] == '大正':
            pdf.draw_string(122 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), "✓")  # 大正
        elif birthday[0:2] == '昭和':
            pdf.draw_string(130 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), "✓")  # 昭和
        elif birthday[0:2] == '令和':
            pass

        # 年
        birthday_year = str(re.findall(r'\d+', birthday)[0]).zfill(2)
        pdf.draw_string(146 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_year[0])
        pdf.draw_string(150.4 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_year[1])

        # 月
        birthday_month = str(re.findall(r'\d+', birthday)[1]).zfill(2)
        pdf.draw_string(159 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_month[0])
        pdf.draw_string(163 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_month[1])

        # 日
        birthday_day = str(re.findall(r'\d+', birthday)[2]).zfill(2)
        pdf.draw_string(172 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_day[0])
        pdf.draw_string(176 + int(self.tf_x.value), (160.5 + int(self.tf_y.value)), birthday_day[1])

        # 郵便番号
        zipcode = self.customer[0]['郵便番号']
        pdf.draw_string(30 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[0])
        pdf.draw_string(37 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[1])
        pdf.draw_string(43 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[2])
        pdf.draw_string(52 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[4])
        pdf.draw_string(57.5 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[5])
        pdf.draw_string(63.5 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[6])
        pdf.draw_string(69.5 + int(self.tf_x.value), (153 + int(self.tf_y.value)), zipcode[7])

        # 住所
        pdf.draw_string(86.5 + int(self.tf_x.value), (152 + int(self.tf_y.value)), self.customer[0]['相続人住所'])

        # フリガナ
        pdf.draw_string(31 + int(self.tf_x.value), 144 + int(self.tf_y.value),
                        jaconv.hira2kata(self.customer[0]['相続人かな']))

        # 氏名
        pdf.draw_string(31 + int(self.tf_x.value), 134 + int(self.tf_y.value), self.customer[0]['相続人'])

        # 電話番号
        contact = re.findall('[0-9]+', self.customer[0]['自宅電話'])
        if contact == []:
            contact = re.findall('[0-9]+', self.customer[0]['携帯電話'])

        if contact != []:
            pdf.draw_string(121 + int(self.tf_x.value), (139 + int(self.tf_y.value)), contact[0])
            pdf.draw_string(142 + int(self.tf_x.value), (139 + int(self.tf_y.value)), contact[1])
            pdf.draw_string(167 + int(self.tf_x.value), (139 + int(self.tf_y.value)), contact[2])

        # 生年月日
        heir_birthday = convert_to_wareki2(self.customer[0]['相続人_生年月日'])
        if heir_birthday[0:2] == '明治':
            pdf.draw_string(113 + int(self.tf_x.value), (129.5 + int(self.tf_y.value)), "✓", 8)  # 明治
        elif heir_birthday[0:2] == '大正':
            pdf.draw_string(121 + int(self.tf_x.value), (129.5 + int(self.tf_y.value)), "✓", 8)  # 大正
        elif heir_birthday[0:2] == '昭和':
            pdf.draw_string(129 + int(self.tf_x.value), (129.5 + int(self.tf_y.value)), "✓", 8)  # 昭和
        elif heir_birthday[0:2] == '令和':
            pass

        # 年
        heir_birthday_year = str(re.findall(r'\d+', heir_birthday)[0]).zfill(2)
        pdf.draw_string(146.5 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_year[0])
        pdf.draw_string(150.4 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_year[1])

        # 月
        heir_birthday_month = str(re.findall(r'\d+', heir_birthday)[1]).zfill(2)
        pdf.draw_string(159 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_month[0])
        pdf.draw_string(163 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_month[1])

        # 日
        heir_birthday_day = str(re.findall(r'\d+', heir_birthday)[2]).zfill(2)
        pdf.draw_string(172 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_day[0])
        pdf.draw_string(176 + int(self.tf_x.value), (129 + int(self.tf_y.value)), heir_birthday_day[1])

        ### 代表相続人以外の相続人
        heir_offer_id = self.customer[0]['代表相続人ID']
        sql = (f'''
            SELECT 
                prefectures || municipalities || townarea || house_number AS 相続人住所,
                building AS 建物名,
                username1 || "  " || username2 AS 相続人
            FROM heir
            WHERE heir_id != {heir_offer_id}
            AND code = "{GlobalValues.code}"
            AND situation = ""
            AND offer != 1
        ''')
        records = GlobalValues.get_db(sql)
        for i, record in enumerate(records):
            if i == 0:
                pdf.draw_string(31 + int(self.tf_x.value), (123 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (116 + int(self.tf_y.value)), record[1], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (103 + int(self.tf_y.value)), record[2], 8)
            elif i == 1:
                pdf.draw_string(31 + int(self.tf_x.value), (95 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (89 + int(self.tf_y.value)), record[1], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (74 + int(self.tf_y.value)), record[2], 8)
            elif i == 2:
                pdf.draw_string(31 + int(self.tf_x.value), (69 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (61 + int(self.tf_y.value)), record[1], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (48 + int(self.tf_y.value)), record[2], 8)
            elif i == 3:
                pdf.draw_string(31 + int(self.tf_x.value), (123 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (116 + int(self.tf_y.value)), record[1], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (103 + int(self.tf_y.value)), record[2], 8)
            elif i == 4:
                pdf.draw_string(31 + int(self.tf_x.value), (95 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (89 + int(self.tf_y.value)), record[1], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (74 + int(self.tf_y.value)), record[2], 8)
            elif i == 5:
                pdf.draw_string(31 + int(self.tf_x.value), (69 + int(self.tf_y.value)), record[0], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (61 + int(self.tf_y.value)), record[1], 8)
                pdf.draw_string(31 + int(self.tf_x.value), (48 + int(self.tf_y.value)), record[2], 8)

        ### 遺産整理受任者
        pdf.draw_string(42 + int(self.tf_x.value), (41 + int(self.tf_y.value)), '✓')
        pdf.draw_string(30 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '1')
        pdf.draw_string(37 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '9')
        pdf.draw_string(43 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '4')
        pdf.draw_string(52 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '0')
        pdf.draw_string(57.5 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '0')
        pdf.draw_string(63.5 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '2')
        pdf.draw_string(69.5 + int(self.tf_x.value), (34 + int(self.tf_y.value)), '2')
        pdf.draw_string(86.5 + int(self.tf_x.value), (32 + int(self.tf_y.value)), '東京都町田市森野一丁目22番5号', 12)
        pdf.draw_string(30 + int(self.tf_x.value), (25 + int(self.tf_y.value)),
                        '相続手続支援センター町田有限責任事業組合', 8)
        pdf.draw_string(118 + int(self.tf_x.value), (25 + int(self.tf_y.value)), '042', 8)
        pdf.draw_string(136 + int(self.tf_x.value), (25 + int(self.tf_y.value)), '710', 8)
        pdf.draw_string(153 + int(self.tf_x.value), (25 + int(self.tf_y.value)), '6178', 8)

        ### 貯金等の明細
        sql = ('''
            SELECT DISTINCT
                bank_number
            FROM bank_customer
            WHERE code = ?
            AND jba_code = 9900
        ''')
        bunk_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        for i, record in enumerate(bunk_records):
            symbol = re.findall(r'\d+', str(record[0]))[0].zfill(5)  # 記号
            number = re.findall(r'\d+', str(record[0]))[1].zfill(8)  # 番号
            pdf.draw_string(210 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[0])
            pdf.draw_string(214 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[1])
            pdf.draw_string(218 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[2])
            pdf.draw_string(222 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[3])
            pdf.draw_string(227 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), symbol[4])

            pdf.draw_string(237 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[0])
            pdf.draw_string(241 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[1])
            pdf.draw_string(246 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[2])
            pdf.draw_string(250 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[3])
            pdf.draw_string(254 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[4])
            pdf.draw_string(258 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[5])
            pdf.draw_string(263 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[6])
            pdf.draw_string(267 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), number[7])

        #
        # for i, records in enumerate(bank_account):
        #     if isinstance(bank_account, list):
        #         symbol = str(bank_account[i][0])  # 記号
        #         number = str(bank_account[i][1])  # 番号
        #
        # pdf.draw_string(210 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{symbol[0:1]}')
        # pdf.draw_string(214 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{symbol[1:2]}')
        # pdf.draw_string(218 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{symbol[2:3]}')
        # pdf.draw_string(222 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{symbol[3:4]}')
        # pdf.draw_string(227 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{symbol[4:5]}')
        #
        # pdf.draw_string(237 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[0:1]}')
        # pdf.draw_string(241 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[1:2]}')
        # pdf.draw_string(246 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[2:3]}')
        # pdf.draw_string(250 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[3:4]}')
        # pdf.draw_string(254 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[4:5]}')
        # pdf.draw_string(258 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[5:6]}')
        # pdf.draw_string(263 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[6:7]}')
        # pdf.draw_string(267 + int(self.tf_x.value), (161 + int(self.tf_y.value) - i * 7), f'{number[7:8]}')
        #
        # 外国人有無
        # いない
        if self.rg_t_foreign_nationality.value == '無':
            pdf.draw_string(190 + int(self.tf_x.value), (77 + int(self.tf_y.value)), '✓')
        # いる
        else:
            pdf.draw_string(190 + int(self.tf_x.value), (84 + int(self.tf_y.value)), '✓')
            pdf.draw_string(209 + int(self.tf_x.value), (79 + int(self.tf_y.value)), self.residence_country1.value)
            pdf.draw_string(240 + int(self.tf_x.value), (79 + int(self.tf_y.value)), self.residence_country2.value)
            pdf.draw_string(268 + int(self.tf_x.value), (79 + int(self.tf_y.value)), self.residence_country3.value)
            pdf.draw_string(209 + int(self.tf_x.value), (72 + int(self.tf_y.value)), self.residence_country4.value)
            pdf.draw_string(240 + int(self.tf_x.value), (72 + int(self.tf_y.value)), self.residence_country5.value)
            pdf.draw_string(268 + int(self.tf_x.value), (72 + int(self.tf_y.value)), self.residence_country6.value)

        # 振込口座
        print("self.heir_bank:", self.heir_bank)
        if self.heir_bank == []:
            pass
            # pdf.draw_string(209 + int(self.tf_x.value), (49 + int(self.tf_y.value)), '0', 14)
            # pdf.draw_string(216 + int(self.tf_x.value), (49 + int(self.tf_y.value)), '8', 14)
            # pdf.draw_string(222 + int(self.tf_x.value), (49 + int(self.tf_y.value)), '5', 14)
        else:
            pdf.draw_string(209 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                            f'{str(self.heir_bank[0]["記号番号"]).zfill(3)[1:2]}', 14)
            pdf.draw_string(215.5 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                            f'{str(self.heir_bank[0]["記号番号"]).zfill(3)[2:3]}', 14)
            pdf.draw_string(221.5 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                            f'{str(self.heir_bank[0]["記号番号"]).zfill(3)[3:4]}', 14)

            try:
                pdf.draw_string(24.5 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[0:1]}', 14)
                pdf.draw_string(246.5 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[1:2]}', 14)
                pdf.draw_string(252.5 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[2:3]}', 14)
                pdf.draw_string(259 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[3:4]}', 14)
                pdf.draw_string(265 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[4:5]}', 14)
                pdf.draw_string(271 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[5:6]}', 14)
                pdf.draw_string(277 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[6:7]}', 14)
                pdf.draw_string(284 + int(self.tf_x.value), (51 +int(self.tf_y.value)),
                                f'{str(self.heir_bank[0]["口座番号"]).zfill(8)[7:8]}', 14)
            except Exception as e:
                print(e)

            # 氏名
            pdf.draw_string(204 + int(self.tf_x.value), (35 + int(self.tf_y.value)), f'{self.customer[0]["相続人"]}', 14)

            # フリガナ
            pdf.draw_string(204 + int(self.tf_x.value), (44 + int(self.tf_y.value)),
                            f'{jaconv.hira2kata(self.customer[0]["相続人かな"])}', 8)

        # pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'ゆうちょ銀行_相続届'),
        #              self.result.value, page=1, open_bool=True)

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'ゆうちょ銀行_相続届'),
                     os.path.dirname(__file__) + "/pdf/ゆうちょ_相続手続請求書.pdf", page=1, open_bool=True)

    def on_hover(self, e):
        e.control.bgcolor = "AMBER" if e.data == "true" else "AMBER_50"
        self.update()

    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            print('e.files[0].path: ', e.files[0].path)
            print('parent_path: ', str(Path(e.files[0].path).parent))
            self.result.value = e.files[0].path
            self.result.update()

    def show_file_picker(self, _: ft.ControlEvent):
        # extensions = ["*"]
        # extensions = ["pdf", "jpg"]
        extensions = ["pdf"]
        sql = 'SELECT folder_s_path FROM customer WHERE code = ?'
        folder_s_path = os.path.join(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0], '金融機関手続', '解約申請書')
        print('folder_s_path: ', folder_s_path)
        self.file_picker.pick_files(
            allow_multiple=False,
            file_type="custom",
            allowed_extensions=extensions,
            initial_directory=folder_s_path
        )


def main(page: ft.Page):
    GlobalValues.code = "2504001"
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = JpBank()
    page.add(cl)
    cl.account_freezing()
    # cl.inheritance_notification()
    # cl.balance_certificate()


if __name__ == '__main__':
    ft.app(target=main)
    # GlobalValues.code = 'E00316'
    # GlobalValues.my_page = ft.Page
    # cl = JpBank()
    # cl.account_freezing_normal()
