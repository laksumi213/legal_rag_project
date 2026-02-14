# みずほ信託　証券代行
import os.path
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from web_operation import Web
# from time import sleep
from datetime import datetime
# import jaconv
import re


class MizuhoTb(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.page = GlobalValues.my_page

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    # 残高証明書
    def balance_certificate(self):
        date = re.findall(r'\d+', datetime.now().strftime('%Y/%m/%d'))
        sql = ('''
            SELECT 
                username1 || " " || username2,
                username1_hurigana || " " || username2_hurigana,
                birthday,
                deathday,
                prefectures || municipalities || townarea || house_number,
                building,
                folder_a_path,
                folder_s_path
            FROM customer 
            WHERE code = ?    
        ''')
        customer_record = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]

        # sql = ('''
        #     SELECT
        #          username1 || " " || username2,
        #          username1_hurigana || " " || username2_hurigana,
        #          prefectures || municipalities || townarea || house_number,
        #          building,
        #          contact_home,
        #          contact_phone
        #     FROM heir
        #     WHERE code = ?
        #     AND legal_heir = 1
        # ''')
        # heir_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))

        pdf = PdfCreate("A4")
        pdf.draw_string(153, 273.5, date[0])
        pdf.draw_string(172, 273.5, date[1])
        pdf.draw_string(186, 273.5, date[2])

        pdf.draw_string(84, 257, '194')
        pdf.draw_string(103, 257, '0022')

        pdf.draw_string(149, 243, '042')
        pdf.draw_string(164, 243, '710')
        pdf.draw_string(179, 243, '6178')

        pdf.draw_string(84, 249, '東京都町田市森野一丁目22番5号', 12)

        pdf.draw_string(80, 231, '相続手続支援センター町田有限責任事業組合　組合員')
        pdf.draw_string(80, 226, '株式会社プロフィット・ワン　職務執行者　大貫利一')

        pdf.draw_string(94, 239,
                      'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 4.7)

        # sql = ('''
        #     SELECT DISTINCT t1.brand_name
        #     FROM securities_brand AS t1
        #         INNER JOIN securities_account AS t2
        #         ON t2.code = ?
        #     WHERE t1.brand_code = (
        #         select brand_code from securities_account WHERE list_caretaker = "みずほ信託銀行" LIMIT 1
        #     )
        # ''')

        sql = ('''
            SELECT brand_name
            FROM securities_brand
                INNER JOIN securities_account
                ON securities_account.brand_code = securities_brand.brand_code
                AND securities_account.code = ?
                AND securities_account.list_caretaker = "みずほ信託銀行"
        ''')
        brand_name_s = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        print('brand_name_s:', brand_name_s)
        buf = ''
        for brand_name in brand_name_s[:3]:
            buf += brand_name[0] + '、'
        buf = buf[:len(buf)-1]
        pdf.draw_string(24, 192, buf + 'を含む全銘柄')

        pdf.draw_string(43, 174, customer_record[4])
        pdf.draw_string(43, 164, customer_record[0])

        pdf.draw_string(22, 136, '✓')
        pdf.draw_string(43, 123, '✓')
        pdf.draw_string(43, 115, '✓')
        pdf.draw_string(43, 110, '✓')
        pdf.draw_string(107, 101, '✓')
        pdf.draw_string(19, 60.5, '✓')

        pdf.draw_string(53, 123, customer_record[3].split('/')[0], 8)
        pdf.draw_string(71, 123, customer_record[3].split('/')[1], 8)
        pdf.draw_string(83, 123, customer_record[3].split('/')[2], 8)

        proc = Web()
        proc.web_open('https://contact.www.mizuho-tb.co.jp/faq/show/85?site_domain=daikou')

        pdf.pdf_save(os.path.join(customer_record[7], '金融機関手続', '残高証明書', '申請書', 'みずほ信託証券代行_残高証明書請求書'),
                     os.path.dirname(__file__) + "/pdf/みずほ信託証券代行_残高証明書請求書.pdf", page=1, open_bool=True)


if __name__ == '__main__':
    GlobalValues.code = '2408030'
    cl = MizuhoTb()
    cl.balance_certificate()
