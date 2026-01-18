import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 1. プロジェクトルートをパスに追加して、srcモジュールを読み込めるようにする
# (このファイルは scripts/ にあるので、2つ上の階層がルート)
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

# 2. 既存のtables.pyからモデル定義を読み込む
# パスエラーが出る場合は、tables.pyの場所を確認してください
try:
    from src.legal_system.models.tables import BankMaster, Base, Case
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print(f"PYTHONPATH: {sys.path}")
    sys.exit(1)

# 3. DBファイルの保存場所 (SQLite)
# tables.py や persistence_service.py で指定しているパスと合わせる
DB_PATH = os.path.join(root_dir, "data", "db", "legal_system.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DB_URL = f"sqlite:///{DB_PATH}"


def init_db():
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)

    # テーブル作成 (既存データは消えません)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # --- A. 銀行マスタの作成 ---
        banks = [
            ("三菱UFJ銀行", "0005"),
            ("三井住友銀行", "0009"),
            ("みずほ銀行", "0001"),
            ("ゆうちょ銀行", "9900"),
        ]

        print("Checking Bank Master...")
        for name, code in banks:
            # 重複チェック: bank_code が既にあるか？
            exists = session.query(BankMaster).filter_by(bank_code=code).first()
            if not exists:
                session.add(BankMaster(bank_name=name, bank_code=code))
                print(f"  + Added: {name}")
            else:
                print(f"  . Exists: {name}")

        # --- B. テスト用案件の作成 ---
        # kintone_data_sample.json の record_id="1001" に対応するデータ
        target_case_id = 1001

        print(f"Checking Case ID: {target_case_id}...")
        # kintone_record_id は Integer か String か tables.py の定義次第ですが、
        # ここでは汎用的にフィルタします
        case_exists = (
            session.query(Case).filter(Case.kintone_record_id == target_case_id).first()
        )

        if not case_exists:
            # 必須フィールドを埋める (tables.pyの定義に基づく)
            new_case = Case(
                case_id=target_case_id,  # 主キーを強制指定
                case_number="G1234",
                client_name="相続 太郎",
                client_name_kana="ソウゾク タロウ",
                kintone_record_id=target_case_id,
                folder_path="/server/G1234",  # NOT NULL制約対策
            )
            session.add(new_case)
            print(f"  + Added Case: G1234 (ID: {target_case_id})")
        else:
            print(f"  . Exists Case: {case_exists.case_number}")

        session.commit()
        print("\n🎉 データベースの初期化が完了しました！")

    except Exception as e:
        session.rollback()
        print(f"❌ Error during initialization: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    init_db()
