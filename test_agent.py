# test_agent.py
import os

from src.legal_system.core.ai_processor import AgenticDocumentProcessor

# 1. テスト用のダミーKintoneデータ（期待値）
mock_kintone_data = {
    "record_id": "TEST-001",
    "顧客名": "山田 太郎",
    "住所": "東京都千代田区千代田1-1",
    "被相続人名": "山田 父郎",  # 書類には「山田 父郎」と書いてあるはず
    "相続開始日": "2024-01-01",
}


def main():
    # 2. テスト対象のPDFを読み込む
    file_path = "sample.pdf"  # テストしたいPDFファイル名を指定

    if not os.path.exists(file_path):
        print(f"エラー: {file_path} が見つかりません。テスト用のPDFを置いてください。")
        # PDFがない場合、ダミーバイト列で強引にテスト（エラーにはなりますが通信は確認できます）
        dummy_bytes = b"%PDF-1.4..."
    else:
        with open(file_path, "rb") as f:
            dummy_bytes = f.read()

    print(f"--- AIエージェント起動 (Mode: {os.getenv('AI_PROVIDER')}) ---")
    print("書類を解析中... (10~20秒かかります)")

    # 3. プロセッサの初期化と実行
    processor = AgenticDocumentProcessor()

    try:
        result = processor.analyze_document(
            file_bytes=dummy_bytes,
            mime_type="application/pdf",
            kintone_data=mock_kintone_data,
        )

        # 4. 結果の表示
        print("\n=== 解析成功 ===")
        print(f"書類タイプ: {result.document_type}")
        print(f"総合判定: {result.overall_status}")

        if result.deceased_info:
            print(f"被相続人名(抽出): {result.deceased_info.name_full.value}")
            print(f"一致判定: {result.deceased_info.name_full.meta.is_consistent}")
            if not result.deceased_info.name_full.meta.is_consistent:
                print(
                    f"不一致理由: {result.deceased_info.name_full.meta.discrepancy_reason}"
                )

        # JSON全体を表示
        print("\n--- Raw JSON Output ---")
        print(result.model_dump_json(indent=2))

    except Exception as e:
        print(f"\nエラーが発生しました: {e}")


if __name__ == "__main__":
    main()
