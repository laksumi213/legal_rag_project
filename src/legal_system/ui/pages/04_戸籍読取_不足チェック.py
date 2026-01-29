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