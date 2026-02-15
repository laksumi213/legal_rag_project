# src/legal_system/ui/pages/99_マスタ管理.py

import json
import os
import streamlit as st
import pandas as pd

st.set_page_config(page_title="マスタ管理", page_icon="⚙️", layout="wide")

# パス設定 (smart_guide.pyと同じ場所を参照)
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
RULES_DIR = os.path.join(ROOT_DIR, "data", "rules")
GUIDE_FILE = os.path.join(RULES_DIR, "bank_guidance.json")

def main():
    st.title("⚙️ 業務ナビ・マスタ設定")
    st.markdown("口座入力画面などで表示される「銀行ごとの注意点」を編集できます。")

    # データの読み込み
    current_data = {}
    if os.path.exists(GUIDE_FILE):
        with open(GUIDE_FILE, "r", encoding="utf-8") as f:
            current_data = json.load(f)

    # 編集しやすいようにリスト形式に変換
    # [{"銀行名": "三菱", "注意文": "...", "詳細": "..."}]
    table_data = []
    for bank, info in current_data.items():
        items_str = "\n".join(info.get("items", []))
        table_data.append({
            "銀行名キーワード": bank,
            "重要アラート(赤枠)": info.get("alert", ""),
            "詳細リスト(改行区切り)": items_str
        })
    
    # 既存データがない場合のダミー
    if not table_data:
        table_data = [{"銀行名キーワード": "例：みずほ", "重要アラート(赤枠)": "注意点", "詳細リスト(改行区切り)": "詳細A\n詳細B"}]

    df = pd.DataFrame(table_data)

    # データエディター（Excelライクな編集画面）
    edited_df = st.data_editor(
        df,
        num_rows="dynamic", # 行の追加・削除を許可
        use_container_width=True,
        column_config={
            "詳細リスト(改行区切り)": st.column_config.TextColumn(width="large")
        }
    )

    if st.button("💾 設定を保存して反映", type="primary"):
        # 保存形式(JSON)に戻す
        new_json = {}
        for index, row in edited_df.iterrows():
            key = row["銀行名キーワード"]
            if not key: continue
            
            alert = row["重要アラート(赤枠)"]
            items_raw = row["詳細リスト(改行区切り)"]
            items = [x.strip() for x in items_raw.split("\n") if x.strip()]
            
            new_json[key] = {
                "alert": alert,
                "items": items
            }
        
        # ファイル書き込み
        os.makedirs(RULES_DIR, exist_ok=True)
        with open(GUIDE_FILE, "w", encoding="utf-8") as f:
            json.dump(new_json, f, ensure_ascii=False, indent=2)
        
        st.success("✅ 保存しました！「預貯金口座入力フォーム」で即座に反映されます。")

if __name__ == "__main__":
    main()