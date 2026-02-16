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
    from legal_system.core.ai_processor import AgenticDocumentProcessor
    from legal_system.core.schemas import DocumentAnalysisResult
except ImportError:
    st.error("コアモジュール (src.legal_system.core) が見つかりません。")
    st.stop()

# DB保存サービス (既存機能の維持)
try:
    from services.persistence_service import (
        VerificationPersistenceService,
    )

    HAS_PERSISTENCE_SERVICE = True
except ImportError:
    HAS_PERSISTENCE_SERVICE = False

# Kintone連携サービス
from services.kintone_sync_service import get_kintone_data_as_dict

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
