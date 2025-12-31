# src/legal_rag_system/ui/app.py

# ==========================================
# 1. ライブラリのインポート
# ==========================================
import hashlib
import os
import sys
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# プロジェクトルートへのパス解決
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

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
from legal_rag_system.core.ai_factory import AIFactory
from legal_rag_system.core.database import DatabaseManager
from legal_rag_system.core.ocr_engine import extract_text_from_scanned_pdf

load_dotenv()

# ==========================================
# 2. アプリケーションの初期設定
# ==========================================
st.set_page_config(page_title="行政書士DX System", layout="wide", page_icon="⚖️")

db_manager = DatabaseManager()
current_user = db_manager.get_current_user_info()


# ==========================================
# 3. 業務ルール・マスタ読み込み関数
# ==========================================
def load_company_rules():
    """全社共通の業務ルールを読み込む"""
    rule_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
        "rules",
        "company_rules.txt",
    )
    if os.path.exists(rule_path):
        try:
            with open(rule_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return "（読込失敗）"
    return "（ファイルなし）"


def get_bank_specific_info(query: str):
    """銀行固有ルールをCSVから取得"""
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
        "rules",
        "bank_master.csv",
    )
    if not os.path.exists(csv_path):
        return ""
    try:
        df = pd.read_csv(csv_path)
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
    """ファイルのMD5ハッシュ値を計算して重複チェックに利用"""
    return hashlib.md5(file_bytes).hexdigest()


def generate_filename(text_content: str, llm):
    """ドキュメント冒頭からファイル名を生成"""
    if not text_content:
        return ""
    prompt = """
    以下のドキュメント冒頭を読み、ファイル名のみを出力してください。
    【出力ルール】
    1. 形式: {金融機関名}_{書類名}
    2. 挨拶、説明、マークダウン記法は禁止。単語のみ返す。
    3. 不明な場合は「不明」と回答。
    【冒頭】{text}
    """
    try:
        response = llm.invoke(prompt.format(text=text_content[:1500]))
        content = response.content if hasattr(response, "content") else str(response)
        cleaned_name = (
            content.strip().replace("ファイル名:", "").replace("```", "").strip()
        )
        if "\n" in cleaned_name:
            cleaned_name = cleaned_name.split("\n")[-1]
        return cleaned_name
    except Exception:
        return ""


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


def filter_docs_by_bank_name(query: str, docs: list) -> list:
    """
    【重要修正】
    クエリに銀行名が含まれる場合、ファイル名にその銀行名が含まれないドキュメントを除外する。
    これにより「ゆうちょ」と聞いて「auじぶん」が出るのを防ぐ。
    """
    # 簡易的な銀行名キーワード辞書 (必要に応じて拡充可)
    # キー: クエリに含まれる言葉, 値: ファイル名に必須の言葉
    bank_keywords = {
        "ゆうちょ": "ゆうちょ",
        "郵貯": "ゆうちょ",
        "じぶん": "じぶん",
        "三菱": "三菱",
        "UFJ": "UFJ",
        "みずほ": "みずほ",
        "三井住友": "三井住友",
        "SMBC": "SMBC",
        "りそな": "りそな",
        "横浜": "横浜",
        "千葉": "千葉",
    }

    target_key = None
    for key, required_str in bank_keywords.items():
        if key in query:
            target_key = required_str
            break

    # ターゲット銀行が見つからなければフィルタリングせずそのまま返す
    if not target_key:
        return docs

    # フィルタリング実行
    filtered_docs = []
    for d in docs:
        filename = d.metadata.get("source", "")
        # ファイル名にターゲット銀行名が含まれているか確認
        if target_key in filename:
            filtered_docs.append(d)

    # もしフィルタリングしすぎて0件になった場合は、
    # 念のため元のリストを返すが、本来は「該当なし」とすべき
    if not filtered_docs:
        # ここは運用判断。今回は「間違った銀行を出すくらいなら空リストの方がマシ」として空を返す手もあるが、
        # いったん元ドキュメントを返して、プロンプトで制御させるアプローチをとる
        # ただし、今回は「明らかに違う銀行が出る」のを防ぎたいので、空なら空を返す。
        return []

    return filtered_docs


def run_rag_search(query: str, mode_label: str, llm):
    """
    RAG検索実行関数。
    回答テキストだけでなく、参照したドキュメント情報も返すように拡張。
    """
    if not llm:
        return "AIモデルの初期化に失敗しました。", []

    # 1. ルール読込
    company_rules = load_company_rules()
    bank_specifics = get_bank_specific_info(query)

    # 2. 検索
    vector_store = AIFactory.get_vector_store()
    try:
        # 多めに取得してからフィルタリングする (k=10)
        docs = vector_store.similarity_search(query, k=10)

        # 【修正】銀行名によるフィルタリングを実行
        docs = filter_docs_by_bank_name(query, docs)

        # コンテキスト用に上位4件に絞る
        docs = docs[:4]

        if not docs:
            return (
                "指定された銀行に関連する資料が見つかりませんでした。ファイル名が正しく登録されているか確認してください。",
                [],
            )

        context = "\n\n".join([d.page_content for d in docs])
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
        return answer, docs  # ドキュメントオブジェクトも返す
    except Exception as e:
        return f"生成エラー: {str(e)}", []


# ==========================================
# 5. UIメイン構成
# ==========================================
def main():
    # --- サイドバー (ユーザー情報) ---
    with st.sidebar:
        st.title("⚖️ 業務メニュー")
        st.info(f"👤 **{current_user['name']}**")
        st.caption(f"所属: {current_user['dept']}")
        if current_user["phone"]:
            st.caption(f"TEL: {current_user['phone']}")

        # ユーザー登録・更新フォーム (電話番号追加)
        with st.expander("ユーザー情報更新"):
            new_name = st.text_input("表示名", value=current_user["name"])
            new_dept = st.text_input("所属", value=current_user["dept"])
            new_phone = st.text_input(
                "電話番号", value=current_user["phone"], placeholder="03-xxxx-xxxx"
            )

            if st.button("更新"):
                db_manager.register_user(
                    current_user["id"], new_name, new_dept, new_phone
                )
                st.success("更新しました。再読み込みしてください。")

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
    tab1, tab2 = st.tabs(["💬 実務Q&A", "📥 資料学習 (OCR)"])

    # --- Tab 1: チャット ---
    with tab1:
        st.subheader(f"金融機関手続検索 ({mode_label})")

        # タブクリック時もフォーカスを当てる
        js_focus_chat_input()

        if mode_label == "LOCAL":
            st.error("【機密モード】データは外部送信されません。")
        else:
            st.success("【クラウドモード】Gemini 2.5 使用中。")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # 履歴表示ループ
        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.write(m["content"])
                # 参照ファイルがあればダウンロードボタンを表示
                if m.get("source_docs"):
                    with st.expander("📚 参照した雛形・資料をダウンロード"):
                        seen_paths = set()
                        for doc in m["source_docs"]:
                            path = doc.metadata.get("path")
                            name = doc.metadata.get("source", "不明なファイル")

                            if path and os.path.exists(path) and path not in seen_paths:
                                seen_paths.add(path)
                                with open(path, "rb") as f:
                                    st.download_button(
                                        label=f"📥 {name}",
                                        data=f,
                                        file_name=os.path.basename(path),
                                        mime="application/pdf",
                                        key=f"dl_{os.path.basename(path)}_{time.time()}",
                                    )

        # 質問入力
        if prompt := st.chat_input("質問を入力..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)

            with st.chat_message("assistant"):
                with st.spinner("社内ルール・手引きを確認中..."):
                    response, source_docs = run_rag_search(prompt, mode_label, llm)
                    st.write(response)

                    # 参照ファイルの表示
                    if source_docs:
                        with st.expander(
                            "📚 参照した雛形・資料をダウンロード", expanded=True
                        ):
                            seen_paths = set()
                            for doc in source_docs:
                                path = doc.metadata.get("path")
                                name = doc.metadata.get("source", "不明なファイル")

                                if (
                                    path
                                    and os.path.exists(path)
                                    and path not in seen_paths
                                ):
                                    seen_paths.add(path)
                                    with open(path, "rb") as f:
                                        st.download_button(
                                            label=f"📥 {name}",
                                            data=f,
                                            file_name=os.path.basename(path),
                                            mime="application/pdf",
                                        )

                    # 履歴に保存 (ソース情報含む)
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
        st.caption("重複チェック機能付き。PDFを解析し登録します。")

        s_norm, s_sec = st.tabs(["🟦 一般雛形", "🟥 記入例 (機密)"])

        # 2-A. 一般
        with s_norm:
            st.info("個人情報を含まない手引き等")
            files_n = st.file_uploader(
                "PDFアップロード (一般)", accept_multiple_files=True, key="up_n"
            )

            if files_n and st.button("🔍 クラウド解析", key="btn_n"):
                st.session_state.upload_stage = []
                llm_cloud = AIFactory.get_llm("cloud")

                for f in files_n:
                    fb = f.read()

                    # === 重複チェック ===
                    f_hash = calculate_file_hash(fb)
                    if db_manager.is_file_registered(f_hash):
                        st.warning(
                            f"⚠️ {f.name} は既に登録されています。スキップします。"
                        )
                        continue

                    text = extract_text_safe(fb)
                    sn = generate_filename(text, llm_cloud) if text else f.name
                    if not sn or "不明" in sn:
                        sn = f.name

                    st.session_state.upload_stage.append(
                        {
                            "old": f.name,
                            "new": sn,
                            "data": fb,
                            "text": text,
                            "type": "general",
                            "hash": f_hash,
                        }
                    )

                if st.session_state.upload_stage:
                    st.rerun()
                else:
                    st.info("新規登録対象のファイルはありませんでした。")

        # 2-B. 機密
        with s_sec:
            st.warning("個人情報を含む書類 (ローカル処理)")
            file_s = st.file_uploader(
                "PDFアップロード (機密)", accept_multiple_files=False, key="up_s"
            )

            if file_s:
                fb_s = file_s.read()

                # === 重複チェック ===
                f_hash = calculate_file_hash(fb_s)
                is_duplicate = db_manager.is_file_registered(f_hash)

                if is_duplicate:
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
                            sn_s = (
                                generate_filename(text_s, llm_local)
                                if text_s
                                else file_s.name
                            )
                            if sn_s and "不明" not in sn_s:
                                sn_s += "_記入例"
                            else:
                                sn_s = file_s.name

                            st.session_state.upload_stage.append(
                                {
                                    "old": file_s.name,
                                    "new": sn_s,
                                    "data": fb_s,
                                    "text": text_s,
                                    "type": "secure",
                                    "hash": f_hash,
                                }
                            )
                        st.rerun()

        # 2-C. 保存処理
        if st.session_state.get("upload_stage"):
            st.divider()
            st.subheader("💾 登録確認")
            with st.form("save_form"):
                configs = []
                for i, item in enumerate(st.session_state.upload_stage):
                    c1, c2 = st.columns([1, 2])
                    c1.text(f"元: {item['old']}")
                    new_name = c2.text_input("登録名", value=item["new"], key=f"fn_{i}")
                    configs.append({**item, "name": new_name})

                if st.form_submit_button("✅ 登録実行"):
                    vector_store = AIFactory.get_vector_store()
                    splitter = RecursiveCharacterTextSplitter(
                        chunk_size=800, chunk_overlap=100
                    )
                    cnt = 0
                    today = datetime.now().strftime("%Y%m%d")

                    for c in configs:
                        fname = f"{c['name']}_{today}.pdf"
                        # パス解決
                        save_path = os.path.join(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(os.path.dirname(__file__))
                                )
                            ),
                            "data",
                            "templates",
                            fname,
                        )
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                        with open(save_path, "wb") as f:
                            f.write(c["data"])

                        # ハッシュ登録
                        db_manager.register_file_hash(c["hash"], fname)

                        chunks = splitter.split_text(c["text"])
                        metadatas = [
                            {
                                "source": fname,
                                "path": save_path,
                                "security_level": c["type"],
                            }
                            for _ in chunks
                        ]

                        vector_store.add_texts(chunks, metadatas=metadatas)
                        cnt += 1

                    st.success(f"{cnt}件登録しました！")
                    st.session_state.upload_stage = []


if __name__ == "__main__":
    main()
