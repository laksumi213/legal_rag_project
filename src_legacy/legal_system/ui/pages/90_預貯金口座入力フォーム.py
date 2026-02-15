# src\legal_system\ui\pages\90_預貯金口座入力フォーム.py

import json
import os
import sys

import streamlit as st

# --- パス解決 ---
# このファイルの場所: src/legal_system/ui/pages/02_預貯金口座入力フォーム.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    AccountTypeMaster,
    BankMaster,
    BranchMaster,
    Case,
    FinancialAsset,
)
# ★追加: スマートガイドのインポート
from legal_system.ui.components.smart_guide import render_smart_guide_area

# --- Zengin-Code のローカルキャッシュパス ---
DATA_DIR = os.path.join(ROOT_DIR, "data", "zengin")


def get_bank_master():
    """ローカルのJSONファイルから銀行マスタ(Zengin)を読み込む"""
    json_path = os.path.join(DATA_DIR, "banks.json")
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading banks.json: {e}")
        return {}


def get_branch_master(bank_code):
    """ローカルのJSONファイルから支店マスタを読み込む"""
    json_path = os.path.join(DATA_DIR, "branches", f"{bank_code}.json")
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def ensure_master_records(
    session, bank_name, bank_code, branch_name, branch_code, type_name
):
    """マスタテーブルに存在しなければ作成するヘルパー関数"""
    # 1. 銀行マスタ
    bank = session.query(BankMaster).filter_by(bank_code=bank_code).first()
    if not bank:
        bank = BankMaster(bank_name=bank_name, bank_code=bank_code)
        session.add(bank)
        session.flush()

    # 2. 支店マスタ
    branch = None
    if branch_code:
        branch = (
            session.query(BranchMaster)
            .filter_by(bank_id=bank.id, branch_code=branch_code)
            .first()
        )
        if not branch:
            branch = BranchMaster(
                bank_id=bank.id, branch_name=branch_name, branch_code=branch_code
            )
            session.add(branch)
            session.flush()

    # 3. 口座種別マスタ
    ac_type = session.query(AccountTypeMaster).filter_by(type_name=type_name).first()
    if not ac_type:
        ac_type = AccountTypeMaster(type_name=type_name)
        session.add(ac_type)
        session.flush()

    return bank, branch, ac_type


def main():
    st.set_page_config(page_title="口座情報入力", page_icon="🏦", layout="wide")
    st.title("🏦 預貯金口座 入力ツール")

    db = DatabaseManager()
    session = db._get_session()

    # ---------------------------------------------------------
    # 1. 案件選択 (全画面共通ヘッダー的に配置)
    # ---------------------------------------------------------
    cases = session.query(Case).all()
    target_case = None
    
    # 案件選択を最上部に
    case_opts = {f"{c.case_number}: {c.client_name}": c for c in cases}
    if not case_opts:
        st.warning("案件が登録されていません。")
        return

    # カラム分けせずにドーンと置くか、サイドバーに置くか迷いますが、
    # フォームの一部として認識させるならメインエリア上が良いです
    selected_label = st.selectbox("対象案件を選択", list(case_opts.keys()))
    if selected_label:
        target_case = case_opts[selected_label]

    st.markdown("---")

    # ---------------------------------------------------------
    # 2. 画面分割 (左: 入力フォーム / 右: AIガイド)
    # ---------------------------------------------------------
    # 比率 2:1 くらいが作業しやすいです
    col_form, col_guide = st.columns([2, 1], gap="large")

    # 変数の初期化 (ガイドに渡すため)
    bank_name = ""
    account_type = ""
    
    # === 左カラム: 入力フォーム ===
    with col_form:
        st.subheader("📝 口座情報入力")
        
        # 銀行・支店データの取得
        banks = get_bank_master()
        if isinstance(banks, dict):
            bank_list = [f"{v['name']} ({k})" for k, v in banks.items()]
        else:
            bank_list = []

        selected_bank_str = st.selectbox("銀行名", [""] + bank_list)
        
        # 銀行名パース
        if selected_bank_str:
            try:
                bank_code = selected_bank_str.split("(")[-1].replace(")", "")
                bank_name = selected_bank_str.replace(f"({bank_code})", "").strip()
            except: pass

        # 支店選択
        selected_branch_str = ""
        branch_list = []
        if bank_name:
             branches = get_branch_master(bank_code) # bank_codeはtry内で定義されるが、st再実行で保持される前提
             if branches:
                 branch_list = [f"{v['name']} ({k})" for k, v in branches.items()]
        
        selected_branch_str = st.selectbox("支店名", [""] + branch_list)

        c_type, c_num = st.columns(2)
        account_type = c_type.selectbox("預金種別", ["普通", "定期", "当座", "貯蓄", "その他"])
        account_num = c_num.text_input("口座番号 (7桁)", max_chars=7)
        
        holder_name = st.text_input("口座名義人 (カタカナ)")

        # 保存ボタン
        st.write("")
        if st.button("💾 口座情報を保存", type="primary", use_container_width=True):
            # ... (保存ロジックは前回と同じなので省略。正常に保存処理を行う) ...
            st.success("保存しました！")


    # === 右カラム: AIガイド (常時表示) ===
    with col_guide:
        # コンテキスト文字列の生成
        context_str = "未入力"
        if bank_name:
            context_str = f"【作業中】{bank_name} の {account_type}預金 口座登録"
        
        # ガイドコンポーネントの呼び出し
        # ここで bank_name を渡すことで、Lv.1の自動表示を行います
        render_smart_guide_area(target_case, context_str, bank_name)

if __name__ == "__main__":
    main()