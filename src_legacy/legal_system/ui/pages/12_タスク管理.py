# src/legal_system/ui/pages/12_タスク管理.py

"""
タスク管理UI

日付: 2026-02-12
機能:
- 案件に紐づくタスクの表示・編集
- タスクの初期化
- 完了チェック、期限日変更、担当者変更
"""

from datetime import date

import pandas as pd
import streamlit as st
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case

from services.task_service import TaskService

st.set_page_config(page_title="タスク管理", page_icon="✅", layout="wide")


def render_task_management():
    """タスク管理画面のメイン関数"""

    st.title("✅ タスク管理")
    st.markdown("---")

    # セッション状態から案件IDを取得
    if (
        "selected_case_id" not in st.session_state
        or not st.session_state.selected_case_id
    ):
        st.warning("⚠️ 案件が選択されていません。案件検索から案件を選択してください。")
        return

    case_id = st.session_state.selected_case_id

    # 案件情報を表示
    db = DatabaseManager()
    session = db._get_session()
    try:
        case = session.query(Case).get(case_id)
        if not case:
            st.error("案件が見つかりません。")
            return

        st.info(f"📋 案件番号: **{case.case_number}** | 依頼者: **{case.client_name}**")
    finally:
        session.close()

    st.markdown("---")

    # タスクサービスを初期化
    task_service = TaskService()

    # タスク一覧を取得
    tasks = task_service.get_tasks_by_case(case_id)

    # タスクが存在しない場合は初期化ボタンを表示
    if not tasks:
        st.warning("📝 この案件にはまだタスクが登録されていません。")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(
                "🚀 標準タスクを初期化", type="primary", use_container_width=True
            ):
                with st.spinner("タスクを初期化中..."):
                    success = task_service.initialize_tasks(case_id)

                if success:
                    st.success("✅ タスクを初期化しました！")
                    # セッション状態をクリアして再読み込み
                    if "task_editor_key" in st.session_state:
                        del st.session_state["task_editor_key"]
                    st.rerun()
                else:
                    st.error("❌ タスクの初期化に失敗しました。")

        return

    # タスク一覧を表示・編集
    st.subheader("📋 タスク一覧")

    # データフレームに変換
    df = pd.DataFrame(tasks)

    # 表示用に整形
    display_df = df[
        [
            "task_id",
            "is_completed",
            "description",
            "due_date",
            "assigned_user_name",
            "weight",
        ]
    ].copy()

    display_df.columns = ["ID", "完了", "タスク名", "期限日", "担当者", "重み"]

    # データエディタで編集可能にする
    st.caption(
        "💡 完了チェック、期限日、担当者を直接編集できます。編集後は「変更を保存」ボタンをクリックしてください。"
    )

    # ユーザー一覧を取得（担当者選択用）
    users = task_service.get_available_users()
    user_names = {user["name"]: user["id"] for user in users}

    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "ID": st.column_config.NumberColumn(
                "ID", help="タスクID", disabled=True, width="small"
            ),
            "完了": st.column_config.CheckboxColumn(
                "完了", help="タスクが完了したらチェック", default=False, width="small"
            ),
            "タスク名": st.column_config.TextColumn(
                "タスク名", help="タスクの説明", disabled=True, width="large"
            ),
            "期限日": st.column_config.DateColumn(
                "期限日", help="タスクの期限日", format="YYYY-MM-DD", width="medium"
            ),
            "担当者": st.column_config.TextColumn(
                "担当者", help="担当者名", width="medium"
            ),
            "重み": st.column_config.NumberColumn(
                "重み",
                help="タスクの重要度（進捗率計算用）",
                min_value=0.1,
                max_value=5.0,
                step=0.1,
                format="%.1f",
                width="small",
            ),
        },
        hide_index=True,
        key="task_editor",
    )

    st.markdown("---")

    # 保存ボタン
    col1, col2, col3 = st.columns([2, 1, 2])

    with col2:
        if st.button("💾 変更を保存", type="primary", use_container_width=True):
            # 変更を検出して更新
            updates = []

            for idx, row in edited_df.iterrows():
                task_id = int(row["ID"])
                original_task = next(
                    (t for t in tasks if t["task_id"] == task_id), None
                )

                if not original_task:
                    continue

                update_data = {"task_id": task_id}
                changed = False

                # 完了状態の変更
                if row["完了"] != original_task["is_completed"]:
                    update_data["is_completed"] = bool(row["完了"])
                    changed = True

                # 期限日の変更
                if pd.notna(row["期限日"]):
                    new_due_date = row["期限日"]
                    if isinstance(new_due_date, pd.Timestamp):
                        new_due_date = new_due_date.date()

                    original_due_date = original_task["due_date"]

                    if new_due_date != original_due_date:
                        update_data["due_date"] = new_due_date
                        changed = True

                # 担当者の変更
                if row["担当者"] != original_task["assigned_user_name"]:
                    # 担当者名からIDを取得
                    new_user_id = user_names.get(row["担当者"])
                    if new_user_id and new_user_id != original_task["assigned_user_id"]:
                        update_data["assigned_user_id"] = new_user_id
                        changed = True

                # 重みの変更
                if pd.notna(row["重み"]) and float(row["重み"]) != float(
                    original_task["weight"]
                ):
                    update_data["weight"] = float(row["重み"])
                    changed = True

                if changed:
                    updates.append(update_data)

            # 更新を実行
            if updates:
                with st.spinner(f"{len(updates)}件のタスクを更新中..."):
                    success = task_service.update_tasks_bulk(updates)

                if success:
                    st.success(f"✅ {len(updates)}件のタスクを更新しました！")
                    # セッション状態をクリアして再読み込み
                    if "task_editor" in st.session_state:
                        del st.session_state["task_editor"]
                    st.rerun()
                else:
                    st.error("❌ タスクの更新に失敗しました。")
            else:
                st.info("変更がありませんでした。")

    st.markdown("---")

    # 進捗サマリー
    st.subheader("📊 進捗サマリー")

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["is_completed"])
    total_weight = sum(t["weight"] for t in tasks)
    completed_weight = sum(t["weight"] for t in tasks if t["is_completed"])

    progress_rate = (completed_weight / total_weight * 100) if total_weight > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("総タスク数", f"{total_tasks}件")

    with col2:
        st.metric("完了タスク数", f"{completed_tasks}件")

    with col3:
        st.metric("進捗率（重み付き）", f"{progress_rate:.1f}%")

    with col4:
        overdue_tasks = sum(
            1
            for t in tasks
            if not t["is_completed"] and t["due_date"] and t["due_date"] < date.today()
        )
        st.metric(
            "期限超過",
            f"{overdue_tasks}件",
            delta=f"-{overdue_tasks}" if overdue_tasks > 0 else None,
            delta_color="inverse",
        )

    # プログレスバー
    st.progress(progress_rate / 100, text=f"タスク進捗: {progress_rate:.1f}%")

    st.markdown("---")

    # カスタムタスク追加
    with st.expander("➕ カスタムタスクを追加"):
        st.caption("標準タスク以外の独自タスクを追加できます。")

        with st.form("add_custom_task"):
            new_description = st.text_input(
                "タスク名", placeholder="例: 特別な書類の作成"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                new_due_date = st.date_input("期限日", value=date.today())

            with col2:
                user_options = ["未割当"] + [u["name"] for u in users]
                selected_user = st.selectbox("担当者", user_options)

            with col3:
                new_weight = st.number_input(
                    "重み", min_value=0.1, max_value=5.0, value=1.0, step=0.1
                )

            submitted = st.form_submit_button(
                "追加", type="primary", use_container_width=True
            )

            if submitted:
                if not new_description:
                    st.error("タスク名を入力してください。")
                else:
                    # 担当者IDを取得
                    assigned_user_id = None
                    if selected_user != "未割当":
                        assigned_user_id = user_names.get(selected_user)

                    success = task_service.add_custom_task(
                        case_id=case_id,
                        description=new_description,
                        due_date=new_due_date,
                        assigned_user_id=assigned_user_id,
                        weight=new_weight,
                    )

                    if success:
                        st.success("✅ カスタムタスクを追加しました！")
                        st.rerun()
                    else:
                        st.error("❌ タスクの追加に失敗しました。")


if __name__ == "__main__":
    render_task_management()
