# src/legal_system/ui/components/cases/nayose_registration.py

import base64
import json
import time
import unicodedata
from io import BytesIO
from typing import List, Union

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from legal_system.ui.components.document_viewer import render_enhanced_document_viewer
from pdf2image import convert_from_bytes

# プロジェクト内モジュール
from legal_system.core.ai_factory import AIFactory
from legal_system.models.tables import RealEstateAsset


def normalize_text(text: str) -> str:
    """テキスト正規化（全角・半角統一）"""
    if not text:
        return ""
    return unicodedata.normalize("NFKC", str(text)).strip()


def analyze_nayose_with_ai(image_inputs: Union[bytes, List[bytes]]) -> dict:
    """
    名寄帳をGemini Visionで解析するロジック
    """
    try:
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

        prompt_text = """
        あなたは日本の不動産登記・固定資産税の専門家（司法書士補助者）です。
        提供された「名寄帳（固定資産税課税明細書）」の画像を解析し、全資産情報をJSONで出力してください。
        
        【抽出ルール】
        - 所有者名 (owner_name) を特定してください。
        - 資産リスト (assets) に、以下の項目を抽出してください。
          - type: "土地", "家屋", "マンション" のいずれか
          - location: 所在
          - number: 地番 または 家屋番号
          - category_structure: 地目 または 構造
          - area: 地積 または 床面積 (数値のみ)
          - assessed_value: 固定資産税評価額 (数値のみ)
        
        【出力JSONフォーマット】
        {
            "owner_name": "所有者氏名",
            "assets": [
                { "type": "土地", "location": "...", "number": "...", "category_structure": "...", "area": 100.0, "assessed_value": 1000000 },
                ...
            ]
        }
        """

        if isinstance(image_inputs, bytes):
            image_inputs = [image_inputs]

        content_list = [{"type": "text", "text": prompt_text}]

        for img_bytes in image_inputs:
            img_str = base64.b64encode(img_bytes).decode("utf-8")
            content_list.append(
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}
            )

        message = HumanMessage(content=content_list)
        response = llm.invoke([message])

        content = response.content.replace("```json", "").replace("```", "").strip()
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        else:
            return {"error": "AIの応答がJSON形式ではありませんでした"}

    except Exception as e:
        return {"error": str(e)}


def render_nayose_registration(session, case_id: int):
    """
    名寄帳登録・不動産管理画面のメインレンダラー
    """
    st.subheader("🏘️ 不動産管理 (名寄帳・登録リスト)")

    # =========================================================
    # 1. 新規登録 (AI-OCR / ファイルアップロード)
    # =========================================================
    with st.expander("📤 新規登録: 名寄帳読み取り (AI)", expanded=True):
        uploaded_nayose = st.file_uploader(
            "名寄帳(PDF/画像)をアップロード",
            type=["pdf", "png", "jpg"],
            key="up_nayose",
        )

        if uploaded_nayose:
            file_bytes = uploaded_nayose.getvalue()

            # ビューワー表示
            render_enhanced_document_viewer(
                file_bytes, uploaded_nayose.type, "nayose_view", base_width=1000
            )

            # 自動解析ロジック
            if (
                "nayose_file_name" not in st.session_state
                or st.session_state["nayose_file_name"] != uploaded_nayose.name
            ):
                with st.spinner("🚀 ファイルを検知しました。AIが自動解析中です..."):
                    target_images_bytes = []
                    if uploaded_nayose.type == "application/pdf":
                        try:
                            images = convert_from_bytes(file_bytes, dpi=200)
                            for img in images:
                                buf = BytesIO()
                                img.convert("RGB").save(buf, format="JPEG")
                                target_images_bytes.append(buf.getvalue())
                        except Exception as e:
                            st.error(f"PDF変換エラー: {e}")
                    else:
                        target_images_bytes.append(file_bytes)

                    if target_images_bytes:
                        result = analyze_nayose_with_ai(target_images_bytes)
                        if "error" not in result:
                            st.session_state["nayose_result"] = result
                            st.session_state["nayose_file_name"] = uploaded_nayose.name
                            st.toast("解析完了！内容を確認してください", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error(f"解析失敗: {result['error']}")

        # AI解析結果の確認・登録フォーム
        if "nayose_result" in st.session_state and st.session_state["nayose_result"]:
            st.info("👇 解析結果を確認し、「この内容で追加」ボタンを押してください。")
            res = st.session_state["nayose_result"]
            st.markdown(f"**検出された所有者:** `{res.get('owner_name', '不明')}`")

            df_assets = pd.DataFrame(res.get("assets", []))
            if df_assets.empty:
                df_assets = pd.DataFrame(
                    columns=[
                        "type",
                        "location",
                        "number",
                        "category_structure",
                        "area",
                        "assessed_value",
                    ]
                )

            column_config = {
                "type": st.column_config.SelectboxColumn(
                    "種類", options=["土地", "家屋", "マンション"], required=True
                ),
                "location": st.column_config.TextColumn("所在", width="medium"),
                "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                "category_structure": st.column_config.TextColumn(
                    "地目/構造", width="small"
                ),
                "area": st.column_config.NumberColumn("地積/床面積"),
                "assessed_value": st.column_config.NumberColumn(
                    "評価額 (円)", format="%d"
                ),
            }

            edited_assets = st.data_editor(
                df_assets,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                key="nayose_editor",
            )

            if st.button(
                "💾 この内容で追加する", type="primary", use_container_width=True
            ):
                try:
                    count = 0
                    for index, row in edited_assets.iterrows():
                        if not row.get("location"):
                            continue

                        p_type_raw = str(row.get("type", ""))
                        p_type = "Land"
                        if "家" in p_type_raw or "建" in p_type_raw:
                            p_type = "Building"
                        elif "マンション" in p_type_raw:
                            p_type = "Condo"

                        area_val = 0.0
                        try:
                            area_val = float(str(row.get("area", 0)).replace(",", ""))
                        except:
                            pass

                        val_val = 0.0
                        try:
                            val_val = float(
                                str(row.get("assessed_value", 0)).replace(",", "")
                            )
                        except:
                            pass

                        new_asset = RealEstateAsset(
                            case_id=case_id,
                            property_type=p_type,
                            location=normalize_text(row.get("location")),
                            lot_number=normalize_text(row.get("number"))
                            if p_type == "Land"
                            else None,
                            land_category=normalize_text(row.get("category_structure"))
                            if p_type == "Land"
                            else None,
                            land_area=area_val if p_type == "Land" else None,
                            house_number=normalize_text(row.get("number"))
                            if p_type != "Land"
                            else None,
                            structure=normalize_text(row.get("category_structure"))
                            if p_type != "Land"
                            else None,
                            floor_area=str(area_val) if p_type != "Land" else None,
                            assessed_value=val_val,
                        )
                        session.add(new_asset)
                        count += 1

                    session.commit()
                    st.success(f"{count}件の不動産情報を追加しました！")
                    time.sleep(1)
                    st.session_state["nayose_result"] = None
                    st.rerun()
                except Exception as e:
                    session.rollback()
                    st.error(f"登録エラー: {e}")

    # =========================================================
    # 2. 登録済み不動産の編集・削除・追加 (CRUD Table)
    # =========================================================
    st.divider()
    st.subheader("📋 登録済み不動産一覧 (編集・修正)")
    st.caption(
        "下表を直接編集し、「変更を保存」ボタンを押してください。行を追加・削除も可能です。"
    )

    # DBから最新データを取得
    db_assets = session.query(RealEstateAsset).filter_by(case_id=case_id).all()

    # 編集用データフレームの構築
    # UIとDBのカラムをマッピングして扱いやすくする
    rows = []
    for asset in db_assets:
        # 表示用の種別変換
        p_type_disp = "土地"
        if asset.property_type == "Building":
            p_type_disp = "家屋"
        elif asset.property_type == "Condo":
            p_type_disp = "マンション"

        # 統合フィールドの作成 (地番と家屋番号を1列で扱う)
        num_disp = (
            asset.lot_number if asset.property_type == "Land" else asset.house_number
        )
        cat_disp = (
            asset.land_category if asset.property_type == "Land" else asset.structure
        )

        # 面積 (LandはFloat, BuildingはStringの場合があるが、表示上はStrで統一して扱う)
        area_disp = (
            asset.land_area if asset.property_type == "Land" else asset.floor_area
        )

        rows.append(
            {
                "id": asset.id,  # 隠しID
                "type": p_type_disp,
                "location": asset.location,
                "number": num_disp,
                "category_structure": cat_disp,
                "area": area_disp,
                "assessed_value": asset.assessed_value or 0,
            }
        )

    df_current = pd.DataFrame(rows)

    # 空の場合のスキーマ定義
    if df_current.empty:
        df_current = pd.DataFrame(
            columns=[
                "id",
                "type",
                "location",
                "number",
                "category_structure",
                "area",
                "assessed_value",
            ]
        )

    # 編集用コンフィグ
    column_config_crud = {
        "id": None,  # IDは非表示
        "type": st.column_config.SelectboxColumn(
            "種類", options=["土地", "家屋", "マンション"], required=True, width="small"
        ),
        "location": st.column_config.TextColumn("所在", width="large", required=True),
        "number": st.column_config.TextColumn("地番/家屋番号", width="medium"),
        "category_structure": st.column_config.TextColumn("地目/構造", width="medium"),
        "area": st.column_config.TextColumn(
            "地積/床面積", width="small"
        ),  # 柔軟性のためText
        "assessed_value": st.column_config.NumberColumn(
            "評価額 (円)", format="%d", width="small"
        ),
    }

    # Data Editor 表示
    edited_df = st.data_editor(
        df_current,
        column_config=column_config_crud,
        num_rows="dynamic",  # 行追加・削除を許可
        use_container_width=True,
        key="real_estate_crud_editor",
        hide_index=True,
    )

    # 保存ボタン
    if st.button("💾 変更を保存 (修正・追加・削除を反映)", type="primary"):
        try:
            # 1. 削除判定: DBにあるがEditorにないIDを削除
            current_ids_in_editor = [
                int(row["id"])
                for index, row in edited_df.iterrows()
                if pd.notna(row["id"])
            ]

            # DB上の全IDを取得
            all_db_ids = [a.id for a in db_assets]

            # 削除対象ID
            ids_to_delete = set(all_db_ids) - set(current_ids_in_editor)

            if ids_to_delete:
                session.query(RealEstateAsset).filter(
                    RealEstateAsset.id.in_(ids_to_delete)
                ).delete(synchronize_session=False)

            # 2. 更新 & 追加ループ
            for index, row in edited_df.iterrows():
                # 必須チェック
                if not row.get("location"):
                    continue

                # 種別変換 (Display -> DB)
                p_type_raw = str(row.get("type", ""))
                p_type = "Land"
                if "家" in p_type_raw or "建" in p_type_raw:
                    p_type = "Building"
                elif "マンション" in p_type_raw:
                    p_type = "Condo"

                # 面積変換
                area_raw = str(row.get("area", "")).replace("㎡", "")
                land_area_val = None
                floor_area_val = None

                if p_type == "Land":
                    try:
                        land_area_val = float(area_raw)
                    except:
                        land_area_val = 0.0
                else:
                    floor_area_val = area_raw  # 建物は文字列(例: 1階20 2階20)のまま保存

                # 行のIDを確認
                row_id = row.get("id")
                target_asset = None

                if pd.notna(row_id):
                    # 既存レコードの取得
                    target_asset = session.query(RealEstateAsset).get(int(row_id))

                if not target_asset:
                    # 新規作成
                    target_asset = RealEstateAsset(case_id=case_id)
                    session.add(target_asset)

                # 値のセット
                target_asset.property_type = p_type
                target_asset.location = normalize_text(row.get("location"))
                target_asset.assessed_value = float(row.get("assessed_value") or 0)

                # 土地/建物によるカラムの振り分け
                if p_type == "Land":
                    target_asset.lot_number = normalize_text(row.get("number"))
                    target_asset.land_category = normalize_text(
                        row.get("category_structure")
                    )
                    target_asset.land_area = land_area_val
                    # 建物のカラムはクリア
                    target_asset.house_number = None
                    target_asset.structure = None
                    target_asset.floor_area = None
                else:
                    target_asset.house_number = normalize_text(row.get("number"))
                    target_asset.structure = normalize_text(
                        row.get("category_structure")
                    )
                    target_asset.floor_area = floor_area_val
                    # 土地のカラムはクリア
                    target_asset.lot_number = None
                    target_asset.land_category = None
                    target_asset.land_area = None

            session.commit()
            st.toast("不動産情報を保存しました！", icon="✅")
            time.sleep(1)
            st.rerun()

        except Exception as e:
            session.rollback()
            st.error(f"保存中にエラーが発生しました: {e}")
