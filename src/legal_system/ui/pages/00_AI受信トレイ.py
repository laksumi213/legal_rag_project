# src/legal_system/ui/pages/00_AI受信トレイ.py

import streamlit as st
import pandas as pd
import json
import os
import sys
from sqlalchemy import desc

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import FileRegistry, Case, FinancialAsset, Heir, Deceased
from src.legal_system.ui.components.document_viewer import render_enhanced_document_viewer
from src.services.folder_service import open_local_folder
from src.services.deceased_service import update_case_folder_path

st.set_page_config(page_title="AI受信トレイ", layout="wide", page_icon="🤖")

def render_ai_inbox():
    st.title("🤖 AI処理 インボックス")
    st.markdown("スキャナから取り込まれた書類を確認し、本登録を行います。")

    db_manager = DatabaseManager()
    
    with db_manager._get_session() as db:
        pending_files = db.query(FileRegistry).filter(
            FileRegistry.status == "PENDING"
        ).order_by(desc(FileRegistry.registered_at)).all()

        if not pending_files:
            st.success("🎉 未確認の書類はありません。すべて処理済みです！")
            if st.button("再読み込み"): st.rerun()
            return

        col_list, col_detail = st.columns([1.5, 2])

        # 1. 左側: 受信リスト & プレビュー
        with col_list:
            st.subheader(f"受信リスト ({len(pending_files)}件)")
            
            def format_option(file_hash):
                f = next((pf for pf in pending_files if pf.file_hash == file_hash), None)
                if not f: return "Unknown"
                time_str = f.registered_at.strftime('%m/%d %H:%M')
                return f"[{time_str}] {f.doc_type} ({f.filename})"

            selected_hash = st.radio(
                "確認する書類を選択:",
                [f.file_hash for f in pending_files],
                format_func=format_option
            )
            target_file = next(f for f in pending_files if f.file_hash == selected_hash)
            
            st.divider()
            st.markdown("##### 📄 書類プレビュー")
            if target_file.file_path and os.path.exists(target_file.file_path):
                try:
                    with open(target_file.file_path, "rb") as f:
                        file_bytes = f.read()
                    file_ext = os.path.splitext(target_file.filename)[1].lower()
                    mime_type = "application/pdf" if file_ext == ".pdf" else "image/jpeg"
                    
                    render_enhanced_document_viewer(
                        file_bytes, 
                        mime_type, 
                        key_prefix=f"inbox_view_{target_file.file_hash}", 
                        base_width=600
                    )
                except Exception as e:
                    st.error(f"プレビュー表示エラー: {e}")
            else:
                st.warning("⚠️ ファイル実体が見つかりません")

        # 2. 右側: 詳細 & アクション
        with col_detail:
            st.subheader(f"📝 {target_file.filename}")
            
            try:
                ai_data = json.loads(target_file.extracted_data or "{}")
            except:
                ai_data = {}

            meta = ai_data.get('meta', {})
            
            # AI判定タイプ
            ai_detected_type = target_file.doc_type or ai_data.get('doc_type', 'other')

            # 案件情報の取得 (DB上の関連付け)
            related_case = None
            if target_file.case_id:
                related_case = db.query(Case).filter(Case.case_id == target_file.case_id).first()
            
            # --- 情報カード ---
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                conf_val = int((target_file.ai_confidence or 0.0) * 100)
                c1.metric("信頼度", f"{conf_val}%")
                c2.metric("書類種別(AI)", ai_detected_type)
                c3.metric("自動紐付案件", related_case.case_number if related_case else "不明")

            st.markdown("#### データ確認・編集")
            
            # 1. 書類種別の手動選択
            type_map = {
                "証券・金融商品 (明細あり)": "securities_statement",
                "銀行・預金 (デフォルト)": "balance_certificate",
                "通帳": "bank_passbook",
                "推定相続人一覧": "heir_list",
                "固定資産税・納税通知書": "tax_payment_notice",
                "その他 (保存のみ)": "other"
            }
            
            # ★UI側での補正ロジック: 銀行名に「証券」が含まれていれば、DB値が何であれ証券モードを優先する
            extracted_bank_name = ai_data.get('bank_name', '')
            is_securities_detected = "証券" in extracted_bank_name or "證券" in extracted_bank_name
            
            default_key = "その他 (保存のみ)"
            
            if ai_detected_type == "heir_list": 
                default_key = "推定相続人一覧"
            elif ai_detected_type == "tax_payment_notice": 
                default_key = "固定資産税・納税通知書"
            elif ai_detected_type == "securities_statement" or (is_securities_detected and ai_detected_type == "balance_certificate"): 
                # 証券モード優先
                default_key = "証券・金融商品 (明細あり)"
            elif ai_detected_type in ["balance_certificate", "bank_passbook", "transaction_detail"]: 
                default_key = "銀行・預金 (デフォルト)"
            
            selected_type_label = st.selectbox(
                "書類種別 (手動修正)", 
                list(type_map.keys()),
                index=list(type_map.keys()).index(default_key),
                key=f"type_sel_{target_file.file_hash}"
            )
            current_doc_type = type_map[selected_type_label]
            
            # 2. 案件選択
            cases = db.query(Case).all()
            case_options = {c.case_id: f"{c.case_number} {c.client_name}" for c in cases}
            default_idx = 0
            if target_file.case_id in case_options:
                default_idx = list(case_options.keys()).index(target_file.case_id)
            
            selected_case_id = st.selectbox(
                "紐付け案件", 
                options=list(case_options.keys()),
                format_func=lambda x: case_options[x],
                index=default_idx,
                key=f"case_sel_{target_file.file_hash}"
            )

            # 紐付け先案件へのクイックアクセス
            target_case_obj = None
            if selected_case_id:
                target_case_obj = db.query(Case).get(selected_case_id)

            if target_case_obj:
                st.caption("🚀 紐付け先のクイックアクセス")
                with st.container(border=True):
                    qc1, qc2 = st.columns([1, 2], gap="small")
                    
                    with qc1:
                        if target_case_obj.kintone_record_id:
                            url = f"https://chester-tax.cybozu.com/k/242/show#record={target_case_obj.kintone_record_id}"
                            st.link_button("🔗 Kintoneで開く", url, type="secondary", use_container_width=True)
                        else:
                            st.button("🔗 連携なし", disabled=True, use_container_width=True)
                    
                    with qc2:
                        path_val = target_case_obj.folder_path or ""
                        col_path_in, col_open_btn = st.columns([3, 1])
                        new_path = col_path_in.text_input("Path", value=path_val, label_visibility="collapsed", key=f"fp_{target_file.file_hash}")
                        if col_open_btn.button("📂 開く", key=f"btn_open_{target_file.file_hash}", use_container_width=True):
                            if new_path: 
                                open_local_folder(new_path)
                                if new_path != path_val:
                                    update_case_folder_path(target_case_obj.case_id, new_path)
                                    st.rerun()
                        if new_path != path_val:
                            update_case_folder_path(target_case_obj.case_id, new_path)

            st.divider()

            # --- 3. フォーム分岐 ---
            
            # A. 証券・金融商品 (明細あり)
            if current_doc_type == "securities_statement":
                st.info("📈 証券会社の報告書として処理します。")
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    sec_name = st.text_input("証券会社名", value=ai_data.get('bank_name', ''), key=f"sec_n_{target_file.file_hash}")
                    sec_branch = st.text_input("本支店名", value=meta.get('branch_name', ''), key=f"sec_b_{target_file.file_hash}")
                with col_s2:
                    sec_acc = st.text_input("口座番号 (英数可)", value=meta.get('account_number', ''), key=f"sec_a_{target_file.file_hash}")
                    
                    # --- ★修正ポイント: float値をintに変換してWarningを解消 ---
                    raw_total = meta.get('balance', 0)
                    sec_total = 0
                    try:
                        if isinstance(raw_total, str):
                            sec_total = int(float(raw_total.replace(",", "").strip()))
                        else:
                            sec_total = int(float(raw_total))
                    except:
                        sec_total = 0
                    
                    # valueにint型を渡す
                    sec_total = st.number_input("合計評価額 (円)", value=sec_total, format="%d", key=f"sec_t_{target_file.file_hash}")

                st.markdown("###### 保有銘柄リスト (銘柄・数量・評価額)")
                
                holdings_data = meta.get("holdings", [])
                if not holdings_data:
                    holdings_data = [{"name": "", "quantity": "", "category": "株式", "valuation": 0}]
                
                df_holdings = pd.DataFrame(holdings_data)
                
                try:
                    # quantity カラムを文字列型に強制変換（単位追記などを許容するため）
                    if "quantity" in df_holdings.columns:
                        df_holdings["quantity"] = df_holdings["quantity"].astype(str)
                    
                    # valuation カラムを整数型に安全に変換（浮動小数点警告を防ぐ）
                    if "valuation" in df_holdings.columns:
                        df_holdings["valuation"] = pd.to_numeric(df_holdings["valuation"], errors='coerce').fillna(0).astype(int)
                except Exception as e:
                    st.warning(f"データ型変換時の警告: {e}")
                
                edited_holdings = st.data_editor(
                    df_holdings,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "name": st.column_config.TextColumn("銘柄名 (ファンド名)", required=True, width="large"),
                        "quantity": st.column_config.TextColumn("数量/口数", width="medium"),
                        "category": st.column_config.SelectboxColumn("種別", options=["株式", "投資信託", "債券", "MRF", "預り金", "その他"], width="small"),
                        "valuation": st.column_config.NumberColumn("評価額", format="%d", width="small")
                    },
                    key=f"holdings_editor_{target_file.file_hash}"
                )
                
                calc_total = 0
                if not edited_holdings.empty and "valuation" in edited_holdings.columns:
                    calc_total = edited_holdings["valuation"].sum()
                
                if calc_total > 0 and calc_total != sec_total:
                    st.caption(f"💡 明細合計: {calc_total:,.0f} 円")

                st.divider()
                
                if st.button("✅ 承認して登録 (証券資産+明細)", type="primary", use_container_width=True):
                    ai_data['bank_name'] = sec_name
                    ai_data['doc_type'] = "securities_statement" 
                    ai_data.setdefault('meta', {})
                    
                    clean_holdings = edited_holdings.to_dict(orient="records")
                    clean_holdings = [h for h in clean_holdings if h.get("name")]
                    
                    ai_data['meta'].update({
                        'branch_name': sec_branch,
                        'account_number': sec_acc,
                        'balance': sec_total,
                        'holdings': clean_holdings
                    })
                    
                    target_file.doc_type = "securities_statement"
                    target_file.extracted_data = json.dumps(ai_data, ensure_ascii=False)
                    db.commit()

                    from src.services.scanner_service import ScannerService
                    svc = ScannerService()
                    svc.process_pending_buffer(target_file.file_hash, selected_case_id, override_doc_type="securities_statement")
                    
                    st.success(f"登録完了！ 銘柄数: {len(clean_holdings)}")
                    st.rerun()

            # B. 推定相続人一覧
            elif current_doc_type == "heir_list":
                st.info("👨‍👩‍👧‍👦 相続人情報が検出されました。内容を確認・修正してください。")
                heirs_data = meta.get("heirs", [])
                if not heirs_data:
                    heirs_data = [{"name": "", "relationship": "", "zip_code": "", "address": "", "occupation": "", "honseki": "", "birth_date": "", "phone": ""}]
                
                df_heirs = pd.DataFrame(heirs_data)
                
                edited_heirs_df = st.data_editor(
                    df_heirs,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "name": st.column_config.TextColumn("氏名", required=True),
                        "relationship": st.column_config.TextColumn("続柄", width="small"),
                        "zip_code": st.column_config.TextColumn("郵便番号", width="small"),
                        "address": st.column_config.TextColumn("住所", width="large"),
                        "occupation": st.column_config.TextColumn("職業", width="small"),
                        "honseki": st.column_config.TextColumn("本籍地", width="medium"),
                        "birth_date": st.column_config.TextColumn("生年月日(YYYY-MM-DD)"),
                        "phone": st.column_config.TextColumn("電話番号")
                    },
                    key=f"heir_editor_{target_file.file_hash}"
                )

                st.divider()
                if st.button("✅ 承認して登録 (相続人を追加)", type="primary", use_container_width=True):
                    if not target_case_obj or not target_case_obj.deceased_ref:
                        st.error("案件に被相続人情報がありません。")
                    else:
                        deceased_id = target_case_obj.deceased_ref.id
                        count = 0
                        try:
                            from src.services.deceased_service import add_heir
                            for index, row in edited_heirs_df.iterrows():
                                if not row.get("name"): continue
                                add_heir(
                                    deceased_id=deceased_id,
                                    name=row["name"],
                                    rel=row.get("relationship", ""),
                                    dob=row.get("birth_date"),
                                    zip_code=row.get("zip_code", ""), 
                                    street=row.get("address", ""),    
                                    occupation=row.get("occupation", ""), 
                                    hometown=row.get("honseki", ""),      
                                    phone_contacts=[{"value": row.get("phone")}] if row.get("phone") else []
                                )
                                count += 1
                            
                            from src.services.scanner_service import ScannerService
                            svc = ScannerService()
                            svc.process_pending_buffer(target_file.file_hash, selected_case_id, override_doc_type="heir_list")
                            
                            st.success(f"{count}名の相続人を追加し、書類を登録しました！")
                            st.rerun()
                        except Exception as e:
                            st.error(f"登録エラー: {e}")

            # C. 固定資産税 (保存のみ)
            elif current_doc_type == "tax_payment_notice":
                st.info("💴 固定資産税納税通知書として保存します。")
                st.caption("※資産データの自動登録は行われません。")
                st.divider()
                if st.button("✅ 承認してファイル保存", type="primary", use_container_width=True):
                    from src.services.scanner_service import ScannerService
                    svc = ScannerService()
                    success = svc.process_pending_buffer(target_file.file_hash, selected_case_id, override_doc_type="tax_payment_notice")
                    
                    if success:
                        st.success("保存完了！")
                        st.rerun()
                    else:
                        st.error("保存に失敗しました。")

            # D. その他 (保存のみ)
            elif current_doc_type == "other":
                st.info("📁 「その他」書類として保存します。")
                st.divider()
                if st.button("✅ 承認してファイル保存", type="primary", use_container_width=True):
                    from src.services.scanner_service import ScannerService
                    svc = ScannerService()
                    success = svc.process_pending_buffer(target_file.file_hash, selected_case_id, override_doc_type="other")
                    if success:
                        st.success("保存完了！")
                        st.rerun()

            # E. 銀行・預金 (デフォルト)
            else:
                st.caption("🏦 銀行・預金情報")
                edited_vals = {}
                col_f1, col_f2 = st.columns(2)
                
                with col_f1:
                    edited_vals['bank_name'] = st.text_input("銀行名", value=ai_data.get('bank_name', ''), key=f"bn_{target_file.file_hash}")
                    edited_vals['branch_name'] = st.text_input("支店名", value=meta.get('branch_name', ''), key=f"br_{target_file.file_hash}")
                
                with col_f2:
                    raw_balance = meta.get('balance', 0)
                    try:
                        if isinstance(raw_balance, str):
                            val_bal = float(raw_balance.replace(",", "").strip())
                        else:
                            val_bal = float(raw_balance)
                    except (ValueError, TypeError):
                        val_bal = 0.0

                    # こちらはフォーマット指定がないのでfloatのままでOKだが、念のためintキャストも可
                    edited_vals['balance'] = st.number_input("金額/残高", value=val_bal, key=f"bal_{target_file.file_hash}")
                    edited_vals['account_number'] = st.text_input("口座番号", value=meta.get('account_number', ''), key=f"an_{target_file.file_hash}")

                st.divider()
                
                b1, b2 = st.columns([1, 1])
                with b1:
                    if st.button("✅ 承認して登録 (資産追加)", type="primary", use_container_width=True, key=f"ok_{target_file.file_hash}"):
                        ai_data['bank_name'] = edited_vals['bank_name']
                        ai_data.setdefault('meta', {})
                        ai_data['meta'].update({
                            'branch_name': edited_vals['branch_name'],
                            'balance': edited_vals['balance'],
                            'account_number': edited_vals['account_number']
                        })
                        target_file.extracted_data = json.dumps(ai_data, ensure_ascii=False)
                        db.commit()

                        from src.services.scanner_service import ScannerService
                        svc = ScannerService()
                        svc.process_pending_buffer(target_file.file_hash, selected_case_id, override_doc_type=current_doc_type)
                        
                        st.success("処理完了！")
                        st.rerun()

            with b2 if 'b2' in locals() else st.container():
                if st.button("🗑️ 除外する", use_container_width=True, key=f"del_{target_file.file_hash}"):
                    target_file.status = "REJECTED"
                    db.commit()
                    st.rerun()

if __name__ == "__main__":
    render_ai_inbox()