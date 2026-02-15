# src/services/graph_service.py

from typing import Dict, List

from legal_system.models.tables import Deceased, Heir


class GraphService:
    """
    DBの相続人情報を基に、Mermaid.js形式のグラフコードを生成するサービス。
    および法定相続人の順位判定ロジックを提供します。
    """

    @staticmethod
    def generate_mermaid_family_tree(deceased: Deceased, heirs: List[Heir]) -> str:
        """
        被相続人を中心に据えた家系図コードを作成。
        """
        if not deceased:
            return "graph TD\n    Error[被相続人データなし]"

        lines = ["graph TD"]

        # 1. スタイルの定義
        lines.append(
            "classDef deceased fill:#f96,stroke:#333,stroke-width:4px,color:white;"
        )
        lines.append("classDef spouse fill:#fff4dd,stroke:#d4a017,stroke-width:2px;")
        lines.append("classDef child fill:#e1f5fe,stroke:#01579b,stroke-width:2px;")
        lines.append(
            "classDef parent fill:#eeeeee,stroke:#666,stroke-width:2px,stroke-dasharray: 5 5;"
        )
        lines.append("classDef sibling fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;")

        # 2. 被相続人ノード
        d_id = f"D{deceased.id}"
        d_name = f"{deceased.name_last}{deceased.name_first}".replace(" ", "").replace(
            "　", ""
        )
        d_label = f"{d_name}<br/>(被相続人)"
        lines.append(f'    {d_id}["{d_label}"]:::deceased')

        # 3. 相続人ノードとエッジ
        if not heirs:
            lines.append('    NoHeir["相続人未登録"]:::child')
            lines.append(f"    {d_id} -.-> NoHeir")
            return "\n".join(lines)

        for h in heirs:
            h_id = f"H{h.id}"
            rel = h.relationship_type or "親族"
            h_name = f"{h.name_last}{h.name_first}".replace(" ", "").replace("　", "")
            h_label = f"{h.name_last} {h.name_first}<br/>[{rel}]"

            # クラス判定と接続ロジック
            h_class = "child"
            edge = "-->"  # デフォルトは子

            if any(k in rel for k in ["妻", "夫", "配偶者"]):
                h_class = "spouse"
                edge = "---"  # 配偶者は横並び線
            elif any(k in rel for k in ["父", "母", "祖父", "祖母"]):
                h_class = "parent"
                edge = "---"  # 尊属（家系図的には上だが、簡易表示では並列か逆矢印）
            elif any(k in rel for k in ["兄", "弟", "姉", "妹"]):
                h_class = "sibling"
                edge = "---"

            lines.append(f'    {h_id}["{h_label}"]:::{h_class}')

            # 関係性の描画
            if h_class == "parent":
                # 尊属は被相続人の上に描きたいが、MermaidのTDでは難しいので破線でつなぐ
                lines.append(f"    {h_id} -.-> {d_id}")
            elif h_class == "spouse":
                lines.append(f"    {d_id} {edge} {h_id}")
            else:
                lines.append(f"    {d_id} {edge} {h_id}")

        return "\n".join(lines)

    @staticmethod
    def determine_inheritance_rank(heirs: List[Heir]) -> Dict[str, List[int]]:
        """
        続柄から法定相続人の優先順位を判定する（簡易版）
        戻り値: {"first": [ids...], "second": [], "third": [], "spouse": []}
        """
        ranks = {"first": [], "second": [], "third": [], "spouse": []}

        for h in heirs:
            rel = h.relationship_type or ""
            # 配偶者
            if any(x in rel for x in ["妻", "夫", "配偶者"]):
                ranks["spouse"].append(h.id)
            # 第1順位（直系卑属）
            elif any(
                x in rel for x in ["長男", "二男", "長女", "二女", "子", "養子", "孫"]
            ):
                ranks["first"].append(h.id)
            # 第2順位（直系尊属）
            elif any(x in rel for x in ["父", "母", "祖父", "祖母"]):
                ranks["second"].append(h.id)
            # 第3順位（兄弟姉妹）
            elif any(x in rel for x in ["兄", "弟", "姉", "妹"]):
                ranks["third"].append(h.id)

        return ranks
