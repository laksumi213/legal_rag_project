# src/legal_system/main.py

import subprocess
import sys
from pathlib import Path

def main():
    """
    Streamlitアプリを最優先で起動するランチャー。
    監視プロセス(Watcher)の起動は、Home.pyのバックグラウンド処理に移譲されました。
    """
    current_dir = Path(__file__).parent.absolute()
    app_path = current_dir / "ui" / "Home.py"

    print("Legal RAG System 起動中...", flush=True)
    
    # Streamlitをメインプロセスとして即座に起動
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    if args:
        cmd.extend(args)

    try:
        print("EXEC:", " ".join(cmd), flush=True)
        # このプロセスが終了するまでブロック (Streamlitが常駐するため通常は戻らない)
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nシステムを終了しました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()