# src/legal_system/ui/pages/05_家系図・相続人可視化.py

import streamlit as st
from sqlalchemy.orm import joinedload
import os
import sys

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir
from src.services.graph_service import GraphService

st.set_page_config(page_title="AI家系図可視化", page_icon="🌳", layout="wide")

def main():
    st.title("🌳 AI家系図・相続権自動判定")
    st.caption("戸籍読取結果から、法定相続人の構成をグラフィカルに表示します。")

    db = DatabaseManager()
    session = db._get_session()

    # 1. 案件選択 (Home同期)
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning("案件を選択してください。")
        return

    # データロード
    case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).get(target_case_id)

    if not case or not case.deceased_ref:
        st.error("案件情報または被相続人情報が不足しています。")
        return

    deceased = case.deceased_ref
    heirs = deceased.heirs

    col_graph, col_info = st.columns([2, 1])

    with col_graph:
        st.subheader("📊 相続関係図 (Mermaid)")
        if not heirs:
            st.info("相続人が登録されていません。「戸籍読取」画面から登録してください。")
        else:
            # グラフ生成
            graph_code = GraphService.generate_mermaid_family_tree(deceased, heirs)
            
            # Mermaidの描画
            st.markdown(f"""
            ```mermaid
            {graph_code}
            ```
            """)
            
            with st.expander("デバッグ: グラフコードを表示"):
                st.code(graph_code)

    with col_info:
        st.subheader("⚖️ 法定相続判定")
        ranks = GraphService.determine_inheritance_rank(heirs)
        
        # 判定表示
        if ranks["spouse"]:
            st.success(f"配偶者: {len(ranks['spouse'])}名検知")
        
        if ranks["first"]:
            st.info(f"第1順位（子・孫）: {len(ranks['first'])}名")
        elif ranks["second"]:
            st.info(f"第2順位（父母）: {len(ranks['second'])}名")
        elif ranks["third"]:
            st.info(f"第3順位（兄弟姉妹）: {len(ranks['third'])}名")
        else:
            st.warning("有効な法定相続人が特定できません。")

        st.divider()
        st.markdown("##### 📝 判定アドバイス")
        if ranks["first"] and ranks["spouse"]:
            st.write("配偶者と子が相続人となります。法定相続分は各1/2です。")
        elif not ranks["first"] and ranks["second"]:
            st.write("子がいないため、配偶者と直系尊属が相続人となります。")
        elif ranks["first"] and not ranks["spouse"]:
             st.write("配偶者がいないため、子が全ての遺産を相続します。")

    session.close()

if __name__ == "__main__":
    main()