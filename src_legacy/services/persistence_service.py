import json
import logging
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# パス解決とインポート
try:
    # あなたの既存のtables.pyを利用
    from src.legal_system.models.tables import (
        AuditLog,
        BankMaster,
        Base,
        Case,
        FinancialAsset,
        User,
    )
except ImportError:
    import sys
    from pathlib import Path

    # ルートディレクトリをパスに追加して再試行
    sys.path.append(str(Path(__file__).resolve().parents[3]))
    from src.legal_system.models.tables import (
        AuditLog,
        BankMaster,
        Base,
        Case,
        FinancialAsset,
    )

from src.legal_system.core.schemas import DocumentAnalysisResult

# DB接続先 (configから読み込むのが理想ですが、今回は直接指定)
# ※ tables.py が想定しているDBに合わせてください (SQLite/PostgreSQL)
DB_URL = "sqlite:///./data/db/legal_system.db"


class PersistenceDatabaseManager:
    """保存処理専用のDB接続クラス"""

    def __init__(self):
        self.engine = create_engine(DB_URL, echo=False)
        # テーブルが存在しない場合は作成（既存テーブルは消えません）
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        return self.SessionLocal()


class VerificationPersistenceService:
    """
    AIの解析結果を、既存の複雑なリレーションを持つDBに安全に保存するサービス
    """

    def __init__(self):
        self.db = PersistenceDatabaseManager()

    def _get_or_create_bank(self, session: Session, bank_name_raw: str) -> BankMaster:
        """
        AIが読み取った銀行名からマスタIDを特定する。
        完全一致しなければ、新規マスタとして登録してしまう（運用回避策）。
        """
        # 1. 完全一致検索
        bank = (
            session.query(BankMaster)
            .filter(BankMaster.bank_name == bank_name_raw)
            .first()
        )
        if bank:
            return bank

        # 2. 部分一致検索 (例: '三菱UFJ' で '三菱UFJ銀行' を当てる)
        # 実際の運用では BankAlias テーブルを使うべきですが、今回は簡易実装
        bank = (
            session.query(BankMaster)
            .filter(BankMaster.bank_name.like(f"%{bank_name_raw}%"))
            .first()
        )
        if bank:
            return bank

        # 3. 見つからない場合は新規作成 (Unknown扱い)
        # codeはダミーで発行
        new_bank = BankMaster(bank_name=bank_name_raw, bank_code="9999")
        session.add(new_bank)
        session.flush()  # ID確定
        return new_bank

    def save_analysis_result(
        self, case_id: int, result: DocumentAnalysisResult, filename: str
    ):
        """
        解析結果を保存するメインメソッド
        """
        session = self.db.get_session()
        try:
            # -------------------------------------------------------
            # 1. 案件(Case)の存在確認
            # -------------------------------------------------------
            case_record = session.query(Case).filter(Case.case_id == case_id).first()
            if not case_record:
                # 案件がないと保存できないためエラーにするか、ダミーを作る
                # ここではデモ用にダミー作成
                case_record = Case(
                    case_id=case_id,
                    case_number=f"G{case_id:04d}",
                    client_name="デモ 依頼者",
                    client_name_kana="デモ イライシャ",
                )
                session.add(case_record)
                session.flush()

            # -------------------------------------------------------
            # 2. 監査ログ(AuditLog)の保存
            # -------------------------------------------------------
            # tables.py の定義に合わせて JSON を文字列化
            details_json = json.dumps(
                result.model_dump(mode="json"), ensure_ascii=False
            )

            # 既存の AuditLog は user_id 必須かもしれませんが、nullableを確認して設定
            # ここでは必要最低限のカラムを埋めます
            audit = AuditLog(
                action_type="AI_VERIFICATION",
                target=filename,
                details=details_json,  # Text型
                timestamp=datetime.now(),
                # user_id = current_user_id # ログイン機能があれば設定
            )
            session.add(audit)

            # -------------------------------------------------------
            # 3. 資産(FinancialAsset)の保存
            # -------------------------------------------------------
            saved_count = 0
            if result.assets:
                for asset in result.assets:
                    # 銀行マスタのID解決 (名前 -> ID)
                    bank_record = self._get_or_create_bank(
                        session, asset.bank_name.value
                    )

                    # FinancialAssetの作成
                    f_asset = FinancialAsset(
                        case_id=case_record.case_id,
                        bank_id=bank_record.id,
                        # bank_codeなどの重複情報は正規化により不要だが、
                        # テーブル定義に合わせて必要な情報を埋める
                        account_number=asset.account_number.value
                        if asset.account_number
                        else "不明",
                        balance=float(asset.balance) if asset.balance else 0.0,
                        # AI判定結果をstatusに入れる
                        status="pending_ai",
                        # 支店や種別は今回AIが取れていれば入れる (なければNULL)
                        # branch_id = ...
                        # account_type_id = ...
                    )
                    session.add(f_asset)
                    saved_count += 1

            session.commit()
            return True, f"保存完了: 資産{saved_count}件を登録しました。"

        except Exception as e:
            session.rollback()
            logging.error(f"DB Save Error: {e}")
            return False, f"システムエラー: {str(e)}"
        finally:
            session.close()
