import os
import sys
import subprocess
from pathlib import Path

def main():
    """
    アプリケーションの起動エントリーポイント
    Ryeなどの環境下でStreamlitを正しくサブプロセスとして起動します。
    """
    # 現在のファイルのディレクトリを取得
    current_dir = Path(__file__).parent.absolute()
    
    # UIファイル(app.py)のパスを特定
    app_path = current_dir / "ui" / "app.py"
    
    print(f"🚀 Legal RAG System を起動します...")
    print(f"📂 UI Path: {app_path}")

    # streamlit run コマンドを構築
    # sys.executable を使うことで、現在の仮想環境(Rye)のPythonを使用する
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    
    # 追加の引数があれば渡す
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        # サブプロセスとしてStreamlitを実行
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 システムを終了します。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
