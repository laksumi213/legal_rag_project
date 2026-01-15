# src/services/folder_service.py
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

# サーバーの基準パス (Windowsのネットワークパス形式)
SERVER_BASE_PATH = r"\\192.168.11.20\行政書士法人チェスター\01.個別ＪＯＢ"

def find_case_folder(search_term: str) -> Optional[str]:
    """
    基準パス配下から、search_term (顧客名など) を含むフォルダを検索してパスを返す。
    """
    if not search_term:
        return None

    target_path = Path(SERVER_BASE_PATH)
    
    if not target_path.exists():
        # ローカルテスト用に一時フォルダをフォールバックとして設定する場合の例
        # target_path = Path(r"C:\TestFolder") 
        return None

    try:
        # 空白除去
        query = search_term.replace(" ", "").replace("　", "")
        # 直下のフォルダを走査
        for item in target_path.iterdir():
            if item.is_dir():
                folder_name = item.name.replace(" ", "").replace("　", "")
                if query in folder_name:
                    return str(item.absolute())
    except Exception as e:
        print(f"Folder search error: {e}")
        return None

def open_local_folder(path: str):
    """
    サーバー側(Streamlit実行環境)でフォルダを開く試み。
    クライアントPCで開くわけではない点に注意が必要ですが、社内LAN(オンプレ)なら機能する場合が多いです。
    """
    if not path or not os.path.exists(path):
        return False
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False