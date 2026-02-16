# src/services/folder_service.py

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, List
import pyautogui

# サーバーの基準パス
SERVER_BASE_PATH = r"\\192.168.11.20\行政書士法人チェスター\01.個別ＪＯＢ"

def find_case_folder(search_term: str) -> Optional[str]:
    """
    基準パス配下からフォルダを検索して、最初に見つかったパスを返す（既存互換用）。
    """
    results = find_all_case_folders(search_term)
    return results[0] if results else None

def find_all_case_folders(search_term: str) -> List[str]:
    """
    基準パス配下から検索条件に一致するフォルダを全て探し、リストで返す。
    """
    if not search_term:
        return []

    target_path = Path(SERVER_BASE_PATH)
    if not target_path.exists():
        return []

    hits = []
    try:
        # 空白除去してマッチング
        query = search_term.replace(" ", "").replace("　", "")
        
        for item in target_path.iterdir():
            if item.is_dir():
                # フォルダ名も空白除去して比較
                folder_name_clean = item.name.replace(" ", "").replace("　", "")
                if query in folder_name_clean:
                    hits.append(str(item.absolute()))
                    
    except Exception as e:
        print(f"Folder search error: {e}")
        return []
    
    return hits

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