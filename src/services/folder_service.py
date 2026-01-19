# src/services/folder_service.py

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional
import pyautogui

# サーバーの基準パス
SERVER_BASE_PATH = r"\\192.168.11.20\行政書士法人チェスター\01.個別ＪＯＢ"

def find_case_folder(search_term: str) -> Optional[str]:
    """
    基準パス配下からフォルダを検索してパスを返す。
    """
    if not search_term:
        return None

    target_path = Path(SERVER_BASE_PATH)
    if not target_path.exists():
        return None

    try:
        query = search_term.replace(" ", "").replace("　", "")
        for item in target_path.iterdir():
            if item.is_dir():
                folder_name = item.name.replace(" ", "").replace("　", "")
                if query in folder_name:
                    return str(item.absolute())
    except Exception as e:
        print(f"Folder search error: {e}")
        return None

def open_local_folder(path: str) -> bool:
    """
    指定されたパスをエクスプローラーで開き、かつ最前面に表示させる。
    """
    if not path or not os.path.exists(path):
        return False

    try:
        if platform.system() == "Windows":
            # --- Windows向けの最強最前面表示ロジック ---
            # 1. まず普通にエクスプローラーで開く
            os.startfile(path)
    
            # ウィンドウが開くまでの猶予（環境によるが0.5~1秒程度）
            # time.sleep(1) 

            pyautogui.hotkey('alt', 'tab')
            
        elif platform.system() == "Darwin": # Mac用
            subprocess.Popen(["open", path])
            subprocess.run(["osascript", "-e", f'tell application "Finder" to activate'])
        else: # Linux用
            subprocess.Popen(["xdg-open", path])
            
        return True
    except Exception as e:
        print(f"Error opening folder: {e}")
        return False