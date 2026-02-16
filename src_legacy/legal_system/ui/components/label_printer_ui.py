# src/legal_system/ui/components/tools/label_printer_ui.py
import os

import streamlit as st
from legal_system.models.tables import Address, H_AddressHistory
from legal_system.ui.label_generator import generate_advanced_label, get_branch_address

from services.deceased_service import get_contact_info

# ルートディレクトリの特定 (相対パス解決)
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/legal_system/ui/components/tools -> root
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)


def render_label_printer(session, case, current_user_info):
    """宛名ラベル作成画面"""
    st.subheader("🖨️ 宛名ラベル出力")

    contractor = None
    c_address = None
    c_phone = ""

    if case.deceased_ref and case.deceased_ref.heirs:
        contractor = next(
            (h for h in case.deceased_ref.heirs if h.is_contracting_party), None
        )
        if not contractor:
            contractor = case.deceased_ref.heirs[0]

        if contractor:
            al = (
                session.query(H_AddressHistory)
                .filter(
                    H_AddressHistory.heir_id == contractor.id,
                    H_AddressHistory.is_current_address == True,
                )
                .first()
            )
            if al:
                c_address = session.query(Address).get(al.address_id)
            contacts = get_contact_info("heir", contractor.id)
            c_phone = next((c["value"] for c in contacts if c["type"] == "PHONE"), "")

    c_l, c_r = st.columns([1, 1.2])
    with c_l:
        st.markdown("##### 👤 宛先")
        with st.container(border=True):
            dn = f"{contractor.name_last} {contractor.name_first}" if contractor else ""
            dz = c_address.zip_code if c_address else ""
            da = (
                f"{c_address.prefecture}{c_address.city_ward_town}{c_address.street_address} {c_address.building_name or ''}"
                if c_address
                else ""
            )

            ln = st.text_input("氏名", value=dn)
            lh = st.selectbox("敬称", ["様", "殿", "御中"])
            lz = st.text_input("郵便番号", value=dz)
            la = st.text_area("住所", value=da, height=80)
            lt = st.text_input("電話番号 (ラベル用)", value=c_phone)
            inc_c = st.checkbox("✅ お客様ラベル印刷", value=True)

    with c_r:
        st.markdown("##### 🏢 差出人 & 設定")
        with st.container(border=True):
            inc_s = st.checkbox("差出人(自分)も印刷", value=True)
            sz, sad, s_tel, sn = "", "", "", ""

            if inc_s:
                mb = "横浜" if "横浜" in current_user_info.get("dept", "") else "東京"
                ma = get_branch_address(mb)
                sn = st.text_input("担当者名", value=current_user_info["name"])
                s_tel = st.text_input("電話", value=current_user_info["phone"])
                sa = st.text_area("差出人住所", value=ma, height=80)

                # 簡易パース
                lines = sa.split("\n")
                sz = lines[0].replace("〒", "") if lines else ""
                sad = "\n ".join(lines[1:]) if len(lines) > 1 else ""

            c_p1, c_p2 = st.columns(2)
            sp = c_p1.number_input("開始位置", 1, 30, 1)
            cp = c_p2.number_input("枚数", 1, 10, 1)

    st.divider()

    def_tpl = os.path.join(
        ROOT_DIR, "data", "templates", "ラベルシート -貼り付け用.docx"
    )
    up_tpl = st.file_uploader("テンプレート変更(任意)", type=["docx"])

    if st.button("🚀 ラベル作成", type="primary"):
        tpl_b = None
        if up_tpl:
            tpl_b = up_tpl.read()
        elif os.path.exists(def_tpl):
            with open(def_tpl, "rb") as f:
                tpl_b = f.read()
        else:
            st.error(f"テンプレートがありません: {def_tpl}")
            return

        plist = []
        c_data = {
            "type": "client",
            "name": ln,
            "honorific": lh,
            "zip_code": lz,
            "address": la,
            "tel": lt,
        }

        s_data = {}
        if inc_s:
            s_data = {
                "type": "sender",
                "name": f"行政書士法人チェスター {sn}",
                "honorific": "",
                "zip_code": sz,
                "address": sad,
                "tel": s_tel,
            }

        for _ in range(cp):
            if inc_c:
                plist.append(c_data)
            if inc_s:
                plist.append(s_data)

        if not plist:
            st.warning("対象なし")
            return

        try:
            io_data = generate_advanced_label(tpl_b, plist, start_position=sp)
            st.download_button(
                "📥 ダウンロード",
                io_data,
                f"宛名ラベル_{ln.replace(' ', '')}.docx",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            st.success("完了！")
        except Exception as e:
            st.error(f"エラー: {e}")
