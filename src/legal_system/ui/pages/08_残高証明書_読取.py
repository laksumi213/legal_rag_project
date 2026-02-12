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
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import Session, joinedload

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
    FileRegistry,
)
from src.utils.date_utils import parse_all_flexible_date
from legal_system.ui.components.document_viewer import render_enhanced_document_viewer


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
    normalized = unicodedata.normalize("NFKC", str(text))
    normalized = normalized.replace(" ", "").replace("　", "")
    return normalized.replace("銀行", "").replace("支店", "")

def find_bank_in_zengin(search_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Zenginデータから銀行を検索し、(code, name) を返す"""
    banks_path = os.path.join(ZENGIN_DATA_DIR, "banks.json")
    if not os.path.exists(banks_path):
        return None, None

    search_key = normalize_name(search_name)
    
    try:
        with open(banks_path, "r", encoding="utf-8") as f:
            banks = json.load(f)
            
        for code, info in banks.items():
            db_name_norm = normalize_name(info["name"])
            if search_key == db_name_norm:
                return code, info["name"]
        
        for code, info in banks.items():
            db_name_norm = normalize_name(info["name"])
            if search_key in db_name_norm:
                return code, info["name"]
                
    except Exception:
        pass
    return None, None

def find_branch_in_zengin(bank_code: str, branch_search_name: str) -> Tuple[Optional[str], Optional[str]]:
    """指定された銀行コード内の支店を検索し、(code, name) を返す"""
    if not bank_code or not branch_search_name:
        return None, None
        
    branch_path = os.path.join(ZENGIN_DATA_DIR, "branches", f"{bank_code}.json")
    if not os.path.exists(branch_path):
        return None, None

    search_key = normalize_name(branch_search_name)

    try:
        with open(branch_path, "r", encoding="utf-8") as f:
            branches = json.load(f)

        for code, info in branches.items():
            db_name_norm = normalize_name(info["name"])
            if search_key == db_name_norm:
                return code, info["name"]
        
        for code, info in branches.items():
            db_name_norm = normalize_name(info["name"])
            if search_key in db_name_norm:
                return code, info["name"]

    except Exception:
        pass
    return None, None


# ==========================================
# 3. AI解析ロジック (Gemini Vision) - 証券会社対応
# ==========================================
def analyze_balance_cert_with_ai(file_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    """残高証明書（銀行・証券会社）をAIで解析"""
    llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    image_data_list: List[bytes] = []
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
    提供された「残高証明書または取引残高報告書（複数ページの可能性あり）」の全画像を読み取り、情報を統合してJSON形式で出力してください。

    【重要】書類の種類を自動判定してください:
    - **銀行の残高証明書**: 支店名、口座番号、残高が記載されている
    - **証券会社の取引残高報告書**: 銘柄名、数量、評価額が記載されている

    【抽出ルール】
    1. **基本情報**:
       - type: "BANK" または "SECURITY" のいずれか（必須）
       - bank_name: 銀行の場合の銀行名（"BANK" のとき推奨）
       - securities_company: 証券会社の場合の証券会社名（"SECURITY" のとき推奨）
       - reference_date: 証明基準日（YYYY-MM-DD形式に変換）

    2. **銀行の場合 (accounts)**:
       - branch_name: 支店名
       - type: 預金種別（普通、定期、貯蓄、当座など）
       - number: 口座番号
       - balance: 残高（円単位の数値）
       - holder: 名義人

    3. **証券会社の場合 (holdings)**:
       - name: 銘柄名（株式、投資信託、国債など）
       - quantity: 数量（例: "100株", "10口"）
       - unit_price: 単価（あれば）
       - amount: 評価額（円単位の数値）
       - asset_category: 資産区分（株式、投資信託、債券など）

    【出力JSONスキーマ - 銀行の場合】
    {
        "type": "BANK",
        "bank_name": "三菱UFJ銀行",
        "reference_date": "2026-02-09",
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

    【出力JSONスキーマ - 証券会社の場合】
    {
        "type": "SECURITY",
        "securities_company": "野村證券",
        "reference_date": "2026-02-09",
        "holdings": [
            {
                "name": "トヨタ自動車",
                "quantity": "100株",
                "unit_price": 2500,
                "amount": 250000,
                "asset_category": "株式"
            },
            {
                "name": "日経225インデックスファンド",
                "quantity": "50口",
                "unit_price": 15000,
                "amount": 750000,
                "asset_category": "投資信託"
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
            parsed = json.loads(json_str[start:end])
            return normalize_ai_result(parsed)
        else:
            return {"error": "AIからの応答がJSON形式ではありませんでした。"}

    except Exception as e:
        return {"error": str(e)}


def normalize_ai_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """AI応答の表記ゆれを吸収し、UI/保存処理が扱いやすい形に正規化する"""
    data: Dict[str, Any] = dict(raw or {})

    # type / institution_type の吸収
    doc_type = str(data.get("type") or data.get("institution_type") or "").strip().upper()
    if not doc_type:
        # holdingsがあればSECURITY優先
        doc_type = "SECURITY" if isinstance(data.get("holdings"), list) and data.get("holdings") else "BANK"
    data["institution_type"] = "SECURITY" if doc_type == "SECURITY" else "BANK"

    # institution_name の統一（UIでは institution_name を参照）
    if data["institution_type"] == "SECURITY":
        inst = data.get("securities_company") or data.get("institution_name") or data.get("bank_name")
    else:
        inst = data.get("bank_name") or data.get("institution_name")
    data["institution_name"] = str(inst or "").strip()

    # 旧スキーマ互換: bank_name/accounts はそのまま受け入れる
    if "accounts" not in data and isinstance(data.get("account"), list):
        data["accounts"] = data.get("account")
    if "holdings" not in data and isinstance(data.get("holding"), list):
        data["holdings"] = data.get("holding")

    # 日付の柔軟パース（失敗しても落とさない）
    ref = str(data.get("reference_date") or "").strip()
    if ref:
        try:
            parsed_dates = parse_all_flexible_date(ref)
            if parsed_dates:
                data["reference_date"] = parsed_dates[0].strftime("%Y-%m-%d")
        except Exception:
            pass

    # holdings/accounts の型保証
    if not isinstance(data.get("accounts"), list):
        data["accounts"] = []
    if not isinstance(data.get("holdings"), list):
        data["holdings"] = []

    return data


# ==========================================
# 4. DB保存ヘルパー - 銀行用
# ==========================================
def save_bank_assets_to_db(session: Session, case_id: int, data: Dict[str, Any]) -> int:
    """銀行口座データをDBに保存"""
    raw_bank_name = str(data.get("institution_name") or data.get("bank_name") or "").strip()
    bank = None
    
    bank = session.query(BankMaster).filter(BankMaster.bank_name == raw_bank_name).first()
    
    if not bank:
        z_code, z_name = find_bank_in_zengin(raw_bank_name)
        if z_code:
            bank = session.query(BankMaster).filter(BankMaster.bank_code == z_code).first()
            if not bank:
                bank = BankMaster(bank_name=z_name, bank_code=z_code)
                session.add(bank)
                session.flush()
                st.toast(f"ℹ️ 全銀データから銀行マスタを登録しました: {z_name} ({z_code})", icon="🏦")
    
    if not bank:
        unique_code = f"TMP-{uuid.uuid4().hex[:6]}"
        bank = BankMaster(bank_name=raw_bank_name, bank_code=unique_code)
        session.add(bank)
        session.flush()

    saved_count = 0
    
    for acc in data.get("accounts", []):
        raw_branch_name = str(acc.get("branch_name") or "").strip()
        branch = None

        if raw_branch_name:
            branch = session.query(BranchMaster).filter(
                BranchMaster.bank_id == bank.id, 
                BranchMaster.branch_name == raw_branch_name
            ).first()

            if not branch and not bank.bank_code.startswith("TMP"):
                bz_code, bz_name = find_branch_in_zengin(bank.bank_code, raw_branch_name)
                if bz_code:
                    branch = session.query(BranchMaster).filter(
                        BranchMaster.bank_id == bank.id,
                        BranchMaster.branch_code == bz_code
                    ).first()
                    if not branch:
                        branch = BranchMaster(bank_id=bank.id, branch_name=bz_name, branch_code=bz_code)
                        session.add(branch)
                        session.flush()
            
            if not branch:
                tmp_br_code = f"T{uuid.uuid4().hex[:3]}"
                branch = BranchMaster(bank_id=bank.id, branch_name=raw_branch_name, branch_code=tmp_br_code)
                session.add(branch)
                session.flush()

        t_name = str(acc.get("type") or "普通").strip()
        ac_type = session.query(AccountTypeMaster).filter_by(type_name=t_name).first()
        if not ac_type:
            ac_type = AccountTypeMaster(type_name=t_name)
            session.add(ac_type)
            session.flush()

        acc_num = str(acc.get("number") or "").strip()
        
        query = session.query(FinancialAsset).filter(
            FinancialAsset.case_id == case_id,
            FinancialAsset.bank_id == bank.id,
            FinancialAsset.account_number == acc_num
        )
        if branch:
            query = query.filter(FinancialAsset.branch_id == branch.id)
        
        existing = query.first()

        try:
            raw_bal = acc.get("balance", 0)
            balance_val = float(raw_bal) if raw_bal is not None else 0.0
        except:
            balance_val = 0.0

        if existing:
            existing.balance = balance_val
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
                balance=balance_val,
                status="残高証明取込",
                asset_type="BANK"
            )
            session.add(new_asset)
        
        saved_count += 1
    
    return saved_count


# ==========================================
# 5. DB保存ヘルパー - 証券会社用
# ==========================================
def save_security_assets_to_db(session: Session, case_id: int, data: Dict[str, Any]) -> int:
    """証券会社の銘柄データをDBに保存"""
    raw_company_name = str(
        data.get("securities_company") or data.get("institution_name") or data.get("bank_name") or ""
    ).strip()
    
    securities_company = session.query(BankMaster).filter(
        BankMaster.bank_name == raw_company_name
    ).first()
    
    if not securities_company:
        sec_code = f"SEC-{uuid.uuid4().hex[:6]}"
        securities_company = BankMaster(bank_name=raw_company_name, bank_code=sec_code)
        session.add(securities_company)
        session.flush()
        st.toast(f"ℹ️ 証券会社マスタを登録しました: {raw_company_name}", icon="📈")
    
    holdings = data.get("holdings", [])
    total_amount = sum(float(h.get("amount", 0)) for h in holdings)
    
    existing = session.query(FinancialAsset).filter(
        FinancialAsset.case_id == case_id,
        FinancialAsset.bank_id == securities_company.id,
        FinancialAsset.asset_type == "SECURITY"
    ).first()
    
    if existing:
        existing.balance = total_amount
        existing.status = "残高証明確認済"
    else:
        new_asset = FinancialAsset(
            case_id=case_id,
            bank_id=securities_company.id,
            branch_id=None,
            account_type_id=None,
            account_number="",
            balance=total_amount,
            status="証券残高取込",
            asset_type="SECURITY"
        )
        session.add(new_asset)
        session.flush()
    
    file_hash = f"SEC-{case_id}-{securities_company.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    file_reg = session.query(FileRegistry).filter(FileRegistry.file_hash == file_hash).first()
    
    holdings_json = json.dumps(holdings, ensure_ascii=False, indent=2)
    
    if file_reg:
        file_reg.extracted_data = holdings_json
    else:
        file_reg = FileRegistry(
            file_hash=file_hash,
            filename=f"{raw_company_name}_銘柄明細.json",
            bank_id=securities_company.id,
            case_id=case_id,
            doc_type="証券残高証明",
            extracted_data=holdings_json,
            status="CONFIRMED"
        )
        session.add(file_reg)
    
    return len(holdings)


# ==========================================
# 6. メイン画面 UI
# ==========================================
def main() -> None:
    st.title("🏦 残高証明書 読取エージェント")

    db = DatabaseManager()
    session = db._get_session()

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

    col_left, col_right = st.columns([1, 1.5])

    with col_left:
        st.subheader("1. 書類アップロード＆自動解析")
        st.caption("書類をアップロードすると、自動的にAI解析が開始されます。")
        
        uploaded_file = st.file_uploader(
            "残高証明書 (PDF/画像)",
            type=["pdf", "png", "jpg", "jpeg"],
            key="balance_cert_uploader"
        )

        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            
            render_enhanced_document_viewer(
                file_bytes=file_bytes,
                file_type=uploaded_file.type,
                key_prefix="zandaka_viewer"
            )
            
            current_file_identifier = (uploaded_file.name, uploaded_file.size)
            if st.session_state.get("last_uploaded_file_identifier") != current_file_identifier:
                with st.spinner("書類の内容をAIが解析しています..."):
                    result = analyze_balance_cert_with_ai(file_bytes, uploaded_file.type)
                    
                    if "error" in result:
                        st.error(f"AI解析エラー: {result['error']}")
                        if "zandaka_result" in st.session_state:
                            del st.session_state["zandaka_result"]
                    else:
                        st.session_state["zandaka_result"] = result
                        st.success("AI解析が完了しました。右側で結果を確認・編集してください。")
                
                st.session_state["last_uploaded_file_identifier"] = current_file_identifier
                st.rerun()

    with col_right:
        st.subheader("2. 抽出結果・編集")
        
        if "zandaka_result" in st.session_state:
            res = normalize_ai_result(st.session_state["zandaka_result"])
            institution_type = res.get("institution_type", "BANK")
            
            with st.form("save_assets_form"):
                c1, c2 = st.columns([2, 1])
                inst_name = c1.text_input(
                    "金融機関名", 
                    value=res.get("institution_name", ""),
                    help="銀行名または証券会社名"
                )
                ref_date = c2.text_input("基準日", value=res.get("reference_date", ""))
                
                if institution_type == "SECURITY":
                    st.info("📈 **証券会社の取引残高報告書** として認識されました")
                    st.markdown("###### 銘柄明細リスト")
                    
                    holdings = res.get("holdings", [])
                    if not holdings:
                        st.warning("銘柄情報が見つかりませんでした。")
                        df = pd.DataFrame(columns=["name", "quantity", "unit_price", "amount", "asset_category"])
                    else:
                        df = pd.DataFrame(holdings)
                    
                    edited_df = st.data_editor(
                        df,
                        column_config={
                            "name": st.column_config.TextColumn("銘柄名", width="large"),
                            "quantity": st.column_config.TextColumn("数量", width="small"),
                            "unit_price": st.column_config.NumberColumn("単価", format="%d"),
                            "amount": st.column_config.NumberColumn("評価額", format="%d"),
                            "asset_category": st.column_config.TextColumn("資産区分", width="small")
                        },
                        num_rows="dynamic",
                        use_container_width=True
                    )
                    
                    total_amount = edited_df["amount"].sum() if "amount" in edited_df.columns else 0
                    st.metric("合計評価額", f"¥{total_amount:,.0f}")
                    
                else:
                    st.info("🏦 **銀行の残高証明書** として認識されました")
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
                        if institution_type == "SECURITY":
                            final_data = {
                                "institution_name": inst_name,
                                "institution_type": "SECURITY",
                                "securities_company": inst_name,
                                "reference_date": ref_date,
                                "holdings": edited_df.to_dict(orient="records")
                            }
                            count = save_security_assets_to_db(session, target_case_id, final_data)
                            session.commit()
                            st.toast(f"登録完了: {count}銘柄の証券資産を保存しました！", icon="✅")
                        else:
                            final_data = {
                                "institution_name": inst_name,
                                "institution_type": "BANK",
                                "bank_name": inst_name,
                                "reference_date": ref_date,
                                "accounts": edited_df.to_dict(orient="records")
                            }
                            count = save_bank_assets_to_db(session, target_case_id, final_data)
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
            
            zengin_path = os.path.join(ZENGIN_DATA_DIR, "banks.json")
            if os.path.exists(zengin_path):
                st.caption(f"✅ 全銀データ連携: 有効 ({len(json.load(open(zengin_path, encoding='utf-8')))}行)")
            else:
                st.caption("⚠️ 全銀データが見つかりません (自動更新スクリプトを実行してください)")

    session.close()

if __name__ == "__main__":
    main()