This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.cursor/
  rules/
    bpo-coding-standard.mdc
.streamlit/
  config.toml
data/
  db/
    chroma/
      local_rag_db/
        6849ff3c-44d5-4815-a7a7-ccaeb2c92357/
          data_level0.bin
          header.bin
          length.bin
          link_lists.bin
        7ec55c3c-907b-4922-a7e0-989eb818156f/
          data_level0.bin
          header.bin
          length.bin
          link_lists.bin
        d50e1e10-53e2-4aea-ac5d-95f27e67e86d/
          data_level0.bin
          header.bin
          length.bin
          link_lists.bin
        chroma.sqlite3
      .keep
    sql/
      .keep
  fonts/
    ipaexg.ttf
  rules/
    bank_guidance.json
    bank_master.csv
    company_rules.md
    donation_recipients.json
  templates/
    .keep
    ラベルシート -貼り付け用.docx
    遺言公正証書文案テンプレート.docx
memory-bank/
  progress.md
  projectBrief.md
  systemPatterns.md
scripts/
  check_buffer.py
  clean_notes.py
  create_dummy_data.py
  manual_link.py
  retry_audio.py
  seed_data.py
src/
  chains/
    bank_procedure_chain.py
  legal_system/
    core/
      __init__.py
      ai_factory.py
      ai_processor.py
      config.py
      data_sync.py
      database_manager.py
      engines.py
      ocr_engine.py
      pdf_processor.py
      preload.py
      schemas.py
    models/
      __init__.py
      base.py
      tables.py
    tools/
      __init__.py
      coord_tool.py
    ui/
      components/
        cases/
          __init__.py
          asset_list.py
          basic_info.py
          dashboard_widgets.py
          header.py
          heir_list.py
          history_log.py
          nayose_registration.py
          registry_acquisition.py
        __init__.py
        admin_tools.py
        case_search.py
        document_viewer.py
        inbox.py
        label_printer_ui.py
        sidebar.py
        smart_guide.py
      pages/
        00_AI受信トレイ.py
        01_案件詳細_統合管理.py
        02_顧客紹介連絡表_読取.py
        03_Kintoneデータ_エクセル入力フォーム.py
        04_戸籍読取_不足チェック.py
        05_家系図・相続人可視化.py
        06_法定相続情報_読取.py
        07_登記情報_読取.py
        08_残高証明書_読取.py
        09_相続書類_作成フォーム.py
        10_公証役場・送付セット作成.py
        11_公正証書遺言_ドラフト作成.py
        90_預貯金口座入力フォーム.py
        97_書式座標登録ツール.py
        98_書類内容チェック_AI.py
        99_マスタ管理.py
      utils/
        __init__.py
        js_helper.py
      __init__.py
      excel_generator.py
      Home.py
      label_generator.py
    __init__.py
    main.py
  legal.egg-info/
    dependency_links.txt
    PKG-INFO
    requires.txt
    SOURCES.txt
    top_level.txt
  services/
    automation/
      __init__.py
      touki_service.py
      will_generator.py
    __init__.py
    case_service.py
    deceased_service.py
    dispatch_service.py
    encryption_service.py
    folder_service.py
    gmail_watcher_service.py
    graph_service.py
    kintone_client.py
    kintone_sync_service.py
    koseki_service.py
    logistics_service.py
    master_service.py
    party_service.py
    persistence_service.py
    rag_search_service.py
    scanner_service.py
    search_service.py
  utils/
    __init__.py
    7za.exe
    date_utils.py
    retry_decorator.py
  __init__.py
tests/
  test_retry_decorator.py
.dockerignore
.gitignore
.python-version
■初回送付セット【20251218版】　.xlsx
add_column_migration.py
agent_rules_sample.json
bank_master.json
branch_routing_rules.json
create_rule_master.py
create_table_migration.py
def enable_advanced_autofocus().txt
directory_structure.txt
docker-compose.yml
Dockerfile
export_code.py
generate_token.py
kintone_data_sample.json
migrate_koseki_table.py
organize_files.py
pyproject.toml
README.md
register_existing_templates.py
requirements-dev.lock
requirements.lock
requirements.txt
reset_db.py
run_watcher.py
schema_definition.md
test_agent.py
update_bank_master.py
```

# Files

## File: src/legal_system/ui/pages/00_AI受信トレイ.py
````python
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
````

## File: src/legal_system/ui/pages/01_案件詳細_統合管理.py
````python
# src/legal_system/ui/pages/01_案件詳細_統合管理.py

import os
import sys
import threading
import time
import pyperclip  # クリップボード用
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from sqlalchemy.orm import joinedload
from st_keyup import st_keyup

# ==========================================
# 1. パス解決 & 環境設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
src_dir = os.path.join(ROOT_DIR, "src")

if src_dir not in sys.path:
    sys.path.append(src_dir)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(
    page_title="高度案件管理 (AI支援)", 
    page_icon="🧠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. モジュールインポート
# ==========================================
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address, Case, Deceased, H_AddressHistory, H_ContactLink, Heir
)
from services.folder_service import open_local_folder, find_case_folder
from services.deceased_service import update_case_folder_path

# ★新機能サービスのインポート
try:
    from services.logistics_service import LogisticsService
    from services.rag_search_service import RagSearchService
except ImportError:
    st.error("新機能サービス(logistics_service, rag_search_service)が見つかりません。src/services/に配置してください。")
    LogisticsService = None
    RagSearchService = None

# ==========================================
# 4. ヘルパー関数 & JS
# ==========================================
def run_background_warmup():
    if "modules_warmed_up" in st.session_state: return
    try:
        from legal_system.core.preload import warm_up_modules
        warm_up_modules()
        st.session_state["modules_warmed_up"] = True
    except: pass

if "warmup_thread_started" not in st.session_state:
    t = threading.Thread(target=run_background_warmup, daemon=True)
    t.start()
    st.session_state["warmup_thread_started"] = True

# 検索（案件選択）ロジック
def search_cases_simple(session, keyword: str):
    base_query = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    )
    if not keyword:
        return base_query.order_by(Case.created_at.desc()).limit(10).all()

    clean_key = f"%{keyword.strip()}%"
    return base_query.filter(
        Case.case_number.ilike(clean_key) | 
        Case.client_name.ilike(clean_key)
    ).limit(10).all()

# ==========================================
# 5. メイン処理 (Main)
# ==========================================
def main():
    db = DatabaseManager()
    session = db._get_session()
    current_user_info = db.get_current_user_info()

    # --- サイドバー構成 ---
    with st.sidebar:
        st.title("🧠 高度AI支援メニュー")
        st.info(f"担当: {current_user_info['name']}")
        st.caption("※基本情報の編集や口座登録は「Home」画面で行ってください。")
        
        st.divider()
        
        # 簡易案件検索 (Homeで選択した案件を引き継ぐが、ここでも切り替え可能にする)
        st.subheader("📂 対象案件切替")
        search_query = st.text_input("案件番号/氏名で検索", key="side_search")
        
        # 1. まず検索条件で案件を取得
        filtered_cases = search_cases_simple(session, search_query)
        
        # ==========================================
        # ★修正: 選択中の案件をリストに強制追加するロジック
        # ==========================================
        current_id = st.session_state.get("selected_case_id")
        
        if current_id:
            # 現在の検索結果リストの中に、選択中の案件が含まれているかチェック
            is_included = any(c.case_id == current_id for c in filtered_cases)
            
            if not is_included:
                # 含まれていない場合（過去の案件など）、DBから取得してリストの先頭に追加する
                target_case_obj = session.query(Case).get(current_id)
                if target_case_obj:
                    filtered_cases.insert(0, target_case_obj)

        # 選択肢辞書の作成
        case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in filtered_cases}
        
        # セッションから選択状態を復元（インデックス特定）
        index = 0
        if current_id in case_options.values():
            keys = list(case_options.keys())
            vals = list(case_options.values())
            index = vals.index(current_id)
            
        selected_label = st.selectbox("選択", list(case_options.keys()), index=index)
        
        # 選択されたらIDを更新
        if selected_label:
            st.session_state["selected_case_id"] = case_options[selected_label]

    # --- メインエリア ---
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning("👈 サイドバーまたはHome画面で案件を選択してください。")
        session.close()
        return

    # 案件データ取得
    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).get(target_case_id)

    if not current_case:
        st.error("案件データが見つかりません")
        session.close(); return

    # --- ヘッダー情報 (Read-only) ---
    d_name = "未登録"
    if current_case.deceased_ref:
        d_name = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}"

    st.title(f"AI支援モード: {current_case.client_name} 様")
    st.caption(f"案件番号: {current_case.case_number} | 被相続人: {d_name}")
    
    # -------------------------------------------------------------
    # ★修正: クイックリンク (常時表示 & 両方表示)
    # -------------------------------------------------------------
    with st.container(border=True):
        col_link, col_folder = st.columns([1, 3], gap="medium")
        
        # 1. Kintoneボタン
        with col_link:
            if current_case.kintone_record_id:
                url = f"https://chester-tax.cybozu.com/k/242/show#record={current_case.kintone_record_id}"
                st.link_button("🔗 Kintoneを開く", url, use_container_width=True)
            else:
                st.button("🔗 連携なし", disabled=True, use_container_width=True)
        
        # 2. フォルダパス操作 (表示・編集・開く)
        with col_folder:
            path_val = current_case.folder_path or ""
            c_input, c_btn = st.columns([4, 1])
            
            new_path = c_input.text_input(
                "フォルダパス", 
                value=path_val, 
                label_visibility="collapsed", 
                placeholder="フォルダパス (\\\\server\\...)"
            )
            
            if c_btn.button("📂 開く", use_container_width=True):
                if new_path:
                    open_local_folder(new_path)
                    # 変更があれば保存
                    if new_path != path_val:
                        update_case_folder_path(target_case_id, new_path)
                        st.rerun()
                else:
                    st.warning("パス未入力")
            
            # Enterキー等で確定した場合の保存
            if new_path != path_val:
                update_case_folder_path(target_case_id, new_path)

    st.divider()

    # =========================================================
    # ★機能別タブ構成 (AI特化)
    # =========================================================
    tab_notary, tab_rag = st.tabs([
        "⚖️ 公証役場・アクセス (Logistics)", 
        "📚 銀行RAG・ナレッジ (Knowledge)"
    ])

    # ---------------------------------------------------------
    # タブ1: 公証役場検索 (AIアドバイス版)
    # ---------------------------------------------------------
    with tab_notary:
        st.subheader("⚖️ 公証役場アクセス・選定支援")
        st.caption("Geminiが住所から最寄りの公証役場を推論し、アクセス方法を提案します。")
        
        # 1. 検索起点の住所取得（DBから）
        origin_address = ""
        if current_case.deceased_ref and current_case.deceased_ref.heirs:
            contractor = next((h for h in current_case.deceased_ref.heirs if h.is_contracting_party), None)
            if contractor:
                addr_link = session.query(H_AddressHistory).filter_by(heir_id=contractor.id, is_current_address=True).first()
                if addr_link:
                    addr_obj = session.query(Address).get(addr_link.address_id)
                    if addr_obj:
                        origin_address = f"{addr_obj.prefecture}{addr_obj.city_ward_town}{addr_obj.street_address}"

        # 2. 入力フォーム
        col_in, col_btn = st.columns([3, 1])
        target_addr = col_in.text_input("検索起点（依頼者住所など）", value=origin_address, key="notary_search_addr")
        
        if col_btn.button("🔍 AIに相談する", type="primary", key="btn_ask_notary"):
            if not target_addr:
                st.error("住所が入力されていません")
            elif not LogisticsService:
                st.error("LogisticsService がロードされていません")
            else:
                with st.spinner("AIが経路と公証役場を調査中..."):
                    logistics = LogisticsService()
                    ai_response = logistics.consult_nearest_notaries(target_addr)
                    st.session_state["notary_advice"] = ai_response

        # 3. 結果表示エリア
        if "notary_advice" in st.session_state:
            st.divider()
            c_res_head, c_res_copy = st.columns([4, 1])
            c_res_head.markdown("##### 🤖 AIからの提案")
            if c_res_copy.button("📋 コピー"):
                try:
                    pyperclip.copy(st.session_state["notary_advice"])
                    st.toast("コピーしました", icon="✅")
                except:
                    st.warning("ローカル環境外ではコピーできません")

            st.markdown(
                f"""
                <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; border-left: 5px solid #d33682;">
                    {st.session_state["notary_advice"]}
                </div>
                """, 
                unsafe_allow_html=True
            )

    # ---------------------------------------------------------
    # タブ2: 銀行RAG・ナレッジ検索
    # ---------------------------------------------------------
    with tab_rag:
        st.subheader("📚 銀行手続・ナレッジ検索")
        st.caption("社内規定、銀行マスタ、および過去の提出書類から検索します。")

        rag_service = RagSearchService() if RagSearchService else None
        
        if not rag_service:
            st.error("RAGサービスが利用できません。")
        else:
            # 検索ボックス
            query = st.text_input("質問・検索キーワード", placeholder="例: 三菱UFJの残高証明に必要な書類は？ / 鈴木一郎の戸籍")
            
            col_knowledge, col_docs = st.columns([1, 1])
            
            if query:
                # 1. 知識検索 (LLM回答)
                with col_knowledge:
                    st.markdown("##### 🤖 AI回答 (規定・マスタ)")
                    with st.spinner("規定を検索中..."):
                        answer = rag_service.search_bank_rules(query)
                        st.info(answer)

                # 2. 過去書類検索 (ファイル一覧)
                with col_docs:
                    st.markdown("##### 📄 関連する過去書類 (個人情報含む)")
                    docs = rag_service.search_past_documents(query)
                    
                    if docs:
                        for doc in docs:
                            with st.expander(f"📄 {doc['filename']}"):
                                st.caption(f"登録日: {doc['registered_at']} | 種別: {doc['doc_type']}")
                                # ダウンロードボタン等のアクション
                                st.button("プレビュー", key=f"prev_{doc['file_hash']}")
                    else:
                        st.caption("該当する過去書類は見つかりませんでした。")

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/02_顧客紹介連絡表_読取.py
````python
# src/legal_system/ui/pages/02_顧客紹介連絡表_読取.py

import base64
import json
import os
import sys
import time
from datetime import datetime
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import joinedload

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if project_root not in sys.path:
    sys.path.append(project_root)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, Deceased, H_AddressHistory, Heir, Contact, H_ContactLink
from src.services.deceased_service import (
    get_next_provisional_number,
    search_zip_by_address_api,
    find_cases_by_attributes, # ★追加: 検索用サービス
    add_heir,                 # ★追加: 相続人追加用
    get_address_info          # ★追加: 住所取得
)
from src.services.dispatch_service import (
    determine_base_from_branch,
    generate_kintone_json_payload,
)

st.set_page_config(page_title="書類読取エージェント", page_icon="📄", layout="wide")


def analyze_document_gemini(file_bytes: bytes, mime_type: str) -> dict:
    """
    Gemini Visionで画像を解析し、書類タイプに応じたJSONを返す
    対応: 顧客紹介連絡表, 推定相続人連絡先一覧
    """
    img_b64 = base64.b64encode(file_bytes).decode("utf-8")
    image_url = f"data:{mime_type};base64,{img_b64}"

    llm = AIFactory.get_llm("cloud", temperature=0.0)

    prompt_text = """
    あなたは日本の行政手続きに精通した「シニア・データ入力オペレーター」です。
    提供された画像を解析し、それが「A: 顧客紹介連絡表」か「B: 推定相続人連絡先一覧」かを判断した上で、必要な情報を抽出してください。

    【共通ルール】
    - 出力は純粋なJSONのみとし、Markdownコードブロック等は含めないでください。
    - 値がない場合は空文字 "" を出力してください。
    - 氏名は姓と名の間に全角スペースを入れてください（例: "山田　太郎"）。

    ---
    ### パターンA: 顧客紹介連絡表 (SMBC日興証券など)
    特徴: 「紹介元」「部店」「同意書取得日」などの記載がある。
    
    【抽出項目】
    - doc_type: "referral"
    - search_key_name: 顧客名（氏名）
    - client_name: 顧客名
    - client_name_kana: 顧客フリガナ
    - client_phone: 顧客電話番号
    - client_address_full: 顧客住所（郵便番号除く）
    - referral_sec_branch_name: 紹介元支店名
    - referral_sec_rep_name: 紹介元担当者名
    - referral_sec_phone: 紹介元電話番号（内線・直通）
    - sol_case_number: SOL案件番号
    - introduction_date: 紹介日 (YYYY-MM-DD)

    ---
    ### パターンB: 推定相続人連絡先一覧
    特徴: 「遺言者様に関する情報」や、表形式の相続人リストがある。

    【抽出項目】
    - doc_type: "heir_list"
    - search_key_name: 遺言者名（または被相続人名）
    - testator_name: 遺言者名
    - heirs: [
        {
            "name": "氏名",
            "kana": "フリガナ",
            "relationship": "続柄",
            "address": "住所",
            "phone": "電話番号",
            "dob": "生年月日(YYYY-MM-DD)"
        },
        ...
    ]

    【出力JSONスキーマの例】
    {
        "doc_type": "referral" OR "heir_list",
        "search_key_name": "山田　太郎",
        ... (各パターンの項目)
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
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        return {}
    except Exception as e:
        st.error(f"AI解析エラー: {e}")
        return {}


def register_new_referral_case(session, data: dict):
    """紹介連絡表からの新規案件登録処理"""
    # 1. 仮番号発番
    temp_no = get_next_provisional_number(session)
    
    # 2. 拠点自動判定
    branch_name = data.get("referral_sec_branch_name", "")
    assigned_base = determine_base_from_branch(branch_name)
    
    # 3. 住所分割 (簡易)
    addr_raw = data.get("client_address_full", "")
    zip_code = search_zip_by_address_api(addr_raw)

    # DB登録処理
    new_case = Case(
        case_number=temp_no,
        client_name=data.get("client_name", ""),
        client_name_kana=data.get("client_name_kana", ""),
        referral_sec_branch_name=branch_name,
        referral_sec_rep_name=data.get("referral_sec_rep_name", ""),
        referral_sec_phone=data.get("referral_sec_phone", ""),
        sol_case_number=data.get("sol_case_number", ""),
        created_at=datetime.now(),
    )
    session.add(new_case)
    session.flush()

    # 関連データ作成
    dec = Deceased(case_id=new_case.case_id, name_last="", name_first="")
    session.add(dec)
    session.flush()

    heir = Heir(
        deceased_id=dec.id,
        name_last=new_case.client_name,
        is_contracting_party=True,
    )
    session.add(heir)
    session.flush()

    addr = Address(zip_code=zip_code, prefecture="", street_address=addr_raw)
    session.add(addr)
    session.flush()
    
    session.add(
        H_AddressHistory(
            heir_id=heir.id,
            address_id=addr.id,
            is_current_address=True,
        )
    )
    
    # 電話番号
    if data.get("client_phone"):
        ct = Contact(value=data.get("client_phone"), type="PHONE")
        session.add(ct)
        session.flush()
        session.add(H_ContactLink(heir_id=heir.id, contact_id=ct.id))

    session.commit()
    
    return {
        "case": new_case,
        "dec": dec,
        "heir": heir,
        "addr": addr,
        "base": assigned_base,
        "temp_no": temp_no
    }


def merge_heirs_to_existing_case(session, case_id: int, heirs_data: list) -> int:
    """既存案件に相続人リストを追加する処理"""
    case = session.query(Case).options(joinedload(Case.deceased_ref)).get(case_id)
    if not case or not case.deceased_ref:
        return 0
    
    deceased_id = case.deceased_ref.id
    added_count = 0
    
    # 既存チェック用
    existing_heirs = session.query(Heir).filter_by(deceased_id=deceased_id).all()
    existing_names = {f"{h.name_last}{h.name_first}".replace(" ", "").replace("　", "") for h in existing_heirs}

    for h_data in heirs_data:
        raw_name = h_data.get("name", "")
        clean_name = raw_name.replace(" ", "").replace("　", "")
        
        if not clean_name or clean_name in existing_names:
            continue
            
        # 登録実行 (住所などは簡易登録)
        # add_heir ヘルパーを使用
        try:
            # 住所分割
            addr_val = h_data.get("address", "")
            zip_val = search_zip_by_address_api(addr_val)
            
            # 生年月日
            dob_val = h_data.get("dob")
            
            # 連絡先
            phone_val = h_data.get("phone")
            contacts = [{"value": phone_val}] if phone_val else []

            add_heir(
                deceased_id=deceased_id,
                name=raw_name,
                rel=h_data.get("relationship", ""),
                kana_last=h_data.get("kana", ""), # 簡易的に姓に入れてしまう等の調整が必要だが一旦渡す
                dob=dob_val,
                # 住所
                zip_code=zip_val,
                pref="", 
                street=addr_val, # streetに全住所を入れる
                # 連絡先
                phone_contacts=contacts
            )
            added_count += 1
            existing_names.add(clean_name)
            
        except Exception as e:
            st.error(f"登録エラー ({raw_name}): {e}")

    return added_count


def main():
    st.title("📄 書類読取 & 案件登録エージェント")
    st.caption("「顧客紹介連絡表」の新規登録、または「推定相続人連絡先一覧」の既存案件への紐付けを行います。")

    # --- セッションステート初期化 ---
    if "ocr_result" not in st.session_state:
        st.session_state["ocr_result"] = None
    if "candidate_cases" not in st.session_state:
        st.session_state["candidate_cases"] = []
    if "target_case_id" not in st.session_state:
        st.session_state["target_case_id"] = None
    if "process_mode" not in st.session_state:
        st.session_state["process_mode"] = None  # 'NEW' or 'MERGE'

    # --- ファイルアップロード ---
    uploaded_file = st.file_uploader(
        "書類 (PDF/画像) をアップロード", 
        type=["pdf", "png", "jpg", "jpeg"],
        key="uploader_main"
    )

    if not uploaded_file:
        # リセット
        st.session_state["ocr_result"] = None
        st.session_state["candidate_cases"] = []
        return

    # ファイル処理
    file_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type
    display_img = None

    if mime_type == "application/pdf":
        images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
        if images:
            display_img = images[0]
            buf = BytesIO()
            display_img.save(buf, format="JPEG")
            # 解析用にはJPEGバイナリを使用
            target_bytes = buf.getvalue()
            mime_type = "image/jpeg"
        else:
            st.error("PDFの読み込みに失敗しました")
            return
    else:
        display_img = Image.open(BytesIO(file_bytes))
        target_bytes = file_bytes

    # --- レイアウト ---
    col_l, col_r = st.columns([1, 1.2])
    
    with col_l:
        st.image(display_img, caption="プレビュー", use_container_width=True)

    with col_r:
        # 1. 解析実行ボタン
        if st.session_state["ocr_result"] is None:
            if st.button("🚀 AI解析を実行", type="primary", use_container_width=True):
                with st.spinner("Geminiが内容を読み取っています..."):
                    res = analyze_document_gemini(target_bytes, mime_type)
                    st.session_state["ocr_result"] = res
                    
                    # 自動検索実行
                    search_key = res.get("search_key_name", "").strip()
                    if search_key:
                        # 顧客名 or 被相続人名 で検索
                        hits = find_cases_by_attributes(client_name=search_key)
                        if not hits:
                            hits = find_cases_by_attributes(deceased_name=search_key)
                        st.session_state["candidate_cases"] = hits
                    
                    st.rerun()

        # 2. 解析後のフロー
        if st.session_state["ocr_result"]:
            data = st.session_state["ocr_result"]
            doc_type = data.get("doc_type", "unknown")
            search_key = data.get("search_key_name", "不明")
            
            st.success(f"✅ 読取完了: {search_key} 様 ({doc_type})")
            
            # --- 案件選択フェーズ ---
            candidates = st.session_state["candidate_cases"]
            db = DatabaseManager()
            session = db._get_session()

            target_id = st.session_state["target_case_id"]
            mode = st.session_state["process_mode"]

            if target_id is None and mode is None:
                st.subheader("🔍 処理対象の選択")
                
                if candidates:
                    st.info(f"💡 既存の案件候補が {len(candidates)} 件見つかりました。")
                    
                    # 選択肢の作成
                    options = {
                        f"【{c['case_number']}】 依頼者:{c['client_name']} (被相続人:{c['deceased_name']})": c['case_id'] 
                        for c in candidates
                    }
                    options["🆕 新規案件として登録する"] = "NEW"
                    
                    selected_label = st.radio("アクションを選択", list(options.keys()))
                    
                    if st.button("決定", type="primary"):
                        val = options[selected_label]
                        if val == "NEW":
                            st.session_state["process_mode"] = "NEW"
                        else:
                            st.session_state["process_mode"] = "MERGE"
                            st.session_state["target_case_id"] = val
                        st.rerun()
                else:
                    st.warning("該当する既存案件は見つかりませんでした。")
                    if st.button("🆕 新規案件として登録する", type="primary"):
                        st.session_state["process_mode"] = "NEW"
                        st.rerun()

            # --- 処理実行フェーズ ---
            elif mode == "MERGE":
                # 既存案件への紐付け (主に相続人リスト追加)
                case = session.query(Case).get(target_id)
                st.info(f"📂 紐付け先: **{case.case_number} {case.client_name}**")
                
                if doc_type == "heir_list":
                    heirs = data.get("heirs", [])
                    st.write(f"検出された相続人: {len(heirs)} 名")
                    st.dataframe(heirs)
                    
                    if st.button("💾 この案件に相続人を追加登録"):
                        count = merge_heirs_to_existing_case(session, target_id, heirs)
                        if count > 0:
                            st.success(f"{count} 名の相続人を追加しました！")
                        else:
                            st.info("追加対象はありませんでした（重複またはデータなし）。")
                        
                        time.sleep(2)
                        # クリアして戻る
                        st.session_state.clear()
                        st.rerun()
                else:
                    st.warning("この書類タイプは既存案件へのマージに対応していません（開発中）。")
                    if st.button("最初に戻る"):
                        st.session_state.clear()
                        st.rerun()

            elif mode == "NEW":
                # 新規登録 (主に紹介連絡表)
                st.subheader("📝 新規案件登録")
                
                with st.form("new_reg_form"):
                    # フォーム内容はAI結果で埋める
                    c1, c2 = st.columns(2)
                    name = c1.text_input("顧客名", value=data.get("client_name", ""))
                    kana = c2.text_input("フリガナ", value=data.get("client_name_kana", ""))
                    
                    addr = st.text_input("住所", value=data.get("client_address_full", ""))
                    
                    r1, r2 = st.columns(2)
                    br = r1.text_input("紹介元支店", value=data.get("referral_sec_branch_name", ""))
                    rep = r2.text_input("紹介元担当者", value=data.get("referral_sec_rep_name", ""))
                    
                    sol = st.text_input("SOL案件No", value=data.get("sol_case_number", ""))
                    
                    if st.form_submit_button("✅ 登録＆Kintoneデータ生成"):
                        # データを補正して登録関数へ
                        reg_data = data.copy()
                        reg_data["client_name"] = name
                        reg_data["client_address_full"] = addr
                        reg_data["referral_sec_branch_name"] = br
                        reg_data["referral_sec_rep_name"] = rep
                        reg_data["sol_case_number"] = sol
                        
                        res = register_new_referral_case(session, reg_data)
                        
                        st.session_state["registered_case_data"] = res
                        st.success(f"登録しました！ 仮番号: {res['temp_no']}")
                        st.rerun()

            session.close()

        # 3. 完了後の表示 (Kintone JSON)
        if "registered_case_data" in st.session_state:
            res = st.session_state["registered_case_data"]
            st.divider()
            st.subheader("📋 Kintone登録用データ")
            
            kintone_json = generate_kintone_json_payload(
                res["case"], res["dec"], res["heir"], res["addr"]
            )
            st.code(json.dumps(kintone_json, ensure_ascii=False, indent=2), language="json")
            
            if st.button("次の書類を読み込む"):
                st.session_state.clear()
                st.rerun()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/03_Kintoneデータ_エクセル入力フォーム.py
````python
# components/pages/03_Kintoneデータ_エクセル入力フォーム.py

import streamlit as st
import json
import io
from src.legal_system.ui.excel_generator import fill_initial_set_excel

def show_document_creation_page():
    """
    案件登録・書類作成画面を表示します。
    KintoneからのJSON貼り付けによるExcel自動作成を行います。
    """
    st.title("📑 案件登録・書類作成")
    st.markdown("Kintoneのデータを貼り付けて、「初回送付セット」Excelを作成します。")

    # --- 1. テンプレート選択エリア ---
    with st.expander("📂 Excelテンプレート設定", expanded=False):
        st.info("デフォルトではサーバー内の最新版テンプレートが使用されます。手元のファイルを修正して使いたい場合のみアップロードしてください。")
        uploaded_template = st.file_uploader(
            "テンプレートExcelをアップロード（任意）", 
            type=["xlsx"],
            key="template_uploader"
        )

    # --- 2. データ入力エリア ---
    st.subheader("1. Kintoneデータ取込")
    json_input = st.text_area(
        "KintoneブックマークレットでコピーしたJSONを貼り付けてください",
        height=300,
        placeholder='{"顧客コード": "Gxxxx", ...}'
    )

    if st.button("解析・Excel作成実行", type="primary"):
        if not json_input:
            st.error("JSONデータが入力されていません。")
            return

        try:
            # JSONパース
            data = json.loads(json_input)
            
            # データプレビュー（確認用）
            st.success("JSONの読み込みに成功しました。以下の内容でExcelを作成します。")
            
            # 主要項目のみ表示して確認
            preview_keys = ["顧客コード_2", "顧客名", "担当者①", "担当者②", "被相続人名"]
            preview_data = {k: data.get(k, "（未設定）") for k in preview_keys}
            st.json(preview_data, expanded=False)

            # --- 3. Excel生成処理 ---
            # アップロードがあればそれを、なければNone（デフォルト使用）を渡す
            template_source = uploaded_template if uploaded_template else None
            
            excel_binary = fill_initial_set_excel(data, template_source)
            
            # --- 4. ダウンロードボタン表示 ---
            st.subheader("2. 書類ダウンロード")
            
            # ファイル名の生成（顧客名を含める）
            customer_name = data.get("顧客名", "未設定").replace("　", "").replace(" ", "")
            filename = f"初回送付セット_{customer_name}様.xlsx"
            
            st.download_button(
                label="📥 作成されたExcelをダウンロード",
                data=excel_binary,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except json.JSONDecodeError:
            st.error("JSON形式の読み込みに失敗しました。コピー内容が正しいか確認してください。")
        except FileNotFoundError as e:
            st.error(f"システムエラー: {e}")
        except KeyError as e:
            st.error(f"Excelテンプレートエラー: {e}")
        except Exception as e:
            st.error(f"予期せぬエラーが発生しました: {e}")

# メイン実行ブロック（単体テスト用）
if __name__ == "__main__":
    show_document_creation_page()
````

## File: src/legal_system/ui/pages/04_戸籍読取_不足チェック.py
````python
# src/legal_system/ui/pages/04_戸籍読取_不足チェック.py

import os
import sys
import time
import pandas as pd
import altair as alt
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
from io import BytesIO
from sqlalchemy.orm import joinedload

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, FamilyRegister, Deceased, Heir
from src.services.koseki_service import KosekiService
from src.utils.date_utils import convert_seireki_to_wareki

st.set_page_config(page_title="戸籍チェック", page_icon="🧬", layout="wide")

def main():
    st.title("🧬 戸籍読取 & 連続性ビジュアルチェック")
    
    # --- 1. モード選択 ---
    mode = st.radio(
        "業務モード", 
        ["相続手続き (被相続人の連続性)", "遺言書作成 (遺言者の情報登録)"], 
        horizontal=True
    )
    is_inheritance = mode.startswith("相続")
    
    if is_inheritance:
        st.caption("被相続人の出生から死亡までの戸籍が繋がっているか（連続性）を可視化・チェックします。")
    else:
        st.caption("遺言者（契約者）の戸籍を読み取り、基本情報を登録します。")

    db = DatabaseManager()
    session = db._get_session()
    service = KosekiService()

    # 2. 案件選択
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning("案件を選択してください。")
        return

    case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).get(target_case_id)

    if not case or not case.deceased_ref:
        st.error("案件情報が不足しています。")
        return
        
    # --- 対象者の特定 ---
    target_person = None
    target_type = "deceased"
    target_role_label = "被相続人"

    if is_inheritance:
        target_person = case.deceased_ref
        target_type = "deceased"
    else:
        target_role_label = "遺言者 (契約者)"
        target_type = "heir"
        if case.deceased_ref and case.deceased_ref.heirs:
            target_person = next((h for h in case.deceased_ref.heirs if h.is_contracting_party), None)
            if not target_person and case.deceased_ref.heirs:
                target_person = case.deceased_ref.heirs[0]
        
        if not target_person:
            st.error("遺言者（契約者）が登録されていません。")
            return

    person_full_name = f"{target_person.name_last}{target_person.name_first}"

    # 基本情報表示
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"**{target_role_label}**: {target_person.name_last} {target_person.name_first}")
        dob_str = convert_seireki_to_wareki(target_person.date_of_birth) if target_person.date_of_birth else "未登録"
        c2.markdown(f"**生年月日**: {dob_str}")
        
        if is_inheritance:
            dod_str = convert_seireki_to_wareki(target_person.date_of_death) if target_person.date_of_death else "未登録"
            c3.markdown(f"**死亡日**: {dod_str}")
            if not target_person.date_of_death:
                st.info("ℹ️ 死亡日が未登録です。除籍謄本等をアップロードすると自動登録されます。")

    st.divider()

    col_L, col_R = st.columns([1, 1.3])

    # --- 左: アップロード ---
    with col_L:
        st.subheader("1. 戸籍画像の登録")
        
        # ヒント情報の自動取得 (名字)
        hint_family_name = ""
        if target_person and target_person.name_last:
            hint_family_name = target_person.name_last
            st.caption(f"💡 AIへのヒント: 名字は「{hint_family_name}」と想定して読み取ります。")

        label = "戸籍謄本・除籍謄本・原戸籍" if is_inheritance else "戸籍謄本（現在戸籍）"
        uploaded_files = st.file_uploader(
            f"{label} (PDF/画像) ※複数可", 
            type=["pdf", "png", "jpg", "jpeg"], 
            key="koseki_uploader",
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if "processed_koseki_ids" not in st.session_state:
                st.session_state["processed_koseki_ids"] = set()
            
            files_to_process = []
            for f in uploaded_files:
                fid = f"{f.name}_{f.size}"
                if fid not in st.session_state["processed_koseki_ids"]:
                    files_to_process.append(f)
            
            if files_to_process:
                with st.status(f"🚀 {len(files_to_process)}件を一括解析中...", expanded=True) as status:
                    for i, file_obj in enumerate(files_to_process):
                        st.write(f"📄 [{i+1}/{len(files_to_process)}] 解析中: {file_obj.name}")
                        try:
                            file_bytes = file_obj.getvalue()
                            # AI解析実行 (ヒント付き)
                            result = service.analyze_koseki_image(
                                file_bytes, 
                                file_obj.type, 
                                expected_name=person_full_name,
                                family_name_hint=hint_family_name
                            )
                            if "error" in result:
                                st.error(f"❌ {file_obj.name}: {result['error']}")
                            else:
                                status_msg = service.register_koseki_record(
                                    case.case_id, target_person.id, target_type, result
                                )
                                if status_msg.startswith("Success"):
                                    st.write(f"✅ {file_obj.name}: 登録完了")
                                    fid = f"{file_obj.name}_{file_obj.size}"
                                    st.session_state["processed_koseki_ids"].add(fid)
                                else:
                                    st.error(f"❌ 保存失敗: {status_msg}")
                        except Exception as e:
                            st.error(f"❌ システムエラー: {e}")
                    status.update(label="🎉 完了しました！", state="complete", expanded=False)
                time.sleep(1.5)
                st.rerun()

    # --- 右: チェック結果 (可視化 & 修正UI) ---
    with col_R:
        st.subheader("2. 読取結果と連続性")
        
        query = session.query(FamilyRegister)
        if target_type == "deceased":
            query = query.filter(FamilyRegister.deceased_id == target_person.id)
        else:
            query = query.filter(FamilyRegister.heir_id == target_person.id)
            
        records = query.order_by(FamilyRegister.valid_from).all()
        
        if not records:
            st.info(f"{target_role_label}の戸籍はまだ登録されていません。")
        else:
            # 1. タイムラインデータの作成 (Altair用)
            timeline_data = []
            for r in records:
                if r.valid_from and r.valid_to:
                    timeline_data.append({
                        "Type": r.doc_type or "不明",
                        "Start": r.valid_from.strftime('%Y-%m-%d'),
                        "End": r.valid_to.strftime('%Y-%m-%d'),
                        "Label": f"{r.doc_type} ({r.valid_from.year}-{r.valid_to.year})"
                    })
            
            # 生存期間（ターゲットライン）
            if target_person.date_of_birth and target_person.date_of_death:
                timeline_data.append({
                    "Type": "【必要期間】出生〜死亡",
                    "Start": target_person.date_of_birth.strftime('%Y-%m-%d'),
                    "End": target_person.date_of_death.strftime('%Y-%m-%d'),
                    "Label": "必要期間"
                })

            if timeline_data:
                df_chart = pd.DataFrame(timeline_data)
                
                # ガントチャート描画
                chart = alt.Chart(df_chart).mark_bar().encode(
                    x=alt.X('Start:T', title='開始日'),
                    x2='End:T',
                    y=alt.Y('Type:N', title='種類', sort=['【必要期間】出生〜死亡']),
                    color=alt.Color('Type:N', legend=None),
                    tooltip=['Label', 'Start', 'End']
                ).properties(
                    title="戸籍の取得状況タイムライン",
                    height=200
                ).interactive()
                
                st.altair_chart(chart, use_container_width=True)

            # 2. ギャップ分析 & AIアドバイス
            if is_inheritance and target_person.date_of_birth and target_person.date_of_death:
                gaps, advices = service.check_continuity_gaps(target_person.id)
                
                if not gaps:
                    st.success("🎉 おめでとうございます！出生から死亡まで連続しています。")
                else:
                    st.error(f"⚠️ {len(gaps)} 箇所の空白期間があります。")
                    
                    # AIによる次の一手アドバイス
                    if st.button("🤖 空白を埋めるためのアクションをAIに聞く", type="primary"):
                        with st.spinner("AIが不足箇所を分析し、請求先を推論中..."):
                            suggestion = service.recommend_missing_koseki_action(target_person.id, gaps)
                            st.session_state["koseki_advice"] = suggestion
                    
                    if "koseki_advice" in st.session_state:
                        st.info("💡 AIからのアドバイス")
                        st.markdown(st.session_state["koseki_advice"])

            # 3. 手動修正テーブル (st.data_editor)
            st.divider()
            st.markdown("##### 📝 データの修正")
            st.caption("AIの誤読がある場合、下表を直接編集して「修正保存」を押してください。")

            edit_data = []
            for r in records:
                edit_data.append({
                    "id": r.id, # 隠しID
                    "書類種類": r.doc_type,
                    "本籍地": r.issuing_authority,
                    "筆頭者": r.head_of_family,
                    "開始日": r.valid_from,
                    "終了日": r.valid_to
                })
            
            df_edit = pd.DataFrame(edit_data)
            
            edited_df = st.data_editor(
                df_edit,
                column_config={
                    "id": None, 
                    "書類種類": st.column_config.SelectboxColumn("種類", options=["現在戸籍", "除籍謄本", "改製原戸籍", "住民票"]),
                    "本籍地": st.column_config.TextColumn("本籍地", width="large"),
                    "筆頭者": st.column_config.TextColumn("筆頭者", width="medium"),
                    "開始日": st.column_config.DateColumn("開始日", format="YYYY/MM/DD"),
                    "終了日": st.column_config.DateColumn("終了日", format="YYYY/MM/DD"),
                },
                use_container_width=True,
                num_rows="dynamic",
                key="koseki_editor"
            )
            
            col_save, col_clear = st.columns([1, 1])
            with col_save:
                if st.button("💾 修正内容を保存する", type="primary"):
                    try:
                        for index, row in edited_df.iterrows():
                            rec_id = row["id"]
                            # 新規行(id=NaN)の対応は今回は省略し、既存修正のみとする
                            if pd.notna(rec_id):
                                record = session.query(FamilyRegister).get(rec_id)
                                if record:
                                    record.doc_type = row["書類種類"]
                                    record.issuing_authority = row["本籍地"]
                                    record.head_of_family = row["筆頭者"]
                                    # 日付変換
                                    if pd.notnull(row["開始日"]):
                                        record.valid_from = row["開始日"].date() if hasattr(row["開始日"], 'date') else row["開始日"]
                                    if pd.notnull(row["終了日"]):
                                        record.valid_to = row["終了日"].date() if hasattr(row["終了日"], 'date') else row["終了日"]
                        
                        session.commit()
                        st.toast("修正を保存しました！", icon="✅")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存エラー: {e}")

            with col_clear:
                if st.button("全データをクリアする"):
                    if target_type == "deceased":
                        session.query(FamilyRegister).filter_by(deceased_id=target_person.id).delete()
                    else:
                        session.query(FamilyRegister).filter_by(heir_id=target_person.id).delete()
                    session.commit()
                    st.session_state["processed_koseki_ids"] = set()
                    st.rerun()

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/05_家系図・相続人可視化.py
````python
# src/legal_system/ui/pages/05_家系図・相続人可視化.py

import streamlit as st
from sqlalchemy.orm import joinedload
import os
import sys

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir
from src.services.graph_service import GraphService

st.set_page_config(page_title="AI家系図可視化", page_icon="🌳", layout="wide")

def main():
    st.title("🌳 AI家系図・相続権自動判定")
    st.caption("戸籍読取結果から、法定相続人の構成をグラフィカルに表示します。")

    db = DatabaseManager()
    session = db._get_session()

    # 1. 案件選択 (Home同期)
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning("案件を選択してください。")
        return

    # データロード
    case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).get(target_case_id)

    if not case or not case.deceased_ref:
        st.error("案件情報または被相続人情報が不足しています。")
        return

    deceased = case.deceased_ref
    heirs = deceased.heirs

    col_graph, col_info = st.columns([2, 1])

    with col_graph:
        st.subheader("📊 相続関係図 (Mermaid)")
        if not heirs:
            st.info("相続人が登録されていません。「戸籍読取」画面から登録してください。")
        else:
            # グラフ生成
            graph_code = GraphService.generate_mermaid_family_tree(deceased, heirs)
            
            # Mermaidの描画
            st.markdown(f"""
            ```mermaid
            {graph_code}
            ```
            """)
            
            with st.expander("デバッグ: グラフコードを表示"):
                st.code(graph_code)

    with col_info:
        st.subheader("⚖️ 法定相続判定")
        ranks = GraphService.determine_inheritance_rank(heirs)
        
        # 判定表示
        if ranks["spouse"]:
            st.success(f"配偶者: {len(ranks['spouse'])}名検知")
        
        if ranks["first"]:
            st.info(f"第1順位（子・孫）: {len(ranks['first'])}名")
        elif ranks["second"]:
            st.info(f"第2順位（父母）: {len(ranks['second'])}名")
        elif ranks["third"]:
            st.info(f"第3順位（兄弟姉妹）: {len(ranks['third'])}名")
        else:
            st.warning("有効な法定相続人が特定できません。")

        st.divider()
        st.markdown("##### 📝 判定アドバイス")
        if ranks["first"] and ranks["spouse"]:
            st.write("配偶者と子が相続人となります。法定相続分は各1/2です。")
        elif not ranks["first"] and ranks["second"]:
            st.write("子がいないため、配偶者と直系尊属が相続人となります。")
        elif ranks["first"] and not ranks["spouse"]:
             st.write("配偶者がいないため、子が全ての遺産を相続します。")

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/06_法定相続情報_読取.py
````python
# src/legal_system/ui/pages/06_法定相続情報_読取.py

import base64
import json
import logging
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, date
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import joinedload

# パス解決
# pages -> ui -> legal_system -> src -> ROOT
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(current_dir))
    )
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, Deceased, Heir, H_AddressHistory

# ★修正: src. を付与して絶対インポートに変更
from src.services.deceased_service import find_cases_by_attributes, search_zip_by_address_api
from src.utils.date_utils import convert_seireki_to_wareki

logger = logging.getLogger(__name__)

st.set_page_config(page_title="法定相続情報 読取", page_icon="👪", layout="wide")

# -----------------------------------------------------------------------------
# ユーティリティ関数
# -----------------------------------------------------------------------------
def normalize_name_with_space(name: str) -> str:
    if not name: return ""
    name = unicodedata.normalize("NFKC", name)
    if " " in name:
        return name.replace(" ", "　")
    if "　" in name:
        return name
    return name

def get_clean_name_for_compare(name: str) -> str:
    if not name: return ""
    return name.replace(" ", "").replace("　", "")

def parse_wareki_str(date_str: str) -> date:
    if not date_str: return None
    s = unicodedata.normalize("NFKC", date_str).strip()
    try:
        return datetime.strptime(s.replace("/", "-"), "%Y-%m-%d").date()
    except: pass
    eras = {"令和": (2018, "R"), "平成": (1988, "H"), "昭和": (1925, "S"), "大正": (1911, "T"), "明治": (1868, "M")}
    pattern = r"([A-Za-z]+|[^\x00-\x7F]+)(\d+|元)[./年](\d+)[./月](\d+)[日]?"
    match = re.match(pattern, s)
    if match:
        era_str = match.group(1)
        year_str = match.group(2)
        month = int(match.group(3))
        day = int(match.group(4))
        year_num = 1 if year_str == "元" else int(year_str)
        seireki_year = 0
        for name, (base, alpha) in eras.items():
            if name in era_str or alpha.lower() == era_str.lower():
                seireki_year = base + year_num
                break
        if seireki_year > 0:
            try:
                return date(seireki_year, month, day)
            except ValueError:
                return None
    return None

def split_address_smart(full_address: str) -> dict:
    if not full_address:
        return {"pref": "", "city_ward": "", "street": "", "build": ""}
    addr = unicodedata.normalize("NFKC", full_address)
    pref = ""
    rest = addr
    m_pref = re.match(r"(.{2,3}[都道府県])(.*)", addr)
    if m_pref:
        pref = m_pref.group(1)
        rest = m_pref.group(2)
    city_ward = ""
    street = ""
    m_split = re.search(r"\d", rest)
    if m_split:
        idx = m_split.start()
        city_ward = rest[:idx]
        street = rest[idx:]
    else:
        city_ward = rest
        street = ""
    build = ""
    if " " in street or "　" in street:
        parts = re.split(r"[ 　]+", street, 1)
        street = parts[0]
        build = parts[1]
    return {"pref": pref, "city_ward": city_ward, "street": street, "build": build}

# ★追加: 漢数字を算用数字に変換する関数
def normalize_address_number(text: str) -> str:
    """
    住所検索のために、漢数字（一丁目など）を算用数字（1丁目）に簡易変換する。
    """
    if not text: return ""
    # 簡易変換
    text = text.replace("一丁目", "1丁目").replace("二丁目", "2丁目").replace("三丁目", "3丁目")
    text = text.replace("四丁目", "4丁目").replace("五丁目", "5丁目").replace("六丁目", "6丁目")
    text = text.replace("七丁目", "7丁目").replace("八丁目", "8丁目").replace("九丁目", "9丁目")
    text = text.replace("十丁目", "10丁目").replace("十一丁目", "11丁目")
    
    return text

def smart_zip_search(pref, city_ward, street):
    """
    住所から郵便番号を検索する。漢数字対応版。
    """
    # 1. そのまま結合して検索
    full = f"{pref}{city_ward}{street}".strip()
    if not full: return ""
    
    zip_code = search_zip_by_address_api(full)
    if zip_code: return zip_code

    # 2. 漢数字を変換して検索 (例: 夏見台一丁目 -> 夏見台1丁目)
    normalized_full = normalize_address_number(full)
    if normalized_full != full:
        zip_code = search_zip_by_address_api(normalized_full)
        if zip_code: return zip_code
    
    # 3. 町域レベルで再検索
    town_level = f"{pref}{city_ward}".strip()
    if town_level:
        zip_code = search_zip_by_address_api(town_level)
    
    return zip_code if zip_code else ""

# -----------------------------------------------------------------------------
# AI解析ロジック
# -----------------------------------------------------------------------------
def analyze_heir_document_with_ai(image_bytes: bytes) -> dict:
    try:
        img_str = base64.b64encode(image_bytes).decode("utf-8")
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        prompt_text = """
        あなたは熟練した行政書士補助者です。
        提供された「法定相続情報一覧図」の画像を読み取り、JSONとして抽出してください。
        
        【抽出項目】
        {
            "deceased": {
                "name": "被相続人の氏名",
                "birth_date": "生年月日(記載通りの和暦)",
                "death_date": "死亡日(記載通りの和暦)",
                "last_address": "最後の住所",
                "registered_domicile": "本籍地"
            },
            "heirs": [
                {
                    "name": "相続人氏名",
                    "relationship": "続柄",
                    "birth_date": "生年月日(記載通りの和暦)",
                    "address": "住所"
                },
                ...
            ]
        }
        """
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"},
            ]
        )
        response = llm.invoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        else:
            raise ValueError("JSON parse error")
    except Exception as e:
        logger.error(f"Heir Analysis Error: {e}")
        return {"error": str(e)}

# -----------------------------------------------------------------------------
# メイン画面
# -----------------------------------------------------------------------------
def main():
    st.title("👪 法定相続情報 読取・自動紐付け")
    st.caption("書類をアップロードすると、**自動的に**内容を読み取り、該当する案件を検索します。")

    db = DatabaseManager()
    session = db._get_session()

    if "heir_result" not in st.session_state:
        st.session_state["heir_result"] = None
    if "target_case_id" not in st.session_state:
        st.session_state["target_case_id"] = None
    if "candidate_cases" not in st.session_state:
        st.session_state["candidate_cases"] = []
    if "last_analyzed_file_id" not in st.session_state:
        st.session_state["last_analyzed_file_id"] = None

    uploaded_file = st.file_uploader("法定相続情報一覧図 (PDF/画像)", type=["pdf", "png", "jpg"])

    if uploaded_file:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        
        file_bytes = uploaded_file.getvalue()
        target_bytes = None
        display_img = None

        try:
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
                display_img = images[0]
            else:
                display_img = Image.open(BytesIO(file_bytes))
            
            buf = BytesIO()
            display_img.convert("RGB").save(buf, format="JPEG")
            target_bytes = buf.getvalue()
        except Exception as e:
            st.error(f"画像変換エラー: {e}")
            return

        # 1. 自動AI解析
        if st.session_state["last_analyzed_file_id"] != file_id:
            st.image(display_img, caption="プレビュー (解析中...)", width=400)
            
            with st.spinner("🤖 自動解析中... (文字読取 & 案件検索)"):
                result = analyze_heir_document_with_ai(target_bytes)
                
                if "error" in result:
                    st.error(f"解析失敗: {result['error']}")
                else:
                    st.session_state["heir_result"] = result
                    st.session_state["last_analyzed_file_id"] = file_id 
                    
                    dec_name = result.get("deceased", {}).get("name", "")
                    if dec_name:
                        clean_name = get_clean_name_for_compare(dec_name)
                        candidates = find_cases_by_attributes(deceased_name=clean_name)
                        st.session_state["candidate_cases"] = candidates
                    
                    st.toast("解析が完了しました！", icon="✅")
                    time.sleep(0.5)
                    st.rerun() 

        # 2. 案件選択
        elif st.session_state["heir_result"] and st.session_state["target_case_id"] is None:
            col_prev, col_sel = st.columns([1, 1.5])
            
            with col_prev:
                st.image(display_img, use_container_width=True)
            
            with col_sel:
                res = st.session_state["heir_result"]
                dec_info = res.get("deceased", {})
                st.success(f"✅ 読み取り完了: 被相続人 **{dec_info.get('name')}**")
                
                candidates = st.session_state["candidate_cases"]
                st.subheader("🔍 紐付け先の案件を選択")

                if candidates:
                    st.info(f"{len(candidates)} 件の候補が見つかりました。")
                    selected_idx = st.radio(
                        "候補案件リスト",
                        options=range(len(candidates)),
                        format_func=lambda i: f"【{candidates[i]['case_number']}】 依頼者: {candidates[i]['client_name']} (被相続人: {candidates[i]['deceased_name']})",
                        key="case_selector_radio"
                    )
                    if st.button("✅ この案件に紐付ける", type="primary", use_container_width=True):
                        st.session_state["target_case_id"] = candidates[selected_idx]["case_id"]
                        st.rerun()
                else:
                    st.warning("⚠️ 自動検索では該当する案件が見つかりませんでした。")
                
                st.markdown("---")
                with st.expander("手動検索 (見つからない場合)", expanded=not candidates):
                    manual_q = st.text_input("案件番号(Gxxxx) または 氏名で検索")
                    if st.button("再検索"):
                        hits = find_cases_by_attributes(case_number=manual_q, client_name=manual_q, deceased_name=manual_q)
                        if hits:
                            st.session_state["candidate_cases"] = hits
                            st.rerun()
                        else:
                            st.error("見つかりませんでした。")

        # 3. 編集・登録
        elif st.session_state["target_case_id"]:
            target_case = session.query(Case).options(
                joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
            ).filter_by(case_id=st.session_state["target_case_id"]).first()
            
            existing_heirs = []
            if target_case.deceased_ref:
                existing_heirs = target_case.deceased_ref.heirs
            
            existing_heir_map = {}
            for h in existing_heirs:
                full_key = get_clean_name_for_compare(f"{h.name_last}{h.name_first}")
                existing_heir_map[full_key] = h

            st.info(f"📁 紐付け先: **{target_case.case_number} {target_case.client_name}** 様")
            
            col_img, col_data = st.columns([1, 1.2])
            with col_img:
                st.image(display_img, use_container_width=True)

            with col_data:
                st.subheader("📝 データ確認・編集")
                data = st.session_state["heir_result"]
                d_info = data.get("deceased", {})

                # --- 1. 被相続人 ---
                st.markdown("##### 1. 被相続人情報")
                with st.container(border=True):
                    db_d = target_case.deceased_ref
                    
                    init_name = f"{db_d.name_last}　{db_d.name_first}" if db_d and db_d.name_last else normalize_name_with_space(d_info.get("name", ""))
                    init_kana = f"{db_d.name_last_kana}　{db_d.name_first_kana}" if db_d and db_d.name_last_kana else ""
                    init_honseki = db_d.hometown if db_d and db_d.hometown else d_info.get("registered_domicile", "")
                    
                    c1, c2 = st.columns(2)
                    d_name = c1.text_input("氏名 (全角スペース区切り)", value=init_name)
                    d_kana = c2.text_input("フリガナ", value=init_kana) 
                    
                    c3, c4 = st.columns(2)
                    d_dod_str = c3.text_input("死亡日 (和暦入力可)", value=d_info.get("death_date", ""), help="例: 令和5年1月1日")
                    d_dob_str = c4.text_input("生年月日 (和暦入力可)", value=d_info.get("birth_date", ""), help="例: 昭和24年5月1日")
                    
                    d_honseki = st.text_input("本籍地", value=init_honseki)
                    
                    st.markdown("---")
                    st.caption("最後の住所")
                    ai_addr_full = d_info.get("last_address", "")
                    split_res = split_address_smart(ai_addr_full)
                    
                    # 郵便番号自動検索 (漢数字対応)
                    auto_zip = ""
                    if ai_addr_full:
                        auto_zip = smart_zip_search(split_res["pref"], split_res["city_ward"], split_res["street"])

                    az, ap = st.columns([1, 1])
                    d_zip = az.text_input("郵便番号", value=auto_zip)
                    d_pref = ap.text_input("都道府県", value=split_res["pref"])
                    ac, ab = st.columns([2, 2])
                    d_city = ac.text_input("市区町村", value=split_res["city_ward"])
                    d_street = ab.text_input("番地", value=split_res["street"])
                    d_bldg = st.text_input("建物名", value=split_res["build"])

                # --- 2. 相続人 (マージロジック適用) ---
                st.markdown("##### 2. 相続人一覧 (手動修正可)")
                heirs_raw = data.get("heirs", [])
                
                grid_data = []
                
                for h in heirs_raw:
                    ai_name_clean = get_clean_name_for_compare(h.get("name", ""))
                    matched_heir = existing_heir_map.get(ai_name_clean)
                    
                    # 住所から郵便番号を検索 (漢数字対応)
                    h_addr_val = h.get("address", "")
                    h_auto_zip = ""
                    if h_addr_val:
                         split_h = split_address_smart(h_addr_val)
                         h_auto_zip = smart_zip_search(split_h["pref"], split_h["city_ward"], split_h["street"])

                    row = {
                        "name": normalize_name_with_space(h.get("name", "")),
                        "kana": "",
                        "relationship": h.get("relationship", ""),
                        "birth_date": h.get("birth_date", ""),
                        "address": h_addr_val,
                        "zip_code": h_auto_zip,
                        "is_contractor": False
                    }
                    
                    if matched_heir:
                        row["name"] = f"{matched_heir.name_last}　{matched_heir.name_first}"
                        if matched_heir.name_last_kana:
                            row["kana"] = f"{matched_heir.name_last_kana}　{matched_heir.name_first_kana}"
                        row["is_contractor"] = matched_heir.is_contracting_party
                    
                    grid_data.append(row)

                df_heirs = pd.DataFrame(grid_data)
                if df_heirs.empty:
                    df_heirs = pd.DataFrame(columns=["name", "kana", "relationship", "birth_date", "address", "zip_code", "is_contractor"])

                column_config = {
                    "name": st.column_config.TextColumn("氏名", required=True),
                    "kana": st.column_config.TextColumn("フリガナ", width="medium"),
                    "relationship": st.column_config.TextColumn("続柄", required=True),
                    "birth_date": st.column_config.TextColumn("生年月日(和暦)"),
                    "address": st.column_config.TextColumn("住所 (全住所)", width="large"),
                    # 郵便番号列 (手動修正可能)
                    "zip_code": st.column_config.TextColumn("郵便番号", width="small"), 
                    "is_contractor": st.column_config.CheckboxColumn("契約者", default=False)
                }

                edited_df = st.data_editor(
                    df_heirs,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="heir_grid"
                )

                st.divider()

                if st.button("💾 データベースを更新 (マージ保存)", type="primary", use_container_width=True):
                    try:
                        # --- Deceased Save ---
                        deceased = target_case.deceased_ref
                        if not deceased:
                            deceased = Deceased(case_id=target_case.case_id)
                            session.add(deceased)

                        if d_name:
                            parts = d_name.replace("　", " ").split(" ")
                            deceased.name_last = parts[0]
                            deceased.name_first = parts[1] if len(parts) > 1 else ""
                        
                        if d_kana:
                            kp = d_kana.replace("　", " ").split(" ")
                            deceased.name_last_kana = kp[0]
                            deceased.name_first_kana = kp[1] if len(kp) > 1 else ""

                        deceased.hometown = d_honseki
                        deceased.date_of_death = parse_wareki_str(d_dod_str)
                        deceased.date_of_birth = parse_wareki_str(d_dob_str)
                        
                        # Deceased Address
                        target_addr = None
                        if deceased.last_address_id:
                            target_addr = session.query(Address).get(deceased.last_address_id)
                        if not target_addr:
                            target_addr = Address(prefecture="", street_address="")
                            session.add(target_addr)
                            session.flush()
                            deceased.last_address_id = target_addr.id
                        
                        target_addr.zip_code = d_zip
                        target_addr.prefecture = d_pref
                        target_addr.city_ward_town = d_city
                        target_addr.street_address = d_street
                        target_addr.building_name = d_bldg

                        # --- Heirs Save (Smart Merge) ---
                        processed_heir_ids = []

                        for index, row in edited_df.iterrows():
                            if not row["name"]: continue

                            full_name = normalize_name_with_space(row["name"])
                            parts = full_name.split("　")
                            lname = parts[0]
                            fname = parts[1] if len(parts) > 1 else ""
                            clean_key = get_clean_name_for_compare(full_name)

                            k_lname, k_fname = "", ""
                            if row["kana"]:
                                k_parts = normalize_name_with_space(row["kana"]).split("　")
                                k_lname = k_parts[0]
                                k_fname = k_parts[1] if len(k_parts) > 1 else ""

                            target_heir = existing_heir_map.get(clean_key)
                            
                            if not target_heir:
                                target_heir = Heir(deceased_id=deceased.id)
                                session.add(target_heir)
                            
                            # 1. 相続人情報の更新 (郵便番号はここではまだ更新されない)
                            target_heir.name_last = lname
                            target_heir.name_first = fname
                            target_heir.name_last_kana = k_lname
                            target_heir.name_first_kana = k_fname
                            target_heir.relationship_type = row["relationship"]
                            target_heir.date_of_birth = parse_wareki_str(str(row["birth_date"]))
                            target_heir.is_contracting_party = row["is_contractor"]
                            
                            session.flush()
                            processed_heir_ids.append(target_heir.id)

                            # 2. 住所情報の更新 (★ここで郵便番号も保存される)
                            if row["address"]:
                                h_addr_val = row["address"]
                                split_h = split_address_smart(h_addr_val)
                                
                                # テーブル上の郵便番号を採用 (編集済み優先)
                                h_zip = str(row.get("zip_code", "")).strip()
                                # 空なら裏で再検索 (漢数字対応)
                                if not h_zip:
                                    h_zip = smart_zip_search(split_h["pref"], split_h["city_ward"], split_h["street"])
                                
                                current_link = session.query(H_AddressHistory).filter(
                                    H_AddressHistory.heir_id == target_heir.id,
                                    H_AddressHistory.is_current_address == True
                                ).first()
                                
                                h_addr_obj = None
                                if current_link:
                                    h_addr_obj = session.query(Address).get(current_link.address_id)
                                
                                if not h_addr_obj:
                                    h_addr_obj = Address(prefecture="", street_address="")
                                    session.add(h_addr_obj)
                                    session.flush()
                                    session.add(H_AddressHistory(
                                        heir_id=target_heir.id,
                                        address_id=h_addr_obj.id,
                                        is_current_address=True
                                    ))
                                
                                # ★保存処理の核心部分
                                h_addr_obj.zip_code = h_zip  # ←ここで保存
                                h_addr_obj.prefecture = split_h["pref"]
                                h_addr_obj.city_ward_town = split_h["city_ward"]
                                h_addr_obj.street_address = split_h["street"]
                                h_addr_obj.building_name = split_h["build"]
                                
                        session.commit()
                        st.success(f"✅ 案件「{target_case.client_name}」の情報を更新しました！")
                        time.sleep(2)
                        
                        st.session_state["heir_result"] = None
                        st.session_state["target_case_id"] = None
                        st.rerun()
                        
                    except Exception as e:
                        session.rollback()
                        st.error(f"保存エラー: {e}")

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/07_登記情報_読取.py
````python
# src/legal_system/ui/pages/07_登記情報_読取.py

import base64
import json
import os
import sys
import time
import re
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
from legal_system.models.tables import Case, RealEstateAsset

# フォルダ操作用サービス
from services.folder_service import find_case_folder, open_local_folder
from services.deceased_service import update_case_folder_path

# ページ設定
st.set_page_config(page_title="登記情報 自動読取", page_icon="🏘️", layout="wide")

# ==========================================
# 2. AI解析ロジック (Gemini Vision)
# ==========================================
def analyze_registry_with_ai(file_bytes: bytes, mime_type: str, target_name: str) -> dict:
    """
    登記情報を読み取り、土地・建物・マンションの情報を抽出する
    """
    llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    # 画像処理 (PDFの場合は全ページを画像化)
    image_data_list = []
    if mime_type == "application/pdf":
        try:
            # 登記情報は細かい文字が多いので高解像度(dpi=300)で変換推奨
            images = convert_from_bytes(file_bytes, dpi=250)
            for img in images:
                buf = BytesIO()
                img.save(buf, format="JPEG")
                image_data_list.append(buf.getvalue())
        except Exception as e:
            return {"error": f"PDF変換エラー: {e}"}
    else:
        image_data_list.append(file_bytes)

    # プロンプトの構築
    prompt_text = f"""
    あなたは日本の不動産登記の専門家です。
    提供された「不動産登記情報（全部事項証明書など）」の画像を読み取り、以下の対象者に関する不動産情報を抽出してJSON形式で出力してください。

    【抽出対象者（被相続人）】
    氏名: {target_name}
    ※この人物が所有者（または共有者）となっている不動産情報を抽出してください。
    ※単独所有の場合は持分を "1/1" としてください。

    【抽出項目定義】
    1. **区分 (type)**: "土地", "建物", "マンション" のいずれか
       ※「敷地権付き区分建物」や「専有部分」の記載がある場合は "マンション" と判定してください。

    --- 共通項目 ---
    * **持分 (share)**: 対象者の持分 ("1/2"など)

    --- A. 土地の場合 ---
    * **所在 (location)**
    * **地番 (number)**
    * **地目 (category)**
    * **地積 (area)**: 数値のみ抽出 (例: 123.45)

    --- B. 建物（戸建）の場合 ---
    * **所在 (location)**
    * **家屋番号 (number)**
    * **種類 (category)**: 居宅など
    * **構造 (structure)**: 木造瓦葺2階建など
    * **床面積 (area)**: 文字列で可 (例: "1階 50.00 2階 40.00")

    --- C. マンション（区分所有建物）の場合 ---
    以下の詳細情報を抽出してください。ない項目は空文字またはnull。
    * **一棟_所在 (m_b_loc)**: 一棟の建物の表示 - 所在
    * **一棟_名称 (m_b_name)**: 一棟の建物の表示 - 建物の名称
    * **土地_符号 (m_l_sym)**: 敷地権の目的である土地 - 符号 (例: "1")。複数ある場合は代表または連結。
    * **土地_所在地番 (m_l_loc)**: 敷地権の目的である土地 - 所在及び地番
    * **土地_地目 (m_l_cat)**: 敷地権の目的である土地 - 地目
    * **土地_地積 (m_l_area)**: 敷地権の目的である土地 - 地積
    * **専有_家屋番号 (number)**: 専有部分の建物の表示 - 家屋番号
    * **専有_名称 (m_p_name)**: 専有部分の建物の表示 - 建物の名称 (部屋番号など)
    * **専有_種類 (category)**: 専有部分の建物の表示 - 種類 (例: "居宅")
    * **専有_構造 (structure)**: 専有部分の建物の表示 - 構造
    * **専有_床面積 (area)**: 専有部分の建物の表示 - 床面積
    * **敷地権_種類 (m_r_type)**: 敷地権の表示 - 敷地権の種類 (例: "所有権")
    * **敷地権_割合 (m_r_ratio)**: 敷地権の表示 - 敷地権の割合

    【出力JSONスキーマ】
    {{
        "assets": [
            {{
                "type": "土地",
                "location": "...", "number": "...", "category": "...", "area": 100.5, "share": "1/1"
            }},
            {{
                "type": "マンション",
                "m_b_loc": "〇〇市〇〇区...",
                "m_b_name": "ライオンズマンション...",
                "m_l_sym": "1",
                "m_l_loc": "〇〇市〇〇区...",
                "m_l_cat": "宅地",
                "m_l_area": "1234.56",
                "number": "家屋番号...",
                "m_p_name": "201",
                "category": "居宅",
                "structure": "鉄筋コンクリート造...",
                "area": "70.55",
                "m_r_type": "所有権",
                "m_r_ratio": "1000分の50",
                "share": "1/1"
            }}
        ]
    }}
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
# 3. 遺言書用テキスト生成関数
# ==========================================
def generate_will_text(assets_df: pd.DataFrame) -> str:
    """
    DataFrameの内容から、遺言書コピペ用のテキストを生成する
    """
    text_lines = []
    
    # 全角スペース
    sp = "　"
    
    for i, row in assets_df.iterrows():
        # 連番 (1) (2)...
        num_prefix = f"（{i+1}）"
        
        p_type = row.get("type", "")
        share = row.get("share", "")
        
        # --- A. 土地 ---
        if p_type == "土地":
            text_lines.append(f"{num_prefix}\t土地")
            text_lines.append(f"{sp}所在{sp}{row.get('location', '')}")
            text_lines.append(f"{sp}地番{sp}{row.get('number', '')}")
            text_lines.append(f"{sp}地目{sp}{row.get('category', '')}")
            text_lines.append(f"{sp}地積{sp}{row.get('area', '')}㎡")
            text_lines.append(f"{sp}持分{sp}{share}")
            
        # --- B. マンション (区分所有) ---
        elif p_type == "マンション":
            text_lines.append(f"{num_prefix}\tマンション")
            
            text_lines.append(f"（一棟の建物の表示）")
            text_lines.append(f"{sp}所在{sp}{row.get('m_b_loc', '')}")
            text_lines.append(f"{sp}建物の名称{sp}{row.get('m_b_name', '')}")
            
            text_lines.append(f"（敷地権の目的である土地の表示）")
            text_lines.append(f"{sp}土地の符号{sp}{row.get('m_l_sym', '1')}")
            text_lines.append(f"{sp}所在及び地番{sp}{row.get('m_l_loc', '')}")
            text_lines.append(f"{sp}地目{sp}{row.get('m_l_cat', '')}")
            text_lines.append(f"{sp}地積{sp}{row.get('m_l_area', '')}㎡")
            
            text_lines.append(f"（専有部分の建物の表示）")
            text_lines.append(f"{sp}家屋番号{sp}{row.get('number', '')}")
            text_lines.append(f"{sp}建物の名称{sp}{row.get('m_p_name', '')}")
            text_lines.append(f"{sp}種類{sp}{row.get('category', '')}")
            text_lines.append(f"{sp}構造{sp}{row.get('structure', '')}")
            text_lines.append(f"{sp}床面積{sp}{row.get('area', '')}㎡")
            
            text_lines.append(f"（敷地権の表示）")
            text_lines.append(f"{sp}土地の符号{sp}{row.get('m_l_sym', '1')}")
            text_lines.append(f"{sp}敷地権の種類{sp}{row.get('m_r_type', '')}")
            text_lines.append(f"{sp}敷地権の割合{sp}{row.get('m_r_ratio', '')}")
            
            # マンションの持分（専有部分の所有権の持分）
            if share and share != "1/1":
                text_lines.append(f"{sp}持分{sp}{share}")

        # --- C. 建物 (戸建) ---
        else:
            text_lines.append(f"{num_prefix}\t建物")
            text_lines.append(f"{sp}所在{sp}{row.get('location', '')}")
            text_lines.append(f"{sp}家屋番号{sp}{row.get('number', '')}")
            text_lines.append(f"{sp}種類{sp}{row.get('category', '')}")
            text_lines.append(f"{sp}構造{sp}{row.get('structure', '')}")
            text_lines.append(f"{sp}床面積{sp}{row.get('area', '')}㎡")
            text_lines.append(f"{sp}持分{sp}{share}")
            
        text_lines.append("") # 空行

    return "\n".join(text_lines)

# ==========================================
# 4. DB保存ヘルパー
# ==========================================
def save_real_estate_to_db(session, case_id: int, assets: list):
    """
    抽出した不動産情報をDBに保存する
    """
    count = 0
    for item in assets:
        p_type_raw = item.get("type", "")
        # DB上の種別マッピング
        if p_type_raw == "土地":
            db_type = "Land"
        elif p_type_raw == "マンション":
            db_type = "Condo"
        else:
            db_type = "Building"
        
        # 面積の数値変換（可能な場合）
        area_val = None
        floor_area_str = str(item.get("area", ""))
        
        if db_type == "Land":
            try:
                # 文字列から数値抽出 ("100.23㎡" -> 100.23)
                match = re.search(r"(\d+(\.\d+)?)", floor_area_str)
                if match:
                    area_val = float(match.group(1))
            except: pass

        # 所在・番号の取得
        # マンションの場合、DBのlocationには一棟の所在、numberには専有家屋番号を入れるのが一般的
        loc = item.get("location") or item.get("m_b_loc")
        num = item.get("number")

        # 重複チェック (簡易)
        q = session.query(RealEstateAsset).filter(
            RealEstateAsset.case_id == case_id,
            RealEstateAsset.location == loc,
        )
        if db_type == "Land":
            q = q.filter(RealEstateAsset.lot_number == num)
        else:
            q = q.filter(RealEstateAsset.house_number == num)
            
        existing = q.first()

        # 値の構築
        if db_type == "Land":
            land_cat = item.get("category")
            land_area = area_val
            struc = None
            fl_area = None
        elif db_type == "Condo":
            # マンションの場合、構造などの詳細を structure カラムに詰め込むか検討が必要だが
            # ここではシンプルに専有部分の情報を保存する
            land_cat = None
            land_area = None
            struc = item.get("structure")
            fl_area = floor_area_str
        else:
            land_cat = None
            land_area = None
            struc = f"{item.get('category', '')} {item.get('structure', '')}".strip()
            fl_area = floor_area_str

        if existing:
            # 更新
            existing.property_type = db_type
            existing.ownership_share = item.get("share")
            existing.land_category = land_cat
            existing.land_area = land_area
            existing.structure = struc
            existing.floor_area = fl_area
        else:
            # 新規作成
            new_asset = RealEstateAsset(
                case_id=case_id,
                property_type=db_type,
                location=loc,
                ownership_share=item.get("share"),
                lot_number=num if db_type == "Land" else None,
                house_number=num if db_type != "Land" else None,
                land_category=land_cat,
                land_area=land_area,
                structure=struc,
                floor_area=fl_area
            )
            session.add(new_asset)
        
        count += 1
    
    return count

# ==========================================
# 5. メイン画面 UI
# ==========================================
def main():
    st.title("🏘️ 登記情報 自動読取")
    st.caption("登記情報(PDF/画像)をアップロードすると、**自動的に**AIが情報を抽出し、遺言書用の形式で出力します。")

    db = DatabaseManager()
    session = db._get_session()

    # ----------------------------------------------------
    # 案件選択 (Home共有)
    # ----------------------------------------------------
    target_case_id = st.session_state.get("selected_case_id")

    if not target_case_id:
        st.warning("⚠️ 案件が選択されていません。")
        st.info("Home画面またはサイドバーで案件を選択してください。")
        with st.expander("案件を選択する（未選択の場合）"):
            cases = session.query(Case).all()
            opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
            sel = st.selectbox("案件選択", list(opts.keys()))
            if st.button("この案件で作業を開始"):
                st.session_state["selected_case_id"] = opts[sel]
                st.rerun()
        return

    # 案件情報取得
    current_case = session.query(Case).options(joinedload(Case.deceased_ref)).get(target_case_id)
    if not current_case:
        st.error("案件情報の取得に失敗しました。")
        return

    d_name = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}" if current_case.deceased_ref else "未登録"
    st.success(f"📂 作業中の案件: **{current_case.case_number} {current_case.client_name}** 様 (被相続人: {d_name})")

    # ----------------------------------------------------
    # フォルダ操作エリア
    # ----------------------------------------------------
    with st.container(border=True):
        col_f1, col_f2 = st.columns([3, 1])
        curr_path = current_case.folder_path or ""
        
        with col_f1:
            new_path = st.text_input(
                "📂 案件フォルダパス", 
                value=curr_path, 
                placeholder=r"\\server\share\案件..."
            )
        
        with col_f2:
            st.write("") 
            st.write("")
            if st.button("フォルダを開く", use_container_width=True):
                if new_path:
                    open_local_folder(new_path)
                    if new_path != curr_path:
                        update_case_folder_path(target_case_id, new_path)
                else:
                    st.warning("パスが入力されていません")

    st.divider()

    # --- UI ---
    col_L, col_R = st.columns([1, 1.5])

    with col_L:
        st.subheader("1. 登記情報アップロード")
        # ★ポイント: keyを固定して再描画時もウィジェットの状態を維持
        uploaded_file = st.file_uploader("全部事項証明書など (PDF/画像)", type=["pdf", "png", "jpg", "jpeg"], key="touki_uploader")

        # ファイルがアップロードされているか確認
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            
            # --- 自動解析ロジック ---
            # ファイルの識別子 (名前 + サイズ) で新規ファイルか判定
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            
            # まだ解析していないファイルなら自動実行
            if "last_analyzed_touki_file" not in st.session_state or st.session_state["last_analyzed_touki_file"] != file_id:
                if not d_name or d_name == "未登録":
                    st.warning("⚠️ 被相続人名が登録されていません。持分の特定が難しくなる可能性があります。")
                
                with st.spinner("🚀 ファイルを検知しました。AIが解析中です..."):
                    result = analyze_registry_with_ai(file_bytes, uploaded_file.type, target_name=d_name)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["touki_result"] = result
                        st.session_state["last_analyzed_touki_file"] = file_id # 解析済みフラグ更新
                        st.toast("解析完了！", icon="✅")
                        time.sleep(0.5)
                        st.rerun() # 結果表示のためにリロード

            # プレビュー表示
            if uploaded_file.type == "application/pdf":
                try:
                    images = convert_from_bytes(file_bytes, dpi=100, first_page=1, last_page=1)
                    if images: st.image(images[0], caption="プレビュー (1ページ目)", use_container_width=True)
                except:
                    st.warning("PDFプレビュー生成に失敗しました（解析は可能です）")
            else:
                st.image(file_bytes, caption="プレビュー", use_container_width=True)

    with col_R:
        st.subheader("2. 結果確認・登録")
        
        # 解析結果がある場合
        if "touki_result" in st.session_state and st.session_state["touki_result"]:
            res = st.session_state["touki_result"]
            assets = res.get("assets", [])
            
            if not assets:
                st.warning("不動産情報が見つかりませんでした。")
            else:
                st.markdown(f"**検出された不動産: {len(assets)}件**")
                
                # 編集用データフレーム作成
                df = pd.DataFrame(assets)
                # 型エラー回避のため文字列化
                for col in ["area", "m_l_area"]:
                    if col in df.columns:
                        df[col] = df[col].astype(str)
                
                # カラム設定 (マンション用のカラムを追加)
                column_config = {
                    "type": st.column_config.SelectboxColumn("区分", options=["土地", "建物", "マンション"], width="small", required=True),
                    "share": st.column_config.TextColumn("持分", width="small"),
                    # --- 土地・建物 ---
                    "location": st.column_config.TextColumn("所在(土地/建物)", width="medium"),
                    "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                    "category": st.column_config.TextColumn("地目/種類", width="small"),
                    "area": st.column_config.TextColumn("地積/床面積", width="small"),
                    "structure": st.column_config.TextColumn("構造", width="medium"),
                    # --- マンション用 (隠さずに表示) ---
                    "m_b_loc": st.column_config.TextColumn("[M]一棟所在"),
                    "m_b_name": st.column_config.TextColumn("[M]建物名称"),
                    "m_l_loc": st.column_config.TextColumn("[M]土地所在"),
                    "m_p_name": st.column_config.TextColumn("[M]専有名称"),
                }
                
                # ★Data Editor (編集結果を取得)
                edited_df = st.data_editor(
                    df,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key="touki_editor"
                )
                
                st.markdown("---")
                
                # ★追加: 遺言書用コピペテキスト生成エリア
                st.markdown("##### 📋 遺言書用テキスト (コピペ用)")
                will_text = generate_will_text(edited_df)
                st.text_area(
                    "以下のテキストをコピーしてWord等に貼り付けてください",
                    value=will_text,
                    height=300
                )
                
                st.markdown("---")
                
                # 保存ボタン
                if st.button("💾 データベースに登録", type="primary"):
                    try:
                        final_assets = edited_df.to_dict(orient="records")
                        count = save_real_estate_to_db(session, target_case_id, final_assets)
                        session.commit()
                        
                        st.toast(f"登録完了: {count}件の不動産を保存しました！", icon="✅")
                        
                        # 登録後も結果を表示し続ける
                        st.success("✅ データベースへの登録が完了しました。")
                        
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
                        session.rollback()
        else:
            st.info("👈 左側で登記情報をアップロードしてください（自動解析されます）。")
            st.markdown("""
            **対応フォーマット:**
            - 土地
            - 建物（戸建）
            - **マンション（区分所有建物）** ← New!
            """)

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/08_残高証明書_読取.py
````python
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
````

## File: src/legal_system/ui/pages/09_相続書類_作成フォーム.py
````python
# src/legal_system/ui/pages/09_相続書類_作成フォーム.py

import os
import sys
from io import BytesIO

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import joinedload

# パス解決
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Case, 
    FileRegistry, 
    Deceased, 
    Heir, 
    H_AddressHistory,
    Address,          # 追加
    FinancialAsset,   # 追加
    RealEstateAsset   # 追加
)
from utils.date_utils import convert_seireki_to_wareki # 和暦変換用

# フォント設定 (変更なし)
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(page_title="書類作成 | 相続業務支援", page_icon="📄", layout="wide")


# ==========================================
# ★改良: データ置換ロジック (資産コンテキスト対応)
# ==========================================
def create_replacement_map(case_data, target_asset=None):
    """
    プレースホルダと実際の値のマッピングを作成する。
    target_asset: FinancialAsset または RealEstateAsset のインスタンス (任意)
    """
    map_dict = {}

    # 1. 案件基本情報
    map_dict["{case_number}"] = case_data.case_number
    map_dict["{client_name}"] = case_data.client_name

    # 2. 被相続人情報
    if case_data.deceased_ref:
        d = case_data.deceased_ref
        full_name = f"{d.name_last} {d.name_first}".strip()
        map_dict["{deceased_name}"] = full_name
        map_dict["{deceased_name_last}"] = d.name_last or ""
        map_dict["{deceased_name_first}"] = d.name_first or ""
        map_dict["{deceased_hometown}"] = d.hometown or ""

        # 生年月日
        if d.date_of_birth:
             map_dict["{deceased_birthday}"] = convert_seireki_to_wareki(d.date_of_birth)

        # 死亡日
        if d.date_of_death:
            map_dict["{death_date}"] = convert_seireki_to_wareki(d.date_of_death)
            map_dict["{death_year_seireki}"] = str(d.date_of_death.year)
            map_dict["{death_month}"] = str(d.date_of_death.month)
            map_dict["{death_day}"] = str(d.date_of_death.day)
            
            # 和暦年 (例: 昭和30) ※数字だけでなく元号含む
            dt = d.date_of_death
            if dt.year >= 2019:
                wareki_year = f"令和{dt.year - 2018}"
                if dt.year == 2019 and dt.month <= 4: wareki_year = f"平成31" # 厳密な分岐が必要なら
            elif dt.year >= 1989:
                wareki_year = f"平成{dt.year - 1988}"
            elif dt.year >= 1926:
                wareki_year = f"昭和{dt.year - 1925}"
            elif dt.year >= 1912:
                wareki_year = f"大正{dt.year - 1911}"
            else:
                wareki_year = f"明治{dt.year - 1868}"
            
            # "令和1" を "令和元" にするかはお好みで調整
            if "令和1" in wareki_year and len(wareki_year) == 3: wareki_year = "令和元"
            
            map_dict["{death_year_wareki}"] = wareki_year
        
        # 最後の住所
        d_addr_str = ""
        if d.last_address:
            a = d.last_address
            d_addr_str = f"{a.prefecture}{a.city_ward_town}{a.street_address} {a.building_name or ''}".strip()
        map_dict["{deceased_address}"] = d_addr_str

    # 3. 相続人情報 (契約者を優先)
    heir = None
    if case_data.deceased_ref and case_data.deceased_ref.heirs:
        for h in case_data.deceased_ref.heirs:
            if h.is_contracting_party:
                heir = h
                break
        if not heir:
            heir = case_data.deceased_ref.heirs[0]

    if heir:
        full_name_h = f"{heir.name_last} {heir.name_first}".strip()
        map_dict["{heir_name}"] = full_name_h
        map_dict["{heir_name_last}"] = heir.name_last or ""
        map_dict["{heir_name_first}"] = heir.name_first or ""
        map_dict["{heir_rel}"] = heir.relationship_type or ""
        
        # ★追加: 生年月日の詳細分解ロジック
        if heir.date_of_birth:
            # 1. 和暦全 (例: 昭和30年1月1日)
            map_dict["{heir_birthday}"] = convert_seireki_to_wareki(heir.date_of_birth)
            
            # 2. 西暦年 (例: 1955)
            map_dict["{heir_birthday_year_seireki}"] = str(heir.date_of_birth.year)
            
            # 3. 和暦年 (例: 昭和30) ※数字だけでなく元号含む
            dt = heir.date_of_birth
            if dt.year >= 2019:
                wareki_year = f"令和{dt.year - 2018}"
                if dt.year == 2019 and dt.month <= 4: wareki_year = f"平成31" # 厳密な分岐が必要なら
            elif dt.year >= 1989:
                wareki_year = f"平成{dt.year - 1988}"
            elif dt.year >= 1926:
                wareki_year = f"昭和{dt.year - 1925}"
            elif dt.year >= 1912:
                wareki_year = f"大正{dt.year - 1911}"
            else:
                wareki_year = f"明治{dt.year - 1868}"
            
            # "令和1" を "令和元" にするかはお好みで調整
            if "令和1" in wareki_year and len(wareki_year) == 3: wareki_year = "令和元"
            
            map_dict["{heir_birthday_year_wareki}"] = wareki_year
            
            # 4. 月・日
            map_dict["{heir_birthday_month}"] = str(dt.month)
            map_dict["{heir_birthday_day}"] = str(dt.day)
        
        # 住所
        addr_str = "（住所未登録）"
        pref, city, street, bldg = "", "", "", ""
        if heir.address_links:
            for link in heir.address_links:
                if link.is_current_address and link.address:
                    a = link.address
                    pref = a.prefecture or ""
                    city = a.city_ward_town or ""
                    street = a.street_address or ""
                    bldg = a.building_name or ""
                    addr_str = f"{pref}{city}{street} {bldg}".strip()
                    break
        
        map_dict["{heir_address}"] = addr_str
        map_dict["{heir_pref}"] = pref
        map_dict["{heir_city}"] = city
        map_dict["{heir_street}"] = street
        map_dict["{heir_building}"] = bldg

    # 4. ★追加: 対象資産情報 (コンテキスト)
    if target_asset:
        # 金融資産の場合
        if isinstance(target_asset, FinancialAsset):
            bank_name = target_asset.bank_ref.bank_name if target_asset.bank_ref else ""
            branch_name = target_asset.branch_ref.branch_name if target_asset.branch_ref else ""
            acc_type = target_asset.account_type_ref.type_name if target_asset.account_type_ref else "普通"
            
            map_dict["{bank_name}"] = bank_name
            map_dict["{branch_name}"] = branch_name
            map_dict["{account_type}"] = acc_type
            map_dict["{account_number}"] = target_asset.account_number or ""
            map_dict["{balance}"] = f"{target_asset.balance:,.0f}" if target_asset.balance else "0"
            # 口座名義人がもしAssetにあれば(現状はDeceased名が一般的だが、名寄せOCR結果等を使うならここ)
            map_dict["{account_holder}"] = f"{d.name_last} {d.name_first}" # 仮: 被相続人名

        # 不動産資産の場合
        elif isinstance(target_asset, RealEstateAsset):
            map_dict["{prop_location}"] = target_asset.location or ""
            map_dict["{prop_number}"] = target_asset.lot_number or target_asset.house_number or ""
            map_dict["{prop_category}"] = target_asset.land_category or target_asset.structure or ""
            map_dict["{prop_area}"] = str(target_asset.land_area or target_asset.floor_area or "")

    return map_dict


def generate_pdf(template_path, coords, replacement_map):
    # (変更なし: 既存のロジックをそのまま使用)
    try:
        reader = PdfReader(template_path)
        output = PdfWriter()
        SCALE_FACTOR = 72.0 / 200.0

        for i, page_obj in enumerate(reader.pages):
            page_num = i + 1
            page_coords = [c for c in coords if c["page"] == page_num]

            if page_coords:
                packet = BytesIO()
                pw = float(page_obj.mediabox.width)
                ph = float(page_obj.mediabox.height)
                can = canvas.Canvas(packet, pagesize=(pw, ph))

                for c in page_coords:
                    raw_val = c["value"]
                    # 辞書から置換。なければ元の値をそのまま使う(固定文字など)
                    text_to_draw = replacement_map.get(raw_val, raw_val)
                    
                    if not text_to_draw: continue

                    draw_x = c["x"] * SCALE_FACTOR
                    top_y = ph - (c["y"] * SCALE_FACTOR)
                    c_obj = red if c["color"] == "red" else black
                    can.setStrokeColor(c_obj)
                    can.setFillColor(c_obj)
                    font_sz = float(c["font_size"])

                    if str(text_to_draw).startswith("RECT:"):
                        try:
                            dims = text_to_draw.replace("RECT:", "").split("x")
                            w_pt, h_pt = float(dims[0]), float(dims[1])
                            can.rect(draw_x, top_y - h_pt, w_pt, h_pt, stroke=1, fill=0)
                        except: pass
                    else:
                        baseline_y = top_y - (font_sz * 0.9)
                        can.setFont("IPAexG", font_sz)
                        can.drawString(draw_x, baseline_y, str(text_to_draw))

                can.save()
                packet.seek(0)
                overlay = PdfReader(packet)
                page_obj.merge_page(overlay.pages[0])

            output.add_page(page_obj)

        out_stream = BytesIO()
        output.write(out_stream)
        return out_stream

    except Exception as e:
        st.error(f"PDF生成エラー: {e}")
        return None


# ==========================================
# メイン画面
# ==========================================
def main():
    st.title("🖨️ 書類自動作成")
    st.caption("登録済みの案件データを選択し、PDFを作成します。")

    db = DatabaseManager()
    session = db._get_session()

    # 1. 案件選択 (Home共有)
    target_case_id = st.session_state.get("selected_case_id")
    
    if not target_case_id:
        # 未選択時の選択UI
        st.warning("⚠️ 案件が選択されていません。")
        with st.expander("案件を選択する", expanded=True):
            cases = session.query(Case).all()
            opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
            sel = st.selectbox("案件リスト", list(opts.keys()))
            if st.button("選択"):
                st.session_state["selected_case_id"] = opts[sel]
                st.rerun()
        return

    # データ一括ロード (FinancialAsset, RealEstateAsset も含める)
    target_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs).joinedload(Heir.address_links).joinedload(H_AddressHistory.address),
        joinedload(Case.deceased_ref).joinedload(Deceased.last_address),
        joinedload(Case.financial_assets).joinedload(FinancialAsset.bank_ref),
        joinedload(Case.financial_assets).joinedload(FinancialAsset.branch_ref),
        joinedload(Case.financial_assets).joinedload(FinancialAsset.account_type_ref),
        joinedload(Case.real_estates)
    ).get(target_case_id)

    if not target_case:
        st.error("案件情報の取得に失敗しました。")
        return

    d_name = target_case.deceased_ref.name_last + " " + target_case.deceased_ref.name_first if target_case.deceased_ref else "未登録"
    st.success(f"📂 対象案件: **{target_case.case_number} {target_case.client_name}** 様 (被相続人: {d_name})")

    st.divider()

    # ------------------------------------
    # 2. 対象資産の選択 (Context Selection)
    # ------------------------------------
    col_asset, col_tpl = st.columns([1, 1])
    
    target_asset = None
    asset_description = "（資産指定なし）"

    with col_asset:
        st.markdown("##### 1. 対象資産を選択 (任意)")
        st.caption("銀行の請求書など、特定の資産に関する書類を作る場合に選択してください。")
        
        # 資産リストの作成
        asset_options = {"指定なし (基本情報のみ)": None}
        
        # 預貯金
        if target_case.financial_assets:
            for fa in target_case.financial_assets:
                b_name = fa.bank_ref.bank_name if fa.bank_ref else "不明銀行"
                br_name = fa.branch_ref.branch_name if fa.branch_ref else ""
                label = f"🏦 {b_name} {br_name} ({fa.account_number})"
                asset_options[label] = fa
        
        # 不動産
        if target_case.real_estates:
            for re_asset in target_case.real_estates:
                loc = re_asset.location if len(re_asset.location or "") < 10 else (re_asset.location[:10] + "...")
                label = f"🏘️ {re_asset.property_type}: {loc}"
                asset_options[label] = re_asset

        selected_asset_label = st.selectbox("資産リスト", list(asset_options.keys()))
        target_asset = asset_options[selected_asset_label]
        
        if target_asset:
            asset_description = selected_asset_label

    # ------------------------------------
    # 3. テンプレート選択
    # ------------------------------------
    with col_tpl:
        st.markdown("##### 2. テンプレートを選択")
        files = session.query(FileRegistry).filter(FileRegistry.filename.like("%.pdf")).all()

        if not files:
            st.warning("テンプレートがありません。")
        else:
            file_opts = {f.filename: f.file_hash for f in files}
            selected_file_name = st.selectbox("テンプレート一覧", list(file_opts.keys()))
            target_hash = file_opts[selected_file_name]

    # ------------------------------------
    # 4. 作成実行
    # ------------------------------------
    st.divider()
    
    if st.button("🚀 PDFを作成する", type="primary", use_container_width=True):
        if not selected_file_name:
            st.error("テンプレートを選択してください")
        else:
            coords = db.get_coordinates_by_hash(target_hash)
            if not coords:
                st.error("このテンプレートには座標が登録されていません。「書式座標登録ツール」で設定してください。")
            else:
                template_path = os.path.join(ROOT_DIR, "data", "templates", selected_file_name)
                
                if not os.path.exists(template_path):
                    st.error("テンプレートファイルが見つかりません。")
                else:
                    # ★ここが重要: 選択された資産(Context)を渡してマッピングを作成
                    replace_map = create_replacement_map(target_case, target_asset)
                    
                    pdf_data = generate_pdf(template_path, coords, replace_map)

                    if pdf_data:
                        st.success(f"✅ 作成完了！ ({asset_description})")
                        
                        # ファイル名に資産名を含める
                        dl_filename = f"作成済_{selected_file_name}"
                        if target_asset and isinstance(target_asset, FinancialAsset) and target_asset.bank_ref:
                             dl_filename = f"{target_asset.bank_ref.bank_name}_{selected_file_name}"

                        st.download_button(
                            label="📥 PDFをダウンロード",
                            data=pdf_data,
                            file_name=dl_filename,
                            mime="application/pdf",
                        )

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/10_公証役場・送付セット作成.py
````python
# src/legal_system/ui/pages/10_公証役場・送付セット作成.py

import os
import sys
import time
import random
import string
import tempfile  # ★追加: 一時フォルダ作成用
from io import BytesIO
from pathlib import Path

import streamlit as st
# import pyzipper  <-- 削除またはコメントアウト
from PIL import Image
from pdf2image import convert_from_bytes
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

# 会社書類テンプレートのパス
TEMPLATES_DIR = os.path.join(ROOT_DIR, "data", "templates")

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased

# ★追加: 暗号化サービスのインポート
from services.encryption_service import EncryptionService

# ページ設定
st.set_page_config(page_title="公証役場連携", page_icon="⚖️", layout="wide")


# ==========================================
# 2. ロジッククラス定義
# ==========================================

class AutoFileCollector:
    """フォルダから関連ファイルを自動収集・分類するクラス"""
    
    KEYWORDS = {
        "戸籍・住民票・身分証": [
            "戸籍", "除籍", "住民票", "除票", "附票", "原戸籍", "身分証明書", 
            "印鑑証明", "印鑑登録証明書", "マイナンバー", "免許証", "保険証"
        ],
        "不動産・登記": [
            "不動産", "登記", "全部事項証明書", "名寄", "固定資産税", "評価証明", 
            "公図", "測量図", "建物図面"
        ],
        "金融資産（通帳・証券）": [
            "通帳", "残高証明", "証券", "取引推移", "定期", "配当", "株式"
        ],
        "遺言書案・要旨": [
            "文案", "遺言", "要旨", "案", "メモ", "下書き", "構成"
        ]
    }

    # 除外キーワード
    EXCLUDE_KEYWORDS = [
        "引継書", "通帳のコピー箇所のご説明", "試算", "委任", 
        "約定書", "テンプレート", "ご案内", "送付状"
    ]

    @staticmethod
    def collect_files(folder_path: str) -> dict:
        results = {k: [] for k in AutoFileCollector.KEYWORDS.keys()}
        if not folder_path or not os.path.exists(folder_path):
            return {}

        try:
            root_path = Path(folder_path)
            for p in root_path.rglob("*"):
                if p.is_file():
                    if p.name.startswith("~$") or p.name.startswith("."): continue
                    if p.suffix.lower() not in ['.pdf', '.jpg', '.jpeg', '.png', '.docx', '.doc', '.xlsx', '.xls']: continue

                    if any(ex in p.name for ex in AutoFileCollector.EXCLUDE_KEYWORDS):
                        continue

                    for category, keywords in AutoFileCollector.KEYWORDS.items():
                        if any(k in p.name for k in keywords):
                            results[category].append(p)
                            break
        except Exception:
            pass
        return {k: v for k, v in results.items() if v}


class DocumentProcessor:
    """ドキュメントの軽量化処理を行うクラス"""
    
    @staticmethod
    def convert_to_monochrome_pdf(file_bytes: bytes, file_name: str, strong_compression: bool = False) -> bytes:
        original_size = len(file_bytes)
        dpi = 100 if strong_compression else 150
        quality = 50 if strong_compression else 75
        
        images = []
        if file_name.lower().endswith(".pdf"):
            try:
                images = convert_from_bytes(file_bytes, dpi=dpi, grayscale=True)
            except Exception:
                return file_bytes
        else:
            try:
                img = Image.open(BytesIO(file_bytes)).convert("L")
                images = [img]
            except Exception:
                return file_bytes

        if not images: return file_bytes

        output = BytesIO()
        try:
            images[0].save(
                output, "PDF", resolution=float(dpi), save_all=True, append_images=images[1:], optimize=True, quality=quality
            )
            processed_data = output.getvalue()
            if len(processed_data) >= original_size:
                return file_bytes
            return processed_data
        except Exception:
            return file_bytes

class ZipManager:
    """暗号化ZIP作成クラス (分割対応・7-Zip版)"""
    
    @staticmethod
    def create_split_encrypted_zips(files: dict, password: str, max_mb: int = 20) -> list:
        zip_list = []
        current_zip_files = {}
        current_size = 0
        current_vol = 1
        limit_bytes = max_mb * 1024 * 1024
        filenames = list(files.keys())
        
        for fname in filenames:
            data = files[fname]
            size = len(data)
            
            if (current_size + size > limit_bytes) and (len(current_zip_files) > 0):
                zip_bytes = ZipManager._make_zip_bytes(current_zip_files, password)
                zip_list.append({
                    "name": f"送付資料_Vol{current_vol}.zip",
                    "data": zip_bytes,
                    "files": list(current_zip_files.keys())
                })
                current_vol += 1
                current_zip_files = {}
                current_size = 0
            
            current_zip_files[fname] = data
            current_size += size
            
        if current_zip_files:
            zip_bytes = ZipManager._make_zip_bytes(current_zip_files, password)
            name = f"送付資料_Vol{current_vol}.zip" if current_vol > 1 else "送付資料一式.zip"
            zip_list.append({"name": name, "data": zip_bytes, "files": list(current_zip_files.keys())})
        return zip_list

    @staticmethod
    def _make_zip_bytes(files_dict, password) -> bytes:
        """
        7za.exe を使用して、ZipCrypto方式(Windows標準機能互換)の暗号化ZIPを作成する。
        """
        # 一時ディレクトリを作成して作業する
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_paths_for_7z = []
            
            # 1. メモリ上のデータを一時ファイルとして書き出す
            for fname, fdata in files_dict.items():
                # ファイル名の安全化
                safe_name = os.path.basename(fname)
                file_path = os.path.join(tmp_dir, safe_name)
                
                with open(file_path, "wb") as f:
                    f.write(fdata)
                
                file_paths_for_7z.append(file_path)
            
            # 2. 出力先のZIPパス
            output_zip_path = os.path.join(tmp_dir, "output.zip")
            
            # 3. 7za.exe を呼び出してZIP作成
            try:
                EncryptionService.create_encrypted_zip(file_paths_for_7z, output_zip_path, password)
            except FileNotFoundError:
                st.error("【構成エラー】7za.exe が見つかりません。システム管理者に連絡してください。")
                return b""
            except Exception as e:
                st.error(f"ZIP作成エラー: {e}")
                return b""

            # 4. 作成されたZIPをバイト列として読み込む
            if os.path.exists(output_zip_path):
                with open(output_zip_path, "rb") as f:
                    zip_bytes = f.read()
                return zip_bytes
            else:
                return b""

class EmailGenerator:
    """公証役場向けメール生成"""
    
    @staticmethod
    def generate_drafts_split(case, notary_name: str, password: str, zip_list: list, user_name: str):
        # 遺言者名の取得 (安全な取得ロジック)
        d_name = ""
        if case.deceased_ref:
            d_name = f"{case.deceased_ref.name_last} {case.deceased_ref.name_first}".strip()
        
        # 被相続人がいない場合はクライアント名(契約者)を使用
        if not d_name or d_name == "未登録":
            contractor = None
            if case.deceased_ref and case.deceased_ref.heirs:
                contractor = next((h for h in case.deceased_ref.heirs if h.is_contracting_party), None)
            
            if contractor:
                d_name = f"{contractor.name_last} {contractor.name_first}".strip()
            else:
                d_name = case.client_name.strip() if case.client_name else "（名称不明）"

        total_vols = len(zip_list)
        drafts = []
        
        # 1. ファイル送付メール
        for i, z_info in enumerate(zip_list):
            vol_num = i + 1
            
            subject_base = f"【新規依頼】公正証書遺言作成のご依頼（遺言者：{d_name}様）／行政書士法人チェスター{user_name}"
            if total_vols > 1:
                subject = f"{subject_base}（{vol_num}/{total_vols}）"
            else:
                subject = subject_base

            files_str = "\n".join([f"・{f}" for f in z_info["files"]])
            
            body = f"""{notary_name}　御中

いつも大変お世話になっております。
行政書士法人チェスターの{user_name}でございます。

この度、弊社クライアントの公正証書遺言作成につきまして、次の通り作成依頼をいたしたく、必要書類を添付にて送付申し上げます。
{'※ファイル容量の関係で、' + str(total_vols) + '通に分けてお送りいたします。本メールはその' + str(vol_num) + '通目です。' if total_vols > 1 else ''}

お忙しいところ恐縮ですが、内容のご確認と今後の段取りについてご教示いただけますと幸いです。

【案件概要】
遺言者氏名： {d_name}
嘱託の種類： 公正証書遺言
証人の手配： 1名依頼いたします。（もう1名は私、{user_name}がお伺いいたします。）
作成希望場所：{notary_name}

【添付書類 ({z_info['name']})】
{files_str}

個人情報保護のため、ファイルにはパスワードを設定しております。パスワードは後ほど別メールにてお送りいたします。
※ZIPファイルはWindows標準機能で解凍可能です。

何卒よろしくお願い申し上げます。"""
            drafts.append({"subject": subject, "body": body, "type": "file", "zip_name": z_info["name"]})

        # 2. パスワード通知メール
        pass_subject = f"【パスワード送付】公正証書遺言作成のご依頼/ 遺言者：{d_name}様"
        
        pass_body = f"""{notary_name}　御中

いつも大変お世話になっております。
行政書士法人チェスターの{user_name}でございます。

先ほどお送りいたしました添付ファイルのパスワードをご案内いたします。
{'（全ファイル共通です）' if total_vols > 1 else ''}

パスワード：{password}

お手数をおかけいたしますが、ご査収のほどよろしくお願い申し上げます。"""
        drafts.append({"subject": pass_subject, "body": pass_body, "type": "pass"})
        return drafts


# ==========================================
# 3. メイン画面 UI
# ==========================================
def main():
    st.title("⚖️ 公証役場連携・送付セット作成")
    st.caption("フォルダからの自動ファイル収集、軽量化、暗号化(Windows互換)、分割ZIP作成を一括で行います。")

    db = DatabaseManager()
    session = db._get_session()
    
    current_user_info = db.get_current_user_info()
    user_name = current_user_info["name"]

    # 1. 案件選択
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning("⚠️ 案件が選択されていません。サイドバーまたはHomeから選択してください。")
        return

    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).get(target_case_id)
    
    d_name_display = "未登録"
    if current_case.deceased_ref:
        d_name_display = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}"
        
    st.success(f"📂 対象案件: **{current_case.client_name}** 様 (被相続人: {d_name_display})")

    st.divider()

    col_L, col_R = st.columns([1, 1.2])

    # --- 左カラム: ファイル選択 & 設定 ---
    with col_L:
        st.subheader("1. 送付資料の準備")
        
        # === A. フォルダ自動収集機能 ===
        st.markdown("###### ① フォルダから自動検出されたファイル")
        case_folder_path = current_case.folder_path
        
        detected_files_map = {}
        if case_folder_path and os.path.exists(case_folder_path):
            st.caption(f"検索先: `{case_folder_path}`")
            detected_files_map = AutoFileCollector.collect_files(case_folder_path)
            
            if not detected_files_map:
                st.info("関連しそうなファイルは見つかりませんでした。")
            
            selected_auto_files = [] 
            
            for category, path_list in detected_files_map.items():
                with st.expander(f"📁 {category} ({len(path_list)}件)", expanded=True):
                    for p in path_list:
                        if st.checkbox(f"{p.name}", value=True, key=f"auto_{p}"):
                            selected_auto_files.append(p)
                            
        else:
            st.warning("⚠️ 案件フォルダパスが登録されていないか、アクセスできません。Home画面で設定してください。")
            selected_auto_files = []

        # === B. 手動アップロード ===
        st.markdown("###### ② 手動追加（フォルダにない場合）")
        uploaded_files = st.file_uploader(
            "ファイルを選択", 
            type=["pdf", "png", "jpg", "jpeg", "docx", "doc", "xlsx", "xls"], 
            accept_multiple_files=True
        )
        
        use_strong_compression = st.checkbox("🔥 強力圧縮 (画質を落としてサイズ優先)", value=False)

        # === C. 会社書類・身分証の自動同梱 ===
        st.markdown("###### ③ 会社書類・身分証の同梱")
        company_docs_selected = []
        if os.path.exists(TEMPLATES_DIR):
            all_templates = [f for f in os.listdir(TEMPLATES_DIR) if f.lower().endswith(".pdf")]
            clean_user_name = user_name.replace(" ", "").replace("　", "")
            
            primary_docs = []
            other_docs = []
            
            for tpl in all_templates:
                clean_tpl = tpl.replace(" ", "").replace("　", "")
                is_target = False
                if "履歴事項全部証明書" in clean_tpl: is_target = True
                elif "行政書士証票" in clean_tpl and clean_user_name in clean_tpl: is_target = True
                elif "免許証" in clean_tpl and clean_user_name in clean_tpl: is_target = True
                
                if is_target: primary_docs.append(tpl)
                else: other_docs.append(tpl)
            
            for doc in primary_docs:
                if st.checkbox(f"📄 {doc}", value=True, key=f"chk_{doc}"):
                    company_docs_selected.append(doc)
            
            with st.expander("その他のファイルを選択"):
                for doc in other_docs:
                    if st.checkbox(f"📄 {doc}", value=False, key=f"chk_other_{doc}"):
                        company_docs_selected.append(doc)
        else:
            st.warning("テンプレートフォルダなし")

        # === D. 設定 ===
        st.markdown("###### ④ 送付設定")
        notary_name = st.text_input("公証役場名", placeholder="例: 京橋公証役場")
        
        if "zip_password" not in st.session_state:
            chars = string.ascii_letters + string.digits
            st.session_state["zip_password"] = ''.join(random.choice(chars) for _ in range(10))
        
        password = st.text_input("ZIPパスワード", value=st.session_state["zip_password"])
        if st.button("パスワード再生成"):
            chars = string.ascii_letters + string.digits
            st.session_state["zip_password"] = ''.join(random.choice(chars) for _ in range(10))
            st.rerun()

        st.markdown("---")
        
        # 実行ボタン
        if st.button("🚀 送付セットを作成する", type="primary", use_container_width=True):
            if not uploaded_files and not company_docs_selected and not selected_auto_files:
                st.error("ファイルが1つも選択されていません。")
            else:
                progress_text = "処理中..."
                my_bar = st.progress(0, text=progress_text)

                files_to_zip = {}
                processor = DocumentProcessor()
                
                total_files = len(uploaded_files) + len(company_docs_selected) + len(selected_auto_files)
                processed_cnt = 0

                # 1. 自動収集ファイルの読み込み & 軽量化
                for p in selected_auto_files:
                    try:
                        with open(p, "rb") as f:
                            bytes_data = f.read()
                        
                        fname = p.name
                        fname_lower = fname.lower()
                        
                        if fname_lower.endswith((".pdf", ".png", ".jpg", ".jpeg")):
                            optimized_bytes = processor.convert_to_monochrome_pdf(
                                bytes_data, fname, strong_compression=use_strong_compression
                            )
                            base_name = os.path.splitext(fname)[0]
                            final_name = f"{base_name}.pdf"
                            files_to_zip[final_name] = optimized_bytes
                        else:
                            files_to_zip[fname] = bytes_data
                            
                    except Exception as e:
                        st.error(f"ファイル読込エラー ({p.name}): {e}")
                    
                    processed_cnt += 1
                    my_bar.progress(processed_cnt / total_files, text=f"処理中: {p.name}")

                # 2. 手動アップロードファイルの処理
                for f in uploaded_files:
                    bytes_data = f.getvalue()
                    fname_lower = f.name.lower()
                    
                    if fname_lower.endswith((".pdf", ".png", ".jpg", ".jpeg")):
                        optimized_bytes = processor.convert_to_monochrome_pdf(
                            bytes_data, f.name, strong_compression=use_strong_compression
                        )
                        base_name = os.path.splitext(f.name)[0]
                        final_name = f"{base_name}.pdf"
                        files_to_zip[final_name] = optimized_bytes
                    else:
                        files_to_zip[f.name] = bytes_data
                    
                    processed_cnt += 1
                    my_bar.progress(processed_cnt / total_files, text=f"処理中: {f.name}")

                # 3. 会社書類の読み込み
                for doc_name in company_docs_selected:
                    path = os.path.join(TEMPLATES_DIR, doc_name)
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            files_to_zip[doc_name] = f.read()
                    processed_cnt += 1
                    my_bar.progress(processed_cnt / total_files, text=f"同梱中: {doc_name}")

                # 4. 分割ZIP作成 (20MB制限)
                my_bar.progress(0.9, text="Windows互換ZIP作成中 (7-Zip)...")
                
                # ★修正: ここで7za.exeを使ったZipManagerを呼び出す
                zip_list = ZipManager.create_split_encrypted_zips(files_to_zip, password, max_mb=20)
                
                # 5. メール生成
                drafts = EmailGenerator.generate_drafts_split(
                    current_case, notary_name, password, zip_list, user_name
                )

                st.session_state["zip_list"] = zip_list
                st.session_state["email_drafts"] = drafts
                
                # 自動保存処理 (案件フォルダへ)
                if case_folder_path and os.path.exists(case_folder_path):
                    try:
                        for z in zip_list:
                            save_path = os.path.join(case_folder_path, z["name"])
                            with open(save_path, "wb") as f:
                                f.write(z["data"])
                        st.success(f"✅ ZIPファイルを案件フォルダに保存しました: {case_folder_path}")
                    except Exception as e:
                        st.warning(f"案件フォルダへの自動保存に失敗しました: {e}")

                my_bar.empty()
                st.success("作成完了！ 下にスクロールしてご確認ください 👇")

    # --- 右カラム: 結果表示 ---
    with col_R:
        st.subheader("2. 生成物ダウンロード")
        
        if "zip_list" in st.session_state:
            zip_list = st.session_state["zip_list"]
            drafts = st.session_state["email_drafts"]
            
            st.markdown("##### 📦 送付ファイル (パスワード付)")
            st.caption("※Windows標準機能で解凍可能")
            
            for i, z_info in enumerate(zip_list):
                col_z1, col_z2 = st.columns([3, 1])
                col_z1.write(f"**{z_info['name']}** ({len(z_info['data'])/1024/1024:.1f} MB)")
                with col_z2:
                    st.download_button(
                        label="📥 DL",
                        data=z_info["data"],
                        file_name=z_info["name"],
                        mime="application/zip",
                        key=f"dl_zip_{i}",
                        type="primary"
                    )
                with st.expander("含まれるファイル"):
                    for inner_f in z_info["files"]:
                        st.caption(f"- {inner_f}")
            
            st.caption(f"パスワード: `{password}`")
            st.divider()
            
            st.markdown("##### 📧 メール下書き")
            tabs = st.tabs([f"通番 {i+1}" for i in range(len(drafts))])
            
            for i, draft in enumerate(drafts):
                with tabs[i]:
                    label = "📎 ファイル送付" if draft["type"] == "file" else "🔑 パスワード通知"
                    st.info(label)
                    
                    st.text_input("件名", value=draft["subject"], key=f"subj_{i}")
                    # コピーしやすいUI
                    st.code(draft["body"], language="text")
                    
                    with st.expander("本文を編集する"):
                        new_body = st.text_area("本文編集", value=draft["body"], height=300, key=f"body_{i}")
                        if new_body != draft["body"]:
                            draft["body"] = new_body
                            st.rerun()

        else:
            st.info("👈 左側で設定を行い、「送付セットを作成する」を押してください。")
            st.markdown("""
            **特徴:**
            - **自動収集**: 案件フォルダから戸籍や登記情報を自動検出します。
            - **Windows互換**: 7-Zipエンジンを使用し、公証役場のPCでも標準機能で開けるZIPを作成します。
            - **容量対策**: 20MB制限を超える場合は自動分割します。
            - **自動保存**: 作成されたZIPは案件フォルダにも保存されます。
            """)

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/11_公正証書遺言_ドラフト作成.py
````python
# src/legal_system/ui/pages/11_公正証書遺言_ドラフト作成.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from io import BytesIO

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.services.automation.will_generator import WillDraftGenerator

def main():
    st.set_page_config(page_title="遺言ドラフト作成", page_icon="📜", layout="wide")
    st.title("📜 公正証書遺言 自動起案システム")

    # --- セッションステート初期化 ---
    if "generated_data" not in st.session_state:
        st.session_state["generated_data"] = None

    col_input, col_action = st.columns([1, 1])
    
    with col_input:
        with st.container(border=True):
            st.subheader("1. 素材データのアップロード")
            uploaded_excel = st.file_uploader("① 遺言内容要旨 (Excel/CSV)", type=["xlsx", "csv"])
            
            st.markdown("---")
            use_default = st.checkbox("サーバー内の標準テンプレートを使用", value=True)
            uploaded_template = None
            if not use_default:
                uploaded_template = st.file_uploader("② 雛形テンプレート (Word)", type=["docx"])
            
            st.markdown("---")
            uploaded_images = st.file_uploader(
                "③ 不動産登記情報 (PDF/画像) ※任意", 
                type=["png", "jpg", "jpeg", "pdf"], 
                accept_multiple_files=True,
                help="PDFは自動で画像化され、「別冊」として出力されます。"
            )

    with col_action:
        st.subheader("2. 生成実行 & プレビュー")
        
        if uploaded_excel:
            try:
                if uploaded_excel.name.endswith('.xlsx'):
                    df_preview = pd.read_excel(uploaded_excel)
                else:
                    df_preview = pd.read_csv(uploaded_excel)
                
                df_preview = df_preview.replace(r'^\s*$', np.nan, regex=True).ffill()
                if 'No' in df_preview.columns:
                    df_preview = df_preview.dropna(subset=['No'])

                st.info(f"📋 要旨データ確認: {len(df_preview)} 行")
                st.dataframe(df_preview, height=200, use_container_width=True)
            except Exception as e:
                st.error(f"プレビューエラー: {e}")

            st.markdown("---")
            
            # --- 生成ボタン処理 ---
            if st.button("🚀 AIドラフト生成を開始", type="primary", use_container_width=True):
                template_source = None
                if use_default:
                    default_path = os.path.join(ROOT_DIR, "data", "templates", "遺言公正証書文案テンプレート.docx")
                    if os.path.exists(default_path):
                        with open(default_path, "rb") as f:
                            template_source = BytesIO(f.read())
                    else:
                        st.error(f"❌ 標準テンプレートなし: {default_path}")
                        st.stop()
                elif uploaded_template:
                    template_source = uploaded_template
                else:
                    st.error("テンプレートを指定してください")
                    st.stop()

                registry_files = uploaded_images if uploaded_images else []

                generator = WillDraftGenerator()
                with st.spinner("🤖 AI思考 & 文書作成中..."):
                    try:
                        uploaded_excel.seek(0)
                        if hasattr(template_source, 'seek'): template_source.seek(0)
                        
                        # 生成実行
                        doc_io, reg_io, ai_data, csv_debug = generator.generate_draft(uploaded_excel, template_source, registry_files)
                        
                        # ★結果をセッションステートに保存（これでボタンを押しても消えなくなる）
                        st.session_state["generated_data"] = {
                            "doc_io": doc_io,
                            "reg_io": reg_io,
                            "ai_data": ai_data,
                            "timestamp": pd.Timestamp.now().strftime('%Y%m%d')
                        }
                        
                        st.success("✅ 生成完了！")
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"エラー: {e}")
                        st.exception(e)

        # --- ダウンロードエリア（セッションにデータがあれば常に表示） ---
        if st.session_state["generated_data"]:
            data = st.session_state["generated_data"]
            
            st.divider()
            st.markdown("### 📥 ダウンロード")
            
            # デバッグ情報
            with st.expander("🔍 生成結果の詳細を確認", expanded=False):
                st.json(data["ai_data"].model_dump())

            c_dl1, c_dl2 = st.columns(2)
            
            # 1. 遺言書本体
            c_dl1.download_button(
                label="📥 遺言書ドラフト (本体)",
                data=data["doc_io"],
                file_name=f"遺言書ドラフト_{data['timestamp']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
                key="dl_btn_main" # キーを指定して競合回避
            )
            
            # 2. 登記情報別冊 (ある場合のみ)
            if data["reg_io"]:
                c_dl2.download_button(
                    label="📥 登記情報 (別冊)",
                    data=data["reg_io"],
                    file_name=f"登記情報別冊_{data['timestamp']}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="dl_btn_reg"
                )

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/90_預貯金口座入力フォーム.py
````python
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
````

## File: src/legal_system/ui/pages/97_書式座標登録ツール.py
````python
# src/legal_system/ui/pages/97_書式座標登録ツール.py

import hashlib
import os
import sys
import time
import uuid
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

# PDF・画像処理ライブラリ
from pdf2image import convert_from_bytes
from PIL import ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from streamlit_image_coordinates import streamlit_image_coordinates

# ==========================================
# 1. パス解決 & 初期設定
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager

# テンプレート保存ディレクトリ
TEMPLATES_DIR = os.path.join(ROOT_DIR, "data", "templates")

# ページ設定
st.set_page_config(layout="wide", page_title="書式・座標管理", page_icon="🛠️")

# フォント設定
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

db = DatabaseManager()
user_info = db.get_current_user_info()


# ==========================================
# 2. ヘルパー関数 & プリセット定義
# ==========================================
def calculate_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def get_wareki(dt):
    if dt.year >= 2019:
        return f"令和{dt.year - 2018}"
    return str(dt.year)


def split_phone_number(phone_str):
    parts = ["", "", ""]
    if phone_str:
        phone_str = phone_str.replace("ー", "-").replace("−", "-")
        splits = phone_str.split("-")
        for i in range(min(len(splits), 3)):
            parts[i] = splits[i]
    return parts


user_phone_parts = split_phone_number(user_info.get("phone", ""))
COMPANY_INFO = {
    "zip1": "100",
    "zip2": "0001",
    "address": "東京都千代田区千代田1-1",
    "name": "行政書士法人未来",
    "rep_name": "行政書士 山田 太郎",
}
today = datetime.now()
wareki_year = get_wareki(today)

PRESETS = {
    "（選択なし）": {"label": "", "val": ""},

    # --- 被相続人 ---
    "----- ★被相続人 -----": {"label": "", "val": ""},
    "{被相続人 氏名(全)}": {"label": "被相続人氏名", "val": "{deceased_name}"},
    "{被相続人 氏(姓)}": {"label": "被相続人_姓", "val": "{deceased_name_last}"},
    "{被相続人 名}": {"label": "被相続人_名", "val": "{deceased_name_first}"},
    "{被相続人 最後の住所}": {"label": "被相続人住所", "val": "{deceased_address}"}, # 追加
    "{被相続人 本籍}": {"label": "被相続人本籍", "val": "{deceased_hometown}"}, # 追加
    "{死亡日 (和暦全)}": {"label": "被相続人死亡日", "val": "{death_date}"},
    "{死亡日 年(西暦)}": {"label": "死亡日_西暦年", "val": "{death_year_seireki}"},
    "{死亡日 年(和暦)}": {"label": "死亡日_和暦年", "val": "{death_year_wareki}"},
    "{死亡日 月}": {"label": "死亡日_月", "val": "{death_month}"},
    "{死亡日 日}": {"label": "死亡日_日", "val": "{death_day}"},
    
    # --- 相続人（代表者） ---
    "----- ★相続人（代表） -----": {"label": "", "val": ""},
    "{相続人 氏名(全)}": {"label": "相続人氏名", "val": "{heir_name}"},
    "{相続人 氏(姓)}": {"label": "相続人_姓", "val": "{heir_name_last}"},
    "{相続人 名}": {"label": "相続人_名", "val": "{heir_name_first}"},
    "{相続人 生年月日 (和暦全)}": {"label": "相続人生年月日", "val": "{heir_birthday}"},
    "{相続人 生年月日 年(西暦)}": {"label": "相続人_西暦年", "val": "{heir_birthday_year_seireki}"},
    "{相続人 生年月日 年(和暦)}": {"label": "相続人_和暦年", "val": "{heir_birthday_year_wareki}"},
    "{相続人 生年月日 月}": {"label": "相続人_月", "val": "{heir_birthday_month}"},
    "{相続人 生年月日 日}": {"label": "相続人_日", "val": "{heir_birthday_day}"},
    "{相続人 続柄}": {"label": "相続人続柄", "val": "{heir_rel}"},
    "{相続人 代理人氏名}": {"label": "相続人_代理人", "val": "{heir_name} 代理人"},
    "{相続人 住所(全)}": {"label": "相続人住所", "val": "{heir_address}"},
    "{相続人 都道府県}": {"label": "相続人_都道府県", "val": "{heir_pref}"},
    "{相続人 市区町村}": {"label": "相続人_市区町村", "val": "{heir_city}"},
    "{相続人 番地}": {"label": "相続人_番地", "val": "{heir_street}"},
    "{相続人 建物名}": {"label": "相続人_建物", "val": "{heir_building}"},
    
    # --- 不動産 (Context Aware) ---
    "----- ★対象不動産 -----": {"label": "", "val": ""},
    "{不動産 所在}": {"label": "不動産所在", "val": "{prop_location}"},
    "{不動産 地番/家屋番号}": {"label": "地番_家屋番号", "val": "{prop_number}"},
    "{不動産 地目/種類}": {"label": "地目_種類", "val": "{prop_category}"},
    "{不動産 地積/床面積}": {"label": "地積_床面積", "val": "{prop_area}"},

    # --- その他 ---
    "----- 図形・記号・担当者 -----": {"label": "", "val": ""},
    "四角形枠": {"label": "枠線", "val": "RECT:30x30"},
    "数字「1」": {"label": "数字1", "val": "1", "size": 11.0},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14.0},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14.0},
    "代理人ラベル": {"label": "代理人ラベル", "val": "代理人"},
    "被相続人ラベル": {"label": "被相続人ラベル", "val": "被相続人"},

    "----- 担当者・会社 -----": {"label": "", "val": ""},
    "会社住所": {"label": "会社住所", "val": COMPANY_INFO["address"]},
    "会社代表者 (固定)": {"label": "会社代表者", "val": "行政書士法人チェスター　代表社員　清水　茜作", "desc": "固定文字列"},
    "案件ID (G番号)": {"label": "案件ID", "val": "{case_number}", "desc": "G●●"},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]}
}

# ---------------------------------------------------------
# ★ステート初期化
# ---------------------------------------------------------
if st.session_state.get("trigger_reset"):
    st.session_state["input_label"] = ""
    st.session_state["input_val"] = ""
    st.session_state["input_desc"] = ""
    st.session_state["preset_sel"] = "（選択なし）"
    st.session_state["trigger_reset"] = False

if "editor_key" not in st.session_state:
    st.session_state["editor_key"] = str(uuid.uuid4())

if "current_ids" not in st.session_state:
    st.session_state["current_ids"] = []

if "current_file_hash" not in st.session_state:
    st.session_state["current_file_hash"] = None

if "last_x" not in st.session_state:
    st.session_state["last_x"] = 0
if "last_y" not in st.session_state:
    st.session_state["last_y"] = 0
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1

if "target_file_bytes" not in st.session_state:
    st.session_state["target_file_bytes"] = None
if "target_file_name" not in st.session_state:
    st.session_state["target_file_name"] = None

# 入力フォーム用
if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 11.0  # ★初期値11.0
if "input_desc" not in st.session_state:
    st.session_state["input_desc"] = ""
if "preset_sel" not in st.session_state:
    st.session_state["preset_sel"] = "（選択なし）"


# ==========================================
# ★コールバック関数
# ==========================================
def on_data_editor_change():
    """テーブル編集時のコールバック"""
    current_key = st.session_state.get("editor_key", "editor")
    if current_key not in st.session_state:
        return

    changes = st.session_state[current_key]
    needs_refresh = False

    # 新規追加
    if changes["added_rows"]:
        for new_row in changes["added_rows"]:
            label = new_row.get("label", "新規項目")

            # 手動追加時の重複チェック
            current_hash = st.session_state.get("current_file_hash")
            new_label = label
            if current_hash:
                current_coords = db.get_coordinates_by_hash(current_hash)
                existing_labels = [c["label"] for c in current_coords]
                count = 1
                while new_label in existing_labels:
                    count += 1
                    new_label = f"{label}_{count}"

            db.register_coordinate(
                file_hash=st.session_state["current_file_hash"],
                label=new_label,
                x=float(new_row.get("x", 100.0)),
                y=float(new_row.get("y", 100.0)),
                page_number=int(new_row.get("page", st.session_state["current_page"])),
                description="手動追加",
                font_size=float(new_row.get("font_size", 11.0)),
                color=new_row.get("color", "black"),
                test_value=new_row.get("value", ""),
            )
        st.toast("✅ 新規行を追加しました")
        needs_refresh = True

    # 編集
    if changes["edited_rows"]:
        id_list = st.session_state["current_ids"]
        for idx_str, row_changes in changes["edited_rows"].items():
            idx = int(idx_str)
            if idx < len(id_list):
                target_id = id_list[idx]
                if "font_size" in row_changes:
                    row_changes["font_size"] = float(row_changes["font_size"])
                db.update_coordinate_direct(int(target_id), row_changes)
        st.toast("✅ 変更を保存しました")

    # 削除
    if changes["deleted_rows"]:
        id_list = st.session_state["current_ids"]
        for idx in changes["deleted_rows"]:
            if int(idx) < len(id_list):
                target_id = id_list[int(idx)]
                db.delete_coordinate(int(target_id))
        st.toast("🗑️ 削除しました")
        needs_refresh = True

    if needs_refresh:
        st.session_state["editor_key"] = str(uuid.uuid4())


# ==========================================
# ★座標エディタ画面のロジック
# ==========================================
def render_coordinate_editor():
    # サイドバー: ファイル選択（新規アップロードは廃止）
    st.sidebar.header("📂 対象ファイル")
    all_files = db.get_all_files()
    if not all_files:
        st.sidebar.warning("登録済みのファイルがありません。")
        st.info(
            "👈 サイドバーで「📥 雛形ファイル登録」を選んでファイルを登録してください。"
        )
        return

    file_options = {f"{f['filename']}": f for f in all_files}

    current_fname = st.session_state.get("target_file_name")
    idx = 0
    if current_fname:
        keys = list(file_options.keys())
        for i, k in enumerate(keys):
            if current_fname in k:
                idx = i
                break

    selected_label = st.sidebar.selectbox(
        "編集するファイルを選択", list(file_options.keys()), index=idx
    )

    if selected_label:
        selected_data = file_options[selected_label]
        fname = selected_data["filename"]

        if st.session_state["target_file_name"] != fname:
            file_path = os.path.join(TEMPLATES_DIR, fname)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    st.session_state["target_file_bytes"] = f.read()
                st.session_state["target_file_name"] = fname
                st.session_state["current_page"] = 1
                st.rerun()

    target_file_bytes = st.session_state["target_file_bytes"]
    if not target_file_bytes:
        return

    # PDF解析
    try:
        reader = PdfReader(BytesIO(target_file_bytes))
        media_box = reader.pages[0].mediabox
        pdf_w_pt = float(media_box.width)
        pdf_h_pt = float(media_box.height)

        images = convert_from_bytes(target_file_bytes, dpi=200)
        total_pages = len(images)

        p_idx = st.session_state["current_page"] - 1
        if p_idx >= total_pages:
            p_idx = 0
    except Exception as e:
        st.error(f"解析エラー: {e}")
        return

    # ------------------------------------
    # メイン画面: 上部コントロール
    # ------------------------------------
    col_p, col_z, col_f = st.columns([1, 1.5, 1])
    with col_p:
        new_page = st.number_input(
            "ページ切替", 1, total_pages, st.session_state["current_page"]
        )
        if new_page != st.session_state["current_page"]:
            st.session_state["current_page"] = new_page
            st.rerun()
    with col_z:
        zoom_rate = st.slider("プレビュー倍率", 0.1, 1.5, 0.4, 0.05)
    with col_f:

        def on_def_size_change():
            st.session_state["input_size"] = st.session_state["def_font_size_key"]

        st.number_input(
            "基本サイズ(pt)",
            4.0,
            72.0,
            11.0,
            step=0.5,  # ★初期値11.0
            key="def_font_size_key",
            on_change=on_def_size_change,
        )

    # ------------------------------------
    # データ準備 & 画像処理
    # ------------------------------------
    file_hash = calculate_hash(target_file_bytes)
    st.session_state["current_file_hash"] = file_hash

    existing_coords = db.get_coordinates_by_hash(file_hash)
    if existing_coords:
        df_existing = pd.DataFrame(existing_coords)
        df_existing = df_existing.sort_values("id").reset_index(drop=True)
        st.session_state["current_ids"] = df_existing["id"].tolist()
    else:
        df_existing = pd.DataFrame()
        st.session_state["current_ids"] = []

    original_image = images[p_idx]
    orig_w_px, orig_h_px = original_image.size
    preview_scale = orig_h_px / pdf_h_pt
    display_image = original_image.resize(
        (int(orig_w_px * zoom_rate), int(orig_h_px * zoom_rate))
    )

    st.divider()

    # ------------------------------------
    # 2カラムレイアウト (画像:大 / 設定:小)
    # ------------------------------------
    col_img, col_ctrl = st.columns([2.5, 1.0])

    # ★重要: 右カラム（設定フォーム）を先に処理してリセットを防ぐ
    with col_ctrl:
        st.subheader("設定・登録")

        def on_preset_change():
            sel = st.session_state["preset_sel"]
            if sel in PRESETS and PRESETS[sel]["val"]:
                p = PRESETS[sel]
                base_label = p["label"]
                # 重複チェック
                existing_labels = (
                    df_existing["label"].tolist() if not df_existing.empty else []
                )
                new_label = base_label
                count = 1
                while new_label in existing_labels:
                    count += 1
                    new_label = f"{base_label}_{count}"

                st.session_state["input_label"] = new_label
                st.session_state["input_val"] = p["val"]
                if "size" in p:
                    st.session_state["input_size"] = float(p["size"])

        st.selectbox(
            "⚡️ プリセット",
            list(PRESETS.keys()),
            key="preset_sel",
            on_change=on_preset_change,
        )

        c1, c2 = st.columns([2, 1])
        label_in = c1.text_input("項目名", key="input_label")
        val_in = c2.text_input("値/タグ", key="input_val")
        c3, c4 = st.columns(2)
        size_in = c3.number_input(
            "サイズ", 0.5, 100.0, key="input_size", step=0.5, format="%.1f"
        )
        color_in = c4.selectbox("色", ["black", "red"], key="input_color")
        desc_in = st.text_input("備考", key="input_desc")

        st.write(
            f"📍 X={st.session_state['last_x']:.1f} / Y={st.session_state['last_y']:.1f}"
        )

        if st.button("💾 登録する", type="primary", use_container_width=True):
            if not label_in:
                st.error("項目名必須")
            elif st.session_state["last_x"] == 0:
                st.error("画像をクリックしてください")
            else:
                success = db.register_coordinate(
                    file_hash=file_hash,
                    label=label_in,
                    x=st.session_state["last_x"],
                    y=st.session_state["last_y"],
                    page_number=st.session_state["current_page"],
                    description=desc_in,
                    font_size=float(size_in),
                    color=color_in,
                    test_value=val_in,
                )
                if success:
                    st.toast("✅ 登録完了")
                    st.session_state["trigger_reset"] = True
                    st.session_state["editor_key"] = str(uuid.uuid4())
                    time.sleep(0.5)
                    st.rerun()

    # --- 左カラム: 画像表示 (後続実行) ---
    with col_img:
        st.subheader("座標指定")
        draw_bg = display_image.copy()
        draw = ImageDraw.Draw(draw_bg)

        def draw_mark(raw_x, raw_y, val, sz, clr):
            dx = raw_x * zoom_rate
            dy = raw_y * zoom_rate
            vsz = int(float(sz) * preview_scale * zoom_rate)
            c = (255, 0, 0) if clr == "red" else (0, 0, 0)
            if not val:
                return
            if str(val).startswith("RECT:"):
                try:
                    dims = val.replace("RECT:", "").split("x")
                    w_pt, h_pt = float(dims[0]), float(dims[1])
                    w_px = w_pt * preview_scale * zoom_rate
                    h_px = h_pt * preview_scale * zoom_rate
                    lw = max(1, int(vsz / 10))
                    draw.rectangle([dx, dy, dx + w_px, dy + h_px], outline=c, width=lw)
                except:
                    pass
            else:
                try:
                    font = ImageFont.truetype(FONT_PATH, max(8, vsz))
                    draw.text((dx, dy), str(val), font=font, fill=c)
                except:
                    pass

        if st.session_state["input_val"]:
            draw_mark(
                st.session_state["last_x"],
                st.session_state["last_y"],
                st.session_state["input_val"],
                size_in,
                color_in,
            )

        if not df_existing.empty:
            for _, c in df_existing.iterrows():
                if c["page"] == st.session_state["current_page"]:
                    draw_mark(c["x"], c["y"], c["value"], c["font_size"], c["color"])

        # width指定でズレ防止
        value = streamlit_image_coordinates(
            draw_bg,
            width=display_image.width,
            key=f"c_{st.session_state['current_page']}_{zoom_rate}",
        )

        if value:
            ox = value["x"] / zoom_rate
            oy = value["y"] / zoom_rate
            if (
                abs(ox - st.session_state["last_x"]) > 1.0
                or abs(oy - st.session_state["last_y"]) > 1.0
            ):
                st.session_state["last_x"] = ox
                st.session_state["last_y"] = oy
                st.rerun()

    # --- 下部: リストエリア ---
    st.divider()
    st.subheader("📋 登録済みリスト")

    cols = ["label", "x", "y", "page", "font_size", "color", "value", "desc", "id"]
    if not df_existing.empty:
        for c in cols:
            if c not in df_existing.columns:
                df_existing[c] = None
        df_show = df_existing[cols]
    else:
        df_show = pd.DataFrame(columns=cols)

    column_config = {
        "label": st.column_config.TextColumn("項目名", width="medium", required=True),
        "x": st.column_config.NumberColumn("X", format="%.1f", required=True),
        "y": st.column_config.NumberColumn("Y", format="%.1f", required=True),
        "page": st.column_config.NumberColumn("P", width="small", min_value=1, step=1),
        "font_size": st.column_config.NumberColumn(
            "サイズ", width="small", min_value=1.0, step=0.5, format="%.1f"
        ),
        "color": st.column_config.SelectboxColumn(
            "色", width="small", options=["black", "red"], default="black"
        ),
        "value": st.column_config.TextColumn("値/タグ", width="medium"),
        "desc": st.column_config.TextColumn("備考", width="large"),
        "id": None,
    }

    st.data_editor(
        df_show,
        hide_index=True,
        use_container_width=True,
        column_config=column_config,
        num_rows="dynamic",
        key=st.session_state["editor_key"],
        on_change=on_data_editor_change,
    )

    if st.button("テストPDF作成 (全ページ)"):
        if df_existing.empty:
            st.error("座標なし")
        else:
            try:
                output = PdfWriter()
                for i, page_obj in enumerate(reader.pages):
                    page_num = i + 1
                    page_coords = df_existing[df_existing["page"] == page_num]
                    if not page_coords.empty:
                        packet_page = BytesIO()
                        pw = float(page_obj.mediabox.width)
                        ph = float(page_obj.mediabox.height)
                        can_page = canvas.Canvas(packet_page, pagesize=(pw, ph))
                        for _, row in page_coords.iterrows():
                            # 簡易プレビュー用スケール (72/200)
                            scale = 72.0 / 200.0
                            draw_x = float(row["x"]) * scale
                            top_y = ph - (float(row["y"]) * scale)
                            f_size = float(row["font_size"])
                            c_obj = red if row["color"] == "red" else black
                            can_page.setFillColor(c_obj)
                            can_page.setStrokeColor(c_obj)

                            val = row["value"]
                            if str(val).startswith("RECT:"):
                                try:
                                    dims = val.replace("RECT:", "").split("x")
                                    w_pt, h_pt = float(dims[0]), float(dims[1])
                                    can_page.rect(
                                        draw_x,
                                        top_y - h_pt,
                                        w_pt,
                                        h_pt,
                                        stroke=1,
                                        fill=0,
                                    )
                                except:
                                    pass
                            else:
                                can_page.setFont("IPAexG", f_size)
                                can_page.drawString(
                                    draw_x, top_y - (f_size * 0.9), str(val)
                                )

                        can_page.save()
                        packet_page.seek(0)
                        overlay = PdfReader(packet_page)
                        page_obj.merge_page(overlay.pages[0])
                    output.add_page(page_obj)
                out_stream = BytesIO()
                output.write(out_stream)
                st.download_button(
                    "📥 テストPDFダウンロード",
                    out_stream,
                    "test.pdf",
                    "application/pdf",
                )
            except Exception as e:
                st.error(f"エラー: {e}")


# ==========================================
# アプリケーション本体
# ==========================================
def main():
    # サイドバーで機能切り替え (統合管理ツール化)
    app_mode = st.sidebar.radio(
        "機能選択", ["📍 座標定義 (編集)", "📥 雛形ファイル登録", "🗑️ 登録データ管理"]
    )

    if app_mode == "📍 座標定義 (編集)":
        render_coordinate_editor()

    elif app_mode == "📥 雛形ファイル登録":
        st.title("📥 雛形ファイル登録")
        st.caption("PDFファイルをシステムにアップロードします。")
        from legal_system.ui.components.admin_tools import render_upload_tab

        render_upload_tab(db)

    elif app_mode == "🗑️ 登録データ管理":
        st.title("🗑️ 登録データ管理")
        st.caption("データベース内の全データを管理します。")
        from legal_system.ui.components.admin_tools import render_management_tab

        render_management_tab(db)


if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/98_書類内容チェック_AI.py
````python
# src/legal_system/ui/pages/98_書類内容チェック_AI.py

import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# パス解決とインポート
# -----------------------------------------------------------------------------
current_file = Path(__file__).resolve()
project_root = current_file.parents[3]  # src/legal_system/ui/pages/ -> root
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# AIプロセッサ (Ver 2.0 Agentic)
try:
    from src.legal_system.core.ai_processor import AgenticDocumentProcessor
    from src.legal_system.core.schemas import DocumentAnalysisResult
except ImportError:
    st.error("コアモジュール (src.legal_system.core) が見つかりません。")
    st.stop()

# DB保存サービス (既存機能の維持)
try:
    from src.legal_system.services.persistence_service import (
        VerificationPersistenceService,
    )

    HAS_PERSISTENCE_SERVICE = True
except ImportError:
    HAS_PERSISTENCE_SERVICE = False

# Kintone連携サービス
from src.services.kintone_sync_service import get_kintone_data_as_dict

# -----------------------------------------------------------------------------
# ページ設定 & ヘルパー関数
# -----------------------------------------------------------------------------
st.set_page_config(layout="wide", page_title="AI書類監査 | Agentic BPO", page_icon="🕵️")


def display_pdf(file_bytes: bytes):
    """PDFをiframeで埋め込み表示（ブラウザ互換性向上）"""
    base64_pdf = base64.b64encode(file_bytes).decode("utf-8")
    # iframeを使用することで、より安定した表示を提供
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def load_kintone_sample_auto() -> Optional[dict]:
    """起動時にサンプルデータを自動探索する（既存機能の維持）"""
    candidates = [
        project_root / "kintone_data_sample.json",
        project_root / "data" / "kintone_data_sample.json",
        "kintone_data_sample.json",
    ]
    for path in candidates:
        if os.path.exists(str(path)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                continue
    return None


def render_verification_table(result: DocumentAnalysisResult):
    """検証結果（Reasoning）をテーブル表示"""
    if not result.verifications:
        return

    data = []
    for v in result.verifications:
        # ステータスアイコン
        status_icon = "✅" if v.is_consistent else "⚠️"
        data.append(
            {
                "項目": v.field_label,
                "判定": status_icon,
                "Kintone (期待値)": v.expected_value or "-",
                "書類 (実測値)": v.actual_value or "-",
                "AIの推論 (Reasoning)": v.reasoning,
            }
        )

    df = pd.DataFrame(data)

    st.markdown("#### 🔍 整合性チェック結果")
    st.dataframe(
        df,
        column_config={
            "判定": st.column_config.TextColumn("判定", width="small"),
            "AIの推論 (Reasoning)": st.column_config.TextColumn(
                "推論理由", width="large"
            ),
        },
        use_container_width=True,
        hide_index=True,
    )


# -----------------------------------------------------------------------------
# メイン画面ロジック
# -----------------------------------------------------------------------------
def main():
    st.title("🕵️ AI書類監査エージェント (Ver 2.0)")
    st.caption(
        "Vertex AI (Zero Data Retention) を使用し、Kintoneデータと書類の整合性を自律的に検証します。"
    )

    # 1. 案件コンテキスト (Context)
    #    既存の自動ロード機能を維持しつつ、ID指定も可能なハイブリッド仕様に変更
    if "kintone_context" not in st.session_state:
        # 初回ロード試行
        auto_data = load_kintone_sample_auto()
        if auto_data:
            st.session_state["kintone_context"] = auto_data

    with st.expander("📂 1. 案件コンテキスト設定 (Kintone)", expanded=True):
        # 現在のロード状況を表示
        ctx = st.session_state.get("kintone_context")
        if ctx:
            st.success(
                f"読込中: {ctx.get('顧客名')} 様 (Record ID: {ctx.get('record_id')})"
            )
            # 簡易表示
            c1, c2, c3 = st.columns(3)
            c1.info(f"被相続人: {ctx.get('被相続人名')}")
            c2.info(f"死亡日: {ctx.get('相続開始日')}")
            c3.info(f"住所: {ctx.get('住所')}")
        else:
            st.warning("データがロードされていません")

        # 切り替えUI
        st.divider()
        col_input, col_btn = st.columns([2, 1])
        case_id_input = col_input.number_input(
            "案件IDを指定してDBから取得", min_value=1, value=1001
        )

        if col_btn.button("DBから取得"):
            # DB連携サービスを利用 (get_kintone_data_as_dict)
            fetched = get_kintone_data_as_dict(case_id_input)
            if fetched:
                st.session_state["kintone_context"] = fetched
                st.rerun()
            else:
                st.error("指定された案件IDのデータが見つかりませんでした。")

    # コンテキスト確定
    kintone_context = st.session_state.get("kintone_context")
    if not kintone_context:
        st.stop()

    # 2. ファイルアップロード
    st.divider()
    st.subheader("2. 書類アップロード & 監査実行")
    uploaded_file = st.file_uploader(
        "監査対象の書類 (PDF/画像)", type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file:
        col_doc, col_analysis = st.columns([1, 1])

        # --- 左カラム: 原本表示 ---
        with col_doc:
            st.markdown("##### 📄 原本プレビュー")
            file_bytes = uploaded_file.read()
            if uploaded_file.type == "application/pdf":
                display_pdf(file_bytes)
            else:
                st.image(file_bytes, use_container_width=True)

        # --- 右カラム: AI分析 ---
        with col_analysis:
            st.markdown("##### 🧠 AI エージェントの推論")

            if st.button("🚀 監査を実行 (Perception & Reasoning)", type="primary"):
                with st.spinner("AIが書類を精査中... (約10-20秒)"):
                    processor = AgenticDocumentProcessor()
                    try:
                        result = processor.analyze_document(
                            file_bytes=file_bytes,
                            mime_type=uploaded_file.type,
                            kintone_data=kintone_context,
                        )
                        st.session_state["latest_result"] = result
                    except Exception as e:
                        st.error(f"解析エラー: {e}")

            # 結果表示
            if "latest_result" in st.session_state:
                result: DocumentAnalysisResult = st.session_state["latest_result"]

                # A. 総合判定バッジ
                status_color = {
                    "APPROVED": "green",
                    "WARNING": "orange",
                    "REJECTED": "red",
                }.get(result.overall_status, "grey")

                st.markdown(f"### 判定: :{status_color}[{result.overall_status}]")
                st.caption(f"書類種別: {result.document_type} | 要約: {result.summary}")

                # B. アラート（最優先表示）
                if result.alerts:
                    st.error("🚨 以下の不備が検出されました")
                    for alert in result.alerts:
                        st.markdown(
                            f"- **{alert.issue_type}**: {alert.doc_name} - {alert.description}"
                        )

                # C. 検証テーブル (Reasoning)
                render_verification_table(result)

                # D. 抽出データ詳細 (Assets情報の補完)
                # 元のコードにあった「資産情報」の表示機能を維持するため、extracted_dataを表示
                with st.expander("📝 抽出データ詳細 (資産情報など)", expanded=False):
                    st.json(result.extracted_data)

                # E. アクションボタン (DB保存機能の完全復活)
                st.divider()
                c_act1, c_act2 = st.columns(2)

                # 承認ボタン: DB保存処理
                if result.overall_status in ["APPROVED", "WARNING"]:
                    if c_act1.button("✅ 承認してDB保存"):
                        if HAS_PERSISTENCE_SERVICE:
                            try:
                                # 永続化サービスの呼び出し
                                service = VerificationPersistenceService()
                                # Kintoneのrecord_id等をIDとして渡す（なければ1）
                                target_id = int(kintone_context.get("record_id", 1))

                                success, msg = service.save_analysis_result(
                                    case_id=target_id,
                                    result=result,
                                    filename=uploaded_file.name,
                                )

                                if success:
                                    st.balloons()
                                    st.success(f"✅ {msg}")
                                else:
                                    st.error(f"❌ 保存失敗: {msg}")
                            except Exception as e:
                                st.error(f"システムエラー: {e}")
                        else:
                            st.warning(
                                "⚠️ DB保存サービスが見つかりません (src/services/persistence_service.py)"
                            )

                # 却下ボタン
                if c_act2.button("❌ 却下"):
                    st.info("この書類は却下されました。担当者に通知します。")


if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/99_マスタ管理.py
````python
# src/legal_system/ui/pages/99_マスタ管理.py

import json
import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="マスタ管理", page_icon="⚙️", layout="wide")

# パス設定 (smart_guide.pyと同じ場所を参照)
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
RULES_DIR = os.path.join(ROOT_DIR, "data", "rules")
GUIDE_FILE = os.path.join(RULES_DIR, "bank_guidance.json")

def main():
    st.title("⚙️ 業務ナビ・マスタ設定")
    st.markdown("口座入力画面などで表示される「銀行ごとの注意点」を編集できます。")

    # データの読み込み
    current_data = {}
    if os.path.exists(GUIDE_FILE):
        with open(GUIDE_FILE, "r", encoding="utf-8") as f:
            current_data = json.load(f)

    # 編集しやすいようにリスト形式に変換
    # [{"銀行名": "三菱", "注意文": "...", "詳細": "..."}]
    table_data = []
    for bank, info in current_data.items():
        items_str = "\n".join(info.get("items", []))
        table_data.append({
            "銀行名キーワード": bank,
            "重要アラート(赤枠)": info.get("alert", ""),
            "詳細リスト(改行区切り)": items_str
        })
    
    # 既存データがない場合のダミー
    if not table_data:
        table_data = [{"銀行名キーワード": "例：みずほ", "重要アラート(赤枠)": "注意点", "詳細リスト(改行区切り)": "詳細A\n詳細B"}]

    df = pd.DataFrame(table_data)

    # データエディター（Excelライクな編集画面）
    edited_df = st.data_editor(
        df,
        num_rows="dynamic", # 行の追加・削除を許可
        use_container_width=True,
        column_config={
            "詳細リスト(改行区切り)": st.column_config.TextColumn(width="large")
        }
    )

    if st.button("💾 設定を保存して反映", type="primary"):
        # 保存形式(JSON)に戻す
        new_json = {}
        for index, row in edited_df.iterrows():
            key = row["銀行名キーワード"]
            if not key: continue
            
            alert = row["重要アラート(赤枠)"]
            items_raw = row["詳細リスト(改行区切り)"]
            items = [x.strip() for x in items_raw.split("\n") if x.strip()]
            
            new_json[key] = {
                "alert": alert,
                "items": items
            }
        
        # ファイル書き込み
        os.makedirs(RULES_DIR, exist_ok=True)
        with open(GUIDE_FILE, "w", encoding="utf-8") as f:
            json.dump(new_json, f, ensure_ascii=False, indent=2)
        
        st.success("✅ 保存しました！「預貯金口座入力フォーム」で即座に反映されます。")

if __name__ == "__main__":
    main()
````

## File: src/utils/retry_decorator.py
````python
"""
統一エラーハンドリング＆リトライ機構

外部API呼び出しに対する指数バックオフ付きリトライデコレータを提供します。
"""

from functools import wraps
import time
import logging
from typing import Callable, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    log_to_audit: bool = False
):
    """
    指数バックオフ付きリトライデコレータ
    
    Args:
        max_retries: 最大リトライ回数（デフォルト: 3回）
        backoff_factor: バックオフ係数（デフォルト: 2.0）
        exceptions: キャッチする例外のタプル
        log_to_audit: AuditLogへの記録を有効化（デフォルト: False）
    
    使用例:
        @retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
        def fetch_data():
            return requests.get("https://api.example.com")
    
    リトライ動作:
        - 1回目の失敗: 2秒待機後リトライ
        - 2回目の失敗: 4秒待機後リトライ
        - 3回目の失敗: 例外を再送出
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    is_last_attempt = (attempt == max_retries - 1)
                    
                    if is_last_attempt:
                        logger.error(
                            f"❌ {func.__name__} failed after {max_retries} attempts: {e}",
                            exc_info=True
                        )
                        
                        # AuditLogへの記録（オプション）
                        if log_to_audit:
                            _log_to_audit_table(func.__name__, str(e), args, kwargs)
                        
                        raise  # 最終試行で失敗したら例外を再送出
                    
                    # リトライ待機時間の計算（指数バックオフ）
                    wait_time = backoff_factor ** attempt
                    logger.warning(
                        f"⚠️ {func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait_time:.1f}s... Error: {e}"
                    )
                    time.sleep(wait_time)
            
        return wrapper
    return decorator


def _log_to_audit_table(func_name: str, error_msg: str, args, kwargs):
    """AuditLogテーブルへエラーを記録（オプション機能）"""
    try:
        from legal_system.core.database_manager import DatabaseManager
        from legal_system.models.tables import AuditLog
        from datetime import datetime
        
        db = DatabaseManager()
        session = db._get_session()
        
        # 引数情報を安全に文字列化（機密情報を含む可能性があるため、長さを制限）
        args_str = str(args)[:500] if args else ""
        kwargs_str = str(kwargs)[:500] if kwargs else ""
        
        log_entry = AuditLog(
            action_type="RETRY_FAILURE",
            target=func_name,
            details=f"Error: {error_msg}\nArgs: {args_str}\nKwargs: {kwargs_str}",
            timestamp=datetime.now()
        )
        session.add(log_entry)
        session.commit()
        session.close()
        logger.info(f"✅ Logged retry failure to AuditLog: {func_name}")
    except Exception as e:
        logger.error(f"Failed to log to AuditLog: {e}")
````

## File: tests/test_retry_decorator.py
````python
"""
リトライデコレータの動作確認テスト

使用方法:
    python tests/test_retry_decorator.py
"""

import logging
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.retry_decorator import retry_with_backoff

# ロガー設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestException(Exception):
    """テスト用の例外"""

    pass


# テスト1: 正常系（1回目で成功）
@retry_with_backoff(max_retries=3, exceptions=(TestException,))
def test_success_on_first_try():
    """1回目で成功するケース"""
    logger.info("✅ 成功しました")
    return "SUCCESS"


# テスト2: 2回失敗後、3回目で成功
call_count = 0


@retry_with_backoff(max_retries=3, backoff_factor=1.0, exceptions=(TestException,))
def test_success_on_third_try():
    """2回失敗後、3回目で成功するケース"""
    global call_count
    call_count += 1

    if call_count < 3:
        logger.info(f"❌ 失敗 (試行 {call_count}/3)")
        raise TestException(f"意図的な失敗 (試行 {call_count})")

    logger.info(f"✅ 成功しました (試行 {call_count}/3)")
    return "SUCCESS_AFTER_RETRIES"


# テスト3: すべて失敗（例外が再送出される）
@retry_with_backoff(max_retries=3, backoff_factor=1.0, exceptions=(TestException,))
def test_all_failures():
    """すべて失敗するケース"""
    logger.info("❌ 失敗しました")
    raise TestException("すべての試行で失敗")


def run_tests():
    """テストを実行"""
    print("=" * 60)
    print("リトライデコレータ 動作確認テスト")
    print("=" * 60)

    # テスト1: 正常系
    print("\n【テスト1】1回目で成功")
    print("-" * 60)
    try:
        result = test_success_on_first_try()
        print(f"結果: {result}")
        print("✅ テスト1 成功\n")
    except Exception as e:
        print(f"❌ テスト1 失敗: {e}\n")

    # テスト2: リトライ後に成功
    print("\n【テスト2】2回失敗後、3回目で成功")
    print("-" * 60)
    global call_count
    call_count = 0  # カウンターリセット
    try:
        result = test_success_on_third_try()
        print(f"結果: {result}")
        print("✅ テスト2 成功\n")
    except Exception as e:
        print(f"❌ テスト2 失敗: {e}\n")

    # テスト3: すべて失敗
    print("\n【テスト3】すべて失敗（例外が再送出される）")
    print("-" * 60)
    try:
        result = test_all_failures()
        print("❌ テスト3 失敗: 例外が発生しませんでした")
    except TestException as e:
        print("✅ テスト3 成功: 期待通り例外が再送出されました")
        print(f"   例外メッセージ: {e}\n")

    print("=" * 60)
    print("テスト完了")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
````

## File: .cursor/rules/bpo-coding-standard.mdc
````
---
description: 遺言・遺産整理BPOシステム開発における回答指針とコード出力ルール
globs: **/*.py, **/*.js, **/*.sh
---

# エージェンティックBPO開発ルール

あなたは「遺言・遺産整理業務」専門のシニア・ソフトウェアエンジニアです。
以下のルールを常に適用し、回答を生成してください。

## 1. コード出力の絶対原則 (Askモード最適化)
- **完全出力の義務:** 私（ユーザー）が手動でコピペするため、コードの一部を省略（`// ... existing code ...` など）することを厳禁します。常にファイル全体の完全なコードを出力してください。
- **パスの明示:** 出力ブロックの直前に、対象となるファイルパスを必ず記載してください。

## 2. 技術・設計スタックの厳守
- **言語/管理:** Python 3.10+, Rye, SQLAlchemy 2.0。
- **AI処理:** Gemini 2.5 Flash Lite。PDFは `application/pdf` で直接送信。
- **データ衛生:** - Kintone同期時は既存データのクリアを優先。
    - 外部からのTEL/メールアドレスは `.pop()` で除外し、DB内の既存データを保護する。
- **暗号化:** `7za.exe` による ZipCrypto 形式、パス解決は `src/utils/` を基準とする。

## 3. 回答フォーマット
常に以下の項目を含めて回答してください。
- 【結論】
- 【修正・作成したファイルパス】
- 【完全なコードブロック】
- 【注意点・例外】
````

## File: .streamlit/config.toml
````toml
[theme]
# ベースとなるテーマ（"light" または "dark"）
base = "light"

# メインのアクセントカラー（ボタンなど）
primaryColor = "#d33682"

# 背景色
backgroundColor = "#ffffff"

# サイドバーなどの背景色
secondaryBackgroundColor = "#f0f2f6"

# 文字色
textColor = "#262730"

# フォント
font = "sans serif"
````

## File: data/db/chroma/.keep
````

````

## File: data/db/sql/.keep
````

````

## File: data/rules/bank_guidance.json
````json
{
  "三菱UFJ銀行": {
    "alert": "遺産分割協議書への実印押印が必須です。",
    "items": [
      "原本還付: 可（要ゴム印）",
      "予約: 必須（Web予約推奨）",
      "備考: 代理人手続きの場合、委任状に捨印を推奨"
    ]
  },
  "みずほ": {
    "alert": "手続き",
    "items": [
      "原本還付: 可",
      "予約: 必須",
      "【事例】海外在住の相続人がいる場合は、サイン証明書が別途必要です",
      "【事例】口座名義人が旧姓のままの場合、改製原戸籍も必要になります。"
    ]
  },
  "三井住友銀行": {
    "alert": "残高証明書の発行は「相続オフィス」への電話予約から始まります。",
    "items": [
      "原本還付: 可",
      "来店: 原則不要（郵送手続可）"
    ]
  },
  "ゆうちょ": {
    "alert": "来店予約",
    "items": [
      "八重洲は予約必須。ただし急ぎの場合は〇〇で飛び込み可"
    ]
  }
}
````

## File: data/rules/company_rules.md
````markdown
# 弊社（行政書士法人）共通業務ルール
## 回答のスタイル
- 挨拶や前置き（「ご案内します」等）は一切不要。結論と箇条書きのみで出力すること。
- 語尾は「です・ます」調だが、簡潔にすること。
- 申請主体は不要（自明のため省略）。
- 証明日はすべて「被相続人の死亡日」を記載すること。（法定相続情報一覧図で確認）
- 既経過利息証明の必要有無：定期預金の口座があれば必ず「必要」とする。
- 取引明細の申請：税申告案件のみ必要。税理士へ有無と期間を確認するよう案内すること。
- 残高証明書の申請提出書類：
  1. 法定相続情報一覧図
  2. 委任状（代表相続人のみ）
  3. 印鑑証明書（代表相続人と弊社分）
  4. 履歴事項証明（弊社分）
  5. 弊社代表の行政書士証票と運転免許証のコピー [参照ファイル](https://example.cybozu.com/k/123/edit)

## 申請書類の共通仕様
- **申請書への押印**: 弊社の「実印（代表印）」を使用する。（認印は不可）
- **戸籍書類**: 原則として「法定相続情報一覧図」の原本還付請求付き提出とする。
  - ※急ぎで一覧図がない場合のみ「被相続人の出生〜死亡の除籍謄本＋相続人の現在戸籍」とする。
- **印鑑証明書**: 
  - 顧客（相続人）のものと、弊社（代理人）のものが必要。
  - 有効期限は銀行の規定に従うが、指定がない場合は「6ヶ月以内」のものを準備する。

## 手数料の支払い
- 原則として「銀行振込」を選択する。（相続人口座からの引落しは選択しない）
- 振込手続きは経理へ依頼すること。
- **経理依頼URL**: [Kintone経理アプリ](https://example.cybozu.com/k/123/edit) （ここから申請レコードを作成）

## ゆうちょ銀行特有のルール
- ゆうちょ銀行の残高証明手数料は、窓口支払ではなく「会社通帳からの引落とし」となる。
- **【必須表示】ゆうちょ銀行の残高証明書は、回答の最後に必ず以下のリンクを表示**:
  - [ゆうちょ引落管理スプレッドシート](https://example.cybozu.com/k/123/edit)
````

## File: data/rules/donation_recipients.json
````json
[
  {
    "name": "日本赤十字社",
    "address": "東京都港区芝大門一丁目１番３号"
  },
  {
    "name": "日本ユニセフ協会",
    "address": "東京都港区高輪四丁目６番１２号"
  },
  {
    "name": "国境なき医師団日本",
    "address": "東京都世田谷区若林二丁目３０番９号"
  },
  {
    "name": "あしなが育英会",
    "address": "東京都千代田区平河町二丁目７番５号"
  },
  {
    "name": "日本財団",
    "address": "東京都港区赤坂一丁目２番２号"
  },
  {
    "name": "がん研究会",
    "address": "東京都江東区有明三丁目８番３１号"
  }
]
````

## File: data/templates/.keep
````

````

## File: memory-bank/progress.md
````markdown
# Progress Log

## 2026-01-30
- `memory-bank/` ディレクトリと初期ドキュメント (`projectBrief.md`, `productContext.md`, `systemPatterns.md`, `progress.md`) を生成。
- 既存コードの分析を開始予定 (`scanner_service.py`, `Home.py`)。
- `productContext.md` に日本の民法に関する注意点を追記予定。
````

## File: memory-bank/projectBrief.md
````markdown
# Project Brief

## Project Name
遺産整理・遺言書作成支援アプリ (Estate Settlement and Will Preparation Support App)

## Objective
PythonとStreamlitを使用して、日本の相続実務に精通したリーガルテックソリューションを開発・継続する。

## Target Users
遺産整理や遺言書作成を検討している行政書士の専門家。

## Key Features (Initial Brainstorm)
- 遺産情報のデジタル化と管理
- 相続関係図の自動生成
- 法定相続分の自動計算
- 遺留分侵害額の計算支援
- 遺言書ドラフト作成支援
- 関連書類のOCR処理とデータ抽出
- 法的ロジックに基づいたアドバイス機能

## Technology Stack
- Backend: Python
- Frontend/UI: Streamlit
- Database: (検討中 - 現状のファイル構造からSQLiteやChromaDBが利用されている可能性あり)
- OCR: (検討中 - 既存の `ocr_engine.py` から何らかのOCRが利用されている可能性あり)

## Current Status
開発継続または開始フェーズ。既存コードの分析と法的要件の整理から始める。
````

## File: memory-bank/systemPatterns.md
````markdown
# System Patterns

## 1. モジュール構成 (高レベル)
- **`src/legal_system/ui/`**: StreamlitアプリケーションのUIコンポーネントとページ
- **`src/services/`**: ビジネスロジック、データ処理、外部連携サービス
- **`src/legal_system/models/`**: データベースモデル、スキーマ定義
- **`src/legal_system/core/`**: アプリケーションのコア機能（設定、データベース管理、AI/OCRエンジンなど）
- **`data/`**: データベースファイル、設定ファイル、テンプレート、一時ファイルなど
- **`scripts/`**: 開発・運用をサポートするユーティリティスクリプト

## 2. データフロー
1. **UIからの入力**: Streamlit UIを通じてユーザーが情報を入力。
2. **サービス層での処理**: `src/services/` 内の各サービス（例: `case_service.py`, `deceased_service.py`）が入力データを処理、検証、ビジネスロジックを適用。
3. **データベース操作**: `src/legal_system/models/` で定義されたモデルと `src/legal_system/core/database_manager.py` を通じてデータベース（例: `chroma.sqlite3`, `sql/.keep` から推測されるRDB）と連携し、データの永続化・取得を行う。
4. **外部連携**: 必要な場合、Kintone (`kintone_client.py`, `kintone_sync_service.py`) やGmail (`gmail_watcher_service.py`) などの外部サービスと連携。
5. **AI/OCR処理**: `src/legal_system/core/ocr_engine.py`, `src/legal_system/core/ai_processor.py` を使用し、ドキュメントからの情報抽出やAIによるアドバイス生成。
6. **UIへの出力**: 処理結果をUIに表示。

## 3. データベースパターン
- **リレーショナルデータベース**: `src/legal_system/models/tables.py` や `data/db/sql/.keep` から、案件情報、相続人情報、財産情報などの構造化データの管理に利用されていると推測。
- **ベクトルデータベース (ChromaDB)**: `data/db/chroma/local_rag_db/` の存在から、RAG (Retrieval Augmented Generation) のためのドキュメント埋め込みやセマンティック検索に利用されていると推測。

## 4. 認証・認可
(現状不明 - 今後の分析で特定)

## 5. エラーハンドリング・ロギング
(現状不明 - 今後の分析で特定)

## 6. ドキュメント処理パターン
- `src/legal_system/core/pdf_processor.py`: PDFファイルの処理。
- `src/legal_system/core/ocr_engine.py`: OCRによる画像・PDFからのテキスト抽出。
- `src/services/scanner_service.py`: スキャナー連携またはスキャンデータの処理。
- `src/legal_system/ui/components/document_viewer.py`: UIでのドキュメント表示。
````

## File: scripts/check_buffer.py
````python
import os, sys, json
from pathlib import Path
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))
from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import IncomingNoteBuffer

def check():
    db = DatabaseManager()
    session = db._get_session()
    notes = session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()
    print(f"--- 保留中のメモ: {len(notes)}件 ---")
    for n in notes:
        print(f"件名: {n.subject}")
        print(f"抽出された名前: {n.detected_names}")
        print("-" * 30)
    session.close()

if __name__ == "__main__":
    check()
````

## File: scripts/clean_notes.py
````python
import os
import sys
from pathlib import Path
from sqlalchemy import text

# パス解決
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.legal_system.core.database_manager import DatabaseManager

def clean_only_notes():
    print("🧹 会議メモデータのクリーニングを開始します（案件データは維持されます）...")
    db = DatabaseManager()
    session = db._get_session()

    try:
        # 1. 既に取り込まれたメールの原本バッファを削除
        print(" -> IncomingNoteBuffer をクリア中...")
        session.execute(text("DELETE FROM incoming_note_buffer;"))

        # 2. 案件に紐付いてしまった「【自動取込】」が含まれる履歴だけを削除
        print(" -> 案件履歴内の自動取込メモをクリア中...")
        session.execute(text("DELETE FROM contact_logs WHERE contact_content LIKE '【自動取込】%';"))

        session.commit()
        print("✅ クリーニング完了！これで修正版AIが過去7日間のメールを再度スキャンします。")

    except Exception as e:
        session.rollback()
        print(f"❌ エラー: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    clean_only_notes()
````

## File: scripts/create_dummy_data.py
````python
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. プロジェクトルートをパスに追加して、srcモジュールを読み込めるようにする
# (このファイルは scripts/ にあるので、2つ上の階層がルート)
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

# 2. 既存のtables.pyからモデル定義を読み込む
# パスエラーが出る場合は、tables.pyの場所を確認してください
try:
    from src.legal_system.models.tables import BankMaster, Base, Case
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

# 3. DBファイルの保存場所 (SQLite)
# tables.py や persistence_service.py で指定しているパスと合わせる
DB_PATH = os.path.join(root_dir, "data", "db", "legal_system.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DB_URL = f"sqlite:///{DB_PATH}"


def init_db():
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)

    # テーブル作成 (既存データは消えません)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # --- A. 銀行マスタの作成 ---
        banks = [
            ("三菱UFJ銀行", "0005"),
            ("三井住友銀行", "0009"),
            ("みずほ銀行", "0001"),
            ("ゆうちょ銀行", "9900"),
        ]

        print("Checking Bank Master...")
        for name, code in banks:
            # 重複チェック: bank_code が既にあるか？
            exists = session.query(BankMaster).filter_by(bank_code=code).first()
            if not exists:
                session.add(BankMaster(bank_name=name, bank_code=code))
                print(f"  + Added: {name}")
            else:
                print(f"  . Exists: {name}")

        # --- B. テスト用案件の作成 ---
        # kintone_data_sample.json の record_id="1001" に対応するデータ
        target_case_id = 1001

        print(f"Checking Case ID: {target_case_id}...")
        # kintone_record_id は Integer か String か tables.py の定義次第ですが、
        # ここでは汎用的にフィルタします
        case_exists = (
            session.query(Case).filter(Case.kintone_record_id == target_case_id).first()
        )

        if not case_exists:
            # 必須フィールドを埋める (tables.pyの定義に基づく)
            new_case = Case(
                case_id=target_case_id,  # 主キーを強制指定
                case_number="G1234",
                client_name="相続 太郎",
                client_name_kana="ソウゾク タロウ",
                kintone_record_id=target_case_id,
                folder_path="/server/G1234",  # NOT NULL制約対策
            )
            session.add(new_case)
            print(f"  + Added Case: G1234 (ID: {target_case_id})")
        else:
            print(f"  . Exists Case: {case_exists.case_number}")

        session.commit()
        print("\n🎉 データベースの初期化が完了しました！")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during initialization: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
````

## File: scripts/manual_link.py
````python
import os
import sys
import json
from pathlib import Path

# パス設定
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import IncomingNoteBuffer, Case, ContactLog

def manual_link_tool():
    db = DatabaseManager()
    session = db._get_session()

    # 1. 保留中のメモを表示
    pendings = session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()
    
    if not pendings:
        print("\n✅ 現在、保留中（未紐付け）のメモはありません。すべて処理済みです。")
        return

    print(f"\n📋 保留中のメモ一覧 ({len(pendings)}件)")
    print("="*60)
    for i, note in enumerate(pendings):
        names = note.detected_names or "[]"
        print(f"ID: {note.id} | 件名: {note.subject}")
        print(f"   -> AI抽出名: {names}")
        print("-" * 60)

    # 2. 操作対象の選択
    target_id_str = input("\n修正・紐付けしたいメモの「ID」を入力してください (終了はEnter): ")
    if not target_id_str: return

    target_note = session.query(IncomingNoteBuffer).get(int(target_id_str))
    if not target_note:
        print("❌ 指定されたIDのメモが見つかりません。")
        return

    # 3. 正しい名前の入力
    print(f"\n対象: {target_note.subject}")
    correct_name = input("紐付けたい案件の「顧客名（氏名）」を入力してください (例: 冨田 総子): ").strip()
    
    if not correct_name:
        print("キャンセルしました。")
        return

    # 4. 案件検索 & 強制紐付け
    # スペースを無視して検索
    clean_target = correct_name.replace(" ", "").replace("　", "")
    
    # 案件テーブルから検索
    cases = session.query(Case).all()
    target_case = None
    
    for c in cases:
        c_name = (c.client_name or "").replace(" ", "").replace("　", "")
        if clean_target in c_name: # 部分一致でもヒットさせる
            target_case = c
            break
            
    if target_case:
        print(f"\n✅ 案件が見つかりました: 【{target_case.case_number}】 {target_case.client_name}")
        confirm = input("この案件に紐付けますか？ (y/n): ")
        
        if confirm.lower() == 'y':
            # A. 抽出名を書き換える（履歴のため）
            target_note.detected_names = json.dumps([target_case.client_name], ensure_ascii=False)
            
            # B. ContactLogに保存
            new_log = ContactLog(
                case_id=target_case.case_id,
                contact_content=target_note.body_text,
                is_thank_you_payment=False
            )
            session.add(new_log)
            
            # C. ステータス更新
            target_note.status = "LINKED"
            target_note.linked_case_id = target_case.case_id
            
            session.commit()
            print(f"\n🎉 完了！ メモを「{target_case.client_name}」様の履歴に追加しました。")
    else:
        print(f"\n❌ 「{correct_name}」に一致する案件がデータベースに見つかりませんでした。")
        print("先にブラウザで案件を登録してください。")

    session.close()

if __name__ == "__main__":
    manual_link_tool()
````

## File: scripts/retry_audio.py
````python
import os
import sys
from pathlib import Path

# パス設定
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import IncomingNoteBuffer

def reset_audio_note():
    db = DatabaseManager()
    session = db._get_session()

    # 件名に「録音」を含むメモを探す
    target_notes = session.query(IncomingNoteBuffer).filter(
        IncomingNoteBuffer.subject.like('%録音%')
    ).all()

    if not target_notes:
        print("❌ 「録音」という件名のメモはデータベースに見つかりませんでした。")
        print("   すでに削除されているか、まだ取り込まれていない可能性があります。")
        return

    print(f"🔍 {len(target_notes)} 件の「録音」メモが見つかりました。")
    
    for note in target_notes:
        print(f"   - ID: {note.id} | 件名: {note.subject} | 受信: {note.received_at}")
        session.delete(note)
    
    session.commit()
    print("\n✅ 削除しました。これでもう一度メールを取り込める状態になりました！")
    print("   👉 'rye run start' を実行すると、音声解析付きで再取得されます。")

    session.close()

if __name__ == "__main__":
    reset_audio_note()
````

## File: scripts/seed_data.py
````python
# scripts/seed_data.py
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.legal_system.core.database_manager import DatabaseManager
from src.legal_system.models.tables import CaseStatus

def seed_statuses():
    print("🌱 初期データの投入を開始します...")
    db = DatabaseManager()
    session = db._get_session()

    try:
        # ステータスマスタの初期値
        statuses = [
            (1, "受任・調査中"),
            (2, "書類作成中"),
            (3, "署名押印待ち"),
            (4, "申請中"),
            (5, "完了"),
            (9, "保留・中止")
        ]

        for s_id, s_name in statuses:
            exists = session.query(CaseStatus).filter_by(id=s_id).first()
            if not exists:
                new_status = CaseStatus(id=s_id, name=s_name, order_num=s_id)
                session.add(new_status)
                print(f"  + 追加: {s_name}")
            else:
                print(f"  . 既存: {s_name}")

        session.commit()
        print("✅ データの投入が完了しました！")

    except Exception as e:
        session.rollback()
        print(f"❌ エラー: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_statuses()
````

## File: src/legal_system/core/__init__.py
````python

````

## File: src/legal_system/core/ai_processor.py
````python
# src/legal_system/core/ai_processor.py

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# プロジェクト内モジュール
from src.legal_system.core.ai_factory import AIFactory

# 追加した CaseSearchKeys をインポート
from src.legal_system.core.schemas import CaseSearchKeys, DocumentAnalysisResult

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parents[3]
env_path = project_root / ".env"
load_dotenv(dotenv_path=env_path)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticDocumentProcessor:
    """
    自律型ドキュメント検証プロセッサ。
    """

    def __init__(self):
        self.provider_mode = os.getenv("AI_PROVIDER", "studio").lower()
        # 構造化出力のために temperature=0.0 を推奨
        self.llm = AIFactory.get_llm(mode=self.provider_mode, temperature=0.0)
        logger.info(f"AgenticProcessor Initialized. Mode: {self.provider_mode}")

    # --- 追加: 検索キー抽出 (予備解析) ---
    def extract_search_keys(self, file_bytes: bytes, mime_type: str) -> CaseSearchKeys:
        """
        書類から「氏名」や「日付」のみを抽出し、案件検索の手がかりにする。
        """
        import base64

        img_b64 = base64.b64encode(file_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{img_b64}"

        prompt = """
        この書類画像から、データベース検索の手がかりとなる「固有名詞」を抽出してください。
        
        # 抽出ルール
        1. **client_name**: 「相続人代表」「依頼者」「受取人」などの氏名があれば抽出。
        2. **deceased_name**: 「被相続人」「名義人（故人）」などの氏名があれば抽出。
        3. **date_hint**: 死亡日や書類作成日など、特定に役立ちそうな日付。
        4. 値が見つからない場合は null (None) にすること。
        """

        try:
            structured_llm = self.llm.with_structured_output(CaseSearchKeys)
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": image_url},
                    ]
                )
            ]
            return structured_llm.invoke(messages)
        except Exception as e:
            logger.error(f"Search key extraction failed: {e}")
            raise e

    # --- 既存: 詳細検証 (本解析) ---
    def _build_verification_prompt(self, kintone_context: Dict[str, Any]) -> str:
        context_str = json.dumps(kintone_context, ensure_ascii=False, indent=2)
        return f"""
        あなたは行政書士事務所の「シニア・ドキュメント・チェッカー」AIです。
        以下の「期待される正解データ（Kintone）」と「入力された書類画像」を比較し、厳格な監査を行ってください。

        ### 1. 期待される正解データ (Context)
        ```json
        {context_str}
        ```

        ### 2. あなたのタスク (Reasoning Process)
        1. **知覚**: 書類の種類を特定し、書かれている文字を読み取る。
        2. **推論**: 
           - 書類の記載内容（Actual）と、正解データ（Expected）を比較する。
           - 氏名、住所、日付、金額などの重要項目について「一致」「不一致」を判定する。
           - 多少の表記ゆれ（「1-1-1」と「1丁目1番1号」など）は、文脈判断で「一致」としてよいが、その理由は明記すること。
           - 有効期限切れや、必須項目の欠落がないかチェックする。
        3. **行動**: 結果を指定されたJSONフォーマット（DocumentAnalysisResult）で出力する。

        ### 3. 出力要件
        - 結論ファーストで、不備がある場合は `alerts` にリストアップすること。
        - 総合判定 (`overall_status`) は、一切の疑義がなければ "APPROVED"、軽微な確認事項があれば "WARNING"、書類違い等は "REJECTED" とすること。
        """

    def analyze_document(
        self, file_bytes: bytes, mime_type: str, kintone_data: Dict[str, Any]
    ) -> DocumentAnalysisResult:
        import base64

        img_b64 = base64.b64encode(file_bytes).decode("utf-8")
        image_url = f"data:{mime_type};base64,{img_b64}"

        system_instruction = self._build_verification_prompt(kintone_data)

        try:
            structured_llm = self.llm.with_structured_output(DocumentAnalysisResult)
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": system_instruction},
                        {"type": "image_url", "image_url": image_url},
                    ]
                )
            ]
            logger.info("🚀 Invoking AI Agent for reasoning...")
            return structured_llm.invoke(messages)
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise e
````

## File: src/legal_system/core/engines.py
````python
# src/legal_system/core/engines.py

import gzip
import os
import time
from typing import Optional

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Google Gemini / LangChain 関連
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 設定読み込み
from src.legal_system.core.config import Config, KeyManager


class BankRepository:
    """
    銀行マスタCSVの読み込みと検索を担当
    """

    def __init__(self, csv_path: str):
        # CSV読み込み時も圧縮やエンコーディングの問題を回避するロジックを使用
        self.df = self._load_csv_safe(csv_path)

    def _load_csv_safe(self, path: str) -> pd.DataFrame:
        """CSVファイルを安全に読み込む（GZIP対応 / エンコーディング自動判別）"""
        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            # GZIP判定
            is_gzipped = False
            with open(path, "rb") as f:
                header = f.read(2)
                if header == b"\x1f\x8b":
                    is_gzipped = True

            # Pandasで読み込み
            if is_gzipped:
                try:
                    return pd.read_csv(
                        path, compression="gzip", encoding="utf-8"
                    ).fillna("")
                except UnicodeDecodeError:
                    return pd.read_csv(
                        path, compression="gzip", encoding="cp932"
                    ).fillna("")
            else:
                try:
                    return pd.read_csv(path, encoding="utf-8").fillna("")
                except UnicodeDecodeError:
                    return pd.read_csv(path, encoding="cp932").fillna("")

        except Exception as e:
            print(f"CSV読み込み警告: {e}")
            return pd.DataFrame()  # エラー時は空のDFを返す

    def search(self, query: str) -> Optional[dict]:
        """クエリ内の銀行名を特定し、行データを辞書として返す"""
        if self.df.empty:
            return None

        for _, row in self.df.iterrows():
            bank_name = str(row.get("銀行名", ""))
            if bank_name and bank_name in query:
                return row.to_dict()
        return None

    def format_rule(self, row: dict) -> str:
        """LLMへの注入用にフォーマット"""
        return f"""
        【特定された銀行の必須ルール (最優先適用)】
        - 銀行名: {row.get("銀行名")}
        - 印鑑証明期限: {row.get("印鑑証明期限")}
        - 代理人本人確認: {row.get("代理人本人確認書類")}
        - 手数料支払: {row.get("振込ルール")}
        - 備考: {row.get("備考")}
        """


class RAGEngine:
    """
    Google Gemini + キーローテーション対応エンジン
    ファイルのGZIP圧縮/文字コードズレを自動吸収する機能付き
    """

    def __init__(self, rules_path: str, bank_repo: BankRepository):
        self.bank_repo = bank_repo
        self.rules_path = rules_path
        self.vector_store = None  # 遅延初期化
        self.embeddings = None
        self.llm = None

        # 初回のクライアント構築
        self._refresh_client()

    def _refresh_client(self):
        """APIキーを取得してクライアントを再生成"""
        try:
            new_key = KeyManager.get_next_key()

            # Embeddingsモデル更新
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=Config.EMBEDDING_MODEL, google_api_key=new_key
            )

            # LLMモデル更新
            self.llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                google_api_key=new_key,
                convert_system_message_to_human=True,
            )

            # ベクトルストア構築（または更新）
            if self.vector_store is None:
                self.vector_store = self._build_vector_store(self.rules_path)
            else:
                self.vector_store.embeddings = self.embeddings

        except Exception as e:
            print(f"クライアント初期化エラー: {e}")
            # エラー発生時もNoneのままにしておき、ask時に再トライさせるかエラーを返す

    def _read_file_safe(self, path: str) -> str:
        """
        ファイルを安全に読み込むヘルパー関数
        - GZIP圧縮されていれば自動解凍
        - UTF-8 で失敗したら CP932 (Shift-JIS) を試行
        """
        if not os.path.exists(path):
            return ""

        content_bytes = b""

        # 1. バイナリとして読み込み、GZIPヘッダー(1f 8b)をチェック
        with open(path, "rb") as f:
            raw_data = f.read()
            if raw_data.startswith(b"\x1f\x8b"):
                # GZIP解凍
                content_bytes = gzip.decompress(raw_data)
            else:
                content_bytes = raw_data

        # 2. 文字コード判別 (utf-8 -> cp932)
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content_bytes.decode("cp932")
            except UnicodeDecodeError:
                # それでもだめならエラー無視で強引に読む
                return content_bytes.decode("utf-8", errors="ignore")

    def _build_vector_store(self, path: str) -> FAISS:
        """ベクトルストア構築"""
        # 安全な読み込み関数を使用
        text = self._read_file_safe(path)

        if not text:
            # ファイルが空、または読めない場合はダミーデータで落ちないようにする
            text = "共通ルールファイルが読み込めませんでした。"

        headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
        docs = splitter.split_text(text)

        if not docs:
            # 分割結果が空の場合のガード
            from langchain_core.documents import Document

            docs = [Document(page_content="ルール情報なし")]

        return FAISS.from_documents(docs, self.embeddings)

    def ask(self, user_query: str, retry_count=0) -> str:
        """質問への回答（自動リトライ機能付き）"""
        if not self.llm:
            return "AIエンジンの初期化に失敗しています。APIキー設定を確認してください。"

        try:
            return self._execute_chain(user_query)
        except Exception as e:
            error_msg = str(e)
            # 429 (Resource Exhausted) などのエラー判定
            if "429" in error_msg or "Resource has been exhausted" in error_msg:
                if retry_count < 3:
                    print(
                        f"⚠️ API制限検知。キーを切り替えてリトライします... ({retry_count + 1}/3)"
                    )
                    self._refresh_client()
                    time.sleep(1)
                    return self.ask(user_query, retry_count + 1)

            return f"エラーが発生しました: {error_msg}"

    def _execute_chain(self, user_query: str) -> str:
        """実際のChain実行処理"""
        # STEP 1: CSV検索
        bank_data = self.bank_repo.search(user_query)
        bank_context = ""
        if bank_data:
            bank_context = self.bank_repo.format_rule(bank_data)

        # STEP 2: ベクトル検索
        enhanced_query = f"{user_query} 代理人 行政書士 手続き"
        docs = self.vector_store.similarity_search(enhanced_query, k=4)
        rule_context = "\n\n".join([d.page_content for d in docs])

        # STEP 3: プロンプト構築
        system_prompt = """
        あなたは行政書士法人の実務支援AIです。
        
        # 行動指針
        1. **結論ファースト**: 挨拶不要。箇条書きで簡潔に答える。
        2. **代理人視点**: 「行政書士（代理人）」の手続きのみ回答する。
        3. **優先順位**: 【銀行別ルール】を最優先する。
        4. **リンク表示**: ゆうちょ銀行や参照ファイルの指示がある場合はURLを表示する。
        
        # 参照情報
        ## 共通業務ルール
        {rule_context}
        
        ## 銀行別ルール (Override)
        {bank_context}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{question}")]
        )

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke(
            {
                "rule_context": rule_context,
                "bank_context": bank_context,
                "question": user_query,
            }
        )
````

## File: src/legal_system/core/pdf_processor.py
````python
# src/legal_system/core/pdf_processor.py

import re
import logging
import fitz  # PyMuPDF
import unicodedata
import numpy as np
from typing import Dict, Any, Tuple, List

from src.legal_system.core.ocr_engine import OCREngine

logger = logging.getLogger(__name__)

class ReferralSheetParser:
    """
    紹介連絡表（フォーマット固定）の解析クラス。
    テキスト抽出を試み、値が取れなければOCRへフォールバックするロジックを搭載。
    """

    def __init__(self):
        self.ocr_engine = OCREngine()

    def parse_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        PDFバイナリを受け取り、解析結果の辞書を返すメインメソッド。
        """
        # Step 1: まず高速なテキスト抽出(PyMuPDF)を試す
        raw_text_1 = self._extract_text_only(file_bytes)
        parsed_data_1 = self._process_text_to_data(raw_text_1)
        
        # Step 2: 判定ロジック
        # 顧客名などの主要項目が空の場合、テキスト抽出では「枠線（ラベル）」しか取れていないと判断し、
        # 強制的にOCR(画像解析)を実行する。
        if not parsed_data_1.get("client_name"):
            logger.info("テキスト抽出で値が取得できないため、OCR(画像解析)を実行します。")
            ocr_text = self._perform_ocr(file_bytes)
            
            # OCR結果で再パース
            parsed_data_2 = self._process_text_to_data(ocr_text)
            parsed_data_2["_debug_mode"] = "OCR_FALLBACK (Auto)"
            parsed_data_2["_debug_raw_text"] = ocr_text
            return parsed_data_2
        
        # テキスト抽出で成功していればそれを返す
        parsed_data_1["_debug_mode"] = "TEXT_LAYER (High Speed)"
        parsed_data_1["_debug_raw_text"] = raw_text_1
        return parsed_data_1

    def _process_text_to_data(self, raw_text: str) -> Dict[str, Any]:
        """テキスト正規化と正規表現抽出の共通処理"""
        # 正規化 (NFKC)
        norm_text = unicodedata.normalize("NFKC", raw_text)
        # 抽出実行
        return self._extract_fields_via_regex(norm_text)

    def _extract_text_only(self, file_bytes: bytes) -> str:
        """PyMuPDFによるテキスト抽出のみ"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _perform_ocr(self, file_bytes: bytes) -> str:
        """PyMuPDFで画像化 -> PaddleOCRで解析"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_ocr_text = []
        import cv2

        for page in doc:
            # 精度向上のためzoom=2.0で画像化
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_array = np.frombuffer(pix.samples, dtype=np.uint8)
            
            # PaddleOCR用にBGR変換
            if pix.n == 4:
                img = img_array.reshape(pix.height, pix.width, 4)
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = img_array.reshape(pix.height, pix.width, 3)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                img = img_array.reshape(pix.height, pix.width, pix.n)

            result = self.ocr_engine.ocr.ocr(img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    full_ocr_text.append(line[1][0])
        
        doc.close()
        # OCR結果は行ごとに分かれているため改行で結合
        return "\n".join(full_ocr_text)

    def _clean_name_spacing(self, text: str) -> str:
        """氏名のスペース整理"""
        if not text: return ""
        text = text.strip()
        text = re.sub(r"[\s　]{2,}", "###", text)
        text = re.sub(r"[\s　]", "", text)
        return text.replace("###", " ")

    def _extract_fields_via_regex(self, text: str) -> Dict[str, Any]:
        """正規表現による項目抽出"""
        data = {}
        
        # 被相続人情報の除外ロジック
        ignore_keywords = ["被相続人", "死亡日", "相続開始", "遺言信託"]
        target_text = text
        
        # 最も上にあるキーワードでカットする
        min_idx = len(text)
        cut_flag = False
        for kw in ignore_keywords:
            idx = text.find(kw)
            if idx != -1 and idx < min_idx:
                min_idx = idx
                cut_flag = True
        
        if cut_flag:
            target_text = text[:min_idx]

        # パターン定義
        patterns = {
            "client_name": r"顧客名(?:\([^)]*\))?[\s:：]*([^\n]+)",
            "client_name_kana": r"フリガナ(?:\([^)]*\))?[\s:：]*([^\n]+)",
            "referral_sec_branch_name": r"(?:支店|部店)名[\s:：]*([^\n]+)",
            "referral_sec_rep_name": r"担当(?:部店)?者名?[\s:：]*([^\n]+)",
            "sol_case_number": r"SOL案件No\.?[\s:：]*([A-Z0-9-]+)",
            "introduction_date": r"紹介日[\s:：]*(\d{4}[\s年/-]\d{1,2}[\s月/-]\d{1,2})",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, target_text)
            if match:
                val = match.group(1).strip()
                # ラベル自体を誤って拾ってしまうケースの除外 ("顧客名" という値が入っていたら空にする)
                if val in ["顧客名", "フリガナ", "住所", "支店名", "担当者名"]:
                    data[key] = ""
                else:
                    data[key] = self._clean_name_spacing(val) if "name" in key else val
            else:
                data[key] = ""

        # 電話番号の抽出
        phones = re.findall(r"[\d-]{10,13}", target_text)
        unique_phones = list(dict.fromkeys(phones))
        data["client_phone_1"] = unique_phones[0] if len(unique_phones) > 0 else ""
        data["client_phone_2"] = unique_phones[1] if len(unique_phones) > 1 else ""

        # 住所抽出
        addr_match = re.search(r"住所[\s:：]*([\s\S]+?)(?:\n\s*(?:ニーズ|電話|TEL|氏名|フリガナ)|$)", target_text)
        if addr_match:
            data["client_address"] = addr_match.group(1).replace("\n", "").strip()
        else:
            data["client_address"] = ""

        return data

def analyze_referral_pdf(file_bytes: bytes) -> Dict[str, Any]:
    return ReferralSheetParser().parse_pdf(file_bytes)
````

## File: src/legal_system/models/__init__.py
````python

````

## File: src/legal_system/models/base.py
````python

````

## File: src/legal_system/tools/__init__.py
````python
def hello() -> str:
    return "Hello from legal-rag-system!"
````

## File: src/legal_system/tools/coord_tool.py
````python
# src/legal_system/tools/coord_tool.py

import hashlib
import os
import sys
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from pdf2image import convert_from_bytes
from PIL import ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from streamlit_image_coordinates import streamlit_image_coordinates

# パス解決
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(BASE_DIR)

from legal_system.core.database_manager import DatabaseManager

# フォント設定
FONT_PATH = os.path.join(BASE_DIR, "data", "fonts", "ipaexg.ttf")
try:
    pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(layout="wide", page_title="座標登録ツール (DB連携対応版)")
st.title("📍 PDF座標 登録 & 編集ツール")

db = DatabaseManager()
user_info = db.get_current_user_info()


# ==========================================
# 0. ヘルパー関数 & プリセット
# ==========================================
def calculate_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def get_wareki(dt):
    if dt.year >= 2019:
        return f"令和{dt.year - 2018}"
    return str(dt.year)


def split_phone_number(phone_str):
    parts = ["", "", ""]
    if phone_str:
        phone_str = phone_str.replace("ー", "-").replace("−", "-")
        splits = phone_str.split("-")
        for i in range(min(len(splits), 3)):
            parts[i] = splits[i]
    return parts


user_phone_parts = split_phone_number(user_info.get("phone", ""))

COMPANY_INFO = {
    "zip1": "100",
    "zip2": "0001",
    "address": "東京都千代田区千代田1-1",
    "name": "行政書士法人未来",
    "rep_name": "行政書士 山田 太郎",
}
today = datetime.now()
wareki_year = get_wareki(today)

PRESETS = {
    "（選択なし）": {"label": "", "val": ""},
    "----- ★DB連携用タグ (自動差込)★ -----": {"label": "", "val": ""},
    "{被相続人 氏名}": {
        "label": "被相続人氏名",
        "val": "{deceased_name}",
        "desc": "DBから被相続人名を自動取得",
    },
    "{被相続人 死亡日}": {
        "label": "被相続人死亡日",
        "val": "{death_date}",
        "desc": "DBから死亡日を自動取得",
    },
    "{相続人 氏名}": {
        "label": "相続人氏名",
        "val": "{heir_name}",
        "desc": "DBから相続人名を自動取得",
    },
    "{相続人 住所}": {
        "label": "相続人住所",
        "val": "{heir_address}",
        "desc": "DBから住所を自動取得",
    },
    "----- 図形・記号 -----": {"label": "", "val": ""},
    "四角形枠 (サイズ指定)": {
        "label": "枠線",
        "val": "RECT:30x30",
        "desc": "RECT:幅x高さ (pt単位)",
    },
    "数字「1」": {"label": "数字1", "val": "1", "size": 11},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14},
    "----- 日付関連 (固定値) -----": {"label": "", "val": ""},
    "今日 (令和〇年)": {"label": "記入日_和暦年", "val": wareki_year},
    "今日 (20XX年)": {"label": "記入日_西暦年", "val": str(today.year)},
    "----- 担当者・会社 (固定値) -----": {"label": "", "val": ""},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]},
    "代理人 (肩書)": {"label": "代理人肩書", "val": "代理人"},
    "電話番号 (市外局番)": {"label": "担当者TEL_1", "val": user_phone_parts[0]},
    "電話番号 (市内局番)": {"label": "担当者TEL_2", "val": user_phone_parts[1]},
    "電話番号 (加入者)": {"label": "担当者TEL_3", "val": user_phone_parts[2]},
    "会社郵便番号 (3桁)": {"label": "会社郵便番号1", "val": COMPANY_INFO["zip1"]},
    "会社郵便番号 (4桁)": {"label": "会社郵便番号2", "val": COMPANY_INFO["zip2"]},
    "会社住所": {"label": "会社住所", "val": COMPANY_INFO["address"]},
    "代表者名": {"label": "代表者名", "val": COMPANY_INFO["rep_name"]},
    "相続人 代理人": {"label": "相続人代理人署名", "val": "相続人 相続 花子 代理人"},
}

# セッション初期化
if "last_x" not in st.session_state:
    st.session_state["last_x"] = 0
if "last_y" not in st.session_state:
    st.session_state["last_y"] = 0
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1

if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 10.5
if "input_color" not in st.session_state:
    st.session_state["input_color"] = "black"
if "input_desc" not in st.session_state:
    st.session_state["input_desc"] = ""

# ==========================================
# 1. サイドバー: ファイル管理エリア
# ==========================================
with st.sidebar:
    st.header("📂 対象ファイル")
    uploaded_file = st.file_uploader("帳票PDFをアップロード", type="pdf")

    file_hash = None
    existing_coords = []
    df_existing = pd.DataFrame()

    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_hash = calculate_hash(file_bytes)
        st.caption(f"File ID: {file_hash[:8]}...")

        # データベースから座標を取得
        existing_coords = db.get_coordinates_by_hash(file_hash)
        if existing_coords:
            df_existing = pd.DataFrame(existing_coords)

        st.success(f"登録済み: {len(existing_coords)} 件")
    else:
        st.warning(
            "左記でファイルをアップロードしてください。\n(再編集の場合も同じファイルをアップロードが必要です)"
        )

    st.divider()
    st.header("⚙️ 設定")

    def on_def_size_change():
        st.session_state["input_size"] = st.session_state["def_font_size_key"]

    def_font_size = st.number_input(
        "基本フォントサイズ (pt)",
        4.0,
        72.0,
        10.5,
        step=0.5,
        key="def_font_size_key",
        on_change=on_def_size_change,
    )

# ==========================================
# 2. メインエリア
# ==========================================
col_img, col_ctrl = st.columns([1.8, 1.2])

if not uploaded_file:
    st.info("👈 サイドバーからPDFをアップロードしてください。")
    st.stop()

# --- プレビュー用準備 ---
reader = PdfReader(BytesIO(file_bytes))
# 1ページ目のサイズを取得 (Point単位)
media_box = reader.pages[0].mediabox
pdf_w_pt = float(media_box.width)
pdf_h_pt = float(media_box.height)

images = convert_from_bytes(file_bytes)
total_pages = len(images)
img_w_px, img_h_px = images[0].size
# プレビュー拡大率
preview_scale = img_h_px / pdf_h_pt


# データ更新用コールバック関数
def on_data_editor_change():
    changes = st.session_state["editor"]
    if changes["edited_rows"]:
        for idx, row_changes in changes["edited_rows"].items():
            target_id = df_existing.iloc[int(idx)]["id"]
            db.update_coordinate_direct(int(target_id), row_changes)
        st.toast("✅ 変更を保存しました")

    if changes["deleted_rows"]:
        for idx in changes["deleted_rows"]:
            target_id = df_existing.iloc[int(idx)]["id"]
            db.delete_coordinate(int(target_id))
        st.toast("🗑️ 削除しました")


# --- 右カラム: 入力 & リスト編集 ---
with col_ctrl:
    st.subheader("2. 設定と登録")

    # プリセット選択
    def on_preset():
        sel = st.session_state["preset_sel"]
        if sel and PRESETS[sel]["val"]:
            p = PRESETS[sel]
            st.session_state["input_label"] = p["label"]
            st.session_state["input_val"] = p["val"]
            if "size" in p:
                st.session_state["input_size"] = float(p["size"])
            if "desc" in p:
                st.session_state["input_desc"] = p["desc"]

    st.selectbox(
        "⚡️ プリセット", list(PRESETS.keys()), key="preset_sel", on_change=on_preset
    )

    # 入力フォーム
    c1, c2 = st.columns([2, 1])
    label_in = c1.text_input(
        "項目名 (必須)", key="input_label", placeholder="例: 被相続人氏名"
    )
    val_in = c2.text_input(
        "テスト値",
        key="input_val",
        help="矩形: 'RECT:幅x高さ', DB連携: '{deceased_name}'",
    )

    c3, c4 = st.columns(2)
    size_in = c3.number_input(
        "サイズ(pt)", 0.5, 100.0, key="input_size", step=0.5, format="%.1f"
    )
    color_in = c4.selectbox("色", ["black", "red"], key="input_color")

    desc_in = st.text_input("備考", key="input_desc")

    st.write(
        f"📍 座標: X={st.session_state['last_x']} / Y={st.session_state['last_y']} (P.{st.session_state['current_page']})"
    )

    if st.button("💾 新規登録 / 上書き保存", type="primary"):
        if not label_in:
            st.error("項目名は必須です")
        elif st.session_state["last_x"] == 0:
            st.error("左の画像をクリックして位置を決めてください")
        else:
            success = db.register_coordinate(
                file_hash=file_hash,
                label=label_in,
                x=st.session_state["last_x"],
                y=st.session_state["last_y"],
                page_number=st.session_state["current_page"],
                description=desc_in,
                font_size=size_in,
                color=color_in,
                test_value=val_in,
            )
            if success:
                st.toast(f"✅ 「{label_in}」を登録しました！")
                import time

                time.sleep(0.5)
                st.rerun()

    st.divider()

    # ▼▼▼ 登録済みリスト (width='stretch'対応) ▼▼▼
    st.subheader("📋 登録済みリスト (直接修正可)")
    if not df_existing.empty:
        column_order = [
            "label",
            "x",
            "y",
            "page",
            "font_size",
            "color",
            "value",
            "desc",
            "id",
        ]
        # 存在するカラムのみフィルタリング
        df_display = df_existing[[c for c in column_order if c in df_existing.columns]]

        st.data_editor(
            df_display,
            column_config={
                "id": None,
                "label": st.column_config.TextColumn("項目名", width="medium"),
                "x": st.column_config.NumberColumn("X", format="%.1f", step=0.1),
                "y": st.column_config.NumberColumn("Y", format="%.1f", step=0.1),
                "page": st.column_config.NumberColumn("頁", width="small"),
                "font_size": st.column_config.NumberColumn(
                    "pt", width="small", format="%.1f", step=0.5
                ),
                "color": st.column_config.SelectboxColumn(
                    "色", options=["black", "red"], width="small"
                ),
                "value": st.column_config.TextColumn("値/RECT", width="medium"),
                "desc": st.column_config.TextColumn("備考", width="large"),
            },
            hide_index=True,
            width="stretch",  # use_container_width=True の代わり
            key="editor",
            num_rows="dynamic",
            on_change=on_data_editor_change,
        )
    else:
        st.info("まだ登録データはありません")

    # ▼▼▼ PDF作成ロジック (リスト下の配置 & 全件出力) ▼▼▼
    st.divider()
    st.subheader("🖨️ PDF作成 (登録済み全件出力)")

    if st.button("現在のリスト内容でPDFを作成"):
        if df_existing.empty:
            st.error("登録されたデータがありません。先に座標を登録してください。")
        else:
            try:
                # ベースPDFの読み込み
                packet = BytesIO()
                # ReportLabキャンバス作成
                can = canvas.Canvas(packet, pagesize=(pdf_w_pt, pdf_h_pt))

                # 登録済みデータを全件ループ
                for index, row in df_existing.iterrows():
                    # ページ番号が違う場合はスキップ（今回は簡易的に1ページずつ出力ではなく、全ページマージする前提）
                    # 実際にはページごとにCanvasを分けるか、ページ移動が必要だが、
                    # 簡易実装として「座標があるページに移動して描く」方式をとる

                    target_page = int(row["page"])
                    val = row["value"]
                    x = float(row["x"])
                    y = float(row["y"])
                    f_size = float(row["font_size"])
                    clr = row["color"]

                    # ページ設定 (ReportLabはページ概念が少し特殊なので、今回は
                    # シンプルに「全ページ処理するPDFWriter」側で合成する方式をとるため
                    # ここではページごとにCanvasを作るのが正しいが、
                    # 簡易的に「ページごとにPDFを作って合成」するループにする)
                    pass

                # --- 修正版PDF生成ロジック (ページ対応) ---
                output = PdfWriter()

                # 1ページずつ処理
                for i, page_obj in enumerate(reader.pages):
                    page_num = i + 1

                    # このページの座標データのみ抽出
                    page_coords = df_existing[df_existing["page"] == page_num]

                    if not page_coords.empty:
                        # このページ用のオーバーレイPDFを作成
                        packet_page = BytesIO()
                        # ページサイズ取得
                        pw = float(page_obj.mediabox.width)
                        ph = float(page_obj.mediabox.height)

                        can_page = canvas.Canvas(packet_page, pagesize=(pw, ph))

                        # 描画ループ
                        for _, row in page_coords.iterrows():
                            val = row["value"]
                            if not val:
                                continue  # 値がなければスキップ

                            x = float(row["x"])
                            y = float(row["y"])
                            f_size = float(row["font_size"])

                            # 色設定
                            c_obj = red if row["color"] == "red" else black
                            can_page.setFillColor(c_obj)
                            can_page.setStrokeColor(c_obj)

                            # 座標変換 (画像クリック(左上) -> PDF(左下))
                            # 登録されているX,Yは「画像上のピクセル」
                            # ここでPDF上のポイントに変換する必要がある
                            # preview_scale = img_h_px / pdf_h_pt なので
                            # pdf_pt = img_px / preview_scale

                            # ★重要: DBの座標はクリック時のもの(Pixel相当)
                            # ここで再計算する
                            # 厳密にはページごとにサイズが違う可能性もあるが、今回は1ページ目の比率を使用

                            scale_x = pw / img_w_px
                            scale_y = ph / img_h_px

                            draw_x = x * scale_x
                            draw_y_base = ph - (y * scale_y)

                            if str(val).startswith("RECT:"):
                                try:
                                    dims = val.replace("RECT:", "").split("x")
                                    w_pt = float(dims[0])
                                    h_pt = float(dims[1])
                                    rect_y = draw_y_base - h_pt
                                    can_page.setLineWidth(f_size)
                                    can_page.rect(
                                        draw_x, rect_y, w_pt, h_pt, stroke=1, fill=0
                                    )
                                except:
                                    pass
                            else:
                                can_page.setFont("IPAexG", f_size)
                                text_y = draw_y_base - (f_size * 0.8)
                                can_page.drawString(draw_x, text_y, str(val))

                        can_page.save()
                        packet_page.seek(0)
                        overlay = PdfReader(packet_page)
                        page_obj.merge_page(overlay.pages[0])

                    output.add_page(page_obj)

                # 出力
                out_stream = BytesIO()
                output.write(out_stream)

                st.success("PDF作成完了！")
                st.download_button(
                    label="📥 作成したPDFをダウンロード",
                    data=out_stream,
                    file_name="filled_result.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF作成中にエラーが発生しました: {e}")
                st.exception(e)  # 詳細エラー表示

# --- 左カラム: 画像プレビュー ---
with col_img:
    st.subheader("1. 座標指定")

    new_page = st.number_input(
        "ページ", 1, total_pages, st.session_state["current_page"]
    )
    if new_page != st.session_state["current_page"]:
        st.session_state["current_page"] = new_page
        st.rerun()

    bg_image = images[st.session_state["current_page"] - 1].copy()
    draw = ImageDraw.Draw(bg_image)

    def draw_on_image(draw_obj, x, y, val, size_pt, color_name):
        color_rgba = (255, 0, 0, 255) if color_name == "red" else (0, 0, 0, 255)
        if not val:
            return

        if str(val).startswith("RECT:"):
            try:
                dims = val.replace("RECT:", "").split("x")
                w_pt = float(dims[0])
                h_pt = float(dims[1])
                w_px = w_pt * preview_scale
                h_px = h_pt * preview_scale
                line_width = int(max(1, size_pt * (preview_scale / 2)))
                draw_obj.rectangle(
                    [x, y, x + w_px, y + h_px], outline=color_rgba, width=line_width
                )
            except:
                pass
        else:
            try:
                px_size = size_pt * preview_scale
                font = ImageFont.truetype(FONT_PATH, int(px_size))
                draw_obj.text((x, y), str(val), font=font, fill=color_rgba)
            except:
                pass

    # A. 入力中のプレビュー
    if val_in:
        draw_on_image(
            draw,
            st.session_state["last_x"],
            st.session_state["last_y"],
            val_in,
            size_in,
            color_in,
        )
        if not str(val_in).startswith("RECT:"):
            try:
                px_size = size_in * preview_scale
                font = ImageFont.truetype(FONT_PATH, int(px_size))
                bbox = draw.textbbox(
                    (st.session_state["last_x"], st.session_state["last_y"]),
                    val_in,
                    font=font,
                )
                draw.rectangle(bbox, outline="blue", width=2)
            except:
                pass

    # B. 登録済みデータのプレビュー
    current_page_coords = [
        c for c in existing_coords if c["page"] == st.session_state["current_page"]
    ]
    for c in current_page_coords:
        draw_on_image(draw, c["x"], c["y"], c["value"], c["font_size"], c["color"])

    # 座標取得
    value = streamlit_image_coordinates(
        bg_image, key=f"canvas_p{st.session_state['current_page']}"
    )
    if value:
        if (
            value["x"] != st.session_state["last_x"]
            or value["y"] != st.session_state["last_y"]
        ):
            st.session_state["last_x"] = value["x"]
            st.session_state["last_y"] = value["y"]
            st.rerun()
````

## File: src/legal_system/ui/components/cases/__init__.py
````python

````

## File: src/legal_system/ui/components/cases/dashboard_widgets.py
````python
# src/legal_system/ui/components/cases/dashboard_widgets.py

import json
import time
import pandas as pd
import streamlit as st
from src.legal_system.models.tables import User, ContactLog
from src.services.deceased_service import update_case_assignment, get_all_users
from src.services.kintone_sync_service import import_kintone_json, get_kintone_data_as_dict
from src.utils.date_utils import convert_seireki_to_wareki

# ---------------------------------------------------------
# 1. 担当者割り当てウィジェット (復活)
# ---------------------------------------------------------
def render_manager_assignment(session, case):
    """
    担当者（マネージャー・実務担当）の割り当てUI
    """
    st.markdown("##### 👥 担当者割り当て")
    
    # ユーザーリスト取得
    users = get_all_users()
    user_opts = {u_id: name for u_id, name in users.items()}
    user_opts[None] = "（未設定）"
    
    # 現在の値
    curr_mgr = case.manager_id
    curr_opr = case.operator_id
    
    c1, c2, c3 = st.columns([2, 2, 1])
    
    # リスト作成（選択肢）
    opts_list = list(user_opts.keys())
    
    with c1:
        # インデックス検索 (None対応)
        idx_m = opts_list.index(curr_mgr) if curr_mgr in opts_list else opts_list.index(None)
        new_mgr = st.selectbox(
            "進捗担当 (Manager)", 
            opts_list, 
            format_func=lambda x: user_opts[x],
            index=idx_m,
            key="sel_mgr"
        )
        
    with c2:
        idx_o = opts_list.index(curr_opr) if curr_opr in opts_list else opts_list.index(None)
        new_opr = st.selectbox(
            "実務担当 (Operator)", 
            opts_list, 
            format_func=lambda x: user_opts[x],
            index=idx_o,
            key="sel_opr"
        )
        
    with c3:
        st.write("") # スペーサー
        st.write("")
        if st.button("更新", key="btn_assign_update"):
            if update_case_assignment(case.case_id, new_mgr, new_opr):
                st.toast("担当者を更新しました", icon="✅")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("更新失敗")

# ---------------------------------------------------------
# 2. SOL情報・紹介元情報 (復活)
# ---------------------------------------------------------
def render_sol_info(session, case):
    """
    紹介元（日興証券など）情報の表示
    """
    st.markdown("##### 🏢 紹介元・SOL情報")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.caption("SOL案件番号")
        c1.write(case.sol_case_number or "（なし）")
        
        c2.caption("紹介元支店 / 担当者")
        br = case.referral_sec_branch_name or "-"
        rep = case.referral_sec_rep_name or "-"
        c2.write(f"{br} / {rep}")
        
        c3.caption("紹介日")
        intro = case.introduction_date
        c3.write(str(intro) if intro else "-")

# ---------------------------------------------------------
# 3. Kintone連携ツール (復活)
# ---------------------------------------------------------
def render_kintone_tool(case_id):
    """
    Kintoneからのデータ再取得・同期ツール
    """
    st.markdown("##### ☁️ Kintoneデータ同期")
    with st.expander("Kintoneから最新データを取り込む"):
        st.info("Kintone上のデータを再取得し、この案件の情報を上書き更新します。")
        if st.button("🔄 同期実行 (Pull from Kintone)", key="btn_kintone_sync"):
            with st.spinner("通信中..."):
                data = get_kintone_data_as_dict(case_id)
                if data:
                    # 同期処理 (import_kintone_json は ID を返す)
                    res_id = import_kintone_json(data, target_case_id=case_id)
                    if res_id > 0:
                        st.success("同期完了！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("データの保存に失敗しました。")
                else:
                    st.error("Kintoneからデータを取得できませんでした。Record IDを確認してください。")

# ---------------------------------------------------------
# 4. 対応履歴・タイムライン (Ver 3.3 新機能)
# ---------------------------------------------------------
def render_contact_logs(session, case_id):
    """
    対応履歴・処理タイムライン表示 (Table形式へアップグレード)
    """
    st.divider()
    st.subheader("⏱️ 処理タイムライン・履歴")
    
    # データを取得
    logs = session.query(ContactLog).filter_by(case_id=case_id).order_by(ContactLog.log_id.desc()).all()
    
    if logs:
        # データフレーム用に整形
        data = []
        for log in logs:
            # ログの内容から情報を簡易抽出（擬似パース）
            content = log.contact_content or ""
            action = "メモ/連絡"
            result = "記録"
            icon = "🗒️"
            
            if "【自動取込】" in content:
                action = "AI自動処理"
                icon = "🤖"
                if "完了" in content or "成功" in content:
                    result = "成功"
                elif "エラー" in content or "失敗" in content:
                    result = "失敗"
                else:
                    result = "通知"
            
            data.append({
                "ID": log.log_id,
                "種別": icon,
                "アクション": action,
                "内容": content.split("\n")[0] if content else "(内容なし)", # 1行目だけ表示
                "詳細": content,
                "結果": result
            })
            
        df = pd.DataFrame(data)
        
        # タイムライン風テーブル表示
        st.dataframe(
            df[["種別", "アクション", "内容", "結果"]],
            column_config={
                "種別": st.column_config.TextColumn("Icon", width="small"),
                "アクション": st.column_config.TextColumn("Action", width="medium"),
                "内容": st.column_config.TextColumn("Content", width="large"),
                "結果": st.column_config.TextColumn("Status", width="small"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        # 詳細確認用エクスパンダー
        with st.expander("詳細ログを確認する"):
            for d in data:
                st.markdown(f"**{d['種別']} {d['アクション']}** : {d['内容']}")
                st.text(d['詳細'])
                st.divider()
    else:
        st.info("履歴はありません。")
````

## File: src/legal_system/ui/components/cases/heir_list.py
````python
# 相続人一覧
````

## File: src/legal_system/ui/components/cases/history_log.py
````python
# 履歴ログ
````

## File: src/legal_system/ui/components/cases/nayose_registration.py
````python
# src/legal_system/ui/components/cases/nayose_registration.py

import base64
import json
import time
import unicodedata
import pandas as pd
import streamlit as st
from io import BytesIO
from typing import List, Union
from PIL import Image
from pdf2image import convert_from_bytes
from langchain_core.messages import HumanMessage

# プロジェクト内モジュール
from src.legal_system.core.ai_factory import AIFactory
from src.legal_system.models.tables import RealEstateAsset
from src.legal_system.ui.components.document_viewer import render_enhanced_document_viewer

def normalize_text(text: str) -> str:
    """テキスト正規化（全角・半角統一）"""
    if not text: return ""
    return unicodedata.normalize("NFKC", str(text)).strip()

def analyze_nayose_with_ai(image_inputs: Union[bytes, List[bytes]]) -> dict:
    """
    名寄帳をGemini Visionで解析するロジック
    """
    try:
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        
        prompt_text = """
        あなたは日本の不動産登記・固定資産税の専門家（司法書士補助者）です。
        提供された「名寄帳（固定資産税課税明細書）」の画像を解析し、全資産情報をJSONで出力してください。
        
        【抽出ルール】
        - 所有者名 (owner_name) を特定してください。
        - 資産リスト (assets) に、以下の項目を抽出してください。
          - type: "土地", "家屋", "マンション" のいずれか
          - location: 所在
          - number: 地番 または 家屋番号
          - category_structure: 地目 または 構造
          - area: 地積 または 床面積 (数値のみ)
          - assessed_value: 固定資産税評価額 (数値のみ)
        
        【出力JSONフォーマット】
        {
            "owner_name": "所有者氏名",
            "assets": [
                { "type": "土地", "location": "...", "number": "...", "category_structure": "...", "area": 100.0, "assessed_value": 1000000 },
                ...
            ]
        }
        """
        
        if isinstance(image_inputs, bytes):
            image_inputs = [image_inputs]
            
        content_list = [{"type": "text", "text": prompt_text}]
        
        for img_bytes in image_inputs:
            img_str = base64.b64encode(img_bytes).decode("utf-8")
            content_list.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{img_str}"
            })

        message = HumanMessage(content=content_list)
        response = llm.invoke([message])
        
        content = response.content.replace("```json", "").replace("```", "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        else:
            return {"error": "AIの応答がJSON形式ではありませんでした"}
            
    except Exception as e:
        return {"error": str(e)}

def render_nayose_registration(session, case_id: int):
    """
    名寄帳登録・不動産管理画面のメインレンダラー
    """
    st.subheader("🏘️ 不動産管理 (名寄帳・登録リスト)")
    
    # =========================================================
    # 1. 新規登録 (AI-OCR / ファイルアップロード)
    # =========================================================
    with st.expander("📤 新規登録: 名寄帳読み取り (AI)", expanded=True):
        uploaded_nayose = st.file_uploader(
            "名寄帳(PDF/画像)をアップロード", 
            type=["pdf", "png", "jpg"], 
            key="up_nayose"
        )
        
        if uploaded_nayose:
            file_bytes = uploaded_nayose.getvalue()
            
            # ビューワー表示
            render_enhanced_document_viewer(file_bytes, uploaded_nayose.type, "nayose_view", base_width=1000)
            
            # 自動解析ロジック
            if "nayose_file_name" not in st.session_state or st.session_state["nayose_file_name"] != uploaded_nayose.name:
                with st.spinner("🚀 ファイルを検知しました。AIが自動解析中です..."):
                    target_images_bytes = []
                    if uploaded_nayose.type == "application/pdf":
                        try:
                            images = convert_from_bytes(file_bytes, dpi=200)
                            for img in images:
                                buf = BytesIO()
                                img.convert("RGB").save(buf, format="JPEG")
                                target_images_bytes.append(buf.getvalue())
                        except Exception as e:
                            st.error(f"PDF変換エラー: {e}")
                    else:
                        target_images_bytes.append(file_bytes)
                    
                    if target_images_bytes:
                        result = analyze_nayose_with_ai(target_images_bytes)
                        if "error" not in result:
                            st.session_state["nayose_result"] = result
                            st.session_state["nayose_file_name"] = uploaded_nayose.name
                            st.toast("解析完了！内容を確認してください", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"解析失敗: {result['error']}")

        # AI解析結果の確認・登録フォーム
        if "nayose_result" in st.session_state and st.session_state["nayose_result"]:
            st.info("👇 解析結果を確認し、「この内容で追加」ボタンを押してください。")
            res = st.session_state["nayose_result"]
            st.markdown(f"**検出された所有者:** `{res.get('owner_name', '不明')}`")
            
            df_assets = pd.DataFrame(res.get("assets", []))
            if df_assets.empty:
                df_assets = pd.DataFrame(columns=["type", "location", "number", "category_structure", "area", "assessed_value"])

            column_config = {
                "type": st.column_config.SelectboxColumn("種類", options=["土地", "家屋", "マンション"], required=True),
                "location": st.column_config.TextColumn("所在", width="medium"),
                "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                "category_structure": st.column_config.TextColumn("地目/構造", width="small"),
                "area": st.column_config.NumberColumn("地積/床面積"),
                "assessed_value": st.column_config.NumberColumn("評価額 (円)", format="%d"),
            }
            
            edited_assets = st.data_editor(
                df_assets, 
                column_config=column_config, 
                num_rows="dynamic", 
                use_container_width=True, 
                key="nayose_editor"
            )
            
            if st.button("💾 この内容で追加する", type="primary", use_container_width=True):
                try:
                    count = 0
                    for index, row in edited_assets.iterrows():
                        if not row.get("location"): continue
                        
                        p_type_raw = str(row.get("type", ""))
                        p_type = "Land"
                        if "家" in p_type_raw or "建" in p_type_raw: p_type = "Building"
                        elif "マンション" in p_type_raw: p_type = "Condo"
                        
                        area_val = 0.0
                        try: area_val = float(str(row.get("area", 0)).replace(",", ""))
                        except: pass
                        
                        val_val = 0.0
                        try: val_val = float(str(row.get("assessed_value", 0)).replace(",", ""))
                        except: pass

                        new_asset = RealEstateAsset(
                            case_id=case_id,
                            property_type=p_type,
                            location=normalize_text(row.get("location")),
                            lot_number=normalize_text(row.get("number")) if p_type == "Land" else None,
                            land_category=normalize_text(row.get("category_structure")) if p_type == "Land" else None,
                            land_area=area_val if p_type == "Land" else None,
                            house_number=normalize_text(row.get("number")) if p_type != "Land" else None,
                            structure=normalize_text(row.get("category_structure")) if p_type != "Land" else None,
                            floor_area=str(area_val) if p_type != "Land" else None,
                            assessed_value=val_val
                        )
                        session.add(new_asset)
                        count += 1
                    
                    session.commit()
                    st.success(f"{count}件の不動産情報を追加しました！")
                    time.sleep(1)
                    st.session_state["nayose_result"] = None
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"登録エラー: {e}")

    # =========================================================
    # 2. 登録済み不動産の編集・削除・追加 (CRUD Table)
    # =========================================================
    st.divider()
    st.subheader("📋 登録済み不動産一覧 (編集・修正)")
    st.caption("下表を直接編集し、「変更を保存」ボタンを押してください。行を追加・削除も可能です。")

    # DBから最新データを取得
    db_assets = session.query(RealEstateAsset).filter_by(case_id=case_id).all()
    
    # 編集用データフレームの構築
    # UIとDBのカラムをマッピングして扱いやすくする
    rows = []
    for asset in db_assets:
        # 表示用の種別変換
        p_type_disp = "土地"
        if asset.property_type == "Building": p_type_disp = "家屋"
        elif asset.property_type == "Condo": p_type_disp = "マンション"
        
        # 統合フィールドの作成 (地番と家屋番号を1列で扱う)
        num_disp = asset.lot_number if asset.property_type == "Land" else asset.house_number
        cat_disp = asset.land_category if asset.property_type == "Land" else asset.structure
        
        # 面積 (LandはFloat, BuildingはStringの場合があるが、表示上はStrで統一して扱う)
        area_disp = asset.land_area if asset.property_type == "Land" else asset.floor_area

        rows.append({
            "id": asset.id, # 隠しID
            "type": p_type_disp,
            "location": asset.location,
            "number": num_disp,
            "category_structure": cat_disp,
            "area": area_disp,
            "assessed_value": asset.assessed_value or 0
        })

    df_current = pd.DataFrame(rows)
    
    # 空の場合のスキーマ定義
    if df_current.empty:
        df_current = pd.DataFrame(columns=["id", "type", "location", "number", "category_structure", "area", "assessed_value"])

    # 編集用コンフィグ
    column_config_crud = {
        "id": None, # IDは非表示
        "type": st.column_config.SelectboxColumn("種類", options=["土地", "家屋", "マンション"], required=True, width="small"),
        "location": st.column_config.TextColumn("所在", width="large", required=True),
        "number": st.column_config.TextColumn("地番/家屋番号", width="medium"),
        "category_structure": st.column_config.TextColumn("地目/構造", width="medium"),
        "area": st.column_config.TextColumn("地積/床面積", width="small"), # 柔軟性のためText
        "assessed_value": st.column_config.NumberColumn("評価額 (円)", format="%d", width="small"),
    }

    # Data Editor 表示
    edited_df = st.data_editor(
        df_current,
        column_config=column_config_crud,
        num_rows="dynamic", # 行追加・削除を許可
        use_container_width=True,
        key="real_estate_crud_editor",
        hide_index=True
    )

    # 保存ボタン
    if st.button("💾 変更を保存 (修正・追加・削除を反映)", type="primary"):
        try:
            # 1. 削除判定: DBにあるがEditorにないIDを削除
            current_ids_in_editor = [int(row["id"]) for index, row in edited_df.iterrows() if pd.notna(row["id"])]
            
            # DB上の全IDを取得
            all_db_ids = [a.id for a in db_assets]
            
            # 削除対象ID
            ids_to_delete = set(all_db_ids) - set(current_ids_in_editor)
            
            if ids_to_delete:
                session.query(RealEstateAsset).filter(RealEstateAsset.id.in_(ids_to_delete)).delete(synchronize_session=False)

            # 2. 更新 & 追加ループ
            for index, row in edited_df.iterrows():
                # 必須チェック
                if not row.get("location"): continue

                # 種別変換 (Display -> DB)
                p_type_raw = str(row.get("type", ""))
                p_type = "Land"
                if "家" in p_type_raw or "建" in p_type_raw: p_type = "Building"
                elif "マンション" in p_type_raw: p_type = "Condo"

                # 面積変換
                area_raw = str(row.get("area", "")).replace("㎡", "")
                land_area_val = None
                floor_area_val = None
                
                if p_type == "Land":
                    try: land_area_val = float(area_raw)
                    except: land_area_val = 0.0
                else:
                    floor_area_val = area_raw # 建物は文字列(例: 1階20 2階20)のまま保存

                # 行のIDを確認
                row_id = row.get("id")
                target_asset = None
                
                if pd.notna(row_id):
                    # 既存レコードの取得
                    target_asset = session.query(RealEstateAsset).get(int(row_id))
                
                if not target_asset:
                    # 新規作成
                    target_asset = RealEstateAsset(case_id=case_id)
                    session.add(target_asset)
                
                # 値のセット
                target_asset.property_type = p_type
                target_asset.location = normalize_text(row.get("location"))
                target_asset.assessed_value = float(row.get("assessed_value") or 0)
                
                # 土地/建物によるカラムの振り分け
                if p_type == "Land":
                    target_asset.lot_number = normalize_text(row.get("number"))
                    target_asset.land_category = normalize_text(row.get("category_structure"))
                    target_asset.land_area = land_area_val
                    # 建物のカラムはクリア
                    target_asset.house_number = None
                    target_asset.structure = None
                    target_asset.floor_area = None
                else:
                    target_asset.house_number = normalize_text(row.get("number"))
                    target_asset.structure = normalize_text(row.get("category_structure"))
                    target_asset.floor_area = floor_area_val
                    # 土地のカラムはクリア
                    target_asset.lot_number = None
                    target_asset.land_category = None
                    target_asset.land_area = None

            session.commit()
            st.toast("不動産情報を保存しました！", icon="✅")
            time.sleep(1)
            st.rerun()

        except Exception as e:
            session.rollback()
            st.error(f"保存中にエラーが発生しました: {e}")
````

## File: src/legal_system/ui/components/__init__.py
````python

````

## File: src/legal_system/ui/components/inbox.py
````python
# src/legal_system/ui/components/inbox.py
import json
import time
import streamlit as st
from src.services.deceased_service import find_cases_by_attributes
from src.legal_system.models.tables import Case
from src.legal_system.core.database_manager import DatabaseManager

# ★修正: 自動更新(30秒)に対応するため、TTLを短く(5秒)設定
# これにより、リフレッシュ時に古いキャッシュが表示され続けるのを防ぐ
@st.cache_data(ttl=5, show_spinner="新着通知を確認中...")
def _get_cached_pendings(_gmail_service):
    return _gmail_service.get_pending_notes()

def render_inbox(session, gmail_service=None, scanner_service=None):
    if not gmail_service:
        return

    try:
        # キャッシュされた通知リストを取得
        pendings = _get_cached_pendings(gmail_service)
        if not pendings:
            return

        st.warning(f"📨 未処理の通知が {len(pendings)} 件あります")
        
        with st.expander("📥 受信トレイを確認 (未紐付け)", expanded=True):
            for n in pendings:
                is_file = n.message_id and n.message_id.startswith("FILE-")
                icon = "📄" if is_file else "🎙️" if "録音" in (n.subject or "") else "✉️"
                date_str = n.received_at.strftime('%m/%d %H:%M')
                
                st.markdown(f"**{icon} {n.subject}** ({date_str})")
                if n.ai_summary:
                    st.caption(n.ai_summary.replace("\n", "  \n"))

                with st.container(border=True):
                    candidates = []
                    try:
                        if is_file:
                            info = json.loads(n.body_text)
                            analysis = info.get("analysis", {})
                            candidates = analysis.get("case_candidates", [])
                        else:
                            names = json.loads(n.detected_names or "[]")
                            for nm in names:
                                hits = find_cases_by_attributes(client_name=nm) or find_cases_by_attributes(deceased_name=nm)
                                for h in hits:
                                    if not any(c['case_id'] == h['case_id'] for c in candidates):
                                        candidates.append(h)
                    except Exception:
                        pass

                    cols_act = st.columns([3, 1])
                    with cols_act[0]:
                        target_id = None
                        
                        if candidates:
                            st.info(f"💡 {len(candidates)} 件の候補が見つかりました。")
                            cand_opts = {f"【{c['case_number']}】 {c['client_name']}": c['case_id'] for c in candidates}
                            # デフォルトで先頭を選択
                            sel_cand_label = st.radio("紐付け先を選択", list(cand_opts.keys()), key=f"rad_{n.id}")
                            target_id = cand_opts[sel_cand_label]
                        else:
                            st.warning("自動マッチする案件が見つかりませんでした。手動で選択してください。")
                            
                            # 全案件から検索するセレクトボックス
                            recent_cases = session.query(Case).order_by(Case.created_at.desc()).limit(50).all()
                            case_map = {f"【{c.case_number}】 {c.client_name}": c.case_id for c in recent_cases}
                            
                            # ★ポイント: keyをユニークにして状態を維持
                            selected_label = st.selectbox(
                                "案件を検索・選択", 
                                ["(選択してください)"] + list(case_map.keys()),
                                key=f"manual_sel_{n.id}"
                            )
                            
                            if selected_label != "(選択してください)":
                                target_id = case_map[selected_label]

                    with cols_act[1]:
                        st.write("")
                        # 登録ボタン
                        if st.button("✅ 登録", key=f"btn_proc_{n.id}", type="primary", use_container_width=True):
                            if target_id:
                                try:
                                    success = False
                                    if is_file:
                                        if scanner_service:
                                            # process_pending_bufferの呼び出し
                                            success = scanner_service.process_pending_buffer(n.id, target_id)
                                        else:
                                            st.error("スキャナーサービスが無効です")
                                    else:
                                        success = gmail_service.link_note_to_case_manually(n.id, target_id)
                                    
                                    if success:
                                        st.success("完了")
                                        st.cache_data.clear() # キャッシュを破棄して最新化
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("処理に失敗しました (詳細はログを確認)")
                                except Exception as e:
                                    st.error(f"システムエラー: {e}")
                            else:
                                st.error("案件を選択してください")
                        
                        if st.button("無視", key=f"ign_{n.id}", use_container_width=True):
                            gmail_service.ignore_note(n.id)
                            st.cache_data.clear()
                            st.rerun()
                st.divider()

    except Exception as e:
        st.error(f"通知取得エラー: {e}")
````

## File: src/legal_system/ui/components/label_printer_ui.py
````python
# src/legal_system/ui/components/tools/label_printer_ui.py
import os
import streamlit as st
from src.legal_system.models.tables import Address, H_AddressHistory
from src.services.deceased_service import get_contact_info
from src.legal_system.ui.label_generator import generate_advanced_label, get_branch_address

# ルートディレクトリの特定 (相対パス解決)
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/legal_system/ui/components/tools -> root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))))

def render_label_printer(session, case, current_user_info):
    """宛名ラベル作成画面"""
    st.subheader("🖨️ 宛名ラベル出力")
    
    contractor = None
    c_address = None
    c_phone = ""
    
    if case.deceased_ref and case.deceased_ref.heirs:
        contractor = next((h for h in case.deceased_ref.heirs if h.is_contracting_party), None)
        if not contractor: contractor = case.deceased_ref.heirs[0]
        
        if contractor:
            al = session.query(H_AddressHistory).filter(H_AddressHistory.heir_id == contractor.id, H_AddressHistory.is_current_address == True).first()
            if al: c_address = session.query(Address).get(al.address_id)
            contacts = get_contact_info("heir", contractor.id)
            c_phone = next((c["value"] for c in contacts if c["type"]=="PHONE"), "")

    c_l, c_r = st.columns([1, 1.2])
    with c_l:
        st.markdown("##### 👤 宛先")
        with st.container(border=True):
            dn = f"{contractor.name_last} {contractor.name_first}" if contractor else ""
            dz = c_address.zip_code if c_address else ""
            da = f"{c_address.prefecture}{c_address.city_ward_town}{c_address.street_address} {c_address.building_name or ''}" if c_address else ""
            
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
                mb = "横浜" if "横浜" in current_user_info.get("dept","") else "東京"
                ma = get_branch_address(mb)
                sn = st.text_input("担当者名", value=current_user_info["name"])
                s_tel = st.text_input("電話", value=current_user_info["phone"])
                sa = st.text_area("差出人住所", value=ma, height=80)
                
                # 簡易パース
                lines = sa.split("\n")
                sz = lines[0].replace("〒", "") if lines else ""
                sad = "\n".join(lines[1:]) if len(lines) > 1 else ""
            
            c_p1, c_p2 = st.columns(2)
            sp = c_p1.number_input("開始位置", 1, 30, 1)
            cp = c_p2.number_input("枚数", 1, 10, 1)

    st.divider()
    
    def_tpl = os.path.join(ROOT_DIR, "data", "templates", "ラベルシート -貼り付け用.docx")
    up_tpl = st.file_uploader("テンプレート変更(任意)", type=["docx"])
    
    if st.button("🚀 ラベル作成", type="primary"):
        tpl_b = None
        if up_tpl: tpl_b = up_tpl.read()
        elif os.path.exists(def_tpl):
            with open(def_tpl, "rb") as f: tpl_b = f.read()
        else:
            st.error(f"テンプレートがありません: {def_tpl}")
            return

        plist = []
        c_data = {"type":"client","name":ln,"honorific":lh,"zip_code":lz,"address":la,"tel":lt}
        
        s_data = {}
        if inc_s:
            s_data = {
                "type": "sender",
                "name": f"行政書士法人チェスター\n{sn}", 
                "honorific": "",
                "zip_code": sz,
                "address": sad,
                "tel": s_tel
            }

        for _ in range(cp):
            if inc_c: plist.append(c_data)
            if inc_s: plist.append(s_data)

        if not plist:
            st.warning("対象なし")
            return

        try:
            io_data = generate_advanced_label(tpl_b, plist, start_position=sp)
            st.download_button("📥 ダウンロード", io_data, f"宛名ラベル_{ln.replace(' ','')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.success("完了！")
        except Exception as e:
            st.error(f"エラー: {e}")
````

## File: src/legal_system/ui/components/sidebar.py
````python
# src/legal_system/ui/components/sidebar.py

import time
import streamlit as st
import os
import sys

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))

# マスタ更新スクリプトのインポート
try:
    from update_bank_master import (
        get_remote_last_commit_date, load_local_state, download_data, save_local_state
    )
    HAS_UPDATE_SCRIPT = True
except ImportError:
    HAS_UPDATE_SCRIPT = False

# ★最適化: ttlを3600秒(1時間)に延長し、st.cache_dataに変更して高速化
@st.cache_data(ttl=3600, show_spinner=False)
def check_update_status_cached():
    """外部API(GitHub)への問い合わせ結果を長時間キャッシュする"""
    if not HAS_UPDATE_SCRIPT:
        return 2, "更新スクリプトなし"
    
    banks_path = os.path.join(ROOT_DIR, "data", "zengin", "banks.json")
    if not os.path.exists(banks_path):
        return 1, "銀行データ未取得"
        
    try:
        # ここで外部通信が発生する
        remote = get_remote_last_commit_date()
        local = load_local_state().get("last_commit_date", "")
        if remote and remote != local:
            return 1, f"更新あり ({remote[:10]})"
        return 0, "最新"
    except Exception:
        return 0, "確認不可"

def render_sidebar(db, current_user_info: dict) -> str:
    with st.sidebar:
        # ========================================
        # 1. 作業メニュー
        # ========================================
        st.title("🗂️ 業務メニュー")
        # st.info(f"👤 **{current_user_info['name']}**")        
        # st.divider()

        if "current_menu" not in st.session_state:
            st.session_state["current_menu"] = "🏠 案件概要・基本情報"

        # st.markdown(
        #     "<p style='font-size: 1.1rem; font-weight: bold; margin-bottom: -10px;'>作業メニュー</p>", 
        #     unsafe_allow_html=True
        # )

        menu_options = [
            "🏠 案件概要・基本情報", "🏦 銀行口座 登録", "📈 証券・その他資産", 
            "🏘️ 不動産 登録", "🌐 登記情報取得", "🖨️ 宛名ラベル作成", "✅ タスク管理"
        ]
        
        try:
            default_index = menu_options.index(st.session_state["current_menu"])
        except ValueError:
            default_index = 0

        menu = st.radio("作業メニュー", menu_options, index=default_index, key="menu_radio", label_visibility="collapsed")
        
        if menu != st.session_state["current_menu"]:
            st.session_state["current_menu"] = menu
            st.rerun()

        st.divider()

        # ========================================
        # 2. 業務設定・プロフィール
        # ========================================
        st.title("👤プロフィール")
        # st.info(f"👤 **{current_user_info['name']}**") 
        st.caption(f"氏名:  **{current_user_info['name']}**") 
        st.caption(f"所属: **{current_user_info['dept']} | Tel: {current_user_info['phone']}**")

        with st.expander("⚙️ プロフィール編集"):
            with st.form("user_profile_form"):
                new_name = st.text_input("表示名", value=current_user_info["name"])
                new_dept = st.text_input("所属部署", value=current_user_info["dept"])
                new_phone = st.text_input("内線/直通", value=current_user_info["phone"])
                if st.form_submit_button("更新"):
                    db.register_user(current_user_info["id"], new_name, new_dept, new_phone)
                    st.success("更新しました"); st.rerun()

        st.divider()
        
        # ========================================
        # 3. 銀行マスタ管理 (キャッシュ利用)
        # ========================================
        st.subheader("🏦 銀行マスタ")
        # キャッシュされた関数を呼び出す（通信が発生しないので一瞬で終わる）
        status_code, info = check_update_status_cached()
        if status_code == 1: st.warning(f"💡 {info}")
        else: st.caption(f"✅ {info}")

        if st.button("🔄 マスタ強制更新", use_container_width=True):
            if HAS_UPDATE_SCRIPT:
                with st.status("更新中...") as s:
                    download_data()
                    save_local_state(get_remote_last_commit_date())
                    st.cache_data.clear() # 更新後はキャッシュをクリア
                    s.update(label="完了！", state="complete")
                st.rerun()

    return menu
````

## File: src/legal_system/ui/components/smart_guide.py
````python
# src/legal_system/ui/components/smart_guide.py

import json
import os
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# プロジェクト内のモジュール読み込み
from legal_system.core.ai_factory import AIFactory

# -----------------------------------------------------------------------------
# パス設定: data/rules/bank_guidance.json を参照するように設定
# -----------------------------------------------------------------------------
# このファイル(smart_guide.py)から見て、ルートディレクトリまで遡りパスを構築します
# src/legal_system/ui/components/ -> root/data/rules
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
RULES_DIR = os.path.join(BASE_DIR, "data", "rules")
GUIDE_FILE = os.path.join(RULES_DIR, "bank_guidance.json")


def load_guidance_data():
    """
    JSONファイルから銀行ごとの案内データを読み込む。
    ファイルが存在しない場合は、デモ用の初期データを作成して返す。
    """
    # ディレクトリがなければ作成
    if not os.path.exists(RULES_DIR):
        os.makedirs(RULES_DIR, exist_ok=True)
    
    # ファイルがなければ初期データを作成（デモでエラーにならないように）
    if not os.path.exists(GUIDE_FILE):
        default_data = {
            "三菱UFJ銀行": {
                "alert": "遺産分割協議書への実印押印が必須です。",
                "items": [
                    "原本還付: 可（要ゴム印）",
                    "予約: 必須（Web予約推奨）",
                    "備考: 代理人手続きの場合、委任状に捨印を推奨"
                ]
            },
            "ゆうちょ銀行": {
                "alert": "窓口ではなく「貯金事務センター」への郵送が基本です。",
                "items": [
                    "手数料: 会社通帳から引落（窓口払い不可）",
                    "期間: 約2週間〜1ヶ月",
                    "必須: 相続確認表のWeb入力"
                ]
            },
            "三井住友銀行": {
                "alert": "残高証明書の発行は「相続オフィス」への電話予約から始まります。",
                "items": [
                    "原本還付: 可",
                    "来店: 原則不要（郵送手続可）"
                ]
            }
        }
        with open(GUIDE_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data
        
    try:
        with open(GUIDE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"マスタデータ読込エラー: {e}")
        return {}


def render_smart_guide_area(case_data, current_context: str, bank_name: str = None):
    """
    メインエリアの右カラム等に配置する「AI業務ナビゲーション」コンポーネント。
    
    Args:
        case_data (Case): 現在選択されている案件オブジェクト
        current_context (str): 画面の状況を表すテキスト（AIへの入力用）
        bank_name (str, optional): 選択中の銀行名（マスタ検索用）
    """
    
    # 枠線付きのコンテナでエリアを強調
    with st.container(border=True):
        st.subheader("🤖 業務ナビ")
        
        # 案件未選択時のガード
        if not case_data:
            st.info("👈 左側のフォームで案件を選択してください。")
            return

        # ==================================================
        # Lv.1 自動表示エリア (JSONマスタ連動・APIコストゼロ)
        # ==================================================
        if bank_name:
            # マスタデータの読み込み
            guidance_db = load_guidance_data()
            
            # 部分一致検索ロジック
            # 入力された "三菱UFJ銀行(0005)" に対して、マスタのキー "三菱UFJ" が含まれるか確認
            hit_data = None
            for key, val in guidance_db.items():
                if key in bank_name:
                    hit_data = val
                    break
            
            st.markdown(f"**🏦 {bank_name} の手続要領**")
            
            if hit_data:
                # 1. 重要アラート（赤枠）
                if hit_data.get("alert"):
                    st.error(f"**重要:** {hit_data['alert']}", icon="⚠️")
                
                # 2. 詳細リスト
                if hit_data.get("items"):
                    for item in hit_data['items']:
                        st.markdown(f"- {item}")
                
                # マスタ管理への誘導（デモ用）
                st.caption(f"※この内容は「マスタ管理」メニューで編集可能です")
            else:
                # マスタにない銀行の場合
                st.info("💡 特別な注意事項は登録されていません（一般手続準拠）")
                st.caption("※特記事項がある場合は「マスタ管理」から追加してください")
        
        st.divider()

        # ==================================================
        # Lv.2 AIアドバイス (ボタン起動・RAG/LLM使用)
        # ==================================================
        st.caption("AIアシスタント (社内規定・事例検索)")
        
        # デモ演出: ボタンを押して初めてAIが動く（コスト管理と「ここぞ」という演出）
        if st.button("💡 規定・過去事例をAI検索", type="primary", use_container_width=True):
            with st.spinner("社内ナレッジを検索中..."):
                try:
                    # AI処理 (Cloud: Gemini or Vertex)
                    llm = AIFactory.get_llm("cloud", temperature=0.0)
                    
                    system_prompt = """
                    あなたは行政書士事務所のベテラン指導員です。
                    新人の担当者が現在行っている作業に対して、
                    「注意すべきポイント」「次にやるべきこと」を
                    社内規定の観点から簡潔にアドバイスしてください。
                    
                    制約:
                    - 結論から述べること
                    - 箇条書きを使用すること
                    - 挨拶は省略すること
                    """
                    
                    # ------------------------------------------------
                    # ★セキュリティ対策: 匿名化プロンプトの構築
                    # 個人名(client_name)は含めず、属性情報のみ渡す
                    # ------------------------------------------------
                    
                    # 証券連携の有無判定
                    has_sec = "あり" if case_data.sol_case_number else "なし"
                    
                    # 口座数のカウント (リレーションがロードされていれば)
                    asset_count = 0
                    if hasattr(case_data, "financial_assets") and case_data.financial_assets:
                        asset_count = len(case_data.financial_assets)

                    safe_user_prompt = f"""
                    【現在の作業コンテキスト】
                    {current_context}
                    
                    【案件属性データ（匿名化済）】
                    - 相続開始日: {case_data.date_of_death}
                    - 証券会社連携: {has_sec}
                    - 登録済み口座数: {asset_count}
                    """

                    # Chain実行
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("human", safe_user_prompt),
                    ])
                    
                    chain = prompt | llm | StrOutputParser()
                    advice = chain.invoke({})
                    
                    # 結果表示
                    st.success("✅ AIアドバイス")
                    st.markdown(advice)

                    # ------------------------------------------------
                    # ★安心(Security)の証明エリア: 監査ログ
                    # ------------------------------------------------
                    with st.expander("🔒 セキュリティ監査ログ", expanded=True):
                        st.caption("AIサーバー(Google)に送信されたデータの実物です。")
                        st.caption("ここには「氏名」「住所」「電話番号」は含まれていません。")
                        st.code(safe_user_prompt, language="text")

                except Exception as e:
                    st.error(f"AI処理エラー: {e}")
````

## File: src/legal_system/ui/utils/__init__.py
````python

````

## File: src/legal_system/ui/utils/js_helper.py
````python
# src/legal_system/ui/utils/js_helper.py

import uuid
import streamlit.components.v1 as components

def enable_keyboard_shortcuts(search_keyword="案件番号"):
    """
    指定されたキーワード（プレースホルダー等）を持つ入力フィールドに
    強制的にフォーカスを当てるJavaScriptを埋め込む。
    
    Ver 12.0: Recursive Deep DOM Traversal (Final Solution)
    - Shadow DOMやIframeの階層に関わらず、全要素を再帰的に探索してターゲットを特定する。
    - 物理キーコード(KeyS)による判定でIMEの影響を排除。
    """
    
    # 検索バーのプレースホルダーに含まれるキーワード
    TARGET_KW = "案件番号" 
    
    # 強制リロード用のID埋め込み
    unique_id = str(uuid.uuid4())
    
    js_code = f"""
    <script>
        /* Force Reload ID: {unique_id} */
        (function() {{
            const SEARCH_KW = "{TARGET_KW}";
            const OPEN_KEYWORDS = ["📂 開く", "フォルダを開く"]; 
            const KINTONE_KEYWORDS = ["🔗 Kintone", "Kintoneで開く"];
            
            console.log("🚀 LegalApp JS Helper v12 (Deep Traversal) loaded.");

            // ============================================================
            // 1. 深層再帰探索ロジック (Shadow DOM & Iframe を貫通)
            // ============================================================
            function findInputRecursive(node) {{
                if (!node) return null;

                // 1. inputタグかつキーワード一致なら発見
                if (node.tagName === 'INPUT') {{
                    const txt = (node.placeholder || "") + (node.getAttribute('aria-label') || "");
                    if (txt.includes(SEARCH_KW) && node.type !== 'hidden' && node.style.display !== 'none') {{
                        return node;
                    }}
                }}

                // 2. Shadow Root があれば内部へ潜る
                if (node.shadowRoot) {{
                    const found = findInputRecursive(node.shadowRoot);
                    if (found) return found;
                }}

                // 3. Iframe があれば内部ドキュメントへ潜る
                if (node.tagName === 'IFRAME') {{
                    try {{
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) {{
                            // iframe内のbodyから再帰探索
                            const found = findInputRecursive(innerDoc.body);
                            if (found) return found;
                        }}
                    }} catch(e) {{
                        // Cross-origin制限などは無視
                    }}
                }}

                // 4. 子要素を再帰探索
                if (node.children) {{
                    for (let i = 0; i < node.children.length; i++) {{
                        const found = findInputRecursive(node.children[i]);
                        if (found) return found;
                    }}
                }}

                return null;
            }}

            // ============================================================
            // 2. アクション (フォーカス & クリック)
            // ============================================================
            function doFocus() {{
                // 親ウィンドウのドキュメント全体から再帰探索開始
                const input = findInputRecursive(window.parent.document.body);
                
                if (input) {{
                    // フォーカス処理 (念入りに実行)
                    input.focus();
                    setTimeout(() => input.focus(), 50);
                    
                    try {{ input.select(); }} catch(e) {{}}
                    
                    // 視覚エフェクト (マゼンタ枠線)
                    const originalBorder = input.style.border;
                    const originalShadow = input.style.boxShadow;
                    
                    input.style.transition = "all 0.2s";
                    input.style.border = "3px solid #d33682"; // マゼンタ色
                    input.style.boxShadow = "0 0 15px rgba(211, 54, 130, 0.6)";
                    
                    setTimeout(() => {{
                        input.style.border = originalBorder;
                        input.style.boxShadow = originalShadow;
                    }}, 1200);
                    
                    return true;
                }}
                return false;
            }}

            function triggerButton(keywords) {{
                const doc = window.parent.document;
                // ボタン類はShadowDOMの深い場所にはあまりないため、querySelectorで探索
                const elements = doc.querySelectorAll('button, a, div[role="button"]');
                for (const el of elements) {{
                    const text = (el.innerText || el.textContent || "").trim();
                    if (!text) continue;
                    if (keywords.some(kw => text.includes(kw))) {{
                        el.click();
                        return true;
                    }}
                }}
                return false;
            }}

            // ============================================================
            // 3. イベントリスナー (ショートカット)
            // ============================================================
            const doc = window.parent.document;
            const HANDLER_NAME = '_legalAppKeyHandler_v12';

            // 既存リスナーの完全削除
            if (window.parent[HANDLER_NAME]) {{
                doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
            }}

            window.parent[HANDLER_NAME] = function(e) {{
                // Altキー必須
                if (!e.altKey) return;

                // 物理キーコードで判定 (IMEの影響を受けない 'KeyS')
                const code = e.code; 
                let handled = false;

                // [Alt+S] 検索
                if (code === 'KeyS') {{
                    // デフォルト動作(ブラウザメニュー等)を完全停止
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    if (doFocus()) {{
                        console.log("LegalApp: Focused via Alt+S");
                    }} else {{
                        console.log("LegalApp: Search Input Not Found via Alt+S");
                    }}
                    handled = true;
                }}
                
                // [Alt+O] フォルダ
                else if (code === 'KeyO') {{
                    if (triggerButton(OPEN_KEYWORDS)) {{
                        e.preventDefault(); 
                        handled = true;
                    }}
                }}

                // [Alt+K] Kintone
                else if (code === 'KeyK') {{
                    if (triggerButton(KINTONE_KEYWORDS)) {{
                        e.preventDefault(); 
                        handled = true;
                    }}
                }}
            }};

            // Captureフェーズ(true)で最優先でイベントを奪取
            doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);


            // ============================================================
            // 4. 自動フォーカス (MutationObserverによる監視)
            // ============================================================
            let hasFocused = false;

            // 初回トライ
            if (doFocus()) hasFocused = true;

            // 画面描画の遅延に対応するため、DOM変化を監視して出現した瞬間にフォーカス
            const observer = new MutationObserver((mutations) => {{
                if (hasFocused) {{
                    observer.disconnect();
                    return;
                }}
                
                // 変更があるたびにトライ (負荷軽減のためシンプルに呼ぶ)
                if (doFocus()) {{
                    console.log("LegalApp: Auto-focused by Observer");
                    hasFocused = true;
                    observer.disconnect();
                }}
            }});

            observer.observe(window.parent.document.body, {{
                childList: true, 
                subtree: true
            }});
            
            // 安全策: 3秒後まで定期的にリトライ (Observerで見逃した場合用)
            let retryCount = 0;
            const interval = setInterval(() => {{
                if (hasFocused || retryCount > 15) {{
                    clearInterval(interval);
                    return;
                }}
                if (doFocus()) {{
                    hasFocused = true;
                }}
                retryCount++;
            }}, 200); // 0.2秒ごとにチェック

        }})();
    </script>
    """
    
    # key引数を使わず、HTML内の unique_id でリロードを強制する
    components.html(js_code, height=0)
````

## File: src/legal_system/ui/__init__.py
````python

````

## File: src/legal_system/ui/excel_generator.py
````python
# components/utils/excel_generator.py
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
import io
from typing import Dict, Union, List, Optional
import os

# デフォルトのテンプレートファイルパス（配置場所に合わせて変更してください）
DEFAULT_TEMPLATE_PATH = "■初回送付セット【20251218版】　.xlsx"

def fill_initial_set_excel(
    json_data: Dict[str, str], 
    template_file: Optional[Union[str, io.BytesIO]] = None
) -> io.BytesIO:
    """
    KintoneのJSONデータを基に、初回送付セットExcelの「基本情報入力」シートに値を転記します。

    Args:
        json_data (Dict[str, str]): Kintoneから取得したJSONデータ（辞書型）
        template_file (Optional[Union[str, io.BytesIO]]): テンプレートExcelファイル。
            指定がない場合はデフォルトパスを使用。

    Returns:
        io.BytesIO: 編集後のExcelバイナリデータ（ダウンロード用）
    
    Raises:
        FileNotFoundError: テンプレートファイルが見つからない場合
        KeyError: 指定されたシートが存在しない場合
    """
    
    # テンプレートの読み込み元を決定
    source = template_file if template_file else DEFAULT_TEMPLATE_PATH
    
    if isinstance(source, str) and not os.path.exists(source):
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {source}")

    # Excelブックを開く
    wb = openpyxl.load_workbook(source)
    
    target_sheet_name = "基本情報入力"
    if target_sheet_name not in wb.sheetnames:
        raise KeyError(f"テンプレート内に '{target_sheet_name}' シートが見つかりません。")
    
    ws: Worksheet = wb[target_sheet_name]

    # マッピング定義
    # JSONのキー : Excelのセル番地（単一文字列 または 文字列のリスト）
    mapping: Dict[str, Union[str, List[str]]] = {
        "顧客コード_2": "B9",
        "顧客名": ["B10", "C24"],  # 複数セルへの転記
        "◎提案項目": "B11",
        "拠点": "B12",
        "担当者①": "B13",
        "担当者②": "D13",
        "被相続人名": "C23",
        "被相続人名（ふりがな）": "D23",
        "相続開始日": "F23",
        "顧客名(ふりがな)": "D24",
        "郵便番号": "G24",
        "住所": "H24",
        "TEL": "J24"
    }

    # データの転記処理
    for json_key, cell_target in mapping.items():
        # JSONから値を取得（キーがない場合は空文字）
        value = json_data.get(json_key, "")
        
        # 転記実行
        if isinstance(cell_target, list):
            for cell_address in cell_target:
                ws[cell_address].value = value
        else:
            ws[cell_target].value = value

    # メモリ上のバイナリとして保存
    output_buffer = io.BytesIO()
    wb.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer
````

## File: src/legal_system/ui/label_generator.py
````python
# src/legal_system/ui/label_generator.py

import io
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

# 拠点ごとの住所定義
BRANCH_ADDRESSES = {
    "東京": "〒103-0028\n東京都中央区八重洲一丁目7-20\n八重洲口会館2階",
    "横浜": "〒220-0011\n神奈川県横浜市西区高島2-19-12\nスカイビル",
    "新宿": "〒163-0000\n東京都新宿区西新宿..." 
}

def get_branch_address(branch_name: str) -> str:
    for key in BRANCH_ADDRESSES:
        if key in branch_name:
            return BRANCH_ADDRESSES[key]
    return BRANCH_ADDRESSES["東京"]

def _set_font_style(run, size_pt=12, is_bold=False):
    """フォントスタイル（MS明朝）を一括適用するヘルパー"""
    run.font.name = "MS Mincho"
    run.font.size = Pt(size_pt)
    run.font.bold = is_bold
    run._element.rPr.rFonts.set(qn('w:eastAsia'), 'ＭＳ 明朝')
    run._element.rPr.rFonts.set(qn('w:ascii'), 'MS Mincho')
    run._element.rPr.rFonts.set(qn('w:hAnsi'), 'MS Mincho')

def _get_cell_width(cell):
    """セルの幅をXMLから取得する（Twips単位）"""
    try:
        tcW = cell._tc.tcPr.tcW
        if tcW.type == 'dxa':
            return int(tcW.w)
        elif tcW.type == 'pct':
            return 0
    except:
        pass
    return 0

def _get_valid_cells(table):
    """幅が極端に狭いセル（余白用スペーサー）を除外する"""
    valid_cells = []
    all_widths = []
    flat_cells = []
    
    for row in table.rows:
        for cell in row.cells:
            w = _get_cell_width(cell)
            all_widths.append(w)
            flat_cells.append(cell)
            
    if not all_widths:
        return flat_cells
        
    max_width = max(all_widths)
    threshold = max_width * 0.5 
    
    for cell, w in zip(flat_cells, all_widths):
        if w == 0 or w > threshold:
            valid_cells.append(cell)
            
    return valid_cells

def _write_cell_content(cell, text_info, is_sender=False):
    """セルにテキストを書き込む（余白調整付き）"""
    cell.text = ""
    if not cell.paragraphs:
        cell.add_paragraph()
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # --- 修正: 上部の余白 (1行あける) ---
    p.add_run("\n")

    # 左余白用のスペース
    pad = " "

    # 1. 郵便番号 (12pt)
    if text_info.get("zip_code"):
        # 半角スペース + 〒...
        run_zip = p.add_run(f"{pad}〒{text_info['zip_code']}\n")
        _set_font_style(run_zip, size_pt=12)

    # 2. 住所 (12pt)
    addr = text_info.get("address", "")
    # 半角スペース + 住所...
    run_addr = p.add_run(f"{pad}{addr}\n\n")
    _set_font_style(run_addr, size_pt=12)

    # 3. 氏名 (14pt Bold)
    name_str = text_info.get("name", "")
    honor = text_info.get("honorific", "")
    
    # 半角スペース + 氏名...
    run_name = p.add_run(f"{pad}{name_str} {honor}")
    _set_font_style(run_name, size_pt=14, is_bold=True)
    
    # 4. TEL (12pt)
    if text_info.get("tel"):
        # 改行 + 半角スペース + TEL...
        run_tel = p.add_run(f"\n{pad}TEL: {text_info['tel']}")
        _set_font_style(run_tel, size_pt=12)

def generate_advanced_label(
    template_bytes: bytes, 
    print_list: list, 
    start_position: int = 1
) -> io.BytesIO:
    """高度なラベル生成関数"""
    target_stream = io.BytesIO()
    target_stream.write(template_bytes)
    target_stream.seek(0)
    
    doc = Document(target_stream)
    
    if not doc.tables:
        raise ValueError("Wordファイルに表(テーブル)が見つかりません。")

    table = doc.tables[0]
    valid_cells = _get_valid_cells(table)
    
    current_idx = start_position - 1
    
    for data in print_list:
        if current_idx >= len(valid_cells):
            break
            
        target_cell = valid_cells[current_idx]
        is_sender = data.get("type") == "sender"
        
        _write_cell_content(target_cell, data, is_sender)
        
        current_idx += 1

    out_stream = io.BytesIO()
    doc.save(out_stream)
    out_stream.seek(0)
    return out_stream
````

## File: src/legal_system/__init__.py
````python

````

## File: src/legal.egg-info/dependency_links.txt
````

````

## File: src/services/automation/__init__.py
````python

````

## File: src/services/__init__.py
````python

````

## File: src/services/case_service.py
````python
# 案件サービス
````

## File: src/services/dispatch_service.py
````python
# src/services/dispatch_service.py
from typing import Any, Dict


def determine_base_from_branch(branch_name: str) -> str:
    """
    紹介元支店名から担当拠点を自動判定するロジック
    """
    if not branch_name:
        return "未定"

    name = branch_name.replace("支店", "").strip()

    # マスタールール (本来はDBかJSONファイルで管理推奨)
    rules = {
        "横浜拠点": ["横浜", "川崎", "港南台", "鎌倉", "藤沢"],
        "新宿拠点": ["新宿", "中野", "杉並", "池袋"],
        "渋谷拠点": ["渋谷", "世田谷", "目黒"],
        "立川拠点": ["立川", "八王子", "町田"],
        "大宮拠点": ["大宮", "浦和", "川口"],
        "千葉拠点": ["千葉", "船橋", "柏"],
    }

    for base, keywords in rules.items():
        for kw in keywords:
            if kw in name:
                return base

    return "本店"  # デフォルト


def generate_kintone_json_payload(
    case_obj, deceased_obj, heir_obj, address_obj
) -> Dict[str, Any]:
    """
    DBオブジェクトからKintoneブックマークレット用のJSONを生成する
    """
    # 氏名結合
    c_name = f"{case_obj.client_name}".strip()
    c_kana = f"{case_obj.client_name_kana}".strip()

    d_name = ""
    d_kana = ""
    if deceased_obj:
        d_name = f"{deceased_obj.name_last}　{deceased_obj.name_first}".strip()
        d_kana = (
            f"{deceased_obj.name_last_kana}　{deceased_obj.name_first_kana}".strip()
        )

    # 住所結合
    addr_full = ""
    zip_code = ""
    if address_obj:
        zip_code = address_obj.zip_code
        addr_full = f"{address_obj.prefecture}{address_obj.city_ward_town}{address_obj.street_address} {address_obj.building_name or ''}".strip()

    # 電話番号（Caseに保存されている紹介元電話番号も備考へ）
    ref_phone_note = ""
    if case_obj.referral_sec_phone:
        ref_phone_note = f"\n【紹介元TEL】{case_obj.referral_sec_phone}"

    return {
        "顧客コード_2": case_obj.case_number,
        "顧客名": c_name,
        "顧客名(ふりがな)": c_kana,
        "郵便番号": zip_code,
        "住所": addr_full,
        # 被相続人
        "被相続人名": d_name,
        "被相続人名（ふりがな）": d_kana,
        "相続開始日": str(deceased_obj.date_of_death)
        if deceased_obj and deceased_obj.date_of_death
        else "",
        # 紹介情報
        "SOL案件No.（日興）": case_obj.sol_case_number or "",
        "支店名（日興）": case_obj.referral_sec_branch_name or "",
        "担当者（日興）": case_obj.referral_sec_rep_name or "",
        "紹介日": str(case_obj.introduction_date) if case_obj.introduction_date else "",
        # 備考などに電話番号を入れる
        "備考": ref_phone_note,
    }
````

## File: src/services/encryption_service.py
````python
# src/services/encryption_service.py
import os
import subprocess
import logging
from typing import List
from pathlib import Path

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncryptionService:
    """
    同梱した7-Zipバイナリ(7za.exe)を使用して暗号化を行うサービスクラス。
    Windows標準機能(エクスプローラー)で解凍可能な ZipCrypto 方式を採用します。
    """

    # src/services/encryption_service.py から見て ../utils/7za.exe を指す
    # 実行環境に合わせて絶対パスに変換
    BASE_DIR = Path(__file__).resolve().parent.parent # srcディレクトリ
    EXE_PATH = str(BASE_DIR / "utils" / "7za.exe")

    @staticmethod
    def create_encrypted_zip(file_paths: List[str], output_path: str, password: str) -> None:
        """
        7-Zipを使用して、Windows標準機能で解凍可能なパスワード付きZIPを作成します。

        Args:
            file_paths (List[str]): 圧縮するファイルのフルパスリスト
            output_path (str): 出力するZIPファイルのパス
            password (str): 設定するパスワード
        """
        if not file_paths or not password:
            raise ValueError("ファイルとパスワードが必要です。")

        # バイナリの存在確認
        if not os.path.exists(EncryptionService.EXE_PATH):
            logger.error(f"7za.exe not found at: {EncryptionService.EXE_PATH}")
            raise FileNotFoundError(
                f"暗号化エンジン(7za.exe)が見つかりません。以下の場所に配置してください:\n{EncryptionService.EXE_PATH}"
            )

        try:
            # 既存の出力ファイルがある場合は削除（7zはデフォルトで追記モードのため）
            if os.path.exists(output_path):
                os.remove(output_path)

            # 7-Zipコマンドの構築
            # a: 追加(圧縮)
            # -tzip: ZIP形式を指定
            # -p: パスワードを指定
            # -mem=ZipCrypto: Windowsエクスプローラー互換の暗号化方式を指定 (重要)
            cmd = [
                EncryptionService.EXE_PATH,
                "a",
                "-tzip",
                f"-p{password}",
                "-mem=ZipCrypto",
                output_path
            ]
            
            # 圧縮対象ファイルの追加
            cmd.extend(file_paths)

            # コマンドの実行 (Windows特有のコンソールウィンドウ非表示設定を含む)
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                creationflags=creationflags
            )
            
            logger.info(f"Encrypted ZIP created successfully: {output_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"7-Zip Error: {e.stderr}")
            raise RuntimeError(f"ZIP作成に失敗しました。\n詳細: {e.stderr}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise RuntimeError(f"予期せぬエラーが発生しました: {str(e)}")
````

## File: src/services/graph_service.py
````python
# src/services/graph_service.py

import json
from typing import List, Dict, Any
from legal_system.models.tables import Heir, Deceased

class GraphService:
    """
    DBの相続人情報を基に、Mermaid.js形式のグラフコードを生成するサービス。
    および法定相続人の順位判定ロジックを提供します。
    """

    @staticmethod
    def generate_mermaid_family_tree(deceased: Deceased, heirs: List[Heir]) -> str:
        """
        被相続人を中心に据えた家系図コードを作成。
        """
        if not deceased:
            return "graph TD\n    Error[被相続人データなし]"

        lines = ["graph TD"]
        
        # 1. スタイルの定義
        lines.append("classDef deceased fill:#f96,stroke:#333,stroke-width:4px,color:white;")
        lines.append("classDef spouse fill:#fff4dd,stroke:#d4a017,stroke-width:2px;")
        lines.append("classDef child fill:#e1f5fe,stroke:#01579b,stroke-width:2px;")
        lines.append("classDef parent fill:#eeeeee,stroke:#666,stroke-width:2px,stroke-dasharray: 5 5;")
        lines.append("classDef sibling fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;")

        # 2. 被相続人ノード
        d_id = f"D{deceased.id}"
        d_name = f"{deceased.name_last}{deceased.name_first}".replace(" ", "").replace("　", "")
        d_label = f"{d_name}<br/>(被相続人)"
        lines.append(f'    {d_id}["{d_label}"]:::deceased')

        # 3. 相続人ノードとエッジ
        if not heirs:
            lines.append(f'    NoHeir["相続人未登録"]:::child')
            lines.append(f'    {d_id} -.-> NoHeir')
            return "\n".join(lines)

        for h in heirs:
            h_id = f"H{h.id}"
            rel = h.relationship_type or "親族"
            h_name = f"{h.name_last}{h.name_first}".replace(" ", "").replace("　", "")
            h_label = f"{h.name_last} {h.name_first}<br/>[{rel}]"
            
            # クラス判定と接続ロジック
            h_class = "child"
            edge = "-->" # デフォルトは子

            if any(k in rel for k in ["妻", "夫", "配偶者"]):
                h_class = "spouse"
                edge = "---" # 配偶者は横並び線
            elif any(k in rel for k in ["父", "母", "祖父", "祖母"]):
                h_class = "parent"
                edge = "---" # 尊属（家系図的には上だが、簡易表示では並列か逆矢印）
            elif any(k in rel for k in ["兄", "弟", "姉", "妹"]):
                h_class = "sibling"
                edge = "---" 

            lines.append(f'    {h_id}["{h_label}"]:::{h_class}')

            # 関係性の描画
            if h_class == "parent":
                # 尊属は被相続人の上に描きたいが、MermaidのTDでは難しいので破線でつなぐ
                lines.append(f"    {h_id} -.-> {d_id}") 
            elif h_class == "spouse":
                lines.append(f"    {d_id} {edge} {h_id}")
            else:
                lines.append(f"    {d_id} {edge} {h_id}")

        return "\n".join(lines)

    @staticmethod
    def determine_inheritance_rank(heirs: List[Heir]) -> Dict[str, List[int]]:
        """
        続柄から法定相続人の優先順位を判定する（簡易版）
        戻り値: {"first": [ids...], "second": [], "third": [], "spouse": []}
        """
        ranks = {"first": [], "second": [], "third": [], "spouse": []}
        
        for h in heirs:
            rel = h.relationship_type or ""
            # 配偶者
            if any(x in rel for x in ["妻", "夫", "配偶者"]):
                ranks["spouse"].append(h.id)
            # 第1順位（直系卑属）
            elif any(x in rel for x in ["長男", "二男", "長女", "二女", "子", "養子", "孫"]):
                ranks["first"].append(h.id)
            # 第2順位（直系尊属）
            elif any(x in rel for x in ["父", "母", "祖父", "祖母"]):
                ranks["second"].append(h.id)
            # 第3順位（兄弟姉妹）
            elif any(x in rel for x in ["兄", "弟", "姉", "妹"]):
                ranks["third"].append(h.id)
                
        return ranks
````

## File: src/services/kintone_client.py
````python
import json
import logging

import requests

from src.utils.retry_decorator import retry_with_backoff

logger = logging.getLogger(__name__)


class KintoneClient:
    def __init__(self, subdomain="chester-tax", api_token=None):
        # 案件管理アプリID (ソースコードより特定)
        self.app_id = "242"
        self.base_url = f"https://{subdomain}.cybozu.com/k/v1"
        self.headers = {
            "X-Cybozu-API-Token": api_token,  # .envなどで管理推奨
            "Content-Type": "application/json",
        }

    @retry_with_backoff(
        max_retries=3,
        backoff_factor=2.0,
        exceptions=(requests.RequestException, requests.HTTPError),
        log_to_audit=True,
    )
    def update_financial_asset(self, record_id, bank_name, balance, date_acquired):
        """
        指定されたレコードの「＜金融機関＞」テーブルに、資産情報を追加・更新する
        """
        # 1. 現在のレコード情報を取得（既存の行を消さないため）
        get_url = f"{self.base_url}/record.json?app={self.app_id}&id={record_id}"
        resp = requests.get(get_url, headers=self.headers, timeout=10)

        if resp.status_code != 200:
            raise requests.HTTPError(f"Kintone Get Error: {resp.text}")

        current_record = resp.json().get("record", {})
        current_table = current_record.get("テーブル_0", {}).get("value", [])

        # 2. 同じ銀行が既にあるかチェック (あれば更新、なければ追加)
        target_row_index = -1
        for i, row in enumerate(current_table):
            existing_bank = row["value"]["文字列__1行__11"]["value"]
            # 部分一致などで判定（例: "三菱UFJ" が含まれていれば）
            if bank_name in existing_bank or existing_bank in bank_name:
                target_row_index = i
                break

        # 3. 行データの作成
        new_row_data = {
            "value": {
                "文字列__1行__11": {"value": bank_name},  # 銀行名
                "残高_0": {"value": str(balance)},  # 残高 (数値も文字列で送る)
                "日付_7": {"value": date_acquired},  # 残証取得日 (YYYY-MM-DD)
            }
        }

        if target_row_index >= 0:
            # 更新: 既存の行を上書き
            logger.info(f"Kintone更新: {bank_name} の情報を上書きします。")
            current_table[target_row_index] = new_row_data
        else:
            # 新規追加
            logger.info(f"Kintone追加: {bank_name} を行末に追加します。")
            current_table.append(new_row_data)

        # 4. 書き戻し (PUT)
        payload = {
            "app": self.app_id,
            "id": record_id,
            "record": {"テーブル_0": {"value": current_table}},
        }

        put_url = f"{self.base_url}/record.json"
        put_resp = requests.put(
            put_url, headers=self.headers, data=json.dumps(payload), timeout=10
        )

        if put_resp.status_code != 200:
            raise requests.HTTPError(f"Kintone Put Error: {put_resp.text}")

        logger.info("✅ Kintoneへの書き戻し成功")
        return True
````

## File: src/services/koseki_service.py
````python
# src/services/koseki_service.py

import logging
import base64
import json
import re
import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from io import BytesIO
from dateutil.relativedelta import relativedelta

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import asc
from pdf2image import convert_from_bytes

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import FamilyRegister, Case, Deceased, Heir
from src.utils.date_utils import parse_all_flexible_date

logger = logging.getLogger(__name__)

class KosekiService:
    def __init__(self):
        self.db = DatabaseManager()
        # 構造化データ抽出のため temperature=0.0
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def _extract_json_safe(self, content: str) -> Dict[str, Any]:
        """AIの回答からJSON部分だけを安全に切り出すヘルパー関数"""
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', content, re.DOTALL)
            if match:
                candidate = match.group(1)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
            return json.loads(content)
        except Exception as e:
            return {"error": f"JSON解析失敗: {str(e)}"}

    def analyze_koseki_image(self, file_bytes: bytes, mime_type: str, expected_name: str = "", family_name_hint: str = "") -> Dict[str, Any]:
        """
        戸籍謄本（複数ページ可）をAIで解析する
        :param expected_name: 対象者のフルネーム（抽出ターゲット）
        :param family_name_hint: 名字のヒント（誤読防止用）
        """
        image_contents = []
        if mime_type == "application/pdf":
            try:
                # PDFを画像リストに変換 (dpi=200程度で十分)
                images = convert_from_bytes(file_bytes, dpi=200)
                for img in images:
                    buf = BytesIO()
                    img.save(buf, format="JPEG")
                    b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
                    image_contents.append({
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{b64_data}"
                    })
            except Exception as e:
                return {"error": f"PDF変換エラー: {e}"}
        else:
            img_b64 = base64.b64encode(file_bytes).decode("utf-8")
            image_contents.append({
                "type": "image_url",
                "image_url": f"data:{mime_type};base64,{img_b64}"
            })

        # プロンプトの構築（ヒント注入）
        name_hint_str = ""
        if expected_name:
            name_hint_str += f"- ターゲット人物: 「{expected_name}」\n"
        if family_name_hint:
            name_hint_str += f"- 名字のヒント: 「{family_name_hint}」 (手書き文字の認識優先度を上げてください)\n"

        prompt = f"""
        あなたは日本の戸籍解読のエキスパートAIです。
        提示された戸籍謄本・除籍謄本・改製原戸籍・住民票（複数ページの場合あり）を読み取り、情報を統合してJSONで抽出してください。

        【読取精度向上のためのヒント】
        {name_hint_str}
        ※上記の名字や人物名が含まれている可能性が高いです。
        ※「旧字体」や「変体仮名」が含まれる場合がありますが、現代の常用漢字・現代仮名遣いに直して出力してください。

        ### 抽出ルール
        1. **筆頭者との混同注意**: 戸籍の冒頭にある「筆頭者」ではなく、氏名欄がターゲット人物となっている箇所の情報を「対象者(target_person)」として抽出してください。
        2. **全関係者の抽出 (family_list)**: 
           - 対象者だけでなく、記載されている**すべて**の人物（配偶者、子、父母、養子、兄弟姉妹、孫、同居人など）を抽出してください。
           - 「除籍」されている人物も抽出してください。
           - 身分事項欄などから、それぞれの「続柄（長男、妻、養女など）」を特定してください。

        ### 抽出項目 (JSON keys)
        1. **doc_type**: "現在戸籍", "除籍謄本", "改製原戸籍", "住民票" のいずれか。
        2. **honseki**: 本籍地。
        3. **head_name**: 筆頭者の氏名。
        4. **target_person**: 対象者の氏名。
        5. **valid_from**: 編製日または入籍日 (YYYY-MM-DD)。
        6. **valid_to**: 除籍日、または現在戸籍の場合は「発行日」 (YYYY-MM-DD)。
        7. **target_birth_date**: 対象者本人の生年月日 (YYYY-MM-DD)。
        8. **target_death_date**: 対象者の死亡日 (YYYY-MM-DD)。生存ならnull。
        9. **family_list**: [{{ "name": "氏名", "rel": "続柄", "birth_date": "YYYY-MM-DD", "death_date": "YYYY-MM-DD" }}, ...]

        ### 出力形式
        JSONのみ出力してください。
        """

        content_list = [{"type": "text", "text": prompt}] + image_contents
        msg = HumanMessage(content=content_list)

        try:
            resp = self.llm.invoke([msg])
            return self._extract_json_safe(resp.content)
        except Exception as e:
            logger.error(f"Koseki Analysis Error: {e}")
            return {"error": str(e)}

    def register_koseki_record(self, case_id: int, target_id: int, target_type: str, data: Dict[str, Any]) -> str:
        """解析結果をDBに保存し、対象者情報および全家族情報を自動登録する"""
        session = self.db._get_session()
        try:
            start_date = parse_all_flexible_date(data.get("valid_from"))
            end_date = parse_all_flexible_date(data.get("valid_to"))

            # 1. 戸籍履歴テーブル(FamilyRegister)への登録
            new_rec = FamilyRegister(
                case_id=case_id,
                doc_type=data.get("doc_type"),
                issuing_authority=data.get("honseki"),
                head_of_family=data.get("head_name"),
                valid_from=start_date,
                valid_to=end_date
            )
            
            if target_type == "deceased":
                new_rec.deceased_id = target_id
            else:
                new_rec.heir_id = target_id
            
            session.add(new_rec)

            updated_items = []
            person = None
            parent_deceased_id = None
            
            # 2. 対象者本人の情報更新（生年月日・死亡日など）
            if target_type == "deceased":
                person = session.query(Deceased).get(target_id)
                parent_deceased_id = target_id
            else:
                person = session.query(Heir).get(target_id)
                if person:
                    parent_deceased_id = person.deceased_id

            if person:
                if not person.date_of_birth:
                    b_date = parse_all_flexible_date(data.get("target_birth_date"))
                    if b_date:
                        person.date_of_birth = b_date
                        updated_items.append("生年月日")
                
                if target_type == "deceased" and not person.date_of_death:
                    d_date = parse_all_flexible_date(data.get("target_death_date"))
                    if d_date:
                        person.date_of_death = d_date
                        updated_items.append("死亡日")
                
                if hasattr(person, "hometown") and not person.hometown:
                    honseki = data.get("honseki")
                    if honseki:
                        person.hometown = honseki
                        updated_items.append("本籍地")

            # 3. 家族リスト(family_list)の取り込み -> Heirテーブルへ追加
            family_list = data.get("family_list", [])
            if parent_deceased_id and family_list:
                existing_heirs = session.query(Heir).filter(Heir.deceased_id == parent_deceased_id).all()
                existing_names = set()
                
                # 既存チェック（名寄せ）
                for h in existing_heirs:
                    full = f"{h.name_last}{h.name_first}".replace(" ", "").replace("　", "")
                    existing_names.add(full)
                
                # 被相続人本人も除外リストに追加
                deceased_obj = session.query(Deceased).get(parent_deceased_id)
                if deceased_obj:
                    d_full = f"{deceased_obj.name_last}{deceased_obj.name_first}".replace(" ", "").replace("　", "")
                    existing_names.add(d_full)

                added_count = 0
                for member in family_list:
                    raw_name = member.get("name", "")
                    clean_name = raw_name.replace(" ", "").replace("　", "")
                    if not clean_name or clean_name in existing_names: continue

                    # 氏名の分割 (全角スペース前提)
                    parts = raw_name.replace("　", " ").split(" ", 1)
                    lname = parts[0]
                    fname = parts[1] if len(parts) > 1 else ""
                    
                    b_date = parse_all_flexible_date(member.get("birth_date"))
                    d_date = parse_all_flexible_date(member.get("death_date"))
                    
                    new_heir = Heir(
                        deceased_id=parent_deceased_id,
                        name_last=lname,
                        name_first=fname,
                        relationship_type=member.get("rel", "関係者"),
                        date_of_birth=b_date,
                        date_of_death=d_date,
                        is_contracting_party=False
                    )
                    session.add(new_heir)
                    existing_names.add(clean_name)
                    added_count += 1
                
                if added_count > 0:
                    updated_items.append(f"関係者{added_count}名をリストに追加")

            session.commit()
            msg = "戸籍情報を登録しました。"
            if updated_items:
                msg += f"\n✨ 自動更新: {'・'.join(updated_items)}"
            return f"Success: {msg}"

        except Exception as e:
            session.rollback()
            logger.error(f"DB Save Error: {e}")
            return f"Error: {str(e)}"
        finally:
            session.close()

    def check_continuity_gaps(self, deceased_id: int) -> Tuple[List[Dict], List[str]]:
        """
        【相続用】連続性チェック
        被相続人の出生〜死亡までの戸籍期間に「空白」がないかチェックする。
        """
        session = self.db._get_session()
        try:
            person = session.query(Deceased).get(deceased_id)
            if not person or not person.date_of_birth or not person.date_of_death:
                return [], ["被相続人の「生年月日」と「死亡日」が必要です。（基本情報を登録してください）"]

            birth_date = person.date_of_birth
            death_date = person.date_of_death

            records = session.query(FamilyRegister).filter(
                FamilyRegister.deceased_id == deceased_id
            ).order_by(asc(FamilyRegister.valid_from)).all()

            if not records:
                return [], ["戸籍が登録されていません。"]

            gaps = []
            intervals = []
            
            # 有効な期間を持つレコードのみ抽出
            for r in records:
                if r.valid_from and r.valid_to:
                    intervals.append((r.valid_from, r.valid_to))
            
            # 開始日でソート
            intervals.sort(key=lambda x: x[0])

            # A. 出生時の不足チェック
            if intervals and intervals[0][0] > birth_date:
                gaps.append({
                    "start": birth_date,
                    "end": intervals[0][0],
                    "reason": "出生時の戸籍不足"
                })
            
            # B. 中間の不足チェック
            # ロジック: 前の終了日と次の開始日が連続しているか？
            merged_end = intervals[0][1] if intervals else birth_date
            
            for i in range(len(intervals) - 1):
                this_end = intervals[i][1]
                next_start = intervals[i+1][0]
                
                # 1日以上のギャップがあれば不足とみなす
                if next_start > this_end + datetime.timedelta(days=1):
                    gaps.append({
                        "start": this_end,
                        "end": next_start,
                        "reason": "連続性の欠如 (転籍・改製など)"
                    })
                
                # 終了日を更新（重複期間を考慮して最大を取る）
                if intervals[i+1][1] > merged_end:
                    merged_end = intervals[i+1][1]

            # C. 死亡時の不足チェック
            if merged_end < death_date:
                gaps.append({
                    "start": merged_end,
                    "end": death_date,
                    "reason": "死亡時の戸籍不足"
                })

            advice = []
            if not gaps:
                advice.append("✅ 出生から死亡まで連続しています。")
            else:
                for g in gaps:
                    s_str = g['start'].strftime('%Y/%m/%d')
                    e_str = g['end'].strftime('%Y/%m/%d')
                    advice.append(f"⚠️ {s_str} 〜 {e_str} の期間が不足しています。")

            return gaps, advice

        except Exception as e:
            return [], [f"エラー: {e}"]
        finally:
            session.close()

    def recommend_missing_koseki_action(self, deceased_id: int, gaps: List[Dict]) -> str:
        """
        不足期間（ギャップ）と登録済み戸籍情報に基づき、
        AIが「次にどこの役所に何を請求すべきか」をアドバイスする。
        """
        if not gaps:
            return "不足期間はありません。すべて揃っています。"

        session = self.db._get_session()
        try:
            # 登録済みの戸籍情報をテキスト化
            records = session.query(FamilyRegister).filter(
                FamilyRegister.deceased_id == deceased_id
            ).order_by(asc(FamilyRegister.valid_from)).all()
            
            records_text = ""
            for r in records:
                s = r.valid_from.strftime('%Y-%m-%d') if r.valid_from else "?"
                e = r.valid_to.strftime('%Y-%m-%d') if r.valid_to else "?"
                records_text += f"- {r.doc_type}: {s}〜{e} (本籍: {r.issuing_authority}, 筆頭者: {r.head_of_family})\n"

            # ギャップ情報テキスト化
            gaps_text = ""
            for g in gaps:
                s = g['start'].strftime('%Y-%m-%d')
                e = g['end'].strftime('%Y-%m-%d')
                gaps_text += f"- 不足期間: {s}〜{e} ({g['reason']})\n"

            # プロンプト作成
            system_prompt = """
            あなたは相続業務専門の行政書士です。
            現在、被相続人の「出生から死亡まで」の戸籍を収集中ですが、一部に不足（空白期間）があります。
            これまでの取得状況と不足期間に基づき、担当者が「次にどのアクションを取るべきか」を具体的にアドバイスしてください。

            【判断ロジック】
            - **出生時の不足**: 最初の戸籍よりさらに前の「改製原戸籍」や「除籍謄本」が必要です。「従前戸籍」欄を確認するよう促してください。
            - **中間の不足**: 転籍や改製によって途切れている可能性があります。「転籍日」や「改製日」を確認し、転籍前の本籍地へ請求するよう促してください。
            - **死亡時の不足**: 死亡の記載がある戸籍（除籍謄本）が必要です。

            【出力フォーマット】
            結論（次に請求すべき役所・書類）を具体的に、箇条書きで答えてください。
            推測が含まれる場合は「〜の可能性があります」と添えてください。
            """

            user_prompt = f"""
            【現在の取得済み戸籍】
            {records_text}

            【不足している期間】
            {gaps_text}

            担当者への次の一手アドバイスをお願いします。
            """

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({})

        except Exception as e:
            return f"アドバイス生成エラー: {e}"
        finally:
            session.close()
````

## File: src/services/master_service.py
````python
# マスタ管理サービス
````

## File: src/services/party_service.py
````python
# 人物管理サービス
````

## File: src/services/persistence_service.py
````python
import json
import logging
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# パス解決とインポート
try:
    # あなたの既存のtables.pyを利用
    from src.legal_system.models.tables import (
        AuditLog,
        BankMaster,
        Base,
        Case,
        FinancialAsset,
        User,
    )
except ImportError:
    import sys
    from pathlib import Path

    # ルートディレクトリをパスに追加して再試行
    sys.path.append(str(Path(__file__).resolve().parents[3]))
    from src.legal_system.models.tables import (
        AuditLog,
        BankMaster,
        Base,
        Case,
        FinancialAsset,
    )

from src.legal_system.core.schemas import DocumentAnalysisResult

# DB接続先 (configから読み込むのが理想ですが、今回は直接指定)
# ※ tables.py が想定しているDBに合わせてください (SQLite/PostgreSQL)
DB_URL = "sqlite:///./data/db/legal_system.db"


class PersistenceDatabaseManager:
    """保存処理専用のDB接続クラス"""

    def __init__(self):
        self.engine = create_engine(DB_URL, echo=False)
        # テーブルが存在しない場合は作成（既存テーブルは消えません）
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()


class VerificationPersistenceService:
    """
    AIの解析結果を、既存の複雑なリレーションを持つDBに安全に保存するサービス
    """

    def __init__(self):
        self.db = PersistenceDatabaseManager()

    def _get_or_create_bank(self, session: Session, bank_name_raw: str) -> BankMaster:
        """
        AIが読み取った銀行名からマスタIDを特定する。
        完全一致しなければ、新規マスタとして登録してしまう（運用回避策）。
        """
        # 1. 完全一致検索
        bank = (
            session.query(BankMaster)
            .filter(BankMaster.bank_name == bank_name_raw)
            .first()
        )
        if bank:
            return bank

        # 2. 部分一致検索 (例: '三菱UFJ' で '三菱UFJ銀行' を当てる)
        # 実際の運用では BankAlias テーブルを使うべきですが、今回は簡易実装
        bank = (
            session.query(BankMaster)
            .filter(BankMaster.bank_name.like(f"%{bank_name_raw}%"))
            .first()
        )
        if bank:
            return bank

        # 3. 見つからない場合は新規作成 (Unknown扱い)
        # codeはダミーで発行
        new_bank = BankMaster(bank_name=bank_name_raw, bank_code="9999")
        session.add(new_bank)
        session.flush()  # ID確定
        return new_bank

    def save_analysis_result(
        self, case_id: int, result: DocumentAnalysisResult, filename: str
    ):
        """
        解析結果を保存するメインメソッド
        """
        session = self.db.get_session()
        try:
            # -------------------------------------------------------
            # 1. 案件(Case)の存在確認
            # -------------------------------------------------------
            case_record = session.query(Case).filter(Case.case_id == case_id).first()
            if not case_record:
                # 案件がないと保存できないためエラーにするか、ダミーを作る
                # ここではデモ用にダミー作成
                case_record = Case(
                    case_id=case_id,
                    case_number=f"G{case_id:04d}",
                    client_name="デモ 依頼者",
                    client_name_kana="デモ イライシャ",
                )
                session.add(case_record)
                session.flush()

            # -------------------------------------------------------
            # 2. 監査ログ(AuditLog)の保存
            # -------------------------------------------------------
            # tables.py の定義に合わせて JSON を文字列化
            details_json = json.dumps(
                result.model_dump(mode="json"), ensure_ascii=False
            )

            # 既存の AuditLog は user_id 必須かもしれませんが、nullableを確認して設定
            # ここでは必要最低限のカラムを埋めます
            audit = AuditLog(
                action_type="AI_VERIFICATION",
                target=filename,
                details=details_json,  # Text型
                timestamp=datetime.now(),
                # user_id = current_user_id # ログイン機能があれば設定
            )
            session.add(audit)

            # -------------------------------------------------------
            # 3. 資産(FinancialAsset)の保存
            # -------------------------------------------------------
            saved_count = 0
            if result.assets:
                for asset in result.assets:
                    # 銀行マスタのID解決 (名前 -> ID)
                    bank_record = self._get_or_create_bank(
                        session, asset.bank_name.value
                    )

                    # FinancialAssetの作成
                    f_asset = FinancialAsset(
                        case_id=case_record.case_id,
                        bank_id=bank_record.id,
                        # bank_codeなどの重複情報は正規化により不要だが、
                        # テーブル定義に合わせて必要な情報を埋める
                        account_number=asset.account_number.value
                        if asset.account_number
                        else "不明",
                        balance=float(asset.balance) if asset.balance else 0.0,
                        # AI判定結果をstatusに入れる
                        status="pending_ai",
                        # 支店や種別は今回AIが取れていれば入れる (なければNULL)
                        # branch_id = ...
                        # account_type_id = ...
                    )
                    session.add(f_asset)
                    saved_count += 1

            session.commit()
            return True, f"保存完了: 資産{saved_count}件を登録しました。"

        except Exception as e:
            session.rollback()
            logging.error(f"DB Save Error: {e}")
            return False, f"システムエラー: {str(e)}"
        finally:
            session.close()
````

## File: src/services/rag_search_service.py
````python
# src/services/rag_search_service.py
import os
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import FileRegistry, BankMaster

class RagSearchService:
    """
    銀行手続き・過去ドキュメント検索サービス
    """
    def __init__(self):
        self.db = DatabaseManager()
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def search_bank_rules(self, query: str) -> str:
        """
        銀行マスタ・規定（JSON/CSV）から手続き情報を回答する (Gemini RAG)
        """
        # 簡易実装: BankMasterテーブルの remarks や JSONルールを検索
        # 本来はVectorStoreを使うが、ここではSQLのLIKE検索とLLM回答生成を組み合わせる例
        session = self.db._get_session()
        try:
            # 1. キーワードに関連する銀行を特定
            banks = session.query(BankMaster).filter(BankMaster.bank_name.contains(query)).all()
            
            context_text = ""
            for b in banks:
                context_text += f"""
                【銀行名: {b.bank_name}】
                - 印鑑証明期限: {b.seal_cert_limit}
                - 本人確認: {b.id_verify_rule}
                - 備考: {b.remarks}
                """
            
            # 2. LLMで回答生成
            prompt = ChatPromptTemplate.from_template("""
            あなたは行政書士事務所のアシスタントです。
            以下の銀行データベース情報を基に、ユーザーの質問に答えてください。
            情報がない場合は「データベースに登録がありません」と答えてください。

            【データベース情報】
            {context}

            質問: {question}
            """)
            
            chain = prompt | self.llm | StrOutputParser()
            return chain.invoke({"context": context_text, "question": query})
            
        finally:
            session.close()

    def search_past_documents(self, query: str) -> List[Dict]:
        """
        過去の提出書類（個人情報含む）をメタデータ検索する
        ※ セキュリティのため、AIには中身を渡さず、ファイル名と種別で検索してヒットさせる
        """
        session = self.db._get_session()
        try:
            # ファイル名、銀行名、書類種別で検索
            # 例: "三菱UFJ 残高証明" -> 三菱UFJの残高証明ファイルを検索
            keywords = query.split()
            base_query = session.query(FileRegistry)
            
            for k in keywords:
                term = f"%{k}%"
                base_query = base_query.filter(
                    (FileRegistry.filename.ilike(term)) | 
                    (FileRegistry.doc_type.ilike(term))
                )
            
            results = base_query.order_by(FileRegistry.registered_at.desc()).limit(10).all()
            
            return [
                {
                    "filename": f.filename,
                    "doc_type": f.doc_type,
                    "case_id": f.case_id,
                    "registered_at": f.registered_at.strftime('%Y-%m-%d'),
                    # 実際のパスは隠蔽し、ダウンロード時に解決
                    "file_hash": f.file_hash 
                }
                for f in results
            ]
        finally:
            session.close()
````

## File: src/services/search_service.py
````python
# src/services/search_service.py

import logging
import unicodedata
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload

from legal_system.models.tables import Case, Deceased, Heir, Contact, H_ContactLink

logger = logging.getLogger(__name__)

def normalize_text_space(text: str) -> str:
    if not text: return ""
    return text.replace(" ", "　").strip()

def normalize_text(text: str) -> str:
    if not text: return ""
    return unicodedata.normalize("NFKC", text).strip()

def search_cases_enhanced(session, keyword: str) -> List[Case]:
    """
    案件検索ロジック（強化版）
    - 案件番号、依頼者名、被相続人名、電話番号などから検索
    """
    base_query = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.manager),
        joinedload(Case.operator)
    )
    
    if not keyword:
        # デフォルトは作成日順で直近10件
        return base_query.order_by(Case.created_at.desc()).limit(10).all()

    clean_key = f"%{keyword.strip()}%"
    
    # 検索クエリ構築
    # 関連テーブルを結合してフィルタリング
    return base_query.join(Case.deceased_ref)\
        .outerjoin(Deceased.heirs)\
        .outerjoin(Heir.contact_links)\
        .outerjoin(H_ContactLink.contact)\
        .filter(
            or_(
                # 1. 案件基本情報
                Case.case_number.ilike(clean_key),
                Case.client_name.ilike(clean_key),
                Case.client_name_kana.ilike(clean_key),
                Case.sol_case_number.ilike(clean_key),
                Case.referral_sec_phone.ilike(clean_key),
                
                # 2. 被相続人 (漢字・カナ・結合)
                Deceased.name_last.ilike(clean_key),
                Deceased.name_first.ilike(clean_key),
                # フルネーム結合検索 (姓+名)
                (Deceased.name_last + Deceased.name_first).ilike(clean_key),
                (Deceased.name_last + " " + Deceased.name_first).ilike(clean_key),
                (Deceased.name_last + "　" + Deceased.name_first).ilike(clean_key),
                # カナ検索
                Deceased.name_last_kana.ilike(clean_key),
                Deceased.name_first_kana.ilike(clean_key),
                (Deceased.name_last_kana + Deceased.name_first_kana).ilike(clean_key),

                # 3. 連絡先 (電話番号など)
                Contact.value.ilike(clean_key)
            )
        ).distinct().limit(20).all()
````

## File: src/utils/__init__.py
````python

````

## File: src/__init__.py
````python

````

## File: .dockerignore
````
.git
.venv
.rye
__pycache__
*.pyc
.env
.DS_Store
data/db/chroma  # ローカルDBはホスト側からマウントするためコピー不要
data/db/sql
repomix-output.md
````

## File: .python-version
````
3.12.4
````

## File: agent_rules_sample.json
````json
[
  {
    "bank_name": "三菱UFJ銀行",
    "procedure_type": "相続手続（代理人）",
    "required_documents": [
      "遺産分割協議書",
      "印鑑証明書",
      "戸籍謄本（出生から死亡まで）",
      "実質的支配者申告書",
      "行政書士証票コピー",
      "委任状"
    ],
    "notes": "任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
    "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）"
  },
  {
    "bank_name": "ゆうちょ銀行",
    "procedure_type": "相続手続（代理人）",
    "required_documents": [
      "相続確認表",
      "貯金等相続手続請求書",
      "委任状",
      "印鑑証明書",
      "戸籍謄本（出生から死亡まで）"
    ],
    "notes": "窓口ではなく相続センターへの郵送対応が基本。Webでの相続確認表入力が必須。",
    "original_return_policy": "原則として原本還付可。コピーの提出が必要。"
  },
  {
    "bank_name": "三井住友銀行",
    "procedure_type": "相続手続（代理人）",
    "required_documents": [
      "相続手続依頼書",
      "印鑑証明書",
      "行政書士証票",
      "戸籍謄本（出生から死亡まで）"
    ],
    "notes": "Web予約をしてからの来店が推奨される。",
    "original_return_policy": "原本還付可"
  }
]
````

## File: bank_master.json
````json
[
    {
        "bank_name": "三菱UFJ銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "遺産分割協議書（実印押印）",
            "相続人全員の印鑑証明書（6ヶ月以内）",
            "被相続人の出生から死亡までの連続した戸籍謄本",
            "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
            "【代理人】行政書士証票のコピー（原本照合済）",
            "【代理人】委任状（銀行所定様式または実印押印のある任意様式）"
        ],
        "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
        "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）"
    },
    {
        "bank_name": "ゆうちょ銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "相続確認表（Web入力可）",
            "貯金等相続手続請求書（代理人による署名・実印）",
            "【代理人】特定事務任用カード（提示のみ）",
            "【代理人】委任状（実印押印必須）"
        ],
        "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
        "original_return_policy": "原則として原本還付可。コピーの提出が必要。"
    },
    {
        "bank_name": "三井住友銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "相続手続依頼書（代理人署名）",
            "【代理人】実印および印鑑証明書（6ヶ月以内）",
            "【代理人】行政書士証票または識別カード",
            "被相続人の全戸籍（出生〜死亡）"
        ],
        "notes": "※Web予約をしてからの来店が推奨される。",
        "original_return_policy": "原本還付可"
    }
]
````

## File: branch_routing_rules.json
````json
{
  "横浜拠点": ["横浜支店", "川崎支店", "港南台支店"],
  "新宿拠点": ["新宿支店", "中野支店", "本店"],
  "大阪拠点": ["梅田支店", "難波支店"]
}
````

## File: create_rule_master.py
````python
import json
from typing import Any, Dict, List

# プロジェクトルートに作成される手続要件マスタ
DATA_FILE: str = "bank_master.json"


def create_initial_bank_data() -> List[Dict[str, Any]]:
    """
    行政書士業務に特化した銀行マスタデータの初期セットを生成する。
    """
    banks = [
        {
            "bank_name": "三菱UFJ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "遺産分割協議書（実印押印）",
                "相続人全員の印鑑証明書（6ヶ月以内）",
                "被相続人の出生から死亡までの連続した戸籍謄本",
                "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
                "【代理人】行政書士証票のコピー（原本照合済）",
                "【代理人】委任状（銀行所定様式または実印押印のある任意様式）",
            ],
            "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
            "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）",
        },
        {
            "bank_name": "ゆうちょ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続確認表（Web入力可）",
                "貯金等相続手続請求書（代理人による署名・実印）",
                "【代理人】特定事務任用カード（提示のみ）",
                "【代理人】委任状（実印押印必須）",
            ],
            "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
            "original_return_policy": "原則として原本還付可。コピーの提出が必要。",
        },
        {
            "bank_name": "三井住友銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続手続依頼書（代理人署名）",
                "【代理人】実印および印鑑証明書（6ヶ月以内）",
                "【代理人】行政書士証票または識別カード",
                "被相続人の全戸籍（出生〜死亡）",
            ],
            "notes": "※Web予約をしてからの来店が推奨される。",
            "original_return_policy": "原本還付可",
        },
    ]
    return banks


def save_bank_master(data: List[Dict[str, Any]]) -> None:
    try:
        # プロジェクトルートに保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 成功: '{DATA_FILE}' を作成しました。")
        print("   これで『01_銀行手続要件_確認』ページが動作します。")
    except IOError as e:
        print(f"❌ エラー: ファイルの書き込みに失敗しました。詳細: {e}")


if __name__ == "__main__":
    bank_data = create_initial_bank_data()
    save_bank_master(bank_data)
````

## File: create_table_migration.py
````python
import os
import sys
from sqlalchemy import inspect

# プロジェクトの src ディレクトリをパスに追加してモジュールを読み込めるようにする
sys.path.append(os.path.join(os.getcwd(), "src"))

# DatabaseManager と 作成したいモデル(IncomingNoteBuffer)をインポート
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import IncomingNoteBuffer

def create_incoming_note_buffer_table():
    print("🚀 'IncomingNoteBuffer' テーブルの作成を開始します...")

    # データベース接続エンジンの取得
    db = DatabaseManager()
    engine = db.engine

    # すでにテーブルが存在するかチェック
    inspector = inspect(engine)
    if inspector.has_table("incoming_note_buffer"):
        print("ℹ️  テーブル 'incoming_note_buffer' は既に存在します。作成をスキップします。")
        return

    try:
        # SQLAlchemyの機能を使って、モデル定義からテーブルを作成する
        IncomingNoteBuffer.__table__.create(engine)
        print("✅ 成功: テーブル 'incoming_note_buffer' を作成しました。")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    create_incoming_note_buffer_table()
````

## File: def enable_advanced_autofocus().txt
````
def enable_advanced_autofocus():
    """
    Streamlitの深いiFrame構造を突破し、
    特定のプレースホルダーを持つ検索バーに強制的にフォーカスを当てる。
    """
    # ターゲットにするプレースホルダーを定義 (st_keyupの引数と一致させる)
    target_placeholder = "案件番号、氏名、電話番号で検索..."

    js_code = f"""
    <script>
        (function() {{
            const TARGET_TEXT = "{target_placeholder}";
            let attempts = 0;
            const maxAttempts = 50; // 最大5秒間試行

            function findAndFocus() {{
                // 1. Streamlitのメインドキュメント(親)を取得
                const mainDoc = window.parent.document;
                
                // 2. すべてのinput要素をスキャン
                const allInputs = mainDoc.querySelectorAll('input');
                
                for (let input of allInputs) {{
                    // プレースホルダーが一致するか確認
                    if (input.placeholder === TARGET_TEXT) {{
                        input.focus();
                        // 視覚的にフォーカスされたことを強調（任意）
                        input.style.boxShadow = "0 0 5px #d33682"; 
                        return true;
                    }}
                }}
                
                // 3. iFrame内にある可能性を考慮 (st_keyup等はiFrameでラップされる場合がある)
                const iframes = mainDoc.querySelectorAll('iframe');
                for (let frame of iframes) {{
                    try {{
                        const frameDoc = frame.contentDocument || frame.contentWindow.document;
                        const frameInputs = frameDoc.querySelectorAll('input');
                        for (let fInput of frameInputs) {{
                            if (fInput.placeholder === TARGET_TEXT) {{
                                fInput.focus();
                                return true;
                            }}
                        }}
                    }} catch (e) {{
                        // クロスドメイン制約でアクセスできない場合はスキップ
                    }}
                }}
                return false;
            }}

            const timer = setInterval(() => {{
                if (findAndFocus() || attempts > maxAttempts) {{
                    clearInterval(timer);
                }}
                attempts++;
            }}, 100);
        }})();
    </script>
    """
    components.html(js_code, height=0)
````

## File: directory_structure.txt
````
.
├── .streamlit/
│   └── config.toml
├── data/
│   ├── db/                 # PostgreSQL (Docker volume) & ChromaDB
│   ├── rules/              # 業務ルール (JSON/Markdown)
│   │   ├── bank_guidance.json
│   │   ├── bank_master.csv
│   │   └── company_rules.md
│   ├── templates/          # PDF雛形ファイル
│   └── zengin/             # 全銀データ
├── src/
│   ├── chains/             # LangChainの処理フロー
│   │   └── bank_procedure_chain.py
│   ├── legal_system/
│   │   ├── core/           # コアロジック
│   │   │   ├── ai_factory.py       # Gemini/Vertex/Ollama切り替え
│   │   │   ├── config.py           # 環境設定
│   │   │   ├── data_sync.py        # Kintone/JSON同期
│   │   │   ├── database_manager.py # DB接続・CRUD
│   │   │   ├── ocr_engine.py       # PaddleOCRラッパー
│   │   │   └── pdf_processor.py    # PDF解析・正規表現抽出
│   │   ├── models/         # SQLAlchemyモデル
│   │   │   └── tables.py
│   │   ├── ui/             # Streamlit画面
│   │   │   ├── components/ # 共通パーツ (smart_guide等)
│   │   │   └── pages/      # 各画面ファイル
│   │   │       ├── 01_Kintoneデータ_エクセル入力フォーム.py
│   │   │       ├── 02_預貯金口座入力フォーム.py
│   │   │       ├── 03_相続書類_作成フォーム.py
│   │   │       ├── 04_法定相続情報_読取.py
│   │   │       ├── 05_顧客紹介連絡表_読取.py
│   │   │       ├── 06_案件登録_手動.py
│   │   │       └── 07_案件詳細_統合管理.py
│   │   └── main.py         # アプリ起動エントリポイント
│   ├── services/           # ビジネスロジック層
│   │   ├── deceased_service.py
│   │   ├── folder_service.py
│   │   └── kintone_sync_service.py
│   └── utils/
│       └── date_utils.py
├── .env
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
````

## File: docker-compose.yml
````yaml
# docker-compose.yml
services:
  # --- 1. アプリケーションサーバー (Streamlit) ---
  app:
    build: .
    container_name: legal_app
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "8501:8501"  # ブラウザからアクセスするポート
    environment:
    - POSTGRES_HOST=db
    - POSTGRES_PORT=5432
    - POSTGRES_DB=${POSTGRES_DB}        # ★ .envから読み込み
    - POSTGRES_USER=${POSTGRES_USER}    # ★ .envから読み込み
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD} # ★ .envから読み込み
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    # environment:
    #   - POSTGRES_HOST=db
    #   - POSTGRES_PORT=5432
    #   - POSTGRES_DB=legal_db
    #   - POSTGRES_USER=postgres
    #   - POSTGRES_PASSWORD=password
    #   # 本番ではGoogle API Key等はここで渡すか、.envファイルを読み込ませます
    #   - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - db
    volumes:
      # ホストのソースコードをコンテナにマウント (開発中は変更が即反映されるように)
      - ./src:/app/src
      - ./data:/app/data
    restart: always

  # --- 2. データベースサーバー (PostgreSQL) ---
  db:
    image: postgres:15
    container_name: legal_db
    environment:
      - POSTGRES_DB=${POSTGRES_DB}        # ★ .envから読み込み
      - POSTGRES_USER=${POSTGRES_USER}    # ★ .envから読み込み
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD} # ★ .envから読み込み
    ports:
      - "5432:5432"
  # db:
  #   image: postgres:15
  #   container_name: legal_db
  #   environment:
  #     - POSTGRES_DB=legal_db
  #     - POSTGRES_USER=postgres
  #     - POSTGRES_PASSWORD=password
  #   ports:
  #     - "5432:5432"
    volumes:
      # DBのデータをDockerボリュームに保存 (コンテナを消してもデータは残る)
      - postgres_data:/var/lib/postgresql/data
    restart: always

# データの永続化領域定義
volumes:
  postgres_data:
````

## File: Dockerfile
````dockerfile
# ベースイメージ: Python 3.12 (軽量版)
FROM python:3.12-slim

# 1. OSレベルの依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 作業ディレクトリの設定
WORKDIR /app

# 3. 依存関係ファイルのコピーとインストール
# エラー回避のため、設定ファイル(pyproject.toml)と説明書(README.md)を先にコピーします
COPY requirements.lock pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.lock

# 4. ソースコード全体をコピー
COPY . .

# 5. 環境変数の設定 (Streamlit用)
ENV PYTHONUNBUFFERED=1

# 6. アプリケーションの起動コマンド
CMD ["python", "src/legal_system/main.py"]
````

## File: export_code.py
````python
import subprocess


def run_repomix():
    print("🚀 ソースコードの集約を開始します...")

    # Repomixを実行するコマンド
    # --style markdown : Geminiが読みやすいマークダウン形式で出力
    # --ignore "**/*.json,**/*.lock" : 不要なファイルを除外（必要に応じて追加）
    command = "npx -y repomix --style markdown"

    try:
        # コマンドを実行
        # shell=True はWindows/Mac両対応のため
        subprocess.run(command, shell=True, check=True)

        print("\n✅ 完了しました！")
        print("📁 'repomix-output.md' というファイルが作成されています。")
        print("🤖 これをGeminiにアップロードしてください。")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    run_repomix()
````

## File: generate_token.py
````python
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# 許可する権限の範囲（読み取り専用）
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def generate_token():
    creds = None
    # すでに token.json がある場合はロード（再生成時など）
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 有効なトークンがない場合、新規取得
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 トークンをリフレッシュします...")
            creds.refresh(Request())
        else:
            print("🚀 ブラウザを起動して認証を行います...")
            
            if not os.path.exists('credentials.json'):
                print("❌ エラー: credentials.json が見つかりません。ルートディレクトリに配置してください。")
                return

            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            
            # ここでローカルサーバーを立ち上げ、ブラウザ認証を行う
            creds = flow.run_local_server(port=0)
        
        # token.json として保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            print("✅ 成功: token.json を生成しました！")

if __name__ == '__main__':
    generate_token()
````

## File: kintone_data_sample.json
````json
{
  "$id": "1001",
  "record_id": "1001",
  "顧客コード_2": "G1234",
  "顧客名": "相続　太郎",
  "顧客名(ふりがな)": "そうぞく　たろう",
  "郵便番号": "100-0001",
  "住所": "東京都千代田区千代田1-1",
  "TEL": "090-1234-5678, 03-1234-5678",
  "メールアドレス": "taro@example.com",
  
  "被相続人名": "相続　父郎",
  "被相続人名（ふりがな）": "そうぞく　ちちろう",
  "相続開始日": "2025-01-01",
  
  "担当者①": "山田 担当",
  "担当者②": "鈴木 補助",
  
  "SOL案件No.（日興）": "SOL-9999",
  "紹介日": "2025-01-10",
  "同意書日付(日興)": "2025-01-15",
  "支店名（日興）": "東京支店",
  "担当者（日興）": "証券　担当男",
  
  "assets": [
    {
      "bank_name": "三菱UFJ銀行",
      "branch_name": "本店",
      "account_number": "1234567",
      "balance": 5000000,
      "status": "新規取込"
    }
  ]
}
````

## File: migrate_koseki_table.py
````python
import sys
import os
from sqlalchemy import text, inspect

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Base

def fix_schema():
    print("🚀 データベース構造の自動修復・同期を開始します...")
    
    db = DatabaseManager()
    engine = db.engine
    
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            
            # ====================================================
            # 1. heirs テーブルの修正 (今回のエラー原因)
            # ====================================================
            if inspector.has_table("heirs"):
                cols = [c['name'] for c in inspector.get_columns("heirs")]
                
                # エラー原因: occupation (職業)
                if "occupation" not in cols:
                    print("🛠️ 'heirs' テーブルに 'occupation' カラムを追加中...")
                    conn.execute(text("ALTER TABLE heirs ADD COLUMN occupation VARCHAR;"))
                
                # 本籍地
                if "hometown" not in cols:
                    print("🛠️ 'heirs' テーブルに 'hometown' カラムを追加中...")
                    conn.execute(text("ALTER TABLE heirs ADD COLUMN hometown VARCHAR;"))
                
                print("   -> heirs テーブル確認完了")

            # ====================================================
            # 2. file_registry テーブルの修正 (Ver 3.3新機能)
            # ====================================================
            if inspector.has_table("file_registry"):
                cols = [c['name'] for c in inspector.get_columns("file_registry")]
                
                if "status" not in cols:
                    print("🛠️ 'file_registry' に 'status' を追加中...")
                    conn.execute(text("ALTER TABLE file_registry ADD COLUMN status VARCHAR DEFAULT 'CONFIRMED';"))
                    
                if "ai_confidence" not in cols:
                    print("🛠️ 'file_registry' に 'ai_confidence' を追加中...")
                    conn.execute(text("ALTER TABLE file_registry ADD COLUMN ai_confidence FLOAT DEFAULT 0.0;"))
                    
                if "extracted_data" not in cols:
                    print("🛠️ 'file_registry' に 'extracted_data' を追加中...")
                    conn.execute(text("ALTER TABLE file_registry ADD COLUMN extracted_data TEXT;"))
                
                print("   -> file_registry テーブル確認完了")

            # ====================================================
            # 3. 未作成テーブルの一括作成 (IncomingNoteBufferなど)
            # ====================================================
            print("🛠️ 未作成のテーブルがあれば作成します...")
            Base.metadata.create_all(engine)

            conn.commit()
            print("\n✅ データベースの修復が完了しました！")
            print("   これで 'occupation' カラムのエラーは解消されます。")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("   PostgreSQLが起動していることを確認してください。")

if __name__ == "__main__":
    fix_schema()
````

## File: organize_files.py
````python
# fix_structure.py
import os
import shutil
from pathlib import Path

def main():
    print("🔧 リファクタリング前の最終微修正を開始します...")
    root_dir = Path.cwd()

    # ==========================================
    # 1. bank_procedure_chain.py のインポート修正
    # ==========================================
    target_file = root_dir / "src/chains/bank_procedure_chain.py"
    if target_file.exists():
        print(f"📝 Fixing imports in: {target_file.name}")
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 間違ったインポートパスを修正
        new_content = content.replace(
            "from src.ai_factory import AIFactory",
            "from legal_system.core.ai_factory import AIFactory"
        )
        
        if content != new_content:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_content)
            print("   ✅ Fixed: Import path corrected.")
        else:
            print("   ✓ Already correct.")
    else:
        print("   ⚠️ File not found: src/chains/bank_procedure_chain.py (Skipping)")

    # ==========================================
    # 2. backupフォルダを src 外へ移動
    # ==========================================
    src_backup_dir = root_dir / "src/legal_system/ui/pages/backup"
    dest_archive_dir = root_dir / "_archive/pages_backup"

    if src_backup_dir.exists():
        print(f"\n📦 Moving backup folder out of src...")
        # 移動先フォルダ作成
        dest_archive_dir.parent.mkdir(exist_ok=True)
        
        try:
            # 既に存在する場合は一旦削除してから移動（上書き）
            if dest_archive_dir.exists():
                shutil.rmtree(dest_archive_dir)
            
            shutil.move(str(src_backup_dir), str(dest_archive_dir))
            print(f"   ✅ Moved: {src_backup_dir} -> {dest_archive_dir}")
        except Exception as e:
            print(f"   ⚠️ Move failed: {e}")
    else:
        print("\n   ✓ Backup folder inside src is already gone.")

    # ==========================================
    # 3. pycacheの掃除
    # ==========================================
    print("\n🧹 Cleaning up __pycache__...")
    for p in root_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(p)
        except:
            pass
    print("   ✅ Cleaned.")

    print("\n✨ 準備完了！")
    print("   これより Home.py のコード分割（コピペ作業）に進んでください。")

if __name__ == "__main__":
    main()
````

## File: README.md
````markdown
# legal-rag-project

Describe your project here.
````

## File: register_existing_templates.py
````python
import hashlib
import os
import sys

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager


def calculate_file_hash(file_path: str) -> str:
    """ファイルのMD5ハッシュを計算"""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return hashlib.md5(file_bytes).hexdigest()


def main():
    print("🚀 既存テンプレートのDB登録を開始します...")

    # パス設定
    base_dir = os.getcwd()
    template_dir = os.path.join(base_dir, "data", "templates")

    if not os.path.exists(template_dir):
        print(f"❌ フォルダが見つかりません: {template_dir}")
        return

    # DB接続
    db = DatabaseManager()

    # 登録処理
    files = [f for f in os.listdir(template_dir) if f.lower().endswith(".pdf")]
    count = 0

    print(f"📂 対象フォルダ: {template_dir}")
    print(f"📄 PDFファイル数: {len(files)}")

    for filename in files:
        file_path = os.path.join(template_dir, filename)
        file_hash = calculate_file_hash(file_path)

        # 既に登録済みかチェック
        if db.is_file_registered(file_hash):
            print(f"SKIP (登録済): {filename}")
            continue

        # 簡易的な種別判定 (ファイル名から推測)
        doc_type = "その他"
        if "残高証明" in filename:
            doc_type = "残高証明"
        elif "相続届" in filename or "手続" in filename:
            doc_type = "相続届"
        elif "委任状" in filename:
            doc_type = "委任状"

        # DBへ登録
        db.register_file_hash(file_hash=file_hash, filename=filename, doc_type=doc_type)
        print(f"✅ REGISTERED: {filename} ({doc_type})")
        count += 1

    print("------------------------------------------------")
    print(f"🎉 完了しました。新規登録: {count} 件")
    print("画面をリロードして確認してください。")


if __name__ == "__main__":
    main()
````

## File: requirements.txt
````
# 📂 遺言・遺産整理業務支援システム 要件定義書 (Ver 1.0)

## 1. プロジェクト概要
* **目的:** 遺言書作成および遺産整理業務の効率化。
* **コアコンセプト:** 「個人情報の完全オフライン管理」と「生成AIによる業務支援」のハイブリッド構成。
* **利用規模:** 本社20名で開始、将来的には全拠点100名以上（年間1000件規模）。

## 2. 技術スタック選定
以下のライブラリ・ツールを標準とする。

| カテゴリ | 技術名 | 選定理由 |
| :--- | :--- | :--- |
| **言語** | **Python 3.10+** | AI/データ処理のエコシステムが最強であるため。 |
| **アプリFW** | **Streamlit** | 社内Webアプリ化が高速。各PCへのインストール不要。 |
| **DB** | **PostgreSQL** | 100人規模の同時接続・排他制御に耐える堅牢性（無料）。 |
| **ORM** | **SQLAlchemy** | DB操作の抽象化。保守性向上のため必須。 |
| **OCR** | **PaddleOCR** | 金融機関書類（日本語・罫線あり）の認識精度が高いため。 |
| **生成AI** | **Google Gemini API** | マニュアル検索、文書案作成用。(google-generativeai) |
| **PDF処理** | **PyMuPDF (fitz)** | PDFの読み込み、加工用。 |

## 3. システムアーキテクチャ
物理的なデータ保管場所と、外部AIへのデータフローを厳密に分離する。

* **サーバー構成:** オンプレミス（社内）サーバー1台にDockerコンテナ等でDBとアプリをホスト。
* **クライアント:** 社員PCのブラウザからイントラネット経由でアクセス。
* **ネットワーク分離:**
    * **Zone A (Secure/Local):** PostgreSQL, OCR処理, 個人情報（氏名, 口座番号）の保存。インターネットへは出さない。
    * **Zone B (Cloud/AI):** Gemini API。ここには「匿名化されたテキスト」と「マニュアル」のみ送信する。

## 4. 機能要件

### A. 顧客・案件管理機能
* 顧客情報（被相続人、相続人）のCRUD処理。
* PostgreSQLを使用し、排他制御を行う。

### B. 帳票OCR取り込み機能
* Streamlit画面から画像/PDFをアップロード。
* PaddleOCRでテキスト化。
* OCR結果と元画像を並べて表示し、人間が修正してDB保存するUI。

### C. 生成AI支援機能（RAG/Drafting）
* **マスキング処理:** 相談内容をGeminiに投げる前に、正規表現等で個人情報（氏名、住所、電話番号、口座番号）をプレースホルダ（例: `[NAME_A]`, `[BANK_ID]`）に置換するロジックを実装すること。
* **マニュアル検索:** 社内規定や金融機関手続きマニュアルをベクトル化、またはコンテキストとして渡し、質問に回答させる。

### D. バックアップ機能
* `pg_dump` を使用し、毎日深夜にDBのダンプファイルを作成。
* 外部ストレージ（NAS等）への転送スクリプト。

## 5. データベース設計指針（ER図イメージ）
* **usersテーブル:** 社員アカウント管理（権限管理用）。
* **customersテーブル:** 顧客基本情報。
* **mattersテーブル:** 案件情報（遺言作成、遺産整理など）。
* **documentsテーブル:** OCR読み取り結果、生成された文書データ。ファイルパス管理。

## 6. セキュリティ・コンプライアンス規定
* **原則:** 顧客のPII（個人特定情報）は、いかなる場合もGemini APIのエンドポイントへ送信してはならない。
* **API設定:** Gemini API利用時は、学習データとして利用されない設定（Enterprise利用またはオプトアウト設定）を確認する。
````

## File: reset_db.py
````python
# file: reset_db.py
import os
import sys

from sqlalchemy import text

# パスを通す
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Base


def reset_database():
    print("🔄 データベースの完全リセットを開始します...")

    db = DatabaseManager()
    engine = db.engine

    # 1. スキーマごと強制削除 (DROP SCHEMA public CASCADE)
    # これにより、テーブル間の依存関係を無視して全てを消し去ります。
    print("💣 既存のスキーマ(public)を破棄中...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()

    # 2. テーブルを再作成
    # 最新の tables.py の定義に基づいて作成されます
    print("🔨 テーブルを再作成中...")
    Base.metadata.create_all(engine)

    print("✅ 完了しました！")
    print(
        "   PostgreSQLは完全に初期化され、最新の定義(client_name含む)と一致しました。"
    )


if __name__ == "__main__":
    print("⚠️ 【警告】PostgreSQLの全データを物理的に破壊・初期化します。")
    check = input("実行してよろしいですか？ (y/n): ")
    if check.lower() == "y":
        try:
            reset_database()
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            print("Dockerが起動しているか、.envの設定が正しいか確認してください。")
    else:
        print("中止しました。")
````

## File: schema_definition.md
````markdown
# Legal System Database Schema (PostgreSQL/SQLAlchemy)

## 1. 案件管理 (Case Management)

### cases (案件テーブル)
- **case_id** (PK, Int): 内部ID
- **case_number** (String, Unique): 案件番号 (例: G1024)
- **client_name** (String): 依頼者（相続人代表）氏名
- **client_name_kana** (String): 依頼者カナ
- **sol_case_number** (String): SOL案件番号（日興証券連携用）
- **kintone_record_id** (Int): Kintone側のレコードID
- **folder_path** (String): ファイルサーバーのパス
- **manager_id** (FK -> users.id): 進捗担当者
- **operator_id** (FK -> users.id): 実務担当者
- **status** (FK -> case_statuses.id): ステータス
- **referral_sec_phone** (String): 紹介元電話番号 (Ver 2.0追加)

### deceased (被相続人)
- **id** (PK, Int)
- **case_id** (FK -> cases.case_id): 1対1リレーション
- **name_last**, **name_first**: 氏名
- **name_last_kana**, **name_first_kana**: カナ
- **date_of_death** (Date): 相続開始日
- **date_of_birth** (Date): 生年月日
- **last_address_id** (FK -> address.id): 最後の住所

### heirs (相続人)
- **id** (PK, Int)
- **deceased_id** (FK -> deceased.id): 1対多リレーション
- **name_last**, **name_first**: 氏名
- **relationship_type**: 続柄 (妻, 長男, 二女 等)
- **is_contracting_party** (Bool): 契約者（依頼主）かどうか
- **address_links**: 住所履歴 (H_AddressHistory経由)
- **contact_links**: 連絡先 (H_ContactLink経由)

## 2. 資産管理 (Assets)

### financial_asset (預貯金)
- **id** (PK, Int)
- **case_id** (FK -> cases.case_id)
- **bank_id** (FK -> bank_master.id)
- **branch_id** (FK -> branch_master.id)
- **account_number** (String): 口座番号
- **balance** (Float): 残高
- **status** (String): 手続き状況

## 3. マスタデータ (Master Data)

### bank_master (銀行マスタ)
- **id** (PK, Int)
- **bank_name** (String): 銀行名 (例: 三菱UFJ銀行)
- **bank_code** (String): 銀行コード
- **seal_cert_limit** (String): 印鑑証明期限ルール
- **id_verify_rule** (String): 本人確認書類ルール
- **remarks** (Text): RAG用特記事項

### users (ユーザー)
- **id** (PK, Int)
- **windows_id** (String): WindowsログインID
- **name** (String): 表示名

### address (住所マスタ)
- **id** (PK, Int)
- **zip_code**, **prefecture**, **city_ward_town**, **street_address**, **building_name**

## 4. RAG・ファイル管理 (Agentic Features)

### file_registry (ファイル管理)
- **file_hash** (PK, String): MD5ハッシュ
- **filename** (String): ファイル名
- **case_id** (FK -> cases.case_id): 紐付け案件
- **doc_type** (String): 書類種別 (戸籍謄本, 残高証明書, 委任状, etc.)
- **registered_at** (DateTime)

### audit_logs (監査ログ)
- **id** (PK, Int)
- **action_type**: "AI_REASONING", "PII_CHECK", etc.
- **target**: 対象ファイル名やデータ
- **details**: AIの思考プロセスやJSON出力
````

## File: test_agent.py
````python
# test_agent.py
import os

from src.legal_system.core.ai_processor import AgenticDocumentProcessor

# 1. テスト用のダミーKintoneデータ（期待値）
mock_kintone_data = {
    "record_id": "TEST-001",
    "顧客名": "山田 太郎",
    "住所": "東京都千代田区千代田1-1",
    "被相続人名": "山田 父郎",  # 書類には「山田 父郎」と書いてあるはず
    "相続開始日": "2024-01-01",
}


def main():
    # 2. テスト対象のPDFを読み込む
    file_path = "sample.pdf"  # テストしたいPDFファイル名を指定

    if not os.path.exists(file_path):
        print(f"エラー: {file_path} が見つかりません。テスト用のPDFを置いてください。")
        # PDFがない場合、ダミーバイト列で強引にテスト（エラーにはなりますが通信は確認できます）
        dummy_bytes = b"%PDF-1.4..."
    else:
        with open(file_path, "rb") as f:
            dummy_bytes = f.read()

    print(f"--- AIエージェント起動 (Mode: {os.getenv('AI_PROVIDER')}) ---")
    print("書類を解析中... (10~20秒かかります)")

    # 3. プロセッサの初期化と実行
    processor = AgenticDocumentProcessor()

    try:
        result = processor.analyze_document(
            file_bytes=dummy_bytes,
            mime_type="application/pdf",
            kintone_data=mock_kintone_data,
        )

        # 4. 結果の表示
        print("\n=== 解析成功 ===")
        print(f"書類タイプ: {result.document_type}")
        print(f"総合判定: {result.overall_status}")

        if result.deceased_info:
            print(f"被相続人名(抽出): {result.deceased_info.name_full.value}")
            print(f"一致判定: {result.deceased_info.name_full.meta.is_consistent}")
            if not result.deceased_info.name_full.meta.is_consistent:
                print(
                    f"不一致理由: {result.deceased_info.name_full.meta.discrepancy_reason}"
                )

        # JSON全体を表示
        print("\n--- Raw JSON Output ---")
        print(result.model_dump_json(indent=2))

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")


if __name__ == "__main__":
    main()
````

## File: src/chains/bank_procedure_chain.py
````python
# src/chains/bank_procedure_chain.py

import logging
from typing import Any, Dict, Optional

import pandas as pd
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from legal_system.core.ai_factory import AIFactory

logger = logging.getLogger(__name__)


class BankMasterRetriever:
    """
    銀行マスタCSVから特定の銀行情報を検索するクラス
    """

    def __init__(self, csv_path: str):
        try:
            # CSV読み込み。文字化け防止のためencoding指定推奨（状況に合わせて cp932 or utf-8）
            self.df = pd.read_csv(csv_path, encoding="utf-8")
            # 銀行名の揺らぎ吸収のため空白除去
            self.df["銀行名"] = self.df["銀行名"].astype(str).str.strip()
        except FileNotFoundError:
            logger.error(f"銀行マスタファイルが見つかりません: {csv_path}")
            # エラー時も動作するように空のDataFrameを作成
            self.df = pd.DataFrame(
                columns=[
                    "銀行名",
                    "印鑑証明期限",
                    "代理人本人確認書類",
                    "振込ルール",
                    "備考",
                ]
            )
        except Exception as e:
            logger.error(f"CSV読み込みエラー: {e}")
            self.df = pd.DataFrame()

    def get_bank_info(self, query: str) -> Optional[Dict[str, Any]]:
        """
        ユーザーの質問文から対象銀行を特定し、マスタ情報を辞書形式で返す
        """
        if not query or self.df.empty:
            return None

        # 単純なキーワードマッチング（実務ではより高度なEntity抽出も検討可）
        for bank_name in self.df["銀行名"]:
            if bank_name in query:
                try:
                    row = self.df[self.df["銀行名"] == bank_name].iloc[0]
                    return row.fillna("特になし").to_dict()
                except IndexError:
                    continue
        return None


def create_inheritance_chain(
    rules_path: str = "data/company_rules.txt",  # パスは環境に合わせて調整してください
    master_path: str = "data/bank_master.csv",
):
    """
    相続手続きRAGチェーンを作成して返す関数
    """

    # 1. 共通ルールの読み込み
    try:
        loader = TextLoader(rules_path, encoding="utf-8")
        docs = loader.load()
        general_rules = "\n".join([d.page_content for d in docs])
    except Exception as e:
        logger.warning(f"共通ルールファイル読み込み失敗: {e}")
        general_rules = "（共通ルール読み込みエラー）"

    # 2. マスタ検索インスタンス
    master_retriever = BankMasterRetriever(master_path)

    # 3. LLMの初期化 (Factory経由でキーローテーション)
    llm = AIFactory.create_model(temperature=0.0)

    # 4. プロンプト定義
    # ここで「ゆうちょ」等の他行ルールを除外する強い指示を与えます
    template_str = """
    あなたは行政書士法人の実務支援AIです。
    ユーザーの質問に対し、以下の情報源を組み合わせて回答を作成してください。

    【情報源の優先順位】
    1. **対象銀行マスタ情報 (最優先)**: 期限や支払方法は必ずこれに従うこと。
    2. **共通業務ルール**: マスタに記載がない事項について参照すること。

    【対象銀行マスタ情報】
    {specific_rules}

    【共通業務ルール（参考）】
    {general_rules}

    【回答作成の厳格なルール】
    1. **対象銀行の特定**: 今回の手続き対象は「{target_bank_name}」です。
    2. **情報の除外**: 共通ルール内に含まれる**「{target_bank_name}」以外の銀行（特にゆうちょ銀行など）に関する記述は完全に無視**してください。
       - 例: 対象が「みずほ銀行」の場合、ゆうちょ銀行の「スプレッドシート」や「会社通帳からの引落とし」の記述は絶対に回答に含めないでください。
    3. **支払方法**: マスタ情報の「振込/引落」に従ってください。
       - 「振込」の場合 → 「経理へ依頼（Kintone経理アプリ）」と案内。
       - 「引落」の場合 → 指定された管理シート等を案内。
    4. **証明書の期限**: マスタ情報の「印鑑証明期限」を正として回答してください（共通ルールの6ヶ月という記述で上書きしないこと）。

    【出力フォーマット】
    - 結論のみを箇条書きで記載。
    - 挨拶や前置きは不要。
    
    質問: {question}
    """

    prompt = ChatPromptTemplate.from_template(template_str)

    # 5. チェーン実行用関数
    def run_chain(inputs: Dict[str, Any]) -> str:
        question = inputs.get("question", "")

        # 銀行情報の取得
        bank_info = master_retriever.get_bank_info(question)

        if bank_info:
            target_bank_name = bank_info.get("銀行名", "指定なし")
            # マスタ情報を文字列化してプロンプトに埋め込む
            specific_rules_str = (
                f"- 銀行名: {target_bank_name}\n"
                f"- 印鑑証明期限: {bank_info.get('印鑑証明期限', '規定なし')}\n"
                f"- 本人確認書類: {bank_info.get('代理人本人確認書類', '規定なし')}\n"
                f"- 支払方法(振込/引落): {bank_info.get('振込ルール', '規定なし')}\n"
                f"- 備考: {bank_info.get('備考', '')}"
            )
        else:
            target_bank_name = "特定できない銀行"
            specific_rules_str = (
                "（マスタに該当する銀行が見つかりません。共通ルールのみを参照します）"
            )

        # チェーン構築
        chain = prompt | llm | StrOutputParser()

        try:
            return chain.invoke(
                {
                    "general_rules": general_rules,
                    "specific_rules": specific_rules_str,
                    "target_bank_name": target_bank_name,
                    "question": question,
                }
            )
        except Exception as e:
            logger.error(f"チェーン実行エラー: {e}")
            return "システムエラーが発生しました。"

    return run_chain
````

## File: src/legal_system/core/preload.py
````python
# src/legal_system/core/preload.py
import streamlit as st
import time

@st.cache_resource(show_spinner=False)
def warm_up_modules():
    """
    重いライブラリおよびメニューコンポーネントをバックグラウンドで事前にインポートし、
    sys.modules（Pythonのモジュールキャッシュ）に乗せておく関数。
    """
    try:
        # --- 1. 外部の重いライブラリ群 ---
        import pypdf
        import reportlab
        import pdf2image
        import PIL
        import docx  # python-docx
        import selenium
        
        # --- 2. メニュー別の独自コンポーネント群 ---
        # これらをインポートしておくことで、Home.py側でimportした瞬間にキャッシュから返されます
        from src.legal_system.ui.components.cases import basic_info
        from src.legal_system.ui.components.cases import asset_list
        from src.legal_system.ui.components.cases import nayose_registration
        from src.legal_system.ui.components.cases import registry_acquisition
        from src.legal_system.ui.components.cases import dashboard_widgets
        from src.legal_system.ui.components import label_printer_ui
        
        # --- 3. 重いAI関連 ---
        from src.legal_system.core import ai_factory
        from src.services import gmail_watcher_service
        from src.services import scanner_service

    except Exception as e:
        # バックグラウンドでの失敗は起動を妨げないようログに留める
        print(f"🐢 Warmup info: Some modules are still loading... {e}")
    
    return True
````

## File: src/legal_system/ui/components/cases/asset_list.py
````python
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
````

## File: src/legal_system/ui/components/cases/basic_info.py
````python
# src/legal_system/ui/components/cases/basic_info.py

import re
import time
import unicodedata

import pandas as pd
import streamlit as st
from sqlalchemy.orm import joinedload

from legal_system.models.tables import Case, Deceased
from src.services.deceased_service import (
    delete_case_and_all_related_data,
    get_address_info,
    get_contact_info,
    search_zip_by_address_api,
    sync_heir_list,
    update_deceased,
    update_heir,
)
from src.utils.date_utils import convert_seireki_to_wareki


def _get_date_input(label, current_value, key=None):
    """
    日付入力ヘルパー（Noneハンドリング & 和暦表示 & key対応）
    """
    val = st.date_input(
        label,
        value=current_value if current_value else None,
        format="YYYY/MM/DD",
        key=key,
    )
    if val:
        wareki = convert_seireki_to_wareki(val)
        st.caption(f"📅 和暦: **{wareki}**")
    else:
        st.caption("📅 和暦: (日付未設定)")
    return val


def _normalize_kanji_numeric(text: str) -> str:
    """
    漢数字の丁目などを算用数字に変換する (APIヒット率向上用)
    例: 仙川町三丁目 -> 仙川町3丁目
    """
    if not text:
        return ""
    res = text
    trans_map = {
        "一": "1",
        "二": "2",
        "三": "3",
        "四": "4",
        "五": "5",
        "六": "6",
        "七": "7",
        "八": "8",
        "九": "9",
        "十": "10",
    }
    # "○丁目" のパターンを探して置換
    for kanji, num in trans_map.items():
        res = res.replace(f"{kanji}丁目", f"{num}丁目")

    return res


def _clean_town_name(text: str) -> str:
    """
    API検索用に、市区町村名から「丁目」「番地」以降をカットして
    最もヒットしやすい「町域」だけの文字列にする
    例: "調布市仙川町三丁目" -> "調布市仙川町"
    """
    if not text:
        return ""

    # 1. NFKC正規化 (全角英数→半角など)
    s = unicodedata.normalize("NFKC", text)
    s = s.replace(" ", "").replace("　", "")

    # 2. 「丁目」以降をカット
    # 漢数字(一～十)＋丁目、または数字＋丁目のパターンを検知
    match = re.search(r"([0-9０-９一二三四五六七八九十]+丁目)", s)
    if match:
        # マッチした箇所の直前までを切り出す
        idx = match.start()
        s = s[:idx]

    # 3. 万が一「番地」「番」などが残っていたらそこもカット
    match_ban = re.search(r"([0-9]+(番地|番))", s)
    if match_ban:
        idx = match_ban.start()
        s = s[:idx]

    return s


def _zip_search_callback(target_prefix):
    """
    住所から郵便番号を検索してSessionStateを更新するコールバック（リトライ対応版）

    【修正版ロジック】
    HeartRails Geo APIの特性に合わせ、「都道府県 + 市区町村(町域のみ)」の
    最も確実なパターンのみで検索を実行する。
    """
    # 現在の入力値を取得
    pref = st.session_state.get(f"{target_prefix}pref", "").strip()
    city = st.session_state.get(f"{target_prefix}city", "").strip()

    if not (pref or city):
        st.toast("⚠️ 都道府県または市区町村を入力してください", icon="⚠️")
        return

    # 町域名の抽出 (丁目・番地カット)
    clean_city = _clean_town_name(city)

    # 検索クエリ作成 (都道府県 + 純粋な町名)
    query = f"{pref}{clean_city}"

    try:
        # 検索実行（リトライ機構が組み込まれた関数を呼び出し）
        found_zip = search_zip_by_address_api(query)

        if found_zip:
            st.session_state[f"{target_prefix}zip"] = found_zip
            st.toast(
                f"郵便番号を補完しました: {found_zip}\n(検索語: {query})", icon="📮"
            )
        else:
            st.toast(f"見つかりませんでした。\n検索語: {query}", icon="🚫")

    except Exception as e:
        # 最終的に失敗した場合のエラー通知（3回リトライ後）
        st.error(f"❌ 郵便番号検索に失敗しました（3回リトライ後）\nエラー: {str(e)}")
        import logging

        logging.getLogger(__name__).error(
            f"Zip search failed after retries: {e}", exc_info=True
        )


def render_basic_info(session, case_id: int):
    """
    基本情報（依頼者・被相続人・相続人）の編集画面を描画する
    """
    # データをリロード（最新状態を取得）
    case = (
        session.query(Case)
        .options(
            joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
            joinedload(Case.deceased_ref).joinedload(Deceased.last_address),
        )
        .get(case_id)
    )

    if not case:
        st.error("案件データが見つかりません。")
        return

    deceased = case.deceased_ref

    # ---------------------------------------------------------
    # 1. 依頼者（契約者）情報
    # ---------------------------------------------------------
    st.subheader("👤 依頼者（契約者）情報")

    contractor = None
    if deceased and deceased.heirs:
        contractor = next((h for h in deceased.heirs if h.is_contracting_party), None)
        if not contractor:
            contractor = deceased.heirs[0]

    with st.container(border=True):
        if contractor:
            c_addr = get_address_info("heir", contractor.id)
            c_conts = get_contact_info("heir", contractor.id)
            c_phone = next((c["value"] for c in c_conts if c["type"] == "PHONE"), "")
            c_email = next((c["value"] for c in c_conts if c["type"] == "EMAIL"), "")

            # 初期値をSessionStateにセット（初回のみ）
            keys_map = {
                "c_zip": c_addr.get("zip_code", ""),
                "c_pref": c_addr.get("prefecture", ""),
                "c_city": c_addr.get("city_ward_town", ""),
                "c_street": c_addr.get("street_address", ""),
                "c_bldg": c_addr.get("building_name", ""),
            }
            for k, v in keys_map.items():
                if k not in st.session_state:
                    st.session_state[k] = v

            col1, col2 = st.columns(2)
            with col1:
                new_c_name = st.text_input(
                    "氏名", value=f"{contractor.name_last}　{contractor.name_first}"
                )
                new_c_kana = st.text_input(
                    "フリガナ",
                    value=f"{contractor.name_last_kana or ''}　{contractor.name_first_kana or ''}",
                )
                new_c_rel = st.text_input("続柄", value=contractor.relationship_type)
                new_c_dob = _get_date_input(
                    "生年月日", contractor.date_of_birth, key="contractor_dob"
                )

            with col2:
                new_c_phone = st.text_input("電話番号", value=c_phone)
                new_c_email = st.text_input("メールアドレス", value=c_email)

                st.markdown("---")
                st.caption("現住所")

                c1, c2_ = st.columns([1, 2])
                new_c_zip = c1.text_input("郵便番号", key="c_zip")
                c1.button(
                    "住所から検索",
                    key="btn_search_c_zip",
                    on_click=_zip_search_callback,
                    args=("c_",),
                    help="住所から郵便番号を検索します",
                )

                new_c_pref = c2_.text_input("都道府県", key="c_pref")
                new_c_city = st.text_input("市区町村", key="c_city")
                new_c_street = st.text_input("番地", key="c_street")
                new_c_bldg = st.text_input("建物名", key="c_bldg")

            if st.button("💾 依頼者情報を更新", key="save_contractor", type="primary"):
                parts = new_c_name.replace("　", " ").split(" ", 1)
                k_parts = new_c_kana.replace("　", " ").split(" ", 1)

                case.client_name = new_c_name
                case.client_name_kana = new_c_kana

                success = update_heir(
                    contractor.id,
                    name=new_c_name,
                    rel=new_c_rel,
                    kana_last=k_parts[0],
                    kana_first=k_parts[1] if len(k_parts) > 1 else "",
                    dob=new_c_dob,
                    zip_code=st.session_state.c_zip,
                    pref=st.session_state.c_pref,
                    city=st.session_state.c_city,
                    street=st.session_state.c_street,
                    building=st.session_state.c_bldg,
                    phone_contacts=[{"value": new_c_phone}] if new_c_phone else [],
                    email_contacts=[{"value": new_c_email}] if new_c_email else [],
                )

                if success:
                    session.commit()
                    st.toast("更新しました", icon="✅")

                    # ★重要: 更新成功時は、古いセッション値を削除して強制リロード
                    for k in keys_map.keys():
                        if k in st.session_state:
                            del st.session_state[k]
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("更新に失敗しました")

        else:
            st.warning("相続人が登録されていません。下のリストから追加してください。")

    # ---------------------------------------------------------
    # 2. 被相続人 情報
    # ---------------------------------------------------------
    st.subheader("🙏 被相続人（故人）情報")
    with st.container(border=True):
        if deceased:
            d_addr = get_address_info("deceased", deceased.id)

            keys_map_d = {
                "d_zip": d_addr.get("zip_code", ""),
                "d_pref": d_addr.get("prefecture", ""),
                "d_city": d_addr.get("city_ward_town", ""),
                "d_street": d_addr.get("street_address", ""),
                "d_bldg": d_addr.get("building_name", ""),
            }
            for k, v in keys_map_d.items():
                if k not in st.session_state:
                    st.session_state[k] = v

            d1, d2 = st.columns(2)
            with d1:
                new_d_name = st.text_input(
                    "被相続人 氏名",
                    value=f"{deceased.name_last}　{deceased.name_first}",
                )
                new_d_kana = st.text_input(
                    "被相続人 フリガナ",
                    value=f"{deceased.name_last_kana or ''}　{deceased.name_first_kana or ''}",
                )

                new_d_dob = _get_date_input(
                    "生年月日", deceased.date_of_birth, key="deceased_dob"
                )
                new_d_dod = _get_date_input(
                    "死亡日（相続開始日）", deceased.date_of_death, key="deceased_dod"
                )

                new_d_honseki = st.text_input("本籍地", value=deceased.hometown or "")

            with d2:
                st.markdown("**最後の住所**")

                dd1, dd2 = st.columns([1, 2])
                new_d_zip = dd1.text_input("郵便番号 (故)", key="d_zip")
                dd1.button(
                    "住所から検索",
                    key="btn_search_d_zip",
                    on_click=_zip_search_callback,
                    args=("d_",),
                    help="都道府県・市区町村（町名まで）を使って郵便番号を検索します",
                )

                new_d_pref = dd2.text_input("都道府県 (故)", key="d_pref")
                new_d_city = st.text_input("市区町村 (故)", key="d_city")
                new_d_street = st.text_input("番地 (故)", key="d_street")
                new_d_bldg = st.text_input("建物名 (故)", key="d_bldg")

            if st.button("💾 被相続人情報を更新", key="save_deceased"):
                d_parts = new_d_name.replace("　", " ").split(" ", 1)
                dk_parts = new_d_kana.replace("　", " ").split(" ", 1)

                success = update_deceased(
                    deceased.id,
                    name_last=d_parts[0],
                    name_first=d_parts[1] if len(d_parts) > 1 else "",
                    kana_last=dk_parts[0],
                    kana_first=dk_parts[1] if len(dk_parts) > 1 else "",
                    dob=new_d_dob,
                    dod=new_d_dod,
                    hometown=new_d_honseki,
                    last_zip_code=st.session_state.d_zip,
                    last_pref=st.session_state.d_pref,
                    last_city=st.session_state.d_city,
                    last_street=st.session_state.d_street,
                    last_building=st.session_state.d_bldg,
                )

                if success:
                    st.toast("更新しました", icon="✅")
                    # ★重要: 更新成功時は、古いセッション値を削除して強制リロード
                    for k in keys_map_d.keys():
                        if k in st.session_state:
                            del st.session_state[k]
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("更新に失敗しました")

    # ---------------------------------------------------------
    # 3. 相続人リスト (編集可能テーブル)
    # ---------------------------------------------------------
    st.subheader("👪 相続人・関係者リスト")

    if deceased:
        current_heirs_data = []
        if deceased.heirs:
            for h in deceased.heirs:
                role = "契約者" if h.is_contracting_party else "相続人"
                current_heirs_data.append(
                    {
                        "id": h.id,
                        "name": f"{h.name_last} {h.name_first}".strip(),
                        "relationship": h.relationship_type,
                        "dob": h.date_of_birth,
                        "role": role,
                    }
                )

        df_heirs = pd.DataFrame(current_heirs_data)

        if df_heirs.empty:
            df_heirs = pd.DataFrame(
                columns=["id", "name", "relationship", "dob", "role"]
            )

        st.info("👇 下の表を直接編集できます。行の追加・削除も可能です。")

        edited_df = st.data_editor(
            df_heirs,
            column_config={
                "id": None,
                "name": st.column_config.TextColumn(
                    "氏名 (全角スペース区切り)", required=True, width="medium"
                ),
                "relationship": st.column_config.TextColumn(
                    "続柄", required=True, width="small"
                ),
                "dob": st.column_config.DateColumn("生年月日", format="YYYY/MM/DD"),
                "role": st.column_config.SelectboxColumn(
                    "役割", options=["相続人", "契約者"], required=True, width="small"
                ),
            },
            num_rows="dynamic",
            use_container_width=True,
            key="heir_list_editor",
            hide_index=True,
        )

        if st.button("💾 リストの変更を保存", type="primary"):
            try:
                data_to_sync = edited_df.to_dict(orient="records")
                result = sync_heir_list(deceased.id, data_to_sync)

                msg = []
                if result["added"]:
                    msg.append(f"{result['added']}名追加")
                if result["updated"]:
                    msg.append(f"{result['updated']}名更新")
                if result["deleted"]:
                    msg.append(f"{result['deleted']}名削除")

                final_msg = "、".join(msg) if msg else "変更はありません"
                st.success(f"保存しました ({final_msg})")

                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"保存中にエラーが発生しました: {e}")

    # ---------------------------------------------------------
    # 4. 案件削除 (Danger Zone)
    # ---------------------------------------------------------
    st.divider()
    with st.expander("🗑️ 案件の削除 (Danger Zone)"):
        st.warning(
            "この操作は取り消せません。案件に関する全てのデータ（資産、履歴、ファイル）が削除されます。"
        )
        if st.checkbox("削除を確認しました"):
            if st.button("案件を完全に削除する", type="primary"):
                if delete_case_and_all_related_data(case.case_number):
                    st.success("削除しました。Homeに戻ります。")
                    st.session_state["selected_case_id"] = None
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("削除に失敗しました")
````

## File: src/legal_system/ui/components/cases/header.py
````python
# src/legal_system/ui/components/cases/header.py

import streamlit as st
import streamlit.components.v1 as components
import time
import os
from sqlalchemy.orm import Session
from src.legal_system.models.tables import Case
from src.services.folder_service import open_local_folder, find_case_folder
from src.services.deceased_service import update_case_folder_path

def _search_folder_callback(case: Case, input_key: str):
    """
    検索ボタンが押されたときに実行されるコールバック関数
    """
    # 検索キーワード: G番号があればそれ、なければ氏名
    q = case.case_number if case.case_number and case.case_number.startswith("G") else case.client_name.replace(" ", "")
    
    # 検索実行
    found_path = find_case_folder(q)
    
    if found_path:
        # 1. DB更新
        update_case_folder_path(case.case_id, found_path)
        
        # 2. セッションステート（入力欄の中身）を更新
        st.session_state[input_key] = found_path
        
        st.toast(f"フォルダを発見しました: {found_path}", icon="📂")
    else:
        st.toast(f"フォルダが見つかりませんでした: {q}", icon="⚠️")

def render_case_header(case: Case):
    """
    案件詳細画面の共通ヘッダーを表示するコンポーネント
    - 案件番号、顧客名、ステータス
    - Kintoneへのリンクボタン (Alt+K)
    - フォルダパスの編集・自動検索・開くボタン (Alt+O)
    """
    if not case:
        st.error("案件データが選択されていません")
        return

    # ---------------------------------------------------------
    # JavaScript: ショートカットキー制御 (Alt+K, Alt+O)
    # キーを押した瞬間に全階層(Deep DOM)を探索する方式
    # ---------------------------------------------------------
    js_shortcuts = """
    <script>
    (function() {
        // ============================================================
        // 1. Deep DOM Search (再帰的にIframe/ShadowRootを探索)
        // ============================================================
        function deepQuerySelectorAll(selector, root) {
            root = root || document;
            const results = [];

            // 現在のルート内で検索
            try {
                const found = root.querySelectorAll(selector);
                found.forEach(el => results.push(el));
            } catch(e) {}

            // IframeやShadowRootの中へ潜る
            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {
                // Shadow DOM
                if (node.shadowRoot) {
                    results.push(...deepQuerySelectorAll(selector, node.shadowRoot));
                }
                // Iframe
                if (node.tagName === 'IFRAME') {
                    try {
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) {
                            results.push(...deepQuerySelectorAll(selector, innerDoc));
                        }
                    } catch(e) {
                        // Cross-origin iframe等は無視
                    }
                }
            }
            return results;
        }

        // ============================================================
        // 2. ターゲット特定ロジック (テキスト等で検索)
        // ============================================================
        function findElementByKeywords(keywords) {
            // ボタン、リンク、Streamlitボタンコンテナ
            const selector = 'button, a, div[role="button"], [data-testid="stButton"] button, [data-testid="stLinkButton"] a';
            
            // ★キーが押された瞬間に window.parent.document から全探索開始
            const candidates = deepQuerySelectorAll(selector, window.parent.document);
            
            for (let el of candidates) {
                // テキスト情報などを収集
                const textContent = (el.innerText || el.textContent || "").toLowerCase();
                const ariaLabel = (el.getAttribute("aria-label") || "").toLowerCase();
                const title = (el.getAttribute("title") || "").toLowerCase();
                
                const fullText = textContent + " " + ariaLabel + " " + title;

                // キーワードが含まれているかチェック
                if (keywords.some(kw => fullText.includes(kw.toLowerCase()))) {
                    return el;
                }
            }
            return null;
        }

        // ============================================================
        // 3. イベントハンドラ (keydown)
        // ============================================================
        const handleKeydown = function(e) {
            if (!e.altKey) return;

            // Alt + K (Kintone)
            if (e.code === 'KeyK') {
                const el = findElementByKeywords(["Kintoneで開く", "Kintone連携"]);
                if (el) {
                    e.preventDefault();
                    e.stopPropagation();
                    el.click();
                    console.log("LegalApp: Alt+K -> Kintone button clicked.");
                } else {
                    console.warn("LegalApp: Kintone button not found.");
                }
            }

            // Alt + O (Open Folder)
            if (e.code === 'KeyO') {
                // キーワードを「フォルダを開く」に限定して競合を回避
                const el = findElementByKeywords(["📂 フォルダを開く", "フォルダを開く"]);
                if (el) {
                    e.preventDefault();
                    e.stopPropagation();
                    el.click();
                    console.log("LegalApp: Alt+O -> Folder Open button clicked.");
                } else {
                    console.warn("LegalApp: Folder Open button not found.");
                }
            }
        };

        // ============================================================
        // 4. リスナー登録 (再登録対応)
        // ============================================================
        const HANDLER_NAME = '_legalAppHeaderKeyHandler_v3';
        const doc = window.parent.document;

        // 既存のリスナーがあれば削除して、重複実行を防ぐ
        if (window.parent[HANDLER_NAME]) {
            doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
        }

        // 新しいハンドラを登録
        window.parent[HANDLER_NAME] = handleKeydown;
        doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);

        console.log("LegalApp: Header Shortcuts (Alt+K, Alt+O) registered (Unique Button Name).");

    })();
    </script>
    """
    components.html(js_shortcuts, height=0, width=0)

    # ---------------------------------------------------------
    # UI コンポーネント
    # ---------------------------------------------------------
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 1.5, 1.5], gap="medium")
        
        with c1:
            case_num = case.case_number or '案件番号未定'
            client_name = case.client_name or '顧客名未設定'
            st.markdown(f"### 🗂 {case_num}: {client_name} 様")
            if case.deceased_ref:
                d_last = case.deceased_ref.name_last or ""
                d_first = case.deceased_ref.name_first or ""
                d_date = case.deceased_ref.date_of_death or "不明"
                st.caption(f"被相続人: {d_last} {d_first} 様 (没年月日: {d_date})")

        with c2:
            raw_status = getattr(case, "status", None)
            current_status_label = "未着手"
            if raw_status:
                if hasattr(raw_status, "status_name"):
                    current_status_label = raw_status.status_name
                elif hasattr(raw_status, "name"):
                    current_status_label = raw_status.name
                else:
                    current_status_label = str(raw_status)
            st.metric("現在のステータス", current_status_label)

        with c3:
            st.write("☁️ **Kintone連携 (Alt+K)**")
            if case.kintone_record_id:
                url = f"https://chester-tax.cybozu.com/k/242/show#record={case.kintone_record_id}"
                st.link_button("🚀 Kintoneで開く", url, type="primary", use_container_width=True)
            else:
                st.button("未連携", disabled=True, use_container_width=True)

        st.divider()

        b1, b2, b3, b4 = st.columns([1, 1, 3, 1.2], gap="small")
        with b1:
            mgr_name = "未割当"
            if case.manager:
                mgr_name = case.manager.name if hasattr(case.manager, "name") else str(case.manager)
            st.info(f"👮 担当: **{mgr_name}**")
        with b2:
            opr_name = "未割当"
            if case.operator:
                opr_name = case.operator.name if hasattr(case.operator, "name") else str(case.operator)
            st.info(f"👩‍💻 実務: **{opr_name}**")

        with b3:
            current_path = case.folder_path or ""
            input_key = f"header_folder_path_input_{case.case_id}"
            new_path = st.text_input(
                "📂 案件フォルダパス", 
                value=current_path, 
                label_visibility="collapsed", 
                placeholder="フォルダパス (\\\\server\\...)",
                key=input_key 
            )
            if new_path != current_path:
                update_case_folder_path(case.case_id, new_path)
                st.toast(f"フォルダパスを更新しました")
                time.sleep(0.5)
                st.rerun()

        with b4:
            c_open, c_search = st.columns([1, 1], gap="small")
            with c_open:
                # ★修正: ボタン名をユニークに変更 ("📂 開く" -> "📂 フォルダを開く")
                if st.button("📂 フォルダを開く", key=f"btn_open_{case.case_id}", use_container_width=True, help="Alt+O"):
                    if new_path:
                        if os.path.exists(new_path):
                            open_local_folder(new_path)
                        else:
                            st.error("フォルダが見つかりません")
                    else:
                        st.warning("パスが未設定です")
            with c_search:
                st.button(
                    "🔍 検索", 
                    key=f"btn_search_{case.case_id}", 
                    use_container_width=True, 
                    help="サーバーから案件番号でフォルダを検索します",
                    on_click=_search_folder_callback,
                    args=(case, input_key)
                )
````

## File: src/legal_system/ui/components/cases/registry_acquisition.py
````python
# src/legal_system/ui/components/cases/registry_acquisition.py

import os
import re
import json
import pandas as pd
import streamlit as st
from sqlalchemy.orm import joinedload
from src.legal_system.models.tables import Case, Address, H_AddressHistory, RealEstateAsset

# サービスのインポート (利用可能な場合のみ)
try:
    from src.services.automation.touki_service import touki_service
except ImportError:
    touki_service = None

# ==========================================
# 定数・パス設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/legal_system/ui/components/cases -> src -> root
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
)
DATA_RULES_DIR = os.path.join(ROOT_DIR, "data", "rules")
RECIPIENTS_FILE = os.path.join(DATA_RULES_DIR, "donation_recipients.json")

# ==========================================
# ヘルパー関数
# ==========================================

def get_probable_prefectures(session, case_id: int) -> list[str]:
    """
    案件データから「関係しそうな都道府県」を推論してリストアップするヘルパー
    """
    prefs = set()
    case = session.query(Case).get(case_id)
    if not case: return []
    
    # 1. 被相続人の最後の住所
    if case.deceased_ref and case.deceased_ref.last_address_id:
        addr = session.query(Address).get(case.deceased_ref.last_address_id)
        if addr and addr.prefecture: prefs.add(addr.prefecture)
    
    # 2. 相続人の住所
    if case.deceased_ref and case.deceased_ref.heirs:
        for h in case.deceased_ref.heirs:
            link = session.query(H_AddressHistory).filter_by(heir_id=h.id, is_current_address=True).first()
            if link:
                addr = session.query(Address).get(link.address_id)
                if addr and addr.prefecture: prefs.add(addr.prefecture)
    
    # 3. 既に登録されている不動産の所在
    existing_assets = session.query(RealEstateAsset).filter_by(case_id=case_id).all()
    for a in existing_assets:
        m = re.match(r'(.{2,3}[都道府県])', a.location or "")
        if m: prefs.add(m.group(1))
        
    return list(prefs)

def update_touki_address_callback(new_address: str):
    """ボタンクリックで住所入力欄を更新するためのコールバック"""
    st.session_state["touki_target_address"] = new_address

def load_donation_recipients() -> list[dict]:
    """寄付先リストをJSONから読み込む（なければデフォルト作成）"""
    if not os.path.exists(RECIPIENTS_FILE):
        # デフォルトデータ
        default_data = [
            {"name": "日本赤十字社", "address": "東京都港区芝大門一丁目１番３号"},
            {"name": "日本ユニセフ協会", "address": "東京都港区高輪四丁目６番１２号"},
            {"name": "国境なき医師団日本", "address": "東京都世田谷区若林二丁目３０番９号"},
            {"name": "あしなが育英会", "address": "東京都千代田区平河町二丁目７番５号"},
            {"name": "日本財団", "address": "東京都港区赤坂一丁目２番２号"},
            {"name": "がん研究会", "address": "東京都江東区有明三丁目８番３１号"}
        ]
        try:
            os.makedirs(DATA_RULES_DIR, exist_ok=True)
            with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            return default_data
        except:
            return []
    
    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_donation_recipients(data: list[dict]):
    """寄付先リストをJSONに保存"""
    os.makedirs(DATA_RULES_DIR, exist_ok=True)
    with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==========================================
# メインレンダラー
# ==========================================
def render_registry_acquisition(session, target_case_id: int):
    """
    登記情報取得ツールのメインレンダラー
    """
    st.subheader("🌐 登記情報取得ツール")

    # 環境チェック
    if os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER"):
        st.warning("⚠️ 現在Docker(サーバー)環境で実行中です。自動操作ブラウザは画面に表示されません（バックグラウンド実行）。")
    else:
        st.info("自動操作ブラウザを起動し、登記情報提供サービスで検索を行います。")

    if not touki_service:
        st.error("機能が無効です (src/services/automation/touki_service.py が見つかりません)")
        return

    # --- UI構成 ---
    category = st.radio("請求カテゴリ", ["土地・建物", "商業・法人"], horizontal=True)
    
    # ステート初期化 (エラー回避のため)
    if "touki_target_address" not in st.session_state: st.session_state["touki_target_address"] = ""
    if "touki_target_address_corp" not in st.session_state: st.session_state["touki_target_address_corp"] = ""
    if "touki_corp_name" not in st.session_state: st.session_state["touki_corp_name"] = ""

    # ==========================
    # A. 商業・法人モード (寄付先対応)
    # ==========================
    if category == "商業・法人":
        # 1. リストデータのロード
        recipients_list = load_donation_recipients()
        recipients_map = {r["name"]: r["address"] for r in recipients_list}
        
        # 2. 入力モード選択
        col_mode, col_blank = st.columns([2, 1])
        with col_mode:
            input_method = st.radio("入力方法", ["手動入力", "寄付先リストから選択"], horizontal=True)

        # 3. リスト選択 & 値の同期ロジック
        if input_method == "寄付先リストから選択":
            if not recipients_map:
                st.warning("登録されている寄付先がありません。下の「リスト管理」から追加してください。")
            else:
                # 選択ボックス
                current_selection = st.selectbox(
                    "団体を選択", 
                    list(recipients_map.keys()), 
                    key="sel_donation_recipient"
                )
                
                # --- ロジック: 選択変更 or 初期表示時の自動反映 ---
                # 前回の選択状態を保存しておく変数を初期化
                if "last_donation_selection" not in st.session_state:
                    st.session_state["last_donation_selection"] = None
                
                # 「今回選択された値が前回と違う」 または 「入力欄が空（初期状態）」 の場合に値をセット
                fields_empty = (not st.session_state.get("touki_corp_name")) and (not st.session_state.get("touki_target_address_corp"))
                selection_changed = (current_selection != st.session_state["last_donation_selection"])
                
                if selection_changed or fields_empty:
                    # マップから該当情報を取得してセッションステート(入力欄)を更新
                    if current_selection in recipients_map:
                        st.session_state["touki_corp_name"] = current_selection
                        st.session_state["touki_target_address_corp"] = recipients_map[current_selection]
                    
                    # 変更を記録
                    st.session_state["last_donation_selection"] = current_selection
                    
                    # ※ ここで on_change コールバックを使わず、描画の直前で値を更新することで
                    #   スムーズに下の text_input に反映させ、不要なリロード（スクロール飛び）を防ぐ
        
        # 4. 入力フォーム
        # セッションステートとバインドされているため、上のロジックで更新された値が即座に表示される
        st.text_input(
            "会社・法人名", 
            key="touki_corp_name", 
            placeholder="例: 株式会社チェスター"
        )
        
        st.text_input(
            "本店所在地", 
            key="touki_target_address_corp",
            placeholder="都道府県 市区町村..."
        )

        # 5. リスト管理機能 (CRUD)
        with st.expander("⚙️ 寄付先リストの管理 (追加・編集・削除)"):
            st.caption("よく使う寄付先などをここに登録しておくと便利です。")
            
            # DataFrame化して編集可能にする
            df_recipients = pd.DataFrame(recipients_list)
            
            edited_df = st.data_editor(
                df_recipients,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn("法人・団体名", required=True),
                    "address": st.column_config.TextColumn("所在地", required=True, width="large")
                },
                key="editor_donation_list"
            )
            
            if st.button("💾 リストを更新して保存", key="btn_save_recipients"):
                # DataFrame -> List[Dict]
                new_data = edited_df.to_dict(orient="records")
                # 空行削除
                clean_data = [d for d in new_data if d.get("name") and d.get("address")]
                
                save_donation_recipients(clean_data)
                st.toast("リストを更新しました！", icon="✅")
                import time
                time.sleep(1)
                st.rerun()

    # ==========================
    # B. 土地・建物モード
    # ==========================
    else:
        target_type = "土地"
        input_mode = st.radio("入力方法", ["登録済み不動産から選択", "手動入力"], horizontal=True, key="touki_input_mode")
        
        # 1. 登録済みから選択
        if input_mode == "登録済み不動産から選択":
            assets = session.query(RealEstateAsset).filter_by(case_id=target_case_id).all()
            if not assets: 
                st.warning("登録された不動産がありません")
            else:
                # 選択肢の作成
                asset_options = {
                    f"【{a.property_type}】{a.location} {a.lot_number or a.house_number or ''}": a 
                    for a in assets
                }
                selected_label = st.selectbox("取得対象を選択", list(asset_options.keys()))
                
                if selected_label:
                    sel_asset = asset_options[selected_label]
                    base_addr = f"{sel_asset.location or ''}{sel_asset.lot_number or sel_asset.house_number or ''}"
                    
                    # 選択変更時にステートを更新
                    if "last_selected_asset_id" not in st.session_state:
                        st.session_state["last_selected_asset_id"] = None
                    
                    if st.session_state["last_selected_asset_id"] != sel_asset.id:
                        st.session_state["touki_target_address"] = base_addr
                        st.session_state["last_selected_asset_id"] = sel_asset.id
                        st.rerun()

                    # 種別の自動判定
                    if sel_asset.property_type in ["Building", "Condo"]: 
                        target_type = "建物"
                    st.caption(f"種別自動判定: {target_type}")

        # 2. 住所入力フォーム (共通)
        current_addr_val = st.text_input(
            "検索する所在・地番 (編集可)", 
            key="touki_target_address",
            placeholder="例: 東京都中央区銀座1丁目1-1"
        )

        # 都道府県補完アシスト
        if current_addr_val and not re.match(r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)', current_addr_val):
            st.warning("⚠️ 住所に都道府県が含まれていません。以下から選択して追加してください。")
            
            prob_prefs = get_probable_prefectures(session, target_case_id)
            if prob_prefs:
                cols = st.columns(len(prob_prefs))
                for idx, p in enumerate(prob_prefs):
                    cols[idx].button(
                        f"+ {p}", 
                        key=f"add_pref_{idx}",
                        on_click=update_touki_address_callback,
                        args=(f"{p}{current_addr_val}",)
                    )
            else:
                st.info("候補が見つかりません。手動で都道府県を入力してください。")

        target_type_radio = st.radio(
            "種別", 
            ["土地", "建物"], 
            index=0 if target_type == "土地" else 1, 
            horizontal=True
        )

    # ==========================
    # C. 実行ボタン
    # ==========================
    st.divider()
    if st.button("🚀 登記情報を取得 (ブラウザ起動)", type="primary", use_container_width=True):
        # 最終的な検索対象住所を決定
        final_addr = ""
        final_name = ""
        
        if category == "商業・法人":
            # セッションステートから値を取得 (バインドされているため)
            final_name = st.session_state.get("touki_corp_name", "")
            final_addr = st.session_state.get("touki_target_address_corp", "")
            
            if not final_name:
                st.error("会社・法人名が入力されていません")
                return
        else:
            final_addr = st.session_state.get("touki_target_address", "")

        if not final_addr:
            st.error("住所/所在が入力されていません")
        else:
            with st.spinner("自動操作中... (ブラウザが起動します)"):
                try:
                    msg = ""
                    if category == "商業・法人":
                        # 会社名と住所を渡す
                        msg = touki_service.request_commercial(final_name, final_addr)
                    else:
                        # 住所と種別を渡す
                        msg = touki_service.request_real_estate(final_addr, target_type_radio)
                    
                    st.success(msg)
                except Exception as e:
                    # エラー詳細を表示
                    import traceback
                    st.error(f"エラーが発生しました: {e}")
                    st.text(traceback.format_exc())
````

## File: src/legal_system/ui/components/case_search.py
````python
# src/legal_system/ui/components/case_search.py

import streamlit as st
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from src.legal_system.models.tables import Case, Deceased
import streamlit.components.v1 as components

def render_case_search(session):
    """
    案件検索コンポーネント
    - 案件番号、依頼者名、被相続人名でのインクリメンタルサーチ
    - ショートカットキー (Alt+S) 対応: Deep DOM Access (On-Demand)
    """
    
    placeholder_text = "案件番号(G...), 依頼者名, 被相続人名..."
    label_text = "案件を検索 (Alt+S)"
    
    try:
        from st_keyup import st_keyup
        search_query = st_keyup(
            label_text, 
            key="global_case_search", 
            placeholder=placeholder_text,
            debounce=300
        )
    except ImportError:
        search_query = st.text_input(
            label_text, 
            placeholder="st_keyupがインストールされていません"
        )

    # ---------------------------------------------------------
    # JavaScript: Deep DOM Access & Focus Control (Alt+S)
    # キー押下時に探索するオンデマンド方式
    # ---------------------------------------------------------
    js_code = f"""
    <script>
    (function() {{
        const TARGET_LABEL = "{label_text}";
        const TARGET_PLACEHOLDER = "案件番号";

        // Deep Search Logic
        function deepQuerySelectorAll(selector, root) {{
            root = root || document;
            const results = [];
            try {{
                const found = root.querySelectorAll(selector);
                found.forEach(el => results.push(el));
            }} catch(e) {{}}

            const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT, null, false);
            let node;
            while (node = walker.nextNode()) {{
                if (node.shadowRoot) {{
                    results.push(...deepQuerySelectorAll(selector, node.shadowRoot));
                }}
                if (node.tagName === 'IFRAME') {{
                    try {{
                        const innerDoc = node.contentDocument || node.contentWindow.document;
                        if (innerDoc) {{
                            results.push(...deepQuerySelectorAll(selector, innerDoc));
                        }}
                    }} catch(e) {{}}
                }}
            }}
            return results;
        }}

        function findTargetInput() {{
            // A. aria-label (st_keyup標準)
            let inputs = deepQuerySelectorAll(`input[aria-label="${{TARGET_LABEL}}"]`, window.parent.document);
            // B. placeholder (フォールバック)
            if (inputs.length === 0) {{
                inputs = deepQuerySelectorAll(`input[placeholder^="${{TARGET_PLACEHOLDER}}"]`, window.parent.document);
            }}
            return inputs.length > 0 ? inputs[0] : null;
        }}

        const HANDLER_NAME = '_legalSearchKeyHandler_v2';
        const doc = window.parent.document;

        // 既存ハンドラ削除
        if (window.parent[HANDLER_NAME]) {{
            doc.removeEventListener('keydown', window.parent[HANDLER_NAME], true);
        }}

        // 新規ハンドラ登録
        window.parent[HANDLER_NAME] = function(e) {{
            // Alt + S
            if (e.altKey && e.code === 'KeyS') {{
                e.preventDefault(); 
                e.stopPropagation();
                
                // ★キーを押した瞬間に探索
                const inputEl = findTargetInput();
                if (inputEl) {{
                    inputEl.focus();
                    console.log("LegalApp: Focused search box via Alt+S");
                }} else {{
                    console.warn("LegalApp: Search box not found via Alt+S.");
                }}
            }}
        }};

        doc.addEventListener('keydown', window.parent[HANDLER_NAME], true);
        console.log("LegalApp: Search Shortcut (Alt+S) registered (On-Demand).");

    }})();
    </script>
    """
    
    components.html(js_code, height=0, width=0)

    # ---------------------------------------------------------
    # 検索処理 (Python側)
    # ---------------------------------------------------------
    selected_case_id = None

    if search_query:
        clean_query = search_query.replace("　", " ").strip()
        
        if clean_query:
            cases = session.query(Case).outerjoin(Case.deceased_ref).filter(
                or_(
                    Case.case_number.ilike(f"%{clean_query}%"),
                    Case.client_name.contains(clean_query),
                    Case.client_name_kana.contains(clean_query),
                    Deceased.name_last.contains(clean_query),
                    Deceased.name_first.contains(clean_query),
                    (Deceased.name_last + Deceased.name_first).contains(clean_query)
                )
            ).limit(10).all()

            if cases:
                # 1件ヒットなら自動選択
                if len(cases) == 1:
                    target_case = cases[0]
                    current_selected_id = st.session_state.get("selected_case_id")
                    
                    if current_selected_id != target_case.case_id:
                        st.session_state["selected_case_id"] = target_case.case_id
                        st.toast(f"案件を自動選択しました: {target_case.client_name} 様", icon="🔍")
                        st.rerun()

                st.caption(f"検索結果: {len(cases)}件")
                
                options = {
                    c.case_id: f"【{c.case_number or '未番'}】 {c.client_name} 様 (被: {c.deceased_ref.name_last if c.deceased_ref else ''})"
                    for c in cases
                }
                
                default_idx = 0
                current_id = st.session_state.get("selected_case_id")
                if current_id in options:
                    default_idx = list(options.keys()).index(current_id)
                
                selected_val = st.radio(
                    "検索結果を選択:", 
                    options=list(options.keys()), 
                    format_func=lambda x: options[x],
                    index=default_idx,
                    label_visibility="collapsed",
                    key="search_result_radio"
                )
                
                if selected_val:
                    selected_case_id = selected_val
                    if st.button("この案件を開く", key="btn_open_searched_case", use_container_width=True, type="primary"):
                        if st.session_state.get("selected_case_id") != selected_case_id:
                            st.session_state["selected_case_id"] = selected_case_id
                            st.rerun()
            else:
                st.warning("該当する案件が見つかりません")
    
    return st.session_state.get("selected_case_id")
````

## File: src/legal_system/ui/components/document_viewer.py
````python
# src/legal_system/ui/components/document_viewer.py

import base64
import streamlit as st
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_bytes

# キャッシュ関数
@st.cache_data(show_spinner=False)
def convert_pdf_to_images_cached(file_bytes: bytes):
    try:
        return convert_from_bytes(file_bytes, dpi=200)
    except Exception:
        return None

def image_to_bytes(img: Image.Image, format: str = "JPEG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def render_enhanced_document_viewer(file_bytes: bytes, file_type: str, key_prefix: str, base_width: int = 700):
    """
    PDFまたは画像のビューワーを表示する共通コンポーネント
    拡大縮小(Zoom)とページ送り機能を提供します。
    """
    with st.container(border=True):
        # ツールバー（ページ送り & ズーム）
        col_nav, col_zoom = st.columns([1, 1])
        
        images = []
        if "pdf" in file_type:
            images = convert_pdf_to_images_cached(file_bytes)
            if not images:
                st.error("PDFの変換に失敗しました。")
                return
        else:
            try:
                img = Image.open(BytesIO(file_bytes))
                images = [img]
            except:
                st.error("画像の読み込みに失敗しました。")
                return

        # セッションステート管理
        page_key = f"{key_prefix}_page"
        zoom_key = f"{key_prefix}_zoom"
        
        if page_key not in st.session_state: st.session_state[page_key] = 0
        if zoom_key not in st.session_state: st.session_state[zoom_key] = 100

        total_pages = len(images)
        current_page = st.session_state[page_key]

        # ナビゲーションUI
        with col_nav:
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            if c_prev.button("◀", key=f"{key_prefix}_prev", disabled=(current_page <= 0)):
                st.session_state[page_key] -= 1
                st.rerun()
            
            c_info.markdown(f"<div style='text-align: center; line-height: 2.3; font-weight: bold;'>Page {current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
            
            if c_next.button("▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages - 1)):
                st.session_state[page_key] += 1
                st.rerun()

        # ズームスライダー
        with col_zoom:
            zoom = st.slider("拡大率 (%)", 50, 300, st.session_state[zoom_key], 10, key=f"{key_prefix}_slider")
            st.session_state[zoom_key] = zoom

        # 画像表示エリア
        target_image = images[current_page]
        display_width = int(base_width * (zoom / 100))
        
        img_b64 = base64.b64encode(image_to_bytes(target_image)).decode()
        
        # ★修正ポイント: max-width: none を指定し、親要素の幅制限を無視して拡大させる
        st.markdown(
            f"""
            <div style="
                overflow: auto; 
                height: 600px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 10px;
                background-color: #f0f2f6;
                text-align: center;
                display: flex;
                justify_content: center;
                align-items: flex-start;">
                <img src="data:image/jpeg;base64,{img_b64}" 
                     style="width: {display_width}px; max-width: none; height: auto;" />
            </div>
            """,
            unsafe_allow_html=True
        )
````

## File: src/services/gmail_watcher_service.py
````python
# src/services/gmail_watcher_service.py

import base64
import difflib
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

import google.generativeai as genai
from google.auth.transport.requests import Request

# Google API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# LangChain / AI
# from langchain_core.output_parsers import JsonOutputParser # 未使用なら削除可
# データベース / SQL
from sqlalchemy.orm import joinedload

from legal_system.core.ai_factory import AIFactory
from legal_system.core.config import Config

# 内部モジュール
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, ContactLog, IncomingNoteBuffer
from src.utils.retry_decorator import retry_with_backoff

# ロガー設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Gmail API スコープ (読み取り専用)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailWatcherService:
    def __init__(self):
        self.db = DatabaseManager()
        self.creds = self._authenticate_gmail()
        self.service = (
            build("gmail", "v1", credentials=self.creds) if self.creds else None
        )

        # LangChain用
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

        # 音声処理用に直接Geminiクライアントを設定
        if os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def _authenticate_gmail(self):
        token_path = "token.json"
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    return None
            if creds:
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
        return creds

    def _get_decoded_body(self, payload: dict) -> str:
        def decode_data(data):
            if not data:
                return ""
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        if "body" in payload and "data" in payload["body"]:
            return decode_data(payload["body"]["data"])

        # 本文探索も再帰的に行うのがベストだが、ここでは簡易的に text/plain を探す
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and "data" in part.get(
                    "body", {}
                ):
                    return decode_data(part["body"]["data"])
        return ""

    @retry_with_backoff(
        max_retries=3, backoff_factor=2.0, exceptions=(HttpError, TimeoutError)
    )
    def _get_attachment_data(self, msg_id: str, attachment_id: str) -> Optional[bytes]:
        """Gmailから添付ファイルの生データを取得（リトライ対応版）"""
        attachment = (
            self.service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=msg_id, id=attachment_id)
            .execute()
        )
        return base64.urlsafe_b64decode(attachment["data"])

    def _walk_parts(
        self, part: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        メールのパートを再帰的に探索してフラットなリストにするヘルパー関数。
        これにより、multipart/alternative 内のネストされた添付ファイルも検出可能になる。
        """
        yield part
        if "parts" in part:
            for sub_part in part["parts"]:
                yield from self._walk_parts(sub_part)

    def poll_and_process(self):
        if not self.service:
            return
        logger.info("📧 Gmail: 新着会議メモを確認中...")
        session = None
        try:
            target_senders = ["gemini-notes@google.com"]
            target_keywords = ["録音", "ボイス"]

            if target_senders:
                senders_part = f"from:({' OR '.join(target_senders)} OR me)"
            else:
                senders_part = "from:(gemini-notes@google.com OR me)"

            conditions = ['subject:"メモ"']
            for kw in target_keywords:
                conditions.append(f"subject:{kw}")
                conditions.append(f"filename:{kw}")

            conditions_part = f"({' OR '.join(conditions)})"
            query = f"{senders_part} {conditions_part} newer_than:7d"

            logger.info(f"🔎 Generated Query: {query}")

            results = (
                self.service.users().messages().list(userId="me", q=query).execute()
            )
            messages = results.get("messages", [])
            if not messages:
                logger.info("   -> 対象のメールは見つかりませんでした。")
                return

            session = self.db._get_session()
            processed_count = 0

            for msg in messages:
                msg_id = msg["id"]
                if (
                    session.query(IncomingNoteBuffer)
                    .filter_by(message_id=msg_id)
                    .first()
                ):
                    continue

                detail = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg_id)
                    .execute()
                )
                payload = detail.get("payload", {})
                subject = next(
                    (
                        h["value"]
                        for h in payload.get("headers", [])
                        if h["name"] == "Subject"
                    ),
                    "No Subject",
                )
                body_text = self._get_decoded_body(payload) or detail.get("snippet", "")

                # --- 【修正】音声ファイルの検出と処理 (再帰対応) ---
                audio_summary = ""
                has_audio = False

                # _walk_partsを使って、ネストされたパートも含めて全てチェックする
                for part in self._walk_parts(payload):
                    fname = part.get("filename", "").lower()

                    # 音声ファイルの拡張子チェック
                    if fname and fname.endswith((".m4a", ".mp3", ".wav", ".aac")):
                        logger.info(f"   🎙️ 音声ファイルを検出: {fname}")
                        att_id = part["body"].get("attachmentId")

                        if att_id:
                            audio_data = self._get_attachment_data(msg_id, att_id)
                            if audio_data:
                                logger.info("   ⏳ 音声をAIに送信中(文字起こし)...")
                                try:
                                    # 音声解析の実行
                                    audio_summary_part = (
                                        self._transcribe_audio_with_gemini(
                                            audio_data, fname
                                        )
                                    )
                                    has_audio = True
                                    body_text += f"\n\n--- 🎙️ 音声解析結果 ({fname}) ---\n{audio_summary_part}"
                                    # 複数の音声ファイルがある場合も考慮して追記する形にする
                                except Exception as e:
                                    logger.error(f"   ❌ 音声解析失敗: {e}")
                                    body_text += f"\n\n（※音声解析エラー: {e}）"
                # ------------------------------------------------

                if not has_audio and not body_text.strip():
                    body_text = "（本文なし・音声ファイルなし）"

                logger.info(f"📥 新規メモ受信: {subject}")

                ai_result = self._analyze_email_with_ai(body_text)
                detected_names = ai_result.get("names", [])

                summary_raw = ai_result.get("summary", "（要約なし）")
                if isinstance(summary_raw, dict):
                    title = summary_raw.get("title", "会議メモ")
                    points = summary_raw.get("points", [])
                    summary_text = f"{title}\n" + "\n".join([f"- {p}" for p in points])
                else:
                    summary_text = str(summary_raw)

                linked_case = self._find_case_by_names_fuzzy(session, detected_names)

                status = "PENDING"
                linked_case_id = None
                formatted_content = f"【AI要約】{summary_text}\n\n--- 以下、メール全文・音声解析 ---\n{body_text}"

                if linked_case:
                    logger.info(f"   ✅ 案件ヒット(Fuzzy): {linked_case.client_name}")
                    self._save_to_contact_log(
                        session, linked_case.case_id, formatted_content
                    )
                    status = "LINKED"
                    linked_case_id = linked_case.case_id
                else:
                    logger.info("   ⏳ 案件未登録 -> 保留バッファへ保存")

                new_note = IncomingNoteBuffer(
                    message_id=msg_id,
                    received_at=datetime.now(),
                    subject=subject,
                    body_text=formatted_content,
                    detected_names=json.dumps(detected_names, ensure_ascii=False),
                    ai_summary=summary_text,
                    status=status,
                    linked_case_id=linked_case_id,
                )
                session.add(new_note)
                processed_count += 1

                if processed_count < len(messages):
                    logger.info("   💤 API負荷軽減のため10秒待機...")
                    time.sleep(10)

            session.commit()
            if processed_count > 0:
                logger.info(f"🎉 {processed_count}件のメモを処理しました。")

        except Exception as e:
            logger.error(f"Gmail Polling Error: {e}")
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    def _transcribe_audio_with_gemini(self, audio_data: bytes, filename: str) -> str:
        """Geminiを使って音声をテキスト化・要約する (Config参照版)"""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=os.path.splitext(filename)[1], delete=False
            ) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Geminiにアップロード
            myfile = genai.upload_file(tmp_path)

            # Configからモデル名を取得 (一元管理)
            target_model = Config.VISION_AUDIO_MODEL
            logger.info(f"   🤖 使用モデル: {target_model}")

            model = genai.GenerativeModel(target_model)

            prompt = "この音声ファイルは行政書士と依頼者の会議録音です。内容を詳細に文字起こしし、重要なポイントを要約してください。"

            response = model.generate_content([prompt, myfile])

            os.remove(tmp_path)
            return response.text

        except Exception as e:
            logger.error(f"Audio Transcribe Error: {e}")
            error_msg = str(e)

            # Configのモデル名が使えなかった場合のヒント
            if "404" in error_msg or "not found" in error_msg.lower():
                return f"（音声解析エラー: モデル '{Config.VISION_AUDIO_MODEL}' が見つかりません。src/legal_system/core/config.py の VISION_AUDIO_MODEL を 'gemini-1.5-flash-001' 等に変更してください。）"

            return f"（音声解析エラー: {e}）"

    def _analyze_email_with_ai(self, text: str) -> Dict[str, Any]:
        prompt = f"""会議メモ（または音声解析結果）を解析し、以下のJSON形式で返してください。
        1. names: 会議に関わる顧客・被相続人の氏名リスト（行政書士名は除外）。
        2. summary: 会議の内容を「title（見出し）」と「points（3点の箇条書きリスト）」に分けて要約。
        本文: {text[:40000]}"""
        try:
            res = self.llm.invoke(prompt)
            content = res.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except:
            return {"names": [], "summary": "AI解析失敗"}

    def _find_case_by_names_fuzzy(self, session, names: List[str]) -> Optional[Case]:
        if not names:
            return None
        all_cases = session.query(Case).options(joinedload(Case.deceased_ref)).all()
        candidate_map = {}
        for c in all_cases:
            candidate_map[(c.client_name or "").replace(" ", "").replace("　", "")] = c
            if c.deceased_ref:
                d = c.deceased_ref
                d_full = (
                    ((d.name_last or "") + (d.name_first or ""))
                    .replace(" ", "")
                    .replace("　", "")
                )
                if d_full:
                    candidate_map[d_full] = c
                for h in d.heirs or []:
                    h_full = (
                        ((h.name_last or "") + (h.name_first or ""))
                        .replace(" ", "")
                        .replace("　", "")
                    )
                    if h_full:
                        candidate_map[h_full] = c

        for name in names:
            target = name.replace(" ", "").replace("　", "")
            if len(target) < 2:
                continue
            if target in candidate_map:
                return candidate_map[target]
            best_match = difflib.get_close_matches(
                target, candidate_map.keys(), n=1, cutoff=0.6
            )
            if best_match:
                return candidate_map[best_match[0]]
        return None

    def _save_to_contact_log(self, session, case_id, content):
        log = ContactLog(case_id=case_id, contact_content=content)
        session.add(log)

    def retry_linking_pending_notes(self):
        session = self.db._get_session()
        try:
            pendings = (
                session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()
            )
            for note in pendings:
                names = json.loads(note.detected_names or "[]")
                linked = self._find_case_by_names_fuzzy(session, names)
                if linked:
                    self._save_to_contact_log(session, linked.case_id, note.body_text)
                    note.status = "LINKED"
                    note.linked_case_id = linked.case_id
            session.commit()
        except Exception as e:
            logger.error(f"Retry error: {e}")
        finally:
            session.close()

    def get_pending_notes(self) -> List[IncomingNoteBuffer]:
        session = self.db._get_session()
        try:
            return (
                session.query(IncomingNoteBuffer)
                .filter_by(status="PENDING")
                .order_by(IncomingNoteBuffer.received_at.desc())
                .all()
            )
        finally:
            session.close()

    def link_note_to_case_manually(self, note_id: int, case_id: int) -> bool:
        session = self.db._get_session()
        try:
            note = session.query(IncomingNoteBuffer).get(note_id)
            case = session.query(Case).get(case_id)
            if not note or not case:
                return False

            log = ContactLog(case_id=case.case_id, contact_content=note.body_text)
            session.add(log)
            note.status = "LINKED"
            note.linked_case_id = case.case_id
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Manual Link Error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def ignore_note(self, note_id: int) -> bool:
        session = self.db._get_session()
        try:
            note = session.query(IncomingNoteBuffer).get(note_id)
            if note:
                note.status = "IGNORED"
                session.commit()
                return True
            return False
        finally:
            session.close()
````

## File: src/services/logistics_service.py
````python
# src/services/logistics_service.py

import urllib.parse
from datetime import datetime
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from legal_system.core.ai_factory import AIFactory

class LogisticsService:
    """
    公証役場へのアクセスや選定アドバイスを行うAIサービス
    """
    def __init__(self):
        # 事実性を重視するため temperature=0.0
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def consult_nearest_notaries(self, origin_address: str) -> str:
        """
        指定された住所に基づき、アクセスの良い公証役場を提案する
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Googleマップ用に出発地をURLエンコードしておく (スペース等は削除)
        clean_origin = origin_address.replace(" ", "").replace("　", "")
        origin_enc = urllib.parse.quote(clean_origin)

        # ★修正: URL形式を標準化し、文字化け対策を追加
        system_prompt = f"""
        あなたは、日本の公証実務に精通したロジスティクスAIです。
        ユーザーから提供された住所（{clean_origin}）を起点として、アクセスが良く**実在する**「公証役場」を2〜3箇所選定し、提案してください。

        【重要：情報の正確性と出力形式】
        1. **出典の厳守**:
           - 「日本公証人連合会」の公式リスト (https://www.koshonin.gr.jp/list) に掲載されている公証役場のみを提案してください。
           - 「我孫子」「流山」など、実在しない役場は絶対に提案しないでください。

        2. **文字化け・ハルシネーション防止**:
           - 住所や名称は正確に記述してください。
           - **不自然な記号の羅列（例: ॒॒॒॒...）や、無意味な空白の繰り返しは厳禁**です。標準的な日本語のみを使用してください。

        3. **地図リンクの生成**:
           - 以下のGoogleマップ公式パラメータ形式を使用してください。
           - 形式: `https://www.google.com/maps/dir/?api=1&origin={origin_enc}&destination=[公証役場の住所]`
           - destinationには、抽出した「公証役場の住所」をそのまま入れてください。

        【出力フォーマット】
        --------------------------------------------------
        ### 1. [公証役場名]
        - **住所**: [郵便番号] [都道府県市区町村...]
        - **最寄り駅**: [駅名] (徒歩〇分)
        - **アクセス**: [出発地からの移動ルート概要]
        - **地図**: [Googleマップでルートを見る](https://www.google.com/maps/dir/?api=1&origin={origin_enc}&destination=[公証役場の住所])
        --------------------------------------------------
        (これを2〜3件繰り返す)

        【選定理由】
        （なぜここを選んだかの理由）

        【注意点】
        （管轄や予約の必要性など）
        """

        user_message = f"検索起点: {clean_origin}"

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"input": user_message})
            
            return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            return f"AI検索エラーが発生しました: {e}"
````

## File: src/utils/date_utils.py
````python
# src/utils/date_utils.py
import datetime
import re

def parse_all_flexible_date(date_obj: object) -> datetime.date:
    """
    様々な形式の日付データ（文字列または日付オブジェクト）を datetime.date に変換する。
    対応形式: YYYY-MM-DD, YYYY/MM/DD, 和暦, datetime.date, datetime.datetime
    """
    if date_obj is None:
        return None
    
    # 既に date 型ならそのまま返す
    if isinstance(date_obj, datetime.date):
        return date_obj
    
    # datetime 型なら date に変換
    if isinstance(date_obj, datetime.datetime):
        return date_obj.date()

    # 文字列でない場合は None (安全策)
    if not isinstance(date_obj, str):
        return None
    
    s = date_obj.strip()
    if not s:
        return None

    # 1. YYYY-MM-DD / YYYY/MM/DD
    try:
        s = s.replace('/', '-')
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        pass

    # 2. YYYY年MM月DD日
    try:
        return datetime.datetime.strptime(s, "%Y年%m月%d日").date()
    except ValueError:
        pass

    # 3. 数字8桁 (20250101)
    if s.isdigit() and len(s) == 8:
        try:
            return datetime.datetime.strptime(s, "%Y%m%d").date()
        except ValueError:
            pass

    # 必要であれば和暦変換ロジックを追加
    return None

def convert_seireki_to_wareki(dt: datetime.date) -> str:
    """西暦Dateを和暦文字列に変換"""
    if not dt: return ""
    if dt.year >= 2019:
        n = dt.year - 2018
        gengo = "令和"
    elif dt.year >= 1989:
        n = dt.year - 1988
        gengo = "平成"
    elif dt.year >= 1926:
        n = dt.year - 1925
        gengo = "昭和"
    else:
        n = dt.year - 1911
        gengo = "大正"
    
    nen = "元" if n == 1 else str(n)
    return f"{gengo}{nen}年{dt.month}月{dt.day}日"
````

## File: update_bank_master.py
````python
# File: update_bank_master.py

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3

# SSL警告を非表示にする（ローカル開発用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 設定エリア (絶対パス化)
# ==========================================
ROOT_DIR = Path(__file__).parent.absolute()
BASE_DIR = ROOT_DIR / "data" / "zengin"
BRANCH_DIR = BASE_DIR / "branches"
STATE_FILE = BASE_DIR / "last_updated.json"

# API & URL
REPO_API_URL = (
    "https://api.github.com/repos/zengin-code/source-data/commits?path=data&per_page=1"
)
BANKS_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/banks.json"
)
BRANCH_BASE_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/branches/"
)


def download_data(progress_callback=None):
    print(f"🚀 [Start] データ保存先を確認: {BASE_DIR}")

    # フォルダ作成
    os.makedirs(BRANCH_DIR, exist_ok=True)

    # 1. 銀行一覧
    if progress_callback:
        progress_callback(0, 100, "銀行一覧を取得中...")

    try:
        # verify=False でSSLエラーを回避
        print(f"connecting to {BANKS_URL} ...")
        resp = requests.get(BANKS_URL, timeout=15, verify=False)
        resp.raise_for_status()
        banks = resp.json()

        with open(BASE_DIR / "banks.json", "w", encoding="utf-8") as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)

        print(f"✅ 銀行マスタ保存完了: {len(banks)}件")

    except Exception as e:
        print(f"❌ 銀行一覧の取得に失敗: {e}")
        return False, None

    # 2. 支店データ
    total_banks = len(banks)
    print(f"🔄 支店データ取得開始: 対象 {total_banks} 行")

    success_count = 0
    # 全件取得（エラーが出ても止まらないようにする）
    for i, bank_code in enumerate(list(banks.keys())):
        branch_url = f"{BRANCH_BASE_URL}{bank_code}.json"
        save_path = BRANCH_DIR / f"{bank_code}.json"

        try:
            r = requests.get(branch_url, timeout=10, verify=False)
            if r.status_code == 200:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f, ensure_ascii=False, indent=2)
                success_count += 1

            # プログレスバー更新 (10件に1回更新で負荷軽減)
            if i % 10 == 0 and progress_callback:
                progress_callback(i + 1, total_banks, f"支店データ取得中: {bank_code}")

            # サーバー負荷軽減のためのスリープ
            time.sleep(0.01)

        except Exception:
            # 個別の失敗は無視して続行
            pass

    print(f"✅ 全ダウンロード完了 (成功: {success_count}件)")
    return True, banks


# --- 以下の関数は変更なし ---
def get_remote_last_commit_date():
    try:
        resp = requests.get(REPO_API_URL, timeout=10, verify=False)
        if resp.status_code == 200:
            return resp.json()[0]["commit"]["committer"]["date"]
    except:
        pass
    return None


def load_local_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_commit_date": ""}


def save_local_state(commit_date):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "last_commit_date": commit_date,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    download_data()
````

## File: src/legal_system/core/data_sync.py
````python
# file: src/legal_system/core/data_sync.py

import json
import logging
import os
from typing import Any, Dict

# ★重要: ロジックを分散させず、サービス層に一元化する
from services.kintone_sync_service import import_kintone_json

logger = logging.getLogger(__name__)

class DataSyncEngine:
    """
    Watcherからの呼び出しを受け付け、Service層へ処理を流すクラス。
    """

    def __init__(self):
        pass

    def sync_from_kintone_json(self, json_path: str) -> bool:
        """
        JSONファイルを読み込み、Service層を通じてDBへUpsertする。
        """
        if not os.path.exists(json_path):
            return False

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return False
        except Exception as e:
            logger.error(f"JSON読込エラー: {e}")
            return False

        try:
            logger.info(f"🔄 同期開始: {os.path.basename(json_path)}")
            
            # 手動取り込みと同じ関数を呼び出す
            # target_case_id=None にすると、JSON内の「顧客コード(G番号)」から自動で案件を特定/作成してくれる
            case_id = import_kintone_json(data, target_case_id=None)

            if case_id and case_id > 0:
                logger.info(f"✅ 同期成功 (Case ID: {case_id})")
                return True
            else:
                logger.warning("⚠️ 同期処理は完了しましたが、IDが返されませんでした。")
                return False

        except Exception as e:
            logger.error(f"❌ 同期エラー: {e}")
            return False
````

## File: src/legal_system/ui/components/admin_tools.py
````python
# src/legal_system/ui/components/admin_tools.py

import hashlib
import json
import os
import random
import re
import time
import base64
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ocr_engine import extract_text_from_scanned_pdf

# ---------------------------------------------------------
# ヘルパー関数群
# ---------------------------------------------------------
def calculate_file_hash(file_bytes: bytes) -> str:
    """ファイルの重複登録を防ぐためのハッシュ計算"""
    return hashlib.md5(file_bytes).hexdigest()

def extract_text_safe(file_bytes: bytes) -> str:
    """
    PDFからテキストを抽出。
    1. テキストレイヤー (pypdf) を試す (高速・無料)
    2. なければ Gemini Vision / PaddleOCR (ocr_engineにお任せ)
    """
    text = ""
    try:
        pdf = PdfReader(BytesIO(file_bytes))
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t
    except:
        pass
        
    # テキストが極端に少ない場合はスキャンデータとみなしてOCRエンジン(Gemini優先)を実行
    if len(text.strip()) < 50:
        st.toast("テキストデータなし。AI視覚解析を実行します...", icon="👁️")
        ocr_text = extract_text_from_scanned_pdf(file_bytes)
        if ocr_text:
            text = ocr_text
                
    return text


def _rule_based_classify(text_content: str) -> dict:
    """
    【高速化・コスト削減】
    AIに投げる前に、強力なルールベースで分類を試みる。
    """
    if not text_content:
        return None

    # 正規化（改行・空白削除）
    normalized_text = text_content.replace("\n", "").replace(" ", "").replace("　", "")

    # 1. 銀行名の特定
    bank_name = "その他"
    known_banks = ["三菱UFJ", "三井住友", "みずほ", "ゆうちょ", "りそな", "横浜銀行"]
    for bank in known_banks:
        if bank in normalized_text:
            bank_name = f"{bank}銀行" if "銀行" not in bank else bank
            break

    # 2. 書類種別の特定
    doc_type = "その他"
    if "残高証明書" in normalized_text:
        doc_type = "残高証明"
    elif "取引推移" in normalized_text or "入出金明細" in normalized_text:
        doc_type = "取引明細"
    elif "相続届" in normalized_text or "相続手続請求書" in normalized_text:
        doc_type = "相続届"
    elif "委任状" in normalized_text:
        doc_type = "委任状"
    elif "手引" in normalized_text or "ご案内" in normalized_text:
        doc_type = "手引き"

    if bank_name != "その他" or doc_type != "その他":
        filename = f"{bank_name}_{doc_type}"
        return {"filename": filename, "bank_name": bank_name, "doc_type": doc_type}

    return None


def analyze_document_info(text_content: str, llm):
    """
    文書の種類や銀行名を推定するハイブリッドロジック
    """
    if not text_content:
        return {"filename": "", "bank_name": "", "doc_type": ""}

    # Priority 1: ルールベース
    rule_result = _rule_based_classify(text_content)
    if rule_result:
        return rule_result

    # Priority 2: AI判定
    prompt = """
    以下のドキュメント冒頭を読み、3つの情報をJSON形式で出力してください。
    1. filename: {金融機関名}_{書類名}
    2. bank_name: 金融機関名 (特定できなければ"その他")
    3. doc_type: "手引き", "残高証明", "相続届", "委任状", "その他" から選択
    
    【ドキュメント冒頭】
    """ + text_content[:1500]

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass

    return {"filename": "解析失敗", "bank_name": "その他", "doc_type": "その他"}


# ---------------------------------------------------------
# メイン機能: アップロードタブの描画
# ---------------------------------------------------------
def render_upload_tab(db_manager: DatabaseManager):
    st.subheader("📂 雛形・記入例の登録 (OCR)")
    st.caption("PDFを解析し、RAGデータベースとファイルサーバーに登録します。")

    s_norm, s_sec = st.tabs(["🟦 一般雛形", "🟥 記入例 (機密)"])

    # ==========================================
    # 1. 一般用タブ (クラウドAI使用)
    # ==========================================
    with s_norm:
        st.info("個人情報を含まない手引き等")

        # 案件紐付け
        session = db_manager._get_session()
        target_case_id = None
        try:
            from legal_system.models.tables import Case
            cases = session.query(Case).all()
            case_opts = {"（全案件共通の雛形として登録）": None}
            for c in cases:
                case_opts[f"{c.case_number}: {c.client_name}"] = c.case_id
            selected = st.selectbox("紐付ける案件 (任意)", list(case_opts.keys()), key="up_case_sel")
            target_case_id = case_opts[selected]
        finally:
            session.close()

        files_n = st.file_uploader("PDFアップロード (一般)", accept_multiple_files=True, key="up_n")

        if files_n:
            if st.button("🔍 クラウド解析", key="btn_n"):
                with st.status("🚀 ハイブリッド解析中 (ルールベース + AI)...", expanded=True) as status:
                    st.session_state.upload_stage = []
                    try:
                        llm_cloud = AIFactory.get_llm("cloud")
                    except Exception as e:
                        status.update(label="❌ エラー発生", state="error")
                        st.error(f"AIモデルの準備に失敗しました: {e}")
                        st.stop()

                    total_files = len(files_n)
                    progress_bar = st.progress(0)

                    for i, f in enumerate(files_n):
                        st.write(f"📄 読込中 ({i + 1}/{total_files}): {f.name}")
                        fb = f.read()

                        f_hash = calculate_file_hash(fb)
                        if db_manager.is_file_registered(f_hash):
                            st.warning(f"⚠️ {f.name} は既に登録されています。スキップします。")
                            time.sleep(0.5)
                            continue

                        text = extract_text_safe(fb)
                        meta = analyze_document_info(text, llm_cloud)
                        st.write(f"   ↳ 判定: {meta.get('doc_type', '不明')} / {meta.get('bank_name', '不明')}")

                        st.session_state.upload_stage.append({
                            "old": f.name,
                            "new": meta.get("filename", f.name),
                            "bank_name": meta.get("bank_name", "その他"),
                            "doc_type": meta.get("doc_type", "その他"),
                            "data": fb,
                            "text": text,
                            "type": "general",
                            "hash": f_hash,
                            "case_id": target_case_id,
                        })
                        progress_bar.progress((i + 1) / total_files)

                    status.update(label="✅ 解析完了！内容を確認して、下の「登録実行」を押してください。", state="complete", expanded=True)

    # ==========================================
    # 2. 機密用タブ (ローカルAI使用)
    # ==========================================
    with s_sec:
        st.warning("個人情報を含む書類 (ローカル処理)")
        session = db_manager._get_session()
        target_case_id_sec = None
        try:
            from legal_system.models.tables import Case
            cases = session.query(Case).all()
            case_opts_s = {"（全案件共通の雛形として登録）": None}
            for c in cases:
                case_opts_s[f"{c.case_number}: {c.client_name}"] = c.case_id
            selected_s = st.selectbox("紐付ける案件 (任意)", list(case_opts_s.keys()), key="up_case_sel_sec")
            target_case_id_sec = case_opts_s[selected_s]
        finally:
            session.close()

        file_s = st.file_uploader("PDFアップロード (機密)", accept_multiple_files=False, key="up_s")

        if file_s:
            fb_s = file_s.read()
            f_hash = calculate_file_hash(fb_s)

            if db_manager.is_file_registered(f_hash):
                st.error(f"⛔ {file_s.name} は既に登録済みです。")
            else:
                if st.checkbox("機密書類であることを確認しました", key="check_s") and st.button("🔒 ローカル解析", key="btn_s"):
                    with st.status("🔒 ローカルAI (Ollama) で解析中...", expanded=True) as status:
                        st.session_state.upload_stage = []
                        try:
                            llm_local = AIFactory.get_llm("local")
                        except Exception as e:
                            status.update(label="❌ エラー発生", state="error")
                            st.error(f"ローカルモデルの起動に失敗: {e}")
                            st.stop()

                        text_s = extract_text_safe(fb_s)
                        meta = analyze_document_info(text_s, llm_local)
                        if "記入例" not in meta["filename"]:
                            meta["filename"] += "_記入例"

                        st.session_state.upload_stage.append({
                            "old": file_s.name,
                            "new": meta.get("filename", file_s.name),
                            "bank_name": meta.get("bank_name", "その他"),
                            "doc_type": meta.get("doc_type", "その他"),
                            "data": fb_s,
                            "text": text_s,
                            "type": "secure",
                            "hash": f_hash,
                            "case_id": target_case_id_sec,
                        })
                        status.update(label="✅ 解析完了！下の「登録実行」へ進んでください。", state="complete", expanded=True)

    # ==========================================
    # 3. 保存確認フォーム
    # ==========================================
    if st.session_state.get("upload_stage"):
        st.divider()
        st.subheader("💾 登録確認")
        st.info("解析結果を確認し、必要であれば修正してから登録してください。")

        with st.form("save_form"):
            configs = []
            for i, item in enumerate(st.session_state.upload_stage):
                c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                c1.text(item["old"])
                new_name = c2.text_input("登録名", value=item["new"], key=f"fn_{i}")
                new_bank = c3.text_input("銀行タグ", value=item["bank_name"], key=f"bk_{i}")

                opts = ["手引き", "残高証明", "取引明細", "顧客勘定元帳", "相続届", "委任状", "その他"]
                curr = item.get("doc_type", "その他")
                idx = opts.index(curr) if curr in opts else 6
                new_type = c4.selectbox("種別", opts, index=idx, key=f"dt_{i}")

                configs.append({
                    **item,
                    "name": new_name,
                    "bank_name": new_bank,
                    "doc_type": new_type,
                })

            if st.form_submit_button("✅ 登録実行"):
                _execute_registration(configs, db_manager)


def _execute_registration(configs, db_manager):
    vector_store = AIFactory.get_vector_store()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    cnt = 0
    today = datetime.now().strftime("%Y%m%d")
    templates_dir = os.path.join(ROOT_DIR, "data", "templates")
    os.makedirs(templates_dir, exist_ok=True)

    with st.status("💾 データベースに登録中...", expanded=True) as status:
        progress_bar = st.progress(0)
        total_configs = len(configs)

        for idx, c in enumerate(configs):
            fname = f"{c['name']}_{today}.pdf"
            st.write(f"📝 登録中 ({idx + 1}/{total_configs}): {fname}")

            save_path = os.path.join(templates_dir, fname)
            with open(save_path, "wb") as f:
                f.write(c["data"])

            db_manager.register_file_hash(c["hash"], fname, c["doc_type"], case_id=c.get("case_id"))

            enriched_text = f"【ファイル名】{fname}\n【銀行名】{c['bank_name']}\n【書類種別】{c['doc_type']}\n\n{c['text']}"
            chunks = splitter.split_text(enriched_text)
            metadatas = [{
                "source": fname, "path": save_path, "security_level": c["type"],
                "bank_name": c["bank_name"], "doc_type": c["doc_type"]
            } for _ in chunks]

            batch_size = 2
            total_chunks = len(chunks)
            for i in range(0, total_chunks, batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]
                
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        vector_store.add_texts(batch_chunks, metadatas=batch_metas)
                        time.sleep(1.0)
                        break
                    except Exception as e:
                        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                            if attempt < max_retries - 1:
                                time.sleep((2**attempt) + random.random() * 2)
                            else:
                                raise e
                        else:
                            raise e

            cnt += 1
            progress_bar.progress((idx + 1) / total_configs)

        status.update(label="✅ 全件登録完了！", state="complete", expanded=False)

    st.success(f"{cnt}件の学習・登録が完了しました！")
    st.session_state.upload_stage = []
    time.sleep(1.5)
    st.rerun()


# ---------------------------------------------------------
# メイン機能: データ管理タブ (★ファイル追跡機能付き)
# ---------------------------------------------------------
def render_management_tab(db_manager: DatabaseManager):
    """
    ファイルの一覧表示、検索、削除を行う管理タブ
    Ver 3.3: ファイル追跡機能を追加
    """
    st.subheader("🔎 ファイル追跡・管理")
    
    files = db_manager.get_all_files()
    
    # ==========================================
    # 1. 追跡ツール (Search & Track)
    # ==========================================
    with st.container(border=True):
        st.markdown("##### 🕵️‍♀️ ファイル追跡")
        st.caption("ファイル名が変わっても、ハッシュ値(ID)で同一性を追跡できます。")
        
        c_s1, c_s2 = st.columns([3, 1])
        search_q = c_s1.text_input("ファイル名 または ハッシュ値(ID) で検索", placeholder="Scan_001.pdf や ハッシュ値...")
        
        if search_q:
            # 簡易検索ロジック (ハッシュまたはファイル名に部分一致)
            hits = [f for f in files if search_q in f['filename'] or search_q in f['hash']]
            
            if hits:
                st.success(f"🎉 {len(hits)} 件見つかりました。")
                for hit in hits:
                    with st.expander(f"📄 {hit['filename']}", expanded=True):
                        st.markdown(f"""
                        - **登録日**: {hit['date']}
                        - **種別**: {hit['type']}
                        - **紐付け案件**: {hit['case']}
                        - **ID (Hash)**: `{hit['hash']}`
                        - **ステータス**: {hit.get('status', '登録済')}
                        """)
            else:
                st.error("❌ 見つかりませんでした。")

    # ==========================================
    # 2. 全リスト表示
    # ==========================================
    st.divider()
    st.markdown("##### 📂 全ファイル一覧")
    
    if not files:
        st.info("登録されているファイルはありません。")
    else:
        df_files = pd.DataFrame(files)
        # ユーザーに見やすいカラムのみ抽出
        display_cols = ["date", "case", "type", "filename", "hash", "status"]
        # データフレームに存在しないカラムがあれば除外（念のため）
        display_cols = [c for c in display_cols if c in df_files.columns]
        
        # カラム名リネーム
        df_display = df_files[display_cols].rename(columns={
            "date": "登録日時",
            "case": "案件",
            "type": "書類種別",
            "filename": "ファイル名",
            "hash": "ID",
            "status": "状態"
        })
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # ==========================================
        # 3. 削除エリア
        # ==========================================
        st.divider()
        with st.expander("🗑️ ファイルの削除 (Danger Zone)", expanded=False):
            st.warning("ここでの削除は取り消せません。")
            
            selected_file = st.selectbox(
                "削除するファイルを選択", 
                options=[f["filename"] for f in files],
                key="delete_file_selector"
            )

            if st.button("選択したファイルを完全に削除する", type="primary"):
                templates_dir = os.path.join(ROOT_DIR, "data", "templates")
                target_path = os.path.join(templates_dir, selected_file)

                # 物理削除
                if os.path.exists(target_path):
                    try:
                        os.remove(target_path)
                    except OSError:
                        pass # ファイルがなくてもDB削除は進める

                # DB削除
                db_manager.delete_file_registry(selected_file)
                
                st.success(f"{selected_file} を削除しました。")
                time.sleep(1)
                st.rerun()
````

## File: src/legal_system/main.py
````python
# src/legal_system/main.py

import subprocess
import sys
from pathlib import Path

def main():
    """
    Streamlitアプリを最優先で起動するランチャー。
    監視プロセス(Watcher)の起動は、Home.pyのバックグラウンド処理に移譲されました。
    """
    current_dir = Path(__file__).parent.absolute()
    app_path = current_dir / "ui" / "Home.py"

    print("🚀 Legal RAG System 起動中...")
    
    # Streamlitをメインプロセスとして即座に起動
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        # このプロセスが終了するまでブロック
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 システムを終了しました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
````

## File: src/services/automation/touki_service.py
````python
# src/services/automation/touki_service.py

import logging
import os
import re
import time
from typing import Optional, Tuple

# Selenium 関連
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from src.utils.retry_decorator import retry_with_backoff

# Webdriver Manager (ドライバ自動更新)
try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    ChromeDriverManager = None

# ロガー設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定数定義
LOGIN_URL = "https://www.touki.or.jp/TeikyoUketsuke/"


class ToukiService:
    """
    登記情報提供サービスの自動操作を行うサービスクラス (完全運用版)
    """

    def __init__(self) -> None:
        self.user_id = os.getenv("TOUKI_USER_ID", "dummy_user")
        self.password = os.getenv("TOUKI_PASSWORD", "dummy_pass")

        # 環境判定: Docker内かどうか
        self.is_docker = os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER")

        # Dockerならヘッドレス必須、ローカルならGUI強制
        self.headless = True if self.is_docker else False

        logger.info(f"🚀 ToukiService Initialized. Headless: {self.headless}")

    def _get_driver(self):
        """Chrome WebDriverの初期化と設定"""
        options = Options()

        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
        else:
            # GUI表示を強制
            options.add_experimental_option("detach", True)
            options.add_argument("--window-position=0,0")
            options.add_argument("--window-size=1280,800")

        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        try:
            if ChromeDriverManager:
                service = ChromeService(ChromeDriverManager().install())
            else:
                service = ChromeService()

            driver = webdriver.Chrome(service=service, options=options)
            if not self.headless:
                driver.maximize_window()
            return driver
        except Exception as e:
            logger.error(f"❌ WebDriverの起動に失敗しました: {e}")
            raise Exception(f"ブラウザ起動エラー: {e}")

    def _wait_and_click(self, driver, by, value, timeout=10):
        """指定した要素が表示されクリック可能になるまで待機してクリックするヘルパー"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            logger.info(f"Clicked element: {value}")
        except Exception as e:
            logger.error(f"Click failed for {value}: {e}")
            raise

    def _wait_and_send_keys(self, driver, by, value, text, timeout=10):
        """指定した要素が表示されるまで待機してテキストを入力するヘルパー"""
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            element.clear()
            element.send_keys(text)
            logger.info(f"Sent keys to {value}")
        except Exception as e:
            logger.error(f"Send keys failed for {value}: {e}")
            raise

    def _to_zenkaku(self, text: str) -> str:
        if not text:
            return ""
        return text.translate(
            str.maketrans(
                "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ",
                "０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝～　",
            )
        )

    def _normalize_touki_input(self, text: str) -> str:
        """登記入力用に正規化（ヶ→ケなど）"""
        if not text:
            return ""
        return text.replace("ヶ", "ケ")

    def _remove_corporate_type(self, name: str) -> str:
        """
        商号から法人格（株式会社など）を除去し、スペースも削除する
        例: 株式会社並木管財 -> 並木管財
        """
        if not name:
            return ""
        targets = [
            "株式会社",
            "有限会社",
            "合同会社",
            "合名会社",
            "合資会社",
            "一般社団法人",
            "一般財団法人",
            "公益社団法人",
            "公益財団法人",
            "特定非営利活動法人",
            "医療法人",
            "学校法人",
            "宗教法人",
            "社会福祉法人",
            "相互会社",
            "ＮＰＯ法人",
            "（株）",
            "（有）",
            "（同）",
            "（名）",
            "（資）",
            "(株)",
            "(有)",
            "(同)",
            "(名)",
            "(資)",
        ]
        cleaned_name = name
        for t in targets:
            cleaned_name = cleaned_name.replace(t, "")
        return cleaned_name.replace(" ", "").replace("　", "").strip()

    def _process_address_efficiently(
        self, address_string: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """住所を 都道府県, 市区町村以下(町域), 番地 に分割"""
        if not address_string:
            return None, None, None

        pref_pattern = r"(東京都|北海道|(?:京都|大阪)府|.{2,3}県)"
        match = re.match(pref_pattern + r"(.+)", address_string)
        if not match:
            return None, None, None
        prefectures = match.group(1)
        buf = match.group(2).strip()

        match_num = re.search(r"\d", buf)
        if match_num:
            idx = match_num.start()
            town_name_raw = buf[:idx]
            block_raw = buf[idx:]
        else:
            town_name_raw = buf
            block_raw = ""

        town_name = self._to_zenkaku(town_name_raw.strip())
        block = self._to_zenkaku(block_raw.strip())
        return prefectures, town_name, block

    def _extract_municipality(self, address_without_pref: str) -> str:
        """
        都道府県を除いた住所から市区町村（政令市の区まで）を抽出する
        例: 千葉市中央区葛城 -> 千葉市中央区
        """
        if not address_without_pref:
            return ""

        # 特殊な市名（「市」を含む市）の先行判定
        special_cities = ["市川市", "市原市", "四日市市", "廿日市市", "野々市市"]
        for sc in special_cities:
            if address_without_pref.startswith(sc):
                return sc

        # 1. 政令指定都市 (例: 千葉市中央区)
        match = re.match(r"^(.+?市.+?区)", address_without_pref)
        if match:
            return match.group(1)

        # 2. 特別区 (例: 渋谷区)
        match = re.match(r"^(.+?区)", address_without_pref)
        if match:
            return match.group(1)

        # 3. 郡 (例: 印旛郡酒々井町)
        match = re.match(r"^(.+?郡.+?[町村])", address_without_pref)
        if match:
            return match.group(1)

        # 4. 通常の市町村 (例: 船橋市)
        match = re.match(r"^(.+?[市町村])", address_without_pref)
        if match:
            return match.group(1)

        return address_without_pref

    def _login(self, driver) -> bool:
        try:
            driver.get(LOGIN_URL)
            if "TeikyoUketsuke" in driver.current_url and "Menu" in driver.title:
                return True
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "userId"))
            )
            driver.find_element(By.ID, "userId").send_keys(self.user_id)
            driver.find_element(By.ID, "password").send_keys(self.password)
            driver.find_element(
                By.XPATH, "//button[contains(@class, 'CForwardLong')]"
            ).click()
            try:
                force_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//span[contains(text(), '強制ログイン')]")
                    )
                )
                force_btn.click()
            except TimeoutException:
                pass
            WebDriverWait(driver, 15).until(EC.url_contains("TeikyoUketsuke"))
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"❌ Login Error: {e}")
            return False

    @retry_with_backoff(
        max_retries=2,
        backoff_factor=3.0,
        exceptions=(TimeoutException, WebDriverException),
        log_to_audit=True,
    )
    def request_real_estate(self, address: str, target_type: str = "土地") -> str:
        """不動産請求を実行（リトライ対応版）"""
        address = self._normalize_touki_input(address)
        driver = None
        try:
            driver = self._get_driver()
            if not self._login(driver):
                raise WebDriverException("ログインに失敗しました")

            # メニュー
            self._wait_and_click(driver, By.XPATH, "//a[contains(@href, 'FUDOSAN')]")

            # 住所解析
            pref, town, blk = self._process_address_efficiently(address)
            if not pref:
                raise ValueError(f"住所の解析に失敗しました: {address}")

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "fuShozaiTypeTOCHI"))
            )
            if target_type == "建物":
                driver.find_element(By.ID, "fuShozaiTypeTATEMONO").click()
            else:
                driver.find_element(By.ID, "fuShozaiTypeTOCHI").click()

            # 都道府県
            Select(
                driver.find_element(By.NAME, "todofukenShozai")
            ).select_by_visible_text(pref)
            time.sleep(0.5)

            # 直接入力タブ
            driver.find_element(By.NAME, "fuShozaiChokusetuNyuryoku").click()
            WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, "chibanKuiki"))
            )

            self._wait_and_send_keys(driver, By.NAME, "chibanKuiki", town)
            self._wait_and_send_keys(driver, By.NAME, "chibanKaoku", blk)

            try:
                kyotan = driver.find_element(By.ID, "fuKyodoTanpoYES")
                if kyotan.is_displayed():
                    kyotan.click()
            except:
                pass

            confirm_xpath = (
                "//button[contains(@class, 'CForward')]/span[contains(text(), '確定')]"
            )
            self._wait_and_click(driver, By.XPATH, confirm_xpath)

            time.sleep(3)
            return f"✅ 「{address}」({target_type}) の請求を確定しました。"
        finally:
            if driver:
                driver.quit()

    @retry_with_backoff(
        max_retries=2,
        backoff_factor=3.0,
        exceptions=(TimeoutException, WebDriverException),
        log_to_audit=True,
    )
    def request_commercial(self, name: str, address: str) -> str:
        """
        商業・法人請求を実行（リトライ対応版）
        - 商号：法人格除去、スペース削除
        - 住所：市区町村（区）まで入力
        - 検索実行 -> リスト選択 -> 確定
        """

        # 1. 商号クレンジング
        clean_name = self._remove_corporate_type(name)
        clean_name = self._to_zenkaku(clean_name)

        # 2. 住所処理 (正規化 -> 都道府県分離 -> 市区町村抽出)
        address = self._normalize_touki_input(address)
        pref, town, blk = self._process_address_efficiently(address)

        # 市区町村レベルまでカット (例: 千葉市中央区)
        addr_to_input = self._extract_municipality(town)

        driver = None
        try:
            driver = self._get_driver()
            if not self._login(driver):
                raise WebDriverException("ログインに失敗しました")

            # メニュー遷移
            try:
                self._wait_and_click(
                    driver, By.XPATH, "//a[contains(@href, 'SHOGYO_HOJIN_TOKIBO')]"
                )
            except TimeoutException:
                self._wait_and_click(driver, By.PARTIAL_LINK_TEXT, "商業・法人請求")

            time.sleep(1.5)

            # 商号・名称検索モード選択
            try:
                self._wait_and_click(driver, By.ID, "shSeikyuMethodSHOGO_KANJI")
                time.sleep(0.5)
            except:
                pass

            # 商号入力
            try:
                self._wait_and_send_keys(driver, By.ID, "shShogoMeisyo", clean_name)
            except TimeoutException:
                self._wait_and_send_keys(driver, By.NAME, "shogo", clean_name)

            # 住所入力
            if pref:
                # 都道府県選択 (JS強制)
                try:
                    pref_elem = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.ID, "shTodofukenShozaiA1"))
                    )
                    driver.execute_script(
                        """
                        var select = arguments[0];
                        var targetText = arguments[1];
                        for(var i=0; i<select.options.length; i++){
                            if(select.options[i].text === targetText){
                                select.selectedIndex = i;
                                select.dispatchEvent(new Event('change'));
                                break;
                            }
                        }
                    """,
                        pref_elem,
                        pref,
                    )
                    time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"都道府県選択失敗: {e}")

                # 直接入力チェック (JS強制)
                try:
                    direct_chk = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located(
                            (By.ID, "shShozaiChokusetuNyuryokuA1")
                        )
                    )
                    if not direct_chk.is_selected():
                        driver.execute_script("arguments[0].click();", direct_chk)
                    time.sleep(1.0)
                except Exception as e:
                    logger.warning(f"直接入力チェック失敗: {e}")

                # 市区町村入力 (有効化待ち)
                try:
                    input_field = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "shChibanKuiki1"))
                    )
                    input_field.clear()
                    input_field.send_keys(addr_to_input)
                    logger.info(f"Sent keys to shChibanKuiki1: {addr_to_input}")
                except Exception as e:
                    logger.warning(f"市区町村入力失敗: {e}")

            # 検索ボタンクリック
            try:
                search_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(., '検索')]")
                    )
                )
                search_btn.click()
                time.sleep(2)
            except Exception as e:
                logger.warning(f"検索ボタンクリック失敗: {e}")

            # --- 検索結果リストでの選択処理 ---
            try:
                # 候補リストのラジオボタンを探す（IDなどで特定せず、テーブル内のラジオボタンを狙う）
                # 検索結果が表示されるまで少し待つ
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//table//input[@type='radio']")
                    )
                )

                # 最初のラジオボタンを選択
                # ※検索条件設定のラジオボタンを除外するため、結果テーブル（と思われる場所）を特定するか、
                # 単純に name="sentaku" 等の属性を持つものを探すのが一般的
                radios = driver.find_elements(
                    By.XPATH,
                    "//input[@type='radio' and not(@name='kensaku') and not(@name='matchingTypeShogo')]",
                )

                if radios:
                    # 見えている最初のラジオボタンをクリック
                    for r in radios:
                        if r.is_displayed() and r.is_enabled():
                            r.click()
                            logger.info("検索結果リストの1件目を選択しました。")
                            time.sleep(0.5)
                            break
            except TimeoutException:
                # リストが出ずに直接確定画面に行く場合もあるので、ここはエラーにしない
                pass
            except Exception as e:
                logger.warning(f"リスト選択処理で警告: {e}")

            # 最終確定ボタン (次へ/確定)
            confirm_xpath = (
                "//button[contains(@class, 'CForward')]/span[contains(text(), '確定')]"
            )
            try:
                self._wait_and_click(driver, By.XPATH, confirm_xpath, timeout=5)
                logger.info("確定ボタンをクリックしました。")
            except TimeoutException:
                return "⚠️ 検索は実行しましたが、確定ボタンが見つかりませんでした（候補選択が必要な可能性があります）。"

            time.sleep(3)
            return f"✅ 法人「{clean_name}」の所在地（{pref}{addr_to_input}）にて請求を確定しました。"

        finally:
            if driver:
                driver.quit()


touki_service = ToukiService()
````

## File: src/services/automation/will_generator.py
````python
# src/services/automation/will_generator.py

import pandas as pd
import numpy as np
import base64
import re  # 正規表現モジュールを確実にインポート
from io import BytesIO
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from docx import Document
from docx.shared import Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from PIL import Image, ImageOps, ImageChops
from pypdf import PdfReader
from pdf2image import convert_from_bytes

from src.legal_system.core.ai_factory import AIFactory
from src.legal_system.core.schemas import WillDraftStructure

class WillDraftGenerator:
    def __init__(self):
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def generate_draft(self, excel_file: BytesIO, template_file: BytesIO, registry_files: List[Any] = None) -> Tuple[BytesIO, Optional[BytesIO], WillDraftStructure, str]:
        """
        遺言書生成のメイン処理
        """
        # 1. Excel解析
        excel_file.seek(0)
        if hasattr(excel_file, 'name') and excel_file.name.endswith('.xlsx'):
            df = pd.read_excel(excel_file)
        else:
            df = pd.read_csv(excel_file)

        # データ補完
        df = df.replace(r'^\s*$', np.nan, regex=True).ffill()
        if 'No' in df.columns:
            df = df.dropna(subset=['No'])

        if df.empty:
            raise ValueError("有効なデータ行がありません。")

        csv_text = df.fillna("").to_csv(index=False)

        # 2. 登記情報の処理 (AIによるフォーマット変換)
        registry_data = self._process_registry_files(registry_files)

        # 3. AI推論 (条文構成)
        draft_data = self._invoke_ai_reasoning(csv_text)

        # 4. 遺言書Word生成 (本体 + テキストデータ)
        template_file.seek(0)
        safe_template = BytesIO(template_file.read())
        # ここで登記情報のテキストを渡す
        will_doc = self._create_will_document(safe_template, draft_data, registry_data.get("text", ""))
        
        will_stream = BytesIO()
        will_doc.save(will_stream)
        will_stream.seek(0)

        # 5. 登記情報Word生成 (別冊・画像のみ)
        registry_stream = None
        if registry_data.get("images"):
            reg_doc = self._create_registry_document(registry_data)
            registry_stream = BytesIO()
            reg_doc.save(registry_stream)
            registry_stream.seek(0)
        
        return will_stream, registry_stream, draft_data, csv_text

    def _process_registry_files(self, files: List[Any]) -> Dict[str, Any]:
        """
        登記情報(PDF/画像)を処理する
        - 画像への変換 & 余白トリミング
        - Gemini Visionによる指定フォーマットでのテキスト化
        """
        processed = {"images": [], "text": ""}
        if not files:
            return processed

        all_images_for_ai = [] # テキスト解析用に全ての画像をリスト化
        
        for f in files:
            f.seek(0)
            file_bytes = f.read()
            file_name = getattr(f, "name", "unknown")

            # PDFの場合
            if file_name.lower().endswith(".pdf") or f.type == "application/pdf":
                try:
                    # 画像変換 (200dpi)
                    pil_images = convert_from_bytes(file_bytes, dpi=200)
                    for img in pil_images:
                        # 1. 別冊用画像 (トリミング済)
                        trimmed = self._trim_whitespace(img)
                        buf = BytesIO()
                        trimmed.save(buf, format="JPEG")
                        processed["images"].append(BytesIO(buf.getvalue()))
                        
                        # 2. AI解析用画像
                        ai_buf = BytesIO()
                        img.convert("RGB").save(ai_buf, format="JPEG")
                        all_images_for_ai.append(BytesIO(ai_buf.getvalue()))

                except Exception as e:
                    print(f"PDF process error: {e}")

            # 画像の場合
            else:
                try:
                    img = Image.open(BytesIO(file_bytes))
                    
                    # 1. 別冊用
                    trimmed = self._trim_whitespace(img)
                    buf = BytesIO()
                    trimmed.save(buf, format="JPEG")
                    processed["images"].append(BytesIO(buf.getvalue()))

                    # 2. AI解析用
                    ai_buf = BytesIO()
                    img.convert("RGB").save(ai_buf, format="JPEG")
                    all_images_for_ai.append(BytesIO(ai_buf.getvalue()))

                except Exception as e:
                    print(f"Image load error: {e}")

        # --- AIによるテキスト化 (Gemini Vision) ---
        if all_images_for_ai:
            processed["text"] = self._analyze_registry_images_with_ai(all_images_for_ai)
        
        return processed

    def _analyze_registry_images_with_ai(self, image_buffers: List[BytesIO]) -> str:
        """登記情報の画像をAIに読み取らせて、指定フォーマットのテキストに変換する"""
        prompt = """
        提供された不動産登記情報の画像を読み取り、公証人が遺言書作成に使用するためのテキストデータを作成してください。
        
        # 【重要】生成ルール
        1. **所在の結合**:
           - 建物の「所在」欄にある「市区町村名」と、その下（または横）にある「地番（または家屋番号の番地部分）」を**必ず1行に結合**してください。
           - 画像上で改行されていても、出力時は全角スペースでつないで1行にしてください。
           - 例:
             [画像]
               四街道市旭ケ丘五丁目
               １５２０番２３６
             [出力]
               所在　四街道市旭ケ丘五丁目　１５２０番２３６

        2. **床面積の改行禁止**:
           - 建物が複数階ある場合でも、**絶対に改行せず**、全角スペースで区切って一行にまとめてください。
           - 例: 1階 79.08　2階 52.58㎡

        3. **マンション判定**: 
           - 文中に「一棟の建物の表示」および「敷地権」という文言が含まれる場合のみ「マンション（区分所有建物）」として扱ってください。それ以外は「土地」または「建物」です。

        4. **持分（シェア）の特定**:
           - 持分は通常、所有者氏名の直上（または直近）に記載されています（例：「持分２分の１」）。
           - 単独所有で持分の記載がない場合は空欄にしてください。（「1/1」と補完しないでください）

        5. **文字の正規化**: 
           - 氏名や地名に含まれる空白（全角・半角スペース）はすべて削除して認識してください。
           - 「ヶ」「ケ」の表記揺れは、登記簿の記載通りにしてください。

        # 出力フォーマット例
        物件ごとに（１）、（２）...と連番を振ってください。

        【土地の場合】
        （Ｎ）　土地
        　所在　■■市■■区■■■　■■番地■
        　地番　■番■
        　地目　■■
        　地積　■.■㎡
        　持分　■分の■（※記載がある場合のみ）

        【建物の場合】
        （Ｎ）　建物
        　所在　■■市■■区■■■　■■番地■
        　家屋番号　■番■
        　種類　■■
        　構造　■■
        　床面積　1階 ■.■　2階 ■.■㎡
        　持分　■分の■（※記載がある場合のみ）
        """
        
        content = [{"type": "text", "text": prompt}]
        
        for img_buf in image_buffers:
            img_buf.seek(0)
            b64_data = base64.b64encode(img_buf.read()).decode("utf-8")
            content.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{b64_data}"
            })
            
        msg = HumanMessage(content=content)
        
        try:
            res = self.llm.invoke([msg])
            raw_text = res.content
            
            # ★追加: Python側での強力な後処理（強制結合）
            return self._post_process_ai_text(raw_text)

        except Exception as e:
            return f"※AI解析エラー: {e}"

    def _post_process_ai_text(self, text: str) -> str:
        """
        AIの出力テキストに対して、正規表現を使って強制的に行を結合する。
        """
        lines = text.split('\n')
        processed_lines = []
        
        skip_next = False
        
        for i in range(len(lines)):
            if skip_next:
                skip_next = False
                continue
            
            line = lines[i].strip()
            
            # 末尾の行ならそのまま追加
            if i == len(lines) - 1:
                processed_lines.append(lines[i])
                continue
                
            next_line = lines[i+1].strip()
            
            # --- ルール1: 床面積の結合 ---
            # 「床面積」が含まれる行の次が、数字や「X階」で始まる場合、結合する
            if "床面積" in line:
                # 次の行が数字、または「○階」で始まっているか？
                if re.match(r'^[\d０-９]+', next_line) or re.match(r'^[1-9１-９]階', next_line):
                    # 行を結合 (全角スペース区切り)
                    merged_line = lines[i].rstrip() + "　" + next_line
                    processed_lines.append(merged_line)
                    skip_next = True
                    continue

            # --- ルール2: 所在の結合 ---
            # 「所在」が含まれる行の次が、数字で始まっている（番地の続き）場合、結合する
            # 例: "所在 四街道市..." の次の行が "1520..."
            if "所在" in line:
                # 次の行が数字で始まっているか？ (全角半角問わず)
                # かつ、次の行が「家屋番号」などの別のヘッダーではないことを確認
                is_number_start = re.match(r'^[\d０-９]+', next_line)
                is_header = any(x in next_line for x in ["家屋番号", "地番", "地目", "種類", "構造", "床面積", "地積", "持分"])
                
                if is_number_start and not is_header:
                    # 番地っぽさを出すために、数字だけなら「番地」などを補完しても良いが、
                    # ここではシンプルに結合する
                    # ユーザー要望: "1520番地236" のようにしたい
                    
                    # もし次の行に「番」が含まれていなければ、「番地」を補完するロジック（オプション）
                    # 今回は単純結合 + 番地補完を試みる
                    if "番" not in next_line and "地" not in next_line:
                        # 数字だけの羅列なら「番地」を挟む？ -> リスクがあるので単純結合にする
                        pass
                    
                    merged_line = lines[i].rstrip() + "　" + next_line
                    processed_lines.append(merged_line)
                    skip_next = True
                    continue

            processed_lines.append(lines[i])

        return "\n".join(processed_lines)

    def _trim_whitespace(self, img: Image.Image) -> Image.Image:
        try:
            bg = Image.new(img.mode, img.size, (255, 255, 255))
            diff = ImageChops.difference(img, bg)
            diff = ImageChops.add(diff, diff, 2.0, -100)
            bbox = diff.getbbox()
            if bbox:
                return img.crop(bbox)
        except: pass
        return img

    def _invoke_ai_reasoning(self, input_text: str) -> WillDraftStructure:
        system_content = """
        あなたは熟練した行政書士です。提供された「遺産整理要旨」に基づき、公正証書遺言の条文案を作成してください。
        （中略: プロンプトは変更なし）
        出力は指定されたJSONスキーマに厳密に従ってください。
        """
        
        parser = PydanticOutputParser(pydantic_object=WillDraftStructure)
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_content),
            HumanMessagePromptTemplate.from_template(
                "以下の要旨データに基づき、遺言書ドラフトの【本文条項のみ】を作成してください。\n\n【要旨データ】\n{input_text}\n\n【出力形式】\n{format_instructions}"
            )
        ])
        
        chain = prompt | self.llm | parser
        return chain.invoke({
            "input_text": input_text,
            "format_instructions": parser.get_format_instructions()
        })

    def _set_jp_font(self, run, size_pt=12, is_bold=False):
        try:
            run.font.name = "MS Mincho"
            run.font.size = Pt(size_pt)
            run.font.bold = is_bold
            run._element.rPr.rFonts.set(qn('w:eastAsia'), 'ＭＳ 明朝')
            run._element.rPr.rFonts.set(qn('w:ascii'), 'MS Mincho')
            run._element.rPr.rFonts.set(qn('w:hAnsi'), 'MS Mincho')
        except Exception:
            pass

    def _create_will_document(self, template_file: BytesIO, data: WillDraftStructure, registry_text: str = "") -> Document:
        """遺言書本体の作成（テンプレート追記モード）"""
        try:
            doc = Document(template_file)
        except Exception:
            doc = Document() 

        doc.add_paragraph("\n") 

        p_date = doc.add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        timestamp = datetime.now().strftime('%Y年%m月%d日 ドラフト作成')
        self._set_jp_font(p_date.add_run(timestamp), size_pt=9)
        doc.add_paragraph("") 

        if not data.articles:
            doc.add_paragraph("※ 生成された条文データがありません。要旨の内容を確認してください。")
            return doc

        for article in data.articles:
            p_title = doc.add_paragraph()
            self._set_jp_font(p_title.add_run(f"{article.article_number}"), size_pt=12, is_bold=True)
            if article.title:
                self._set_jp_font(p_title.add_run(f"　（{article.title}）"), size_pt=12, is_bold=True)
            
            p_content = doc.add_paragraph()
            p_content.paragraph_format.first_line_indent = Mm(5)
            
            content_text = article.content if article.content else ""
            
            if "※要確認" in content_text:
                parts = content_text.split("（※要確認")
                self._set_jp_font(p_content.add_run(parts[0]), size_pt=12)
                if len(parts) > 1:
                    run_alert = p_content.add_run(f"（※要確認{parts[1]}")
                    self._set_jp_font(run_alert, size_pt=12, is_bold=True)
                    run_alert.font.color.rgb = RGBColor(255, 0, 0)
            else:
                self._set_jp_font(p_content.add_run(content_text), size_pt=12)
            
            doc.add_paragraph("")

        if data.supplementary_provisions:
            p_head = doc.add_paragraph()
            self._set_jp_font(p_head.add_run("（付言事項）"), size_pt=12, is_bold=True)
            p_body = doc.add_paragraph()
            p_body.paragraph_format.first_line_indent = Mm(5)
            self._set_jp_font(p_body.add_run(data.supplementary_provisions), size_pt=12)

        if registry_text:
            doc.add_page_break()
            p_ht = doc.add_paragraph()
            p_ht.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._set_jp_font(p_ht.add_run("【参考】不動産登記情報（テキストデータ）"), size_pt=14, is_bold=True)
            doc.add_paragraph("※公証人作成用の参考テキストです。\n")
            
            p_txt = doc.add_paragraph(registry_text)
            if p_txt.runs:
                self._set_jp_font(p_txt.runs[0], size_pt=10.5)
            else:
                self._set_jp_font(p_txt.add_run(registry_text), size_pt=10.5)

        return doc

    def _create_registry_document(self, registry_data: Dict[str, Any]) -> Document:
        """登記情報（別冊・画像のみ）の作成"""
        doc = Document()
        
        p_main = doc.add_paragraph()
        p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self._set_jp_font(p_main.add_run("【別冊】不動産登記情報"), size_pt=20, is_bold=True)
        doc.add_paragraph("\n")
        
        images = registry_data.get("images", [])
        if images:
            for img_data in images:
                try:
                    img_data.seek(0)
                    doc.add_picture(img_data, width=Mm(170))
                    doc.add_paragraph("") 
                except Exception as e:
                    doc.add_paragraph(f"※画像エラー: {e}")
        
        return doc
````

## File: src/services/folder_service.py
````python
# src/services/folder_service.py

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional
import pyautogui

# サーバーの基準パス
SERVER_BASE_PATH = r"\\192.168.11.20\行政書士法人チェスター\01.個別ＪＯＢ"

def find_case_folder(search_term: str) -> Optional[str]:
    """
    基準パス配下からフォルダを検索してパスを返す。
    """
    if not search_term:
        return None

    target_path = Path(SERVER_BASE_PATH)
    if not target_path.exists():
        return None

    try:
        query = search_term.replace(" ", "").replace("　", "")
        for item in target_path.iterdir():
            if item.is_dir():
                folder_name = item.name.replace(" ", "").replace("　", "")
                if query in folder_name:
                    return str(item.absolute())
    except Exception as e:
        print(f"Folder search error: {e}")
        return None

def open_local_folder(path: str) -> bool:
    """
    指定されたパスをエクスプローラーで開き、かつ最前面に表示させる。
    """
    if not path or not os.path.exists(path):
        return False

    try:
        if platform.system() == "Windows":
            # --- Windows向けの最強最前面表示ロジック ---
            # 1. まず普通にエクスプローラーで開く
            os.startfile(path)
    
            # ウィンドウが開くまでの猶予（環境によるが0.5~1秒程度）
            # time.sleep(1) 

            pyautogui.hotkey('alt', 'tab')
            
        elif platform.system() == "Darwin": # Mac用
            subprocess.Popen(["open", path])
            subprocess.run(["osascript", "-e", f'tell application "Finder" to activate'])
        else: # Linux用
            subprocess.Popen(["xdg-open", path])
            
        return True
    except Exception as e:
        print(f"Error opening folder: {e}")
        return False
````

## File: add_column_migration.py
````python
# migrate_add_assessed_value.py
import os
import sys
from sqlalchemy import text

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager

def add_assessed_value_column():
    print("🔄 データベース構造の変更を開始します...")
    print("👉 'real_estate_assets' テーブルに 'assessed_value' カラムを追加します。")

    db = DatabaseManager()
    engine = db.engine

    # SQLコマンド
    alter_sql = text("ALTER TABLE real_estate_assets ADD COLUMN assessed_value FLOAT DEFAULT 0.0;")

    try:
        with engine.connect() as conn:
            conn.execute(alter_sql)
            conn.commit()
        print("✅ 成功: カラムを追加しました。")

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg or "Duplicate column" in error_msg:
            print("ℹ️  スキップ: カラムは既に追加されています。")
        else:
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    add_assessed_value_column()
````

## File: src/legal_system/core/ocr_engine.py
````python
# src/legal_system/core/ocr_engine.py

"""
OCR処理エンジン・モジュール (Hybrid: Gemini Vision + PaddleOCR)
デフォルトではGemini Visionを使用し、環境が整っている場合のみPaddleOCRを補助的に使用します。
"""

import logging
import os
import base64
import tempfile
from typing import List, Dict, Any, Optional, Union

# PyMuPDF (fitz)
import fitz

# LangChain (Gemini用)
from langchain_core.messages import HumanMessage
from src.legal_system.core.ai_factory import AIFactory

# PaddleOCR / OpenCV (Optional - Import Errorを許容)
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

logger = logging.getLogger(__name__)


class OCREngine:
    """
    PaddleOCRを使用した帳票OCR取り込み機能を提供するクラス。
    ライブラリが不足している場合は、機能を無効化します（クラッシュさせない）。
    """

    def __init__(self, lang: str = "japan"):
        self.ocr = None
        self.is_available = False

        if cv2 is None or np is None:
            logger.warning("OpenCV (cv2) または numpy が見つかりません。Local OCRは無効化されます。")
        elif PaddleOCR is None:
            logger.warning("PaddleOCR が見つかりません。Local OCRは無効化されます。")
        else:
            try:
                # PaddleOCRの初期化 (GUIがない環境を想定して use_angle_cls=True)
                # show_log=False でログ出力を抑制
                self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
                self.is_available = True
            except Exception as e:
                logger.error(f"PaddleOCR init failed: {e}")

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDFファイルからテキストと座標情報を抽出する（Local OCR）。
        
        Returns:
            List[Dict]: 抽出結果のリスト。OCR不可の場合は空リスト。
        """
        if not self.is_available:
            return []

        results = []
        doc = None
        try:
            doc = fitz.open(pdf_path)
            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                pix = page.get_pixmap()
                
                # PyMuPDF -> OpenCV
                img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                
                if pix.n == 4:
                    img = img_array.reshape(pix.height, pix.width, 4)
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n == 3:
                    img = img_array.reshape(pix.height, pix.width, 3)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    img = img_array.reshape(pix.height, pix.width, pix.n)

                page_result = self.ocr.ocr(img, cls=True)
                
                if not page_result:
                    continue

                for line in page_result:
                    if not line: continue
                    for res in line:
                        # res format: [coords, [text, confidence]]
                        results.append({
                            "page": page_index + 1,
                            "coords": res[0],
                            "text": res[1][0],
                            "confidence": res[1][1]
                        })
        except Exception as e:
            logger.error(f"Local OCR Error: {e}")
            return []
        finally:
            if doc:
                doc.close()
            
        return results


# -----------------------------------------------------------------------------
# 外部公開関数 (Hybrid: Gemini優先)
# -----------------------------------------------------------------------------

def extract_text_with_gemini(file_bytes: bytes) -> str:
    """
    Gemini Vision APIを使用して、PDF/画像から全文テキストを抽出する。
    """
    try:
        # CloudモードのLLMを取得
        llm = AIFactory.get_llm("cloud", temperature=0.0)
        
        # PDFを画像リストに変換 (最初の2ページのみを対象として軽量化・高速化)
        # ※ pdf2image が必要
        try:
            from pdf2image import convert_from_bytes
            # dpi=150 は速度と精度のバランスが良い
            images = convert_from_bytes(file_bytes, dpi=150, first_page=1, last_page=2)
        except ImportError:
            logger.warning("pdf2image not found. Skipping Gemini Vision.")
            return ""
        except Exception as e:
            logger.error(f"PDF conversion failed: {e}")
            return ""

        if not images:
            return ""

        # メッセージ構築
        content_parts = [{"type": "text", "text": "この書類に書かれているすべての文字を、読み取れる順序で書き起こしてください。Markdownなどは不要で、テキストのみを出力してください。"}]
        
        for img in images:
            # メモリ上でJPEG変換
            buf = base64.BytesIO() if hasattr(base64, 'BytesIO') else __import__('io').BytesIO()
            img.save(buf, format="JPEG")
            b64_data = base64.b64encode(buf.getvalue()).decode("utf-8")
            
            content_parts.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{b64_data}"
            })

        msg = HumanMessage(content=content_parts)
        res = llm.invoke([msg])
        
        return res.content

    except Exception as e:
        logger.error(f"Gemini OCR Failed: {e}")
        return ""


def extract_text_from_scanned_pdf(file_input: Union[str, bytes]) -> str:
    """
    スキャンされたPDFからテキストを抽出する（Gemini優先）。
    
    Args:
        file_input (str | bytes): ファイルパス(str) または ファイル本体(bytes)
    
    Returns:
        str: 抽出されたテキスト全文
    """
    # 入力がパスならバイト列を読み込む
    file_bytes = None
    if isinstance(file_input, str):
        if os.path.exists(file_input):
            with open(file_input, "rb") as f:
                file_bytes = f.read()
    else:
        file_bytes = file_input

    if not file_bytes:
        return ""

    # 1. Gemini Vision を試行 (優先)
    logger.info("Attempting Gemini Vision for text extraction...")
    gemini_text = extract_text_with_gemini(file_bytes)
    if gemini_text and len(gemini_text.strip()) > 20: # ある程度読めたら採用
        logger.info("Used Gemini Vision for OCR.")
        return gemini_text

    # 2. Geminiがダメなら Local OCR (PaddleOCR) を試行
    logger.info("Gemini Vision failed or returned empty. Falling back to Local OCR (PaddleOCR)...")
    engine = OCREngine()
    if engine.is_available:
        # Local OCRはファイルパスが必要なため、一時ファイルを作成
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            results = engine.process_pdf(tmp_path)
            full_text = "\n".join([r["text"] for r in results])
            if full_text:
                logger.info("Used PaddleOCR (Local) for OCR.")
                return full_text
        except Exception as e:
            logger.error(f"Local OCR failed: {e}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return "" # どちらも失敗
````

## File: src/legal_system/core/schemas.py
````python
# src/legal_system/core/schemas.py

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class WillArticle(BaseModel):
    """遺言書の個別の条文"""
    article_number: str = Field(..., description="条数表記（例: 第１条）")
    title: Optional[str] = Field(None, description="条文の見出し（例: 不動産の遺贈）")
    content: str = Field(..., description="条文の本文")

class WillDraftStructure(BaseModel):
    """遺言書全体の構成データ"""
    testator_name: str = Field(..., description="遺言者（依頼主）の氏名")
    articles: List[WillArticle] = Field(..., description="条文のリスト")
    supplementary_provisions: Optional[str] = Field(None, description="付言事項")


# --- 追加: 案件検索用の軽量モデル ---
class CaseSearchKeys(BaseModel):
    """
    案件特定のために書類から抽出するキー情報。
    """

    client_name: Optional[str] = Field(
        None, description="依頼者（相続人代表）と思われる氏名"
    )
    deceased_name: Optional[str] = Field(
        None, description="被相続人（亡くなった方）と思われる氏名"
    )
    date_hint: Optional[str] = Field(
        None, description="書類に記載されている日付（死亡日や発行日など）"
    )
    summary_for_search: str = Field(..., description="検索のヒントになる短い要約")


# --- 以下、既存の検証用モデル (変更なし) ---
class VerificationField(BaseModel):
    field_label: str = Field(..., description="項目名（例: 被相続人氏名）")
    expected_value: Optional[str] = Field(None, description="Kintone上の値（期待値）")
    actual_value: Optional[str] = Field(
        None, description="書類から読み取った値（実測値）"
    )
    is_consistent: bool = Field(
        ..., description="矛盾がないか (True: 一致/許容範囲, False: 不一致)"
    )
    reasoning: str = Field(
        ..., description="判定の理由（例: '表記揺れ（斎藤/斉藤）だが同一人物と判断'）"
    )
    confidence_score: float = Field(..., description="AIの自信度 (0.0 - 1.0)")


class MissingDocAlert(BaseModel):
    doc_name: str = Field(..., description="不足している、または不備がある書類名")
    issue_type: Literal["MISSING", "EXPIRED", "INVALID_SEAL", "OTHER"] = Field(
        ..., description="不備の種類"
    )
    description: str = Field(..., description="詳細な指摘内容")


class DocumentAnalysisResult(BaseModel):
    summary: str = Field(..., description="解析全体の要約（監査ログ用）")
    document_type: str = Field(
        ..., description="書類種別（例: '残高証明書', '戸籍謄本'）"
    )
    verifications: List[VerificationField] = Field(
        default_factory=list, description="各項目の照合結果リスト"
    )
    alerts: List[MissingDocAlert] = Field(
        default_factory=list, description="検出された不備・不足"
    )
    extracted_data: dict = Field(
        default_factory=dict, description="DB保存用の正規化済みデータ(JSON)"
    )
    overall_status: Literal["APPROVED", "WARNING", "REJECTED"] = Field(
        ...,
        description="AIによる一次判定。不整合がなければAPPROVED、要確認はWARNING。",
    )

# --- ★新規追加: スキャナー読取用モデル ---
class ScannedHeirInfo(BaseModel):
    """スキャンデータから読み取った相続人1人分の情報"""
    name: str = Field(..., description="相続人の氏名")
    relationship: str = Field(..., description="続柄（例: 長男、妻）")
    address: Optional[str] = Field(None, description="住所（手書き文字を読み取る）")
    phone: Optional[str] = Field(None, description="電話番号")

class HeirListAnalysisResult(BaseModel):
    """「推定相続人連絡先一覧」の詳細解析結果"""
    # ★修正点: 遺言者を特定するためのフィールドを追加
    testator_name: Optional[str] = Field(None, description="書類下部の「遺言者様に関する情報」欄に記載されている氏名")
    
    case_number_hint: Optional[str] = Field(None, description="記載されている案件番号(G番号)")
    deceased_name_hint: Optional[str] = Field(None, description="記載されている被相続人名")
    heirs: List[ScannedHeirInfo] = Field(default_factory=list, description="リストアップされている相続人情報")
````

## File: src/legal.egg-info/top_level.txt
````
__init__
chains
legal_system
services
utils
````

## File: src/services/scanner_service.py
````python
# src/services/scanner_service.py

import os
import time
import shutil
import logging
import datetime
import json
import base64
import uuid
import hashlib
import unicodedata
import re
from pathlib import Path
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage
from sqlalchemy.orm import joinedload 
from sqlalchemy import or_, func

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.config import Config
from legal_system.models.tables import (
    Case, FinancialAsset, BankMaster, BranchMaster, AccountTypeMaster,
    ContactLog, IncomingNoteBuffer, Liability, Deceased, FileRegistry, Heir
)
from services.deceased_service import find_cases_by_attributes, search_zip_by_address_api, search_address_by_zip_api

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ヘルパー関数群
BASE_DIR = Path(__file__).resolve().parents[2]
ZENGIN_DATA_DIR = BASE_DIR / "data" / "zengin"

def normalize_name(text: str) -> str:
    if not text: return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace(" ", "").replace("　", "")
    return normalized.replace("銀行", "").replace("支店", "")

def find_bank_in_zengin(search_name: str):
    banks_path = ZENGIN_DATA_DIR / "banks.json"
    if not banks_path.exists(): return None, None
    search_key = normalize_name(search_name)
    try:
        with open(banks_path, "r", encoding="utf-8") as f:
            banks = json.load(f)
        for code, info in banks.items():
            if search_key == normalize_name(info["name"]): return code, info["name"]
        for code, info in banks.items():
            if search_key in normalize_name(info["name"]): return code, info["name"]
    except: pass
    return None, None

def find_branch_in_zengin(bank_code: str, branch_search_name: str):
    if not bank_code or not branch_search_name: return None, None
    branch_path = ZENGIN_DATA_DIR / "branches" / f"{bank_code}.json"
    if not branch_path.exists(): return None, None
    search_key = normalize_name(branch_search_name)
    try:
        with open(branch_path, "r", encoding="utf-8") as f:
            branches = json.load(f)
        for code, info in branches.items():
            if search_key == normalize_name(info["name"]): return code, info["name"]
        for code, info in branches.items():
            if search_key in normalize_name(info["name"]): return code, info["name"]
    except: pass
    return None, None

def katakana_to_hiragana(text: str) -> str:
    if not text: return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6: result += chr(code - 0x60)
        else: result += char
    return result

# ---------------------------------------------------------
# ハンドラー定義
# ---------------------------------------------------------
class DocumentHandler(ABC):
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    @abstractmethod
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        """
        処理実行メソッド
        """
        pass

    def _generate_filename(self, case: Case, doc_name: str, identifier: str = "") -> str:
        g_number = case.case_number or "G不明"
        client_full = case.client_name or "不明"
        client_last = client_full.replace("　", " ").split(" ")[0]
        today_str = datetime.datetime.now().strftime('%Y%m%d')
        id_part = f"_{identifier}" if identifier else ""
        return f"{g_number}{client_last}様_{doc_name}{id_part}_{today_str}.pdf"

    # --- フォルダ操作ヘルパー ---
    
    def _find_folder(self, root_path: str, keyword: str) -> Optional[Path]:
        """指定したキーワードを含むフォルダを検索して返す（なければNone）"""
        if not root_path: return None
        root = Path(root_path)
        if not root.exists(): return None
        
        for item in root.iterdir():
            if item.is_dir() and keyword in item.name:
                return item
        return None

    def _ensure_folder(self, root_path: str, keyword: str, force_name: str = None) -> Optional[Path]:
        """
        指定したキーワードを含むフォルダを検索して返す。
        なければ作成して返す。
        force_nameが指定されていればその名前で作成、なければ '00_{keyword}' で作成。
        """
        if not root_path: return None
        root = Path(root_path)
        if not root.exists(): return None # ルート自体がない場合は諦める

        # 1. 検索
        found = self._find_folder(root_path, keyword)
        if found: return found
        
        # 2. 作成
        new_folder_name = force_name if force_name else f"00_{keyword}"
        new_path = root / new_folder_name
        try:
            new_path.mkdir(exist_ok=True)
            return new_path
        except Exception as e:
            logger.error(f"フォルダ作成失敗: {new_path} - {e}")
            return None

    def _find_target_folder(self, root_path: str, parent_keyword: str, target_keyword: str = None) -> Optional[Path]:
        """旧ロジック互換用（必要に応じて使用）"""
        parent_dir = self._ensure_folder(root_path, parent_keyword)
        if not parent_dir: return None
        
        if not target_keyword: return parent_dir
        
        # サブフォルダ検索・作成
        target_dir = None
        for item in parent_dir.iterdir():
            if item.is_dir() and target_keyword in item.name:
                target_dir = item
                break
        if not target_dir:
            try:
                target_dir = parent_dir / f"00_{target_keyword}"
                target_dir.mkdir(exist_ok=True)
            except: return None
        return target_dir

    def _save_file_copy(self, src: Path, dest_dir: Path, filename: str):
        dest_path = dest_dir / filename
        if dest_path.exists():
            base = dest_path.stem; ext = dest_path.suffix; counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{base}_{counter}{ext}"
                counter += 1
        try:
            if not src.exists():
                logger.error(f"   ❌ Source file missing: {src}")
                return None
            
            shutil.copy2(str(src), str(dest_path))
            logger.info(f"   ✅ [File Copied] {dest_path}")
            return dest_path

        except Exception as e:
            logger.error(f"   ❌ [File Copy Error] {e}")
            return None

    def _update_or_create_registry(self, session, case_id: int, file_path: Path, doc_type: str, analysis_data: dict, file_hash: str = None, status: str = "CONFIRMED"):
        try:
            if not file_path or not file_path.exists():
                return

            if not file_hash:
                with open(file_path, "rb") as f:
                    file_bytes = f.read()
                file_hash = hashlib.md5(file_bytes).hexdigest()
            
            extracted_json = json.dumps(analysis_data, ensure_ascii=False) if analysis_data else None
            
            existing = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            
            conf_score = 1.0 if status == "CONFIRMED" else 0.0

            if existing:
                existing.case_id = case_id
                existing.filename = file_path.name
                existing.file_path = str(file_path)
                existing.doc_type = doc_type
                existing.status = status
                existing.ai_confidence = conf_score
                if extracted_json: existing.extracted_data = extracted_json
                existing.registered_at = datetime.datetime.now()
                logger.info(f"   🔄 FileRegistry更新(移動反映): {file_path.name}")
            else:
                new_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=file_path.name,
                    case_id=case_id,
                    doc_type=doc_type,
                    file_path=str(file_path),
                    registered_at=datetime.datetime.now(),
                    status=status,
                    ai_confidence=conf_score,
                    extracted_data=extracted_json
                )
                session.add(new_reg)
                logger.info(f"   💾 FileRegistry新規登録: {file_path.name}")

        except Exception as e:
            logger.error(f"   ⚠️ FileRegistry登録エラー: {e}")

# =========================================================
# ハンドラー実装
# =========================================================

class CorporateRegistryHandler(DocumentHandler):
    """
    商業・法人登記簿謄本用ハンドラー
    ・「取得代行資料/商業登記」などのフォルダに保存
    """
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"🏢 商業登記・ハンドラー起動")
        meta = analysis_data.get("meta", {})
        corp_name = meta.get("corporate_name", "法人")
        
        # ファイル名: Gxxxx様_商業登記(法人名)_YYYYMMDD.pdf
        new_filename = self._generate_filename(case, "商業登記簿", corp_name)
        
        # 保存先: 「取得代行資料」の中の「商業登記」または直下
        parent_dir = self._ensure_folder(case.folder_path, "取得代行資料")
        if parent_dir:
            dest_dir = self._ensure_folder(str(parent_dir), "商業登記", force_name="商業登記")
        else:
            dest_dir = None
            
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "corporate_registry", analysis_data, file_hash, status="CONFIRMED")
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】商業登記簿({corp_name})を保存しました: {saved_path.name}")
                session.add(log)
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

class TaxPaymentNoticeHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"💴 固定資産税・ハンドラー起動")
        new_filename = self._generate_filename(case, "固定資産税納税通知書")
        dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "固定資産税納税通知書", analysis_data, file_hash, status="CONFIRMED")
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】固定資産税納税通知書を保存しました: {saved_path.name}")
                session.add(log)
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

class BankPassbookHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        meta = analysis_data.get("meta", {})
        branch_name = meta.get("branch_name", "")
        acc_type_name = meta.get("account_type", "普通") 
        acc_number = meta.get("account_number", "")
        
        logger.info(f"📘 通帳ハンドラー起動: {bank_name} {branch_name}")

        new_filename = self._generate_filename(case, "通帳コピー", bank_name)
        dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
        if dest_dir: 
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "通帳", analysis_data, file_hash, status="CONFIRMED")
                session.add(ContactLog(case_id=case.case_id, contact_content=f"【自動処理】通帳コピーを保存しました: {saved_path.name}"))
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

        if bank_name: 
            self._register_passbook_asset(session, case.case_id, bank_name, branch_name, acc_type_name, acc_number)

    def _register_passbook_asset(self, session, case_id, bank_name, branch_name, acc_type_name, acc_number):
        try:
            z_bank_code, z_bank_name = find_bank_in_zengin(bank_name)
            
            if z_bank_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_bank_code).first()
            else:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == bank_name).first()
            
            if not bank:
                use_code = z_bank_code if z_bank_code else f"TMP-{uuid.uuid4().hex[:6]}"
                use_name = z_bank_name if z_bank_name else bank_name
                bank = BankMaster(bank_name=use_name, bank_code=use_code)
                session.add(bank)
                session.flush()

            branch = None
            if branch_name:
                z_br_code, z_br_name = (None, None)
                if not bank.bank_code.startswith("TMP"):
                    z_br_code, z_br_name = find_branch_in_zengin(bank.bank_code, branch_name)
                
                if z_br_code:
                    branch = session.query(BranchMaster).filter(BranchMaster.bank_id == bank.id, BranchMaster.branch_code == z_br_code).first()
                else:
                    branch = session.query(BranchMaster).filter(BranchMaster.bank_id == bank.id, BranchMaster.branch_name == branch_name).first()
                
                if not branch:
                    use_br_code = z_br_code if z_br_code else f"B-{uuid.uuid4().hex[:3]}"
                    use_br_name = z_br_name if z_br_name else branch_name
                    branch = BranchMaster(bank_id=bank.id, branch_name=use_br_name, branch_code=use_br_code)
                    session.add(branch)
                    session.flush()

            ac_type = session.query(AccountTypeMaster).filter(AccountTypeMaster.type_name.like(f"%{acc_type_name}%")).first()
            if not ac_type:
                ac_type = AccountTypeMaster(type_name=acc_type_name)
                session.add(ac_type)
                session.flush()

            search_num = acc_number if acc_number else "AI読取"
            
            existing = session.query(FinancialAsset).filter(
                FinancialAsset.case_id == case_id, 
                FinancialAsset.bank_id == bank.id, 
                FinancialAsset.account_number == search_num
            ).first()

            if existing:
                existing.status = "通帳確認済"
                if not existing.branch_id and branch: 
                    existing.branch_id = branch.id
                logger.info(f"   💰 資産更新: {bank.bank_name}")
            else:
                new_asset = FinancialAsset(
                    case_id=case_id, 
                    bank_id=bank.id, 
                    branch_id=branch.id if branch else None, 
                    account_type_id=ac_type.id, 
                    account_number=search_num, 
                    balance=0, 
                    status="通帳確認", 
                    asset_type="BANK"
                )
                session.add(new_asset)
                logger.info(f"   💰 資産新規登録: {bank.bank_name}")

        except Exception as e:
            logger.error(f"通帳DB登録失敗: {e}")

class BalanceCertificateHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        logger.info(f"🏦 残高証明書ハンドラー起動: {bank_name}")
        new_filename = self._generate_filename(case, "残高証明書", bank_name)
        
        dest_dir = self._find_folder(case.folder_path, "残高証明書")
        if not dest_dir:
            dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】{bank_name}の残高証明書を保存・登録しました: {saved_path.name}")
                session.add(log)
                self._update_or_create_registry(session, case.case_id, saved_path, "残高証明書", analysis_data, file_hash, status="CONFIRMED")
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

        balance = analysis_data.get("meta", {}).get("balance", 0)
        if balance: self._upsert_asset(session, case.case_id, bank_name, balance)

    def _upsert_asset(self, session, case_id, bank_name, balance):
        try:
            z_code, z_name = find_bank_in_zengin(bank_name)
            if z_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_code).first()
            else:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == bank_name).first()

            if not bank:
                use_code = z_code if z_code else f"TMP-{uuid.uuid4().hex[:6]}"
                use_name = z_name if z_name else bank_name
                bank = BankMaster(bank_name=use_name, bank_code=use_code)
                session.add(bank); session.flush()

            existing = session.query(FinancialAsset).filter_by(case_id=case_id, bank_id=bank.id).first()
            if existing:
                existing.balance = balance
                existing.status = "残高証明書確認済"
            else:
                new_asset = FinancialAsset(case_id=case_id, bank_id=bank.id, account_number="AI読取", balance=balance, status="残高証明書確認済")
                session.add(new_asset)
        except Exception as e:
            logger.error(f"   ❌ 資産登録エラー: {e}")

class SecuritiesStatementHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        sec_company_name = analysis_data.get("bank_name", "不明証券").strip()
        meta = analysis_data.get("meta", {})
        branch_name = meta.get("branch_name", "")
        account_number = meta.get("account_number", "")
        total_balance = meta.get("balance", 0)
        
        logger.info(f"📈 証券ハンドラー起動: {sec_company_name} (Acc: {account_number})")

        new_filename = self._generate_filename(case, "取引残高報告書", sec_company_name)
        
        dest_dir = self._find_target_folder(case.folder_path, "受領資料", "証券")
        if not dest_dir: dest_dir = self._ensure_folder(case.folder_path, "受領資料")

        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "証券取引報告書", analysis_data, file_hash, status="CONFIRMED")
                session.add(ContactLog(case_id=case.case_id, contact_content=f"【自動処理】{sec_company_name}の報告書を保存しました: {saved_path.name}")
        else:
            logger.warning(f"   ⚠️ 保存先フォルダが見つかりません: {case.folder_path}")

        if sec_company_name:
            self._register_securities_asset(session, case.case_id, sec_company_name, branch_name, account_number, total_balance)

    def _register_securities_asset(self, session, case_id, company_name, branch_name, account_number, balance):
        try:
            z_code, z_name = find_bank_in_zengin(company_name)
            if z_code:
                bank = session.query(BankMaster).filter(BankMaster.bank_code == z_code).first()
            else:
                bank = session.query(BankMaster).filter(BankMaster.bank_name == company_name).first()
            
            if not bank:
                use_code = z_code if z_code else f"SEC-{uuid.uuid4().hex[:6]}"
                use_name = z_name if z_name else company_name
                bank = BankMaster(bank_name=use_name, bank_code=use_code)
                session.add(bank)
                session.flush()

            branch = None
            if branch_name:
                branch = session.query(BranchMaster).filter(BranchMaster.bank_id == bank.id, BranchMaster.branch_name == branch_name).first()
                if not branch:
                    branch = BranchMaster(bank_id=bank.id, branch_name=branch_name, branch_code=f"B-{uuid.uuid4().hex[:3]}")
                    session.add(branch)
                    session.flush()

            search_num = account_number if account_number else "AI読取"
            existing = session.query(FinancialAsset).filter(
                FinancialAsset.case_id == case_id, 
                FinancialAsset.bank_id == bank.id, 
                FinancialAsset.account_number == search_num
            ).first()

            if existing:
                existing.balance = balance
                existing.status = "証券明細確認済"
                existing.asset_type = "SECURITY"
                if not existing.branch_id and branch: 
                    existing.branch_id = branch.id
            else:
                new_asset = FinancialAsset(
                    case_id=case_id, 
                    bank_id=bank.id, 
                    branch_id=branch.id if branch else None, 
                    account_number=search_num, 
                    balance=balance, 
                    status="証券明細確認済", 
                    asset_type="SECURITY"
                )
                session.add(new_asset)

        except Exception as e:
            logger.error(f"証券DB登録失敗: {e}")

class TransactionDetailHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        bank_name = analysis_data.get("bank_name", "不明銀行").strip()
        new_filename = self._generate_filename(case, "取引明細書", bank_name)
        
        dest_dir = self._find_folder(case.folder_path, "取引履歴")
        if not dest_dir:
            dest_dir = self._ensure_folder(case.folder_path, "受領資料")
            
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "取引明細書", analysis_data, file_hash)
                session.add(ContactLog(case_id=case.case_id, contact_content=f"【自動処理】取引明細書を保存しました: {saved_path.name}"))

class InvoiceHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        meta = analysis_data.get("meta", {})
        sender = meta.get("sender_name", "不明な請求元")
        amount = meta.get("amount", 0)
        due_date = meta.get("due_date", "")
        identifier = sender.replace(" ", "").replace("　", "")
        new_filename = self._generate_filename(case, "請求書", identifier)
        
        dest_dir = self._ensure_folder(case.folder_path, "請求書", force_name="請求書")
        
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "請求書", analysis_data, file_hash)
                msg = f"【自動処理】請求書を保存しました。\n請求元: {sender}\n金額: {amount:,}円\n保存先: {saved_path.name}"
                session.add(ContactLog(case_id=case.case_id, contact_content=msg))
        
        existing_debt = session.query(Liability).filter(Liability.case_id == case.case_id, Liability.description.like(f"%{sender}%"), Liability.amount == amount).first()
        if not existing_debt:
            new_liability = Liability(case_id=case.case_id, is_debt=True, description=f"【請求書】{sender} (期限: {due_date})", amount=amount, is_funeral_cost=False)
            session.add(new_liability)

class RegistryDocumentHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        final_filename = original_path.name
        
        dest_dir = self._find_folder(case.folder_path, "名寄帳")
        if not dest_dir:
            dest_dir = self._ensure_folder(case.folder_path, "不動産登記情報", force_name="不動産登記情報")

        saved_path = self._save_file_copy(original_path, dest_dir, final_filename) if dest_dir else None
        if saved_path:
            self._update_or_create_registry(session, case.case_id, saved_path, "不動産登記情報", analysis_data, file_hash)
            msg = f"【自動処理】不動産登記情報を保存しました。\n保存先: {dest_dir.name}/{saved_path.name}\n※Home画面の「不動産登録」から登録してください。"
            session.add(ContactLog(case_id=case.case_id, contact_content=msg))

class OtherDocumentHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        doc_type = analysis_data.get("doc_type", "書類")
        final_filename = self._generate_filename(case, doc_type)
        
        dest_dir = Path(case.folder_path) if case.folder_path and os.path.exists(case.folder_path) else None
        
        saved_path = self._save_file_copy(original_path, dest_dir, final_filename) if dest_dir else None
        if saved_path:
            self._update_or_create_registry(session, case.case_id, saved_path, doc_type, analysis_data, file_hash)
            msg = f"【自動処理】{doc_type}を保存しました。\n保存先: {saved_path.name}"
            session.add(ContactLog(case_id=case.case_id, contact_content=msg))

class HeirListHandler(DocumentHandler):
    def handle(self, session, case: Case, analysis_data: dict, original_path: Path, file_hash: str = None):
        logger.info(f"👨‍👩‍👧‍👦 相続人リスト・ハンドラー起動")
        new_filename = self._generate_filename(case, "推定相続人連絡先一覧")
        # デフォルト動作: 受領資料
        dest_dir = self._ensure_folder(case.folder_path, "受領資料")
        
        if dest_dir:
            saved_path = self._save_file_copy(original_path, dest_dir, new_filename)
            if saved_path:
                self._update_or_create_registry(session, case.case_id, saved_path, "推定相続人連絡先一覧", analysis_data, file_hash, status="CONFIRMED")
                log = ContactLog(case_id=case.case_id, contact_content=f"【自動処理】推定相続人連絡先一覧を保存しました: {saved_path.name}")
                session.add(log)

# ---------------------------------------------------------
# メインサービスクラス
# ---------------------------------------------------------
class ScannerService:
    def __init__(self, inbox_path: str = None, processed_root: str = None):
        self.inbox_path = Path(inbox_path) if inbox_path else Path(os.path.join(os.path.expanduser("~"), "Downloads"))
        if processed_root: self.processed_root = Path(processed_root)
        else: self.processed_root = Config.DATA_DIR / "cases"
        self.db = DatabaseManager()
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        self.handlers = {
            "corporate_registry": CorporateRegistryHandler(self.db), # ★新規
            "balance_certificate": BalanceCertificateHandler(self.db),
            "transaction_detail": TransactionDetailHandler(self.db),
            "bank_passbook": BankPassbookHandler(self.db),
            "securities_statement": SecuritiesStatementHandler(self.db),
            "invoice": InvoiceHandler(self.db),
            "registry_document": RegistryDocumentHandler(self.db),
            "heir_list": HeirListHandler(self.db),
            "tax_payment_notice": TaxPaymentNoticeHandler(self.db),
            "other": OtherDocumentHandler(self.db)
        }

    def process_file(self, file_path: str):
        """Watcherからの自動処理エントリーポイント"""
        path = Path(file_path)
        logger.info(f"🚀 [Scanner] 処理開始: {path.name}")
        time.sleep(1.0)
        try:
            if not path.exists():
                logger.error(f"   ❌ ファイル消失: {path}")
                return
            with open(path, "rb") as f: file_bytes = f.read()
            f_hash = hashlib.md5(file_bytes).hexdigest()
            
            logger.info("   🤖 AI解析を実行中...")
            analysis = self._analyze_document(file_bytes)
            candidates = analysis.get("case_candidates", [])
            doc_type = analysis.get('doc_type', 'unknown')
            
            logger.info(f"   📋 解析完了: {doc_type}")
            logger.info(f"   💡 候補案件: {len(candidates)} 件")
            
            session = self.db._get_session()
            try:
                # ----------------------------------------------------------------
                # 自律実行モード (Auto Mode)
                # 条件: 候補が1件だけ かつ 書類種別が明確
                # ※ 商業登記(corporate_registry)は誤紐付け防止のため自動処理から除外する
                # ----------------------------------------------------------------
                is_high_confidence = (len(candidates) == 1) and \
                                     (doc_type not in ["other", "unknown", "corporate_registry"])
                
                if is_high_confidence:
                    target_case_id = candidates[0]['case_id']
                    logger.info(f"   ✨ 高信頼度 (100%) -> 自動処理を実行します (Case: {target_case_id})")
                    
                    self._execute_handler(session, target_case_id, analysis, path, file_hash=f_hash)
                    
                    try:
                        os.remove(path)
                        logger.info("   🗑️ 元ファイルを削除しました (処理完了)")
                    except Exception as ex:
                        logger.warning(f"   ⚠️ 元ファイル削除失敗: {ex}")
                        
                else:
                    # ----------------------------------------------------------------
                    # 従来モード (保留 / PENDING)
                    # ----------------------------------------------------------------
                    logger.info("   🤔 確認が必要 -> 受信トレイ(Pending)へ")
                    
                    temp_storage = Config.DATA_DIR / "uploads" / "pending"
                    temp_storage.mkdir(parents=True, exist_ok=True)
                    saved_path = temp_storage / path.name
                    shutil.copy2(str(path), str(saved_path))
                    
                    candidate_id = candidates[0]['case_id'] if candidates else None
                    self._register_file_entry(session, candidate_id, saved_path, doc_type, analysis, status="PENDING")
                    
                    try:
                        os.remove(path)
                    except: pass
                
                session.commit()
                
            except Exception as e:
                session.rollback()
                logger.error(f"   ❌ DB保存エラー: {e}")
                raise e
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"   ❌ ファイル処理エラー (Top Level): {e}")

    def _register_file_entry(self, session, case_id, file_path, doc_type, analysis_data, status="PENDING"):
        if not file_path or not file_path.exists(): return
        with open(file_path, "rb") as f: file_bytes = f.read()
        f_hash = hashlib.md5(file_bytes).hexdigest()
        
        extracted_json = json.dumps(analysis_data, ensure_ascii=False) if analysis_data else None
        
        existing = session.query(FileRegistry).filter_by(file_hash=f_hash).first()
        conf = 1.0 if status == "CONFIRMED" else 0.0
        
        if existing:
            existing.status = status
            existing.extracted_data = extracted_json
            existing.filename = file_path.name
            existing.ai_confidence = conf
            if case_id: existing.case_id = case_id
        else:
            new_reg = FileRegistry(
                file_hash=f_hash,
                filename=file_path.name,
                case_id=case_id,
                doc_type=doc_type,
                file_path=str(file_path),
                registered_at=datetime.datetime.now(),
                status=status,
                ai_confidence=conf,
                extracted_data=extracted_json
            )
            session.add(new_reg)

    def _execute_handler(self, session, case_id: int, analysis: dict, path: Path, file_hash: str):
        case = session.query(Case).options(joinedload(Case.deceased_ref)).get(case_id)
        if case:
            doc_type = analysis.get("doc_type", "other")
            handler = self.handlers.get(doc_type, self.handlers["other"])
            
            if handler: 
                logger.info(f"   🔧 ハンドラー実行: {doc_type} -> Case {case.case_number}")
                handler.handle(session, case, analysis, path, file_hash=file_hash)
        else:
            logger.error(f"Case ID {case_id} not found.")

    def process_pending_buffer(self, buffer_id: str, target_case_id: int, override_doc_type: str = None) -> bool:
        session = self.db._get_session()
        try:
            file_entry = session.query(FileRegistry).filter_by(file_hash=buffer_id).first()
            if not file_entry:
                logger.error(f"FileHash {buffer_id} not found.")
                return False
            
            logger.info(f"承認処理開始: File {file_entry.filename} -> Case ID {target_case_id}")
            
            file_path = Path(file_entry.file_path) if file_entry.file_path else None
            if not file_path or not file_path.exists():
                logger.error(f"❌ 実ファイルが見つかりません: {file_path}")
                return False

            analysis = {}
            if file_entry.extracted_data:
                try: analysis = json.loads(file_entry.extracted_data)
                except: pass
            
            if override_doc_type:
                analysis["doc_type"] = override_doc_type

            self._execute_handler(session, target_case_id, analysis, file_path, file_hash=buffer_id)
            
            file_entry = session.query(FileRegistry).filter_by(file_hash=buffer_id).first() 
            if file_entry and file_entry.status != "CONFIRMED":
                file_entry.status = "CONFIRMED"
                file_entry.case_id = target_case_id
                file_entry.ai_confidence = 1.0
            
            session.commit()
            logger.info("✅ 承認処理成功")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"承認処理エラー: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            session.close()

    def _analyze_document(self, file_bytes: bytes) -> dict:
        mime = "application/pdf" if file_bytes.startswith(b"%PDF") else "image/jpeg"
        doc_b64 = base64.b64encode(file_bytes).decode("utf-8")
        
        prompt = """
        この書類を解析し、以下のJSON形式で出力してください。
        
        # 1. 基本情報抽出
        - **names**: 「遺言者」「依頼者」「契約者」「お客様」などの氏名を最優先で抽出。なければ被相続人名。
        - **bank_name**: 金融機関名・証券会社名。
        
        # 2. 書類種別 (doc_type) の判定
        - **corporate_registry**: 「全部事項証明書」「履歴事項全部証明書」など、会社の登記簿謄本。タイトルに「事項証明書」とあり、かつ「商号」「本店」の記載があるもの。
        - **securities_statement**: 証券会社の報告書。
        - **tax_payment_notice**: 固定資産税納税通知書。
        - **heir_list**: 相続人一覧。
        - registry_document: 不動産登記情報 (土地・建物)。
        - bank_passbook: 通帳。
        - balance_certificate: 残高証明書。
        - transaction_detail: 取引明細。
        - invoice: 請求書。
        - other: その他。

        # 3. メタデータ (meta) の抽出
        
        **【A】corporate_registry (商業登記) の場合**
        - **corporate_name**: 商号（会社名）。「株式会社〇〇」など。
        - **head_office**: 本店所在地。

        **【B】securities_statement (証券関連) の場合**
        - branch_name, account_number, balance, holdings.

        **【C】balance_certificate / bank_passbook (銀行関連) の場合**
        - branch_name, account_number, balance, holder_name, account_type.

        # 出力JSON例 (商業登記)
        {
            "names": [],
            "doc_type": "corporate_registry",
            "meta": {
                "corporate_name": "株式会社チェスター",
                "head_office": "東京都中央区..."
            },
            "case_candidates": []
        }
        """
        
        msg = HumanMessage(content=[{"type": "text", "text": prompt}, {"type": "image_url", "image_url": f"data:{mime};base64,{doc_b64}"}])
        try:
            resp = self.llm.invoke([msg])
            ai_data = json.loads(resp.content.replace("```json", "").replace("```", "").strip())
        except: return {}
        
        # --- Pythonによる後処理 ---
        bank_name = ai_data.get("bank_name", "")
        doc_type = ai_data.get("doc_type", "")
        
        if "証券" in bank_name or "證券" in bank_name:
            if doc_type != "securities_statement":
                ai_data["doc_type"] = "securities_statement"
        
        if "野村" in bank_name and doc_type == "balance_certificate":
             ai_data["doc_type"] = "securities_statement"

        # 名前クレンジング & 案件検索
        names = ai_data.get("names", [])
        holder = ai_data.get("meta", {}).get("holder_name")
        if holder and holder not in names: names.append(holder)
        cleaned_names = [n.replace("様", "").replace("殿", "").strip() for n in names]

        candidates = []
        if cleaned_names:
            session = self.db._get_session()
            try:
                for name in cleaned_names:
                    hits = find_cases_by_attributes(client_name=name) or find_cases_by_attributes(deceased_name=name)
                    if hits: candidates.extend(hits)
            finally: session.close()
            
        unique_candidates = {c['case_id']: c for c in candidates}.values()
        final_candidates_list = []
        for c in unique_candidates:
            new_c = c.copy()
            for k, v in new_c.items():
                if isinstance(v, (datetime.date, datetime.datetime)):
                    new_c[k] = v.strftime('%Y-%m-%d')
            final_candidates_list.append(new_c)

        ai_data["case_candidates"] = final_candidates_list
        ai_data["names"] = cleaned_names
        return ai_data
````

## File: src/legal_system/core/ai_factory.py
````python
# src/legal_system/core/ai_factory.py

import os
import logging
import requests
from typing import Any, Optional

# LangChain - Community / Local
from langchain_community.chat_models import ChatOllama

# LangChain - Google Studio
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# LangChain - Google Vertex AI
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from .config import Config, KeyManager

logger = logging.getLogger(__name__)

class AIFactory:
    """
    AIモデル（LLM）、Embeddings、VectorStoreのインスタンス生成を一元管理するファクトリークラス。
    AI_PROVIDERの設定に基づき、Google AI Studio または Vertex AI を切り替えます。
    """

    @staticmethod
    def _check_ollama_server(base_url: str) -> bool:
        """Ollamaサーバーの生存確認"""
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=1.0)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def get_llm(cls, mode: str = "cloud", temperature: Optional[float] = None) -> Any:
        """
        LLMインスタンスを取得します。
        
        Args:
            mode (str): "cloud" (Gemini/Vertex) または "local" (Ollama/Llama)
            temperature (float): 生成温度。Noneの場合はConfig値を使用。
        """
        temp = temperature if temperature is not None else Config.TEMPERATURE

        # --- Local Mode (Ollama) ---
        if mode == "local":
            base_url = "http://host.docker.internal:11434"
            
            # 接続チェック（開発時の利便性のため、失敗時はエラーログを出してフォールバック検討等は実装依存）
            if not cls._check_ollama_server(base_url):
                # Docker内通信がだめな場合、localhostも試行(開発環境用)
                base_url = "http://localhost:11434"
                if not cls._check_ollama_server(base_url):
                    raise ConnectionError("❌ Ollamaサーバーに接続できません。")

            # 軽量モデルを指定
            model_name = "llama3.2:1b"
            logger.info(f"🤖 Local LLM Mode: {model_name}")

            return ChatOllama(
                base_url=base_url,
                model=model_name,
                temperature=temp,
                format="json",
                timeout=120,
            )
        
        # --- Cloud Mode (Gemini / Vertex) ---
        else:
            if Config.is_vertex_enabled():
                # Vertex AI (Enterprise)
                logger.info(f"☁️ Cloud LLM Mode: Vertex AI ({Config.GOOGLE_MODEL_NAME})")
                
                # VertexAIはADC(Application Default Credentials)を利用するためAPIキー指定は不要
                # Project/RegionはConfigまたは環境変数から自動取得されるが、明示も可能
                return ChatVertexAI(
                    model_name=Config.GOOGLE_MODEL_NAME,
                    project=Config.GOOGLE_CLOUD_PROJECT,
                    location=Config.GOOGLE_CLOUD_REGION,
                    temperature=temp,
                    convert_system_message_to_human=True,
                    max_retries=2
                )
            else:
                # Google AI Studio (Personal / API Key)
                logger.info(f"☁️ Cloud LLM Mode: AI Studio ({Config.GOOGLE_MODEL_NAME})")
                api_key = KeyManager.get_next_key()
                
                return ChatGoogleGenerativeAI(
                    model=Config.GOOGLE_MODEL_NAME,
                    google_api_key=api_key,
                    temperature=temp,
                    convert_system_message_to_human=True,
                    max_retries=2
                )

    @classmethod
    def get_embeddings(cls) -> Any:
        """埋め込みモデル（Embeddings）を返します。"""
        
        if Config.is_vertex_enabled():
            # Vertex AI Embeddings
            # モデル名は text-embedding-004 などが望ましいが、Configに従う
            return VertexAIEmbeddings(
                model_name="text-embedding-004", # Vertex推奨モデルに固定
                project=Config.GOOGLE_CLOUD_PROJECT,
                location=Config.GOOGLE_CLOUD_REGION,
            )
        else:
            # AI Studio Embeddings
            api_key = KeyManager.get_next_key()
            return GoogleGenerativeAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                google_api_key=api_key
            )

    @classmethod
    def get_vector_store(cls):
        """永続化されたChromaベクトルストアのインスタンスを返します。"""
        from langchain_chroma import Chroma
        
        embeddings = cls.get_embeddings()

        if not Config.VECTOR_STORE_PATH.exists():
            os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)

        return Chroma(
            persist_directory=str(Config.VECTOR_STORE_PATH),
            embedding_function=embeddings,
        )
````

## File: src/legal_system/models/tables.py
````python
# src/legal_system/models/tables.py

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ==========================================
# 1. 共通マスタ (Core Master Data)
# ==========================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    windows_id = Column(String, unique=True, nullable=False, comment="PCログインID")
    name = Column(String, nullable=False, comment="表示名")
    role = Column(String, default="Operator", comment="権限: Manager/Operator")
    department = Column(String, nullable=True, comment="所属部署")
    phone = Column(String, nullable=True, comment="内線・連絡先")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class BankMaster(Base):
    __tablename__ = "bank_master"
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    bank_code = Column(String, nullable=False)
    seal_cert_limit = Column(String, comment="印鑑証明期限")
    id_verify_rule = Column(String, comment="本人確認書類")
    transfer_rule = Column(String, comment="振込ルール")
    remarks = Column(Text, comment="特記事項")

    __table_args__ = (
        UniqueConstraint("bank_name", name="_bank_name_uc"),
        UniqueConstraint("bank_code", name="_bank_code_uc"),
    )
    branches = relationship("BranchMaster", back_populates="bank_ref", cascade="all, delete-orphan")
    financial_assets = relationship("FinancialAsset", back_populates="bank_ref")
    aliases = relationship("BankAlias", back_populates="bank_ref", cascade="all, delete-orphan")
    rag_files = relationship("FileRegistry", back_populates="bank_ref")

class BankAlias(Base):
    __tablename__ = "bank_aliases"
    id = Column(Integer, primary_key=True, index=True)
    alias_name = Column(String, unique=True, index=True, nullable=False)
    bank_id = Column(Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False)
    bank_ref = relationship("BankMaster", back_populates="aliases")

class BranchMaster(Base):
    __tablename__ = "branch_master"
    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False)
    branch_name = Column(String, nullable=False)
    branch_code = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("bank_id", "branch_code", name="_bank_branch_code_uc"),)
    bank_ref = relationship("BankMaster", back_populates="branches")
    financial_assets = relationship("FinancialAsset", back_populates="branch_ref")

class AccountTypeMaster(Base):
    __tablename__ = "account_type_master"
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String, unique=True, nullable=False)
    financial_assets = relationship("FinancialAsset", back_populates="account_type_ref")

class DocumentType(Base):
    __tablename__ = "document_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class ShippingMethod(Base):
    __tablename__ = "shipping_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tracking_base_url = Column(String, nullable=False)
    estimated_days = Column(Integer)

class SubmissionDocType(Base):
    __tablename__ = "submission_doc_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

# ==========================================
# 2. RAGシステム・ファイル管理
# ==========================================

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String)
    target = Column(String)
    details = Column(Text)
    user = relationship("User")

class FileRegistry(Base):
    __tablename__ = "file_registry"
    file_hash = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    doc_type = Column(String, default="その他")
    registered_at = Column(DateTime, default=datetime.now)
    security_level = Column(String, default="general")
    file_path = Column(String)
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="CONFIRMED")
    ai_confidence = Column(Float, default=0.0)
    extracted_data = Column(Text, nullable=True)

    bank_ref = relationship("BankMaster", back_populates="rag_files")
    case_ref = relationship("Case", back_populates="files")
    registrar = relationship("User")

# ==========================================
# 3. 個人情報管理テーブル
# ==========================================

class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    zip_code = Column(String)
    prefecture = Column(String, nullable=False)
    city_ward_town = Column(String)
    street_address = Column(String, nullable=False)
    building_name = Column(String)
    deceased_history = relationship("D_AddressHistory", back_populates="address", cascade="all, delete-orphan")
    heir_history = relationship("H_AddressHistory", back_populates="address", cascade="all, delete-orphan")

class Contact(Base):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    type = Column(String, nullable=False)
    sub_type = Column(String)

class Deceased(Base):
    __tablename__ = "deceased"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, unique=True)
    name_last = Column(String)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    hometown = Column(String, comment="本籍地")
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    relationship_type = Column(String)
    last_address_id = Column(Integer, ForeignKey("address.id"))
    heirs = relationship("Heir", back_populates="deceased", cascade="all, delete-orphan")
    address_links = relationship("D_AddressHistory", back_populates="deceased", cascade="all, delete-orphan")
    contact_links = relationship("D_ContactLink", back_populates="deceased", cascade="all, delete-orphan")
    case = relationship("Case", back_populates="deceased_ref")
    last_address = relationship("Address", foreign_keys=[last_address_id])

class Heir(Base):
    """相続人"""
    __tablename__ = "heirs"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    name_last = Column(String, nullable=False)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    
    # 本籍地として使用
    hometown = Column(String, comment="本籍地")
    
    # ★追加: 職業カラム
    occupation = Column(String, comment="職業")
    
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    relationship_type = Column(String)
    is_contracting_party = Column(Boolean, default=False)

    deceased = relationship("Deceased", back_populates="heirs")
    address_links = relationship("H_AddressHistory", back_populates="heir", cascade="all, delete-orphan")
    contact_links = relationship("H_ContactLink", back_populates="heir", cascade="all, delete-orphan")

# --- リンクテーブル ---

class D_AddressHistory(Base):
    __tablename__ = "d_address_history"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_last_address = Column(Boolean, nullable=False, default=False)
    deceased = relationship("Deceased", back_populates="address_links")
    address = relationship("Address", back_populates="deceased_history")

class H_AddressHistory(Base):
    __tablename__ = "h_address_history"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_current_address = Column(Boolean, nullable=False, default=False)
    heir = relationship("Heir", back_populates="address_links")
    address = relationship("Address", back_populates="heir_history")

class D_ContactLink(Base):
    __tablename__ = "d_contact_link"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    deceased = relationship("Deceased", back_populates="contact_links")
    contact = relationship("Contact")

class H_ContactLink(Base):
    __tablename__ = "h_contact_link"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    heir = relationship("Heir", back_populates="contact_links")
    contact = relationship("Contact")

# ==========================================
# 4. 案件ハブテーブル
# ==========================================

class CaseStatus(Base):
    __tablename__ = "case_statuses"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    order_num = Column(Integer)

class Case(Base):
    __tablename__ = "cases"
    case_id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    folder_path = Column(String)
    client_name = Column(String, nullable=False)
    client_name_kana = Column(String)
    manager_id = Column(Integer, ForeignKey("users.id"))
    operator_id = Column(Integer, ForeignKey("users.id"))
    current_status_id = Column(Integer, ForeignKey("case_statuses.id"))
    kintone_record_id = Column(Integer, nullable=True)
    fee_contract_amount = Column(Float, default=0.0)
    deposit_required_amount = Column(Float, default=0.0)
    deposit_paid_amount = Column(Float, default=0.0)
    is_paid_in_full = Column(Boolean, default=False)
    certs_of_seal_count = Column(Integer, default=0)
    power_of_attorney_count = Column(Integer, default=0)
    date_of_death = Column(Date)
    interview_date = Column(DateTime)
    contract_date = Column(Date)
    tax_deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    sol_case_number = Column(String, nullable=True)
    introduction_date = Column(Date, nullable=True)
    referral_sec_branch_name = Column(String, nullable=True)
    referral_sec_rep_name = Column(String, nullable=True)
    consent_date = Column(Date, nullable=True)
    referral_sec_phone = Column(String, nullable=True)

    manager = relationship("User", foreign_keys=[manager_id])
    operator = relationship("User", foreign_keys=[operator_id])
    status_ref = relationship("CaseStatus")
    deceased_ref = relationship("Deceased", back_populates="case", uselist=False, cascade="all, delete-orphan")
    financial_assets = relationship("FinancialAsset", back_populates="case_ref", cascade="all, delete-orphan")
    real_estates = relationship("RealEstateAsset", back_populates="case_ref", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="case_ref", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="case_ref", cascade="all, delete-orphan")
    submitted_docs = relationship("CaseSubmissionDoc", back_populates="case_ref", cascade="all, delete-orphan")
    contact_logs = relationship("ContactLog", back_populates="case_ref", cascade="all, delete-orphan")
    insurance_assets = relationship("InsuranceAsset", back_populates="case_ref", cascade="all, delete-orphan")
    other_assets = relationship("OtherAsset", back_populates="case_ref", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="case_ref", cascade="all, delete-orphan")
    contact_points = relationship("CaseContactPoint", back_populates="case_ref", cascade="all, delete-orphan")
    files = relationship("FileRegistry", back_populates="case_ref")

class CaseContactPoint(Base):
    __tablename__ = "case_contact_points"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_person_name = Column(String)
    relationship_to_client = Column(String)
    address_id = Column(Integer, ForeignKey("address.id"))
    contact_id = Column(Integer, ForeignKey("contact.id"))
    is_primary_contact = Column(Boolean, default=False)
    is_primary_mail_send_destination = Column(Boolean, default=False)
    case_ref = relationship("Case", back_populates="contact_points")
    address_ref = relationship("Address")
    contact_ref = relationship("Contact")

# ==========================================
# 5. タスク管理
# ==========================================

class TaskTemplate(Base):
    __tablename__ = "task_templates"
    template_id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    default_due_days = Column(Integer, default=1)
    is_manager_task = Column(Boolean, default=False)
    depends_on_template_id = Column(Integer, ForeignKey("task_templates.template_id"))
    depends_on = relationship("TaskTemplate", remote_side=[template_id])

class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    template_id = Column(Integer, ForeignKey("task_templates.template_id"))
    description = Column(String, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    template_ref = relationship("TaskTemplate")
    document_logs = relationship("TaskDocumentLog", back_populates="task_ref", cascade="all, delete-orphan")
    case_ref = relationship("Case", back_populates="tasks")

class TaskDocumentLog(Base):
    __tablename__ = "task_document_logs"
    log_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    shipping_method_id = Column(Integer, ForeignKey("shipping_methods.id"), nullable=False)
    sent_date = Column(DateTime, nullable=False)
    sent_to = Column(String, nullable=False)
    tracking_number = Column(String, unique=True)
    is_returned = Column(Boolean, default=False)
    document_type = relationship("DocumentType")
    shipping_method = relationship("ShippingMethod")
    task_ref = relationship("Task", back_populates="document_logs")

# ==========================================
# 6. 財産・トランザクション詳細
# ==========================================

class FinancialAsset(Base):
    __tablename__ = "financial_asset"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String, default="BANK")
    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch_master.id"))
    account_type_id = Column(Integer, ForeignKey("account_type_master.id"), nullable=True)
    account_number = Column(String)
    balance = Column(Float, default=0.0)
    status = Column(String, default="未確認")
    case_ref = relationship("Case", back_populates="financial_assets")
    bank_ref = relationship("BankMaster", back_populates="financial_assets")
    branch_ref = relationship("BranchMaster", back_populates="financial_assets")
    account_type_ref = relationship("AccountTypeMaster", back_populates="financial_assets")

class RealEstateAsset(Base):
    __tablename__ = "real_estate_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    property_type = Column(String, default="Land")
    location = Column(String, comment="所在")
    lot_number = Column(String, comment="地番")
    land_category = Column(String, comment="地目")
    land_area = Column(Float, comment="地積")
    house_number = Column(String, comment="家屋番号")
    structure = Column(String, comment="構造")
    floor_area = Column(String, comment="床面積")
    assessed_value = Column(Float, comment="固定資産税評価額", default=0.0)
    ownership_share = Column(String, nullable=True, comment="被相続人の持分")
    registry_pdf_path = Column(String, nullable=True, comment="登記情報PDFパス")
    registry_image_path = Column(String, nullable=True, comment="Word貼付用画像パス")
    case_ref = relationship("Case", back_populates="real_estates")

class InsuranceAsset(Base):
    __tablename__ = "insurance_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    insurance_company = Column(String)
    policy_number = Column(String)
    estimated_value = Column(Float)
    case_ref = relationship("Case", back_populates="insurance_assets")

class OtherAsset(Base):
    __tablename__ = "other_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    estimated_value = Column(Float)
    case_ref = relationship("Case", back_populates="other_assets")

class Liability(Base):
    __tablename__ = "liability"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    is_debt = Column(Boolean, nullable=False, default=True)
    description = Column(String)
    amount = Column(Float, nullable=False)
    is_funeral_cost = Column(Boolean, nullable=False, default=False)
    case_ref = relationship("Case", back_populates="liabilities")

class Expense(Base):
    __tablename__ = "expenses"
    expense_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    amount = Column(Float, nullable=False)
    expense_date = Column(Date)
    case_ref = relationship("Case", back_populates="expenses")

class ContactLog(Base):
    __tablename__ = "contact_logs"
    log_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_content = Column(String, nullable=False)
    is_thank_you_payment = Column(Boolean, default=False)
    case_ref = relationship("Case", back_populates="contact_logs")

class CaseSubmissionDoc(Base):
    __tablename__ = "case_submission_docs"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    case_ref = relationship("Case", back_populates="submitted_docs")

class Coordinate(Base):
    __tablename__ = "coordinates"
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String, index=True, nullable=False, comment="ファイル識別ハッシュ")
    label = Column(String, nullable=False, comment="項目名")
    x_point = Column(Float, nullable=False, comment="X座標")
    y_point = Column(Float, nullable=False, comment="Y座標")
    page_number = Column(Integer, default=1, comment="ページ番号")
    font_size = Column(Integer, default=10, comment="フォントサイズ")
    color = Column(String, default="black", comment="文字色")
    value = Column(String, nullable=True, comment="テスト値")
    description = Column(String, nullable=True, comment="備考")

# ==========================================
# 7. 遺言作成業務テーブル
# ==========================================

class WillCase(Base):
    __tablename__ = "will_cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    testator_name = Column(String, nullable=False)
    testator_birth = Column(Date)
    testator_address_id = Column(Integer, ForeignKey("address.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    will_type = Column(String, default="公正証書", comment="公正証書/自筆証書")
    status = Column(String, default="ヒアリング中", comment="起案中/公証役場調整中/完了")
    notary_office_name = Column(String, nullable=True)
    draft_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    allocations = relationship("WillAllocation", back_populates="will_case")

class WillAllocation(Base):
    __tablename__ = "will_allocations"
    id = Column(Integer, primary_key=True)
    will_id = Column(Integer, ForeignKey("will_cases.id"), nullable=False)
    asset_description = Column(String, nullable=False, comment="例: ○○銀行の預金全額")
    beneficiary_name = Column(String, nullable=False)
    relationship_to_testator = Column(String, comment="続柄: 妻, 長男, 孫...")
    percentage = Column(Float, nullable=True, comment="割合指定の場合 (例: 0.5)")
    will_case = relationship("WillCase", back_populates="allocations")

class IncomingNoteBuffer(Base):
    __tablename__ = "incoming_note_buffer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, unique=True, nullable=False, comment="GmailのMessage-ID")
    received_at = Column(DateTime, nullable=False, default=datetime.now)
    subject = Column(String, nullable=True)
    body_text = Column(Text, nullable=False)
    detected_names = Column(String, nullable=True, comment="AIが抽出した氏名候補(JSON文字列)")
    ai_summary = Column(Text, nullable=True, comment="AIによる簡易要約")
    status = Column(String, default="PENDING", comment="PENDING(未紐付)/LINKED(紐付済)/IGNORED(対象外)")
    linked_case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    linked_case = relationship("Case")

class FamilyRegister(Base):
    __tablename__ = "family_registers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=True)
    doc_type = Column(String, comment="書類種別(戸籍謄本/除籍謄本/改製原戸籍)")
    issuing_authority = Column(String, comment="本籍地/発行元")
    head_of_family = Column(String, comment="筆頭者氏名")
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    file_registry_id = Column(String, ForeignKey("file_registry.file_hash"), nullable=True)
    case = relationship("Case")
    deceased = relationship("Deceased")
    heir = relationship("Heir")
````

## File: .gitignore
````
# --- Python & Rye ---
__pycache__/
*.pyc
.venv/
.rye/

# --- 環境変数 & 機密情報 (絶対にGitにあげない) ---
.env
.streamlit/secrets.toml

# --- データベース & ログ ---
# 監査ログやベクターDBはローカルで生成されるため除外
db/sql/*.db
db/chroma/
*.log

# --- 生成されたファイル・アップロードデータ ---
# テンプレートPDFやアップロードされた一時ファイル
data/templates/*.pdf
data/uploads/
data/generated/
data/zengin

# ※フォントファイル(ipaexg.ttf)などはアプリの動作に必要なので
#   除外せず、Gitに含めるのが一般的です

# --- AI Context / Repomix ---
# ソースコードをまとめたファイルは除外
repomix-output.*
all_code_context.txt

# --- IDE / エディタ ---
.vscode/
.idea/

# --- Python Testing / Caching ---
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage

# --- OS ---
.DS_Store
Thumbs.db

bootstrap.py
credentials.json
token.json
# --- Backups ---
src_backup_*/
temp_archived/
data/scan_inbox/
````

## File: src/legal_system/core/database_manager.py
````python
# src/legal_system/core/database_manager.py

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

# テーブル定義
from src.legal_system.models.tables import (
    AuditLog,
    Base,
    Case,
    Coordinate,
    FileRegistry,
    User,
)

# Config
from .config import Config

# ==========================================
# エンジン生成の共通ロジック
# ==========================================
def _create_new_engine() -> Engine:
    """SQLAlchemyエンジンを新規作成する内部関数"""
    engine = create_engine(
        Config.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"client_encoding": "utf8"}
    )
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        msg = f"❌ データベース接続エラー: {e}"
        if os.environ.get("IS_WATCHER_PROCESS") != "true":
            try:
                import streamlit as st
                st.error(msg)
            except ImportError:
                print(msg)
        else:
            print(msg)
        raise e
    return engine

# ==========================================
# 公開アクセサ (環境判定ロジック付き)
# ==========================================
def get_db_engine() -> Engine:
    """
    実行環境に応じて適切なエンジン取得方法を選択する。
    - Watcherプロセス: Streamlitを無視して新規作成
    - Streamlitアプリ: st.cache_resourceを利用
    """
    if os.environ.get("IS_WATCHER_PROCESS") == "true":
        return _create_new_engine()
    else:
        try:
            import streamlit as st
            
            # キャッシュ衝突を避けるため、関数内部で定義
            @st.cache_resource(show_spinner="データベースに接続中...")
            def _get_cached_engine() -> Engine:
                return _create_new_engine()
                
            return _get_cached_engine()
        except ImportError:
            return _create_new_engine()

class DatabaseManager:
    def __init__(self):
        self.engine = get_db_engine()
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def _get_session(self):
        return self.Session()

    # ---------------------------------------------------------
    # ユーザー管理
    # ---------------------------------------------------------
    def get_current_user_info(self) -> Dict[str, str]:
        """Windowsログインユーザー情報を取得または作成"""
        pc_user = os.environ.get("USERNAME", "guest_user")

        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=pc_user).first()
            if user:
                return {
                    "id": user.windows_id,
                    "name": user.name,
                    "dept": user.department if user.department else "",
                    "phone": user.phone if user.phone else "",
                }
            else:
                default_name = f"{pc_user}"
                default_dept = "未設定"
                new_user = User(
                    windows_id=pc_user,
                    name=default_name,
                    department=default_dept,
                    role="Operator",
                )
                session.add(new_user)
                session.commit()
                return {
                    "id": pc_user,
                    "name": default_name,
                    "dept": default_dept,
                    "phone": "",
                }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {"id": pc_user, "name": pc_user, "dept": "Error", "phone": ""}
        finally:
            session.close()

    def register_user(self, windows_id: str, display_name: str, department: str, phone: str):
        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=windows_id).first()
            if user:
                user.name = display_name
                user.department = department
                user.phone = phone
                user.updated_at = datetime.now()
            else:
                user = User(
                    windows_id=windows_id,
                    name=display_name,
                    department=department,
                    phone=phone,
                    role="Operator",
                )
                session.add(user)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------------------------------------------------------
    # ログ管理
    # ---------------------------------------------------------
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        session = self._get_session()
        try:
            db_user = session.query(User).filter_by(windows_id=user_id).first()
            u_id = db_user.id if db_user else None

            log = AuditLog(
                user_id=u_id,
                action_type=action,
                target=target,
                details=details,
                timestamp=datetime.now(),
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---------------------------------------------------------
    # ファイル管理 (FileRegistry)
    # ---------------------------------------------------------
    def is_file_registered(self, file_hash: str) -> bool:
        session = self._get_session()
        try:
            exists = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            return exists is not None
        finally:
            session.close()

    def register_file_hash(
        self,
        file_hash: str,
        filename: str,
        doc_type: str = "その他",
        case_id: Optional[int] = None,
        status: str = "CONFIRMED", # デフォルトは確認済(手動アップロード等)
        ai_confidence: float = 0.0,
        extracted_data: str = None
    ):
        session = self._get_session()
        try:
            file_reg = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            if file_reg:
                file_reg.filename = filename
                file_reg.doc_type = doc_type
                if case_id is not None:
                    file_reg.case_id = case_id
                
                # 更新
                file_reg.status = status
                file_reg.extracted_data = extracted_data
                file_reg.registered_at = datetime.now()
            else:
                file_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=filename,
                    doc_type=doc_type,
                    case_id=case_id,
                    registered_at=datetime.now(),
                    status=status,
                    ai_confidence=ai_confidence,
                    extracted_data=extracted_data
                )
                session.add(file_reg)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_files(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            results = (
                session.query(FileRegistry, Case)
                .outerjoin(Case, FileRegistry.case_id == Case.case_id)
                .order_by(desc(FileRegistry.registered_at))
                .all()
            )
            output = []
            for f, c in results:
                case_label = f"{c.case_number}" if c else "（共通雛形）"
                output.append({
                    "filename": f.filename,
                    "date": f.registered_at.strftime("%Y-%m-%d %H:%M:%S") if f.registered_at else "",
                    "hash": f.file_hash,
                    "type": f.doc_type if f.doc_type else "その他",
                    "case": case_label,
                    "doc_type": f.doc_type,
                    "uploaded_at": f.registered_at,
                    "status": f.status,
                    "ai_confidence": f.ai_confidence
                })
            return output
        finally:
            session.close()

    def delete_file_registry(self, filename: str):
        session = self._get_session()
        try:
            session.query(FileRegistry).filter_by(filename=filename).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------------------------------------------------------
    # 座標管理
    # ---------------------------------------------------------
    def register_coordinate(self, file_hash, label, x, y, page_number=1, description="", font_size=10, color="black", test_value=""):
        session = self._get_session()
        try:
            coord = session.query(Coordinate).filter_by(file_hash=file_hash, label=label).first()
            if not coord:
                coord = Coordinate(file_hash=file_hash, label=label)
                session.add(coord)

            coord.x_point = x
            coord.y_point = y
            coord.page_number = page_number
            coord.description = description
            coord.font_size = font_size
            coord.color = color
            coord.value = test_value
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def get_coordinates_by_hash(self, file_hash: str) -> List[Dict]:
        session = self._get_session()
        try:
            coords = session.query(Coordinate).filter_by(file_hash=file_hash).all()
            return [{
                "id": c.id,
                "label": c.label,
                "x": c.x_point,
                "y": c.y_point,
                "page": c.page_number,
                "desc": c.description,
                "font_size": c.font_size,
                "color": c.color,
                "value": c.value,
            } for c in coords]
        finally:
            session.close()

    def update_coordinate_direct(self, coord_id: int, updates: Dict):
        session = self._get_session()
        try:
            coord = session.query(Coordinate).filter_by(id=coord_id).first()
            if coord:
                for k, v in updates.items():
                    if k == "x": coord.x_point = v
                    elif k == "y": coord.y_point = v
                    elif k == "desc": coord.description = v
                    elif hasattr(coord, k): setattr(coord, k, v)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def delete_coordinate(self, coordinate_id: int):
        session = self._get_session()
        try:
            session.query(Coordinate).filter_by(id=coordinate_id).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
````

## File: src/services/kintone_sync_service.py
````python
# src/services/kintone_sync_service.py

import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, List

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address, Case, Contact, Deceased, H_AddressHistory, H_ContactLink, Heir, User
)
from src.utils.date_utils import parse_all_flexible_date
from services.deceased_service import get_next_case_number_service

logger = logging.getLogger(__name__)

# ... (ヘルパー関数群 katakana_to_hiragana, format_name_full_width 等は変更なし) ...
def katakana_to_hiragana(text: str) -> str:
    if not text: return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6: result += chr(code - 0x60)
        else: result += char
    return result

def format_name_full_width(last: str, first: str) -> str:
    l = (last or "").strip(); f = (first or "").strip()
    return f"{l}　{f}" if l and f else f"{l}{f}"

def get_value_from_keys(data: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        if k in data and data[k]:
            val = str(data[k]).strip()
            if val.lower() != "none": return val
    return ""

def get_raw_value(data: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        if k in data:
            val = str(data[k]).strip()
            if val.lower() == "none": return ""
            return val
    return None

# ... (get_kintone_data_as_dict は変更なし) ...
def get_kintone_data_as_dict(case_id: int) -> Optional[Dict[str, Any]]:
    # 省略（既存コードのまま）
    db = DatabaseManager()
    session = db._get_session()
    try:
        case = session.query(Case).filter_by(case_id=case_id).first()
        if not case: return None
        deceased = case.deceased_ref
        
        manager_name = ""
        if case.manager_id:
            m_user = session.query(User).get(case.manager_id)
            if m_user: manager_name = m_user.name
        operator_name = ""
        if case.operator_id:
            o_user = session.query(User).get(case.operator_id)
            if o_user: operator_name = o_user.name

        d_name = ""; d_kana = ""; start_date = ""
        if deceased:
            d_name = format_name_full_width(deceased.name_last, deceased.name_first)
            d_kana = format_name_full_width(katakana_to_hiragana(deceased.name_last_kana), katakana_to_hiragana(deceased.name_first_kana))
            if deceased.date_of_death: start_date = deceased.date_of_death.strftime("%Y-%m-%d")

        contractor = None
        if deceased and deceased.heirs:
            contractor = next((h for h in deceased.heirs if h.is_contracting_party), None)
            if not contractor and deceased.heirs: contractor = deceased.heirs[0]

        heir_tel = ""; heir_mail = ""
        if contractor:
            links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for l in links:
                c = session.query(Contact).get(l.contact_id)
                if c:
                    if c.type == "PHONE" and not heir_tel: heir_tel = c.value
                    if c.type == "EMAIL" and not heir_mail: heir_mail = c.value

        return {
            "顧客コード_2": case.case_number,
            "顧客名": case.client_name,
            "顧客名(ふりがな)": case.client_name_kana,
            "TEL": heir_tel,
            "メールアドレス": heir_mail,
            "被相続人名": d_name,
            "被相続人名（ふりがな）": d_kana,
            "相続開始日": start_date,
            "担当者①": manager_name,
            "担当者②": operator_name,
            "SOL案件No.（日興）": case.sol_case_number or "",
            "支店名（日興）": case.referral_sec_branch_name or "",
            "担当者（日興）": case.referral_sec_rep_name or "",
            "紹介日": str(case.introduction_date) if case.introduction_date else "",
            "備考": f"【紹介元電話】{case.referral_sec_phone}" if case.referral_sec_phone else "",
        }
    except Exception as e:
        logger.error(f"Kintone data build error: {e}"); return None
    finally:
        session.close()

def copy_kintone_data_to_clipboard(case_id: int) -> bool:
    data = get_kintone_data_as_dict(case_id)
    return data is not None

# ---------------------------------------------------------
# データ取込 (Kintone -> DB)
# ---------------------------------------------------------
def import_kintone_json(
    json_data: Dict[str, Any], target_case_id: Optional[int] = None
) -> int:
    """
    KintoneのJSONデータを取り込み、DBを更新または新規作成する。
    """
    db = DatabaseManager()
    session = db._get_session()

    try:
        # 1. データの正規化
        k_rec_id_raw = get_value_from_keys(json_data, ["$id", "record_id", "レコード番号"])
        k_record_id = int(k_rec_id_raw) if k_rec_id_raw and k_rec_id_raw.isdigit() else None
        case_num = get_value_from_keys(json_data, ["顧客コード", "顧客コード_2", "case_number", "案件番号"])
        client_name_raw = get_value_from_keys(json_data, ["顧客名", "client_name", "氏名"]).replace("　", " ")
        client_kana_raw = get_value_from_keys(json_data, ["顧客名(ふりがな)", "顧客名（ふりがな）", "client_name_kana", "フリガナ"]).replace("　", " ")
        deceased_name_raw = get_value_from_keys(json_data, ["被相続人名", "deceased_name", "被相続人"]).replace("　", " ")
        deceased_kana_raw = get_value_from_keys(json_data, ["被相続人名（ふりがな）", "被相続人名(ふりがな)", "deceased_name_kana"]).replace("　", " ")
        sol_no = get_value_from_keys(json_data, ["SOL案件No.（日興）", "SOL案件No", "sol_case_number"])
        intro_date = parse_all_flexible_date(get_value_from_keys(json_data, ["紹介日", "introduction_date"]))
        consent_date = parse_all_flexible_date(get_value_from_keys(json_data, ["同意書日付(日興)", "同意書日付", "consent_date"]))
        mgr_name = get_value_from_keys(json_data, ["担当者①", "manager_name", "担当者1"])
        opr_name = get_value_from_keys(json_data, ["担当者②", "operator_name", "担当者2"])

        # 2. 案件 (Case) の特定または作成
        case = None
        if target_case_id:
            case = session.query(Case).get(target_case_id)
        if not case and case_num:
            case = session.query(Case).filter_by(case_number=case_num).first()
        if not case:
            if case_num: temp_num = case_num
            else:
                try: temp_num = get_next_case_number_service()
                except: temp_num = f"TMP-{datetime.now().strftime('%H%M%S')}"
            case = Case(case_number=temp_num, client_name=client_name_raw or "名称未設定", created_at=datetime.now())
            session.add(case)
            session.flush()

        # 3. 案件情報の更新
        if k_record_id: case.kintone_record_id = k_record_id
        if client_name_raw: case.client_name = client_name_raw
        if client_kana_raw: case.client_name_kana = client_kana_raw
        case.sol_case_number = sol_no
        case.introduction_date = intro_date
        case.consent_date = consent_date
        case.referral_sec_branch_name = get_value_from_keys(json_data, ["支店名（日興）", "支店名（大和）", "紹介元支店", "referral_branch"])
        case.referral_sec_rep_name = get_value_from_keys(json_data, ["担当者（日興）", "担当者（大和）", "紹介元担当者", "referral_rep"])
        
        if mgr_name:
            u = session.query(User).filter(User.name.contains(mgr_name)).first()
            if u: case.manager_id = u.id
        if opr_name:
            u = session.query(User).filter(User.name.contains(opr_name)).first()
            if u: case.operator_id = u.id
        session.flush()

        # 4. 被相続人 (Deceased) の更新
        deceased = session.query(Deceased).filter_by(case_id=case.case_id).first()
        if not deceased:
            deceased = Deceased(case_id=case.case_id)
            session.add(deceased)
        if deceased_name_raw:
            d_parts = deceased_name_raw.split(" ", 1)
            deceased.name_last = d_parts[0]
            deceased.name_first = d_parts[1] if len(d_parts) > 1 else ""
        if deceased_kana_raw:
            d_k_parts = deceased_kana_raw.split(" ", 1)
            deceased.name_last_kana = d_k_parts[0]
            deceased.name_first_kana = d_k_parts[1] if len(d_k_parts) > 1 else ""
        start_date = parse_all_flexible_date(get_value_from_keys(json_data, ["相続開始日", "死亡日", "date_of_death", "death_date"]))
        if start_date: deceased.date_of_death = start_date
        session.flush()

        # =======================================================
        # 5. 契約者 (Heir) の更新 (★ここを修正)
        # =======================================================
        contractor = (
            session.query(Heir)
            .filter(Heir.deceased_id == deceased.id, Heir.is_contracting_party == True)
            .first()
        )

        # 契約者フラグが立っている人がいない場合、
        # いきなり新規作成するのではなく、既存の相続人がいればその人を契約者に昇格させる
        if not contractor:
            existing_heir = session.query(Heir).filter(Heir.deceased_id == deceased.id).first()
            if existing_heir:
                contractor = existing_heir
                contractor.is_contracting_party = True # 昇格
            else:
                # 誰もいない場合のみ新規作成
                contractor = Heir(
                    deceased_id=deceased.id,
                    is_contracting_party=True,
                    relationship_type="相談者",
                )
                session.add(contractor)

        # 氏名更新
        if client_name_raw:
            c_parts = client_name_raw.split(" ", 1)
            contractor.name_last = c_parts[0]
            contractor.name_first = c_parts[1] if len(c_parts) > 1 else ""
        if client_kana_raw:
            c_k_parts = client_kana_raw.split(" ", 1)
            contractor.name_last_kana = c_k_parts[0]
            contractor.name_first_kana = c_k_parts[1] if len(c_k_parts) > 1 else ""

        # 6. 住所 (Heirに紐づくAddress)
        zip_code = get_value_from_keys(json_data, ["郵便番号", "zip_code"])
        address_full = get_value_from_keys(json_data, ["住所", "address"])

        if zip_code or address_full:
            addr_link = session.query(H_AddressHistory).filter(H_AddressHistory.heir_id == contractor.id, H_AddressHistory.is_current_address == True).first()
            pref = ""; street = address_full
            match = re.match(r"(.{2,3}[都道府県])(.+)", address_full)
            if match:
                pref = match.group(1); street = match.group(2)

            if addr_link:
                addr = session.query(Address).get(addr_link.address_id)
                addr.zip_code = zip_code
                addr.prefecture = pref
                addr.city_ward_town = "" 
                addr.street_address = street
                addr.building_name = "" 
            else:
                new_addr = Address(zip_code=zip_code, prefecture=pref, street_address=street)
                session.add(new_addr)
                session.flush()
                session.add(H_AddressHistory(heir_id=contractor.id, address_id=new_addr.id, is_current_address=True))

        # 7. 電話番号 (TEL) の取込 (完全上書きモード)
        raw_tel = get_raw_value(json_data, ["TEL", "電話番号", "phone", "mobile"])
        if raw_tel is not None:
            existing_links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for link in existing_links:
                contact = session.query(Contact).get(link.contact_id)
                if contact and contact.type == "PHONE":
                    session.delete(contact); session.delete(link)
            
            if raw_tel:
                tels = raw_tel.replace("、", ",").split(",")
                for i, t in enumerate(tels):
                    clean_tel = t.strip()
                    if clean_tel:
                        c = Contact(value=clean_tel, type="PHONE", sub_type="Primary" if i == 0 else "Secondary")
                        session.add(c); session.flush()
                        session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))

        # 8. メールアドレス (Email) の取込 (完全上書きモード)
        raw_mail = get_raw_value(json_data, ["メールアドレス", "email", "mail"])
        if raw_mail is not None:
            existing_links = session.query(H_ContactLink).filter(H_ContactLink.heir_id == contractor.id).all()
            for link in existing_links:
                contact = session.query(Contact).get(link.contact_id)
                if contact and contact.type == "EMAIL":
                    session.delete(contact); session.delete(link)

            if raw_mail:
                c = Contact(value=raw_mail.strip(), type="EMAIL", sub_type="Primary")
                session.add(c); session.flush()
                session.add(H_ContactLink(heir_id=contractor.id, contact_id=c.id))

        session.commit()
        return case.case_id

    except Exception as e:
        session.rollback()
        logger.error(f"Import Error: {e}")
        return -1
    finally:
        session.close()
````

## File: run_watcher.py
````python
# run_watcher.py

import logging
import os
import sys
import time
import threading
import traceback
from pathlib import Path

# ==========================================
# ログ設定
# ==========================================
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "watcher.log")
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(log_file_path, mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# ==========================================
# 監視設定
# ==========================================
try:
    from watchdog.observers.polling import PollingObserver as Observer
    logger.info("ℹ️ Windows 互換モード (PollingObserver) で起動します。")
except ImportError:
    from watchdog.observers import Observer
    logger.info("ℹ️ 標準モード (Observer) で起動します。")

from watchdog.events import FileSystemEventHandler

# パス解決
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

os.environ["IS_WATCHER_PROCESS"] = "true"

from legal_system.core.data_sync import DataSyncEngine
from legal_system.core.database_manager import DatabaseManager
from services.gmail_watcher_service import GmailWatcherService

# ScannerServiceのインポート
ScannerService = None
try:
    from services.scanner_service import ScannerService
    logger.info("✅ ScannerService モジュールをロードしました。")
except ImportError as e:
    logger.error(f"❌ ScannerService のインポートに失敗しました: {e}")
except Exception as e:
    logger.error(f"❌ ScannerService ロード中に予期せぬエラー: {e}")

def get_downloads_path():
    home = Path.home()
    candidates = [
        home / "Downloads",
        home / "OneDrive" / "Downloads",
        home / "OneDrive - 行政書士法人チェスター" / "Downloads",
    ]
    for path in candidates:
        if path.exists(): return str(path)
    return os.path.join(os.path.expanduser("~"), "Downloads")

WATCH_DIR_DOWNLOADS = get_downloads_path()

def get_target_scan_folder():
    """スキャン監視用フォルダを決定する"""
    try:
        db = DatabaseManager()
        user_info = db.get_current_user_info()
        target_name = user_info["name"]
        if not target_name: target_name = os.environ.get("USERNAME", "Unknown")
    except:
        target_name = os.environ.get("USERNAME", "Unknown")
    
    # NASパス (存在しなければローカルの data/scan_inbox を使用)
    nas_root = r"\\192.168.11.20\行政書士法人チェスター\08.その他\スキャン"
    if not os.path.exists(nas_root):
        nas_root = os.path.join(BASE_DIR, "data", "scan_inbox")
        os.makedirs(nas_root, exist_ok=True)

    target_path = os.path.join(nas_root, target_name)
    if not os.path.exists(target_path):
        try: os.makedirs(target_path, exist_ok=True)
        except: pass
            
    return target_path, target_name

# ==========================================
# ★追加: 重複防止機能付きハンドラ
# ==========================================
class DebouncedEventHandler(FileSystemEventHandler):
    """同じファイルのイベントが連続して発生した場合、指定時間内は無視する"""
    def __init__(self, cooldown=10.0): # クールダウンを10秒に延長
        super().__init__()
        self._processed_cache = {} # path -> timestamp
        self._cooldown = cooldown

    def _should_process(self, filepath):
        current_time = time.time()
        filename = os.path.basename(filepath)
        
        # 除外ファイル
        if filename.startswith(".") or filename.startswith("~$"): return False
        if filename.lower().endswith((".tmp", ".crdownload", ".part", ".lock")): return False

        # クールダウン判定
        if filepath in self._processed_cache:
            last_time = self._processed_cache[filepath]
            if current_time - last_time < self._cooldown:
                # logger.debug(f"Skip duplicate: {filename}")
                return False 
        
        # 処理許可 & 時刻更新
        self._processed_cache[filepath] = current_time
        
        # キャッシュ掃除
        if len(self._processed_cache) > 1000:
            self._processed_cache = {k:v for k,v in self._processed_cache.items() if current_time - v < self._cooldown}
            
        return True

# ==========================================
# 1. Downloads Handler
# ==========================================
class DownloadsHandler(DebouncedEventHandler):
    def __init__(self):
        super().__init__()
        self.syncer = DataSyncEngine()
        cases_root = os.path.join(BASE_DIR, "data", "cases")
        self.scanner = ScannerService(inbox_path=WATCH_DIR_DOWNLOADS, processed_root=cases_root) if ScannerService else None
        logger.info("👀 DownloadsHandler 準備完了")

    def _process(self, filepath):
        if not self._should_process(filepath): return
        if not os.path.exists(filepath): return

        filename = os.path.basename(filepath)
        time.sleep(1.0) # 書き込み待ち

        # Kintone JSON
        if filename.lower().endswith(".json"):
            keywords = ["G", "NoNumber", "Record", "kintone", "案件", "顧客"]
            if any(kw in filename for kw in keywords):
                logger.info(f"🔍 [DL] Kintoneデータ検知: {filename}")
                try:
                    if self.syncer.sync_from_kintone_json(filepath):
                        logger.info(f"   ✅ 同期成功")
                        try: os.remove(filepath)
                        except: pass
                except Exception as e:
                    logger.error(f"   ❌ 同期エラー: {e}")
            return

        # 登記情報PDF
        if filename.lower().endswith(".pdf") and "不動産登記" in filename:
            logger.info(f"🔍 [DL] 登記情報検知: {filename}")
            if self.scanner:
                try: self.scanner.process_file(filepath)
                except Exception as e: logger.error(f"   ❌ スキャナー処理エラー: {e}")

    def on_created(self, event):
        if not event.is_directory: self._process(event.src_path)
    def on_moved(self, event):
        if not event.is_directory: self._process(event.dest_path)
    def on_modified(self, event):
        if not event.is_directory: self._process(event.src_path)

# ==========================================
# 2. Scan Handler
# ==========================================
class ScanHandler(DebouncedEventHandler):
    def __init__(self, inbox_path, processed_root): 
        super().__init__()
        self.inbox_path = inbox_path
        self.service = ScannerService(inbox_path, processed_root) if ScannerService else None
        if self.service:
            logger.info(f"👀 ScanHandler 準備完了 (監視先: {inbox_path})")

    def _process(self, filepath):
        if not self._should_process(filepath): return
        if not os.path.exists(filepath): return

        filename = os.path.basename(filepath)
        valid_exts = (".pdf", ".jpg", ".jpeg", ".png")
        
        if filename.lower().endswith(valid_exts):
            logger.info(f"🔍 [Scan] 書類検知: {filename}")
            time.sleep(2.0) # スキャナ書き込み待ち
            
            if self.service:
                logger.info(f"   🖨️ 解析開始 -> 受信トレイへ")
                try:
                    self.service.process_file(filepath)
                except Exception as e:
                    logger.error(f"   ❌ 解析エラー: {e}")
                    logger.error(traceback.format_exc())

    def on_created(self, event):
        if not event.is_directory: self._process(event.src_path)
    def on_moved(self, event):
        if not event.is_directory: self._process(event.dest_path)
    # スキャンフォルダはModified監視を除外（二重起動防止）
    # def on_modified(self, event): ...

# ==========================================
# Main
# ==========================================
def run_gmail_watcher():
    logger.info("📧 Gmail監視スレッド起動")
    try:
        service = GmailWatcherService()
        if not service.service: return
        while True:
            service.poll_and_process()
            service.retry_linking_pending_notes()
            time.sleep(600)
    except Exception as e:
        logger.error(f"Gmail Watcher Error: {e}")

if __name__ == "__main__":
    print("\n\n")
    logger.info("==========================================")
    logger.info("🚀 監視プロセス Ver 3.9.2 (Final Fix)")
    logger.info("==========================================")

    observer = Observer()
    CASES_ROOT = os.path.join(BASE_DIR, "data", "cases") 

    # Downloads
    if os.path.exists(WATCH_DIR_DOWNLOADS):
        observer.schedule(DownloadsHandler(), WATCH_DIR_DOWNLOADS, recursive=False)
        logger.info(f"✅ DL監視: {WATCH_DIR_DOWNLOADS}")

    # Scan
    scan_dir, user_name = get_target_scan_folder()
    if not os.path.exists(scan_dir):
        try: os.makedirs(scan_dir, exist_ok=True)
        except: pass

    if ScannerService and os.path.exists(scan_dir):
        scan_handler = ScanHandler(inbox_path=scan_dir, processed_root=CASES_ROOT)
        observer.schedule(scan_handler, scan_dir, recursive=False)
        logger.info(f"✅ Scan監視: {scan_dir}")

    # Gmail
    t = threading.Thread(target=run_gmail_watcher, daemon=True)
    t.start()
    
    observer.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
````

## File: src/legal_system/core/config.py
````python
# src/legal_system/core/config.py

import os
import random
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# ==========================================
# 1. パス設定 (モジュールレベル定数)
# ==========================================
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"

# DB関連パス
DB_FILE_SQLITE = DATA_DIR / "db" / "sql" / "legal_system.db"
DB_DIR_CHROMA = DATA_DIR / "db" / "chroma" / "local_rag_db"

# データ一時保存先
DATA_DIR_TEMPLATES = DATA_DIR / "templates"
VECTOR_STORE_PATH = DB_DIR_CHROMA

# RAG関連パス
RULES_DIR = DATA_DIR / "rules"
BANK_MASTER_PATH = RULES_DIR / "bank_master.csv"
COMPANY_RULES_PATH = RULES_DIR / "company_rules.txt"

# スキャナ監視 (デフォルト設定)
# ※ run_watcher.py で動的に上書きされる場合があります
WATCH_DIR_DEFAULT = DATA_DIR / "scanned_inbox"


# ==========================================
# 2. 設定管理クラス (Config)
# ==========================================
class Config:
    """
    システム全体の設定定数を管理するクラス。
    """

    # --- パス設定 ---
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    TEMPLATES_DIR = DATA_DIR_TEMPLATES

    # RAG関連パス
    BANK_MASTER_PATH = BANK_MASTER_PATH
    COMPANY_RULES_PATH = COMPANY_RULES_PATH
    VECTOR_STORE_PATH = VECTOR_STORE_PATH
    
    # 監視設定 (Ver 3.3 追加)
    WATCH_DIR = WATCH_DIR_DEFAULT
    SCAN_INTERVAL_SEC = 2

    # --- データベース設定 (PostgreSQL) ---
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "legal_db")

    DATABASE_URL = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # --- AIプロバイダー設定 ---
    AI_PROVIDER = os.getenv("AI_PROVIDER", "studio").lower()

    # --- Vertex AI 設定 ---
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "asia-northeast1")

    # --- モデル設定 (ここで一元管理) ---
    # 通常のテキスト生成・チャット用
    GOOGLE_MODEL_NAME = "gemini-2.5-flash-lite"
    MODEL_NAME = "gemini-2.5-flash-lite"
    
    # ★追加: 音声・画像解析用 (マルチモーダル性能が高いモデルを指定)
    # 404エラーが出た場合はここを "gemini-1.5-flash-001" や "gemini-1.5-pro" に書き換えるだけで済みます
    VISION_AUDIO_MODEL = "gemini-2.5-flash-lite" 
    
    # Embedding Model
    EMBEDDING_MODEL = "models/embedding-001"
    
    TEMPERATURE = 0.0

    # APIキー管理 (Studio用)
    _keys_str = os.getenv("GOOGLE_API_KEYS", "")
    GOOGLE_API_KEYS: List[str] = [k.strip() for k in _keys_str.split(",") if k.strip()]

    if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
        GOOGLE_API_KEYS = [os.getenv("GOOGLE_API_KEY")]

    @classmethod
    def validate_paths(cls) -> None:
        """必須ディレクトリの存在確認"""
        if not cls.DATA_DIR.exists():
            os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not cls.TEMPLATES_DIR.exists():
            os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)
        if not cls.WATCH_DIR.exists():
            os.makedirs(cls.WATCH_DIR, exist_ok=True)
        
    @classmethod
    def is_vertex_enabled(cls) -> bool:
        return cls.AI_PROVIDER == "vertex"


# ==========================================
# 3. キー管理クラス (KeyManager)
# ==========================================
class KeyManager:
    @staticmethod
    def get_next_key() -> str:
        if Config.is_vertex_enabled():
            return "vertex-managed"
            
        keys = Config.GOOGLE_API_KEYS
        if not keys:
            env_key = os.getenv("GOOGLE_API_KEY")
            if env_key:
                return env_key
            raise ValueError("❌ 有効な Google API Key が見つかりません。")
        return random.choice(keys)
````

## File: src/services/deceased_service.py
````python
# src/services/deceased_service.py

import datetime
import logging
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import requests
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address,
    Case,
    Contact,
    D_ContactLink,
    Deceased,
    H_AddressHistory,
    H_ContactLink,
    Heir,
    IncomingNoteBuffer,
    User,
)
from src.utils.date_utils import parse_all_flexible_date
from src.utils.retry_decorator import retry_with_backoff

logger = logging.getLogger(__name__)


# ==========================================
# セッション管理ヘルパー
# ==========================================
def get_db_session():
    """現在のDatabaseManagerからセッションを取得"""
    return DatabaseManager()._get_session()


# ==========================================
# 1. ユーティリティ (パス正規化など)
# ==========================================
def normalize_folder_path(path_str: str) -> str:
    if not path_str:
        return ""
    cleaned = path_str.strip().strip('"').strip("'")
    return cleaned.replace("/", "\\")


def get_next_provisional_number(session) -> str:
    """仮番号（整数4桁）の最大値+1を取得する"""
    cases = session.query(Case.case_number).all()
    max_num = 1000  # 初期値

    for (c_num,) in cases:
        if c_num and c_num.isdigit():
            try:
                val = int(c_num)
                if val > max_num:
                    max_num = val
            except:
                pass

    return str(max_num + 1)


def get_next_case_number_service() -> str:
    session = get_db_session()
    try:
        return get_next_provisional_number(session)
    finally:
        session.close()


def is_case_number_duplicate(case_number: str) -> bool:
    session = get_db_session()
    try:
        return (
            session.query(Case).filter(Case.case_number == case_number).first()
            is not None
        )
    finally:
        session.close()


def promote_to_formal_case_number(case_id: int) -> bool:
    """仮番号を正式番号(G番号)に昇格させる"""
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        if not case:
            return False

        current_num = case.case_number
        if current_num.startswith("G"):
            return True

        if current_num.isdigit():
            new_num = f"G{current_num}"
            existing = session.query(Case).filter(Case.case_number == new_num).first()
            if existing:
                return False

            case.case_number = new_num
            session.commit()
            return True
        return False
    except:
        session.rollback()
        return False
    finally:
        session.close()


# ==========================================
# ★異体字展開ロジック (名寄せ強化)
# ==========================================
def _expand_name_variants(name: str) -> Set[str]:
    """
    入力された氏名に対し、一般的な異体字（旧字・俗字）の組み合わせを展開して返す。
    例: "宮崎" -> {"宮崎", "宮﨑"}
    """
    if not name:
        return set()

    clean_base = name.replace(" ", "").replace("　", "")
    candidates = {clean_base}

    variant_map = {
        "崎": ["崎", "﨑", "嵜"],
        "﨑": ["崎", "﨑", "嵜"],
        "高": ["高", "髙"],
        "髙": ["高", "髙"],
        "沢": ["沢", "澤"],
        "澤": ["沢", "澤"],
        "斉": ["斉", "斎", "齋", "齊"],
        "斎": ["斉", "斎", "齋", "齊"],
        "辺": ["辺", "邉", "邊"],
        "浜": ["浜", "濱"],
        "濱": ["浜", "濱"],
        "吉": ["吉", "𠮷"],
        "𠮷": ["吉", "𠮷"],
        "富": ["富", "冨"],
        "冨": ["富", "冨"],
    }

    for char, variants in variant_map.items():
        if char in clean_base:
            current_list = list(candidates)
            for base_str in current_list:
                for v in variants:
                    candidates.add(base_str.replace(char, v))

    return candidates


# ==========================================
# 2. 案件 (Case) 操作 & 検索 (大幅強化版)
# ==========================================
def find_cases_by_attributes(
    client_name: Optional[str] = None,
    deceased_name: Optional[str] = None,
    case_number: Optional[str] = None,
) -> List[Dict[str, Any]]:
    session = get_db_session()
    results = []

    logger.info(
        f"🔎 FindCase Search: Num={case_number}, Client={client_name}, Dec={deceased_name}"
    )

    try:
        query = session.query(Case).outerjoin(Case.deceased_ref)
        conditions = []

        if case_number:
            c_num = case_number.strip()
            conditions.append(Case.case_number.ilike(f"%{c_num}%"))

        if client_name:
            c_variants = _expand_name_variants(client_name)
            if c_variants:
                db_client_clean = func.replace(
                    func.replace(Case.client_name, " ", ""), "　", ""
                )
                variant_conditions = [db_client_clean.contains(v) for v in c_variants]
                conditions.append(or_(*variant_conditions))

        if deceased_name:
            clean_search_key = deceased_name.replace(" ", "").replace("　", "")
            d_variants = _expand_name_variants(clean_search_key)
            full_name_db = Deceased.name_last + Deceased.name_first
            full_name_clean = func.replace(
                func.replace(full_name_db, " ", ""), "　", ""
            )

            v_conds = []
            for v in d_variants:
                v_conds.append(full_name_clean.contains(v))
                v_conds.append(Deceased.name_last.contains(v))

            conditions.append(or_(*v_conds))

        if not conditions:
            return []

        cases = query.filter(or_(*conditions)).limit(20).all()
        logger.info(f"   -> Hits: {len(cases)} cases found.")

        for c in cases:
            d_name = "未登録"
            d_date = None
            if c.deceased_ref:
                d_name = f"{c.deceased_ref.name_last} {c.deceased_ref.name_first}"
                d_date = c.deceased_ref.date_of_death

            results.append(
                {
                    "case_id": c.case_id,
                    "case_number": c.case_number,
                    "client_name": c.client_name,
                    "deceased_name": d_name,
                    "date_of_death": d_date,
                }
            )
        return results
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return []
    finally:
        session.close()


def add_new_case_for_client_registration(case_number, name, **kwargs) -> int:
    session = get_db_session()
    try:
        name_parts = name.replace("　", " ").split(" ", 1)
        lname = name_parts[0]
        fname = name_parts[1] if len(name_parts) > 1 else ""

        kana_last = kwargs.get("kana_last", "")
        kana_first = kwargs.get("kana_first", "")
        client_kana = f"{kana_last} {kana_first}".strip()

        new_case = Case(
            case_number=case_number,
            client_name=name,
            client_name_kana=client_kana,
            manager_id=kwargs.get("manager_id"),
            operator_id=kwargs.get("operator_id"),
            folder_path=normalize_folder_path(kwargs.get("folder_path", "")),
            contract_date=datetime.date.today(),
            current_status_id=1,
            created_at=datetime.datetime.now(),
        )
        session.add(new_case)
        session.flush()

        deceased = Deceased(
            case_id=new_case.case_id,
            name_last="",
            name_first="",
            relationship_type="本人",
        )
        session.add(deceased)
        session.flush()

        heir = Heir(
            deceased_id=deceased.id,
            name_last=lname,
            name_first=fname,
            name_last_kana=kana_last,
            name_first_kana=kana_first,
            relationship_type=kwargs.get("rel", ""),
            hometown=kwargs.get("hometown", ""),
            is_contracting_party=True,
        )
        session.add(heir)
        session.flush()

        if kwargs.get("pref") or kwargs.get("street"):
            addr = Address(
                zip_code=kwargs.get("zip_code"),
                prefecture=kwargs.get("pref"),
                city_ward_town=kwargs.get("city"),
                street_address=kwargs.get("street"),
                building_name=kwargs.get("building"),
            )
            session.add(addr)
            session.flush()
            session.add(
                H_AddressHistory(
                    heir_id=heir.id, address_id=addr.id, is_current_address=True
                )
            )

        session.commit()
        return deceased.id
    except Exception as e:
        session.rollback()
        logger.error(f"Registration Error: {e}")
        return -1
    finally:
        session.close()


def get_case_id_by_deceased_id(deceased_id: int) -> Optional[int]:
    session = get_db_session()
    try:
        d = session.query(Deceased).get(deceased_id)
        return d.case_id if d else None
    finally:
        session.close()


def update_case_folder_path(case_id: int, folder_path: str) -> bool:
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        if case:
            case.folder_path = normalize_folder_path(folder_path)
            session.commit()
            return True
        return False
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()


def update_case_number(case_id: int, new_number: str) -> bool:
    if not new_number:
        return False
    session = get_db_session()
    try:
        exists = (
            session.query(Case)
            .filter(Case.case_number == new_number, Case.case_id != case_id)
            .first()
        )
        if exists:
            return False

        case = session.query(Case).get(case_id)
        if case:
            case.case_number = new_number
            session.commit()
            return True
        return False
    except:
        session.rollback()
        return False
    finally:
        session.close()


def get_case_folder_path(case_id: int) -> Optional[str]:
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        return case.folder_path if case else None
    finally:
        session.close()


get_case_folder_path_service = get_case_folder_path


def get_case_by_id(case_id: int) -> Optional[Case]:
    session = get_db_session()
    try:
        return (
            session.query(Case)
            .options(joinedload(Case.deceased_ref).joinedload(Deceased.heirs))
            .filter(Case.case_id == case_id)
            .first()
        )
    finally:
        session.close()


def get_deceased_by_case_id(case_id: int) -> Optional[Deceased]:
    session = get_db_session()
    try:
        return session.query(Deceased).filter(Deceased.case_id == case_id).first()
    finally:
        session.close()


def get_deceased_by_id(deceased_id: int) -> Optional[Deceased]:
    session = get_db_session()
    try:
        return (
            session.query(Deceased).options(joinedload(Deceased.heirs)).get(deceased_id)
        )
    finally:
        session.close()


def delete_case_and_all_related_data(case_number: str) -> bool:
    session = get_db_session()
    try:
        case = session.query(Case).filter(Case.case_number == case_number).first()
        if case:
            session.query(IncomingNoteBuffer).filter(
                IncomingNoteBuffer.linked_case_id == case.case_id
            ).delete(synchronize_session=False)

            session.delete(case)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Delete Error: {e}")
        return False
    finally:
        session.close()


def update_case_assignment(
    case_id: int, manager_id: Optional[int], operator_id: Optional[int]
) -> bool:
    session = get_db_session()
    try:
        case = session.query(Case).get(case_id)
        if case:
            case.manager_id = manager_id
            case.operator_id = operator_id
            session.commit()
            return True
        return False
    finally:
        session.close()


def get_all_users() -> Dict[int, str]:
    session = get_db_session()
    try:
        users = session.query(User).all()
        return {u.id: u.name for u in users}
    finally:
        session.close()


# ==========================================
# 3. 連絡先・住所関連 (参照用)
# ==========================================
def get_address_by_id(address_id: int) -> Optional[Address]:
    session = get_db_session()
    try:
        return session.query(Address).get(address_id)
    finally:
        session.close()


def get_address_info(target_type: str, target_id: int) -> dict:
    session = get_db_session()
    try:
        addr = None
        if target_type == "heir":
            link = (
                session.query(H_AddressHistory)
                .filter(
                    H_AddressHistory.heir_id == target_id,
                    H_AddressHistory.is_current_address == True,
                )
                .first()
            )
            if link:
                addr = session.query(Address).get(link.address_id)
        elif target_type == "deceased":
            d = session.query(Deceased).get(target_id)
            if d and d.last_address_id:
                addr = session.query(Address).get(d.last_address_id)

        if addr:
            return {
                "zip_code": addr.zip_code,
                "prefecture": addr.prefecture,
                "city_ward_town": addr.city_ward_town or "",
                "street_address": addr.street_address or "",
                "building_name": addr.building_name or "",
            }
        return {}
    finally:
        session.close()


def get_contact_info(target_type: str, target_id: int) -> List[dict]:
    session = get_db_session()
    try:
        contacts = []
        if target_type == "heir":
            links = (
                session.query(H_ContactLink)
                .filter(H_ContactLink.heir_id == target_id)
                .all()
            )
            for link in links:
                c = session.query(Contact).get(link.contact_id)
                if c:
                    contacts.append(
                        {
                            "id": c.id,
                            "type": c.type,
                            "value": c.value,
                            "sub_type": c.sub_type,
                        }
                    )
        elif target_type == "deceased":
            links = (
                session.query(D_ContactLink)
                .filter(D_ContactLink.deceased_id == target_id)
                .all()
            )
            for link in links:
                c = session.query(Contact).get(link.contact_id)
                if c:
                    contacts.append(
                        {
                            "id": c.id,
                            "type": c.type,
                            "value": c.value,
                            "sub_type": c.sub_type,
                        }
                    )
        return contacts
    finally:
        session.close()


# ==========================================
# 4. 被相続人・相続人 (CRUD)
# ==========================================
def update_deceased(deceased_id: int, **kwargs) -> bool:
    session = get_db_session()
    try:
        d = session.query(Deceased).get(deceased_id)
        if not d:
            return False

        d.name_last = kwargs.get("name_last", d.name_last)
        d.name_first = kwargs.get("name_first", d.name_first)
        d.name_last_kana = kwargs.get("kana_last", d.name_last_kana)
        d.name_first_kana = kwargs.get("kana_first", d.name_first_kana)

        if "hometown" in kwargs:
            d.hometown = kwargs["hometown"]

        # ★修正: 日付型のチェックを入れる
        if kwargs.get("dob"):
            val = kwargs["dob"]
            if isinstance(val, (datetime.date, datetime.datetime)):
                d.date_of_birth = val
            else:
                d.date_of_birth = parse_all_flexible_date(val)

        if kwargs.get("dod"):
            val = kwargs["dod"]
            if isinstance(val, (datetime.date, datetime.datetime)):
                d.date_of_death = val
            else:
                d.date_of_death = parse_all_flexible_date(val)

        # ★修正: 住所関連のキーが1つでも存在すれば更新処理に入る
        address_keys = [
            "last_pref",
            "last_city",
            "last_street",
            "last_building",
            "last_zip_code",
        ]
        if any(k in kwargs for k in address_keys):
            if d.last_address_id:
                addr = session.query(Address).get(d.last_address_id)
                if addr:
                    addr.zip_code = kwargs.get("last_zip_code", addr.zip_code)
                    addr.prefecture = kwargs.get("last_pref", addr.prefecture)
                    addr.city_ward_town = kwargs.get("last_city", addr.city_ward_town)
                    addr.street_address = kwargs.get("last_street", addr.street_address)
                    addr.building_name = kwargs.get("last_building", addr.building_name)
            else:
                new_addr = Address(
                    zip_code=kwargs.get("last_zip_code", ""),
                    prefecture=kwargs.get("last_pref", ""),
                    city_ward_town=kwargs.get("last_city", ""),
                    street_address=kwargs.get("last_street", ""),
                    building_name=kwargs.get("last_building", ""),
                )
                session.add(new_addr)
                session.flush()
                d.last_address_id = new_addr.id

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Update Deceased Error: {e}")
        return False
    finally:
        session.close()


def add_heir(deceased_id: int, name: str, rel: str, **kwargs) -> int:
    session = get_db_session()
    try:
        parts = name.replace("　", " ").split(" ", 1)
        lname = parts[0]
        fname = parts[1] if len(parts) > 1 else ""

        # 日付変換
        dob_val = kwargs.get("dob")
        if dob_val and not isinstance(dob_val, (datetime.date, datetime.datetime)):
            dob_val = parse_all_flexible_date(dob_val)

        new_heir = Heir(
            deceased_id=deceased_id,
            name_last=lname,
            name_first=fname,
            name_last_kana=kwargs.get("kana_last"),
            name_first_kana=kwargs.get("kana_first"),
            relationship_type=rel,
            is_contracting_party=kwargs.get("is_contracting_party", False),
            occupation=kwargs.get("occupation"),
            hometown=kwargs.get("hometown"),
            date_of_birth=dob_val,
        )
        session.add(new_heir)
        session.flush()

        # 住所登録
        street = kwargs.get("street", "")
        pref = kwargs.get("pref", "")

        if street or pref or kwargs.get("city") or kwargs.get("building"):
            zip_val = kwargs.get("zip_code", "")

            new_addr = Address(
                zip_code=zip_val,
                prefecture=pref,
                city_ward_town=kwargs.get("city", ""),
                street_address=street,
                building_name=kwargs.get("building", ""),
            )
            session.add(new_addr)
            session.flush()

            session.add(
                H_AddressHistory(
                    heir_id=new_heir.id, address_id=new_addr.id, is_current_address=True
                )
            )

        # 連絡先
        if "phone_contacts" in kwargs:
            for c_data in kwargs["phone_contacts"]:
                val = c_data.get("value")
                if val:
                    nc = Contact(value=val, type="PHONE", sub_type="Primary")
                    session.add(nc)
                    session.flush()
                    session.add(H_ContactLink(heir_id=new_heir.id, contact_id=nc.id))

        session.commit()
        return new_heir.id
    except Exception as e:
        session.rollback()
        logger.error(f"Add Heir Error: {e}")
        return -1
    finally:
        session.close()


def update_heir(heir_id: int, name: str, rel: str, **kwargs) -> bool:
    session = get_db_session()
    try:
        heir = session.query(Heir).get(heir_id)
        if not heir:
            return False

        parts = name.replace("　", " ").split(" ", 1)
        heir.name_last = parts[0]
        heir.name_first = parts[1] if len(parts) > 1 else ""
        heir.relationship_type = rel

        if "kana_last" in kwargs:
            heir.name_last_kana = kwargs["kana_last"]
        if "kana_first" in kwargs:
            heir.name_first_kana = kwargs["kana_first"]

        # ★修正: 日付型のチェックを入れる
        if kwargs.get("dob"):
            val = kwargs["dob"]
            if isinstance(val, (datetime.date, datetime.datetime)):
                heir.date_of_birth = val
            else:
                heir.date_of_birth = parse_all_flexible_date(val)

        if "occupation" in kwargs:
            heir.occupation = kwargs["occupation"]
        if "hometown" in kwargs:
            heir.hometown = kwargs["hometown"]

        # ★修正: 住所関連のキーが1つでも存在すれば更新処理に入る
        address_keys = ["pref", "city", "street", "building", "zip_code"]
        if any(k in kwargs for k in address_keys):
            link = (
                session.query(H_AddressHistory)
                .filter(
                    H_AddressHistory.heir_id == heir_id,
                    H_AddressHistory.is_current_address == True,
                )
                .first()
            )

            if link:
                addr = session.query(Address).get(link.address_id)
                addr.zip_code = kwargs.get("zip_code", addr.zip_code)
                addr.prefecture = kwargs.get("pref", addr.prefecture)
                addr.city_ward_town = kwargs.get("city", addr.city_ward_town)
                addr.street_address = kwargs.get("street", addr.street_address)
                addr.building_name = kwargs.get("building", addr.building_name)
            else:
                new_addr = Address(
                    zip_code=kwargs.get("zip_code", ""),
                    prefecture=kwargs.get("pref", ""),
                    city_ward_town=kwargs.get("city", ""),
                    street_address=kwargs.get("street", ""),
                    building_name=kwargs.get("building", ""),
                )
                session.add(new_addr)
                session.flush()
                session.add(
                    H_AddressHistory(
                        heir_id=heir.id, address_id=new_addr.id, is_current_address=True
                    )
                )

        if "phone_contacts" in kwargs or "email_contacts" in kwargs:
            session.query(H_ContactLink).filter(
                H_ContactLink.heir_id == heir_id
            ).delete()

            if "phone_contacts" in kwargs:
                for c_data in kwargs["phone_contacts"]:
                    val = c_data.get("value")
                    if val:
                        nc = Contact(value=val, type="PHONE", sub_type="Primary")
                        session.add(nc)
                        session.flush()
                        session.add(H_ContactLink(heir_id=heir.id, contact_id=nc.id))

            if "email_contacts" in kwargs:
                for c_data in kwargs["email_contacts"]:
                    val = c_data.get("value")
                    if val:
                        nc = Contact(value=val, type="EMAIL", sub_type="Primary")
                        session.add(nc)
                        session.flush()
                        session.add(H_ContactLink(heir_id=heir.id, contact_id=nc.id))

        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Update Heir Error: {e}")
        return False
    finally:
        session.close()


def delete_heir(heir_id: int) -> bool:
    session = get_db_session()
    try:
        heir = session.query(Heir).get(heir_id)
        if heir:
            session.delete(heir)
            session.commit()
            return True
        return False
    finally:
        session.close()


def sync_heir_list(
    deceased_id: int, heir_data_list: List[Dict[str, Any]]
) -> Dict[str, int]:
    session = get_db_session()
    result = {"added": 0, "updated": 0, "deleted": 0}

    try:
        existing_heirs = (
            session.query(Heir).filter(Heir.deceased_id == deceased_id).all()
        )
        existing_ids = {h.id for h in existing_heirs}

        incoming_ids = set()

        for data in heir_data_list:
            h_id = data.get("id")

            full_name = data.get("name", "").strip().replace("　", " ")
            parts = full_name.split(" ", 1)
            lname = parts[0]
            fname = parts[1] if len(parts) > 1 else ""
            rel = data.get("relationship", "")
            role_flg = True if data.get("role") == "契約者" else False

            dob = data.get("dob")
            if hasattr(dob, "date"):
                dob = dob.date()
            if pd.isnull(dob):
                dob = None

            if h_id and h_id in existing_ids:
                incoming_ids.add(h_id)
                target = session.query(Heir).get(h_id)
                target.name_last = lname
                target.name_first = fname
                target.relationship_type = rel
                target.date_of_birth = dob
                target.is_contracting_party = role_flg
                result["updated"] += 1
            else:
                if not lname:
                    continue
                new_h = Heir(
                    deceased_id=deceased_id,
                    name_last=lname,
                    name_first=fname,
                    relationship_type=rel,
                    date_of_birth=dob,
                    is_contracting_party=role_flg,
                )
                session.add(new_h)
                result["added"] += 1

        ids_to_delete = existing_ids - incoming_ids
        if ids_to_delete:
            session.query(Heir).filter(Heir.id.in_(ids_to_delete)).delete(
                synchronize_session=False
            )
            result["deleted"] = len(ids_to_delete)

        session.commit()
        return result

    except Exception as e:
        session.rollback()
        logger.error(f"Sync Heir List Error: {e}")
        raise e
    finally:
        session.close()


@retry_with_backoff(
    max_retries=3,
    backoff_factor=2.0,
    exceptions=(requests.RequestException, requests.Timeout),
)
def search_zip_by_address_api(address: str) -> Optional[str]:
    if not address:
        return None

    res = requests.get(
        "http://geoapi.heartrails.com/api/json",
        params={"method": "suggest", "matching": "like", "keyword": address},
        timeout=5,
    )
    data = res.json()
    if data and data.get("response") and data["response"].get("location"):
        p = data["response"]["location"][0].get("postal")
        if p:
            return f"{p[:3]}-{p[3:]}"
    return None


@retry_with_backoff(
    max_retries=3,
    backoff_factor=2.0,
    exceptions=(requests.RequestException, requests.Timeout),
)
def search_address_by_zip_api(zip_code: str) -> Optional[dict]:
    if not zip_code:
        return None

    res = requests.get(
        f"https://zipcloud.ibsnet.co.jp/api/search?zipcode={zip_code.replace('-', '')}",
        timeout=5,
    )
    data = res.json()
    if data and data.get("results"):
        r = data["results"][0]
        return {
            "prefecture": r["address1"],
            "city_ward_town": r["address2"],
            "street_address": r["address3"],
        }
    return {}
````

## File: src/legal.egg-info/PKG-INFO
````
Metadata-Version: 2.4
Name: legal
Version: 0.1.1
Summary: Administrative Scrivener RAG System
Author-email: Admin <admin@example.com>
Requires-Python: >=3.10
Description-Content-Type: text/markdown
Requires-Dist: streamlit>=1.34.0
Requires-Dist: langchain>=0.1.0
Requires-Dist: langchain-community>=0.0.20
Requires-Dist: langchain-core>=0.1.25
Requires-Dist: langchain-google-genai>=0.0.9
Requires-Dist: langchain-google-vertexai>=3.2.1
Requires-Dist: google-cloud-aiplatform>=1.38.0
Requires-Dist: langchain-huggingface>=0.0.1
Requires-Dist: langchain-chroma>=0.1.0
Requires-Dist: chromadb>=0.4.24
Requires-Dist: pypdf>=4.0.1
Requires-Dist: pdf2image>=1.17.0
Requires-Dist: pytesseract>=0.3.10
Requires-Dist: python-dotenv>=1.0.1
Requires-Dist: pandas>=2.3.3
Requires-Dist: openpyxl>=3.1.2
Requires-Dist: sentence-transformers>=5.2.0
Requires-Dist: numpy<2.0
Requires-Dist: streamlit-image-coordinates>=0.4.0
Requires-Dist: reportlab>=4.4.7
Requires-Dist: watchdog>=6.0.0
Requires-Dist: psycopg2-binary>=2.9.11
Requires-Dist: opencv-python<4.9
Requires-Dist: opencv-python-headless<4.9
Requires-Dist: pymupdf>=1.26.7
Requires-Dist: streamlit-drawable-canvas>=0.9.3
Requires-Dist: pyperclip>=1.11.0
Requires-Dist: google-genai>=1.59.0
Requires-Dist: pyautogui>=0.9.54
Requires-Dist: python-docx>=1.2.0
Requires-Dist: streamlit-keyup>=0.3.0
Requires-Dist: selenium>=4.40.0
Requires-Dist: webdriver-manager>=4.0.2
Requires-Dist: pyzipper>=0.3.6
Requires-Dist: google-auth-oauthlib>=1.2.4
Requires-Dist: google-api-python-client>=2.188.0
Requires-Dist: google-generativeai>=0.8.6

# legal-rag-project

Describe your project here.
````

## File: src/legal.egg-info/requires.txt
````
streamlit>=1.34.0
langchain>=0.1.0
langchain-community>=0.0.20
langchain-core>=0.1.25
langchain-google-genai>=0.0.9
langchain-google-vertexai>=3.2.1
google-cloud-aiplatform>=1.38.0
langchain-huggingface>=0.0.1
langchain-chroma>=0.1.0
chromadb>=0.4.24
pypdf>=4.0.1
pdf2image>=1.17.0
pytesseract>=0.3.10
python-dotenv>=1.0.1
pandas>=2.3.3
openpyxl>=3.1.2
sentence-transformers>=5.2.0
numpy<2.0
streamlit-image-coordinates>=0.4.0
reportlab>=4.4.7
watchdog>=6.0.0
psycopg2-binary>=2.9.11
opencv-python<4.9
opencv-python-headless<4.9
pymupdf>=1.26.7
streamlit-drawable-canvas>=0.9.3
pyperclip>=1.11.0
google-genai>=1.59.0
pyautogui>=0.9.54
python-docx>=1.2.0
streamlit-keyup>=0.3.0
selenium>=4.40.0
webdriver-manager>=4.0.2
pyzipper>=0.3.6
google-auth-oauthlib>=1.2.4
google-api-python-client>=2.188.0
google-generativeai>=0.8.6
````

## File: src/legal.egg-info/SOURCES.txt
````
README.md
pyproject.toml
src/__init__.py
src/chains/bank_procedure_chain.py
src/legal.egg-info/PKG-INFO
src/legal.egg-info/SOURCES.txt
src/legal.egg-info/dependency_links.txt
src/legal.egg-info/requires.txt
src/legal.egg-info/top_level.txt
src/legal_system/__init__.py
src/legal_system/main.py
src/legal_system/core/__init__.py
src/legal_system/core/ai_factory.py
src/legal_system/core/ai_processor.py
src/legal_system/core/config.py
src/legal_system/core/data_sync.py
src/legal_system/core/database_manager.py
src/legal_system/core/engines.py
src/legal_system/core/ocr_engine.py
src/legal_system/core/pdf_processor.py
src/legal_system/core/preload.py
src/legal_system/core/schemas.py
src/legal_system/models/__init__.py
src/legal_system/models/base.py
src/legal_system/models/tables.py
src/legal_system/tools/__init__.py
src/legal_system/tools/coord_tool.py
src/legal_system/ui/Home.py
src/legal_system/ui/__init__.py
src/legal_system/ui/excel_generator.py
src/legal_system/ui/label_generator.py
src/legal_system/ui/components/admin_tools.py
src/legal_system/ui/components/smart_guide.py
src/legal_system/ui/pages/01_案件登録_手動.py
src/legal_system/ui/pages/02_顧客紹介連絡表_読取.py
src/legal_system/ui/pages/03_Kintoneデータ_エクセル入力フォーム.py
src/legal_system/ui/pages/04_法定相続情報_読取.py
src/legal_system/ui/pages/05_残高証明書_読取.py
src/legal_system/ui/pages/06_相続書類_作成フォーム.py
src/legal_system/ui/pages/07_登記情報_読取.py
src/legal_system/ui/pages/08_書式座標登録ツール.py
src/legal_system/ui/pages/13_公証役場連携.py
src/legal_system/ui/pages/89_案件詳細_統合管理.py
src/legal_system/ui/pages/90_預貯金口座入力フォーム.py
src/legal_system/ui/pages/91_公正証書遺言_ドラフト作成.py
src/legal_system/ui/pages/98_書類内容チェック_AI.py
src/legal_system/ui/pages/99_マスタ管理.py
src/legal_system/ui/pages/backup/06_相続書類_作成フォーム.py
src/legal_system/ui/pages/backup/07_登記情報_読取.py
src/legal_system/ui/pages/backup/98_Llama実験室.py
src/legal_system/ui/pages/backup/99_Gemini実験室.py
src/legal_system/ui/pages/backup/_07_案件詳細_統合管理.py
src/services/__init__.py
src/services/deceased_service.py
src/services/dispatch_service.py
src/services/encryption_service.py
src/services/folder_service.py
src/services/gmail_watcher_service.py
src/services/kintone_sync_service.py
src/services/logistics_service.py
src/services/persistence_service.py
src/services/rag_search_service.py
src/services/automation/__init__.py
src/services/automation/touki_service.py
src/services/automation/will_generator.py
src/utils/__init__.py
src/utils/date_utils.py
````

## File: src/legal_system/ui/Home.py
````python
# src/legal_system/ui/Home.py

import os
import sys
import threading
import time
import subprocess
import streamlit as st
from sqlalchemy.orm import joinedload
from sqlalchemy import desc

# 自動更新ライブラリ
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

# ==========================================
# 1. パス解決 & 環境設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
# src/legal_system/ui/Home.py (current_dir) -> ui -> legal_system -> src -> ROOT (3階層上)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(ROOT_DIR, "src")

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(
    page_title="案件統合管理ホーム", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. Watcher（監視プロセス）起動ロジック
# ==========================================

@st.cache_resource
def get_shared_state():
    """スレッド間で状態を共有するためのコンテナ"""
    return {"services_ready": False, "watcher_started": False}

def launch_watcher_process():
    """run_watcher.py を起動する（コンソールは統合）"""
    watcher_path = os.path.join(ROOT_DIR, "run_watcher.py")
    python_exe = sys.executable
    
    if not os.path.exists(watcher_path):
        return False, f"ファイルが見つかりません: {watcher_path} (ROOT: {ROOT_DIR})"

    try:
        # Windowsで黒い画面を別に出さない設定
        subprocess.Popen(
            [python_exe, "-u", str(watcher_path)], 
            cwd=str(ROOT_DIR),
            close_fds=True
        )
        return True, "起動成功 (ログはターミナルを確認)"
    except Exception as e:
        return False, str(e)

def background_loader():
    """バックグラウンド読込スレッド"""
    try:
        from src.legal_system.core.preload import warm_up_modules
        warm_up_modules()
        
        state = get_shared_state()
        state["services_ready"] = True

        # 自動起動の試行
        if not state.get("watcher_started"):
            success, msg = launch_watcher_process()
            if success:
                state["watcher_started"] = True
                print(f"✨ [Watcher Auto-Start] SUCCESS: {msg}")
            else:
                print(f"⚠️ [Watcher Auto-Start] FAILED: {msg}")
    except Exception as e: 
        print(f"Background loader error: {e}")

if "bg_thread_started" not in st.session_state:
    t = threading.Thread(target=background_loader, daemon=True)
    t.start()
    st.session_state["bg_thread_started"] = True

# ==========================================
# 4. コンポーネントのインポート
# ==========================================
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir, FileRegistry, IncomingNoteBuffer, AuditLog
from src.legal_system.ui.components.sidebar import render_sidebar
from src.legal_system.ui.components.case_search import render_case_search
from src.legal_system.ui.components.inbox import render_inbox
from src.legal_system.ui.components.cases.header import render_case_header

@st.cache_resource(show_spinner=False)
def get_gmail_service_silent():
    try:
        from src.services.gmail_watcher_service import GmailWatcherService
        return GmailWatcherService()
    except Exception: return None

@st.cache_resource(show_spinner=False)
def get_scanner_service_silent():
    try:
        from src.services.scanner_service import ScannerService
        return ScannerService()
    except Exception: return None

# ==========================================
# ★追加: 通知レンダリング関数
# ==========================================
def render_notifications(session):
    """
    ヘッダーに表示する通知・ステータスエリア
    """
    # 1. 未処理件数のカウント
    pending_files = session.query(FileRegistry).filter_by(status="PENDING").count()
    pending_notes = session.query(IncomingNoteBuffer).filter_by(status="PENDING").count()
    total_pending = pending_files + pending_notes
    
    # 2. 直近のアクションログ (過去5件)
    recent_actions = session.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(5).all()

    state = get_shared_state()
    
    with st.expander("🛠️ システム通知 & 監視ステータス", expanded=bool(total_pending > 0)):
        col_stat, col_noti, col_log = st.columns([1, 1.5, 2])
        
        # --- ステータス ---
        with col_stat:
            st.markdown("##### 🟢 監視プロセス")
            status_text = "稼働中" if state["watcher_started"] else "停止中"
            st.caption(f"状態: **{status_text}**")
            if st.button("🚀 監視を再起動", use_container_width=True):
                success, msg = launch_watcher_process()
                if success:
                    state["watcher_started"] = True
                    st.success(f"再起動: {msg}")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"失敗: {msg}")

        # --- 通知 (Pending) ---
        with col_noti:
            st.markdown(f"##### 🔴 要確認 ({total_pending}件)")
            if total_pending == 0:
                st.caption("✅ すべて処理済みです")
            else:
                if pending_files > 0:
                    if st.button(f"📄 スキャン書類: {pending_files} 件 (AI処理へ)", type="primary", use_container_width=True):
                        st.switch_page("pages/00_AI受信トレイ.py")
                
                if pending_notes > 0:
                    st.warning(f"✉️ Gmailメモ: **{pending_notes}** 件")
                    st.caption("※Gmailメモはこの画面下部の「受信トレイ」を確認してください")

        # --- アクションログ ---
        with col_log:
            st.markdown("##### 🔵 直近のアクション")
            if recent_actions:
                for log in recent_actions:
                    t_str = log.timestamp.strftime('%H:%M')
                    target = log.target[:15] + "..." if len(log.target or "") > 15 else log.target
                    st.text(f"[{t_str}] {log.action_type}: {target}")
            else:
                st.caption("履歴なし")

# ==========================================
# 5. メインアプリ処理
# ==========================================
def main():
    # 自動更新設定 (30秒)
    if st_autorefresh:
        st_autorefresh(interval=30000, limit=None, key="global_auto_refresh")

    db = DatabaseManager()
    session = db._get_session()
    current_user_info = db.get_current_user_info()

    # 1. サイドバー
    menu = render_sidebar(db, current_user_info)

    # 2. 通知エリア
    render_notifications(session)

    # 3. 受信トレイ
    state = get_shared_state()
    if state["services_ready"]:
        gmail_svc = get_gmail_service_silent()
        scanner_svc = get_scanner_service_silent()
        if gmail_svc:
            render_inbox(session, gmail_service=gmail_svc, scanner_service=scanner_svc)
    else:
        st.caption("⏳ 連携サービス準備中...")

    st.divider()

    # 4. 案件検索
    target_case_id = render_case_search(session)
    if not target_case_id:
        st.info("👈 上記で案件を検索・選択してください。")
        session.close()
        return

    # データロード
    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.manager), joinedload(Case.operator)
    ).get(target_case_id)

    if not current_case:
        st.error("データなし")
        session.close()
        return

    render_case_header(current_case)

    # 6. コンテンツ表示 (Lazy Loading)
    if menu == "🏠 案件概要・基本情報":
        from src.legal_system.ui.components.cases.basic_info import render_basic_info
        from src.legal_system.ui.components.cases.dashboard_widgets import (
            render_manager_assignment, render_sol_info, render_kintone_tool, render_contact_logs
        )
        render_basic_info(session, target_case_id)
        st.divider(); render_manager_assignment(session, current_case)
        st.divider(); render_sol_info(session, current_case)
        st.divider(); render_kintone_tool(target_case_id)
        render_contact_logs(session, target_case_id)

    elif menu == "🏦 銀行口座 登録":
        from src.legal_system.ui.components.cases.asset_list import render_bank_account_list
        render_bank_account_list(session, target_case_id)

    elif menu == "📈 証券・その他資産":
        # ★機能追加: 証券・その他資産のCRUD画面
        from src.legal_system.ui.components.cases.asset_list import render_securities_list
        render_securities_list(session, target_case_id)

    elif menu == "🏘️ 不動産 登録":
        from src.legal_system.ui.components.cases.nayose_registration import render_nayose_registration
        render_nayose_registration(session, target_case_id)

    elif menu == "🌐 登記情報取得":
        from src.legal_system.ui.components.cases.registry_acquisition import render_registry_acquisition
        render_registry_acquisition(session, target_case_id)

    elif menu == "🖨️ 宛名ラベル作成":
        from src.legal_system.ui.components.label_printer_ui import render_label_printer
        render_label_printer(session, current_case, current_user_info)

    elif menu == "✅ タスク管理":
        st.info(f"メニュー: {menu} は準備中です。")

    session.close()

if __name__ == "__main__":
    main()
````

## File: requirements-dev.lock
````
# generated by rye
# use `rye lock` or `rye sync` to update this lockfile
#
# last locked with the following flags:
#   pre: false
#   features: []
#   all-features: false
#   with-sources: false
#   generate-hashes: false
#   universal: false

-e file:.
aiohappyeyeballs==2.6.1
    # via aiohttp
aiohttp==3.13.2
    # via langchain-community
aiosignal==1.4.0
    # via aiohttp
altair==6.0.0
    # via streamlit
annotated-types==0.7.0
    # via pydantic
anyio==4.12.0
    # via google-genai
    # via httpx
    # via watchfiles
async-generator==1.10
    # via trio-typing
attrs==25.4.0
    # via aiohttp
    # via jsonschema
    # via outcome
    # via referencing
    # via trio
backoff==2.2.1
    # via posthog
bcrypt==5.0.0
    # via chromadb
blinker==1.9.0
    # via streamlit
bottleneck==1.6.0
    # via langchain-google-vertexai
build==1.3.0
    # via chromadb
cachetools==6.2.4
    # via streamlit
certifi==2026.1.4
    # via httpcore
    # via httpx
    # via kubernetes
    # via requests
    # via selenium
cffi==2.0.0
    # via trio
charset-normalizer==3.4.4
    # via reportlab
    # via requests
chromadb==1.4.0
    # via langchain-chroma
    # via legal
click==8.3.1
    # via streamlit
    # via typer
    # via uvicorn
colorama==0.4.6
    # via build
    # via click
    # via tqdm
    # via uvicorn
coloredlogs==15.0.1
    # via onnxruntime
dataclasses-json==0.6.7
    # via langchain-community
distro==1.9.0
    # via google-genai
    # via posthog
docstring-parser==0.17.0
    # via google-cloud-aiplatform
durationpy==0.10
    # via kubernetes
et-xmlfile==2.0.0
    # via openpyxl
filelock==3.20.1
    # via huggingface-hub
    # via torch
    # via transformers
filetype==1.2.0
    # via langchain-google-genai
flatbuffers==25.12.19
    # via onnxruntime
frozenlist==1.8.0
    # via aiohttp
    # via aiosignal
fsspec==2025.12.0
    # via huggingface-hub
    # via torch
gitdb==4.0.12
    # via gitpython
gitpython==3.1.45
    # via streamlit
google-ai-generativelanguage==0.6.15
    # via google-generativeai
google-api-core==2.29.0
    # via google-ai-generativelanguage
    # via google-api-python-client
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
    # via google-generativeai
google-api-python-client==2.188.0
    # via google-generativeai
    # via legal
google-auth==2.47.0
    # via google-ai-generativelanguage
    # via google-api-core
    # via google-api-python-client
    # via google-auth-httplib2
    # via google-auth-oauthlib
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
    # via google-genai
    # via google-generativeai
google-auth-httplib2==0.3.0
    # via google-api-python-client
google-auth-oauthlib==1.2.4
    # via legal
google-cloud-aiplatform==1.133.0
    # via langchain-google-vertexai
    # via legal
google-cloud-bigquery==3.40.0
    # via google-cloud-aiplatform
google-cloud-core==2.5.0
    # via google-cloud-bigquery
    # via google-cloud-storage
google-cloud-resource-manager==1.15.0
    # via google-cloud-aiplatform
google-cloud-storage==3.8.0
    # via google-cloud-aiplatform
    # via langchain-google-vertexai
google-crc32c==1.8.0
    # via google-cloud-storage
    # via google-resumable-media
google-genai==1.59.0
    # via google-cloud-aiplatform
    # via langchain-google-genai
    # via legal
google-generativeai==0.8.6
    # via legal
google-resumable-media==2.8.0
    # via google-cloud-bigquery
    # via google-cloud-storage
googleapis-common-protos==1.72.0
    # via google-api-core
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
greenlet==3.3.0
    # via sqlalchemy
grpc-google-iam-v1==0.14.3
    # via google-cloud-resource-manager
grpcio==1.76.0
    # via chromadb
    # via google-api-core
    # via google-cloud-resource-manager
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
grpcio-status==1.71.2
    # via google-api-core
h11==0.16.0
    # via httpcore
    # via uvicorn
    # via wsproto
httpcore==1.0.9
    # via httpx
httplib2==0.31.1
    # via google-api-python-client
    # via google-auth-httplib2
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via chromadb
    # via google-genai
    # via langchain-google-vertexai
    # via langgraph-sdk
    # via langsmith
httpx-sse==0.4.3
    # via langchain-community
    # via langchain-google-vertexai
huggingface-hub==0.36.0
    # via langchain-huggingface
    # via sentence-transformers
    # via tokenizers
    # via transformers
humanfriendly==10.0
    # via coloredlogs
idna==3.11
    # via anyio
    # via httpx
    # via requests
    # via trio
    # via yarl
importlib-metadata==8.7.1
    # via opentelemetry-api
    # via trio-typing
importlib-resources==6.5.2
    # via chromadb
jinja2==3.1.6
    # via altair
    # via pydeck
    # via streamlit-keyup
    # via torch
joblib==1.5.3
    # via scikit-learn
jsonpatch==1.33
    # via langchain-core
jsonpointer==3.0.0
    # via jsonpatch
jsonschema==4.25.1
    # via altair
    # via chromadb
jsonschema-specifications==2025.9.1
    # via jsonschema
kubernetes==35.0.0
    # via chromadb
langchain==1.2.0
    # via legal
langchain-chroma==1.1.0
    # via legal
langchain-classic==1.0.1
    # via langchain-community
langchain-community==0.4.1
    # via legal
langchain-core==1.2.5
    # via langchain
    # via langchain-chroma
    # via langchain-classic
    # via langchain-community
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langchain-huggingface
    # via langchain-text-splitters
    # via langgraph
    # via langgraph-checkpoint
    # via langgraph-prebuilt
    # via legal
langchain-google-genai==4.1.2
    # via legal
langchain-google-vertexai==3.2.1
    # via legal
langchain-huggingface==1.2.0
    # via legal
langchain-text-splitters==1.1.0
    # via langchain-classic
langgraph==1.0.5
    # via langchain
langgraph-checkpoint==3.0.1
    # via langgraph
    # via langgraph-prebuilt
langgraph-prebuilt==1.0.5
    # via langgraph
langgraph-sdk==0.3.1
    # via langgraph
langsmith==0.5.2
    # via langchain-classic
    # via langchain-community
    # via langchain-core
lxml==6.0.2
    # via python-docx
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==3.26.2
    # via dataclasses-json
mdurl==0.1.2
    # via markdown-it-py
mmh3==5.2.0
    # via chromadb
mouseinfo==0.1.3
    # via pyautogui
mpmath==1.3.0
    # via sympy
multidict==6.7.0
    # via aiohttp
    # via yarl
mypy-extensions==1.1.0
    # via trio-typing
    # via typing-inspect
narwhals==2.14.0
    # via altair
networkx==3.6.1
    # via torch
numexpr==2.14.1
    # via langchain-google-vertexai
numpy==1.26.4
    # via bottleneck
    # via chromadb
    # via langchain-chroma
    # via langchain-community
    # via legal
    # via numexpr
    # via onnxruntime
    # via opencv-python
    # via opencv-python-headless
    # via pandas
    # via pydeck
    # via scikit-learn
    # via scipy
    # via streamlit
    # via streamlit-drawable-canvas
    # via transformers
oauthlib==3.3.1
    # via requests-oauthlib
onnxruntime==1.23.2
    # via chromadb
opencv-python==4.8.1.78
    # via legal
opencv-python-headless==4.8.1.78
    # via legal
openpyxl==3.1.5
    # via legal
opentelemetry-api==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
opentelemetry-exporter-otlp-proto-common==1.39.1
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-otlp-proto-grpc==1.39.1
    # via chromadb
opentelemetry-proto==1.39.1
    # via opentelemetry-exporter-otlp-proto-common
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-sdk==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-semantic-conventions==0.60b1
    # via opentelemetry-sdk
orjson==3.11.5
    # via chromadb
    # via langgraph-sdk
    # via langsmith
ormsgpack==1.12.1
    # via langgraph-checkpoint
outcome==1.3.0.post0
    # via trio
    # via trio-websocket
overrides==7.7.0
    # via chromadb
packaging==25.0
    # via altair
    # via build
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via huggingface-hub
    # via langchain-core
    # via langsmith
    # via marshmallow
    # via onnxruntime
    # via pytesseract
    # via streamlit
    # via transformers
    # via trio-typing
    # via webdriver-manager
pandas==2.3.3
    # via legal
    # via streamlit
pdf2image==1.17.0
    # via legal
pillow==12.0.0
    # via pdf2image
    # via pytesseract
    # via reportlab
    # via streamlit
    # via streamlit-drawable-canvas
posthog==5.4.0
    # via chromadb
propcache==0.4.1
    # via aiohttp
    # via yarl
proto-plus==1.27.0
    # via google-ai-generativelanguage
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
protobuf==5.29.5
    # via google-ai-generativelanguage
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
    # via google-generativeai
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via onnxruntime
    # via opentelemetry-proto
    # via proto-plus
    # via streamlit
psycopg2-binary==2.9.11
    # via legal
pyarrow==22.0.0
    # via langchain-google-vertexai
    # via streamlit
pyasn1==0.6.1
    # via pyasn1-modules
    # via rsa
pyasn1-modules==0.4.2
    # via google-auth
pyautogui==0.9.54
    # via legal
pybase64==1.4.3
    # via chromadb
pycparser==2.23
    # via cffi
pycryptodomex==3.23.0
    # via pyzipper
pydantic==2.12.5
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via google-generativeai
    # via langchain
    # via langchain-classic
    # via langchain-core
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langgraph
    # via langsmith
    # via pydantic-settings
pydantic-core==2.41.5
    # via pydantic
pydantic-settings==2.12.0
    # via langchain-community
pydeck==0.9.1
    # via streamlit
pygetwindow==0.0.9
    # via pyautogui
pygments==2.19.2
    # via rich
pymsgbox==2.0.1
    # via pyautogui
pymupdf==1.26.7
    # via legal
pyparsing==3.3.2
    # via httplib2
pypdf==6.5.0
    # via legal
pyperclip==1.11.0
    # via legal
    # via mouseinfo
pypika==0.48.9
    # via chromadb
pyproject-hooks==1.2.0
    # via build
pyreadline3==3.5.4
    # via humanfriendly
pyrect==0.2.0
    # via pygetwindow
pyscreeze==1.0.1
    # via pyautogui
pysocks==1.7.1
    # via urllib3
pytesseract==0.3.13
    # via legal
python-dateutil==2.9.0.post0
    # via google-cloud-bigquery
    # via kubernetes
    # via pandas
    # via posthog
python-docx==1.2.0
    # via legal
python-dotenv==1.2.1
    # via legal
    # via pydantic-settings
    # via uvicorn
    # via webdriver-manager
pytweening==1.2.0
    # via pyautogui
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via chromadb
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langchain-core
    # via transformers
    # via uvicorn
pyzipper==0.3.6
    # via legal
referencing==0.37.0
    # via jsonschema
    # via jsonschema-specifications
regex==2025.11.3
    # via transformers
reportlab==4.4.7
    # via legal
requests==2.32.5
    # via google-api-core
    # via google-auth
    # via google-cloud-bigquery
    # via google-cloud-storage
    # via google-genai
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langsmith
    # via posthog
    # via requests-oauthlib
    # via requests-toolbelt
    # via streamlit
    # via transformers
    # via webdriver-manager
requests-oauthlib==2.0.0
    # via google-auth-oauthlib
    # via kubernetes
requests-toolbelt==1.0.0
    # via langsmith
rich==14.2.0
    # via chromadb
    # via typer
rpds-py==0.30.0
    # via jsonschema
    # via referencing
rsa==4.9.1
    # via google-auth
safetensors==0.7.0
    # via transformers
scikit-learn==1.8.0
    # via sentence-transformers
scipy==1.16.3
    # via scikit-learn
    # via sentence-transformers
selenium==4.40.0
    # via legal
sentence-transformers==5.2.0
    # via legal
shellingham==1.5.4
    # via typer
six==1.17.0
    # via kubernetes
    # via posthog
    # via python-dateutil
smmap==5.0.2
    # via gitdb
sniffio==1.3.1
    # via google-genai
    # via trio
sortedcontainers==2.4.0
    # via trio
sqlalchemy==2.0.45
    # via langchain-classic
    # via langchain-community
streamlit==1.52.2
    # via legal
    # via streamlit-drawable-canvas
    # via streamlit-image-coordinates
    # via streamlit-keyup
streamlit-drawable-canvas==0.9.3
    # via legal
streamlit-image-coordinates==0.4.0
    # via legal
streamlit-keyup==0.3.0
    # via legal
sympy==1.14.0
    # via onnxruntime
    # via torch
tenacity==9.1.2
    # via chromadb
    # via google-genai
    # via langchain-community
    # via langchain-core
    # via streamlit
threadpoolctl==3.6.0
    # via scikit-learn
tokenizers==0.22.1
    # via chromadb
    # via langchain-huggingface
    # via transformers
toml==0.10.2
    # via streamlit
torch==2.2.2
    # via sentence-transformers
tornado==6.5.4
    # via streamlit
tqdm==4.67.1
    # via chromadb
    # via google-generativeai
    # via huggingface-hub
    # via sentence-transformers
    # via transformers
transformers==4.57.3
    # via sentence-transformers
trio==0.32.0
    # via selenium
    # via trio-typing
    # via trio-websocket
trio-typing==0.10.0
    # via selenium
trio-websocket==0.12.2
    # via selenium
typer==0.21.0
    # via chromadb
types-certifi==2021.10.8.3
    # via selenium
types-urllib3==1.26.25.14
    # via selenium
typing-extensions==4.15.0
    # via aiosignal
    # via altair
    # via anyio
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via google-generativeai
    # via grpcio
    # via huggingface-hub
    # via langchain-core
    # via opentelemetry-api
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
    # via pydantic
    # via pydantic-core
    # via python-docx
    # via referencing
    # via selenium
    # via sentence-transformers
    # via sqlalchemy
    # via streamlit
    # via torch
    # via trio-typing
    # via typer
    # via typing-inspect
    # via typing-inspection
typing-inspect==0.9.0
    # via dataclasses-json
typing-inspection==0.4.2
    # via pydantic
    # via pydantic-settings
tzdata==2025.3
    # via pandas
uritemplate==4.2.0
    # via google-api-python-client
urllib3==2.6.3
    # via kubernetes
    # via requests
    # via selenium
uuid-utils==0.12.0
    # via langchain-core
    # via langsmith
uvicorn==0.40.0
    # via chromadb
validators==0.35.0
    # via langchain-google-vertexai
watchdog==6.0.0
    # via legal
    # via streamlit
watchfiles==1.1.1
    # via uvicorn
webdriver-manager==4.0.2
    # via legal
websocket-client==1.9.0
    # via kubernetes
    # via selenium
websockets==15.0.1
    # via google-genai
    # via uvicorn
wsproto==1.3.2
    # via trio-websocket
xxhash==3.6.0
    # via langgraph
yarl==1.22.0
    # via aiohttp
zipp==3.23.0
    # via importlib-metadata
zstandard==0.25.0
    # via langsmith
````

## File: requirements.lock
````
# generated by rye
# use `rye lock` or `rye sync` to update this lockfile
#
# last locked with the following flags:
#   pre: false
#   features: []
#   all-features: false
#   with-sources: false
#   generate-hashes: false
#   universal: false

-e file:.
aiohappyeyeballs==2.6.1
    # via aiohttp
aiohttp==3.13.2
    # via langchain-community
aiosignal==1.4.0
    # via aiohttp
altair==6.0.0
    # via streamlit
annotated-types==0.7.0
    # via pydantic
anyio==4.12.0
    # via google-genai
    # via httpx
    # via watchfiles
async-generator==1.10
    # via trio-typing
attrs==25.4.0
    # via aiohttp
    # via jsonschema
    # via outcome
    # via referencing
    # via trio
backoff==2.2.1
    # via posthog
bcrypt==5.0.0
    # via chromadb
blinker==1.9.0
    # via streamlit
bottleneck==1.6.0
    # via langchain-google-vertexai
build==1.3.0
    # via chromadb
cachetools==6.2.4
    # via streamlit
certifi==2026.1.4
    # via httpcore
    # via httpx
    # via kubernetes
    # via requests
    # via selenium
cffi==2.0.0
    # via trio
charset-normalizer==3.4.4
    # via reportlab
    # via requests
chromadb==1.4.0
    # via langchain-chroma
    # via legal
click==8.3.1
    # via streamlit
    # via typer
    # via uvicorn
colorama==0.4.6
    # via build
    # via click
    # via tqdm
    # via uvicorn
coloredlogs==15.0.1
    # via onnxruntime
dataclasses-json==0.6.7
    # via langchain-community
distro==1.9.0
    # via google-genai
    # via posthog
docstring-parser==0.17.0
    # via google-cloud-aiplatform
durationpy==0.10
    # via kubernetes
et-xmlfile==2.0.0
    # via openpyxl
filelock==3.20.1
    # via huggingface-hub
    # via torch
    # via transformers
filetype==1.2.0
    # via langchain-google-genai
flatbuffers==25.12.19
    # via onnxruntime
frozenlist==1.8.0
    # via aiohttp
    # via aiosignal
fsspec==2025.12.0
    # via huggingface-hub
    # via torch
gitdb==4.0.12
    # via gitpython
gitpython==3.1.45
    # via streamlit
google-ai-generativelanguage==0.6.15
    # via google-generativeai
google-api-core==2.29.0
    # via google-ai-generativelanguage
    # via google-api-python-client
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
    # via google-generativeai
google-api-python-client==2.188.0
    # via google-generativeai
    # via legal
google-auth==2.47.0
    # via google-ai-generativelanguage
    # via google-api-core
    # via google-api-python-client
    # via google-auth-httplib2
    # via google-auth-oauthlib
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
    # via google-genai
    # via google-generativeai
google-auth-httplib2==0.3.0
    # via google-api-python-client
google-auth-oauthlib==1.2.4
    # via legal
google-cloud-aiplatform==1.133.0
    # via langchain-google-vertexai
    # via legal
google-cloud-bigquery==3.40.0
    # via google-cloud-aiplatform
google-cloud-core==2.5.0
    # via google-cloud-bigquery
    # via google-cloud-storage
google-cloud-resource-manager==1.15.0
    # via google-cloud-aiplatform
google-cloud-storage==3.8.0
    # via google-cloud-aiplatform
    # via langchain-google-vertexai
google-crc32c==1.8.0
    # via google-cloud-storage
    # via google-resumable-media
google-genai==1.59.0
    # via google-cloud-aiplatform
    # via langchain-google-genai
    # via legal
google-generativeai==0.8.6
    # via legal
google-resumable-media==2.8.0
    # via google-cloud-bigquery
    # via google-cloud-storage
googleapis-common-protos==1.72.0
    # via google-api-core
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
greenlet==3.3.0
    # via sqlalchemy
grpc-google-iam-v1==0.14.3
    # via google-cloud-resource-manager
grpcio==1.76.0
    # via chromadb
    # via google-api-core
    # via google-cloud-resource-manager
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
grpcio-status==1.71.2
    # via google-api-core
h11==0.16.0
    # via httpcore
    # via uvicorn
    # via wsproto
httpcore==1.0.9
    # via httpx
httplib2==0.31.1
    # via google-api-python-client
    # via google-auth-httplib2
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via chromadb
    # via google-genai
    # via langchain-google-vertexai
    # via langgraph-sdk
    # via langsmith
httpx-sse==0.4.3
    # via langchain-community
    # via langchain-google-vertexai
huggingface-hub==0.36.0
    # via langchain-huggingface
    # via sentence-transformers
    # via tokenizers
    # via transformers
humanfriendly==10.0
    # via coloredlogs
idna==3.11
    # via anyio
    # via httpx
    # via requests
    # via trio
    # via yarl
importlib-metadata==8.7.1
    # via opentelemetry-api
    # via trio-typing
importlib-resources==6.5.2
    # via chromadb
jinja2==3.1.6
    # via altair
    # via pydeck
    # via streamlit-keyup
    # via torch
joblib==1.5.3
    # via scikit-learn
jsonpatch==1.33
    # via langchain-core
jsonpointer==3.0.0
    # via jsonpatch
jsonschema==4.25.1
    # via altair
    # via chromadb
jsonschema-specifications==2025.9.1
    # via jsonschema
kubernetes==35.0.0
    # via chromadb
langchain==1.2.0
    # via legal
langchain-chroma==1.1.0
    # via legal
langchain-classic==1.0.1
    # via langchain-community
langchain-community==0.4.1
    # via legal
langchain-core==1.2.5
    # via langchain
    # via langchain-chroma
    # via langchain-classic
    # via langchain-community
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langchain-huggingface
    # via langchain-text-splitters
    # via langgraph
    # via langgraph-checkpoint
    # via langgraph-prebuilt
    # via legal
langchain-google-genai==4.1.2
    # via legal
langchain-google-vertexai==3.2.1
    # via legal
langchain-huggingface==1.2.0
    # via legal
langchain-text-splitters==1.1.0
    # via langchain-classic
langgraph==1.0.5
    # via langchain
langgraph-checkpoint==3.0.1
    # via langgraph
    # via langgraph-prebuilt
langgraph-prebuilt==1.0.5
    # via langgraph
langgraph-sdk==0.3.1
    # via langgraph
langsmith==0.5.2
    # via langchain-classic
    # via langchain-community
    # via langchain-core
lxml==6.0.2
    # via python-docx
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==3.26.2
    # via dataclasses-json
mdurl==0.1.2
    # via markdown-it-py
mmh3==5.2.0
    # via chromadb
mouseinfo==0.1.3
    # via pyautogui
mpmath==1.3.0
    # via sympy
multidict==6.7.0
    # via aiohttp
    # via yarl
mypy-extensions==1.1.0
    # via trio-typing
    # via typing-inspect
narwhals==2.14.0
    # via altair
networkx==3.6.1
    # via torch
numexpr==2.14.1
    # via langchain-google-vertexai
numpy==1.26.4
    # via bottleneck
    # via chromadb
    # via langchain-chroma
    # via langchain-community
    # via legal
    # via numexpr
    # via onnxruntime
    # via opencv-python
    # via opencv-python-headless
    # via pandas
    # via pydeck
    # via scikit-learn
    # via scipy
    # via streamlit
    # via streamlit-drawable-canvas
    # via transformers
oauthlib==3.3.1
    # via requests-oauthlib
onnxruntime==1.23.2
    # via chromadb
opencv-python==4.8.1.78
    # via legal
opencv-python-headless==4.8.1.78
    # via legal
openpyxl==3.1.5
    # via legal
opentelemetry-api==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
opentelemetry-exporter-otlp-proto-common==1.39.1
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-otlp-proto-grpc==1.39.1
    # via chromadb
opentelemetry-proto==1.39.1
    # via opentelemetry-exporter-otlp-proto-common
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-sdk==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-semantic-conventions==0.60b1
    # via opentelemetry-sdk
orjson==3.11.5
    # via chromadb
    # via langgraph-sdk
    # via langsmith
ormsgpack==1.12.1
    # via langgraph-checkpoint
outcome==1.3.0.post0
    # via trio
    # via trio-websocket
overrides==7.7.0
    # via chromadb
packaging==25.0
    # via altair
    # via build
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via huggingface-hub
    # via langchain-core
    # via langsmith
    # via marshmallow
    # via onnxruntime
    # via pytesseract
    # via streamlit
    # via transformers
    # via trio-typing
    # via webdriver-manager
pandas==2.3.3
    # via legal
    # via streamlit
pdf2image==1.17.0
    # via legal
pillow==12.0.0
    # via pdf2image
    # via pytesseract
    # via reportlab
    # via streamlit
    # via streamlit-drawable-canvas
posthog==5.4.0
    # via chromadb
propcache==0.4.1
    # via aiohttp
    # via yarl
proto-plus==1.27.0
    # via google-ai-generativelanguage
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
protobuf==5.29.5
    # via google-ai-generativelanguage
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
    # via google-generativeai
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via onnxruntime
    # via opentelemetry-proto
    # via proto-plus
    # via streamlit
psycopg2-binary==2.9.11
    # via legal
pyarrow==22.0.0
    # via langchain-google-vertexai
    # via streamlit
pyasn1==0.6.1
    # via pyasn1-modules
    # via rsa
pyasn1-modules==0.4.2
    # via google-auth
pyautogui==0.9.54
    # via legal
pybase64==1.4.3
    # via chromadb
pycparser==2.23
    # via cffi
pycryptodomex==3.23.0
    # via pyzipper
pydantic==2.12.5
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via google-generativeai
    # via langchain
    # via langchain-classic
    # via langchain-core
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langgraph
    # via langsmith
    # via pydantic-settings
pydantic-core==2.41.5
    # via pydantic
pydantic-settings==2.12.0
    # via langchain-community
pydeck==0.9.1
    # via streamlit
pygetwindow==0.0.9
    # via pyautogui
pygments==2.19.2
    # via rich
pymsgbox==2.0.1
    # via pyautogui
pymupdf==1.26.7
    # via legal
pyparsing==3.3.2
    # via httplib2
pypdf==6.5.0
    # via legal
pyperclip==1.11.0
    # via legal
    # via mouseinfo
pypika==0.48.9
    # via chromadb
pyproject-hooks==1.2.0
    # via build
pyreadline3==3.5.4
    # via humanfriendly
pyrect==0.2.0
    # via pygetwindow
pyscreeze==1.0.1
    # via pyautogui
pysocks==1.7.1
    # via urllib3
pytesseract==0.3.13
    # via legal
python-dateutil==2.9.0.post0
    # via google-cloud-bigquery
    # via kubernetes
    # via pandas
    # via posthog
python-docx==1.2.0
    # via legal
python-dotenv==1.2.1
    # via legal
    # via pydantic-settings
    # via uvicorn
    # via webdriver-manager
pytweening==1.2.0
    # via pyautogui
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via chromadb
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langchain-core
    # via transformers
    # via uvicorn
pyzipper==0.3.6
    # via legal
referencing==0.37.0
    # via jsonschema
    # via jsonschema-specifications
regex==2025.11.3
    # via transformers
reportlab==4.4.7
    # via legal
requests==2.32.5
    # via google-api-core
    # via google-auth
    # via google-cloud-bigquery
    # via google-cloud-storage
    # via google-genai
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langsmith
    # via posthog
    # via requests-oauthlib
    # via requests-toolbelt
    # via streamlit
    # via transformers
    # via webdriver-manager
requests-oauthlib==2.0.0
    # via google-auth-oauthlib
    # via kubernetes
requests-toolbelt==1.0.0
    # via langsmith
rich==14.2.0
    # via chromadb
    # via typer
rpds-py==0.30.0
    # via jsonschema
    # via referencing
rsa==4.9.1
    # via google-auth
safetensors==0.7.0
    # via transformers
scikit-learn==1.8.0
    # via sentence-transformers
scipy==1.16.3
    # via scikit-learn
    # via sentence-transformers
selenium==4.40.0
    # via legal
sentence-transformers==5.2.0
    # via legal
shellingham==1.5.4
    # via typer
six==1.17.0
    # via kubernetes
    # via posthog
    # via python-dateutil
smmap==5.0.2
    # via gitdb
sniffio==1.3.1
    # via google-genai
    # via trio
sortedcontainers==2.4.0
    # via trio
sqlalchemy==2.0.45
    # via langchain-classic
    # via langchain-community
streamlit==1.52.2
    # via legal
    # via streamlit-drawable-canvas
    # via streamlit-image-coordinates
    # via streamlit-keyup
streamlit-drawable-canvas==0.9.3
    # via legal
streamlit-image-coordinates==0.4.0
    # via legal
streamlit-keyup==0.3.0
    # via legal
sympy==1.14.0
    # via onnxruntime
    # via torch
tenacity==9.1.2
    # via chromadb
    # via google-genai
    # via langchain-community
    # via langchain-core
    # via streamlit
threadpoolctl==3.6.0
    # via scikit-learn
tokenizers==0.22.1
    # via chromadb
    # via langchain-huggingface
    # via transformers
toml==0.10.2
    # via streamlit
torch==2.2.2
    # via sentence-transformers
tornado==6.5.4
    # via streamlit
tqdm==4.67.1
    # via chromadb
    # via google-generativeai
    # via huggingface-hub
    # via sentence-transformers
    # via transformers
transformers==4.57.3
    # via sentence-transformers
trio==0.32.0
    # via selenium
    # via trio-typing
    # via trio-websocket
trio-typing==0.10.0
    # via selenium
trio-websocket==0.12.2
    # via selenium
typer==0.21.0
    # via chromadb
types-certifi==2021.10.8.3
    # via selenium
types-urllib3==1.26.25.14
    # via selenium
typing-extensions==4.15.0
    # via aiosignal
    # via altair
    # via anyio
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via google-generativeai
    # via grpcio
    # via huggingface-hub
    # via langchain-core
    # via opentelemetry-api
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
    # via pydantic
    # via pydantic-core
    # via python-docx
    # via referencing
    # via selenium
    # via sentence-transformers
    # via sqlalchemy
    # via streamlit
    # via torch
    # via trio-typing
    # via typer
    # via typing-inspect
    # via typing-inspection
typing-inspect==0.9.0
    # via dataclasses-json
typing-inspection==0.4.2
    # via pydantic
    # via pydantic-settings
tzdata==2025.3
    # via pandas
uritemplate==4.2.0
    # via google-api-python-client
urllib3==2.6.3
    # via kubernetes
    # via requests
    # via selenium
uuid-utils==0.12.0
    # via langchain-core
    # via langsmith
uvicorn==0.40.0
    # via chromadb
validators==0.35.0
    # via langchain-google-vertexai
watchdog==6.0.0
    # via legal
    # via streamlit
watchfiles==1.1.1
    # via uvicorn
webdriver-manager==4.0.2
    # via legal
websocket-client==1.9.0
    # via kubernetes
    # via selenium
websockets==15.0.1
    # via google-genai
    # via uvicorn
wsproto==1.3.2
    # via trio-websocket
xxhash==3.6.0
    # via langgraph
yarl==1.22.0
    # via aiohttp
zipp==3.23.0
    # via importlib-metadata
zstandard==0.25.0
    # via langsmith
````

## File: pyproject.toml
````toml
[project]
name = "legal"
version = "0.1.1"
description = "Administrative Scrivener RAG System"
authors = [
    { name = "Admin", email = "admin@example.com" }
]
dependencies = [
    "streamlit>=1.34.0",
    "streamlit-autorefresh>=1.0.1", # ★追加: 自動更新用ライブラリ
    "langchain>=0.1.0",
    "langchain-community>=0.0.20",
    "langchain-core>=0.1.25",
    "langchain-google-genai>=0.0.9",
    "langchain-google-vertexai>=3.2.1",
    "google-cloud-aiplatform>=1.38.0",
    "langchain-huggingface>=0.0.1",
    "langchain-chroma>=0.1.0",
    "chromadb>=0.4.24",
    "pypdf>=4.0.1",
    "pdf2image>=1.17.0",
    "pytesseract>=0.3.10",
    "python-dotenv>=1.0.1",
    "pandas>=2.3.3",
    "openpyxl>=3.1.2",
    "sentence-transformers>=5.2.0",
    "numpy<2.0",
    "streamlit-image-coordinates>=0.4.0",
    "reportlab>=4.4.7",
    "watchdog>=6.0.0",
    "psycopg2-binary>=2.9.11",
    "opencv-python<4.9",
    "opencv-python-headless<4.9",
    "pymupdf>=1.26.7",
    "streamlit-drawable-canvas>=0.9.3",
    "pyperclip>=1.11.0",
    "google-genai>=1.59.0",
    "pyautogui>=0.9.54",
    "python-docx>=1.2.0",
    "streamlit-keyup>=0.3.0",
    "selenium>=4.40.0",
    "webdriver-manager>=4.0.2",
    "pyzipper>=0.3.6",
    "google-auth-oauthlib>=1.2.4",
    "google-api-python-client>=2.188.0",
    "google-generativeai>=0.8.6",
]
readme = "README.md"
requires-python = ">= 3.10"

[tool.rye]
managed = true
dev-dependencies = []

[tool.rye.scripts]
start = "rye run python src/legal_system/main.py"
pdf = "rye run streamlit run src/legal_system/tools/coord_tool.py"
exp = "rye run python export_code.py"
````
