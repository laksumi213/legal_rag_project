# src/legal_system/ui/pages/13_進捗ダッシュボード.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from services.progress_tracker import ProgressTracker

st.set_page_config(page_title="進捗ダッシュボード", page_icon="📊", layout="wide")


def render_progress_dashboard():
    """進捗ダッシュボードのメイン画面"""

    st.title("📊 案件進捗ダッシュボード")
    st.markdown("---")

    tracker = ProgressTracker()

    # タブで表示を切り替え
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 全案件サマリー", "⚠️ SLA違反検出", "🔍 ボトルネック分析", "📋 個別案件詳細"]
    )

    with tab1:
        render_all_cases_summary(tracker)

    with tab2:
        render_sla_violations(tracker)

    with tab3:
        render_bottleneck_analysis(tracker)

    with tab4:
        render_individual_case_detail(tracker)


def render_all_cases_summary(tracker: ProgressTracker):
    """全案件サマリー表示"""
    st.header("全案件の進捗状況")

    with st.spinner("データを読み込み中..."):
        summary = tracker.get_all_cases_summary()

    if not summary:
        st.info("進行中の案件がありません。")
        return

    # KPI表示
    col1, col2, col3, col4 = st.columns(4)

    total_cases = len(summary)
    avg_progress = (
        sum(c["progress"] for c in summary) / total_cases if total_cases > 0 else 0
    )
    overdue_cases = sum(1 for c in summary if c["is_overdue"])
    on_track_cases = sum(
        1 for c in summary if c["progress"] >= 70 and not c["is_overdue"]
    )

    with col1:
        st.metric("総案件数", f"{total_cases}件")

    with col2:
        st.metric("平均進捗率", f"{avg_progress:.1f}%")

    with col3:
        st.metric(
            "SLA違反",
            f"{overdue_cases}件",
            delta=f"-{overdue_cases}",
            delta_color="inverse",
        )

    with col4:
        st.metric("順調な案件", f"{on_track_cases}件", delta=f"+{on_track_cases}")

    st.markdown("---")

    # 進捗率ヒートマップ
    st.subheader("📊 案件別進捗率ヒートマップ")

    df = pd.DataFrame(summary)

    # 進捗率で色分け
    def get_progress_color(progress):
        if progress >= 80:
            return "🟢"
        elif progress >= 50:
            return "🟡"
        elif progress >= 30:
            return "🟠"
        else:
            return "🔴"

    df["進捗アイコン"] = df["progress"].apply(get_progress_color)

    # 表示用データフレーム
    display_df = df[
        [
            "case_number",
            "client_name",
            "progress",
            "進捗アイコン",
            "status",
            "days_since_contract",
            "is_overdue",
        ]
    ].copy()

    display_df.columns = [
        "案件番号",
        "依頼者名",
        "進捗率(%)",
        "状態",
        "ステータス",
        "経過日数",
        "SLA違反",
    ]

    # SLA違反を強調表示
    display_df["SLA違反"] = display_df["SLA違反"].apply(
        lambda x: "⚠️ 違反" if x else "✅ 正常"
    )

    # データエディタで表示（色付き）
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "進捗率(%)": st.column_config.ProgressColumn(
                "進捗率(%)",
                help="案件の全体進捗率",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "経過日数": st.column_config.NumberColumn(
                "経過日数", help="契約日からの経過日数", format="%d日"
            ),
        },
    )

    # 進捗率分布グラフ
    st.subheader("📈 進捗率分布")

    col1, col2 = st.columns(2)

    with col1:
        # ヒストグラム
        fig_hist = px.histogram(
            df,
            x="progress",
            nbins=10,
            title="進捗率の分布",
            labels={"progress": "進捗率(%)", "count": "案件数"},
            color_discrete_sequence=["#1f77b4"],
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        # 円グラフ（進捗ステージ別）
        progress_categories = []
        for p in df["progress"]:
            if p >= 80:
                progress_categories.append("80%以上")
            elif p >= 50:
                progress_categories.append("50-80%")
            elif p >= 30:
                progress_categories.append("30-50%")
            else:
                progress_categories.append("30%未満")

        category_counts = pd.Series(progress_categories).value_counts()

        fig_pie = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="進捗ステージ別案件数",
            color_discrete_sequence=px.colors.sequential.RdYlGn[::-1],
        )
        st.plotly_chart(fig_pie, use_container_width=True)


def render_sla_violations(tracker: ProgressTracker):
    """SLA違反案件の表示"""
    st.header("⚠️ SLA違反案件")

    # 閾値設定
    col1, col2 = st.columns([1, 3])
    with col1:
        days_threshold = st.number_input(
            "SLA閾値（日数）",
            min_value=30,
            max_value=180,
            value=90,
            step=10,
            help="契約日からこの日数を超えた案件をSLA違反とみなします",
        )

    with st.spinner("SLA違反案件を検出中..."):
        violations = tracker.detect_sla_violations(days_threshold=days_threshold)

    if not violations:
        st.success(f"✅ {days_threshold}日以内の案件はすべて順調です！")
        return

    st.warning(f"⚠️ {len(violations)}件のSLA違反案件が検出されました")

    # 違反案件リスト
    df_violations = pd.DataFrame(violations)

    # 表示用に整形
    display_df = df_violations[
        [
            "case_number",
            "client_name",
            "contract_date",
            "days_elapsed",
            "progress",
            "overdue_tasks",
        ]
    ].copy()

    display_df.columns = [
        "案件番号",
        "依頼者名",
        "契約日",
        "経過日数",
        "進捗率(%)",
        "期限超過タスク数",
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "経過日数": st.column_config.NumberColumn(
                "経過日数", help="契約日からの経過日数", format="%d日"
            ),
            "進捗率(%)": st.column_config.ProgressColumn(
                "進捗率(%)",
                help="案件の全体進捗率",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "期限超過タスク数": st.column_config.NumberColumn(
                "期限超過タスク数", help="期限を過ぎたタスクの数", format="%d件"
            ),
        },
    )

    # 経過日数 vs 進捗率の散布図
    st.subheader("📊 経過日数と進捗率の関係")

    fig_scatter = px.scatter(
        df_violations,
        x="days_elapsed",
        y="progress",
        size="overdue_tasks",
        hover_data=["case_number", "client_name"],
        title="SLA違反案件の分析",
        labels={
            "days_elapsed": "経過日数",
            "progress": "進捗率(%)",
            "overdue_tasks": "期限超過タスク数",
        },
        color="progress",
        color_continuous_scale="RdYlGn",
    )

    # SLA閾値ラインを追加
    fig_scatter.add_vline(
        x=days_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text=f"SLA閾値 ({days_threshold}日)",
    )

    st.plotly_chart(fig_scatter, use_container_width=True)


def render_bottleneck_analysis(tracker: ProgressTracker):
    """ボトルネック分析の表示"""
    st.header("🔍 ボトルネック分析")

    with st.spinner("ボトルネックを分析中..."):
        analysis = tracker.get_bottleneck_analysis()

    if "error" in analysis:
        st.error(f"エラー: {analysis['error']}")
        return

    # 最も遅延しているステージ
    st.subheader("🎯 最も遅延しているステージ")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(
            "ボトルネック工程",
            analysis.get("most_delayed_stage", "不明"),
            help="最も多くの案件が遅延している工程",
        )

    with col2:
        # ステージ別遅延案件数
        delayed_counts = analysis.get("delayed_count_by_stage", {})

        if delayed_counts:
            fig_bar = px.bar(
                x=list(delayed_counts.keys()),
                y=list(delayed_counts.values()),
                title="ステージ別遅延案件数",
                labels={"x": "ステージ", "y": "遅延案件数"},
                color=list(delayed_counts.values()),
                color_continuous_scale="Reds",
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # 停滞案件リスト
    st.subheader("⏸️ 停滞している案件（上位10件）")

    stuck_cases = analysis.get("stuck_cases", [])

    if not stuck_cases:
        st.info("停滞している案件はありません。")
        return

    df_stuck = pd.DataFrame(stuck_cases)

    display_df = df_stuck[["case_number", "stage", "days_stuck", "progress"]].copy()

    display_df.columns = ["案件番号", "停滞ステージ", "停滞日数", "進捗率(%)"]

    st.dataframe(
        display_df,
        use_container_width=True,
        column_config={
            "停滞日数": st.column_config.NumberColumn(
                "停滞日数", help="このステージで停滞している日数", format="%d日"
            ),
            "進捗率(%)": st.column_config.ProgressColumn(
                "進捗率(%)",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


def render_individual_case_detail(tracker: ProgressTracker):
    """個別案件の詳細進捗表示"""
    st.header("📋 個別案件の詳細進捗")

    # 案件IDの入力
    case_id = st.number_input(
        "案件IDを入力",
        min_value=1,
        value=1,
        step=1,
        help="詳細を表示したい案件のIDを入力してください",
    )

    if st.button("進捗を表示", type="primary"):
        with st.spinner("データを読み込み中..."):
            progress = tracker.calculate_case_progress(case_id)

        if "error" in progress:
            st.error(f"エラー: {progress['error']}")
            return

        # 全体進捗率
        st.metric("全体進捗率", f"{progress['overall']}%")

        st.markdown("---")

        # ステージ別進捗率
        st.subheader("ステージ別進捗率")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("タスク", f"{progress['tasks']}%")

        with col2:
            st.metric("銀行解約", f"{progress['banks']}%")

        with col3:
            st.metric("戸籍収集", f"{progress['koseki']}%")

        with col4:
            st.metric("不動産登記", f"{progress['real_estate']}%")

        # レーダーチャート
        st.subheader("📊 進捗バランス")

        categories = ["タスク", "銀行解約", "戸籍収集", "不動産登記"]
        values = [
            progress["tasks"],
            progress["banks"],
            progress["koseki"],
            progress["real_estate"],
        ]

        fig_radar = go.Figure()

        fig_radar.add_trace(
            go.Scatterpolar(r=values, theta=categories, fill="toself", name="進捗率")
        )

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title="各ステージの進捗バランス",
        )

        st.plotly_chart(fig_radar, use_container_width=True)

        # 詳細情報
        st.subheader("📝 詳細情報")

        details = progress.get("details", {})

        col1, col2 = st.columns(2)

        with col1:
            st.write("**タスク情報**")
            st.write(f"- 総タスク数: {details.get('total_tasks', 0)}件")
            st.write(f"- 完了タスク数: {details.get('completed_tasks', 0)}件")
            st.write(f"- 総重み: {details.get('total_weight', 0):.1f}")
            st.write(f"- 完了重み: {details.get('completed_weight', 0):.1f}")

        with col2:
            st.write("**資産情報**")
            st.write(f"- 総銀行数: {details.get('total_banks', 0)}件")
            st.write(f"- 解約済み: {details.get('completed_banks', 0)}件")
            st.write(f"- 総不動産数: {details.get('total_estates', 0)}件")
            st.write(f"- 登記取得済み: {details.get('completed_estates', 0)}件")

        st.write("**戸籍情報**")
        st.write(f"- 登録戸籍数: {details.get('total_koseki', 0)}件")
        st.write(
            f"- 連続性: {'✅ あり' if details.get('has_continuity') else '❌ なし'}"
        )
        st.write(f"- 出生記録: {'✅ あり' if details.get('has_birth') else '❌ なし'}")
        st.write(f"- 死亡記録: {'✅ あり' if details.get('has_death') else '❌ なし'}")


if __name__ == "__main__":
    render_progress_dashboard()
