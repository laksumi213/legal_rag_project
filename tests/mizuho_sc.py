# みずほ証券
import os.path
from convert_to_wareki import convert_to_wareki2
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
# from time import sleep
from datetime import datetime
import jaconv
import re


class MizuhoSc(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.heir = None
        self.page = GlobalValues.my_page

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    # 残高証明書
    def balance_certificate(self):
        date = re.findall(r'\d+', datetime.now().strftime('%Y/%m/%d'))
        sql = ('''
            SELECT
                t1.username1 || "  " || username2 AS 氏名,
                t1.folder_s_path AS フォルダパス
            FROM customer AS t1
            WHERE
                t1.code = ?      
        ''')
        record = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        pdf = PdfCreate("A4")
        pdf.draw_string(147, 251, date[0][2])
        pdf.draw_string(151.5, 251, date[0][3])
        pdf.draw_string(160, 251, str(date[1]).zfill(2)[0])
        pdf.draw_string(164.5, 251, str(date[1]).zfill(2)[1])
        pdf.draw_string(173.5, 251, str(date[2]).zfill(2)[0])
        pdf.draw_string(178, 251, str(date[2]).zfill(2)[1])
        pdf.draw_string(56, 225, '東京都町田市森野一丁目22番5号', 12)
        pdf.draw_string(56, 217, '相続手続支援センター町田有限責任事業組合　組合員')
        pdf.draw_string(56, 212, '株式会社プロフィット・ワン　職務執行者　大貫利一')
        pdf.draw_string(56, 205, '042-710-6178', 12)
        pdf.draw_string(56, 179, record['氏名'], 12)
        pdf.pdf_save(os.path.join(record['フォルダパス'], 'みずほ証券_残高証明書_申請書'),
                     "./pdf/みずほ証券_残高証明書依頼書.pdf", page=1, open_bool=True)

    def inheritance_notification_create(self):
        ### 被相続人口座情報 ###
        self.bank_number = '5720323'

        ### 相続人口座情報 ###
        self.bank_number_heir = '3305959'

        dt_now = re.findall(r'\d+', datetime.now().strftime('%Y/%m/%d'))
        sql = ('''
            SELECT
                folder_s_path AS フォルダパス,
                username1_hurigana || "  " || username2_hurigana AS 氏名ふりがな,
                username1 || "  " || username2 AS 氏名,
                deathday AS 死亡日,
                birthday AS 生年月日,
                prefectures || municipalities || townarea || house_number AS 住所,
                building AS 建物名
            FROM customer
            WHERE code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])

        pdf = PdfCreate("A3", 'landscape')
        pdf.draw_string(116, 168.7, dt_now[0][2], 8)
        pdf.draw_string(119, 168.7, dt_now[0][3], 8)
        pdf.draw_string(126, 168.7, dt_now[1][0], 8)
        pdf.draw_string(129, 168.7, dt_now[1][1], 8)
        pdf.draw_string(135, 168.7, dt_now[2][0], 8)
        pdf.draw_string(138, 168.7, dt_now[2][1], 8)
        pdf.draw_string(33, 155.5, self.customer['氏名'])
        pdf.draw_string(33, 149, self.customer['住所'], 8)
        pdf.draw_string(33, 144, self.customer['建物名'], 8)
        pdf.draw_string(97, 159, '✓', 8)
        birthday = re.findall(r'\d+', self.customer['生年月日'])
        pdf.draw_string(110, 156, birthday[0][0], 8)
        pdf.draw_string(113.5, 156, birthday[0][1], 8)
        pdf.draw_string(116, 156, birthday[0][2], 8)
        pdf.draw_string(119, 156, birthday[0][3], 8)
        pdf.draw_string(126, 156, str(birthday[1]).zfill(2)[0], 8)
        pdf.draw_string(129, 156, str(birthday[1]).zfill(2)[1], 8)
        pdf.draw_string(135, 156, str(birthday[2]).zfill(2)[0], 8)
        pdf.draw_string(138, 156, str(birthday[2]).zfill(2)[1], 8)
        deathday = re.findall(r'\d+', self.customer['死亡日'])
        pdf.draw_string(110, 149, deathday[0][0], 8)
        pdf.draw_string(113.5, 149, deathday[0][1], 8)
        pdf.draw_string(116, 149, deathday[0][2], 8)
        pdf.draw_string(119, 149, deathday[0][3], 8)
        pdf.draw_string(126, 149, str(deathday[1]).zfill(2)[0], 8)
        pdf.draw_string(129, 149, str(deathday[1]).zfill(2)[1], 8)
        pdf.draw_string(135, 149, str(deathday[2]).zfill(2)[0], 8)
        pdf.draw_string(138, 149, str(deathday[2]).zfill(2)[1], 8)
        pdf.draw_string(100, 141, str(self.bank_number).zfill(7)[0])
        pdf.draw_string(106, 141, str(self.bank_number).zfill(7)[1])
        pdf.draw_string(112.5, 141, str(self.bank_number).zfill(7)[2])
        pdf.draw_string(118.5, 141, str(self.bank_number).zfill(7)[3])
        pdf.draw_string(125, 141, str(self.bank_number).zfill(7)[4])
        pdf.draw_string(131, 141, str(self.bank_number).zfill(7)[5])
        pdf.draw_string(138, 141, str(self.bank_number).zfill(7)[6])
        pdf.draw_string(19, 118, '相続手続支援センター町田有限責任事業組合　組合員', 5)
        pdf.draw_string(19, 115, '株式会社プロフィット・ワン　職務執行者　大貫利一', 5)
        pdf.draw_string(34, 112, '042', 6)
        pdf.draw_string(45, 112, '710', 6)
        pdf.draw_string(56, 112, '6178', 6)
        pdf.draw_string(28, 59, '✓', 16)

        # 受取人
        sql = ('''
            SELECT
                username1_hurigana || "  " || username2_hurigana AS 氏名ふりがな,
                username1 || "  " || username2 AS 氏名,
                birthday AS 生年月日,
                zipcode AS 郵便番号,
                prefectures || municipalities || townarea || house_number || building AS 住所
            FROM heir
            WHERE code = ?
            AND offer = 1
        ''')
        self.heir = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)[0]
        print(GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0])
        pdf.draw_string(46, 39.3, jaconv.hira2kata(self.heir['氏名ふりがな']), 6)
        pdf.draw_string(46, 33, self.heir['氏名'])
        pdf.draw_string(93.5, 38.5, '✓', 8)
        birthday = re.findall(r'\d+', self.heir['生年月日'])
        pdf.draw_string(108, 33, birthday[0][0], 8)
        pdf.draw_string(111.5, 33, birthday[0][1], 8)
        pdf.draw_string(114.5, 33, birthday[0][2], 8)
        pdf.draw_string(117.5, 33, birthday[0][3], 8)
        pdf.draw_string(124, 33, str(birthday[1]).zfill(2)[0], 8)
        pdf.draw_string(127, 33, str(birthday[1]).zfill(2)[1], 8)
        pdf.draw_string(133, 33, str(birthday[2]).zfill(2)[0], 8)
        pdf.draw_string(136, 33, str(birthday[2]).zfill(2)[1], 8)
        pdf.draw_string(39, 28, self.heir['郵便番号'], 7)
        pdf.draw_string(39, 23, self.heir['住所'], 8)
        pdf.draw_string(112, 23, str(self.bank_number_heir).zfill(7)[0])
        pdf.draw_string(116.5, 23, str(self.bank_number_heir).zfill(7)[1])
        pdf.draw_string(121.5, 23, str(self.bank_number_heir).zfill(7)[2])
        pdf.draw_string(126, 23, str(self.bank_number_heir).zfill(7)[3])
        pdf.draw_string(131, 23, str(self.bank_number_heir).zfill(7)[4])
        pdf.draw_string(135.5, 23, str(self.bank_number_heir).zfill(7)[5])
        pdf.draw_string(140, 23, str(self.bank_number_heir).zfill(7)[6])

        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'みずほ証券_相続届1'),
                     os.path.dirname(__file__) + r"/pdf/みずほ証券_相続届.pdf", page=1, open_bool=False)

        pdf = PdfCreate("A3", 'landscape')
        pdf.pdf_save(os.path.join(self.customer['フォルダパス'], 'みずほ証券_相続届2'),
                     os.path.dirname(__file__) + r"/pdf/みずほ証券_相続届.pdf", page=2, open_bool=False)

        os.makedirs(os.path.join(self.customer['フォルダパス'], '金融機関手続書類', '解約申請書'), exist_ok=True)
        pdf.pdf_marge(
            os.path.join(self.customer['フォルダパス'], '金融機関手続書類', '解約申請書', 'みずほ証券_相続届'),
            os.path.join(self.customer['フォルダパス'], 'みずほ証券_相続届1'),
            os.path.join(self.customer['フォルダパス'], 'みずほ証券_相続届2')
        )


if __name__ == '__main__':
    GlobalValues.code = 'E00287'
    cl = MizuhoSc()
    # cl.balance_certificate()
    cl.inheritance_notification_create()
