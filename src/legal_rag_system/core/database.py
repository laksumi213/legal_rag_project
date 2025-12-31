# src/legal_rag_system/core/database.py

import getpass
import os
import sqlite3
from datetime import datetime
from typing import Dict

# パス設定（config.pyに依存せず自己解決するように記述）
# プロジェクトルート/db/sql/audit_log.db を指す
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
DB_FILE_SQLITE = os.path.join(BASE_DIR, "db", "sql", "audit_log.db")


class DatabaseManager:
    """
    SQLiteを使用した監査ログ、ユーザー管理、ファイル重複チェックを行うクラス
    """

    def __init__(self):
        """データベース接続の初期化とテーブル作成"""
        os.makedirs(os.path.dirname(DB_FILE_SQLITE), exist_ok=True)
        # check_same_thread=FalseはStreamlitのマルチスレッド対策
        self.conn = sqlite3.connect(DB_FILE_SQLITE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """必要なテーブルが存在しない場合に作成する"""
        cur = self.conn.cursor()

        # 1. ユーザー管理テーブル (電話番号 phone を追加)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                pc_username TEXT PRIMARY KEY,
                display_name TEXT,
                department TEXT,
                phone TEXT,
                updated_at TEXT
            )
        """)

        # 2. 監査ログテーブル
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_id TEXT,
                action_type TEXT,
                target TEXT,
                details TEXT
            )
        """)

        # 3. ファイルハッシュ管理テーブル (重複防止用)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS file_registry (
                file_hash TEXT PRIMARY KEY,
                filename TEXT,
                registered_at TEXT
            )
        """)
        self.conn.commit()

    # --- ユーザー管理 ---
    def get_current_user_info(self) -> Dict[str, str]:
        """
        PCのログインユーザー名を取得し、DB登録情報を返す
        """
        pc_user = getpass.getuser()
        cur = self.conn.cursor()

        # カラム追加に対応するため phone も取得
        try:
            cur.execute(
                "SELECT display_name, department, phone FROM users WHERE pc_username = ?",
                (pc_user,),
            )
            res = cur.fetchone()
        except sqlite3.OperationalError:
            # カラム不足エラーなどの場合（旧DBなど）、一度Noneを返して再構築を促すなどの処理も可能だが
            # ここでは簡易的に未登録扱いにする
            res = None

        if res:
            return {
                "id": pc_user,
                "name": res[0],
                "dept": res[1],
                "phone": res[2] if res[2] else "",
            }
        else:
            # 未登録ユーザーの初期化
            default_name = f"{pc_user}(未登録)"
            default_dept = "所属未定"
            self.register_user(pc_user, default_name, default_dept, "")
            return {
                "id": pc_user,
                "name": default_name,
                "dept": default_dept,
                "phone": "",
            }

    def register_user(
        self, pc_username: str, display_name: str, department: str, phone: str
    ):
        """ユーザー情報の登録・更新"""
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            """
            INSERT OR REPLACE INTO users (pc_username, display_name, department, phone, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (pc_username, display_name, department, phone, now),
        )
        self.conn.commit()

    # --- ログ管理 ---
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        """操作ログを記録する"""
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute(
            """
            INSERT INTO audit_logs (timestamp, user_id, action_type, target, details)
            VALUES (?, ?, ?, ?, ?)
        """,
            (now, user_id, action, target, details),
        )
        self.conn.commit()

    # --- ファイル重複チェック ---
    def is_file_registered(self, file_hash: str) -> bool:
        """指定されたハッシュ値のファイルが既に登録されているか確認"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT filename FROM file_registry WHERE file_hash = ?", (file_hash,)
        )
        return cur.fetchone() is not None

    def register_file_hash(self, file_hash: str, filename: str):
        """ファイルのハッシュ値を登録"""
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            INSERT OR REPLACE INTO file_registry (file_hash, filename, registered_at)
            VALUES (?, ?, ?)
        """,
            (file_hash, filename, now),
        )
        self.conn.commit()
