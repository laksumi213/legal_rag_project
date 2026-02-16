# scripts/migrate_postgres_data.py

import logging
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
from pathlib import Path

from sqlalchemy import MetaData, Table, create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))
SRC_DIR = ROOT_DIR / "src"
sys.path.append(str(SRC_DIR))

from legal_system.core.config import Config
from legal_system.models.tables import (
    AccountTypeMaster,
    Base,
    Case,
    CaseStatus,
    Deceased,
    Heir,
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def migrate_data():
    logger.info("🚀 PostgreSQL データ移行プロセスを開始します...")

    # DB接続エンジンの作成
    # ※移行元と移行先が同じDBと想定
    engine = create_engine(Config.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # メタデータ管理用
    metadata_old = MetaData()

    try:
        # 1. 旧テーブルの存在確認と読み込み (Reflection)
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # 旧テーブル名（レガシーシステムで使われていた名前）
        legacy_table_names = ["customer", "heir", "bank_customer"]

        # 必須テーブルがあるかチェック
        if "customer" not in existing_tables:
            logger.error(
                "❌ 旧テーブル 'customer' が見つかりません。移行を中止します。"
            )
            return

        logger.info("📦 旧テーブル定義を読み込んでいます...")
        # 旧テーブルを動的に定義（ORMモデルとの衝突回避）
        t_customer = Table("customer", metadata_old, autoload_with=engine)

        # 'heir'テーブルは新旧で名前が被るため、旧テーブルは t_heir_old として扱う
        t_heir_old = Table("heir", metadata_old, autoload_with=engine)

        t_bank_customer = Table("bank_customer", metadata_old, autoload_with=engine)

        # 2. 新テーブルの作成
        # ※既存のデータ(customerなど)は消さずに、新しいテーブル(casesなど)だけを作る
        logger.info("🔨 新しいテーブルスキーマを作成中...")
        Base.metadata.create_all(engine)

        # 3. マスタデータの投入 (Status, AccountType)
        logger.info("🌱 初期マスタデータを投入中...")
        _seed_master_data(session)

        # 4. データ移行: Customer -> Case & Deceased
        logger.info("🔄 案件・被相続人データを移行中...")

        # 旧 customer テーブルから全件取得
        query = select(t_customer)
        customers = session.execute(query).fetchall()

        case_map = {}  # 旧code -> 新case_id

        for row in customers:
            # Rowオブジェクトはカラム名でアクセス可能 (row.code, row.username1...)
            # ※カラム名が実際と異なる場合は適宜修正してください

            # --- Case作成 ---
            # 新DBでの重複チェック
            existing_case = session.query(Case).filter_by(case_number=row.code).first()
            if existing_case:
                logger.info(f"   ℹ️ 案件 {row.code} は既に存在します。スキップします。")
                case_map[row.code] = existing_case.case_id
                continue

            client_name_temp = f"{row.username1}家 相続"

            new_case = Case(
                case_number=row.code,
                client_name=client_name_temp,
                folder_path=getattr(
                    row, "folder_s_path", None
                ),  # カラムがない場合に備えてgetattr
                created_at=datetime.now(),
                current_status_id=1,
            )
            session.add(new_case)
            session.flush()  # ID発行

            case_map[row.code] = new_case.case_id

            # --- Deceased作成 ---
            new_deceased = Deceased(
                case_id=new_case.case_id,
                name_last=row.username1,
                name_first=row.username2,
                name_last_kana=getattr(row, "username1_hurigana", ""),
                name_first_kana=getattr(row, "username2_hurigana", ""),
                hometown=getattr(row, "domicile", ""),
                # date_of_death=... (日付パースが必要ならここで変換)
            )
            session.add(new_deceased)

        session.commit()

        # 5. データ移行: Heir(旧) -> Heir(新)
        logger.info("🔄 相続人データを移行中...")

        query_heir = select(t_heir_old)
        old_heirs = session.execute(query_heir).fetchall()

        for row in old_heirs:
            case_code = row.code
            if case_code not in case_map:
                continue

            case_id = case_map[case_code]

            # 親となるDeceasedを取得
            dec = session.query(Deceased).filter_by(case_id=case_id).first()
            if not dec:
                continue

            # 重複チェック（簡易的：名前で判断）
            full_name_last = row.username1 or ""
            full_name_first = row.username2 or ""

            exists = (
                session.query(Heir)
                .filter_by(
                    deceased_id=dec.id,
                    name_last=full_name_last,
                    name_first=full_name_first,
                )
                .first()
            )

            if exists:
                continue

            is_contractor = getattr(row, "offer", 0) == 1

            new_heir = Heir(
                deceased_id=dec.id,
                name_last=full_name_last,
                name_first=full_name_first,
                name_last_kana=getattr(row, "username1_hurigana", ""),
                name_first_kana=getattr(row, "username2_hurigana", ""),
                relationship_type=getattr(row, "relationship", ""),
                is_contracting_party=is_contractor,
                hometown=getattr(row, "domicile", ""),
                occupation=getattr(row, "job", ""),
            )
            session.add(new_heir)

            # 契約者ならCaseのclient_nameを更新
            if is_contractor:
                case_obj = session.query(Case).get(case_id)
                case_obj.client_name = f"{full_name_last} {full_name_first}"
                case_obj.client_name_kana = f"{getattr(row, 'username1_hurigana', '')} {getattr(row, 'username2_hurigana', '')}"

        session.commit()

        # 6. データ移行: BankCustomer -> FinancialAsset
        # 必要であればここに追加（前回のロジックと同様）
        # ...

        logger.info("✅ PostgreSQLデータ移行が正常に完了しました！")

    except Exception as e:
        session.rollback()
        logger.error(f"❌ 移行中にエラーが発生しました: {e}")
        import traceback

        logger.error(traceback.format_exc())
    finally:
        session.close()


def _seed_master_data(session):
    """初期マスタデータの投入"""
    # ステータス
    statuses = [
        (1, "受任・調査中"),
        (2, "書類作成中"),
        (3, "署名押印待ち"),
        (4, "申請中"),
        (5, "完了"),
        (9, "保留・中止"),
    ]
    for sid, sname in statuses:
        if not session.query(CaseStatus).get(sid):
            session.add(CaseStatus(id=sid, name=sname))

    # 口座種別
    ac_types = ["普通", "当座", "定期", "貯蓄", "外貨", "その他"]
    for at in ac_types:
        if not session.query(AccountTypeMaster).filter_by(type_name=at).first():
            session.add(AccountTypeMaster(type_name=at))

    session.commit()


if __name__ == "__main__":
    migrate_data()
