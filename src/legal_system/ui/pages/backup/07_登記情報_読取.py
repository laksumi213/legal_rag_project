# src/legal_system/ui/pages/07_登記情報_読取.py

import base64
import json
import os
import sys
import time
import re
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy.orm import joinedload

# ==========================================
# 1. パス解決 & インポート
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, RealEstateAsset

# フォルダ操作用サービス
from services.folder_service import find_case_folder, open_local_folder
from services.deceased_service import update_case_folder_path

# ページ設定
st.set_page_config(page_title="登記情報 自動読取", page_icon="🏘️", layout="wide")

# ==========================================
# 2. AI解析ロジック (Gemini Vision)
# ==========================================
def analyze_registry_with_ai(file_bytes: bytes, mime_type: str, target_name: str) -> dict:
    """
    登記情報を読み取り、土地・建物の情報を抽出する
    """
    llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    # 画像処理 (PDFの場合は全ページを画像化)
    image_data_list = []
    if mime_type == "application/pdf":
        try:
            # 登記情報は細かい文字が多いので高解像度(dpi=300)で変換推奨
            images = convert_from_bytes(file_bytes, dpi=250)
            for img in images:
                buf = BytesIO()
                img.save(buf, format="JPEG")
                image_data_list.append(buf.getvalue())
        except Exception as e:
            return {"error": f"PDF変換エラー: {e}"}
    else:
        image_data_list.append(file_bytes)

    # プロンプトの構築
    prompt_text = f"""
    あなたは日本の不動産登記の専門家です。
    提供された「不動産登記情報（全部事項証明書など）」の画像を読み取り、以下の対象者に関する不動産情報を抽出してJSON形式で出力してください。

    【抽出対象者（被相続人）】
    氏名: {target_name}
    ※この人物が所有者（または共有者）となっている不動産情報を抽出してください。
    ※過去の所有者ではなく、「現在効力のある所有権」を確認し、この人物の「持分」を特定してください。
    ※単独所有の場合は持分を "1/1" としてください。

    【抽出項目定義】
    1. **区分 (type)**: "土地" または "建物"
    2. **所在 (location)**: "〇〇市〇〇区〇〇町一丁目" のように抽出
    3. **番号 (number)**: 
       - 土地の場合: 地番 ("123番4" など)
       - 建物の場合: 家屋番号 ("123番4" など)
    4. **種類 (category)**: 
       - 土地の場合: 地目 ("宅地", "畑" など)
       - 建物の場合: 種類 ("居宅", "共同住宅" など)
    5. **面積 (area)**:
       - 土地の場合: 地積 (数値のみ。例: 123.45)
       - 建物の場合: 床面積 (文字列で可。例: "1階 50.00 2階 40.00" や合計値)
    6. **構造 (structure)**:
       - 建物の場合のみ抽出 ("木造かわらぶき2階建" など)。土地の場合は null。
    7. **持分 (share)**:
       - 対象者({target_name})の持分 ("1/2", "1/1" など)

    【出力JSONスキーマ】
    {{
        "assets": [
            {{
                "type": "土地",
                "location": "東京都千代田区...",
                "number": "10番1",
                "category": "宅地",
                "area": 100.5,
                "structure": null,
                "share": "1/1"
            }},
            {{
                "type": "建物",
                "location": "東京都千代田区...",
                "number": "10番1",
                "category": "居宅",
                "area": "1階 50.00",
                "structure": "木造スレート葺",
                "share": "1/2"
            }}
        ]
    }}
    """

    content_parts = [{"type": "text", "text": prompt_text}]
    for img_data in image_data_list:
        img_b64 = base64.b64encode(img_data).decode("utf-8")
        content_parts.append(
            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"}
        )

    try:
        message = HumanMessage(content=content_parts)
        response = llm.invoke([message])
        
        raw_content = response.content
        json_str = raw_content.replace("```json", "").replace("```", "").strip()
        
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(json_str[start:end])
        else:
            return {"error": "AIからの応答がJSON形式ではありませんでした。"}

    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 3. 遺言書用テキスト生成関数
# ==========================================
def generate_will_text(assets_df: pd.DataFrame) -> str:
    """
    DataFrameの内容から、遺言書コピペ用のテキストを生成する
    """
    text_lines = []
    
    # 全角スペース
    sp = "　"
    
    for i, row in assets_df.iterrows():
        # 連番 (1) (2)...
        num_prefix = f"（{i+1}）"
        
        p_type = row.get("type", "")
        loc = row.get("location", "")
        num = row.get("number", "")
        cat = row.get("category", "")
        area = row.get("area", "")
        share = row.get("share", "")
        
        # 土地の場合
        if p_type == "土地":
            text_lines.append(f"{num_prefix}\t土地")
            text_lines.append(f"{sp}所在{sp}{loc}")
            text_lines.append(f"{sp}地番{sp}{num}")
            text_lines.append(f"{sp}地目{sp}{cat}")
            text_lines.append(f"{sp}地積{sp}{area}㎡")
            text_lines.append(f"{sp}持分{sp}{share}")
            
        #建物の場合
        else:
            struc = row.get("structure", "")
            text_lines.append(f"{num_prefix}\t建物")
            text_lines.append(f"{sp}所在{sp}{loc}")
            text_lines.append(f"{sp}家屋番号{sp}{num}")
            text_lines.append(f"{sp}種類{sp}{cat}")
            text_lines.append(f"{sp}構造{sp}{struc}")
            text_lines.append(f"{sp}床面積{sp}{area}㎡")
            text_lines.append(f"{sp}持分{sp}{share}")
            
        text_lines.append("") # 空行

    return "\n".join(text_lines)

# ==========================================
# 4. DB保存ヘルパー
# ==========================================
def save_real_estate_to_db(session, case_id: int, assets: list):
    """
    抽出した不動産情報をDBに保存する
    """
    count = 0
    for item in assets:
        p_type = "Land" if item.get("type") == "土地" else "Building"
        
        # 面積の数値変換（可能な場合）
        area_val = None
        floor_area_str = None
        
        raw_area = item.get("area")
        if p_type == "Land":
            # 土地はFloatで保存したい
            try:
                if isinstance(raw_area, (int, float)):
                    area_val = float(raw_area)
                else:
                    # 文字列から数値抽出 ("100.23㎡" -> 100.23)
                    match = re.search(r"(\d+(\.\d+)?)", str(raw_area))
                    if match:
                        area_val = float(match.group(1))
            except:
                pass
        else:
            # 建物は構造が複雑なため文字列として保存
            floor_area_str = str(raw_area)

        # 重複チェック (簡易): 同じ案件、同じ所在、同じ地番/家屋番号
        q = session.query(RealEstateAsset).filter(
            RealEstateAsset.case_id == case_id,
            RealEstateAsset.location == item.get("location"),
        )
        if p_type == "Land":
            q = q.filter(RealEstateAsset.lot_number == item.get("number"))
        else:
            q = q.filter(RealEstateAsset.house_number == item.get("number"))
            
        existing = q.first()

        if existing:
            # 更新
            existing.property_type = p_type
            existing.ownership_share = item.get("share")
            if p_type == "Land":
                existing.land_category = item.get("category")
                existing.land_area = area_val
            else:
                existing.structure = item.get("structure")
                existing.floor_area = floor_area_str
                full_struct = f"{item.get('category', '')} {item.get('structure', '')}".strip()
                existing.structure = full_struct
        else:
            # 新規作成
            new_asset = RealEstateAsset(
                case_id=case_id,
                property_type=p_type,
                location=item.get("location"),
                ownership_share=item.get("share"),
            )
            
            if p_type == "Land":
                new_asset.lot_number = item.get("number")
                new_asset.land_category = item.get("category")
                new_asset.land_area = area_val
            else:
                new_asset.house_number = item.get("number")
                full_struct = f"{item.get('category', '')} {item.get('structure', '')}".strip()
                new_asset.structure = full_struct
                new_asset.floor_area = floor_area_str
            
            session.add(new_asset)
        
        count += 1
    
    return count

# ==========================================
# 5. メイン画面 UI
# ==========================================
def main():
    st.title("🏘️ 登記情報 自動読取")
    st.caption("登記情報(PDF/画像)をアップロードすると、**自動的に**AIが所在・地番・持分等を抽出します。")

    db = DatabaseManager()
    session = db._get_session()

    # ----------------------------------------------------
    # 案件選択 (Home共有)
    # ----------------------------------------------------
    target_case_id = st.session_state.get("selected_case_id")

    if not target_case_id:
        st.warning("⚠️ 案件が選択されていません。")
        st.info("Home画面またはサイドバーで案件を選択してください。")
        with st.expander("案件を選択する（未選択の場合）"):
            cases = session.query(Case).all()
            opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
            sel = st.selectbox("案件選択", list(opts.keys()))
            if st.button("この案件で作業を開始"):
                st.session_state["selected_case_id"] = opts[sel]
                st.rerun()
        return

    # 案件情報取得
    current_case = session.query(Case).options(joinedload(Case.deceased_ref)).get(target_case_id)
    if not current_case:
        st.error("案件情報の取得に失敗しました。")
        return

    d_name = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}" if current_case.deceased_ref else "未登録"
    st.success(f"📂 作業中の案件: **{current_case.case_number} {current_case.client_name}** 様 (被相続人: {d_name})")

    # ----------------------------------------------------
    # フォルダ操作エリア
    # ----------------------------------------------------
    with st.container(border=True):
        col_f1, col_f2 = st.columns([3, 1])
        curr_path = current_case.folder_path or ""
        
        with col_f1:
            new_path = st.text_input(
                "📂 案件フォルダパス", 
                value=curr_path, 
                placeholder=r"\\server\share\案件..."
            )
        
        with col_f2:
            st.write("") 
            st.write("")
            if st.button("フォルダを開く", use_container_width=True):
                if new_path:
                    open_local_folder(new_path)
                    if new_path != curr_path:
                        update_case_folder_path(target_case_id, new_path)
                else:
                    st.warning("パスが入力されていません")

    st.divider()

    # --- UI ---
    col_L, col_R = st.columns([1, 1.5])

    with col_L:
        st.subheader("1. 登記情報アップロード")
        # ★ポイント: keyを固定して再描画時もウィジェットの状態を維持
        uploaded_file = st.file_uploader("全部事項証明書など (PDF/画像)", type=["pdf", "png", "jpg", "jpeg"], key="touki_uploader")

        # ファイルがアップロードされているか確認
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            
            # --- 自動解析ロジック ---
            # ファイルの識別子 (名前 + サイズ) で新規ファイルか判定
            file_id = f"{uploaded_file.name}_{uploaded_file.size}"
            
            # まだ解析していないファイルなら自動実行
            if "last_analyzed_touki_file" not in st.session_state or st.session_state["last_analyzed_touki_file"] != file_id:
                if not d_name or d_name == "未登録":
                    st.warning("⚠️ 被相続人名が登録されていません。持分の特定が難しくなる可能性があります。")
                
                with st.spinner("🚀 ファイルを検知しました。AIが解析中です..."):
                    result = analyze_registry_with_ai(file_bytes, uploaded_file.type, target_name=d_name)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["touki_result"] = result
                        st.session_state["last_analyzed_touki_file"] = file_id # 解析済みフラグ更新
                        st.toast("解析完了！", icon="✅")
                        time.sleep(0.5)
                        st.rerun() # 結果表示のためにリロード

            # プレビュー表示
            if uploaded_file.type == "application/pdf":
                try:
                    images = convert_from_bytes(file_bytes, dpi=100, first_page=1, last_page=1)
                    if images: st.image(images[0], caption="プレビュー (1ページ目)", use_container_width=True)
                except:
                    st.warning("PDFプレビュー生成に失敗しました（解析は可能です）")
            else:
                st.image(file_bytes, caption="プレビュー", use_container_width=True)

    with col_R:
        st.subheader("2. 結果確認・登録")
        
        # 解析結果がある場合
        if "touki_result" in st.session_state and st.session_state["touki_result"]:
            res = st.session_state["touki_result"]
            assets = res.get("assets", [])
            
            if not assets:
                st.warning("不動産情報が見つかりませんでした。")
            else:
                st.markdown(f"**検出された不動産: {len(assets)}件**")
                
                # 編集用データフレーム作成
                df = pd.DataFrame(assets)
                if "area" in df.columns:
                    df["area"] = df["area"].astype(str)
                
                column_config = {
                    "type": st.column_config.SelectboxColumn("区分", options=["土地", "建物"], width="small"),
                    "location": st.column_config.TextColumn("所在", width="medium"),
                    "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                    "category": st.column_config.TextColumn("地目/種類", width="small"),
                    "area": st.column_config.TextColumn("地積/床面積", width="small"),
                    "structure": st.column_config.TextColumn("構造 (建物のみ)", width="medium"),
                    "share": st.column_config.TextColumn("持分", width="small"),
                }
                
                # ★Data Editor (編集結果を取得)
                edited_df = st.data_editor(
                    df,
                    column_config=column_config,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True,
                    key="touki_editor"
                )
                
                st.markdown("---")
                
                # ★追加: 遺言書用コピペテキスト生成エリア
                st.markdown("##### 📋 遺言書用テキスト (コピペ用)")
                will_text = generate_will_text(edited_df)
                st.text_area(
                    "以下のテキストをコピーしてWord等に貼り付けてください",
                    value=will_text,
                    height=200
                )
                
                st.markdown("---")
                
                # 保存ボタン
                if st.button("💾 データベースに登録", type="primary"):
                    try:
                        final_assets = edited_df.to_dict(orient="records")
                        count = save_real_estate_to_db(session, target_case_id, final_assets)
                        session.commit()
                        
                        st.toast(f"登録完了: {count}件の不動産を保存しました！", icon="✅")
                        
                        # 登録後も結果を表示し続けるため、touki_resultは削除しない
                        # ただし、登録済みであることを示す表示を追加してもよい
                        st.success("✅ データベースへの登録が完了しました。")
                        
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
                        session.rollback()
        else:
            st.info("👈 左側で登記情報をアップロードしてください（自動解析されます）。")
            st.markdown("""
            **読み取り項目:**
            - 所在、地番/家屋番号
            - 地目/種類、構造
            - 地積/床面積
            - **被相続人の持分** (甲区の権利者情報から判定)
            """)

    session.close()

if __name__ == "__main__":
    main()