# src/legal_system/ui/pages/02_顧客紹介連絡表_読取.py

import base64
import json
import os
import sys
from datetime import datetime
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if project_root not in sys.path:
    sys.path.append(project_root)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, Deceased, H_AddressHistory, Heir
from src.services.deceased_service import (
    get_next_provisional_number,
    search_zip_by_address_api,
)
from src.services.dispatch_service import (
    determine_base_from_branch,
    generate_kintone_json_payload,
)

st.set_page_config(page_title="顧客紹介連絡表 読取", page_icon="📄", layout="wide")


def analyze_referral_sheet_gemini(file_bytes: bytes, mime_type: str):
    """Gemini Visionで画像を解析"""
    img_b64 = base64.b64encode(file_bytes).decode("utf-8")
    image_url = f"data:{mime_type};base64,{img_b64}"

    llm = AIFactory.get_llm("cloud", temperature=0.0)

    # 強化版プロンプト
    prompt_text = """
        あなたは日本の行政手続きに精通した「シニア・データ入力オペレーター」です。
        提供された「顧客紹介連絡表」の画像を視覚的に解析し、以下の情報を抽出してJSON形式のみを出力してください。

        【全体的な処理ルール】
        - 画像内のレイアウト（上部・中部・下部）を理解し、項目と値の対応関係を正確に読み取ってください。
        - 項目が見つからない、または空欄の場合は、null ではなく必ず空文字 "" を出力してください。
        - 出力は純粋なJSONのみとし、Markdownのコードブロック（```json）や挨拶文は含めないでください。

        【1. 顧客情報の抽出ルール】
        - **氏名 (client_name/kana)**:
          - 姓と名の間に必ず『全角スペース』を入れてください（例: "山田　太郎"）。
          - 姓や名の中にスペースは入れないでください（例: "山田　太郎" (OK), "山田 太郎" (NG), "山田太郎" (NG), "山 田　太 郎" (NG),, "山田　太 郎" (NG), "山 田　太郎" (NG)）。
          - 「様」「殿」などの敬称が記載されていても、除去して氏名のみとしてください。
        - **電話番号 (client_phone)**:
          - 顧客情報欄（通常は上部〜中部）にある電話番号を優先してください。
          - 複数の電話番号がある場合、携帯電話を優先して `client_phone_1` に、固定電話を `client_phone_2` に入れてください。
        - **住所 (client_address)**:
          - 可能な限り「都道府県」「市区町村」「番地」「建物名」に分割してください。
          - 住所内の数字は半角に統一してください（例: "１丁目" → "1丁目"）。
          - 分割が困難な場合は `client_address_full` に全文を入れ、他を空文字にしても構いません。
          - **郵便番号は抽出不要です。**

        【2. 紹介元情報の抽出ルール（重要）】
        - 帳票の下部にある「SMBC日興証券」「紹介元」「担当者」欄を探してください。
        - **referral_sec_branch_name**: 「支店」や「部店」の名称を抽出してください（例: "横浜支店"）。
        - **referral_sec_rep_name**: 紹介元の担当者名を抽出してください。
        - **referral_sec_phone**: **最重要項目です。** 紹介元の署名欄や担当者印の近くにある「内線」や「直通電話」を抽出してください。顧客の電話番号と混同しないよう注意してください。

        【3. 日付・管理番号の抽出ルール】
        - **日付 (introduction_date / consent_date)**:
          - 「和暦（令和〇年）」や「短縮形（R5.5.1）」で記載されている場合、必ず **西暦の `YYYY-MM-DD` 形式** に変換してください。
            - 例: "令和5年1月1日" → "2023-01-01"
            - 例: "R5.5.1" → "2023-05-01"
        - **sol_case_number**:
          - "SOL" から始まる英数字の管理番号があれば抽出してください。

        【出力JSONスキーマ】
        {
            "client_name": "顧客氏名(全角スペース区切り)",
            "client_name_kana": "顧客フリガナ(全角スペース区切り)",
            "client_phone_1": "顧客電話番号1(ハイフンあり)",
            "client_phone_2": "顧客電話番号2(ハイフンあり)",
            "client_prefecture": "都道府県",
            "client_city": "市区町村",
            "client_street": "番地",
            "client_building": "建物名・部屋番号",
            "client_address_full": "住所全文(予備)",
            "sol_case_number": "SOL案件番号",
            "introduction_date": "紹介日(YYYY-MM-DD)",
            "referral_sec_branch_name": "紹介元支店名",
            "referral_sec_rep_name": "紹介元担当者名",
            "consent_date": "同意書取得日(YYYY-MM-DD)",
            "referral_sec_phone": "紹介元電話番号"
        }
        """

    try:
        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": image_url},
            ]
        )
        response = llm.invoke([msg])
        content = response.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        st.error(f"AI解析エラー: {e}")
        return {}


def main():
    st.title("📄 顧客紹介連絡表 読取エージェント (Ver 2.2)")
    st.caption(
        "Gemini Visionにより、拠点振り分け・電話番号抽出・Kintoneデータ生成を一括で行います。"
    )

    uploaded_file = st.file_uploader(
        "紹介連絡表 (PDF/画像) をアップロード", type=["pdf", "png", "jpg", "jpeg"]
    )

    if not uploaded_file:
        return

    # 画像処理
    file_bytes = uploaded_file.read()
    target_bytes = file_bytes
    mime_type = uploaded_file.type
    display_img = None

    if uploaded_file.type == "application/pdf":
        with st.spinner("PDFを画像に変換中..."):
            images = convert_from_bytes(file_bytes)
            if images:
                display_img = images[0]
                buf = BytesIO()
                display_img.save(buf, format="JPEG")
                target_bytes = buf.getvalue()
                mime_type = "image/jpeg"
    else:
        display_img = Image.open(BytesIO(file_bytes))
        target_bytes = file_bytes

    # 解析実行
    col_l, col_r = st.columns([1, 1.2])
    with col_l:
        st.image(display_img, caption="原本", use_container_width=True)

    with col_r:
        st.subheader("🤖 AI解析結果")
        if "ocr_result" not in st.session_state:
            if st.button("🚀 解析開始", type="primary"):
                with st.spinner("Geminiが内容を読み取っています..."):
                    res = analyze_referral_sheet_gemini(target_bytes, mime_type)
                    st.session_state["ocr_result"] = res
                    st.rerun()

        data = st.session_state.get("ocr_result")

        if data:
            with st.form("reg_form"):
                db = DatabaseManager()
                session = db._get_session()

                # 1. 仮番号発番
                temp_no = get_next_provisional_number(session)
                st.info(f"💡 仮案件番号: **{temp_no}**")

                # 2. 拠点自動判定
                branch_name = data.get("referral_sec_branch_name", "")
                assigned_base = determine_base_from_branch(branch_name)
                st.success(
                    f"📍 担当拠点判定: **{assigned_base}** (紹介元: {branch_name})"
                )

                # 入力フィールド
                c1, c2 = st.columns(2)
                name = c1.text_input("顧客名", value=data.get("client_name", ""))
                kana = c2.text_input("フリガナ", value=data.get("client_name_kana", ""))

                # 住所（分割 or 全文）
                addr_full = data.get("client_address_full", "")
                if not addr_full:
                    # 分割データを結合
                    addr_full = f"{data.get('client_prefecture', '')}{data.get('client_city', '')}{data.get('client_street', '')}{data.get('client_building', '')}"

                addr_raw = st.text_input("住所", value=addr_full)

                st.markdown("---")
                r1, r2 = st.columns(2)
                br = r1.text_input("紹介元支店", value=branch_name)
                rep = r2.text_input(
                    "紹介元担当者", value=data.get("referral_sec_rep_name", "")
                )

                # ★要望の機能: 電話番号
                ref_tel = st.text_input(
                    "紹介元電話番号",
                    value=data.get("referral_sec_phone", ""),
                    help="Kintoneの備考欄に転記されます",
                )
                sol = st.text_input("SOL案件No", value=data.get("sol_case_number", ""))

                if st.form_submit_button("✅ 仮登録＆Kintoneデータ生成"):
                    try:
                        # 住所分割 (簡易)
                        zip_code = search_zip_by_address_api(addr_raw)
                        # DB登録処理
                        new_case = Case(
                            case_number=temp_no,
                            client_name=name,
                            client_name_kana=kana,
                            referral_sec_branch_name=br,
                            referral_sec_rep_name=rep,
                            referral_sec_phone=ref_tel,  # ★保存
                            sol_case_number=sol,
                            created_at=datetime.now(),
                        )
                        session.add(new_case)
                        session.flush()

                        # 関連データ作成 (被相続人ダミー、相続人、住所)
                        dec = Deceased(
                            case_id=new_case.case_id, name_last="", name_first=""
                        )
                        session.add(dec)
                        session.flush()

                        heir = Heir(
                            deceased_id=dec.id,
                            name_last=name,
                            is_contracting_party=True,
                        )
                        session.add(heir)
                        session.flush()

                        addr = Address(
                            zip_code=zip_code, prefecture="", street_address=addr_raw
                        )
                        session.add(addr)
                        session.flush()
                        session.add(
                            H_AddressHistory(
                                heir_id=heir.id,
                                address_id=addr.id,
                                is_current_address=True,
                            )
                        )

                        session.commit()

                        st.session_state["registered_case"] = {
                            "case": new_case,
                            "dec": dec,
                            "heir": heir,
                            "addr": addr,
                        }
                        st.toast(
                            "保存しました！Kintone用データを生成します。", icon="💾"
                        )

                    except Exception as e:
                        st.error(f"保存エラー: {e}")
                    finally:
                        session.close()

            # 3. Kintone連携エリア (保存後に表示)
            if "registered_case" in st.session_state:
                st.divider()
                st.subheader("📋 Kintone登録用データ")
                st.info(
                    "以下のJSONをコピーし、Kintoneのブックマークレットで読み込んでください。"
                )

                rc = st.session_state["registered_case"]
                kintone_json = generate_kintone_json_payload(
                    rc["case"], rc["dec"], rc["heir"], rc["addr"]
                )

                st.code(
                    json.dumps(kintone_json, ensure_ascii=False, indent=2),
                    language="json",
                )

                if st.button("続けて次の書類を読み込む"):
                    st.session_state.clear()
                    st.rerun()


if __name__ == "__main__":
    main()
