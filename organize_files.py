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