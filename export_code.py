import subprocess


def run_repomix():
    print("🚀 ソースコードの集約を開始します...")

    # Repomixを実行するコマンド
    # --style markdown : Geminiが読みやすいマークダウン形式で出力
    # --ignore "**/*.json,**/*.lock" : 不要なファイルを除外（必要に応じて追加）
    command = "npx -y repomix --style markdown"

    try:
        # コマンドを実行
        # shell=True はWindows/Mac両対応のため
        subprocess.run(command, shell=True, check=True)

        print("\n✅ 完了しました！")
        print("📁 'repomix-output.md' というファイルが作成されています。")
        print("🤖 これをGeminiにアップロードしてください。")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    run_repomix()
