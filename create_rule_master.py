import json
from typing import Any, Dict, List

# プロジェクトルートに作成される手続要件マスタ
DATA_FILE: str = "bank_master.json"


def create_initial_bank_data() -> List[Dict[str, Any]]:
    """
    行政書士業務に特化した銀行マスタデータの初期セットを生成する。
    """
    banks = [
        {
            "bank_name": "三菱UFJ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "遺産分割協議書（実印押印）",
                "相続人全員の印鑑証明書（6ヶ月以内）",
                "被相続人の出生から死亡までの連続した戸籍謄本",
                "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
                "【代理人】行政書士証票のコピー（原本照合済）",
                "【代理人】委任状（銀行所定様式または実印押印のある任意様式）",
            ],
            "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
            "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）",
        },
        {
            "bank_name": "ゆうちょ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続確認表（Web入力可）",
                "貯金等相続手続請求書（代理人による署名・実印）",
                "【代理人】特定事務任用カード（提示のみ）",
                "【代理人】委任状（実印押印必須）",
            ],
            "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
            "original_return_policy": "原則として原本還付可。コピーの提出が必要。",
        },
        {
            "bank_name": "三井住友銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続手続依頼書（代理人署名）",
                "【代理人】実印および印鑑証明書（6ヶ月以内）",
                "【代理人】行政書士証票または識別カード",
                "被相続人の全戸籍（出生〜死亡）",
            ],
            "notes": "※Web予約をしてからの来店が推奨される。",
            "original_return_policy": "原本還付可",
        },
    ]
    return banks


def save_bank_master(data: List[Dict[str, Any]]) -> None:
    try:
        # プロジェクトルートに保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 成功: '{DATA_FILE}' を作成しました。")
        print("   これで『01_銀行手続要件_確認』ページが動作します。")
    except IOError as e:
        print(f"❌ エラー: ファイルの書き込みに失敗しました。詳細: {e}")


if __name__ == "__main__":
    bank_data = create_initial_bank_data()
    save_bank_master(bank_data)
