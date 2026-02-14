###
import flet as ft
from globalvalues import GlobalValues
from pdf_create import PdfCreate
from zengin import BankSearch
from convert_to_wareki import convert_to_wareki2
from datetime import datetime
import jaconv
import re
import os.path


class SagamiShinkin(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.b_add = None
        self.recipient_field = None
        self.recipient = None
        self.delete_items = []
        self.customer = None
        self.page = GlobalValues.my_page

    def build(self):
        pass

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    ### 相続届
    def inheritance_notification(self):
        create_date = ft.TextField(label='作成日', width=150, value=datetime.now().strftime('%Y/%m/%d'))

        # 行追加ボタン
        self.b_add = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.ADD),
                    ft.Text(value="行追加"),
                ]
            ),
            on_click=self.row_add_clicked,
        )

        # 受取人
        self.recipient = ft.Column()
        self.recipient.controls.append(InputField(self.row_delete))

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('さがみ信金の手続き'),
            content=ft.Column(
                [
                    create_date,
                    ft.VerticalDivider(),
                    ft.Column([
                        self.recipient,
                        self.b_add,
                    ]),
                    # ft.Container(
                    #     ft.Column([
                    #         self.recipient,
                    #         self.b_add,
                    #     ]),
                    #     border=ft.border.all(2, ft.colors.WHITE10),
                    #     padding=15
                    # ),
                ],
                height=450,
                width=200,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True,
                                       on_click=lambda e: self.inheritance_notification_create(create_date.value)),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def inheritance_notification_create(self, e):
        self.close_dlg(self)
        dt = re.findall('[0-9]+', convert_to_wareki2(e))
        pdf = PdfCreate("A3")
        # sql = (f'''
        #     SELECT
        #         t1.folder_s_path AS フォルダパス,
        #         t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
        #         t1.username1 || "  " || t1.username2 AS 被相続人,
        #         t1.deathday AS 死亡日,
        #         t2.branch_code AS 店番号,
        #         t2.bank_number AS 口座番号,
        #         t2.deposit_type AS 種類,
        #         t3.bank_branch_name AS 支店名,
        #         t4.username1 || "  " || t4.username2 AS 相続人
        #     FROM customer AS t1
        #         INNER JOIN bank_customer AS t2
        #         ON t1.code = t2.code
        #         AND t2.jba_code = "1288"
        #             INNER JOIN bank_branch AS t3
        #             ON t3.bank_branch_code = t2.branch_code
        #             AND t3.jba_code = "1288"
        #                 INNER JOIN heir AS t4
        #                 ON t1.code = t4.code
        #                 AND t4.situation = ""
        #     WHERE t1.code = ?
        # ''')

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
                AND t2.jba_code = "1288"
                    INNER JOIN bank_branch AS t3
                    ON t3.bank_branch_code = t2.branch_code
                    AND t3.jba_code = "1288"
            WHERE t1.code = ?
        ''')
        self.customer = GlobalValues.get_db(sql, tuple([GlobalValues.code]), True)
        print('self.customer: ', GlobalValues.get_db(sql, tuple([GlobalValues.code])))

        sql = (f'''
            SELECT
                heir.prefectures || heir.municipalities || heir.townarea || heir.house_number AS 相続人住所,
                heir.building AS 相続人建物名,
                heir.username1_hurigana || "  " || heir.username2_hurigana AS 相続人かな,
                heir.username1 || "  " || heir.username2 AS 相続人,
                heir.contact_home AS 自宅電話,
                heir.contact_phone AS 携帯電話,
                heir.birthday AS 相続人_生年月日,
                heir_bank.branch_code AS 振込先支店コード,
                heir_bank.bank_number AS 振込先口座番号,
                bank_customer.branch_code AS 解約支店コード,
                bank_customer.bank_number AS 解約口座番号
            FROM heir
                INNER JOIN heir_bank
                ON heir_bank.bank_customer_id = bank_customer.bank_customer_id
                    INNER JOIN bank_customer
                    ON heir.code = bank_customer.code
                    AND bank_customer.code = "{GlobalValues.code}" 
                    AND bank_customer.jba_code = 1288
                        INNER JOIN customer
                        ON customer.code = "{GlobalValues.code}"
            WHERE heir.situation = ''
        ''')
        self.heir = GlobalValues.get_db(sql, row_factory=True)
        print('self.heir: ', GlobalValues.get_db(sql=sql))

        pdf.draw_string(115, 188, dt[0])
        pdf.draw_string(125, 188, dt[1])
        pdf.draw_string(134, 188, dt[2])

        deathday = re.findall(r'\d+', convert_to_wareki2(self.customer[0]["死亡日"]))
        if convert_to_wareki2(self.customer[0]["死亡日"])[0:2] == '令和':
            pdf.draw_string(92, 182.5, '〇')
        elif convert_to_wareki2(self.customer[0]["死亡日"])[0:2] == '平成':
            pdf.draw_string(86, 182.5, '〇')
        pdf.draw_string(97, 183, deathday[0], 8)
        pdf.draw_string(105, 183, deathday[1], 8)
        pdf.draw_string(112, 183, deathday[2], 8)
        pdf.draw_string(63, 174, self.customer[0]['被相続人'], 14)

        row = 0
        col = 0
        for i, heir in enumerate(self.heir):
            pdf.draw_string(22 + col, 167 - row * 23.2, '〇')
            pdf.draw_string(18 + col, 161 - row * 23.2, heir['相続人住所'], 8)
            pdf.draw_string(25 + col, 157 - row * 23.2, heir['相続人建物名'], 8)
            pdf.draw_string(18 + col, 151 - row * 23.2, heir['相続人'])
            # print(customer['相続人'])
            # print(str(customer['口座番号']).zfill(7))
            if i == 3:
                row = 0
                col = 64
            else:
                row += 1

        print('i:', i)
        row = 81
        if i < 3:
            col = 161
        elif i == 3:
            col = 137
        elif i == 4:
            col = 114

        pdf.draw_string(row + 37, col + 6, f'左記 相続人{i + 1}名 代理人', 4.5)
        pdf.draw_string(row, col, '東京都町田市森野一丁目22番5号', 8)
        pdf.draw_string(row, col - 7, '相続手続支援センター町田有限責任事業組合　組合員', 6)
        pdf.draw_string(row, col - 11, '株式会社プロフィット・ワン　職務執行者　大貫利一', 6)

        pdf.draw_string(103, 96, '042-710-6178', 8)
        pdf.draw_string(103, 91, '税理士　大貫利一', 10)

        # 2 相続預金一覧
        for i, customer in enumerate(self.customer):
            if '普通' in customer['種類']:
                pdf.draw_string(155, 187 - i * 9.4, '〇', 12)
            elif '定期' in customer['種類']:
                pdf.draw_string(155, 184 - i * 9.4, '〇', 12)

            pdf.draw_string(169, 183 - i * 9.4, str(customer['店番号']).zfill(3), 8)
            pdf.draw_string(181, 183 - i * 9.4, str(customer['口座番号']).zfill(7), 8)
            pdf.draw_string(208, 186 - i * 9.4, '〇', 12)

        # 3 お受け取り方法
        for i, recipient in enumerate(self.recipient.controls):
            sql = (f'''
                SELECT
                    heir.username1_hurigana || "  " || heir.username2_hurigana AS 相続人かな,
                    heir.username1 || "  " || heir.username2 AS 相続人,
                    heir_bank.jba_code AS 振込先銀行コード,
                    heir_bank.branch_code AS 振込先支店コード,
                    heir_bank.bank_number AS 振込先口座番号,
                    heir_bank.subjects AS 種類
                FROM heir
                    INNER JOIN heir_bank
                    ON heir_bank.bank_customer_id = bank_customer.bank_customer_id
                        INNER JOIN bank_customer
                        ON heir.code = bank_customer.code
                        AND bank_customer.code = "{GlobalValues.code}" 
                        AND bank_customer.jba_code = 1288
                            INNER JOIN customer
                            ON customer.code = "{GlobalValues.code}"
                WHERE heir.username1 || heir.username2 = ?
            ''')
            self.heir_bank = GlobalValues.get_db(sql, tuple([recipient.dd_heir.value.replace(" ", "")]), True)[0]
            print(GlobalValues.get_db(sql, tuple([recipient.dd_heir.value.replace(" ", "")]), False)[0])

            pdf.draw_string(160, 38 - i * 14, jaconv.hira2kata(self.heir_bank['相続人かな']), 6)
            pdf.draw_string(160, 33 - i * 14, self.heir_bank['相続人'])

            bank_name = [(bank_name, bank_code) for bank_name, bank_code in
                         BankSearch.bank_search(code=str(self.heir_bank['振込先銀行コード']).zfill(4))][0]
            print('bank_name:', bank_name)
            pdf.draw_string(200, 36 - i * 14, bank_name[0])

            branch_name = [(branch_code, branch_name) for branch_code, branch_name in
                           BankSearch.branch_search(bank_code=str(self.heir_bank['振込先銀行コード']).zfill(4),
                                                    code=str(self.heir_bank['振込先支店コード']).zfill(3))][0]
            print('branch_name:', branch_name)
            pdf.draw_string(222, 36 - i * 14, branch_name[1])

            if '普通' in self.heir_bank['種類']:
                pdf.draw_string(245, 38 - i * 12, '〇', 12)
            else:
                pdf.draw_string(245, 36 - i * 13, self.heir_bank['種類'])

            pdf.draw_string(259, 36 - i * 14, str(self.heir_bank['振込先口座番号']).zfill(7))

        pdf.pdf_save(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'さがみ信用金庫_相続届'),
            "./pdf/さがみ信用金庫_相続届.pdf", page=1, open_bool=True)

    def row_add_clicked(self, e):
        elm = InputField(self.row_delete)
        self.recipient.controls.append(elm)
        self.recipient.update()
        elm.dd_heir.focus()
        # self.detail_field[e.control.data].controls.append(self.input_field[len(self.input_field) - 1])
        # self.update()

    def row_delete(self, e):
        self.delete_items.append(e)
        self.recipient.controls.remove(e)
        self.update()


class InputField(ft.UserControl):
    def __init__(self, row_delete):
        super().__init__()
        self.body = None
        self.row_delete = row_delete

        sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND(situation = "" OR situation = " " OR situation IS NULL)'
        self.heirs = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        self.dd_heir = ft.Dropdown(label='振込先相続人', width=150, on_change=self.dd_heir_change)
        [self.dd_heir.options.append(ft.dropdown.Option(heir[0])) for heir in self.heirs]

    def build(self):
        self.body = ft.Column([
            ft.Row(
                controls=[
                    self.dd_heir,
                    ft.IconButton(
                        ft.icons.DELETE_OUTLINE,
                        on_click=self.row_delete,
                    ),
                ],
            ),
        ])

        # self.body = ft.Row(
        #     controls=[
        #         self.dd_heir,
        #         ft.IconButton(
        #             ft.icons.DELETE_OUTLINE,
        #             on_click=self.row_delete,
        #         ),
        #     ],
        # )

        return self.body

    def row_delete(self, e):
        self.row_delete(self)

    def dd_heir_change(self, e):
        pass


def main(page: ft.Page):
    GlobalValues.code = "E00286"
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = SagamiShinkin()
    page.add(cl)
    cl.inheritance_notification()


if __name__ == '__main__':
    ft.app(target=main)
