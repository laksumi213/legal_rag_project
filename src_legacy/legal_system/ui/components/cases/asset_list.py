# src/legal_system/ui/components/cases/asset_list.py

import json
import time

import pandas as pd
import streamlit as st
from sqlalchemy import desc
from sqlalchemy.orm import joinedload

from legal_system.models.tables import FileRegistry, FinancialAsset
from legal_system.services.asset_service import sync_bank_assets


def render_bank_account_list(session, case_id: int):
    """
    銀行口座リストの表示とCRUD編集
    """
    st.subheader("🏦 銀行・金融資産管理")

    # データを取得してDataFrameに変換
    assets = (
        session.query(FinancialAsset)
        .options(
            joinedload(FinancialAsset.bank_ref),
            joinedload(FinancialAsset.branch_ref),
            joinedload(FinancialAsset.account_type_ref),
        )
        .filter(
            FinancialAsset.case_id == case_id,
            (FinancialAsset.asset_type == "BANK") | (FinancialAsset.asset_type == None),
        )
        .all()
    )

    asset_data = []
    for a in assets:
        asset_data.append(
            {
                "id": a.id,
                "銀行名": a.bank_ref.bank_name if a.bank_ref else "",
                "支店名": a.branch_ref.branch_name if a.branch_ref else "",
                "種別": a.account_type_ref.type_name if a.account_type_ref else "普通",
                "口座番号": a.account_number,
                "残高": int(a.balance) if a.balance is not None else 0,
                "状況": a.status,
            }
        )

    df = pd.DataFrame(asset_data)

    st.info("👇 下の表で銀行口座の情報を直接編集できます。行の追加・削除も可能です。")

    # データエディタ
    edited_df = st.data_editor(
        df,
        key="bank_asset_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "id": None,  # ID列は非表示
            "銀行名": st.column_config.TextColumn(
                "銀行名", required=True, width="medium"
            ),
            "支店名": st.column_config.TextColumn("支店名", width="medium"),
            "種別": st.column_config.SelectboxColumn(
                "種別",
                options=["普通", "当座", "貯蓄", "定期"],
                required=True,
                width="small",
            ),
            "口座番号": st.column_config.TextColumn("口座番号", width="small"),
            "残高": st.column_config.NumberColumn(
                "残高 (円)", format="%d", width="medium"
            ),
            "状況": st.column_config.TextColumn("状況", width="medium"),
        },
    )

    if st.button("💾 銀行口座リストを保存", type="primary"):
        try:
            data_to_sync = edited_df.to_dict(orient="records")
            result = sync_bank_assets(session, case_id, data_to_sync)
            session.commit()

            msg_parts = []
            if result.get("added"):
                msg_parts.append(f"{result['added']}件追加")
            if result.get("updated"):
                msg_parts.append(f"{result['updated']}件更新")
            if result.get("deleted"):
                msg_parts.append(f"{result['deleted']}件削除")

            final_msg = "、".join(msg_parts) if msg_parts else "変更はありませんでした"
            st.success(f"保存しました ({final_msg})")

            time.sleep(1)
            st.rerun()

        except Exception as e:
            session.rollback()
            st.error(f"保存中にエラーが発生しました: {e}")
            logger.error(f"Asset Save Error: {e}", exc_info=True)


def render_securities_list(session, case_id: int):
    """
    証券・その他資産の管理 (CRUD機能)
    銘柄ごとの明細をJSONから復元して編集可能にする
    """
    st.subheader("📈 証券・投資信託・その他資産")

    # 証券資産の取得
    assets = (
        session.query(FinancialAsset)
        .filter(
            FinancialAsset.case_id == case_id, FinancialAsset.asset_type == "SECURITY"
        )
        .all()
    )

    if not assets:
        st.info(
            "登録された証券口座はありません。「AI受信トレイ」から報告書を取り込むか、新規登録してください。"
        )
        # ここに手動登録ボタンを追加することも可能
        return

    for asset in assets:
        sec_name = asset.bank_ref.bank_name if asset.bank_ref else "不明な証券会社"
        branch = asset.branch_ref.branch_name if asset.branch_ref else "-"
        acc_num = asset.account_number or "不明"

        # 合計評価額の表示
        label = f"📈 {sec_name} ({branch}) - 口座: {acc_num} | 評価額: {asset.balance:,.0f}円"

        with st.expander(label, expanded=False):
            # -------------------------------------------------
            # 1. 明細データのロード (FileRegistryからJSONを取得)
            # -------------------------------------------------
            # この資産に紐づく最新の「証券取引報告書」データを検索
            # (bank_id と case_id で紐付け)
            linked_file = (
                session.query(FileRegistry)
                .filter(
                    FileRegistry.case_id == case_id,
                    FileRegistry.doc_type == "securities_statement",
                )
                .order_by(desc(FileRegistry.registered_at))
                .all()
            )

            # 銀行名が一致するファイルを探す (簡易マッチング)
            target_file_record = None
            extracted_json = {}

            # FileRegistryにbank_idがあればベストだが、なければextracted_data内のbank_nameで探す
            for f in linked_file:
                try:
                    data = json.loads(f.extracted_data or "{}")
                    if data.get("bank_name") == sec_name:
                        target_file_record = f
                        extracted_json = data
                        break
                except:
                    continue

            # 明細データの取り出し
            meta = extracted_json.get("meta", {})
            holdings = meta.get("holdings", [])

            # データがない場合の初期値
            if not holdings:
                holdings = [
                    {"name": "", "quantity": "", "category": "株式", "valuation": 0}
                ]

            st.markdown("###### 📊 保有銘柄明細 (編集・追加・削除可)")

            df_holdings = pd.DataFrame(holdings)

            # 編集用テーブル
            edited_df = st.data_editor(
                df_holdings,
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "name": st.column_config.TextColumn(
                        "銘柄・ファンド名", required=True, width="large"
                    ),
                    "quantity": st.column_config.TextColumn(
                        "数量 (株/口)", width="medium"
                    ),
                    "category": st.column_config.SelectboxColumn(
                        "種別",
                        options=["株式", "投資信託", "債券", "MRF", "預り金", "その他"],
                        width="small",
                    ),
                    "valuation": st.column_config.NumberColumn(
                        "評価額 (円)", format="%d", width="medium"
                    ),
                },
                key=f"sec_edit_{asset.id}",
            )

            # 自動計算
            current_total = 0
            try:
                current_total = edited_df["valuation"].sum()
            except:
                pass

            c_calc, c_act = st.columns([2, 1])
            c_calc.info(f"💰 明細合計: {current_total:,.0f} 円")

            if c_act.button(
                "💾 明細を保存 & 残高更新", key=f"save_sec_{asset.id}", type="primary"
            ):
                try:
                    # 1. FinancialAsset (親) の更新
                    asset.balance = float(current_total)
                    asset.status = "確認済"

                    # 2. 明細データ (JSON) の保存
                    # 紐づくファイルレコードがあれば更新、なければ警告（またはダミー作成）
                    clean_holdings = edited_df.to_dict(orient="records")
                    clean_holdings = [
                        h for h in clean_holdings if h.get("name")
                    ]  # 空行除去

                    if target_file_record:
                        # 既存JSONの一部だけ更新
                        try:
                            current_data = json.loads(target_file_record.extracted_data)
                        except:
                            current_data = {"meta": {}}

                        if "meta" not in current_data:
                            current_data["meta"] = {}

                        current_data["meta"]["holdings"] = clean_holdings
                        current_data["meta"]["balance"] = float(
                            current_total
                        )  # 合計も同期

                        target_file_record.extracted_data = json.dumps(
                            current_data, ensure_ascii=False
                        )
                        st.toast("明細データを更新しました")
                    else:
                        # ファイルがない場合（手動登録など）の対応
                        # ここではシンプルにFinancialAssetのみ更新し、警告を出す
                        st.warning(
                            "紐づくスキャンデータが見つからないため、明細は一時的な保存となります。"
                        )

                    session.commit()
                    st.success("✅ 資産情報を更新しました！")
                    import time

                    time.sleep(1)
                    st.rerun()

                except Exception as e:
                    st.error(f"保存エラー: {e}")
