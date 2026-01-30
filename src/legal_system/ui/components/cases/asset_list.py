# src/legal_system/ui/components/cases/asset_list.py

import json
import pandas as pd
import streamlit as st
from sqlalchemy import desc
from src.legal_system.models.tables import FinancialAsset, FileRegistry, BankMaster

def render_bank_account_list(session, case_id: int):
    """
    銀行口座リストの表示と簡易編集 (既存機能)
    """
    st.subheader("🏦 銀行・金融資産管理")
    
    # asset_type="BANK" または Null (互換性のため) のものを表示
    assets = session.query(FinancialAsset).filter(
        FinancialAsset.case_id == case_id,
        (FinancialAsset.asset_type == "BANK") | (FinancialAsset.asset_type == None)
    ).all()
    
    if assets:
        for a in assets:
            b = a.bank_ref.bank_name if a.bank_ref else "不明"
            br = a.branch_ref.branch_name if a.branch_ref else ""
            
            with st.expander(f"🏦 {b} {br} ({a.account_number})"):
                c1, c2 = st.columns(2)
                nb = c1.number_input("残高", value=int(a.balance), key=f"ab_{a.id}")
                ns = c2.text_input("状況", value=a.status, key=f"as_{a.id}")
                
                if st.button("更新", key=f"ub_{a.id}"):
                    a.balance = nb
                    a.status = ns
                    session.commit()
                    st.toast("保存しました")
    else:
        st.info("登録された銀行口座はありません。")

def render_securities_list(session, case_id: int):
    """
    証券・その他資産の管理 (CRUD機能)
    銘柄ごとの明細をJSONから復元して編集可能にする
    """
    st.subheader("📈 証券・投資信託・その他資産")
    
    # 証券資産の取得
    assets = session.query(FinancialAsset).filter(
        FinancialAsset.case_id == case_id,
        FinancialAsset.asset_type == "SECURITY"
    ).all()
    
    if not assets:
        st.info("登録された証券口座はありません。「AI受信トレイ」から報告書を取り込むか、新規登録してください。")
        # ここに手動登録ボタンを追加することも可能
        return

    for asset in assets:
        sec_name = asset.bank_ref.bank_name if asset.bank_ref else "不明な証券会社"
        branch = asset.branch_ref.branch_name if asset.branch_ref else "-"
        acc_num = asset.account_number or "不明"
        
        # 合計評価額の表示
        label = f"📈 {sec_name} ({branch}) - 口座: {acc_num} | 評価額: {asset.balance:,.0f}円"
        
        with st.expander(label, expanded=False):
            # -------------------------------------------------
            # 1. 明細データのロード (FileRegistryからJSONを取得)
            # -------------------------------------------------
            # この資産に紐づく最新の「証券取引報告書」データを検索
            # (bank_id と case_id で紐付け)
            linked_file = session.query(FileRegistry).filter(
                FileRegistry.case_id == case_id,
                FileRegistry.doc_type == "securities_statement"
            ).order_by(desc(FileRegistry.registered_at)).all()
            
            # 銀行名が一致するファイルを探す (簡易マッチング)
            target_file_record = None
            extracted_json = {}
            
            # FileRegistryにbank_idがあればベストだが、なければextracted_data内のbank_nameで探す
            for f in linked_file:
                try:
                    data = json.loads(f.extracted_data or "{}")
                    if data.get("bank_name") == sec_name:
                        target_file_record = f
                        extracted_json = data
                        break
                except: continue
            
            # 明細データの取り出し
            meta = extracted_json.get("meta", {})
            holdings = meta.get("holdings", [])
            
            # データがない場合の初期値
            if not holdings:
                holdings = [{"name": "", "quantity": "", "category": "株式", "valuation": 0}]

            st.markdown("###### 📊 保有銘柄明細 (編集・追加・削除可)")
            
            df_holdings = pd.DataFrame(holdings)
            
            # 編集用テーブル
            edited_df = st.data_editor(
                df_holdings,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn("銘柄・ファンド名", required=True, width="large"),
                    "quantity": st.column_config.TextColumn("数量 (株/口)", width="medium"),
                    "category": st.column_config.SelectboxColumn("種別", options=["株式", "投資信託", "債券", "MRF", "預り金", "その他"], width="small"),
                    "valuation": st.column_config.NumberColumn("評価額 (円)", format="%d", width="medium")
                },
                key=f"sec_edit_{asset.id}"
            )
            
            # 自動計算
            current_total = 0
            try:
                current_total = edited_df["valuation"].sum()
            except: pass
            
            c_calc, c_act = st.columns([2, 1])
            c_calc.info(f"💰 明細合計: {current_total:,.0f} 円")
            
            if c_act.button("💾 明細を保存 & 残高更新", key=f"save_sec_{asset.id}", type="primary"):
                try:
                    # 1. FinancialAsset (親) の更新
                    asset.balance = float(current_total)
                    asset.status = "確認済"
                    
                    # 2. 明細データ (JSON) の保存
                    # 紐づくファイルレコードがあれば更新、なければ警告（またはダミー作成）
                    clean_holdings = edited_df.to_dict(orient="records")
                    clean_holdings = [h for h in clean_holdings if h.get("name")] # 空行除去
                    
                    if target_file_record:
                        # 既存JSONの一部だけ更新
                        try:
                            current_data = json.loads(target_file_record.extracted_data)
                        except:
                            current_data = {"meta": {}}
                        
                        if "meta" not in current_data: current_data["meta"] = {}
                        
                        current_data["meta"]["holdings"] = clean_holdings
                        current_data["meta"]["balance"] = float(current_total) # 合計も同期
                        
                        target_file_record.extracted_data = json.dumps(current_data, ensure_ascii=False)
                        st.toast("明細データを更新しました")
                    else:
                        # ファイルがない場合（手動登録など）の対応
                        # ここではシンプルにFinancialAssetのみ更新し、警告を出す
                        st.warning("紐づくスキャンデータが見つからないため、明細は一時的な保存となります。")

                    session.commit()
                    st.success("✅ 資産情報を更新しました！")
                    import time
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"保存エラー: {e}")