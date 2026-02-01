# src/legal_system/core/database_manager.py

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (  # Added relationship for eager loading
    relationship,
    scoped_session,
    sessionmaker,
)

# テーブル定義
from src.legal_system.models.tables import (
    AuditLog,
    Base,
    Case,
    Coordinate,
    Deceased,
    FileRegistry,
    FinancialAsset,
    Heir,
    User,
)

# Config
from .config import Config


# ==========================================
# エンジン生成の共通ロジック
# ==========================================
def _create_new_engine() -> Engine:
    """SQLAlchemyエンジンを新規作成する内部関数"""
    engine = create_engine(
        Config.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"client_encoding": "utf8"},
    )
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        msg = f"❌ データベース接続エラー: {e}"
        if os.environ.get("IS_WATCHER_PROCESS") != "true":
            try:
                import streamlit as st

                st.error(msg)
            except ImportError:
                print(msg)
        else:
            print(msg)
        raise e
    return engine


# ==========================================
# 公開アクセサ (環境判定ロジック付き)
# ==========================================
def get_db_engine() -> Engine:
    """
    実行環境に応じて適切なエンジン取得方法を選択する。
    - Watcherプロセス: Streamlitを無視して新規作成
    - Streamlitアプリ: st.cache_resourceを利用
    """
    if os.environ.get("IS_WATCHER_PROCESS") == "true":
        return _create_new_engine()
    else:
        try:
            import streamlit as st

            # キャッシュ衝突を避けるため、関数内部で定義
            @st.cache_resource(show_spinner="データベースに接続中...")
            def _get_cached_engine() -> Engine:
                return _create_new_engine()

            return _get_cached_engine()
        except ImportError:
            return _create_new_engine()


class DatabaseManager:
    def __init__(self):
        self.engine = get_db_engine()
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def _get_session(self):
        return self.Session()

    # ---------------------------------------------------------
    # ユーザー管理
    # ---------------------------------------------------------
    def get_current_user_info(self) -> Dict[str, str]:
        """Windowsログインユーザー情報を取得または作成"""
        pc_user = os.environ.get("USERNAME", "guest_user")

        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=pc_user).first()
            if user:
                return {
                    "id": user.windows_id,
                    "name": user.name,
                    "dept": user.department if user.department else "",
                    "phone": user.phone if user.phone else "",
                }
            else:
                default_name = f"{pc_user}"
                default_dept = "未設定"
                new_user = User(
                    windows_id=pc_user,
                    name=default_name,
                    department=default_dept,
                    role="Operator",
                )
                session.add(new_user)
                session.commit()
                return {
                    "id": pc_user,
                    "name": default_name,
                    "dept": default_dept,
                    "phone": "",
                }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {"id": pc_user, "name": pc_user, "dept": "Error", "phone": ""}
        finally:
            session.close()

    def register_user(
        self, windows_id: str, display_name: str, department: str, phone: str
    ):
        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=windows_id).first()
            if user:
                user.name = display_name
                user.department = department
                user.phone = phone
                user.updated_at = datetime.now()
            else:
                user = User(
                    windows_id=windows_id,
                    name=display_name,
                    department=department,
                    phone=phone,
                    role="Operator",
                )
                session.add(user)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------------------------------------------------------
    # ログ管理
    # ---------------------------------------------------------
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        session = self._get_session()
        try:
            db_user = session.query(User).filter_by(windows_id=user_id).first()
            u_id = db_user.id if db_user else None

            log = AuditLog(
                user_id=u_id,
                action_type=action,
                target=target,
                details=details,
                timestamp=datetime.now(),
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---------------------------------------------------------
    # ファイル管理 (FileRegistry)
    # ---------------------------------------------------------
    def is_file_registered(self, file_hash: str) -> bool:
        session = self._get_session()
        try:
            exists = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            return exists is not None
        finally:
            session.close()

    def register_file_hash(
        self,
        file_hash: str,
        filename: str,
        doc_type: str = "その他",
        case_id: Optional[int] = None,
        status: str = "CONFIRMED",  # デフォルトは確認済(手動アップロード等)
        ai_confidence: float = 0.0,
        extracted_data: str = None,
    ):
        session = self._get_session()
        try:
            file_reg = (
                session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            )
            if file_reg:
                file_reg.filename = filename
                file_reg.doc_type = doc_type
                if case_id is not None:
                    file_reg.case_id = case_id

                # 更新
                file_reg.status = status
                file_reg.extracted_data = extracted_data
                file_reg.registered_at = datetime.now()
            else:
                file_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=filename,
                    doc_type=doc_type,
                    case_id=case_id,
                    registered_at=datetime.now(),
                    status=status,
                    ai_confidence=ai_confidence,
                    extracted_data=extracted_data,
                )
                session.add(file_reg)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_files(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            results = (
                session.query(FileRegistry, Case)
                .outerjoin(Case, FileRegistry.case_id == Case.case_id)
                .order_by(desc(FileRegistry.registered_at))
                .all()
            )
            output = []
            for f, c in results:
                case_label = f"{c.case_number}" if c else "（共通雛形）"
                output.append(
                    {
                        "filename": f.filename,
                        "date": f.registered_at.strftime("%Y-%m-%d %H:%M:%S")
                        if f.registered_at
                        else "",
                        "hash": f.file_hash,
                        "type": f.doc_type if f.doc_type else "その他",
                        "case": case_label,
                        "doc_type": f.doc_type,
                        "uploaded_at": f.registered_at,
                        "status": f.status,
                        "ai_confidence": f.ai_confidence,
                    }
                )
            return output
        finally:
            session.close()

    def delete_file_registry(self, filename: str):
        session = self._get_session()
        try:
            session.query(FileRegistry).filter_by(filename=filename).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------------------------------------------------------
    # 座標管理
    # ---------------------------------------------------------
    def register_coordinate(
        self,
        file_hash,
        label,
        x,
        y,
        page_number=1,
        description="",
        font_size=10,
        color="black",
        test_value="",
    ):
        session = self._get_session()
        try:
            coord = (
                session.query(Coordinate)
                .filter_by(file_hash=file_hash, label=label)
                .first()
            )
            if not coord:
                coord = Coordinate(file_hash=file_hash, label=label)
                session.add(coord)

            coord.x_point = x
            coord.y_point = y
            coord.page_number = page_number
            coord.description = description
            coord.font_size = font_size
            coord.color = color
            coord.value = test_value
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def get_coordinates_by_hash(self, file_hash: str) -> List[Dict]:
        session = self._get_session()
        try:
            coords = session.query(Coordinate).filter_by(file_hash=file_hash).all()
            return [
                {
                    "id": c.id,
                    "label": c.label,
                    "x": c.x_point,
                    "y": c.y_point,
                    "page": c.page_number,
                    "desc": c.description,
                    "font_size": c.font_size,
                    "color": c.color,
                    "value": c.value,
                }
                for c in coords
            ]
        finally:
            session.close()

    def update_coordinate_direct(self, coord_id: int, updates: Dict):
        session = self._get_session()
        try:
            coord = session.query(Coordinate).filter_by(id=coord_id).first()
            if coord:
                for k, v in updates.items():
                    if k == "x":
                        coord.x_point = v
                    elif k == "y":
                        coord.y_point = v
                    elif k == "desc":
                        coord.description = v
                    elif hasattr(coord, k):
                        setattr(coord, k, v)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def delete_coordinate(self, coordinate_id: int):
        session = self._get_session()
        try:
            session.query(Coordinate).filter_by(id=coordinate_id).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    # ---------------------------------------------------------
    # 案件・資産情報取得
    # ---------------------------------------------------------
    def get_all_cases(self) -> List[Case]:
        session = self._get_session()
        try:
            return session.query(Case).order_by(desc(Case.created_at)).all()
        finally:
            session.close()

    def get_case_with_details(self, case_id: int) -> Optional[Case]:
        session = self._get_session()
        try:
            return (
                session.query(Case)
                .filter(Case.case_id == case_id)
                .outerjoin(Deceased)
                .outerjoin(Heir)
                .first()
            )
        finally:
            session.close()

    def get_financial_assets_by_case_id(self, case_id: int) -> List[FinancialAsset]:
        session = self._get_session()
        try:
            return (
                session.query(FinancialAsset)
                .filter(FinancialAsset.case_id == case_id)
                .options(  # eager loading
                    relationship(FinancialAsset.bank_ref),
                    relationship(FinancialAsset.branch_ref),
                    relationship(FinancialAsset.account_type_ref),
                )
                .all()
            )
        finally:
            session.close()

    def get_financial_asset_details(
        self, financial_asset_id: int
    ) -> Optional[FinancialAsset]:
        session = self._get_session()
        try:
            return (
                session.query(FinancialAsset)
                .filter(FinancialAsset.id == financial_asset_id)
                .options(
                    relationship(FinancialAsset.bank_ref),
                    relationship(FinancialAsset.branch_ref),
                    relationship(FinancialAsset.account_type_ref),
                    relationship(FinancialAsset.case_ref),
                )
                .first()
            )
        finally:
            session.close()

    def get_file_registry_by_hash(self, file_hash: str) -> Optional[FileRegistry]:
        session = self._get_session()
        try:
            return (
                session.query(FileRegistry)
                .filter(FileRegistry.file_hash == file_hash)
                .first()
            )
        finally:
            session.close()
