import os
import datetime

# 監視対象のパス
NAS_PATH = r"\\192.168.11.20\行政書士法人チェスター\08.その他\スキャン"
TEST_FILE = os.path.join(NAS_PATH, "PYTHON_CONNECTION_TEST.txt")

print(f"🔍 書き込みテスト開始: {NAS_PATH}")

try:
    if not os.path.exists(NAS_PATH):
        print("❌ フォルダが見つかりません。")
    else:
        # テストファイルを作成
        with open(TEST_FILE, "w", encoding="utf-8") as f:
            f.write(f"接続テスト成功: {datetime.datetime.now()}\n")
            f.write("このファイルが見えれば、場所は合っています。")
        
        print("✅ ファイル書き込みに成功しました！")
        print(f"📁 作成ファイル: {TEST_FILE}")
        print("\n👉 エクスプローラーでこのフォルダを開き、")
        print("   'PYTHON_CONNECTION_TEST.txt' があるか確認してください。")

except Exception as e:
    print(f"❌ 書き込み失敗: {e}")
    print("   権限がないか、パスが間違っています。")