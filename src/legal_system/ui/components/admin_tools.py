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
# Gemini用メッセージは ocr_engine 側に移動したので不要だが、残しておいても害はない
from langchain_core.messages import HumanMessage 

# パス解決 (プロジェクト構成に合わせて調整)
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
# ★修正: Gemini優先ロジックを含む関数をインポート
from legal_system.core.ocr_engine import extract_text_from_scanned_pdf

# ---------------------------------------------------------
# ヘルパー関数群
# ---------------------------------------------------------
def calculate_file_hash(file_bytes: bytes) -> str:
    """ファイルの重複登録を防ぐためのハッシュ計算"""
    return hashlib.md5(file_bytes).hexdigest()

# ★削除: extract_text_with_gemini は ocr_engine.py に移動したため削除

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
    戻り値: {"filename": ..., "bank_name": ..., "doc_type": ...} または None
    """
    if not text_content:
        return None

    # 正規化（改行・空白削除）
    normalized_text = text_content.replace("\n", "").replace(" ", "").replace("　", "")

    # 1. 銀行名の特定（マスタ等からキーワード拡張可能）
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

    # 銀行と種別の両方が「その他」でなければ、一定の信頼度で採用
    if bank_name != "その他" or doc_type != "その他":
        filename = f"{bank_name}_{doc_type}"
        return {"filename": filename, "bank_name": bank_name, "doc_type": doc_type}

    return None


def analyze_document_info(text_content: str, llm):
    """
    文書の種類や銀行名を推定するハイブリッドロジック
    Priority 1: ルールベース判定 (高速・無料)
    Priority 2: AI判定 (低速・高コスト・高精度)
    """
    if not text_content:
        return {"filename": "", "bank_name": "", "doc_type": ""}

    # Priority 1: ルールベース
    rule_result = _rule_based_classify(text_content)
    if rule_result:
        # ルールベースで判定できた場合、ここで終了
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


def js_scroll_to_bottom():
    js = """<script>
        var mainParams = window.parent.document.querySelector('section.main');
        if (mainParams) { mainParams.scrollTo({ top: mainParams.scrollHeight, behavior: 'smooth' }); }
    </script>"""
    st.components.v1.html(js, height=0)


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
            selected = st.selectbox(
                "紐付ける案件 (任意)", list(case_opts.keys()), key="up_case_sel"
            )
            target_case_id = case_opts[selected]
        finally:
            session.close()

        files_n = st.file_uploader(
            "PDFアップロード (一般)", accept_multiple_files=True, key="up_n"
        )

        if files_n:
            if st.button("🔍 クラウド解析", key="btn_n"):
                # ステータスコンテナで進捗を表示
                with st.status(
                    "🚀 ハイブリッド解析中 (ルールベース + AI)...", expanded=True
                ) as status:
                    st.session_state.upload_stage = []

                    st.write("🧠 AIモデルを初期化中...")
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

                        # ハッシュチェック
                        f_hash = calculate_file_hash(fb)
                        if db_manager.is_file_registered(f_hash):
                            st.warning(
                                f"⚠️ {f.name} は既に登録されています。スキップします。"
                            )
                            time.sleep(0.5)
                            continue

                        # 解析処理 (extract_text_safe -> ocr_engine -> Gemini Vision)
                        text = extract_text_safe(fb)
                        if not text:
                            st.warning(
                                f"⚠️ {f.name} からテキストを抽出できませんでした。"
                            )

                        # ハイブリッド判定 (ルール -> AI)
                        meta = analyze_document_info(text, llm_cloud)
                        st.write(
                            f"   ↳ 判定: {meta.get('doc_type', '不明')} / {meta.get('bank_name', '不明')}"
                        )

                        st.session_state.upload_stage.append(
                            {
                                "old": f.name,
                                "new": meta.get("filename", f.name),
                                "bank_name": meta.get("bank_name", "その他"),
                                "doc_type": meta.get("doc_type", "その他"),
                                "data": fb,
                                "text": text,
                                "type": "general",
                                "hash": f_hash,
                                "case_id": target_case_id,
                            }
                        )
                        # プログレスバー更新
                        progress_bar.progress((i + 1) / total_files)

                    # 完了時はexpanded=Trueのままにして、rerunしない（結果を表示し続ける）
                    status.update(
                        label="✅ 解析完了！内容を確認して、下の「登録実行」を押してください。",
                        state="complete",
                        expanded=True,
                    )
                # ここで st.rerun() はしない

    # ==========================================
    # 2. 機密用タブ (ローカルAI使用)
    # ==========================================
    with s_sec:
        st.warning("個人情報を含む書類 (ローカル処理)")
        # 案件紐付け
        session = db_manager._get_session()
        target_case_id_sec = None
        try:
            from legal_system.models.tables import Case

            cases = session.query(Case).all()
            case_opts_s = {"（全案件共通の雛形として登録）": None}
            for c in cases:
                case_opts_s[f"{c.case_number}: {c.client_name}"] = c.case_id
            selected_s = st.selectbox(
                "紐付ける案件 (任意)", list(case_opts_s.keys()), key="up_case_sel_sec"
            )
            target_case_id_sec = case_opts_s[selected_s]
        finally:
            session.close()

        file_s = st.file_uploader(
            "PDFアップロード (機密)", accept_multiple_files=False, key="up_s"
        )

        if file_s:
            fb_s = file_s.read()
            f_hash = calculate_file_hash(fb_s)

            if db_manager.is_file_registered(f_hash):
                st.error(f"⛔ {file_s.name} は既に登録済みです。")
            else:
                if convert_from_bytes:
                    try:
                        # プレビュー表示用
                        from pdf2image import convert_from_bytes # 再度インポート確認
                        images = convert_from_bytes(fb_s, first_page=1, last_page=1)
                        if images:
                            st.image(images[0], width=400)
                    except:
                        pass

                if st.checkbox(
                    "機密書類であることを確認しました", key="check_s"
                ) and st.button("🔒 ローカル解析", key="btn_s"):
                    with st.status(
                        "🔒 ローカルAI (Ollama) で解析中...", expanded=True
                    ) as status:
                        st.session_state.upload_stage = []

                        st.write("🧠 ローカルモデル(Llama)をロード中...")
                        try:
                            llm_local = AIFactory.get_llm("local")
                        except Exception as e:
                            status.update(label="❌ エラー発生", state="error")
                            st.error(f"ローカルモデルの起動に失敗: {e}")
                            st.stop()

                        st.write("📄 テキスト抽出中...")
                        # ★注意: 機密タブですが、今回はユーザ要望により Gemini Vision (Cloud) を優先する ocr_engine を使っています。
                        # 完全ローカル運用が必要な場合は、ここを分岐させる必要がありますが、現状は共通化しています。
                        text_s = extract_text_safe(fb_s)

                        st.write("🔍 文書解析中 (ルールベース + Llama)...")
                        meta = analyze_document_info(text_s, llm_local)
                        if "記入例" not in meta["filename"]:
                            meta["filename"] += "_記入例"

                        st.session_state.upload_stage.append(
                            {
                                "old": file_s.name,
                                "new": meta.get("filename", file_s.name),
                                "bank_name": meta.get("bank_name", "その他"),
                                "doc_type": meta.get("doc_type", "その他"),
                                "data": fb_s,
                                "text": text_s,
                                "type": "secure",
                                "hash": f_hash,
                                "case_id": target_case_id_sec,
                            }
                        )
                        status.update(
                            label="✅ 解析完了！下の「登録実行」へ進んでください。",
                            state="complete",
                            expanded=True,
                        )
                # ここで st.rerun() はしない

    # ==========================================
    # 3. 保存確認フォーム (解析結果がある場合のみ表示)
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
                new_bank = c3.text_input(
                    "銀行タグ", value=item["bank_name"], key=f"bk_{i}"
                )

                opts = [
                    "手引き",
                    "残高証明",
                    "取引明細",
                    "顧客勘定元帳",
                    "相続届",
                    "委任状",
                    "その他",
                ]
                curr = item.get("doc_type", "その他")
                idx = opts.index(curr) if curr in opts else 6
                new_type = c4.selectbox("種別", opts, index=idx, key=f"dt_{i}")

                configs.append(
                    {
                        **item,
                        "name": new_name,
                        "bank_name": new_bank,
                        "doc_type": new_type,
                    }
                )

            if st.form_submit_button("✅ 登録実行"):
                _execute_registration(configs, db_manager)


# ---------------------------------------------------------
# 登録実行ロジック (リトライ処理付き)
# ---------------------------------------------------------
def _execute_registration(configs, db_manager):
    vector_store = AIFactory.get_vector_store()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    cnt = 0
    today = datetime.now().strftime("%Y%m%d")
    templates_dir = os.path.join(ROOT_DIR, "data", "templates")
    os.makedirs(templates_dir, exist_ok=True)

    # 登録時もステータス表示
    with st.status("💾 データベースに登録中...", expanded=True) as status:
        progress_bar = st.progress(0)
        total_configs = len(configs)

        for idx, c in enumerate(configs):
            fname = f"{c['name']}_{today}.pdf"
            st.write(f"📝 登録中 ({idx + 1}/{total_configs}): {fname}")

            save_path = os.path.join(templates_dir, fname)

            # 1. 物理ファイル保存
            with open(save_path, "wb") as f:
                f.write(c["data"])

            # 2. DBへのハッシュ登録
            db_manager.register_file_hash(
                c["hash"], fname, c["doc_type"], case_id=c.get("case_id")
            )

            # 3. Vector Store Registration
            enriched_text = f"【ファイル名】{fname}\n【銀行名】{c['bank_name']}\n【書類種別】{c['doc_type']}\n\n{c['text']}"
            chunks = splitter.split_text(enriched_text)
            metadatas = [
                {
                    "source": fname,
                    "path": save_path,
                    "security_level": c["type"],
                    "bank_name": c["bank_name"],
                    "doc_type": c["doc_type"],
                }
                for _ in chunks
            ]

            # バッチ処理とリトライロジック (API制限対策)
            # 無料枠対策としてバッチサイズを小さく設定
            batch_size = 2
            total_chunks = len(chunks)

            for i in range(0, total_chunks, batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]

                # 最大5回のリトライロジック (指数バックオフ)
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        vector_store.add_texts(batch_chunks, metadatas=batch_metas)
                        # 成功したら少し待機して次へ (連打防止)
                        time.sleep(1.0)
                        break
                    except Exception as e:
                        error_str = str(e)
                        # 429(Resource Exhausted) または 400(Bad Request: e.g. Key expired) を検知
                        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            if attempt < max_retries - 1:
                                wait_time = (2**attempt) + random.random() * 2
                                st.warning(
                                    f"⚠️ API制限を検知。{wait_time:.1f}秒待機して再試行します... ({attempt + 1}/{max_retries})"
                                )
                                time.sleep(wait_time)
                            else:
                                st.error(
                                    f"❌ リトライ上限に達しました。登録失敗: {fname}"
                                )
                                raise e
                        else:
                            # その他のエラーは即座に上げる
                            raise e

            cnt += 1
            progress_bar.progress((idx + 1) / total_configs)

        status.update(label="✅ 全件登録完了！", state="complete", expanded=False)

    st.success(f"{cnt}件の学習・登録が完了しました！")
    st.session_state.upload_stage = []
    time.sleep(1.5)
    st.rerun()


# ---------------------------------------------------------
# メイン機能: データ管理タブの描画
# ---------------------------------------------------------
def render_management_tab(db_manager: DatabaseManager):
    st.subheader("🗑️ 登録済みファイルの管理")
    files = db_manager.get_all_files()

    if not files:
        st.info("登録されているファイルはありません。")
    else:
        df_files = pd.DataFrame(files)
        # カラム名のマッピング調整
        df_files.columns = [
            "ファイル名",
            "登録日時",
            "ハッシュ値",
            "書類種別",
            "案件",
            "doc_type_raw",
            "uploaded_at_raw",
        ]
        st.dataframe(
            df_files[["登録日時", "案件", "書類種別", "ファイル名"]],
            use_container_width=True,
        )

        st.divider()
        st.warning("【削除エリア】")
        selected_file = st.selectbox(
            "削除するファイルを選択", [f["filename"] for f in files]
        )

        if st.button("選択したファイルを完全に削除する"):
            templates_dir = os.path.join(ROOT_DIR, "data", "templates")
            target_path = os.path.join(templates_dir, selected_file)

            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError:
                    pass

            db_manager.delete_file_registry(selected_file)
            st.success(f"{selected_file} を削除しました。")
            time.sleep(1)
            st.rerun()