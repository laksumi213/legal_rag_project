# src/legal_rag_system/core/database.py

import getpass
import os
import sqlite3
from datetime import datetime
from typing import Dict, List

# プロジェクトのルートディレクトリを特定
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
# データベースファイルのパス
DB_FILE_SQLITE = os.path.join(BASE_DIR, "db", "sql", "audit_log.db")


class DatabaseManager:
    """
    SQLiteを使用した監査ログ、ユーザー管理、ファイル管理を行うクラス
    """

    def __init__(self):
        """データベース接続の初期化とテーブル作成"""
        # フォルダがなければ作成
        os.makedirs(os.path.dirname(DB_FILE_SQLITE), exist_ok=True)
        # SQLite接続 (check_same_thread=FalseはStreamlit対策)
        self.conn = sqlite3.connect(DB_FILE_SQLITE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        """必要なテーブルを作成"""
        cur = self.conn.cursor()

        # 1. ユーザー管理テーブル
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

        # 3. ファイル管理テーブル (重複チェック & 書類種別用)
        # 【変更】doc_type カラムを追加
        cur.execute("""
            CREATE TABLE IF NOT EXISTS file_registry (
                file_hash TEXT PRIMARY KEY,
                filename TEXT,
                doc_type TEXT,
                registered_at TEXT
            )
        """)
        self.conn.commit()

    # ==========================================
    # ユーザー管理機能
    # ==========================================
    def get_current_user_info(self) -> Dict[str, str]:
        """現在のPCログインユーザー情報を取得"""
        pc_user = getpass.getuser()
        cur = self.conn.cursor()
        try:
            cur.execute(
                "SELECT display_name, department, phone FROM users WHERE pc_username = ?",
                (pc_user,),
            )
            res = cur.fetchone()
        except:
            res = None

        if res:
            return {
                "id": pc_user,
                "name": res[0],
                "dept": res[1],
                "phone": res[2] if res[2] else "",
            }
        else:
            # 未登録時は初期値を作成
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
        """ユーザー情報を登録・更新"""
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

    # ==========================================
    # 監査ログ機能
    # ==========================================
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        """操作ログを記録"""
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

    # ==========================================
    # ファイル管理機能
    # ==========================================
    def is_file_registered(self, file_hash: str) -> bool:
        """指定されたハッシュ値のファイルが既に登録されているか確認"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT filename FROM file_registry WHERE file_hash = ?", (file_hash,)
        )
        return cur.fetchone() is not None

    def register_file_hash(
        self, file_hash: str, filename: str, doc_type: str = "その他"
    ):
        """【変更】ファイルのハッシュ値と書類種別を登録"""
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            """
            INSERT OR REPLACE INTO file_registry (file_hash, filename, doc_type, registered_at)
            VALUES (?, ?, ?, ?)
        """,
            (file_hash, filename, doc_type, now),
        )
        self.conn.commit()

    def get_all_files(self) -> List[Dict[str, str]]:
        """【変更】登録済みファイル一覧を取得 (doc_type含む)"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT filename, registered_at, file_hash, doc_type FROM file_registry ORDER BY registered_at DESC"
        )
        return [
            {
                "filename": r[0],
                "date": r[1],
                "hash": r[2],
                "type": r[3] if r[3] else "その他",
            }
            for r in cur.fetchall()
        ]

    def delete_file_registry(self, filename: str):
        """ファイル登録情報を削除"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM file_registry WHERE filename = ?", (filename,))
        self.conn.commit()
