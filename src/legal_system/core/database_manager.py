# file: src/legal_system/core/database_manager.py

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from sqlalchemy import create_engine, desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

# テーブル定義
from src.legal_system.models.tables import (
    AuditLog,
    Base,
    Case,
    Coordinate,
    FileRegistry,
    User,
)

# Config
from .config import Config


# ==========================================
# エンジン生成の共通ロジック (キャッシュなし)
# ==========================================
def _create_new_engine() -> Engine:
    """
    SQLAlchemyエンジンを新規作成する内部関数。
    Streamlitへの依存を含みません。
    """
    # 【修正ポイント】 Windows環境での文字コードエラー(0x83)を防ぐため
    # client_encoding='utf8' を明示的に指定します。
    engine = create_engine(
        Config.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"client_encoding": "utf8"}  # Windows対策: 文字化けクラッシュ防止
    )

    # テーブル作成 (初回のみ)
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        # Streamlit環境下であればエラー表示、そうでなければ標準出力へ
        msg = f"❌ データベース接続エラー: {e}"
        # Watcherプロセスかどうかの判定
        if os.environ.get("IS_WATCHER_PROCESS") != "true":
            st.error(msg)
            st.info("PostgreSQLサーバー設定(.env)を確認してください。")
        else:
            print(msg)
        raise e

    return engine


# ==========================================
# Streamlit用 キャッシュ付きエンジン取得
# ==========================================
@st.cache_resource(show_spinner="データベースに接続中...")
def _get_cached_engine() -> Engine:
    """Streamlitのキャッシュ機能を利用してエンジンを保持する"""
    return _create_new_engine()


# ==========================================
# 公開アクセサ (環境判定ロジック付き)
# ==========================================
def get_db_engine() -> Engine:
    """
    実行環境に応じて適切なエンジン取得方法を選択するファクトリー関数。
    - Watcherプロセス (IS_WATCHER_PROCESS=true): キャッシュなしで新規作成
    - Streamlitアプリ: st.cache_resourceを利用して高速化
    """
    if os.environ.get("IS_WATCHER_PROCESS") == "true":
        # バックグラウンド処理ではStreamlitのキャッシュ機能を使わない
        return _create_new_engine()
    else:
        # UIスレッドではキャッシュを使う
        return _get_cached_engine()


class DatabaseManager:
    """
    データベース操作を一元管理するクラス。
    環境に応じたエンジン取得戦略を内部で自動解決します。
    """

    def __init__(self):
        # 環境判定済みのエンジン取得関数を呼び出し
        self.engine = get_db_engine()

        # セッションファクトリの作成
        self.session_factory = sessionmaker(bind=self.engine)

        # スレッドセーフなセッション
        self.Session = scoped_session(self.session_factory)

    def _get_session(self):
        """新しいセッションを発行"""
        return self.Session()

    # ---------------------------------------------------------
    # ユーザー管理
    # ---------------------------------------------------------
    def get_current_user_info(self) -> Dict[str, str]:
        """Windowsログインユーザー情報を取得または作成"""
        # Streamlit Cloud等でOSユーザーが取れない場合のフォールバック
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
                # 新規自動登録
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
            # user_id (windows_id) から内部IDを引く
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
    # ファイル管理
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
                file_reg.registered_at = datetime.now()
            else:
                file_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=filename,
                    doc_type=doc_type,
                    case_id=case_id,
                    registered_at=datetime.now(),
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
    # 座標管理 (Coordinate Tool)
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
                    # 必要に応じて他のフィールドも追加
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