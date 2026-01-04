import json
import os
import sys
from typing import Any, Dict, List, Optional

import streamlit as st

# --- パス解決 (srcフォルダへのパスを通す) ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src
SRC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
ROOT_DIR = os.path.dirname(SRC_DIR)
sys.path.append(SRC_DIR)

# 定数設定 (プロジェクトルート直下の data/bank_master.json)
DATA_FILE = os.path.join(ROOT_DIR, "bank_master.json")

# ページ設定
st.set_page_config(
    page_title="銀行手続要件確認 | 相続業務支援システム", page_icon="🏦", layout="wide"
)


def load_bank_master() -> List[Dict[str, Any]]:
    """銀行マスタJSONを読み込む"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        st.error("データの形式が不正です。管理者に連絡してください。")
        return []


def display_agent_warning() -> None:
    """行政書士補助者向けの注意喚起"""
    st.warning(
        "【重要】この画面は「行政書士が代理人として行う場合」の要件を表示しています。\n"
        "相続人本人が窓口に行く場合とは必要書類が異なるため、必ず委任状の要件を確認してください。",
        icon="⚠️",
    )


def main() -> None:
    st.title("🏦 銀行手続要件・必要書類確認")
    st.caption("各銀行の「代理人手続き」に関する特記事項を確認します。")

    display_agent_warning()

    # データのロード
    banks: List[Dict[str, Any]] = load_bank_master()

    if not banks:
        st.error(
            f"⚠️ 銀行データファイル（bank_master.json）が見つかりません。\n"
            f"参照パス: {DATA_FILE}\n\n"
            "以下の手順を実行してください：\n"
            "1. プロジェクトルートで `python update_bank_master.py` を実行"
        )
        return

    # 銀行選択セレクトボックス
    bank_names: List[str] = [b["bank_name"] for b in banks]
    selected_bank_name: Optional[str] = st.selectbox(
        "確認したい金融機関を選択してください",
        options=bank_names,
        index=None,
        placeholder="銀行を選択...",
    )

    if selected_bank_name:
        # 選択された銀行データを取得
        selected_data: Optional[Dict[str, Any]] = next(
            (b for b in banks if b["bank_name"] == selected_bank_name), None
        )

        if selected_data:
            st.divider()

            # メイン情報の表示
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader(f"📂 {selected_data['bank_name']} の手続要件")
                st.info(f"区分: {selected_data.get('procedure_type', '不明')}")

                st.markdown("#### 📄 必要書類リスト")
                for doc in selected_data.get("required_documents", []):
                    # 代理人特有の書類は太字で強調
                    if "委任状" in doc or "印鑑証明" in doc or "行政書士" in doc:
                        st.markdown(f"- **{doc}** 👈 Check")
                    else:
                        st.markdown(f"- {doc}")

            with col2:
                st.markdown("#### 💡 代理人特記事項")
                st.caption(selected_data.get("notes", "特記事項なし"))

                st.markdown("#### ↩️ 原本還付の方針")
                st.success(selected_data.get("original_return_policy", "要確認"))

            # 補助者向けのアクションガイド
            st.divider()
            st.markdown("### 👩‍💼 補助者アクション")

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                st.info("書類作成へ進みますか？")
                if st.button(f"➡️ {selected_bank_name}用 書類作成画面へ"):
                    st.switch_page("pages/02_相続書類_作成.py")

            with c_act2:
                st.info("支店コードを調べますか？")
                if st.button("➡️ 支店検索・口座入力画面へ"):
                    st.switch_page("pages/99_口座情報_入力.py")


if __name__ == "__main__":
    main()
