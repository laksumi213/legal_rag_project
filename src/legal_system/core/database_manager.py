# src/legal_system/core/database_manager.py

import getpass
import os
from datetime import datetime
from typing import Dict, List

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import scoped_session, sessionmaker

# 設定とモデルの読み込み
from legal_system.core.config import DB_FILE_SQLITE
from legal_system.models.tables import AuditLog, Base, Coordinate, FileRegistry, User


class DatabaseManager:
    """
    システムのデータベース操作を一元管理するクラス
    SQLAlchemyを使用し、User, AuditLog, FileRegistry, Coordinate等のテーブルを操作します。
    """

    def __init__(self):
        """データベース接続の初期化とテーブル作成"""
        # データベース保存先のディレクトリを作成
        db_dir = os.path.dirname(DB_FILE_SQLITE)
        os.makedirs(db_dir, exist_ok=True)

        # SQLiteエンジン作成 (check_same_thread=FalseはStreamlitでのマルチスレッド対策)
        self.engine = create_engine(
            f"sqlite:///{DB_FILE_SQLITE}", connect_args={"check_same_thread": False}
        )

        # テーブルが存在しない場合は作成 (tables.pyの定義に基づく)
        Base.metadata.create_all(self.engine)

        # セッションファクトリの作成
        self.session_factory = sessionmaker(bind=self.engine)
        # スレッドセーフなセッション管理
        self.Session = scoped_session(self.session_factory)

    def _get_session(self):
        """セッションを取得する内部ヘルパー"""
        return self.Session()

    # ==========================================
    # ユーザー管理機能 (User)
    # ==========================================
    def get_current_user_info(self) -> Dict[str, str]:
        """
        現在のPCログインユーザー情報を取得する。
        DBに登録がなければ仮登録を行う。
        """
        pc_user = getpass.getuser()
        session = self._get_session()

        try:
            # windows_id (PCユーザー名) で検索
            user = session.query(User).filter_by(windows_id=pc_user).first()

            if user:
                return {
                    "id": user.windows_id,
                    "name": user.name,
                    "dept": user.department if user.department else "",
                    "phone": user.phone if user.phone else "",
                }
            else:
                # 未登録時は初期値を作成して保存
                default_name = f"{pc_user}(未登録)"
                default_dept = "所属未定"

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
        """ユーザー情報を登録・更新する"""
        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=windows_id).first()
            if user:
                # 更新
                user.name = display_name
                user.department = department
                user.phone = phone
                user.updated_at = datetime.now()
            else:
                # 新規作成
                user = User(
                    windows_id=windows_id,
                    name=display_name,
                    department=department,
                    phone=phone,
                    role="Operator",
                )
                session.add(user)
            session.commit()
        except Exception as e:
            print(f"Error registering user: {e}")
            session.rollback()
        finally:
            session.close()

    # ==========================================
    # 監査ログ機能 (AuditLog)
    # ==========================================
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        """操作ログを記録する"""
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
        except Exception as e:
            print(f"Error logging action: {e}")
            session.rollback()
        finally:
            session.close()

    # ==========================================
    # ファイル管理機能 (FileRegistry)
    # ==========================================
    def is_file_registered(self, file_hash: str) -> bool:
        """指定されたハッシュ値のファイルが既に登録されているか確認"""
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
        case_id: int = None,
    ):
        """ファイルの登録情報を保存・更新"""
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
        except Exception as e:
            print(f"Error registering file: {e}")
            session.rollback()
        finally:
            session.close()

    def get_all_files(self) -> List[Dict[str, str]]:
        """登録済みファイル一覧を取得 (案件情報も含める)"""
        session = self._get_session()
        try:
            # 循環参照回避のためメソッド内でインポート
            from legal_system.models.tables import Case, FileRegistry

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
                        "case": case_label,  # 表示用に案件番号を追加
                    }
                )
            return output
        finally:
            session.close()

    def delete_file_registry(self, filename: str):
        """ファイル登録情報を削除"""
        session = self._get_session()
        try:
            session.query(FileRegistry).filter_by(filename=filename).delete()
            session.commit()
        except Exception as e:
            print(f"Error deleting file registry: {e}")
            session.rollback()
        finally:
            session.close()

    # ==========================================
    # 座標管理機能 (Coordinate)
    # ==========================================
    def register_coordinate(
        self,
        file_hash: str,
        label: str,
        x: float,
        y: float,
        page_number: int = 1,
        description: str = "",
        font_size: int = 10,
        color: str = "black",
        test_value: str = "",
    ):
        """PDFの座標を登録（ファイルハッシュで区別）"""
        session = self._get_session()
        try:
            # 「同じファイル」かつ「同じラベル」なら更新
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
        except Exception as e:
            print(f"Error registering coordinate: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_coordinates_by_hash(self, file_hash: str) -> List[Dict]:
        """指定したファイルに関連する座標のみ取得"""
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
        """リストで直接編集された内容をDBに反映"""
        session = self._get_session()
        try:
            coord = session.query(Coordinate).filter_by(id=coord_id).first()
            if coord:
                if "label" in updates:
                    coord.label = updates["label"]
                if "x" in updates:
                    coord.x_point = updates["x"]
                if "y" in updates:
                    coord.y_point = updates["y"]
                if "font_size" in updates:
                    coord.font_size = updates["font_size"]
                if "color" in updates:
                    coord.color = updates["color"]
                if "desc" in updates:
                    coord.description = updates["desc"]
                if "value" in updates:
                    coord.value = updates["value"]
                session.commit()
                return True
            return False
        except Exception as e:
            print(f"Update error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_coordinate(self, coordinate_id: int):
        """指定されたIDの座標データを削除する"""
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
