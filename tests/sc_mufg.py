### 三菱ＵＦＪモルガン・スタンレー証券
import os.path
import flet as ft
import jaconv
from globalvalues import GlobalValues
from pdf_create import PdfCreate
# from pypdf import PdfReader
from datetime import datetime
import re


class ScMufg(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.inheritance_method = None
        self.page = GlobalValues.my_page

        self.info = ft.Text('＜三菱ＵＦＪモルガン・スタンレー証券＞', size=24)
        self.t_code = ft.Text(size=16)
        self.t_name = ft.Text(size=16)
        sql = 'SELECT * FROM customer WHERE code = ?'
        record = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]
        self.t_code.value = f'被相続人： {GlobalValues.code}'
        # self.t_code.value = f'被相続人： {record[1]}'
        self.t_name.value = f'{record[2]}　{record[3]}'

        # 作成日のフィールドとカレンダー
        self.date_picker_creation_date = ft.DatePicker(
            on_change=self.change_date,
            first_date=datetime.now(),
            data='creation_date',
        )
        self.page.overlay.append(self.date_picker_creation_date)
        self.page.update()
        self.date_button_creation_date = ft.ElevatedButton(
            "作成日",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker_creation_date.pick_date(),
        )
        self.tf_creation_date = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'),
                                             hint_text='1900/1/1', width=200, border_color='GREY', autofocus=True,
                                             on_blur=self.convert_seireki)

        # 2 相続の方法について
        self.rg_inheritance_method = ft.RadioGroup(
            ft.Row([
                ft.Radio(label='遺言書に基づき相続', value='遺言書に基づき相続'),
                ft.Divider(),
                ft.Radio(label='裁判所の審判・調停等に基づき相続', value='裁判所の審判・調停等に基づき相続'),
                ft.Divider(),
                ft.Radio(label='遺産分割協議書に基づき相続', value='遺産分割協議書に基づき相続'),
                ft.Divider(),
                ft.Radio(label='遺言書や遺産分割協議書はない', value='遺言書や遺産分割協議書はない'),
                ft.Divider(),
                ft.Radio(label='その他', value='その他'),
            ]),
            on_change=self.rg_inheritance_method_change
        )
        self.rg_other = ft.TextField(label='その他の内容を入力', width=1000, multiline=True, visible=False,
                                     border_color='GREY')

        # 4 相続資産の分割方法について
        self.rb_division_method = ft.RadioGroup(
            ft.Row([
                ft.Radio(label='法定相続人がいない', value='法定相続人がいない'),
                ft.Divider(),
                ft.Radio(label='当社資産受取人が1名(分割しない)', value='当社資産受取人が1名(分割しない)'),
                ft.Divider(),
                ft.Radio(label='当社資産受取人が複数名いる', value='当社資産受取人が複数名いる'),
                ft.Divider(),
            ]),
            on_change=self.rb_division_method_change
        )
        self.rb_multiple_people = ft.RadioGroup(
            ft.Row([
                ft.Divider(), ft.Divider(), ft.Divider(), ft.Divider(), ft.Divider(),
                ft.Radio(label='①分割する銘柄・数量が確定している', value='①分割する銘柄・数量が確定している'),
                ft.Divider(),
                ft.Radio(label='②割合または金額換算によって分割する', value='②割合または金額換算によって分割する'),
                ft.Divider(),
                ft.Radio(label='左記①②の分割方法が混在する', value='上記①②の分割方法が混在する'),
                ft.Divider(),
            ]),
            visible=False,
            on_change=self.rb_multiple_people_change
        )

        self.rb_disposal_dedicated_account = ft.RadioGroup(
            ft.Row([
                ft.Radio(label='弊社が売却取引・受取手続きを代理', value='弊社が売却取引・受取手続きを代理'),
                ft.Divider(),
                ft.Radio(label='次の相続人が売却取引・受取手続きを委任',
                         value='次の相続人が売却取引・受取手続きを委任'),
                ft.Divider()
            ]),
            on_change=self.rb_disposal_dedicated_account_change
        )
        self.dd_representative = ft.Dropdown(label='代表者名', visible=False)
        sql = 'SELECT username1 || " " username2 FROM heir WHERE code = ? AND(situation = "" OR situation IS NULL)'
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        [self.dd_representative.options.append(ft.dropdown.Option(record)) for record in records]

        # 移管希望日のフィールドとカレンダー
        self.date_picker_transfer_date = ft.DatePicker(
            on_change=self.change_date,
            first_date=datetime.now(),
            data='transfer_date',
        )
        self.page.overlay.append(self.date_picker_transfer_date)
        self.page.update()
        self.date_button_transfer_date = ft.ElevatedButton(
            "移管日",
            icon=ft.icons.CALENDAR_MONTH,
            on_click=lambda _: self.date_picker_transfer_date.pick_date(),
        )
        self.tf_transfer_date = ft.TextField(label='移管日(空欄の場合は可能な限り早い日)',
                                             hint_text='1900/1/1', width=300, border_color='GREY', autofocus=True,
                                             on_blur=self.convert_seireki)

        # 5 相続人と当社相続資産の明細について
        # 行（銘柄）追加ボタン
        self.b_add = ft.ElevatedButton(
            # content=ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.ADD),
                    ft.Text(value="銘柄追加"),
                ]
            ),
            # ),
            on_click=self.add_clicked,
        )

        self.b_add_field = []
        self.detail = ft.Column()
        self.input_field = []
        # self.detail_field = ft.Column()
        self.detail_field = []

        sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND(situation = "" OR situation IS NULL)'
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        heir_names = []
        [heir_names.append(record[0]) for record in records]
        for i, heir_name in enumerate(heir_names):
            self.b_add_field.append(
                ft.ElevatedButton(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.icons.ADD),
                            ft.Text(value="銘柄追加"),
                        ]
                    ),
                    data=i,
                    on_click=self.add_clicked,
                )
            )
            self.detail_field.append(ft.Column())
            self.detail.controls.append(
                ft.Container(
                    ft.Column([
                        ft.Text(value=heir_name, size=18),
                        ft.TextField(label="口座番号", width=150),
                        self.detail_field[i],
                        # self.b_add
                        # self.detail_field,
                        self.b_add_field[i],
                    ]),
                    border=ft.border.all(2, ft.colors.WHITE10),
                    padding=15
                )
            )
            self.input_field.append(InputField(i, self.row_delete))
            self.detail_field[i].controls.append(self.input_field[i])

        # 数量
        # self.detail.controls[1].content.controls[2].controls[0].tf_quantity.value

        # for i, heir_name in enumerate(heir_names):
        #     self.detail.controls[i].self.detail_field.append(self.input_field[i])
            # self.detail.controls[0].content.controls[2]
            # self.detail_field.controls.append(self.input_field[i])

        # 6 相続資産以外から金銭が発生した場合のお受取人
        self.dd_code = ft.Dropdown(label='お受取人名', value='', width=450)
        sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND situation = ""'
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        [self.dd_code.options.append(ft.dropdown.Option(record[0])) for record in records]

        # 7 口座振替で受け取れず、売却専用口座を利用する場合の代理人
        self.rb_agent = ft.RadioGroup(
            ft.Row([
                ft.Radio(label='弊社が売却取引・受取手続きを代理', value='弊社が売却取引・受取手続きを代理'),
                ft.Divider(),
                ft.Radio(label='次の相続人が売却取引・受取手続きを委任',
                         value='次の相続人が売却取引・受取手続きを委任'),
                ft.Divider()
            ]),
            on_change=self.agent_change
        )

        self.dd_receiving_representative = ft.Dropdown(label='代表者名', visible=False)
        sql = 'SELECT username1 || " " || username2 FROM heir WHERE code = ? AND(situation = "" OR situation IS NULL)'
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        [self.dd_receiving_representative.options.append(ft.dropdown.Option(record[0])) for record in records]

        # 作成ボタン
        self.b_create = ft.ElevatedButton(
            content=ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.icons.ADD),
                        ft.Text(value="作成"),
                    ]
                )
            ),
            height=50,
            on_click=self.create_clicked,
        )

    def build(self):
        self.body = ft.Column(
            [
                self.info,
                ft.Row([self.t_code, self.t_name]),
                ft.VerticalDivider(),
                ft.Row([self.tf_creation_date, self.date_button_creation_date]),
                ft.VerticalDivider(),
                ft.Text('■ 相続の方法', size=20),
                ft.Container(
                    ft.Column([
                        self.rg_inheritance_method,
                        self.rg_other
                    ]),
                    border=ft.border.all(2, ft.colors.WHITE10),
                    # border=ft.border.all(2, ft.colors.with_opacity(0.0, ft.colors.PRIMARY)),
                    padding=15
                ),
                ft.VerticalDivider(),
                ft.Text('■ 相続資産の分割方法', size=20),
                ft.Container(
                    ft.Column([
                        self.rb_division_method,
                        self.rb_multiple_people
                    ]),
                    border=ft.border.all(2, ft.colors.WHITE10),
                    padding=15
                ),
                ft.VerticalDivider(),
                ft.Text('■ 相続人と当社相続資産の明細について', size=20),
                # self.b_add,
                ft.Row([self.tf_transfer_date, self.date_button_transfer_date]),
                self.detail,
                ft.VerticalDivider(),
                ft.VerticalDivider(),
                ft.Text('■ 口座振替で受け取れず、売却専用口座を利用する場合の代理人について', size=20),
                self.rb_agent,
                self.dd_receiving_representative,
                ft.VerticalDivider(),
                ft.VerticalDivider(),
                ft.Text('■ 相続資産以外から金銭が発生した場合の受取人について', size=20),
                self.dd_code,
                ft.VerticalDivider(),
                self.b_create
            ]
        )
        GlobalValues.body = self.body
        return self.body

    def convert_seireki(self, e):
        if e.control.value == '':
            return

        wareki_s = e.control.value

        era = {
            'r': '令和',
            'h': '平成',
            's': '昭和',
            't': '大正',
            'm': '明治'
        }

        era_dic = {
            "明治": 1868,
            "大正": 1912,
            "昭和": 1926,
            "平成": 1989,
            "令和": 2019
        }

        tmp = re.findall('[0-9]+', wareki_s)

        if len(tmp) == 2:
            e.control.value = f'{datetime.now().strftime("%Y")}/{tmp[0]}/{tmp[1]}'
            self.update()
            return

        try:
            if wareki_s[0] == 'r' or wareki_s[0] == 'h' or wareki_s[0] == 's' or wareki_s[0] == 't' or wareki_s[
                0] == 'm':
                wareki = era[wareki_s[0]] + tmp[0]
            else:
                wareki = wareki_s
        except Exception as e:
            print(e)

        s = re.match(r'(明治|大正|昭和|平成|令和)([0-9]+|元)', str(wareki))
        if s is None:
            return wareki_s
        y = int(s.group(2)) if s.group(2) != '元' else 1
        e.control.value = f'{era_dic[s.group(1)] + y - 1}/{tmp[1]}/{tmp[2]}'
        self.update()

    def change_date(self, e):
        if e.control.data == 'creation_date':
            self.tf_creation_date.value = str(e.control.value)[:10].replace('-', '/')
        elif e.control.data == 'transfer_date':
            self.tf_transfer_date.value = str(e.control.value)[:10].replace('-', '/')
        self.update()

    def rg_inheritance_method_change(self, e):
        if e.control.value == 'その他':
            self.rg_other.visible = True
            self.rg_other.focus()
        else:
            self.rg_other.visible = False
        self.rg_inheritance_method.data = e.control.value
        self.update()

    def rb_division_method_change(self, e):
        if e.control.value == '当社資産受取人が複数名いる':
            self.rb_multiple_people.visible = True
        else:
            self.rb_multiple_people.visible = False
        self.rb_division_method.data = e.control.value
        self.update()

    def rb_multiple_people_change(self, e):
        self.rb_multiple_people.data = e.control.value

    def rb_disposal_dedicated_account_change(self, e):
        if e.control.value == '次の相続人が売却取引・受取手続きを委任':
            self.dd_representative.visible = True
        else:
            self.dd_representative.visible = False
        self.dd_representative.data = e.control.value
        self.update()

    def add_clicked(self, e):
        self.input_field.append(InputField(e.control.data, self.row_delete))
        self.detail_field[e.control.data].controls.append(self.input_field[len(self.input_field) - 1])
        self.update()

    def row_delete(self, e):
        self.detail_field[e.cnt].controls.remove(e)
        self.update()

    def agent_change(self, e):
        if e.control.value == '弊社が売却取引・受取手続きを代理':
            self.dd_receiving_representative.visible = False
        else:
            self.dd_receiving_representative.visible = True
        e.control.data = e.control.value
        self.update()

    def create_clicked(self, _):
        # reader = PdfReader("./pdf/三菱UFJモルガン・スタンレー証券_相続資産受取依頼書.pdf")
        # dt_now = datetime(
        #     int(self.tf_creation_date.value.split('/')[0]),
        #     int(self.tf_creation_date.value.split('/')[1]),
        #     int(self.tf_creation_date.value.split('/')[2])
        # ).strftime('%Y/%m/%d')

        pdf = PdfCreate(pagesize='A3')

        dt_now = re.findall(r'\d+', self.tf_creation_date.value)
        pdf.draw_string(171, 168, dt_now[0], 9)
        pdf.draw_string(186, 168, dt_now[1], 9)
        pdf.draw_string(197, 168, dt_now[2], 9)

        sql = ('''
            SELECT 
                prefectures || municipalities || townarea || house_number,
                username1 || " " || username2,
                deathday,
                building,
                folder_s_path
            FROM customer
            WHERE code = ?
        ''')
        customer_record = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]

        # 1 被相続人の情報
        if customer_record[3] == "" or customer_record[3] is None:
            pdf.draw_string(169, 147, customer_record[0], 10)
        else:
            pdf.draw_string(169, 149, customer_record[0], 8)
            pdf.draw_string(169, 144, customer_record[3], 8)
        pdf.draw_string(169, 136, customer_record[1], 11)
        deathday = re.findall(r'\d+', customer_record[2])
        pdf.draw_string(246, 135, deathday[0], 11)
        pdf.draw_string(263, 135, deathday[1], 11)
        pdf.draw_string(273, 135, deathday[2], 11)

        # 2 相続の方法について
        # self.rg_inheritance_method.value = '遺産分割協議書に基づき相続'
        if self.rg_inheritance_method.value == '遺言書に基づき相続':
            pdf.draw_string(173.5, 118, '✓', 9)
        elif self.rg_inheritance_method.value == '裁判所の審判・調停等に基づき相続':
            pdf.draw_string(231, 118, '✓', 9)
        elif self.rg_inheritance_method.value == '遺産分割協議書に基づき相続':
            pdf.draw_string(173.5, 112, '✓', 9)
        elif self.rg_inheritance_method.value == '遺言書や遺産分割協議書はない':
            pdf.draw_string(231, 112, '✓', 9)
        elif self.rg_inheritance_method.value == 'その他':
            pdf.draw_string(173.5, 106, '✓', 9)
            pdf.draw_string(186, 106, self.rg_other.value, 8)

        # 3 相続の手続代理人について
        pdf.draw_string(229, 89, '✓', 9)
        pdf.draw_string(174, 80, '✓', 8)
        # pdf.draw_string(216, 75, '✓')
        # pdf.set_font(7)
        # pdf.draw_string(229, 75, '代理人')
        pdf.draw_string(174, 71, 'ｿｳｿﾞｸﾃﾂﾂﾞｷｼｴﾝｾﾝﾀｰﾏﾁﾀﾞﾕｳｹﾞﾝｾｷﾆﾝｼﾞｷﾞｮｳｸﾐｱｲ ｸﾐｱｲｲﾝ ｶﾌﾞｼｷｶｲｼｬﾌﾟﾛﾌｨｯﾄﾜﾝ ｼｮｸﾑｼｯｺｳｼｬ ｵｵﾇｷﾄｼｶｽﾞ', 5)
        pdf.draw_string(174, 66, '相続手続支援センター町田有限責任事業組合組合員', 8)
        pdf.draw_string(174, 62, '株式会社プロフィット・ワン 職務執行者　大貫利一', 8)

        # 4 相続資産の分割方法について
        # self.rb_division_method.value = '当社資産受取人が複数名いる'
        # self.rb_multiple_people.value = '①分割する銘柄・数量が確定している'
        # bool5 = False
        bool6 = False
        bool7 = False
        if self.rb_division_method.value == '法定相続人がいない':
            bool7 = True
            pdf.draw_string(156.5, 43, '✓', 7)
        elif self.rb_division_method.value == '当社資産受取人が1名(分割しない)':
            # bool5 = True
            pdf.draw_string(156.5, 38, '✓', 7)
        elif self.rb_division_method.value == '当社資産受取人が複数名いる':
            pdf.draw_string(156.5, 33, '✓', 7)
            if self.rb_multiple_people.value == '①分割する銘柄・数量が確定している':
                # bool5 = True
                bool6 = True
                pdf.draw_string(160.5, 27, '✓', 7)
            elif self.rb_multiple_people.value == '②割合または金額換算によって分割する':
                bool7 = True
                pdf.draw_string(160.5, 20, '✓', 7)
            elif self.rb_multiple_people.value == '上記①②の分割方法が混在する':
                # bool5 = True
                bool6 = True
                bool7 = True
                pdf.draw_string(160.5, 13, '✓', 7)

        # 6 相続資産以外から金銭が発生した場合のお受取人
        # self.dd_code.value = '丹下　和子'
        if bool6:
            pdf.draw_string(33, 181, self.dd_code.value, 12)

        # 7 口座振替で受け取れず、売却専用口座を利用する場合の代理人
        if bool7:
            if self.rb_agent.value == '弊社が売却取引・受取手続きを代理':
                pdf.draw_string(20, 166, '✓', 7)
            elif self.rb_agent.value == '次の相続人が売却取引・受取手続きを委任':
                pdf.draw_string(20, 161, '✓', 7)
                pdf.draw_string(43, 153, self.dd_receiving_representative.value, 12)

        pdf.pdf_save(output_name='111', marge_pdf="./pdf/三菱UFJモルガン・スタンレー証券_相続資産受取依頼書.pdf", page=1, open_bool=False)

        ### 2ページ目
        pdf2 = PdfCreate(pagesize='A3')
        # sql = ('''
        #     SELECT
        #         username1 || " " || username2,
        #         birthday
        #     FROM heir
        #     WHERE code = ? AND(situation = "" OR situation IS NULL)
        # ''')
        # heir_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        # 5 移管希望日
        if self.tf_transfer_date.value == '':
            pdf2.draw_string(32, 191, '✓', 7)
        else:
            pdf2.draw_string(32, 186, '✓', 7)
            date = re.findall(r'\d+', self.tf_transfer_date.value)
            pdf2.draw_string(43, 186, date[0], 7)
            pdf2.draw_string(56, 186, date[1], 7)
            pdf2.draw_string(65, 186, date[2], 7)

        # 銘柄名を記入
        sql = ('''
            SELECT 
                t3.brand_name
            FROM 
                securities_account AS t1
                    INNER JOIN securities_company AS t2
                    ON t1.securities_code = t2.securities_code
                    AND t1.code = (:code)
                    AND t1.securities_code = (:securities_code)
                        INNER JOIN securities_brand AS t3
                        ON t1.brand_code = t3.brand_code
        ''')
        p = dict(zip(['code', 'securities_code'], [GlobalValues.code, 9532]))
        records = GlobalValues.get_db(sql, p)
        for i, record in enumerate(records):
            # print(len(record[0]))
            if len(record[0]) < 14:
                size = 10
            else:
                size = 8 - len(record[0]) / 14
            pdf2.draw_string(20, 120 - i * 8, record[0], size)
            # pos = pdf2.get_pos(record[0])
            # print(pos)

        cnt = 0
        for i, my_detail in enumerate(self.detail.controls):
            # if i == 0:
            #     my_detail.content.controls[1].value = '67776630'
            # elif i == 2:
            #     my_detail.content.controls[1].value = '18970630'
            # elif i == 3:
            #     my_detail.content.controls[1].value = '18988630'
            # elif i == 4:
            #     my_detail.content.controls[1].value = '18996630'

            # 口座番号が空欄ではない場合
            # ※協議書がない場合は、相続人全員を記入する
            if my_detail.content.controls[1].value != '':
                pdf2.draw_string(72 + cnt * 53.8, 168, my_detail.content.controls[0].value, 12)
                sql = ('''
                    SELECT 
                        username1 || " " || username2,
                        birthday,
                        username1_hurigana || "  " || username2_hurigana
                    FROM heir 
                    WHERE code = (:code)
                    AND username1 = (:username1)
                    AND username2 = (:username2)
                ''')
                p = dict(zip(['code', 'username1', 'username2'], [GlobalValues.code, my_detail.content.controls[0].value.split(" ")[0], my_detail.content.controls[0].value.split(" ")[1]]))
                heir_record = GlobalValues.get_db(sql, p)
                pdf2.draw_string(72 + cnt * 53.8, 176.5, jaconv.hira2kata(heir_record[0][2]), 6)
                birthday = re.findall(r'\d+', heir_record[0][1])
                pdf2.draw_string(71 + cnt * 53.8, 153, birthday[0], 8)
                pdf2.draw_string(82 + cnt * 53.8, 153, birthday[1], 8)
                pdf2.draw_string(89 + cnt * 53.8, 153, birthday[2], 8)

                if my_detail.content.controls[1].value == "":
                    pdf2.draw_string(70 + cnt * 53.8, 139.5, '✓', 8)
                else:
                    pdf2.draw_string(80 + cnt * 53.8, 139.5, '✓', 8)
                    pdf2.draw_string(91 + cnt * 53.8, 137, str(str(my_detail.content.controls[1].value).zfill(10)).zfill(10)[0], 6)
                    pdf2.draw_string(94 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[1], 6)
                    pdf2.draw_string(97 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[2], 6)
                    pdf2.draw_string(100 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[3], 6)
                    pdf2.draw_string(103 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[4], 6)
                    pdf2.draw_string(106 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[5], 6)
                    pdf2.draw_string(109 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[6], 6)
                    pdf2.draw_string(112.5 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[7], 6)
                    pdf2.draw_string(115.5 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[8], 6)
                    pdf2.draw_string(118.5 + cnt * 53.8, 137, str(my_detail.content.controls[1].value).zfill(10)[9], 6)
                    pdf2.draw_string(109 + cnt * 53.8, 132, '✓', 8)

                # 銘柄
                # self.input_field[0].controls[0].controls[0].controls[0].value
                # 数量
                # self.input_field[0].controls[0].controls[0].controls[1].value

                # inputfield数
                # self.detail_field[0].controls
                # self.detail_field[0].controls[0].controls[0].controls[0].controls[0].value 和子1つ目の銘柄
                # self.detail_field[0].controls[1].controls[0].controls[0].controls[0].value 和子2つ目の銘柄
                # for record in my_detail.content.controls[2].controls[0].controls[0].controls:
                # for record in self.detail_field[0].controls[:len(self.detail_field[0].controls)-1]:
                for record in self.detail_field[i].controls:
                    if record.controls[0].controls[0].controls[0].value is not None:
                        pos = pdf2.get_pos(record.controls[0].controls[0].controls[0].value)
                        print(record.controls[0].controls[0].controls[0].value)
                        print(record.controls[0].controls[0].controls[1].value)
                        pdf2.draw_string(20 + (cnt + 1) * 55, pos[1], record.controls[0].controls[0].controls[1].value)

                # for record in my_detail.content.controls[2].controls[0].controls[0].controls[0].controls:
                #     print(record.value)
                #     print(my_detail.content.controls[2].controls[0].controls[0].controls[0].controls[1].value)
                cnt += 1

        pdf2.pdf_save(output_name='222', marge_pdf="./pdf/三菱UFJモルガン・スタンレー証券_相続資産受取依頼書.pdf", page=2, open_bool=False)

        # PDF結合
        # pdf3 = PdfCreate
        pdf.pdf_marge(os.path.join(customer_record[4], '三菱UFJモルガン・スタンレー証券_相続資産受取依頼書'), '111', '222')
        # pdf.pdf_marge(os.path.join(customer_record[4], '金融機関手続', '解約申請書', '三菱UFJモルガン・スタンレー証券_相続資産受取依頼書'), '111', '222')


class InputField(ft.UserControl):
    def __init__(self, i, row_delete):
        super().__init__()
        self.cnt = i

        # 銘柄名
        self.dd_brand_name = ft.Dropdown(label='銘柄名', on_change=self.dd_brand_name_change)
        p = dict(zip(['code', 'securities_code'], [GlobalValues.code, 9532]))
        sql = ('''
            SELECT 
                t3.brand_name
            FROM 
                securities_account AS t1
                INNER JOIN 
                    securities_company AS t2
                    ON t1.securities_code = t2.securities_code
                    AND t1.code = (:code)
                    AND t1.securities_code = (:securities_code)
                        INNER JOIN securities_brand AS t3
                            ON t1.brand_code = t3.brand_code
        ''')
        records = GlobalValues.get_db(sql, p)
        [self.dd_brand_name.options.append(ft.dropdown.Option(s[0])) for s in records]

        # 銘柄コード
        self.tf_brand_code = ft.Text(visible=False)

        # 口数
        self.tf_quantity = ft.TextField(
            label='数量',
            width=200
        )
        self.row_delete = row_delete

    def build(self):
        self.body = ft.Column([
            ft.Row(
                controls=[
                    self.dd_brand_name,
                    self.tf_quantity,
                    ft.IconButton(
                        ft.icons.DELETE_OUTLINE,
                        on_click=self.row_delete_clicked,
                    ),
                ],
            ),
        ])
        return self.body

    # 銘柄名を選択　→　銘柄コードを更新
    def dd_brand_name_change(self, e):
        sql = 'SELECT brand_code FROM securities_brand WHERE brand_name = ?'
        self.tf_brand_code.value = GlobalValues.get_db(sql, tuple([e.control.value]))[0][0]
        self.update()

    def row_delete_clicked(self, e):
        self.row_delete(self)


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
    cl = ScMufg()
    page.add(cl)


if __name__ == '__main__':
    GlobalValues.code = "E00248"
    # cl = ScMufg()
    ft.app(target=main)