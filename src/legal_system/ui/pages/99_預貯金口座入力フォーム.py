import json
import os
import sys

import streamlit as st

# --- パス解決 ---
# このファイルの場所: src/legal_system/ui/pages/99_預貯金口座入力フォーム.py
# ROOT_DIR: プロジェクトルート
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    AccountTypeMaster,
    BankMaster,
    BranchMaster,
    Case,
    FinancialAsset,
)

# --- Zengin-Code のローカルキャッシュパス ---
DATA_DIR = os.path.join(ROOT_DIR, "data", "zengin")


# ★修正: キャッシュ(st.cache_data)を削除しました。
# JSONの読み込みは十分に高速であり、ファイル更新を即座に反映させるためです。
def get_bank_master():
    """ローカルのJSONファイルから銀行マスタ(Zengin)を読み込む"""
    json_path = os.path.join(DATA_DIR, "banks.json")

    # デバッグ用: パスが合っているか確認したい場合は以下のコメントを外す
    # print(f"Looking for banks at: {json_path}")

    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading banks.json: {e}")
        return {}


# ★修正: こちらもキャッシュを削除、またはTTLを設定
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
    st.set_page_config(page_title="口座情報入力", page_icon="🏦", layout="centered")
    st.title("🏦 預貯金口座 入力ツール")
    st.caption(
        "案件ごとの口座情報を登録します。ここで登録したデータが書類作成に使用されます。"
    )

    # 1. 銀行選択
    banks = get_bank_master()

    if not banks:
        st.error(
            "⚠️ 銀行データ(Zengin)が見つかりません。Home画面の「更新」ボタンを押してください。"
        )
        # デバッグ用にパスを表示
        st.caption(f"参照パス: {os.path.join(DATA_DIR, 'banks.json')}")
        return

    # 銀行リスト作成 (辞書型かリスト型かで処理を分ける)
    if isinstance(banks, dict):
        bank_list = [f"{v['name']} ({k})" for k, v in banks.items()]
    else:
        # 想定外のフォーマットの場合のガード
        bank_list = []

    selected_bank_str = st.selectbox(
        "銀行名", options=[""] + bank_list, placeholder="銀行名を入力または選択..."
    )

    # 2. 支店選択
    selected_branch_str = ""
    bank_code = ""
    bank_name = ""

    if selected_bank_str:
        # 文字列 "三菱UFJ銀行 (0005)" からコードと名前を抽出
        try:
            # 右側の括弧内のコードを取得
            bank_code = selected_bank_str.split("(")[-1].replace(")", "")
            # コード部分を除いた名前を取得
            bank_name = selected_bank_str.replace(f"({bank_code})", "").strip()

            branches = get_branch_master(bank_code)
            if branches:
                branch_list = [f"{v['name']} ({k})" for k, v in branches.items()]
                selected_branch_str = st.selectbox("支店名", options=[""] + branch_list)
            else:
                st.warning("支店データがありません（手入力してください）")
                selected_branch_str = st.text_input("支店名 (手入力)")
        except Exception:
            st.error("銀行名のパースに失敗しました")

    # 3. 口座詳細入力
    c1, c2 = st.columns(2)
    account_type = c1.selectbox("預金種別", ["普通", "定期", "当座", "貯蓄", "その他"])
    account_num = c2.text_input("口座番号 (7桁)", max_chars=7)

    holder_name = st.text_input("口座名義人 (カタカナ)", placeholder="ヤマダ タロウ")

    # 案件番号入力
    case_number = st.text_input(
        "案件番号 (G番号)", value="G0001", help="既存の案件番号を入力してください"
    )

    st.divider()

    if st.button("💾 データを確定する", type="primary"):
        if not (bank_name and case_number):
            st.error("銀行名と案件番号は必須です。")
            return

        # 支店情報のパース
        branch_name = ""
        branch_code = "000"

        if selected_branch_str:
            if "(" in selected_branch_str and ")" in selected_branch_str:
                try:
                    branch_code = selected_branch_str.split("(")[-1].replace(")", "")
                    branch_name = selected_branch_str.replace(
                        f"({branch_code})", ""
                    ).strip()
                except:
                    branch_name = selected_branch_str
            else:
                branch_name = selected_branch_str

        try:
            db = DatabaseManager()
            session = db._get_session()

            # 1. 案件の確保
            case = session.query(Case).filter_by(case_number=case_number).first()
            if not case:
                # 案件がない場合は簡易作成
                case = Case(case_number=case_number, client_name=f"案件{case_number}")
                session.add(case)
                session.flush()

            # 2. マスタの確保
            bank_obj, branch_obj, type_obj = ensure_master_records(
                session, bank_name, bank_code, branch_name, branch_code, account_type
            )

            # 3. 資産データの登録
            new_asset = FinancialAsset(
                case_id=case.case_id,
                bank_id=bank_obj.id,
                branch_id=branch_obj.id if branch_obj else None,
                account_type_id=type_obj.id,
                account_number=account_num,
                status=f"名義:{holder_name}",
            )
            session.add(new_asset)
            session.commit()

            st.success(f"✅ {bank_name} {branch_name} の口座情報を登録しました！")
            # 完了後、セッションを閉じる
            session.close()

        except Exception as e:
            st.error(f"DB保存エラー: {e}")
            return


if __name__ == "__main__":
    main()
