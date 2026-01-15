# src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py

import base64
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image

# ==========================================
# 1. パス解決 & インポート
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if src_dir not in sys.path:
    sys.path.append(src_dir)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.config import Config
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, CaseContactPoint, Contact, User, Deceased, Heir, H_AddressHistory, H_ContactLink

from services.deceased_service import search_zip_by_address_api

logger = logging.getLogger(__name__)

st.set_page_config(page_title="顧客紹介連絡表 読取", page_icon="🤝", layout="wide")

# ... (get_next_provisional_number, analyze_image_with_ai 等のヘルパー関数は変更なしのため省略) ...
# ※ ファイル全体を貼り付ける場合は、前回のコードの該当関数を含めてください。
# ここでは main() 関数内の変更点を中心に示します。

def get_next_provisional_number(session) -> str:
    cases = session.query(Case.case_number).all()
    max_num = 0
    pattern = re.compile(r"(\d+)")
    for (c_num,) in cases:
        if c_num:
            match = pattern.search(c_num)
            if match:
                try:
                    num = int(match.group(1))
                    if num > max_num: max_num = num
                except: continue
    return f"{max_num + 1:04d}"

def analyze_image_with_ai(image_bytes: bytes) -> dict:
    # ... (前回のanalyze_image_with_aiと同じ) ...
    try:
        img_str = base64.b64encode(image_bytes).decode("utf-8")
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

        # プロンプト定義 (郵便番号の抽出指示を削除)
        prompt_text = """
        あなたは熟練したデータ入力オペレーターです。
        提供された「顧客紹介連絡表」の画像を読み取り、以下の情報を抽出してJSON形式のみを出力してください。
        
        【重要：氏名の抽出ルール】
        - 「顧客名」および「フリガナ」の姓と名の間は、必ず『全角スペース』を入れてください。ただし、姓の中と氏の中はスペースは開けないこと
          例: "山田　太郎" (OK), "山田 太郎" (NG), "山田太郎" (NG), "山 田　太 郎" (NG),, "山田　太 郎" (NG), "山 田　太郎" (NG)

        【重要：電話番号の抽出ルール】
        1. **禁止事項**: 帳票の下部にある「SMBC日興証券」「担当者」「紹介元」欄に記載されている電話番号は、**絶対に**顧客の電話番号として抽出しないでください。
           これは紹介元の連絡先であり、顧客の連絡先ではありません。
        2. 顧客情報欄（上部または中部）にある電話番号のみを抽出してください。
        3. 携帯電話（090/080/070等）の記載がない場合は、無理に他の番号を入れず、空文字 "" にしてください。

        【重要：住所の抽出ルール】
        - 住所は可能な限り以下の要素に分割して出力してください。
          - client_prefecture: 都道府県 (例: 東京都)
          - client_city: 市区町村 (例: 中央区、〇〇市〇〇町)
          - client_street: 番地 (例: 1-1-1)
          - client_building: 建物名・部屋番号 (例: 〇〇ビル 101)
        - 分割が難しい場合は、client_address_full にまとめて、他を空にしても構いません。
        - **郵便番号は抽出不要です。**

        【その他の抽出ルール】
        - 項目が見つからない場合は空文字 "" を設定してください。
        - JSON以外の解説文は一切不要です。
        
        【出力JSONスキーマ】
        {
            "client_name": "顧客氏名(全角スペース区切り)",
            "client_name_kana": "顧客フリガナ(全角スペース区切り)",
            "client_phone_1": "固定電話またはメインの連絡先",
            "client_phone_2": "携帯電話またはサブの連絡先(なければ空文字)",
            "client_prefecture": "都道府県",
            "client_city": "市区町村",
            "client_street": "番地",
            "client_building": "建物名",
            "client_address_full": "住所全文(予備)",
            "sol_case_number": "SOL案件番号(英数字)",
            "introduction_date": "紹介日(YYYY-MM-DD形式に補正)",
            "referral_sec_branch_name": "紹介元支店名",
            "referral_sec_rep_name": "紹介元担当者名",
            "consent_date": "同意書取得日(YYYY-MM-DD形式)"
        }
        """
        # ... (LLM呼び出し部分は同じ) ...
        message = HumanMessage(content=[{"type": "text", "text": prompt_text}, {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}])
        response = llm.invoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        logger.error(f"AI Vision Analysis Error: {e}")
        return {}

def main():
    st.title("🤝 顧客紹介連絡表 読取・登録")
    # ... (プロバイダー表示等) ...
    
    db = DatabaseManager()
    session = db._get_session()

    # 1. アップロード & 2. 画像変換 & 3. 解析実行 (前回と同じ)
    with st.container(border=True):
        uploaded_file = st.file_uploader("📂 PDFまたは画像をアップロード", type=["pdf", "png", "jpg", "jpeg"])
    
    if not uploaded_file:
        session.close(); return

    file_bytes = uploaded_file.read()
    target_img_bytes = None; display_img = None
    try:
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1); display_img = images[0]
        else:
            display_img = Image.open(BytesIO(file_bytes))
        buf = BytesIO(); display_img.convert("RGB").save(buf, format="JPEG"); target_img_bytes = buf.getvalue()
    except Exception as e:
        st.error(f"ファイル読込エラー: {e}"); session.close(); return

    if "ocr_res_05" not in st.session_state or st.session_state.get("current_file_05") != uploaded_file.name:
        st.session_state["ocr_res_05"] = None; st.session_state["current_file_05"] = uploaded_file.name

    if st.button("🔍 AI解析を実行 (Gemini)", type="primary", use_container_width=True):
        with st.spinner("解析中..."):
            res = analyze_image_with_ai(target_img_bytes)
            st.session_state["ocr_res_05"] = res

    # 4. フォーム
    st.divider()
    ocr_data = st.session_state.get("ocr_res_05") or {}
    
    col_img, col_form = st.columns([1, 1.2])
    with col_img: st.image(display_img, use_container_width=True)

    with col_form:
        st.subheader("📝 データ確認・登録")
        with st.form("referral_form"):
            c1, c2 = st.columns(2)
            case_no = get_next_provisional_number(session)
            c_no_input = c1.text_input("案件番号 (仮4桁)", value=case_no)
            
            name = c1.text_input("顧客名", value=ocr_data.get("client_name", ""))
            kana = c2.text_input("フリガナ", value=ocr_data.get("client_name_kana", ""))
            phone1 = c1.text_input("電話1 (固定)", value=ocr_data.get("client_phone_1", ""))
            phone2 = c2.text_input("電話2 (携帯)", value=ocr_data.get("client_phone_2", ""))
            
            st.markdown("---")
            st.caption("住所情報 (分割)")
            ap, ac = st.columns([1, 1.5])
            pref = ap.text_input("都道府県", value=ocr_data.get("client_prefecture", ""))
            city = ac.text_input("市区町村", value=ocr_data.get("client_city", ""))
            
            as_, ab = st.columns([1.5, 1])
            street = as_.text_input("番地", value=ocr_data.get("client_street", ""))
            building = ab.text_input("建物名・部屋番号", value=ocr_data.get("client_building", ""))
            
            # 予備住所
            full_addr = ocr_data.get("client_address_full", "")
            if full_addr and not (pref or city):
                st.info(f"予備住所: {full_addr}")

            st.markdown("---")
            # ★ 修正: 同意書日付フィールドの追加
            c_sol, c_intro = st.columns(2)
            sol = c_sol.text_input("SOL案件番号", value=ocr_data.get("sol_case_number", ""))
            intro_date = c_intro.text_input("紹介日", value=ocr_data.get("introduction_date", ""))
            
            c_cons, _ = st.columns(2)
            consent_date = c_cons.text_input("同意書日付", value=ocr_data.get("consent_date", ""))
            
            c_br, c_rep = st.columns(2)
            branch = c_br.text_input("紹介元支店", value=ocr_data.get("referral_sec_branch_name", ""))
            rep = c_rep.text_input("紹介元担当者", value=ocr_data.get("referral_sec_rep_name", ""))

            submitted = st.form_submit_button("💾 データベースに保存", type="primary")

        if submitted:
            try:
                # 日付変換
                i_dt = None
                if intro_date:
                    try: i_dt = datetime.strptime(intro_date, "%Y-%m-%d").date()
                    except: pass
                
                c_dt = None
                if consent_date:
                    try: c_dt = datetime.strptime(consent_date, "%Y-%m-%d").date()
                    except: pass

                # 1. 案件作成
                new_case = Case(
                    case_number=c_no_input,
                    client_name=name,
                    client_name_kana=kana,
                    sol_case_number=sol,
                    referral_sec_branch_name=branch,
                    referral_sec_rep_name=rep,
                    introduction_date=i_dt,
                    consent_date=c_dt, # ★保存
                    created_at=datetime.now()
                )
                session.add(new_case)
                session.flush()

                # ... (以下、Deceased, Heir, Address, Phoneの登録処理は前回と同じなので省略なしで記述) ...
                
                # 2. 被相続人
                new_deceased = Deceased(case_id=new_case.case_id, name_last="", name_first="", relationship_type="本人")
                session.add(new_deceased); session.flush()

                # 3. 顧客(相続人)
                parts = name.replace("　", " ").split(" ", 1)
                lname = parts[0]; fname = parts[1] if len(parts)>1 else ""
                k_parts = kana.replace("　", " ").split(" ", 1)
                klname = k_parts[0]; kfname = k_parts[1] if len(k_parts)>1 else ""
                
                new_heir = Heir(
                    deceased_id=new_deceased.id, name_last=lname, name_first=fname,
                    name_last_kana=klname, name_first_kana=kfname, is_contracting_party=True
                )
                session.add(new_heir); session.flush()

                # 4. 住所 (郵便番号検索)
                search_t = f"{pref}{city}"
                if street:
                    m = re.match(r'^([^0-9\-\uFF10-\uFF19]+)', street)
                    if m: search_t += m.group(1).strip()
                    else: search_t += street
                
                z = search_zip_by_address_api(search_t)
                if not z: z = search_zip_by_address_api(f"{pref}{city}")

                new_addr = Address(zip_code=z or "", prefecture=pref, city_ward_town=city, street_address=street, building_name=building)
                session.add(new_addr); session.flush()
                session.add(H_AddressHistory(heir_id=new_heir.id, address_id=new_addr.id, is_current_address=True))

                # 5. 電話
                pm = phone2 if phone2 else phone1
                ps = phone1 if phone2 else ""
                if pm:
                    c1 = Contact(value=pm, type="PHONE", sub_type="Primary")
                    session.add(c1); session.flush()
                    session.add(H_ContactLink(heir_id=new_heir.id, contact_id=c1.id))
                if ps:
                    c2 = Contact(value=ps, type="PHONE", sub_type="Secondary")
                    session.add(c2); session.flush()
                    session.add(H_ContactLink(heir_id=new_heir.id, contact_id=c2.id))

                session.commit()
                st.toast(f"登録完了！(〒{z})" if z else "登録完了！", icon="✅")
                time.sleep(1.5)
                st.session_state["ocr_res_05"] = None
                st.rerun()

            except Exception as e:
                session.rollback(); st.error(f"エラー: {e}")

    session.close()

if __name__ == "__main__":
    main()