import shutil  # ★追加
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv  # NEW IMPORT

load_dotenv()  # Load environment variables from .env file

from legal_system.services.rag_search_service import RagSearchService

from legal_system.core.config import Config  # ★追加
from legal_system.services.scanner_service import ScannerService  # NEW IMPORT

st.set_page_config(page_title="遺言書AI解析デモ", page_icon="🤖", layout="wide")
st.title("🤖 遺言書AI意味解析・インデックス化デモ")
st.caption(
    "Wordファイルをアップロードし、その内容をAIが解析・インデックス化して、セマンティック検索で回答を生成するデモです。"
)

# RAGサービスを初期化
rag_service = RagSearchService()
# ScannerServiceを初期化
scanner_service = ScannerService()  # Moved to top level


def clear_vector_store():
    """ChromaDBの永続化ディレクトリを削除してクリアする"""
    if Config.VECTOR_STORE_PATH.exists():
        shutil.rmtree(Config.VECTOR_STORE_PATH)
        st.success("Vector Storeをクリアしました。")
    else:
        st.info("Vector Storeは既に存在しませんでした。")


# --- フォルダからのインデックス化 ---
st.subheader("1. 遺言書フォルダからのファイル検索とインデックス化")
st.caption(
    "指定したフォルダ内（サブフォルダ含む）から遺言書関連ファイル（Word, PDF）を検索し、その内容をAIが解析・インデックス化します。"
)

# Directory input
ingest_folder_path = st.text_input(
    "インデックス化したいフォルダのパスを入力してください (例: Z:/path/to/遺言)",
    value="data/demo_wills/",  # Using local demo wills folder for testing
)

if st.button("📁 フォルダから遺言書を検索しインデックス化", type="primary"):
    if (
        ingest_folder_path
        and Path(ingest_folder_path).exists()
        and Path(ingest_folder_path).is_dir()
    ):
        found_will_docs = []

        target_folder = Path(ingest_folder_path)

        # Walk through the directory to find relevant files
        all_files = list(target_folder.rglob("*"))  # Recursive search

        progress_bar = st.progress(0, text="フォルダを検索中...")

        # Filter for will documents
        for i, file_path in enumerate(all_files):
            if file_path.is_file():
                filename = file_path.name.lower()
                is_will_folder = False
                current_path = file_path.parent
                # Check if any parent folder contains "遺言"
                while (
                    current_path != current_path.parent
                    and current_path != target_folder.parent
                ):
                    if "遺言" in current_path.name:
                        is_will_folder = True
                        break
                    current_path = current_path.parent

                if (
                    is_will_folder
                    and ("遺言書" in filename or "公正証書" in filename)
                    and file_path.suffix.lower() in [".docx", ".pdf"]
                ):
                    found_will_docs.append(file_path)

            progress_bar.progress(
                (i + 1) / len(all_files), text=f"フォルダを検索中: {file_path.name}"
            )
        progress_bar.empty()

        if found_will_docs:
            st.info(
                f"✅ {len(found_will_docs)} 個の遺言関連ファイルが見つかりました。インデックス化を開始します。"
            )

            progress_bar = st.progress(0, text="インデックス化中...")
            for i, will_doc_path in enumerate(found_will_docs):
                with st.spinner(f"'{will_doc_path.name}' をRAGに取り込み中..."):
                    try:
                        scanner_service.ingest_will_for_rag(will_doc_path)
                        st.success(
                            f"✅ ファイル '{will_doc_path.name}' のRAG取り込みが完了しました。"
                        )
                    except Exception as e:
                        st.error(
                            f"❌ ファイル '{will_doc_path.name}' のRAG取り込み中にエラーが発生しました: {e}"
                        )
                progress_bar.progress(
                    (i + 1) / len(found_will_docs),
                    text=f"インデックス化中: {will_doc_path.name}",
                )
            progress_bar.empty()
            st.info(
                f"{len(found_will_docs)} 個のファイルのインデックス化が完了しました。"
            )
        else:
            st.warning(
                "指定されたフォルダからは遺言関連ファイルが見つかりませんでした。"
            )

    else:
        st.error("有効なフォルダパスを入力してください。")

st.markdown("--- # 2. セマンティック検索による質問")

st.markdown("---")
st.subheader("3. Z:ドライブからのRAG取り込みテスト")
st.caption("指定したパスの遺言書ファイルをRAGインデックスに直接取り込みます。")

# ScannerServiceの初期化 - REMOVED, now initialized globally
# scanner_service = ScannerService()

z_drive_file_path = st.text_input(
    "取り込みたいZ:ドライブ上のファイルパスを入力してください (例: Z:/path/to/遺言書/will.docx)",
    value="data/demo_wills/will_sample_1.docx",  # Local test file for convenience
)

if st.button("📥 Z:ドライブファイルをRAGに取り込む", type="secondary"):
    if z_drive_file_path:
        with st.spinner(
            f"Z:ドライブファイル '{z_drive_file_path}' をRAGに取り込み中..."
        ):
            try:
                # Pathオブジェクトに変換して渡す
                scanner_service.ingest_will_for_rag(Path(z_drive_file_path))
                st.success(
                    f"✅ ファイル '{z_drive_file_path}' のRAG取り込みが完了しました。"
                )
            except Exception as e:
                st.error(
                    f"❌ ファイル '{z_drive_file_path}' のRAG取り込み中にエラーが発生しました: {e}"
                )
    else:
        st.warning("取り込みたいファイルパスを入力してください。")


st.markdown("--- # ユーティリティ")

# --- セマンティック検索 ---
st.subheader("2. インデックス化されたドキュメントへの質問")
query = st.text_area(
    "遺言書の内容について質問を入力してください",
    placeholder="例: 遺産は誰にどのように分配されますか？、不動産の記述はありますか？",
)

if st.button("🔍 質問をAIに問い合わせる", type="primary"):
    if query:
        with st.spinner("AIが回答を生成中..."):
            try:
                answer = rag_service.semantic_search_will_documents(query)
                st.markdown("##### 💡 AIからの回答")
                st.write(answer)
            except Exception as e:
                st.error(f"質問処理中にエラーが発生しました: {e}")
    else:
        st.warning("質問が入力されていません。")

st.markdown("--- # ユーティリティ")
st.subheader("ユーティリティ")
if st.button("🗑️ 全てのインデックスをクリアする (要確認)"):
    if st.checkbox("本当にクリアしますか？ (この操作は元に戻せません)"):
        clear_vector_store()

if st.checkbox(f"Vector Store Path: {Config.VECTOR_STORE_PATH.absolute()}"):
    st.write(rag_service.vector_store.get())
