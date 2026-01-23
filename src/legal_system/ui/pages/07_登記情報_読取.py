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
    登記情報を読み取り、土地・建物・マンションの情報を抽出する
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
    ※単独所有の場合は持分を "1/1" としてください。

    【抽出項目定義】
    1. **区分 (type)**: "土地", "建物", "マンション" のいずれか
       ※「敷地権付き区分建物」や「専有部分」の記載がある場合は "マンション" と判定してください。

    --- 共通項目 ---
    * **持分 (share)**: 対象者の持分 ("1/2"など)

    --- A. 土地の場合 ---
    * **所在 (location)**
    * **地番 (number)**
    * **地目 (category)**
    * **地積 (area)**: 数値のみ抽出 (例: 123.45)

    --- B. 建物（戸建）の場合 ---
    * **所在 (location)**
    * **家屋番号 (number)**
    * **種類 (category)**: 居宅など
    * **構造 (structure)**: 木造瓦葺2階建など
    * **床面積 (area)**: 文字列で可 (例: "1階 50.00 2階 40.00")

    --- C. マンション（区分所有建物）の場合 ---
    以下の詳細情報を抽出してください。ない項目は空文字またはnull。
    * **一棟_所在 (m_b_loc)**: 一棟の建物の表示 - 所在
    * **一棟_名称 (m_b_name)**: 一棟の建物の表示 - 建物の名称
    * **土地_符号 (m_l_sym)**: 敷地権の目的である土地 - 符号 (例: "1")。複数ある場合は代表または連結。
    * **土地_所在地番 (m_l_loc)**: 敷地権の目的である土地 - 所在及び地番
    * **土地_地目 (m_l_cat)**: 敷地権の目的である土地 - 地目
    * **土地_地積 (m_l_area)**: 敷地権の目的である土地 - 地積
    * **専有_家屋番号 (number)**: 専有部分の建物の表示 - 家屋番号
    * **専有_名称 (m_p_name)**: 専有部分の建物の表示 - 建物の名称 (部屋番号など)
    * **専有_種類 (category)**: 専有部分の建物の表示 - 種類 (例: "居宅")
    * **専有_構造 (structure)**: 専有部分の建物の表示 - 構造
    * **専有_床面積 (area)**: 専有部分の建物の表示 - 床面積
    * **敷地権_種類 (m_r_type)**: 敷地権の表示 - 敷地権の種類 (例: "所有権")
    * **敷地権_割合 (m_r_ratio)**: 敷地権の表示 - 敷地権の割合

    【出力JSONスキーマ】
    {{
        "assets": [
            {{
                "type": "土地",
                "location": "...", "number": "...", "category": "...", "area": 100.5, "share": "1/1"
            }},
            {{
                "type": "マンション",
                "m_b_loc": "〇〇市〇〇区...",
                "m_b_name": "ライオンズマンション...",
                "m_l_sym": "1",
                "m_l_loc": "〇〇市〇〇区...",
                "m_l_cat": "宅地",
                "m_l_area": "1234.56",
                "number": "家屋番号...",
                "m_p_name": "201",
                "category": "居宅",
                "structure": "鉄筋コンクリート造...",
                "area": "70.55",
                "m_r_type": "所有権",
                "m_r_ratio": "1000分の50",
                "share": "1/1"
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
        share = row.get("share", "")
        
        # --- A. 土地 ---
        if p_type == "土地":
            text_lines.append(f"{num_prefix}\t土地")
            text_lines.append(f"{sp}所在{sp}{row.get('location', '')}")
            text_lines.append(f"{sp}地番{sp}{row.get('number', '')}")
            text_lines.append(f"{sp}地目{sp}{row.get('category', '')}")
            text_lines.append(f"{sp}地積{sp}{row.get('area', '')}㎡")
            text_lines.append(f"{sp}持分{sp}{share}")
            
        # --- B. マンション (区分所有) ---
        elif p_type == "マンション":
            text_lines.append(f"{num_prefix}\tマンション")
            
            text_lines.append(f"（一棟の建物の表示）")
            text_lines.append(f"{sp}所在{sp}{row.get('m_b_loc', '')}")
            text_lines.append(f"{sp}建物の名称{sp}{row.get('m_b_name', '')}")
            
            text_lines.append(f"（敷地権の目的である土地の表示）")
            text_lines.append(f"{sp}土地の符号{sp}{row.get('m_l_sym', '1')}")
            text_lines.append(f"{sp}所在及び地番{sp}{row.get('m_l_loc', '')}")
            text_lines.append(f"{sp}地目{sp}{row.get('m_l_cat', '')}")
            text_lines.append(f"{sp}地積{sp}{row.get('m_l_area', '')}㎡")
            
            text_lines.append(f"（専有部分の建物の表示）")
            text_lines.append(f"{sp}家屋番号{sp}{row.get('number', '')}")
            text_lines.append(f"{sp}建物の名称{sp}{row.get('m_p_name', '')}")
            text_lines.append(f"{sp}種類{sp}{row.get('category', '')}")
            text_lines.append(f"{sp}構造{sp}{row.get('structure', '')}")
            text_lines.append(f"{sp}床面積{sp}{row.get('area', '')}㎡")
            
            text_lines.append(f"（敷地権の表示）")
            text_lines.append(f"{sp}土地の符号{sp}{row.get('m_l_sym', '1')}")
            text_lines.append(f"{sp}敷地権の種類{sp}{row.get('m_r_type', '')}")
            text_lines.append(f"{sp}敷地権の割合{sp}{row.get('m_r_ratio', '')}")
            
            # マンションの持分（専有部分の所有権の持分）
            if share and share != "1/1":
                text_lines.append(f"{sp}持分{sp}{share}")

        # --- C. 建物 (戸建) ---
        else:
            text_lines.append(f"{num_prefix}\t建物")
            text_lines.append(f"{sp}所在{sp}{row.get('location', '')}")
            text_lines.append(f"{sp}家屋番号{sp}{row.get('number', '')}")
            text_lines.append(f"{sp}種類{sp}{row.get('category', '')}")
            text_lines.append(f"{sp}構造{sp}{row.get('structure', '')}")
            text_lines.append(f"{sp}床面積{sp}{row.get('area', '')}㎡")
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
        p_type_raw = item.get("type", "")
        # DB上の種別マッピング
        if p_type_raw == "土地":
            db_type = "Land"
        elif p_type_raw == "マンション":
            db_type = "Condo"
        else:
            db_type = "Building"
        
        # 面積の数値変換（可能な場合）
        area_val = None
        floor_area_str = str(item.get("area", ""))
        
        if db_type == "Land":
            try:
                # 文字列から数値抽出 ("100.23㎡" -> 100.23)
                match = re.search(r"(\d+(\.\d+)?)", floor_area_str)
                if match:
                    area_val = float(match.group(1))
            except: pass

        # 所在・番号の取得
        # マンションの場合、DBのlocationには一棟の所在、numberには専有家屋番号を入れるのが一般的
        loc = item.get("location") or item.get("m_b_loc")
        num = item.get("number")

        # 重複チェック (簡易)
        q = session.query(RealEstateAsset).filter(
            RealEstateAsset.case_id == case_id,
            RealEstateAsset.location == loc,
        )
        if db_type == "Land":
            q = q.filter(RealEstateAsset.lot_number == num)
        else:
            q = q.filter(RealEstateAsset.house_number == num)
            
        existing = q.first()

        # 値の構築
        if db_type == "Land":
            land_cat = item.get("category")
            land_area = area_val
            struc = None
            fl_area = None
        elif db_type == "Condo":
            # マンションの場合、構造などの詳細を structure カラムに詰め込むか検討が必要だが
            # ここではシンプルに専有部分の情報を保存する
            land_cat = None
            land_area = None
            struc = item.get("structure")
            fl_area = floor_area_str
        else:
            land_cat = None
            land_area = None
            struc = f"{item.get('category', '')} {item.get('structure', '')}".strip()
            fl_area = floor_area_str

        if existing:
            # 更新
            existing.property_type = db_type
            existing.ownership_share = item.get("share")
            existing.land_category = land_cat
            existing.land_area = land_area
            existing.structure = struc
            existing.floor_area = fl_area
        else:
            # 新規作成
            new_asset = RealEstateAsset(
                case_id=case_id,
                property_type=db_type,
                location=loc,
                ownership_share=item.get("share"),
                lot_number=num if db_type == "Land" else None,
                house_number=num if db_type != "Land" else None,
                land_category=land_cat,
                land_area=land_area,
                structure=struc,
                floor_area=fl_area
            )
            session.add(new_asset)
        
        count += 1
    
    return count

# ==========================================
# 5. メイン画面 UI
# ==========================================
def main():
    st.title("🏘️ 登記情報 自動読取")
    st.caption("登記情報(PDF/画像)をアップロードすると、**自動的に**AIが情報を抽出し、遺言書用の形式で出力します。")

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
                # 型エラー回避のため文字列化
                for col in ["area", "m_l_area"]:
                    if col in df.columns:
                        df[col] = df[col].astype(str)
                
                # カラム設定 (マンション用のカラムを追加)
                column_config = {
                    "type": st.column_config.SelectboxColumn("区分", options=["土地", "建物", "マンション"], width="small", required=True),
                    "share": st.column_config.TextColumn("持分", width="small"),
                    # --- 土地・建物 ---
                    "location": st.column_config.TextColumn("所在(土地/建物)", width="medium"),
                    "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                    "category": st.column_config.TextColumn("地目/種類", width="small"),
                    "area": st.column_config.TextColumn("地積/床面積", width="small"),
                    "structure": st.column_config.TextColumn("構造", width="medium"),
                    # --- マンション用 (隠さずに表示) ---
                    "m_b_loc": st.column_config.TextColumn("[M]一棟所在"),
                    "m_b_name": st.column_config.TextColumn("[M]建物名称"),
                    "m_l_loc": st.column_config.TextColumn("[M]土地所在"),
                    "m_p_name": st.column_config.TextColumn("[M]専有名称"),
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
                    height=300
                )
                
                st.markdown("---")
                
                # 保存ボタン
                if st.button("💾 データベースに登録", type="primary"):
                    try:
                        final_assets = edited_df.to_dict(orient="records")
                        count = save_real_estate_to_db(session, target_case_id, final_assets)
                        session.commit()
                        
                        st.toast(f"登録完了: {count}件の不動産を保存しました！", icon="✅")
                        
                        # 登録後も結果を表示し続ける
                        st.success("✅ データベースへの登録が完了しました。")
                        
                    except Exception as e:
                        st.error(f"登録エラー: {e}")
                        session.rollback()
        else:
            st.info("👈 左側で登記情報をアップロードしてください（自動解析されます）。")
            st.markdown("""
            **対応フォーマット:**
            - 土地
            - 建物（戸建）
            - **マンション（区分所有建物）** ← New!
            """)

    session.close()

if __name__ == "__main__":
    main()