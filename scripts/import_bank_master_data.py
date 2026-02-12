import os
import sys
import csv
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import BankMaster, FinancialAsset, BranchMaster, BankAlias

def import_bank_master_data():
    print("🏦 銀行マスタデータのインポートを開始します...")
    
    db = DatabaseManager()
    session = db._get_session()

    print("🔄 既存の銀行マスタデータをクリアします...")

    # 関連テーブルからデータを先に削除
    session.query(FinancialAsset).delete()
    session.query(BranchMaster).delete()
    session.query(BankAlias).delete()
    session.commit()
    print("✅ 関連データクリア完了。")

    session.query(BankMaster).delete()
    session.commit()
    print("✅ 既存銀行マスタデータクリア完了。")

    
    csv_path = ROOT_DIR / "data" / "rules" / "bank_master.csv"
    imported_count = 0
    skipped_count = 0

    if not csv_path.exists():
        print(f"❌ エラー: {csv_path} が見つかりません。")
        session.close()
        return

    try:
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bank_name = row.get("bank_name")
                bank_code = row.get("bank_code")

                if not bank_name or not bank_code:
                    print(f"⚠️ スキップ: 'bank_name' または 'bank_code' が不足している行があります: {row}")
                    skipped_count += 1
                    continue

                # 既に登録済みかチェック (bank_name または bank_code で)
                exists = session.query(BankMaster).filter(
                    (BankMaster.bank_name == bank_name) | 
                    (BankMaster.bank_code == bank_code)
                ).first()

                if exists:
                    print(f"  . スキップ (登録済み): {bank_name} ({bank_code})")
                    skipped_count += 1
                    continue

                new_bank = BankMaster(
                    bank_name=bank_name,
                    bank_code=bank_code,
                    seal_cert_limit=row.get("seal_cert_limit"),
                    id_verify_rule=row.get("id_verify_rule"),
                    transfer_rule=row.get("transfer_rule"),
                    remarks=row.get("remarks"),
                )
                session.add(new_bank)
                print(f"  + 登録: {bank_name} ({bank_code})")
                imported_count += 1

        session.commit()
        print(f"\n✅ 銀行マスタデータのインポート完了 (新規: {imported_count}件, スキップ: {skipped_count}件)")

    except Exception as e:
        session.rollback()
        print(f"❌ エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    import_bank_master_data()