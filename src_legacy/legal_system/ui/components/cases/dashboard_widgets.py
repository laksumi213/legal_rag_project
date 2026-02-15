# src/legal_system/ui/components/cases/dashboard_widgets.py

import time

import pandas as pd
import streamlit as st

from legal_system.models.tables import ContactLog
from legal_system.services.deceased_service import get_all_users, update_case_assignment
from legal_system.services.kintone_sync_service import (
    get_kintone_data_as_dict,
    import_kintone_json,
)


# ---------------------------------------------------------
# 1. 担当者割り当てウィジェット (復活)
# ---------------------------------------------------------
def render_manager_assignment(session, case):
    """
    担当者（マネージャー・実務担当）の割り当てUI
    """
    st.markdown("##### 👥 担当者割り当て")

    # ユーザーリスト取得
    users = get_all_users()
    user_opts = {u_id: name for u_id, name in users.items()}
    user_opts[None] = "（未設定）"

    # 現在の値
    curr_mgr = case.manager_id
    curr_opr = case.operator_id

    c1, c2, c3 = st.columns([2, 2, 1])

    # リスト作成（選択肢）
    opts_list = list(user_opts.keys())

    with c1:
        # インデックス検索 (None対応)
        idx_m = (
            opts_list.index(curr_mgr)
            if curr_mgr in opts_list
            else opts_list.index(None)
        )
        new_mgr = st.selectbox(
            "進捗担当 (Manager)",
            opts_list,
            format_func=lambda x: user_opts[x],
            index=idx_m,
            key="sel_mgr",
        )

    with c2:
        idx_o = (
            opts_list.index(curr_opr)
            if curr_opr in opts_list
            else opts_list.index(None)
        )
        new_opr = st.selectbox(
            "実務担当 (Operator)",
            opts_list,
            format_func=lambda x: user_opts[x],
            index=idx_o,
            key="sel_opr",
        )

    with c3:
        st.write("")  # スペーサー
        st.write("")
        if st.button("更新", key="btn_assign_update"):
            if update_case_assignment(case.case_id, new_mgr, new_opr):
                st.toast("担当者を更新しました", icon="✅")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("更新失敗")


# ---------------------------------------------------------
# 2. SOL情報・紹介元情報 (復活)
# ---------------------------------------------------------
def render_sol_info(session, case):
    """
    紹介元（日興証券など）情報の表示
    """
    st.markdown("##### 🏢 紹介元・SOL情報")
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.caption("SOL案件番号")
        c1.write(case.sol_case_number or "（なし）")

        c2.caption("紹介元支店 / 担当者")
        br = case.referral_sec_branch_name or "-"
        rep = case.referral_sec_rep_name or "-"
        c2.write(f"{br} / {rep}")

        c3.caption("紹介日")
        intro = case.introduction_date
        c3.write(str(intro) if intro else "-")


# ---------------------------------------------------------
# 3. Kintone連携ツール (復活)
# ---------------------------------------------------------
def render_kintone_tool(case_id):
    """
    Kintoneからのデータ再取得・同期ツール
    """
    st.markdown("##### ☁️ Kintoneデータ同期")
    with st.expander("Kintoneから最新データを取り込む"):
        st.info("Kintone上のデータを再取得し、この案件の情報を上書き更新します。")
        if st.button("🔄 同期実行 (Pull from Kintone)", key="btn_kintone_sync"):
            with st.spinner("通信中..."):
                data = get_kintone_data_as_dict(case_id)
                if data:
                    # 同期処理 (import_kintone_json は ID を返す)
                    res_id = import_kintone_json(data, target_case_id=case_id)
                    if res_id > 0:
                        st.success("同期完了！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("データの保存に失敗しました。")
                else:
                    st.error(
                        "Kintoneからデータを取得できませんでした。Record IDを確認してください。"
                    )


# ---------------------------------------------------------
# 4. 対応履歴・タイムライン (Ver 3.3 新機能)
# ---------------------------------------------------------
def render_contact_logs(session, case_id):
    """
    対応履歴・処理タイムライン表示 (Table形式へアップグレード)
    """
    st.divider()
    st.subheader("⏱️ 処理タイムライン・履歴")

    # データを取得
    logs = (
        session.query(ContactLog)
        .filter_by(case_id=case_id)
        .order_by(ContactLog.log_id.desc())
        .all()
    )

    if logs:
        # データフレーム用に整形
        data = []
        for log in logs:
            # ログの内容から情報を簡易抽出（擬似パース）
            content = log.contact_content or ""
            action = "メモ/連絡"
            result = "記録"
            icon = "🗒️"

            if "【自動取込】" in content:
                action = "AI自動処理"
                icon = "🤖"
                if "完了" in content or "成功" in content:
                    result = "成功"
                elif "エラー" in content or "失敗" in content:
                    result = "失敗"
                else:
                    result = "通知"

            data.append(
                {
                    "ID": log.log_id,
                    "種別": icon,
                    "アクション": action,
                    "内容": content.split("\n")[0]
                    if content
                    else "(内容なし)",  # 1行目だけ表示
                    "詳細": content,
                    "結果": result,
                }
            )

        df = pd.DataFrame(data)

        # タイムライン風テーブル表示
        st.dataframe(
            df[["種別", "アクション", "内容", "結果"]],
            column_config={
                "種別": st.column_config.TextColumn("Icon", width="small"),
                "アクション": st.column_config.TextColumn("Action", width="medium"),
                "内容": st.column_config.TextColumn("Content", width="large"),
                "結果": st.column_config.TextColumn("Status", width="small"),
            },
            use_container_width=True,
            hide_index=True,
        )

        # 詳細確認用エクスパンダー
        with st.expander("詳細ログを確認する"):
            for d in data:
                st.markdown(f"**{d['種別']} {d['アクション']}** : {d['内容']}")
                st.text(d["詳細"])
                st.divider()
    else:
        st.info("履歴はありません。")
