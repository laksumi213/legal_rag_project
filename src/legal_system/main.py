# ファイルパス: src/legal_system/main.py

import subprocess
import sys
from pathlib import Path


def main():
    """
    Streamlitアプリとフォルダ監視(Watcher)を同時に起動するランチャー
    """
    current_dir = Path(__file__).parent.absolute()
    app_path = current_dir / "ui" / "Home.py"

    # プロジェクトルートにある run_watcher.py のパス
    # src/legal_system/main.py -> src/legal_system -> src -> root
    root_dir = current_dir.parent.parent
    watcher_path = root_dir / "run_watcher.py"

    print("🚀 Legal RAG System を起動します...")

    # 1. 監視プロセスをバックグラウンドで起動
    watcher_process = None
    if watcher_path.exists():
        print("👀 フォルダ監視(Watcher)を開始します...")
        watcher_process = subprocess.Popen([sys.executable, str(watcher_path)])
    else:
        print("⚠️ run_watcher.py が見つからないため、監視機能はスキップします。")

    # 2. Streamlitをメインプロセスとして起動 (これが終わるまで待機)
    print(f"📂 UI起動: {app_path}")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 システムを終了します。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        # アプリが終了したら、監視プロセスも終了させる
        if watcher_process:
            print("🛑 監視プロセスを停止中...")
            watcher_process.terminate()
            watcher_process.wait()
            print("✅ 完了")


if __name__ == "__main__":
    main()
