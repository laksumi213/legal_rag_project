# src/legal_system/ui/pages/08_残高証明書_読取.py

import base64
import json
import os
import sys
import time
import uuid
import unicodedata
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import joinedload

# ==========================================
# 1. パス解決 & インポート
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    AccountTypeMaster,
    BankMaster,
    BranchMaster,
    Case,
    FinancialAsset,
)
from utils.date_utils import parse_all_flexible_date

# Zenginデータのパス
ZENGIN_DATA_DIR = os.path.join(ROOT_DIR, "data", "zengin")

# ページ設定
st.set_page_config(page_title="残高証明書 自動読取", page_icon="🏦", layout="wide")


# ==========================================
# 2. Zengin Code 検索ロジック (表記ゆれ対応)
# ==========================================
def normalize_name(text: str) -> str:
    """検索用に銀行名・支店名を正規化する (全角統一、スペース除去、'銀行'削除)"""
    if not text:
        return ""
    # NFKC正規化（半角カナ→全角、全角英数→半角 など）
    normalized = unicodedata.normalize("NFKC", text)
    # スペース除去
    normalized = normalized.replace(" ", "").replace("　", "")
    # '銀行' '支店' などの接尾辞を一時的に除去して比較（完全一致率を高めるため）
    return normalized.replace("銀行", "").replace("支店", "")

def find_bank_in_zengin(search_name: str):
    """
    Zenginデータから銀行を検索し、(code, name) を返す
    """
    banks_path = os.path.join(ZENGIN_DATA_DIR, "banks.json")
    if not os.path.exists(banks_path):
        return None, None

    search_key = normalize_name(search_name)
    
    try:
        with open(banks_path, "r", encoding="utf-8") as f:
            banks = json.load(f)
            
        # 1. 完全一致・部分一致検索
        for code, info in banks.items():
            db_name_norm = normalize_name(info["name"])
            if search_key == db_name_norm:
                return code, info["name"]
        
        # 2. 逆包含検索 ("三菱UFJ" で "三菱UFJ銀行" をヒットさせる)
        for code, info in banks.items():
            db_name_norm = normalize_name(info["name"])
            if search_key in db_name_norm:
                return code, info["name"]
                
    except Exception:
        pass
    return None, None

def find_branch_in_zengin(bank_code: str, branch_search_name: str):
    """
    指定された銀行コード内の支店を検索し、(code, name) を返す
    """
    if not bank_code or not branch_search_name:
        return None, None
        
    branch_path = os.path.join(ZENGIN_DATA_DIR, "branches", f"{bank_code}.json")
    if not os.path.exists(branch_path):
        return None, None

    search_key = normalize_name(branch_search_name)

    try:
        with open(branch_path, "r", encoding="utf-8") as f:
            branches = json.load(f)

        # 支店検索
        for code, info in branches.items():
            db_name_norm = normalize_name(info["name"])
            if search_key == db_name_norm:
                return code, info["name"]
        
        # 部分一致 ("本店" で "本店営業部" など)
        for code, info in branches.items():
            db_name_norm = normalize_name(info["name"])
            if search_key in db_name_norm:
                return code, info["name"]

    except Exception:
        pass
    return None, None


# ==========================================
# 3. AI解析ロジック (Gemini Vision)
# ==========================================
def analyze_balance_cert_with_ai(file_bytes: bytes, mime_type: str) -> dict:
    llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    image_data_list = []
    if mime_type == "application/pdf":
        try:
            images = convert_from_bytes(file_bytes, dpi=200)
            for img in images:
                buf = BytesIO()
                img.save(buf, format="JPEG")
                image_data_list.append(buf.getvalue())
        except Exception as e:
            return {"error": f"PDF変換エラー: {e}"}
    else:
        image_data_list.append(file_bytes)

    prompt_text = """
    あなたは金融機関の書類に精通した「データ入力専門家」です。
    提供された「残高証明書（複数ページの可能性あり）」の全画像を読み取り、情報を統合してJSON形式で出力してください。

    【抽出ルール】
    1. **基本情報**:
       - bank_name: 銀行名（「株式会社」などは省く。例: 三菱UFJ銀行）
       - reference_date: 証明基準日（YYYY-MM-DD形式に変換）。複数の日付がある場合は、最も新しい「証明日（死亡日）」を採用してください。

    2. **口座リスト (accounts)**:
       - 全ページの表形式部分から、すべての口座明細を抽出してください。
       - **branch_name**: 各口座が属する「支店名」を抽出してください。
         - 表の中に支店名列がある場合はそこから取得。
         - 表の外（ヘッダー部分）に支店名が記載されている場合は、そのページ内の全口座にその支店名を適用してください。
       - type: 預金種別（普通、定期、貯蓄、当座、投資信託、外貨など）
       - number: 口座番号（記号やスペースは除去）
       - balance: 残高（円単位の数値。カンマは除去。マイナス表記「△」は負の値にする）
       - holder: 名義人（カタカナまたは漢字。記載があれば抽出）

    【出力JSONスキーマ】
    {
        "bank_name": "銀行名",
        "reference_date": "YYYY-MM-DD",
        "accounts": [
            {
                "branch_name": "東京支店",
                "type": "普通",
                "number": "1234567",
                "balance": 1000000,
                "holder": "メイギジン"
            }
        ]
    }
    """

    content_parts = [{"type": "text", "text": prompt_text}]
    for img_data in image_data_list:
        img_b64 = base64.b64encode(img_data).decode("utf-8")
        content_parts.append(
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
        )

    try:
        message = HumanMessage(content=content_parts)
        response = llm.invoke([message])
        
        raw_content = response.content
        json_str = raw_content.replace("```json", "").replace("```", "").strip()
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(json_str[start:end])
        else:
            return {"error": "AIからの応答がJSON形式ではありませんでした。"}

    except Exception as e:
        return {"error": str(e)}


# ==========================================
# 4. DB保存ヘルパー (Zengin連携版)
# ==========================================
def save_assets_to_db_with_zengin(session, case_id: int, data: dict):
    """
    抽出データをDBに保存（Zengin検索によるマスタ登録機能付き）
    """
    # ------------------------------------
    # A. 銀行マスタの特定・登録
    # ------------------------------------
    raw_bank_name = data.get("bank_name", "").strip()
    bank = None
    
    # 1. DB内検索 (名前一致)
    bank = session.query(BankMaster).filter(BankMaster.bank_name == raw_bank_name).first()
    
    # 2. Zengin検索
    if not bank:
        z_code, z_name = find_bank_in_zengin(raw_bank_name)
        if z_code:
            # Zenginで見つかった -> コードを使ってDB内を再検索 (既にコードはあるが名前が違う場合など)
            bank = session.query(BankMaster).filter(BankMaster.bank_code == z_code).first()
            if not bank:
                # DBになければZenginの正しい名前とコードで新規登録
                bank = BankMaster(bank_name=z_name, bank_code=z_code)
                session.add(bank)
                session.flush()
                st.toast(f"ℹ️ 全銀データから銀行マスタを登録しました: {z_name} ({z_code})", icon="🏦")
    
    # 3. それでもなければ仮コード発行
    if not bank:
        # 重複しないユニークな仮コード
        unique_code = f"TMP-{uuid.uuid4().hex[:6]}"
        bank = BankMaster(bank_name=raw_bank_name, bank_code=unique_code)
        session.add(bank)
        session.flush()

    saved_count = 0
    
    # ------------------------------------
    # B. 口座ごとの登録ループ
    # ------------------------------------
    for acc in data.get("accounts", []):
        raw_branch_name = acc.get("branch_name", "").strip()
        branch = None

        # --- 支店マスタの特定・登録 ---
        if raw_branch_name:
            # 1. DB内検索
            branch = session.query(BranchMaster).filter(
                BranchMaster.bank_id == bank.id, 
                BranchMaster.branch_name == raw_branch_name
            ).first()

            # 2. Zengin検索 (銀行が正規コードを持っている場合のみ)
            if not branch and not bank.bank_code.startswith("TMP"):
                bz_code, bz_name = find_branch_in_zengin(bank.bank_code, raw_branch_name)
                if bz_code:
                    # コードで再検索
                    branch = session.query(BranchMaster).filter(
                        BranchMaster.bank_id == bank.id,
                        BranchMaster.branch_code == bz_code
                    ).first()
                    if not branch:
                        # 新規登録
                        branch = BranchMaster(bank_id=bank.id, branch_name=bz_name, branch_code=bz_code)
                        session.add(branch)
                        session.flush()
            
            # 3. 仮登録
            if not branch:
                # 支店コードもユニーク制約がある場合に備えてランダム化
                tmp_br_code = f"T{uuid.uuid4().hex[:3]}"
                branch = BranchMaster(bank_id=bank.id, branch_name=raw_branch_name, branch_code=tmp_br_code)
                session.add(branch)
                session.flush()

        # --- 口座種別 ---
        t_name = acc.get("type", "普通")
        ac_type = session.query(AccountTypeMaster).filter_by(type_name=t_name).first()
        if not ac_type:
            ac_type = AccountTypeMaster(type_name=t_name)
            session.add(ac_type)
            session.flush()

        # --- 資産データUpsert ---
        acc_num = acc.get("number", "")
        
        query = session.query(FinancialAsset).filter(
            FinancialAsset.case_id == case_id,
            FinancialAsset.bank_id == bank.id,
            FinancialAsset.account_number == acc_num
        )
        if branch:
            query = query.filter(FinancialAsset.branch_id == branch.id)
        
        existing = query.first()

        if existing:
            existing.balance = acc.get("balance", 0)
            existing.status = "残高証明確認済"
            if not existing.branch_id and branch:
                existing.branch_id = branch.id
        else:
            new_asset = FinancialAsset(
                case_id=case_id,
                bank_id=bank.id,
                branch_id=branch.id if branch else None,
                account_type_id=ac_type.id,
                account_number=acc_num,
                balance=acc.get("balance", 0),
                status="残高証明取込",
                asset_type="BANK"
            )
            session.add(new_asset)
        
        saved_count += 1
    
    return saved_count


# ==========================================
# 5. メイン画面 UI
# ==========================================
def main():
    st.title("🏦 残高証明書 読取エージェント")

    db = DatabaseManager()
    session = db._get_session()

    # 案件ID取得 (Home共有)
    target_case_id = st.session_state.get("selected_case_id")

    if not target_case_id:
        st.warning("⚠️ 案件が選択されていません。")
        st.info("Home画面またはサイドバーで案件を選択してください。")
        with st.expander("案件を選択する（未選択の場合）", expanded=True):
            cases = session.query(Case).options(joinedload(Case.deceased_ref)).all()
            opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
            sel = st.selectbox("案件選択", list(opts.keys()))
            if st.button("この案件で作業を開始"):
                st.session_state["selected_case_id"] = opts[sel]
                st.rerun()
        return

    current_case = session.query(Case).options(joinedload(Case.deceased_ref)).get(target_case_id)
    if not current_case:
        st.error("案件情報の取得に失敗しました。")
        return

    d_name = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}" if current_case.deceased_ref else "未登録"
    st.success(f"📂 作業中の案件: **{current_case.case_number} {current_case.client_name}** 様 (被相続人: {d_name})")

    st.divider()

    # UIレイアウト
    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.subheader("1. 書類アップロード")
        st.caption("複数ページ・複数支店に対応。全銀データ照合あり。")
        uploaded_file = st.file_uploader("残高証明書 (PDF/画像)", type=["pdf", "png", "jpg", "jpeg"])

        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            
            display_image = None
            if uploaded_file.type == "application/pdf":
                try:
                    images = convert_from_bytes(file_bytes, dpi=150, first_page=1, last_page=1)
                    if images: display_image = images[0]
                except Exception as e:
                    st.error(f"PDFプレビューエラー: {e}")
            else:
                display_image = Image.open(BytesIO(file_bytes))
            
            if display_image:
                st.image(display_image, caption="プレビュー (1ページ目)", use_container_width=True)

            if st.button("🚀 AI解析を開始", type="primary", use_container_width=True):
                with st.spinner("Geminiが全ページを解析中..."):
                    result = analyze_balance_cert_with_ai(file_bytes, uploaded_file.type)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["zandaka_result"] = result
                        st.success("解析完了！")

    with col_right:
        st.subheader("2. 抽出結果・編集")
        
        if "zandaka_result" in st.session_state:
            res = st.session_state["zandaka_result"]
            
            with st.form("save_assets_form"):
                c1, c2 = st.columns([2, 1])
                b_name = c1.text_input("銀行名", value=res.get("bank_name", ""), help="全銀データと照合されます")
                ref_date = c2.text_input("基準日", value=res.get("reference_date", ""))
                
                st.markdown("###### 口座明細リスト")
                
                accounts = res.get("accounts", [])
                if not accounts:
                    st.warning("口座情報が見つかりませんでした。")
                    df = pd.DataFrame(columns=["branch_name", "type", "number", "balance", "holder"])
                else:
                    df = pd.DataFrame(accounts)
                
                edited_df = st.data_editor(
                    df,
                    column_config={
                        "branch_name": st.column_config.TextColumn("支店名", width="medium"),
                        "type": st.column_config.TextColumn("種別", width="small"),
                        "number": st.column_config.TextColumn("口座番号", width="medium"),
                        "balance": st.column_config.NumberColumn("残高", format="%d"),
                        "holder": st.column_config.TextColumn("名義人")
                    },
                    num_rows="dynamic",
                    use_container_width=True
                )
                
                st.markdown("---")
                if st.form_submit_button("💾 データベースに登録"):
                    try:
                        final_data = {
                            "bank_name": b_name,
                            "reference_date": ref_date,
                            "accounts": edited_df.to_dict(orient="records")
                        }
                        
                        # ★ここが変更点: Zengin対応の保存関数を使用
                        count = save_assets_to_db_with_zengin(session, target_case_id, final_data)
                        session.commit()
                        
                        st.toast(f"登録完了: {count}件の資産を保存しました！", icon="✅")
                        st.balloons()
                        
                        del st.session_state["zandaka_result"]
                        time.sleep(2)
                        st.rerun()

                    except Exception as e:
                        st.error(f"登録エラー: {e}")
                        session.rollback()
        else:
            st.info("👈 左側で書類をアップロードしてください。")
            
            # Zenginデータのステータス表示
            zengin_path = os.path.join(ZENGIN_DATA_DIR, "banks.json")
            if os.path.exists(zengin_path):
                st.caption(f"✅ 全銀データ連携: 有効 ({len(json.load(open(zengin_path, encoding='utf-8')))}行)")
            else:
                st.caption("⚠️ 全銀データが見つかりません (自動更新スクリプトを実行してください)")

    session.close()

if __name__ == "__main__":
    main()