# ファイルパス: src/legal_system/ui/Home.py

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# プロジェクトルートへのパス解決 (update_bank_master読み込み用)
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(ROOT_DIR)

# LangChain関連
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# PDFプレビュー用
try:
    from pdf2image import convert_from_bytes
except ImportError:
    convert_from_bytes = None

# 自作モジュール
from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ocr_engine import extract_text_from_scanned_pdf

# 更新スクリプトの関数をインポート
try:
    from update_bank_master import (
        download_data,
        get_remote_last_commit_date,
        load_local_state,
        save_local_state,
    )
except ImportError:
    get_remote_last_commit_date = None

load_dotenv()

# ==========================================
# 2. アプリケーションの初期設定
# ==========================================
st.set_page_config(page_title="書士業務システム | ホーム", layout="wide", page_icon="⚖️")

# DBマネージャーの初期化
db_manager = DatabaseManager()
current_user = db_manager.get_current_user_info()


# ==========================================
# 更新チェック機能 (キャッシュ化)
# ==========================================
@st.cache_resource(ttl=3600)  # 1時間は再チェックしない
def check_update_status():
    """
    更新があるかチェックする関数
    戻り値: (status_code, message/date)
    status_code: 0=最新/オフライン, 1=更新あり, 2=エラー
    """
    if not get_remote_last_commit_date:
        return 2, "更新スクリプトなし"

    # 1. リモート確認 (タイムアウト付きで安全に)
    remote_date = get_remote_last_commit_date()
    if not remote_date:
        return 0, "オフライン (更新チェック不可)"

    # 2. ローカル確認
    local_state = load_local_state()
    local_date = local_state.get("last_commit_date", "")

    # 3. 比較
    if remote_date != local_date:
        return 1, remote_date  # 更新あり！日付を返す

    return 0, "最新です"


# ==========================================
# 3. 業務ルール・マスタ読み込み関数
# ==========================================
def load_company_rules():
    """全社共通の業務ルールを読み込む"""
    rule_path = os.path.join(ROOT_DIR, "data", "rules", "company_rules.txt")

    if os.path.exists(rule_path):
        try:
            with open(rule_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(rule_path, "r", encoding="cp932") as f:
                    return f.read()
            except Exception:
                return "（読込失敗：文字コード不明）"
        except Exception:
            return "（読込失敗）"
    return "（ファイルなし）"


def get_bank_specific_info(query: str):
    """銀行固有ルールをCSVから取得"""
    csv_path = os.path.join(ROOT_DIR, "data", "rules", "bank_master.csv")

    if not os.path.exists(csv_path):
        return ""

    df = None
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, encoding="cp932")
        except Exception:
            return ""
    except Exception:
        return ""

    if df is None:
        return ""

    try:
        info_text = ""
        for index, row in df.iterrows():
            bank_name = str(row.get("銀行名", ""))
            if bank_name and bank_name in query:
                info_text += f"""
                【{bank_name} 個別ルール】
                - 印鑑証明書の期限: {row.get("印鑑証明期限", "規定なし")}
                - 代理人本人確認書類: {row.get("代理人本人確認書類", "規定なし")}
                - 手数料支払方法: {row.get("振込ルール", "規定なし")}
                - 特記事項: {row.get("備考", "")}
                """
        return info_text
    except Exception:
        return ""


# ==========================================
# 4. ヘルパー関数 (ロジック & UI操作)
# ==========================================
def js_scroll_to_bottom():
    """画面最下部へスクロール"""
    js = """
    <script>
        var mainParams = window.parent.document.querySelector('section.main');
        if (mainParams) {
            mainParams.scrollTo({ top: mainParams.scrollHeight, behavior: 'smooth' });
        }
    </script>
    """
    components.html(js, height=0)


def js_focus_chat_input():
    """チャット入力欄にフォーカス"""
    js = """
    <script>
        setTimeout(function() {
            const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (textArea) { textArea.focus(); }
        }, 500);
    </script>
    """
    components.html(js, height=0)


def calculate_file_hash(file_bytes: bytes) -> str:
    """ファイルのMD5ハッシュ値を計算"""
    return hashlib.md5(file_bytes).hexdigest()


def analyze_document_info(text_content: str, llm):
    """ドキュメントから「ファイル名」「銀行名」「書類種別」を抽出する"""
    if not text_content:
        return {"filename": "", "bank_name": "", "doc_type": ""}

    prompt = """
    以下のドキュメント冒頭を読み、3つの情報をJSON形式で出力してください。
    
    1. filename: {金融機関名}_{書類名}
    2. bank_name: 金融機関名 (特定できなければ"その他")
    3. doc_type: 以下のいずれかを選択
       - "手引き": 手続きガイド、マニュアル、要領
       - "残高証明": 残高証明書発行依頼書
       - "相続届": 相続届、解約依頼書、名義変更届
       - "委任状": 委任状
       - "その他": 上記以外
    
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


def extract_text_safe(file_bytes: bytes) -> str:
    """PDFからテキスト抽出 (pypdf -> OCR)"""
    text = ""
    try:
        pdf = PdfReader(BytesIO(file_bytes))
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t
    except:
        pass
    if len(text.strip()) < 50:
        text = extract_text_from_scanned_pdf(file_bytes)
    return text


def filter_docs_by_bank_metadata(query: str, docs: list) -> list:
    """銀行名キーワードによる検索結果のフィルタリング"""
    bank_keywords = {
        "ゆうちょ": "ゆうちょ",
        "郵貯": "ゆうちょ",
        "じぶん": "じぶん",
        "au": "じぶん",
        "三菱": "三菱",
        "UFJ": "三菱",
        "みずほ": "みずほ",
        "三井": "三井",
        "SMBC": "三井",
        "りそな": "りそな",
        "横浜": "横浜",
        "千葉": "千葉",
    }

    target_key = None
    for key, required_str in bank_keywords.items():
        if key in query:
            target_key = required_str
            break

    if not target_key:
        return docs

    filtered_docs = []
    for d in docs:
        bank_meta = d.metadata.get("bank_name", "")
        filename = d.metadata.get("source", "")

        if target_key in bank_meta or target_key in filename:
            filtered_docs.append(d)

    return filtered_docs if filtered_docs else []


def run_rag_search(query: str, mode_label: str, llm):
    """RAG検索実行関数"""
    if not llm:
        return "AIモデルの初期化に失敗しました。", []

    # 1. ルール読込
    company_rules = load_company_rules()
    bank_specifics = get_bank_specific_info(query)

    # 2. 検索
    vector_store = AIFactory.get_vector_store()
    try:
        docs = vector_store.similarity_search(query, k=10)
        docs = filter_docs_by_bank_metadata(query, docs)
        docs = docs[:4]

        context = "\n\n".join([d.page_content for d in docs]) if docs else ""
        if not docs:
            context = "（関連する資料は見つかりませんでした）"

        db_manager.log_action(
            current_user["id"], "SEARCH", f"Mode:{mode_label}", f"Query: {query}"
        )
    except Exception as e:
        return f"検索エラー: {e}", []

    # 3. 回答生成
    system_prompt = f"""
    あなたは行政書士法人の業務システムです。回答対象は「行政書士補助者」です。
    【社内ルール】と【銀行マスタ】を**最優先**し、【参照資料】で補完して回答してください。
    
    【社内ルール】{company_rules}
    【銀行情報】{bank_specifics}
    
    【基本】
    1. 申請主体は「代表行政書士（代理人）」
    2. 挨拶不要。結論から記述。
    3. OCR誤字は補正して解釈。
    """
    template = f"""{system_prompt}\n【参照資料】{{context}}\n【質問】{{question}}"""

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()

    try:
        answer = chain.invoke({"context": context, "question": query})
        return answer, docs
    except Exception as e:
        return f"生成エラー: {str(e)}", []


# ==========================================
# 5. UIメイン構成
# ==========================================
def main():
    # --- サイドバー (ユーザー情報 & 更新) ---
    with st.sidebar:
        st.title("⚖️ 業務メニュー")
        st.info(f"👤 **{current_user['name']}**")
        st.caption(f"所属: {current_user['dept']}")
        if current_user["phone"]:
            st.caption(f"TEL: {current_user['phone']}")

        with st.expander("ユーザー情報更新"):
            new_name = st.text_input("表示名", value=current_user["name"])
            new_dept = st.text_input("所属", value=current_user["dept"])
            new_phone = st.text_input("電話番号", value=current_user["phone"])

            if st.button("更新"):
                db_manager.register_user(
                    current_user["id"], new_name, new_dept, new_phone
                )
                st.success("更新しました。再読み込みしてください。")

        st.divider()

        # ▼▼▼ 自動更新チェック機能 (UIプログレス対応版) ▼▼▼
        st.subheader("🔄 マスタデータ管理")

        # 起動時に一瞬だけチェック
        status, info = check_update_status()

        if status == 1:
            st.warning(f"⚠️ 新しい銀行データがあります\n({info[:10]})")

            if st.button("今すぐ更新して取り込む"):
                # --- Streamlitのプログレスバーを定義 ---
                progress_text = "データをダウンロード中..."
                my_bar = st.progress(0, text=progress_text)

                # --- コールバック関数: ダウンロード処理から呼び出される ---
                def update_progress(current, total, message):
                    percent = current / total
                    if percent > 1.0:
                        percent = 1.0
                    my_bar.progress(percent, text=f"{message} ({current}/{total})")

                # --- 実行 ---
                success, _ = download_data(progress_callback=update_progress)

                if success:
                    my_bar.progress(1.0, text="完了しました！")
                    save_local_state(info)
                    st.success("更新完了！アプリをリロードします。")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("更新に失敗しました。ネット接続を確認してください。")
        elif status == 0:
            st.caption(f"✅ {info}")
        else:
            st.caption("⚠️ 更新機能無効")
        # ▲▲▲ ここまで ▲▲▲

        st.divider()
        st.subheader("🤖 AIモード選択")
        ai_mode = st.radio(
            "処理モード:", ("☁️ Cloud (Gemini)", "🔒 Secure (Local)"), index=0
        )

        if "Cloud" in ai_mode:
            mode_label = "CLOUD"
            llm = AIFactory.get_llm("cloud")
            st.info("🚀 **高速・高機能**\n一般手続用。個人情報入力禁止。")
        else:
            mode_label = "LOCAL"
            llm = AIFactory.get_llm("local")
            st.warning("🛡️ **機密保護**\nオフライン処理。機密書類用。")

    # --- メインエリア ---
    tab1, tab2, tab3 = st.tabs(["💬 実務Q&A", "📥 資料学習 (OCR)", "🗑️ データ管理"])

    # --- Tab 1: チャット ---
    with tab1:
        st.subheader(f"金融機関手続のAI検索 ({mode_label})")
        js_focus_chat_input()

        if mode_label == "LOCAL":
            st.error("【機密モード】データは外部送信されません。")
        else:
            st.success("【クラウドモード】Gemini 2.5 使用中。")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.write(m["content"])
                if m.get("source_docs"):
                    with st.expander("📚 参照した雛形・資料をダウンロード"):
                        seen_paths = set()
                        for doc in m["source_docs"]:
                            path = doc.metadata.get("path")
                            name = doc.metadata.get("source", "不明なファイル")
                            bank = doc.metadata.get("bank_name", "")
                            dtype = doc.metadata.get("doc_type", "")

                            label_parts = [f"📥 {name}"]
                            if bank:
                                label_parts.append(f"({bank})")
                            if dtype:
                                label_parts.append(f"[{dtype}]")
                            label = " ".join(label_parts)

                            if path and os.path.exists(path) and path not in seen_paths:
                                seen_paths.add(path)
                                with open(path, "rb") as f:
                                    st.download_button(
                                        label=label,
                                        data=f,
                                        file_name=os.path.basename(path),
                                        mime="application/pdf",
                                        key=f"dl_{os.path.basename(path)}_{time.time()}",
                                    )

        if prompt := st.chat_input("質問を入力..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("社内ルール・手引きを確認中..."):
                    response, source_docs = run_rag_search(prompt, mode_label, llm)
                    st.write(response)

                    if source_docs:
                        with st.expander(
                            "📚 参照した雛形・資料をダウンロード", expanded=True
                        ):
                            seen_paths = set()
                            for doc in source_docs:
                                path = doc.metadata.get("path")
                                name = doc.metadata.get("source", "不明なファイル")
                                bank = doc.metadata.get("bank_name", "")
                                dtype = doc.metadata.get("doc_type", "")

                                label_parts = [f"📥 {name}"]
                                if bank:
                                    label_parts.append(f"({bank})")
                                if dtype:
                                    label_parts.append(f"[{dtype}]")
                                label = " ".join(label_parts)

                                if (
                                    path
                                    and os.path.exists(path)
                                    and path not in seen_paths
                                ):
                                    seen_paths.add(path)
                                    with open(path, "rb") as f:
                                        st.download_button(
                                            label=label,
                                            data=f,
                                            file_name=os.path.basename(path),
                                            mime="application/pdf",
                                        )

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                            "source_docs": source_docs,
                        }
                    )

    # --- Tab 2: アップロード ---
    with tab2:
        st.subheader("📂 雛形・記入例の登録")
        st.caption("重複チェック・タグ付け機能付き。PDFを解析し登録します。")

        s_norm, s_sec = st.tabs(["🟦 一般雛形", "🟥 記入例 (機密)"])

        # 2-A. 一般
        with s_norm:
            st.info("個人情報を含まない手引き等")

            # === 【追加】案件紐付け選択エリア ===
            session = db_manager._get_session()
            target_case_id = None
            try:
                from legal_system.models.tables import Case

                cases = session.query(Case).all()
                # 選択肢: None(共通) + 各案件
                case_opts = {"（全案件共通の雛形として登録）": None}
                for c in cases:
                    case_opts[f"{c.case_number}: {c.client_name}"] = c.case_id

                selected_case_label = st.selectbox(
                    "紐付ける案件 (任意)",
                    list(case_opts.keys()),
                    help="特定の案件専用の資料であれば案件を選択してください。テンプレートの場合は「共通」のままにしてください。",
                )
                target_case_id = case_opts[selected_case_label]
            finally:
                session.close()
            # =====================================

            files_n = st.file_uploader(
                "PDFアップロード (一般)", accept_multiple_files=True, key="up_n"
            )

            if files_n and st.button("🔍 クラウド解析", key="btn_n"):
                st.session_state.upload_stage = []
                llm_cloud = AIFactory.get_llm("cloud")

                for f in files_n:
                    fb = f.read()
                    f_hash = calculate_file_hash(fb)
                    if db_manager.is_file_registered(f_hash):
                        st.warning(f"⚠️ {f.name} は既に登録されています。")
                        continue

                    text = extract_text_safe(fb)
                    meta = (
                        analyze_document_info(text, llm_cloud)
                        if text
                        else {
                            "filename": f.name,
                            "bank_name": "その他",
                            "doc_type": "その他",
                        }
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
                            "case_id": target_case_id,  # 選択された案件IDを保持
                        }
                    )

                if st.session_state.upload_stage:
                    st.rerun()
                else:
                    st.info("新規登録対象はありません。")

        # 2-B. 機密
        with s_sec:
            st.warning("個人情報を含む書類 (ローカル処理)")
            # こちらも同様に案件紐付けを追加
            session = db_manager._get_session()
            target_case_id_sec = None
            try:
                from legal_system.models.tables import Case

                cases = session.query(Case).all()
                case_opts = {"（全案件共通の雛形として登録）": None}
                for c in cases:
                    case_opts[f"{c.case_number}: {c.client_name}"] = c.case_id

                selected_case_label_sec = st.selectbox(
                    "紐付ける案件 (任意)",
                    list(case_opts.keys()),
                    key="sec_case_sel",
                    help="特定の案件専用の資料であれば案件を選択してください。",
                )
                target_case_id_sec = case_opts[selected_case_label_sec]
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
                            images = convert_from_bytes(fb_s, first_page=1, last_page=1)
                            if images:
                                st.image(images[0], caption="プレビュー", width=400)
                                js_scroll_to_bottom()
                        except:
                            pass

                    check = st.checkbox(
                        "機密書類であることを確認しました", key="check_s"
                    )
                    if check:
                        js_scroll_to_bottom()

                    if check and st.button("🔒 ローカル解析", key="btn_s"):
                        st.session_state.upload_stage = []
                        llm_local = AIFactory.get_llm("local")

                        with st.spinner("解析中..."):
                            text_s = extract_text_safe(fb_s)
                            meta = (
                                analyze_document_info(text_s, llm_local)
                                if text_s
                                else {
                                    "filename": file_s.name,
                                    "bank_name": "その他",
                                    "doc_type": "その他",
                                }
                            )
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
                                    "case_id": target_case_id_sec,  # 案件IDを保持
                                }
                            )
                        st.rerun()

        # 2-C. 保存処理
        if st.session_state.get("upload_stage"):
            st.divider()
            st.subheader("💾 登録確認")
            with st.form("save_form"):
                configs = []
                st.caption("登録名、銀行名タグ、書類種別を確認してください。")

                for i, item in enumerate(st.session_state.upload_stage):
                    c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                    c1.text(item["old"])
                    new_name = c2.text_input("登録名", value=item["new"], key=f"fn_{i}")
                    new_bank = c3.text_input(
                        "銀行タグ", value=item["bank_name"], key=f"bk_{i}"
                    )

                    current_type = item.get("doc_type", "その他")
                    type_options = [
                        "手引き",
                        "残高証明",
                        "取引明細",
                        "顧客勘定元帳",
                        "相続届",
                        "その他",
                    ]
                    idx = (
                        type_options.index(current_type)
                        if current_type in type_options
                        else 4
                    )
                    new_type = c4.selectbox(
                        "種別", type_options, index=idx, key=f"dt_{i}"
                    )

                    configs.append(
                        {
                            **item,
                            "name": new_name,
                            "bank_name": new_bank,
                            "doc_type": new_type,
                        }
                    )

                if st.form_submit_button("✅ 登録実行"):
                    vector_store = AIFactory.get_vector_store()
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=800, chunk_overlap=100
                    )
                    cnt = 0
                    today = datetime.now().strftime("%Y%m%d")

                    templates_dir = os.path.join(ROOT_DIR, "data", "templates")
                    os.makedirs(templates_dir, exist_ok=True)

                    for c in configs:
                        fname = f"{c['name']}_{today}.pdf"
                        save_path = os.path.join(templates_dir, fname)

                        with open(save_path, "wb") as f:
                            f.write(c["data"])

                        # 【修正】case_idを渡して登録
                        db_manager.register_file_hash(
                            c["hash"], fname, c["doc_type"], case_id=c.get("case_id")
                        )

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

                        vector_store.add_texts(chunks, metadatas=metadatas)
                        cnt += 1

                    st.success(f"{cnt}件登録しました！")
                    st.session_state.upload_stage = []

    # --- Tab 3: データ管理 ---
    with tab3:
        st.subheader("🗑️ 登録済みファイルの管理")
        files = db_manager.get_all_files()

        if not files:
            st.info("登録されているファイルはありません。")
        else:
            df_files = pd.DataFrame(files)
            # 【修正】カラムに「案件」を追加
            df_files.columns = [
                "ファイル名",
                "登録日時",
                "ハッシュ値",
                "書類種別",
                "案件",
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
                    os.remove(target_path)

                db_manager.delete_file_registry(selected_file)
                st.success(f"{selected_file} を削除しました。再登録してください。")
                time.sleep(1)
                st.rerun()


if __name__ == "__main__":
    main()
