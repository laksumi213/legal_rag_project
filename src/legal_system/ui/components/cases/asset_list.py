# 資産リスト
# src/legal_system/ui/components/cases/asset_list.py
import streamlit as st
from src.legal_system.models.tables import FinancialAsset

def render_bank_account_list(session, case_id: int):
    """
    銀行口座リストの表示と簡易編集
    """
    st.subheader("🏦 銀行・金融資産管理")
    
    assets = session.query(FinancialAsset).filter_by(case_id=case_id).all()
    
    if assets:
        for a in assets:
            b = a.bank_ref.bank_name if a.bank_ref else "不明"
            br = a.branch_ref.branch_name if a.branch_ref else ""
            
            with st.expander(f"{b} {br} ({a.account_number})"):
                c1, c2 = st.columns(2)
                nb = c1.number_input("残高", value=int(a.balance), key=f"ab_{a.id}")
                ns = c2.text_input("状況", value=a.status, key=f"as_{a.id}")
                
                if st.button("更新", key=f"ub_{a.id}"):
                    a.balance = nb
                    a.status = ns
                    session.commit()
                    st.toast("保存しました")
    else:
        st.info("登録された口座はありません。サイドバーの「預貯金口座入力フォーム」等から追加してください。")