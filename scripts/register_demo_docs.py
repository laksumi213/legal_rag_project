# scripts/register_demo_docs.py
import hashlib
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import FileRegistry


def calculate_file_hash(file_path):
    """ファイルのSHA256ハッシュを計算する"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()


def register_documents():
    """data/demo_bank_docs/ にあるPDFをDBに登録する"""
    print("📄 デモ用PDFのデータベース登録を開始します...")

    db = DatabaseManager()
    session = db._get_session()

    docs_dir = ROOT_DIR / "data" / "demo_bank_docs"
    registered_count = 0
    skipped_count = 0

    try:
        pdf_files = list(docs_dir.glob("*.pdf"))
        if not pdf_files:
            print("⚠️ 対象のPDFファイルが見つかりません。")
            return

        for pdf_path in pdf_files:
            file_hash = calculate_file_hash(pdf_path)

            # 既に登録済みかチェック
            exists = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            if exists:
                print(f"  . スキップ (登録済み): {pdf_path.name}")
                skipped_count += 1
                continue

            # doc_typeをファイル名から簡易的に判定
            doc_type = "その他"
            if "残高証明書" in pdf_path.name or "残証" in pdf_path.name:
                doc_type = "残高証明書"

            new_registry = FileRegistry(
                file_hash=file_hash,
                filename=pdf_path.name,
                file_path=str(pdf_path.relative_to(ROOT_DIR)).replace("\\", "/"),
                doc_type=doc_type,
                registered_at=datetime.now(),
                status="CONFIRMED",
            )

            session.add(new_registry)
            print(f"  + 登録: {pdf_path.name}")
            registered_count += 1

        session.commit()
        print(
            f"\n✅ 登録完了 (新規: {registered_count}件, スキップ: {skipped_count}件)"
        )

    except Exception as e:
        session.rollback()
        print(f"❌ エラーが発生しました: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    register_documents()
