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

    print("🚀 Legal RAG System 起動中...")
    
    # Streamlitをメインプロセスとして即座に起動
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        # このプロセスが終了するまでブロック
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 システムを終了しました。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()