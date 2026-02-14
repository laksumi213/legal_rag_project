import flet as ft
from globalvalues import GlobalValues
from datetime import datetime
from pdf_create import PdfCreate
from zengin import BankSearch
import jaconv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
import time
import signal
import os


class my_RadioGroup(ft.UserControl):
    def __init__(self, label, value='有'):
        super().__init__()
        self.label = label
        self.value = value

    def build(self):
        return ft.Column(
            [
                ft.Text(value=self.label),
                ft.RadioGroup(
                    content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無')]),
                    value=self.value,
                    data=re.findall(r'\d+', self.label)[0]
                ),
            ]
        )


class KiraboshiBank(ft.UserControl):
    def __init__(self):
        super().__init__()
        self.rg_bankbook1 = None
        self.page = GlobalValues.my_page

    def close_dlg(self, e):
        self.page.dialog.open = False
        self.page.update()

    # 口座凍結連絡　手続き選択
    def account_freezing(self):
        self.t_overseas = ft.Text('海外居住の相続人')
        self.rg_overseas = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.t_adult_guardian = ft.Text('成年後見制度利用者')
        self.rg_adult_guardian = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.t_unknown_heir = ft.Text('行方不明の相続人')
        self.rg_unknown_heir = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.t_minor = ft.Text('未成年者の相続人')
        self.rg_minor = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.t_inheritance_abandonment = ft.Text('相続放棄した方')
        self.rg_inheritance_abandonment = ft.RadioGroup(
            value='無',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

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

        self.t_balance_certificate = ft.Text('相続用残高証明書発行希望')
        self.rg_balance_certificate = ft.RadioGroup(
            value='',
            content=ft.Row([ft.Radio(value='有', label='有'), ft.Radio(value='無', label='無'), ]),
        )

        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('きらぼし銀行の口座凍結連絡手続き'),
            content=ft.Column(
                [
                    self.t_overseas,
                    self.rg_overseas,
                    ft.VerticalDivider(),
                    self.t_adult_guardian,
                    self.rg_adult_guardian,
                    ft.VerticalDivider(),
                    self.t_unknown_heir,
                    self.rg_unknown_heir,
                    ft.VerticalDivider(),
                    self.t_minor,
                    self.rg_minor,
                    ft.VerticalDivider(),
                    # self.t_inheritance_abandonment,
                    # self.rg_inheritance_abandonment,
                    # ft.VerticalDivider(),
                    self.t_discussed_document,
                    self.rg_discussed_document,
                    ft.VerticalDivider(),
                    self.t_will,
                    self.rg_will,
                    ft.VerticalDivider(),
                    self.t_will_execution_person,
                    self.rg_will_execution_person,
                    ft.VerticalDivider(),
                    self.t_conciliation_or_judge,
                    self.rg_conciliation_or_judge,
                    ft.VerticalDivider(),
                    self.t_balance_certificate,
                    self.rg_balance_certificate
                ],
                height=1000,
            ),
            actions=[ft.ElevatedButton(text="OK", on_click=self.account_freezing_create),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    # 口座凍結連絡　作成
    def account_freezing_create(self, e):
        self.close_dlg(self)
        self.page.update()
        sql = ('''
            SELECT
                username1,
                username2,
                username1_hurigana,
                username2_hurigana,
                birthday,
                deathday,
                zipcode,
                prefectures,
                municipalities,
                townarea,
                house_number,
                building
            FROM
                customer
            WHERE
                code = ?
        ''')
        customer_rec = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]

        sql = ('''
            SELECT 
                bank_number,
                branch_code,
                deposit_type
            FROM bank_customer
            WHERE jba_code = "0137"
            AND code = ?
        ''')
        customer_bank = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]

        try:
            # options = Options()
            bw = webdriver.Chrome()
            bw.maximize_window()
            bw.implicitly_wait(3)
            bw.get("https://faq-kiraboshibank.dga.jp/form/inheritance.html")

            # 確認しました
            bw.find_element(By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div[1]/div[3]/label").click()
            bw.find_element(By.XPATH, "/html/body/div[1]/div/div[3]/div/div/div[1]/div[2]/div[3]/label").click()

            ## 1.被相続人さま（お亡くなりになられた方）について
            # 氏名
            bw.find_element(By.NAME, 'inquiry_101_1').send_keys(customer_rec[0])
            bw.find_element(By.NAME, 'inquiry_101_2').send_keys(customer_rec[1])
            bw.find_element(By.NAME, 'inquiry_102_1').send_keys(jaconv.hira2kata(customer_rec[2]))
            bw.find_element(By.NAME, 'inquiry_102_2').send_keys(jaconv.hira2kata(customer_rec[3]))

            # 郵便番号
            bw.find_element(By.NAME, 'inquiry_2_1').send_keys(customer_rec[6][0:3])
            bw.find_element(By.NAME, 'inquiry_2_2').send_keys(customer_rec[6][4:])
            bw.find_element(By.XPATH,
                            "/html/body/div[1]/div/div[3]/div/div/form/table[1]/tbody/tr[3]/td/div/ul/li/button/span").click()
            time.sleep(0.5)

            # 住所
            bw.find_element(By.NAME, 'inquiry_103').send_keys(customer_rec[10] + customer_rec[11])

            # 生年月日
            birth = re.findall(r'\d+', customer_rec[4])
            bw.find_element(By.NAME, 'inquiry_104').send_keys(
                f'{birth[0]}{str(birth[1]).zfill(2)}{str(birth[2]).zfill(2)}')

            # 死亡日
            death = re.findall(r'\d+', customer_rec[5])
            bw.find_element(By.NAME, 'inquiry_105').send_keys(
                f'{death[0]}{str(death[1]).zfill(2)}{str(death[2]).zfill(2)}')

            # 支店番号
            bw.find_element(By.NAME, 'inquiry_106_1').send_keys(str(customer_bank[1]).zfill(3))

            # 科目
            if '普通' in customer_bank[2]:
                Select(bw.find_element(By.NAME, "inquiry_106_2")).select_by_visible_text('普通預金')
            elif '積金' in customer_bank[2]:
                Select(bw.find_element(By.NAME, "inquiry_106_2")).select_by_visible_text('定期積金')
            elif '定期' in customer_bank[2]:
                Select(bw.find_element(By.NAME, "inquiry_106_2")).select_by_visible_text('定期預金')
            elif '当座' in customer_bank[2]:
                Select(bw.find_element(By.NAME, "inquiry_106_2")).select_by_visible_text('当座預金')
            else:
                Select(bw.find_element(By.NAME, "inquiry_106_2")).select_by_visible_text('その他')

            # 口座番号
            bw.find_element(By.NAME, 'inquiry_106_3').send_keys(str(customer_bank[0]).zfill(7))

            ## 2.ご入力者さまについて (ご入力者さまが原則、相続手続代表者さまとなります。）
            # 氏名
            bw.find_element(By.NAME, 'inquiry_107_1').send_keys(
                GlobalValues.get_config(GlobalValues, os.getlogin(), 'family_name'))
            bw.find_element(By.NAME, 'inquiry_107_2').send_keys(
                GlobalValues.get_config(GlobalValues, os.getlogin(), 'name'))
            bw.find_element(By.NAME, 'inquiry_108_1').send_keys(
                GlobalValues.get_config(GlobalValues, os.getlogin(), 'family_name_huri'))
            bw.find_element(By.NAME, 'inquiry_108_2').send_keys(
                GlobalValues.get_config(GlobalValues, os.getlogin(), 'name_huri'))

            # メールアドレス
            bw.find_element(By.NAME, 'inquiry_5_1').send_keys(
                GlobalValues.get_config(GlobalValues, os.getlogin(), 'mail'))
            bw.find_element(By.NAME, 'inquiry_5_2').send_keys(
                GlobalValues.get_config(GlobalValues, os.getlogin(), 'mail'))

            # 郵便番号
            bw.find_element(By.NAME, 'inquiry_109_1').send_keys('194')
            bw.find_element(By.NAME, 'inquiry_109_2').send_keys('0022')
            bw.find_element(By.XPATH,
                            "/html/body/div[1]/div/div[3]/div/div/form/table[2]/tbody/tr[4]/td/div/span/button/span").click()
            time.sleep(0.5)

            # 住所
            bw.find_element(By.NAME, 'inquiry_111').send_keys('一丁目22番5号 町田310五十子ビル3F')

            # 電話番号
            bw.find_element(By.NAME, 'inquiry_4_1').send_keys('042')
            bw.find_element(By.NAME, 'inquiry_4_2').send_keys('710')
            bw.find_element(By.NAME, 'inquiry_4_3').send_keys('6178')

            # 電話OKな時間帯
            Select(bw.find_element(By.NAME, "inquiry_112")).select_by_visible_text('希望なし')

            # 間柄
            Select(bw.find_element(By.NAME, "inquiry_113")).select_by_visible_text('その他')

            ## 3.相続関係の基本情報について
            # 配偶者
            sql = "SELECT COUNT(*) FROM heir WHERE code = ? AND situation != '死亡' AND(relationship = '妻' OR relationship = '夫')"
            spouse_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if spouse_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_1")).select_by_visible_text('配偶者あり')
            else:
                Select(bw.find_element(By.NAME, "inquiry_114_1")).select_by_visible_text('配偶者なし')

            # 子ども
            sql = "SELECT COUNT(*) FROM heir WHERE code = ? AND situation != '死亡' AND(relationship LIKE '%男' OR relationship LIKE '%女') AND relationship NOT LIKE '%孫%'"
            children_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if children_count == 0:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供なし')
            elif children_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供1名')
            elif children_count == 2:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供2名')
            elif children_count == 3:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供3名')
            elif children_count == 4:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供4名')
            elif children_count == 5:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供5名')
            elif children_count >= 6:
                Select(bw.find_element(By.NAME, "inquiry_114_2")).select_by_visible_text('子供6名以上')

            # 孫
            sql = "SELECT COUNT(*) FROM heir WHERE code = ? AND situation != '死亡' AND relationship LIKE '%孫%'"
            grandchild_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if grandchild_count == 0:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫なし')
            elif grandchild_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫1名')
            elif grandchild_count == 2:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫2名')
            elif grandchild_count == 3:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫3名')
            elif grandchild_count == 4:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫4名')
            elif grandchild_count == 5:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫5名')
            elif grandchild_count >= 6:
                Select(bw.find_element(By.NAME, "inquiry_114_3")).select_by_visible_text('孫6名以上')

            # 父母
            sql = "SELECT COUNT(*) FROM heir WHERE code = ? AND situation != '死亡' AND(relationship LIKE '%父%' OR relationship LIKE '%母%')"
            parents_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if parents_count == 0:
                Select(bw.find_element(By.NAME, "inquiry_114_4")).select_by_visible_text('父母なし')
            elif parents_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_4")).select_by_visible_text('父母1名')
            elif parents_count == 2:
                Select(bw.find_element(By.NAME, "inquiry_114_4")).select_by_visible_text('父母2名')
            elif parents_count == 3:
                Select(bw.find_element(By.NAME, "inquiry_114_4")).select_by_visible_text('父母3名')
            elif parents_count == 4:
                Select(bw.find_element(By.NAME, "inquiry_114_4")).select_by_visible_text('父母4名')

            # 祖父母
            sql = "SELECT COUNT(*) FROM heir WHERE code = ? AND situation != '死亡' AND(relationship LIKE '%祖父%' OR relationship LIKE '%祖母%')"
            old_parents_spouse_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if old_parents_spouse_count == 0:
                Select(bw.find_element(By.NAME, "inquiry_114_5")).select_by_visible_text('祖父母なし')
            elif old_parents_spouse_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_5")).select_by_visible_text('祖父母1名')
            elif old_parents_spouse_count == 2:
                Select(bw.find_element(By.NAME, "inquiry_114_5")).select_by_visible_text('祖父母2名')
            elif old_parents_spouse_count == 3:
                Select(bw.find_element(By.NAME, "inquiry_114_5")).select_by_visible_text('祖父母3名')
            elif old_parents_spouse_count == 4:
                Select(bw.find_element(By.NAME, "inquiry_114_5")).select_by_visible_text('祖父母4名')

            # 兄弟姉妹
            sql = "SELECT COUNT(*) FROM Heir WHERE code = ? AND situation != '死亡' AND(relationship LIKE '%兄弟' OR relationship LIKE '%姉妹') AND relationship NOT LIKE '%孫%'"
            brother_sister_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if brother_sister_count == 0:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹なし')
            elif brother_sister_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹1名')
            elif brother_sister_count == 2:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹2名')
            elif brother_sister_count == 3:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹3名')
            elif brother_sister_count == 4:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹4名')
            elif brother_sister_count == 5:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹5名')
            elif brother_sister_count >= 6:
                Select(bw.find_element(By.NAME, "inquiry_114_6")).select_by_visible_text('兄弟姉妹6名以上')

            # 甥姪
            sql = "SELECT COUNT(*) FROM Heir WHERE code = ? AND situation != '死亡' AND(relationship LIKE '%甥' OR relationship LIKE '%姪') AND relationship NOT LIKE '%孫%'"
            nephew_niece_count = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0][0]
            if nephew_niece_count == 0:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪なし')
            elif nephew_niece_count == 1:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪1名')
            elif nephew_niece_count == 2:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪2名')
            elif nephew_niece_count == 3:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪3名')
            elif nephew_niece_count == 4:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪4名')
            elif nephew_niece_count == 5:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪5名')
            elif nephew_niece_count >= 6:
                Select(bw.find_element(By.NAME, "inquiry_114_7")).select_by_visible_text('甥姪6名以上')

            # 合計
            bw.find_element(By.NAME, 'inquiry_114_10').send_keys(
                spouse_count + children_count + grandchild_count + parents_count + old_parents_spouse_count + brother_sister_count + nephew_niece_count)

            sql = "SELECT situation FROM heir WHERE code = ?"
            heir_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))

            # 海外居住の相続人
            if self.rg_overseas.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_115_1")).select_by_visible_text('海外居住の相続人なし')
            elif self.rg_overseas.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_115_1")).select_by_visible_text('海外居住の相続人あり')

            # 成年後見制度利用者
            if self.rg_adult_guardian.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_115_2")).select_by_visible_text('成年後見制度利用者なし')
            elif self.rg_adult_guardian.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_115_2")).select_by_visible_text('成年後見制度利用者あり')

            # 行方不明の相続人
            if self.rg_unknown_heir.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_115_3")).select_by_visible_text('行方不明の相続人なし')
            elif self.rg_unknown_heir.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_115_3")).select_by_visible_text('行方不明の相続人あり')

            # 未成年者の相続人
            if self.rg_minor.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_115_4")).select_by_visible_text('未成年者の相続人なし')
            elif self.rg_minor.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_115_4")).select_by_visible_text('未成年者の相続人あり')

            # 相続放棄した方
            bool = 0
            for heir_record in heir_records:
                if heir_record[0] == '相続放棄':
                    bool = 1

            if bool == 1:
                Select(bw.find_element(By.NAME, "inquiry_115_5")).select_by_visible_text('相続放棄した方あり')
                bool = 0
            else:
                Select(bw.find_element(By.NAME, "inquiry_115_5")).select_by_visible_text('相続放棄した方なし')

            # 遺産分割協議書
            if self.rg_discussed_document.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_116_1")).select_by_visible_text('遺産分割協議書なし')
            elif self.rg_discussed_document.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_116_1")).select_by_visible_text('遺産分割協議書あり')

            # 遺言書
            if self.rg_will.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_116_2")).select_by_visible_text('遺言書なし')
            elif self.rg_will.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_116_2")).select_by_visible_text('遺言書あり')

            # 遺言執行者
            if self.rg_will_execution_person.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_116_3")).select_by_visible_text('遺言執行者なし')
            elif self.rg_will_execution_person.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_116_3")).select_by_visible_text('遺言執行者あり')

            # 家庭裁判所による遺産分割調停又は審判
            if self.rg_conciliation_or_judge.value == '無':
                Select(bw.find_element(By.NAME, "inquiry_116_4")).select_by_visible_text(
                    '家庭裁判所による遺産分割調停又は審判なし')
            elif self.rg_conciliation_or_judge.value == '有':
                Select(bw.find_element(By.NAME, "inquiry_116_4")).select_by_visible_text(
                    '家庭裁判所による遺産分割調停又は審判あり')

            ## ４.その他確認事項について
            # 屋号付きのお口座　→　なし

            # 残高証明書の発行希望有無
            if self.rg_balance_certificate.value == '無':
                bw.find_element(By.XPATH, '//*[@id="inquiry_item118"]/div/ul/li[1]/label/span').click()
            elif self.rg_balance_certificate.value == '有':
                bw.find_element(By.XPATH, '//*[@id="inquiry_item118"]/div/ul/li[2]/label/span').click()

            # 通帳等が揃っているか　→　不明で統一
            bw.find_element(By.XPATH, '//*[@id="inquiry_item119"]/div/ul/li[3]/label/span').click()

            # 確認ボタンクリック
            bw.find_element(By.XPATH, '//*[@id="isfw_inquiry"]/div[3]/div/div/form/div[4]/ul/li/button/span').click()

        finally:
            os.kill(bw.service.process.pid, signal.SIGTERM)

    # 残高証明書
    def balance_certificate(self):
        self.create_date = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'))
        self.page = GlobalValues.my_page
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('きらぼし銀行の残高証明書'),
            content=ft.Column(
                [
                    self.create_date,
                ],
                height=100,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True,
                                       on_click=self.balance_certificate_create),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def balance_certificate_create(self, e):
        self.close_dlg(self)
        sql = (f'''
           SELECT
               t1.folder_s_path AS フォルダパス,
               t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
               t1.username1 || "  " || t1.username2 AS 被相続人,
               t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || t1.building AS 被相続人住所,
               t1.deathday AS 死亡日,
               t2.branch_code AS 店番号,
               t2.bank_number AS 口座番号,
               t2.deposit_type AS 種類,
               t3.bank_branch_name AS 支店名,
               (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
               t4.username1 || "  " || t4.username2 AS 相続人,
               t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな,
               (SELECT username1 || "  " || username2 FROM heir WHERE code = "{GlobalValues.code}" AND offer = 1) AS 代表相続人
           FROM customer AS t1
               INNER JOIN bank_customer AS t2
               ON t1.code = t2.code
               AND t2.jba_code = "0137"
                   INNER JOIN bank_branch AS t3
                   ON t3.bank_branch_code = t2.branch_code
                       INNER JOIN heir AS t4
                       ON t4.code = t1.code
                       AND t4.code = "{GlobalValues.code}"
           WHERE t1.code = "{GlobalValues.code}"
        ''')
        self.customer = GlobalValues.get_db(sql, row_factory=True)

        if self.customer == []:
            sql = (f'''
               SELECT
                   t1.folder_s_path AS フォルダパス,
                   t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
                   t1.username1 || "  " || t1.username2 AS 被相続人,
                   t1.prefectures || t1.municipalities || t1.townarea || t1.house_number || t1.building AS 被相続人住所,
                   t1.deathday AS 死亡日,
                   (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
                   t4.username1 || "  " || t4.username2 AS 相続人,
                   t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな,
                   (SELECT username1 || "  " || username2 FROM heir WHERE code = "{GlobalValues.code}" AND offer = 1) AS 代表相続人
               FROM customer AS t1
                   INNER JOIN heir AS t4
                   ON t4.code = t1.code
                   AND t4.code = "{GlobalValues.code}"
               WHERE t1.code = "{GlobalValues.code}"
            ''')
            self.customer = GlobalValues.get_db(sql, row_factory=True)

        pdf = PdfCreate("A4")

        # 日付
        if self.create_date.value != '':
            pdf.draw_string(135, 271.5, self.create_date.value[0:4])
            pdf.draw_string(157, 271.5, self.create_date.value[5:7])
            pdf.draw_string(172, 271.5, self.create_date.value[8:])

        pdf.draw_string(80, 265.5, str(self.customer[0]['支店名']).replace('支店', ''), 12)
        # try:
        #     pdf.draw_string(80, 265.5, str(self.customer[0]['支店名']).replace('支店', ''), 12)
        #     bln = 0
        #     for i, customer in enumerate(self.customer):
        #         if '定期' in customer['種類']:
        #             bln = 1
        #             break
        #
        #     # 経過利息
        #     if bln == 1:
        #         pdf.draw_string(40.5, 96, '✓', 12)  # 必要にチェック
        #         pdf.draw_string(51.5, 91, '✓', 12)  # 定期預金にチェック
        #     else:
        #         pdf.draw_string(40, 87, '✓', 12)  # 不要
        # except Exception as e:
        #     print(e)
        #     # 経過利息
        #     pdf.draw_string(40.5, 96, '✓', 12)  # 必要にチェック
        #     pdf.draw_string(51.5, 91, '✓', 12)  # 定期預金にチェック

        pdf.draw_rect(140, 255, 152, 260)  # その他にチェック
        # pdf.draw_rect(142, 260, 154, 265)   # その他にチェック
        pdf.draw_string(157, 255.5, '相続人代理人')
        # pdf.draw_string(160, 261, '相続人代理人')
        pdf.draw_string(105, 245, '194-0022')
        pdf.draw_string(105, 237, '東京都町田市森野一丁目22番5号')
        # pdf.draw_string(100, 250, '東京都町田市森野一丁目22番5号')
        pdf.draw_string(100, 230, f'相続人　{self.customer[0]["代表相続人"]}　代理人', 8)
        # pdf.draw_string(100, 239, f'相続人　{self.customer[0]["代表相続人"]}　代理人', 8)
        pdf.draw_string(100, 226, '相続手続支援センター町田有限責任事業組合　組合員', 8)
        # pdf.draw_string(100, 235, '相続手続支援センター町田有限責任事業組合　組合員', 8)
        pdf.draw_string(100, 222, '株式会社プロフィット・ワン　職務執行者　大貫利一', 8)
        # pdf.draw_string(100, 231, '株式会社プロフィット・ワン　職務執行者　大貫利一', 8)
        pdf.draw_string(100, 213, self.customer[0]['被相続人'])
        # pdf.draw_string(100, 217, self.customer[0]['被相続人'])
        deathday = re.findall('[0-9]+', self.customer[0]['死亡日'])
        # deathday = re.findall('[0-9]+', self.customer[0]['死亡日'])
        pdf.draw_string(140, 213, deathday[0])
        # pdf.draw_string(143, 216, deathday[0])
        pdf.draw_string(157, 213, deathday[1])
        # pdf.draw_string(160, 216, deathday[1])
        pdf.draw_string(172, 213, deathday[2])
        # pdf.draw_string(175, 216, deathday[2])
        pdf.draw_string(40.5, 175.5, '✓', 12)  # 全ての取引
        # pdf.draw_string(39.5, 177.5, '✓', 12)
        pdf.draw_string(104.8, 130, '✓', 12)  # 取引の口座番号毎の残高
        # 証明日
        # pdf.draw_string(99.5, 115, '✓', 12)
        pdf.draw_string(53, 120.4, deathday[0])
        # pdf.draw_string(43, 100, deathday[0])
        pdf.draw_string(72, 120.4, deathday[1])
        # pdf.draw_string(65, 100, deathday[1])
        pdf.draw_string(87, 120.4, deathday[2])
        # pdf.draw_string(78, 100, deathday[2])
        pdf.draw_string(59, 111, '1')
        # pdf.draw_string(56, 85, '1')
        pdf.draw_string(40.5, 78, '✓', 12)  # 郵送する住所

        os.makedirs(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書'),
                    exist_ok=True)

        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '残高証明書', '申請書',
                                  'きらぼし銀行_残高証明書依頼書'),
                     os.path.dirname(__file__) + "/pdf/きらぼし銀行_残高証明書依頼書.pdf", page=1, open_bool=True)

    ### 相続届
    def inheritance_notification(self):
        create_date = ft.TextField(label='作成日', value=datetime.now().strftime('%Y/%m/%d'))
        self.lv = ft.ListView(expand=20, spacing=20, padding=0)
        sql = 'SELECT bank_number FROM bank_customer WHERE code = ? AND jba_code = "0137"'
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        for record in records:
            self.lv.controls.append(my_RadioGroup(label=f'口座番号:{record[0]}　通帳有無'))
        self.page = GlobalValues.my_page
        self.page.dialog = ft.AlertDialog(
            open=True,
            modal=True,
            title=ft.Text('きらぼし銀行の手続き'),
            content=ft.Column(
                [
                    create_date,
                    ft.VerticalDivider(),
                    self.lv,
                ],
                height=300,
            ),
            actions=[ft.ElevatedButton(text="OK", autofocus=True,
                                       on_click=lambda e: self.inheritance_notification_create(create_date.value)),
                     ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            # actions=[ft.ElevatedButton(text="OK", autofocus=True, on_click=self.inheritance_notification_create(create_date.value)),
            #          ft.ElevatedButton(text="キャンセル", on_click=self.close_dlg)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.update()

    def inheritance_notification_create(self, e):
        self.close_dlg(self)
        sql = (f'''
           SELECT
               t1.folder_s_path AS フォルダパス,
               t1.username1_hurigana || "  " || t1.username2_hurigana AS 被相続人_かな,
               t1.username1 || "  " || t1.username2 AS 被相続人,
               t1.prefectures || t1.municipalities || t1.townarea || t1.house_number AS 被相続人住所,
               t1.building AS 被相続人建物名,
               t1.deathday AS 死亡日,
               t2.branch_code AS 店番号,
               t2.bank_number AS 口座番号,
               t2.deposit_type AS 種類,
               t3.bank_branch_name AS 支店名,
               (SELECT count(*) FROM heir WHERE code = "{GlobalValues.code}" AND situation = "") AS 相続人数,
               t4.username1 || "  " || t4.username2 AS 相続人,
               t4.username1_hurigana || "  " || t4.username2_hurigana AS 相続人かな
           FROM customer AS t1
               INNER JOIN bank_customer AS t2
               ON t1.code = t2.code
               AND t2.jba_code = "0137"
                   INNER JOIN bank_branch AS t3
                   ON t3.bank_branch_code = t2.branch_code
                       INNER JOIN heir AS t4
                       ON t4.code = t1.code
                       AND t4.code = "{GlobalValues.code}"
           WHERE t1.code = "{GlobalValues.code}"
       ''')
        self.customer = GlobalValues.get_db(sql, row_factory=True)

        # 書類1
        pdf = PdfCreate("A3", 'landscape')
        pdf.draw_string(256, 178.5, re.findall(r'\d+', e)[0], 7)
        pdf.draw_string(267, 178.5, re.findall(r'\d+', e)[1], 7)
        pdf.draw_string(274, 178.5, re.findall(r'\d+', e)[2], 7)
        pdf.draw_string(179, 172.5, self.customer[0]['被相続人住所'], 8)
        pdf.draw_string(179, 169, self.customer[0]['被相続人建物名'], 8)
        pdf.draw_string(179, 160, self.customer[0]['被相続人'])
        customer_deathday = re.findall('[0-9]+', self.customer[0]['死亡日'])
        pdf.draw_string(256, 161.6, customer_deathday[0], 6)
        pdf.draw_string(266, 161.6, customer_deathday[1], 6)
        pdf.draw_string(273, 161.6, customer_deathday[2], 6)
        pdf.draw_string(234, 68, '東京都町田市森野一丁目22番5号', 6)
        pdf.draw_string(234, 63, '相続手続支援センター町田　有限責任事業組合　組合員', 4)
        pdf.draw_string(234, 59, '株式会社プロフィット・ワン　職務執行者　大貫　利一', 4)
        pdf.draw_string(175, 21, '相続手続支援センター町田　有限責任事業組合　組合員')
        pdf.draw_string(175, 16.5, '株式会社プロフィット・ワン　職務執行者　大貫　利一')
        pdf.draw_string(247, 12.5, '042', 8)
        pdf.draw_string(258, 12.5, '710', 8)
        pdf.draw_string(269, 12.5, '6178', 8)

        pdf.pdf_save(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',
                         'きらぼし銀行_相続手続依頼書1'),
            os.path.dirname(__file__) + "/pdf/きらぼし銀行_相続手続依頼書.pdf", page=1, open_bool=False)

        # 書類2
        sql = ('''
            SELECT
                branch_code AS 店番号,
                bank_number AS 口座番号,
                deposit_type AS 種類
            FROM bank_customer
            WHERE code = ?
            AND jba_code = "0137"
        ''')
        bank_account_records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))

        pdf = PdfCreate("A3", 'landscape')
        ## 左ページ
        for i, bank_account_record in enumerate(bank_account_records):
            branches = BankSearch.branch_search(bank_code='0137', code=str(bank_account_record[0]).zfill(3))
            for branch in branches:
                branch_name = branch[1]
            pdf.draw_string(15, (168 - i * 8.5), f'{branch_name}', 8)
            pdf.draw_string(31, (168 - i * 8.5), f'{bank_account_record[2]}', 9)
            pdf.draw_string(52, (168 - i * 8.5), str(bank_account_record[1]).zfill(7), 9)
            pdf.draw_string(80.5, (170 - i * 8), '〇', 12)
            # if not '定期' in bank_account_record[2]:
            #     if self.lv.controls[i].controls[0].controls[1].value == '有':
            #         pdf.draw_string(132, (165 - i * 8.5), '〇', 12)
            #     elif self.lv.controls[i].controls[0].controls[1].value == '無':
            #         pdf.draw_string(132, (162 - i * 8.5), '〇', 12)

        ## 右ページ
        # 5.通帳等の紛失
        # i = 0
        # x = 0
        # for lv in self.lv.controls:
        #     if lv.controls[0].controls[1].value == '無':
        #         sql = (f'''
        #             SELECT
        #                 branch_code AS 店番号,
        #                 bank_number AS 口座番号,
        #                 deposit_type AS 種類
        #             FROM bank_customer
        #             WHERE code = ?
        #             AND jba_code = "0137"
        #             AND bank_number = "{lv.controls[0].controls[1].data}"
        #         ''')
        #         record = GlobalValues.get_db(sql, tuple([GlobalValues.code]))[0]
        # branches = BankSearch.branch_search(bank_code='0137', code=str(record[0]).zfill(3))
        # for branch in branches:
        #     branch_name = branch[1]
        # pdf.draw_string(160 + x, 165 - i * 7, branch_name, 6)
        # pdf.draw_string(171 + x, 165 - i * 7, record[2], 4)
        # pdf.draw_string(180 + x, 165 - i * 7, str(record[1]).zfill(7), 8)
        # pdf.draw_string(201 + x, 167 - i * 7, '〇', 8)  # 通帳
        # i += 1
        # if i == 4:
        #     i = 0
        #     x = 160

        # 振込に〇
        x = 163.7
        y = 140
        pdf.draw_rect(x, y, x + 3.8, y + 4.1)

        pdf.draw_string(164.2, 117, '〇', 8)

        sql = ('''
            SELECT
                t1.username1 || " " || t1.username2,
                t2.heir_bank_id,
                t2.heir_id,
                (SELECT bank_name FROM bank WHERE jba_code = t2.jba_code),
                t2.jba_code,
                t2.branch_code,
                t2.bank_number,
                t2.subjects,
                (SELECT bank_branch_name FROM bank_branch WHERE bank_branch_code = t2.branch_code),
                t1.username1_hurigana || " " || t1.username2_hurigana
            FROM heir_bank AS t2
                INNER JOIN heir AS t1
                ON t1.heir_id = t2.heir_id
            WHERE t2.bank_customer_id = (
                SELECT bank_customer_id
                FROM bank_customer
                WHERE code = ?
                AND jba_code = "0137"
            )
        ''')
        records = GlobalValues.get_db(sql, tuple([GlobalValues.code]))
        for i, record in enumerate(records):
            pdf.draw_string(187, 129 - i * 23, f'{jaconv.hira2kata(record[9])}', 6)
            pdf.draw_string(187, 118 - i * 23, f'{record[0]}', 10)
            pdf.draw_string(216, 126.5 - i * 23, record[3], 8)
            if str(record[4]).zfill(4) == '9900':
                branch_name = 'ゆうちょ'
            else:
                branches = BankSearch.branch_search(bank_code=str(record[4]).zfill(4), code=str(record[5]).zfill(3))
                branch_name = [branch_name for branch_code, branch_name in branches]
                pdf.draw_string(242, 126.5 - i * 23, branch_name[0], 8)
            if '普通' in record[7] or '通常' in record[7]:
                pdf.draw_string(213, 116 - i * 23, '〇', 10)  # 普通
            elif '当座' in record[7]:
                pdf.draw_string(220, 110 - i * 23, '〇', 10)  # 当座
            bank_number = str(record[6]).zfill(7)
            pdf.draw_string(232, 118 - i * 23, bank_number[0], 10)
            pdf.draw_string(236, 118 - i * 23, bank_number[1], 10)
            pdf.draw_string(239.5, 118 - i * 23, bank_number[2], 10)
            pdf.draw_string(243, 118 - i * 23, bank_number[3], 10)
            pdf.draw_string(247, 118 - i * 23, bank_number[4], 10)
            pdf.draw_string(251, 118 - i * 23, bank_number[5], 10)
            pdf.draw_string(254.5, 118 - i * 23, bank_number[6], 10)
            pdf.draw_string(261, 128, '〇', 10)
        pdf.pdf_save(os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',
                                  'きらぼし銀行_相続手続依頼書2'),
                     os.path.dirname(__file__) + "/pdf/きらぼし銀行_相続手続依頼書.pdf", page=2, open_bool=False)

        pdf.pdf_marge(
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書', 'きらぼし銀行_相続手続依頼書'),
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',
                         'きらぼし銀行_相続手続依頼書1'),
            os.path.join(self.customer[0]['フォルダパス'], '金融機関手続', '解約申請書',
                         'きらぼし銀行_相続手続依頼書2'),
        )


def main(page: ft.Page):
    # import pyautogui as pag
    GlobalValues.code = "2409011"
    page.scrollTo = "always"
    page.scroll = 'AUTO'
    # size = 0.95
    page.window_width = 1930
    page.window_height = 1080 - 50
    page.window_center()
    page.window_minimizable = True
    page.window_maximizable = True
    page.window_resizable = True
    GlobalValues.my_page = page
    cl = KiraboshiBank()
    page.add(cl)
    # cl.account_freezing()
    cl.inheritance_notification()
    # cl.balance_certificate()


if __name__ == '__main__':
    # pdf = PdfCreate()
    # pdf.pdf_marge(
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf', 'きらぼし銀行_相続手続依頼書'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf', 'きらぼし銀行_相続手続依頼書1'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf', 'きらぼし銀行_相続手続依頼書2'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf', 'きらぼし銀行_相続手続依頼書3'),
    #     os.path.join(r'C:\Users\prof162\OneDrive - 株式会社プロフィット・ワン\General\py\pdf', 'きらぼし銀行_相続手続依頼書4'),
    # )
    ft.app(target=main)
