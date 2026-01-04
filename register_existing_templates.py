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
