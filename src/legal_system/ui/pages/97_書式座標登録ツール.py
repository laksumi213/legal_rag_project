# src/legal_system/ui/pages/97_書式座標登録ツール.py

import hashlib
import os
import sys
import time
import uuid
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

# PDF・画像処理ライブラリ
from pdf2image import convert_from_bytes
from PIL import ImageDraw, ImageFont
from pypdf import PdfReader
from legal_system.utils.pdf_utils import apply_coordinates_to_pdf
# ReportLab関連のインポートはpdf_utilsに移動したため、ここでは削除
from streamlit_drawable_canvas import st_canvas

# ==========================================
# 1. パス解決 & 初期設定
# ==========================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager

# テンプレート保存ディレクトリ
TEMPLATES_DIR = os.path.join(ROOT_DIR, "data", "templates")

# ページ設定
st.set_page_config(layout="wide", page_title="書式・座標管理", page_icon="🛠️")

# フォント設定 (ImageFontで使うためFONT_PATHの定義は残す)
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
# pdfmetrics.registerFont は pdf_utils.py に移動したため削除

db = DatabaseManager()
user_info = db.get_current_user_info()


# ==========================================
# 2. ヘルパー関数 & プリセット定義
# ==========================================
def calculate_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()


def get_wareki(dt):
    if dt.year >= 2019:
        return f"令和{dt.year - 2018}"
    return str(dt.year)


def split_phone_number(phone_str):
    parts = ["", "", ""]
    if phone_str:
        phone_str = phone_str.replace("ー", "-").replace("−", "-")
        splits = phone_str.split("-")
        for i in range(min(len(splits), 3)):
            parts[i] = splits[i]
    return parts


user_phone_parts = split_phone_number(user_info.get("phone", ""))
COMPANY_INFO = {
    "zip1": "100",
    "zip2": "0001",
    "address": "東京都千代田区千代田1-1",
    "name": "行政書士法人未来",
    "rep_name": "行政書士 山田 太郎",
}
today = datetime.now()
wareki_year = get_wareki(today)

PRESETS = {
    "（選択なし）": {"label": "", "val": ""},

    # --- 被相続人 ---
    "----- ★被相続人 -----": {"label": "", "val": ""},
    "{被相続人 氏名(全)}": {"label": "被相続人氏名", "val": "{deceased_name}"},
    "{被相続人 氏(姓)}": {"label": "被相続人_姓", "val": "{deceased_name_last}"},
    "{被相続人 名}": {"label": "被相続人_名", "val": "{deceased_name_first}"},
    "{被相続人 最後の住所}": {"label": "被相続人住所", "val": "{deceased_address}"}, # 追加
    "{被相続人 本籍}": {"label": "被相続人本籍", "val": "{deceased_hometown}"}, # 追加
    "{死亡日 (和暦全)}": {"label": "被相続人死亡日", "val": "{death_date}"},
    "{死亡日 年(西暦)}": {"label": "死亡日_西暦年", "val": "{death_year_seireki}"},
    "{死亡日 年(和暦)}": {"label": "死亡日_和暦年", "val": "{death_year_wareki}"},
    "{死亡日 月}": {"label": "死亡日_月", "val": "{death_month}"},
    "{死亡日 日}": {"label": "死亡日_日", "val": "{death_day}"},
    
    # --- 相続人（代表者） ---
    "----- ★相続人（代表） -----": {"label": "", "val": ""},
    "{相続人 氏名(全)}": {"label": "相続人氏名", "val": "{heir_name}"},
    "{相続人 氏(姓)}": {"label": "相続人_姓", "val": "{heir_name_last}"},
    "{相続人 名}": {"label": "相続人_名", "val": "{heir_name_first}"},
    "{相続人 生年月日 (和暦全)}": {"label": "相続人生年月日", "val": "{heir_birthday}"},
    "{相続人 生年月日 年(西暦)}": {"label": "相続人_西暦年", "val": "{heir_birthday_year_seireki}"},
    "{相続人 生年月日 年(和暦)}": {"label": "相続人_和暦年", "val": "{heir_birthday_year_wareki}"},
    "{相続人 生年月日 月}": {"label": "相続人_月", "val": "{heir_birthday_month}"},
    "{相続人 生年月日 日}": {"label": "相続人_日", "val": "{heir_birthday_day}"},
    "{相続人 続柄}": {"label": "相続人続柄", "val": "{heir_rel}"},
    "{相続人 代理人氏名}": {"label": "相続人_代理人", "val": "{heir_name} 代理人"},
    "{相続人 住所(全)}": {"label": "相続人住所", "val": "{heir_address}"},
    "{相続人 都道府県}": {"label": "相続人_都道府県", "val": "{heir_pref}"},
    "{相続人 市区町村}": {"label": "相続人_市区町村", "val": "{heir_city}"},
    "{相続人 番地}": {"label": "相続人_番地", "val": "{heir_street}"},
    "{相続人 建物名}": {"label": "相続人_建物", "val": "{heir_building}"},
    
    # --- 不動産 (Context Aware) ---
    "----- ★対象不動産 -----": {"label": "", "val": ""},
    "{不動産 所在}": {"label": "不動産所在", "val": "{prop_location}"},
    "{不動産 地番/家屋番号}": {"label": "地番_家屋番号", "val": "{prop_number}"},
    "{不動産 地目/種類}": {"label": "地目_種類", "val": "{prop_category}"},
    "{不動産 地積/床面積}": {"label": "地積_床面積", "val": "{prop_area}"},

    # --- その他 ---
    "----- 図形・記号・担当者 -----": {"label": "", "val": ""},
    "四角形枠": {"label": "枠線", "val": "RECT:30x30", "width": 30.0, "height": 30.0, "size": 1.0},
    "数字「1」": {"label": "数字1", "val": "1", "size": 11.0},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14.0},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14.0},
    "代理人ラベル": {"label": "代理人ラベル", "val": "代理人"},
    "被相続人ラベル": {"label": "被相続人ラベル", "val": "被相続人"},

    "----- 担当者・会社 -----": {"label": "", "val": ""},
    "会社住所": {"label": "会社住所", "val": COMPANY_INFO["address"]},
    "会社代表者 (固定)": {"label": "会社代表者", "val": "行政書士法人チェスター　代表社員　清水　茜作", "desc": "固定文字列"},
    "案件ID (G番号)": {"label": "案件ID", "val": "{case_number}", "desc": "G●●"},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]}
}

# ---------------------------------------------------------
# ★ステート初期化
# ---------------------------------------------------------
if st.session_state.get("trigger_reset"):
    st.session_state["input_label"] = ""
    st.session_state["input_val"] = ""
    st.session_state["input_desc"] = ""
    st.session_state["preset_sel"] = "（選択なし）"
    st.session_state["trigger_reset"] = False

if "editor_key" not in st.session_state:
    st.session_state["editor_key"] = str(uuid.uuid4())

if "current_ids" not in st.session_state:
    st.session_state["current_ids"] = []

if "current_file_hash" not in st.session_state:
    st.session_state["current_file_hash"] = None

if "last_x" not in st.session_state:
    st.session_state["last_x"] = 0
if "last_y" not in st.session_state:
    st.session_state["last_y"] = 0
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1

if "target_file_bytes" not in st.session_state:
    st.session_state["target_file_bytes"] = None
if "target_file_name" not in st.session_state:
    st.session_state["target_file_name"] = None

# 入力フォーム用
if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 11.0  # ★初期値11.0
if "input_width" not in st.session_state:
    st.session_state["input_width"] = 0.0
if "input_height" not in st.session_state:
    st.session_state["input_height"] = 0.0
if "input_desc" not in st.session_state:
    st.session_state["input_desc"] = ""
if "preset_sel" not in st.session_state:
    st.session_state["preset_sel"] = "（選択なし）"


# ==========================================
# ★コールバック関数
# ==========================================
def on_data_editor_change():
    """テーブル編集時のコールバック"""
    current_key = st.session_state.get("editor_key", "editor")
    if current_key not in st.session_state:
        return

    changes = st.session_state[current_key]
    needs_refresh = False

    # 新規追加
    if changes["added_rows"]:
        for new_row in changes["added_rows"]:
            label = new_row.get("label", "新規項目")

            # 手動追加時の重複チェック
            current_hash = st.session_state.get("current_file_hash")
            new_label = label
            if current_hash:
                current_coords = db.get_coordinates_by_hash(current_hash)
                existing_labels = [c["label"] for c in current_coords]
                count = 1
                while new_label in existing_labels:
                    count += 1
                    new_label = f"{label}_{count}"

            db.register_coordinate(
                file_hash=st.session_state["current_file_hash"],
                label=new_label,
                x=float(new_row.get("x", 100.0)),
                y=float(new_row.get("y", 100.0)),
                page_number=int(new_row.get("page", st.session_state["current_page"])),
                width=float(new_row.get("width", 0.0)),
                height=float(new_row.get("height", 0.0)),
                description="手動追加",
                font_size=float(new_row.get("font_size", 11.0)),
                color=new_row.get("color", "black"),
                test_value=new_row.get("value", ""),
            )
        st.toast("✅ 新規行を追加しました")
        needs_refresh = True

    # 編集
    if changes["edited_rows"]:
        id_list = st.session_state["current_ids"]
        for idx_str, row_changes in changes["edited_rows"].items():
            idx = int(idx_str)
            if idx < len(id_list):
                target_id = id_list[idx]
                if "font_size" in row_changes:
                    row_changes["font_size"] = float(row_changes["font_size"])
                if "width" in row_changes:
                    row_changes["width"] = float(row_changes["width"])
                if "height" in row_changes:
                    row_changes["height"] = float(row_changes["height"])
                db.update_coordinate_direct(int(target_id), row_changes)
        st.toast("✅ 変更を保存しました")

    # 削除
    if changes["deleted_rows"]:
        id_list = st.session_state["current_ids"]
        for idx in changes["deleted_rows"]:
            if int(idx) < len(id_list):
                target_id = id_list[int(idx)]
                db.delete_coordinate(int(target_id))
        st.toast("🗑️ 削除しました")
        needs_refresh = True

    if needs_refresh:
        st.session_state["editor_key"] = str(uuid.uuid4())


# ==========================================
# ★座標エディタ画面のロジック
# ==========================================
def render_coordinate_editor():
    # サイドバー: ファイル選択（新規アップロードは廃止）
    st.sidebar.header("📂 対象ファイル")
    all_files = db.get_template_files()
    
    if not all_files:
        st.sidebar.warning("登録済みの雛形ファイルがありません。")
        return

    file_options = [f["filename"] for f in all_files]
    
    # --- ファイル選択と読込ロジック (再修正) ---
    
    # 前回選択されたファイル名を取得
    last_selected = st.session_state.get("target_file_name")
    
    # ファイルリストからインデックスを決定
    idx = 0
    if last_selected and last_selected in file_options:
        idx = file_options.index(last_selected)

    # selectboxを表示
    selected_filename = st.sidebar.selectbox(
        "編集するファイルを選択",
        file_options,
        index=idx,
        key="sb_template_file" # キーを変更して衝突を避ける
    )

    # 選択が変更されたか、まだファイルが読み込まれていないかチェック
    if selected_filename != last_selected or st.session_state.get("target_file_bytes") is None:
        st.session_state["target_file_name"] = selected_filename
        st.session_state["current_page"] = 1

        file_path = os.path.join(TEMPLATES_DIR, selected_filename)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                st.session_state["target_file_bytes"] = f.read()
            # 状態を更新したので、一度だけ再実行してUI全体を正しく描画させる
            st.rerun()
        else:
            st.error(f"ファイルが見つかりません: {file_path}")
            # ファイルが見つからない場合はバイトデータをクリア
            st.session_state["target_file_bytes"] = None

    target_file_bytes = st.session_state.get("target_file_bytes")
    if not target_file_bytes:
        st.warning("対象ファイルがロードされていません。ファイルを選択してください。")
        return

    # PDF解析
    try:
        reader = PdfReader(BytesIO(target_file_bytes))
        media_box = reader.pages[0].mediabox
        pdf_w_pt = float(media_box.width)
        pdf_h_pt = float(media_box.height)

        images = convert_from_bytes(target_file_bytes, dpi=200)
        total_pages = len(images)

        p_idx = st.session_state["current_page"] - 1
        if p_idx >= total_pages:
            p_idx = 0

        # Current page image as bytes for st_canvas
        img_byte_arr = BytesIO()
        images[p_idx].save(img_byte_arr, format="PNG")
        st.session_state["current_page_image_bytes"] = img_byte_arr.getvalue()

    except Exception as e:
        st.error(f"解析エラー: {e}")
        return

    # ------------------------------------
    # メイン画面: 上部コントロール
    # ------------------------------------
    col_p, col_z, col_f = st.columns([1, 1.5, 1])
    with col_p:
        new_page = st.number_input(
            "ページ切替", 1, total_pages, st.session_state["current_page"]
        )
        if new_page != st.session_state["current_page"]:
            st.session_state["current_page"] = new_page
            st.rerun()
    with col_z:
        zoom_rate = st.slider("プレビュー倍率", 0.1, 1.5, 0.4, 0.05)
    with col_f:

        def on_def_size_change():
            st.session_state["input_size"] = st.session_state["def_font_size_key"]

        st.number_input(
            "基本サイズ(pt)",
            4.0,
            72.0,
            11.0,
            step=0.5,  # ★初期値11.0
            key="def_font_size_key",
            on_change=on_def_size_change,
        )

    # ------------------------------------
    # データ準備 & 画像処理
    # ------------------------------------
    file_hash = calculate_hash(target_file_bytes)
    st.session_state["current_file_hash"] = file_hash

    existing_coords = db.get_coordinates_by_hash(file_hash)
    if existing_coords:
        df_existing = pd.DataFrame(existing_coords)
        df_existing = df_existing.sort_values("id").reset_index(drop=True)
        st.session_state["current_ids"] = df_existing["id"].tolist()
    else:
        df_existing = pd.DataFrame()
        st.session_state["current_ids"] = []

    original_image = images[p_idx]
    orig_w_px, orig_h_px = original_image.size
    preview_scale = orig_h_px / pdf_h_pt
    display_image = original_image.resize(
        (int(orig_w_px * zoom_rate), int(orig_h_px * zoom_rate))
    )

    st.divider()

    # ------------------------------------
    # 2カラムレイアウト (画像:大 / 設定:小)
    # ------------------------------------
    col_img, col_ctrl = st.columns([2.5, 1.0])

    # ★重要: 右カラム（設定フォーム）を先に処理してリセットを防ぐ
    with col_ctrl:
        st.subheader("設定・登録")

        def on_preset_change():
            sel = st.session_state["preset_sel"]
            if sel in PRESETS and PRESETS[sel]["val"]:
                p = PRESETS[sel]
                base_label = p["label"]
                # 重複チェック
                existing_labels = (
                    df_existing["label"].tolist() if not df_existing.empty else []
                )
                new_label = base_label
                count = 1
                while new_label in existing_labels:
                    count += 1
                    new_label = f"{base_label}_{count}"

                st.session_state["input_label"] = new_label
                st.session_state["input_val"] = p["val"]
                if "size" in p:
                    st.session_state["input_size"] = float(p["size"])
                if "width" in p:
                    st.session_state["input_width"] = float(p["width"])
                if "height" in p:
                    st.session_state["input_height"] = float(p["height"])

        st.selectbox(
            "⚡️ プリセット",
            list(PRESETS.keys()),
            key="preset_sel",
            on_change=on_preset_change,
        )

        c1, c2 = st.columns([2, 1])
        label_in = c1.text_input("項目名", key="input_label")
        val_in = c2.text_input("値/タグ", key="input_val")
        c3, c4 = st.columns(2)
        size_in = c3.number_input(
            "サイズ", 0.5, 100.0, key="input_size", step=0.5, format="%.1f"
        )
        color_in = c4.selectbox("色", ["black", "red"], key="input_color")

        c5, c6 = st.columns(2)
        width_in = c5.number_input("幅", 0.0, 1000.0, key="input_width", step=1.0, format="%.1f")
        height_in = c6.number_input("高さ", 0.0, 1000.0, key="input_height", step=1.0, format="%.1f")

        desc_in = st.text_input("備考", key="input_desc")

        st.write(
            f"📍 X={st.session_state['last_x']:.1f} / Y={st.session_state['last_y']:.1f}"
        )

        if st.button("💾 登録する", type="primary", use_container_width=True):
            if not label_in:
                st.error("項目名必須")
            elif st.session_state["last_x"] == 0:
                st.error("画像をクリックしてください")
            else:
                success = db.register_coordinate(
                    file_hash=file_hash,
                    label=label_in,
                    x=st.session_state["last_x"],
                    y=st.session_state["last_y"],
                    width=float(width_in),
                    height=float(height_in),
                    page_number=st.session_state["current_page"],
                    description=desc_in,
                    font_size=float(size_in),
                    color=color_in,
                    test_value=val_in,
                )
                if success:
                    st.toast("✅ 登録完了")
                    st.session_state["trigger_reset"] = True
                    st.session_state["editor_key"] = str(uuid.uuid4())
                    time.sleep(0.5)
                    st.rerun()

    # --- 左カラム: 画像表示 (後続実行) ---
    with col_img:
        st.subheader("座標指定")
        draw_bg = display_image.copy()
        draw = ImageDraw.Draw(draw_bg)

        def draw_mark(raw_x, raw_y, val, sz, clr, w=None, h=None):
            dx = raw_x * zoom_rate
            dy = raw_y * zoom_rate
            vsz = int(float(sz) * preview_scale * zoom_rate)
            c = (255, 0, 0) if clr == "red" else (0, 0, 0)

            if str(val).startswith("RECT:") and w is not None and h is not None:
                w_px = w * preview_scale * zoom_rate
                h_px = h * preview_scale * zoom_rate
                lw = max(1, int(vsz / 10))
                draw.rectangle([dx, dy, dx + w_px, dy + h_px], outline=c, width=lw)
            elif val:
                try:
                    font = ImageFont.truetype(FONT_PATH, max(8, vsz))
                    draw.text((dx, dy), str(val), font=font, fill=c)
                except Exception as e:
                    print(f"Error drawing text: {e}")
                    pass

        if st.session_state["input_val"]:
            draw_mark(
                st.session_state["last_x"],
                st.session_state["last_y"],
                st.session_state["input_val"],
                size_in,
                color_in,
                width_in,
                height_in,
            )

        if not df_existing.empty:
            for _, c in df_existing.iterrows():
                if c["page"] == st.session_state["current_page"]:
                    draw_mark(c["x"], c["y"], c["value"], c["font_size"], c["color"], c["width"], c["height"])

        # width指定でズレ防止
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Orange with 30% opacity
            stroke_width=2,
            stroke_color="#FF0000",  # Red
            background_image=original_image, # Use original_image for canvas background
            update_streamlit=True,
            height=original_image.height,
            width=original_image.width,
            drawing_mode="rect",
            point_display_mode="point",
            key=f"canvas_{st.session_state['current_page']}_{zoom_rate}",
        )

        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if objects:
                last_object = objects[-1]  # 最後の描画オブジェクトを取得
                if last_object["type"] == "rect":
                    # st_canvasから取得する座標は描画領域内のピクセル座標なので、PDF座標に変換
                    # st_canvasのbackground_imageはdisplay_imageと同じサイズで表示しているため、そのまま利用できる
                    x_on_display = last_object["left"]
                    y_on_display = last_object["top"]
                    width_on_display = last_object["width"]
                    height_on_display = last_object["height"]

                    # PDF座標に変換 (ズーム倍率で逆算)
                    x_pdf = x_on_display / preview_scale
                    y_pdf = y_on_display / preview_scale
                    width_pdf = width_on_display / preview_scale
                    height_pdf = height_on_display / preview_scale

                    # 状態を更新
                    st.session_state["last_x"] = x_pdf
                    st.session_state["last_y"] = y_pdf
                    st.session_state["input_width"] = width_pdf
                    st.session_state["input_height"] = height_pdf

                    # フォームの値を更新
                    st.session_state["input_label"] = st.session_state["input_label"] if st.session_state["input_label"] else "新規枠"
                    st.session_state["preset_sel"] = "（選択なし）" # プリセット選択をリセット
                    st.rerun()

    # --- 下部: リストエリア ---
    st.divider()
    st.subheader("📋 登録済みリスト")

    cols = ["label", "x", "y", "width", "height", "page", "font_size", "color", "value", "desc", "id"]
    if not df_existing.empty:
        for c in cols:
            if c not in df_existing.columns:
                df_existing[c] = None
        df_show = df_existing[cols]
    else:
        df_show = pd.DataFrame(columns=cols)

    column_config = {
        "label": st.column_config.TextColumn("項目名", width="medium", required=True),
        "x": st.column_config.NumberColumn("X", format="%.1f", required=True),
        "y": st.column_config.NumberColumn("Y", format="%.1f", required=True),
        "width": st.column_config.NumberColumn("幅", format="%.1f", required=True),
        "height": st.column_config.NumberColumn("高さ", format="%.1f", required=True),
        "page": st.column_config.NumberColumn("P", width="small", min_value=1, step=1),
        "font_size": st.column_config.NumberColumn(
            "サイズ", width="small", min_value=1.0, step=0.5, format="%.1f"
        ),
        "color": st.column_config.SelectboxColumn(
            "色", width="small", options=["black", "red"], default="black"
        ),
        "value": st.column_config.TextColumn("値/タグ", width="medium"),
        "desc": st.column_config.TextColumn("備考", width="large"),
        "id": None,
    }

    st.data_editor(
        df_show,
        hide_index=True,
        use_container_width=True,
        column_config=column_config,
        num_rows="dynamic",
        key=st.session_state["editor_key"],
        on_change=on_data_editor_change,
    )

    if st.button("テストPDF作成 (全ページ)"):
        if df_existing.empty:
            st.error("座標なし")
        else:
            try:
                # apply_coordinates_to_pdf 関数に渡す座標データを準備
                # DataFrameから辞書のリストに変換
                coords_for_apply = df_existing.to_dict(orient="records")

                # PDFに座標を適用
                filled_pdf_stream = apply_coordinates_to_pdf(
                    original_pdf_bytes=target_file_bytes,
                    coordinates=coords_for_apply
                )

                st.download_button(
                    label="📥 テストPDFダウンロード",
                    data=filled_pdf_stream,
                    file_name="test_filled.pdf",
                    mime="application/pdf",
                )
                st.success("テストPDF作成完了！")

            except Exception as e:
                st.error(f"エラー: {e}")
                st.exception(e)

# ==========================================
# アプリケーション本体
# ==========================================
def main():
    # サイドバーで機能切り替え (統合管理ツール化)
    app_mode = st.sidebar.radio(
        "機能選択", ["📍 座標定義 (編集)", "📥 雛形ファイル登録", "🗑️ 登録データ管理"]
    )

    if app_mode == "📍 座標定義 (編集)":
        render_coordinate_editor()

    elif app_mode == "📥 雛形ファイル登録":
        st.title("📥 雛形ファイル登録")
        st.caption("PDFファイルをシステムにアップロードします。")
        from legal_system.ui.components.admin_tools import render_upload_tab

        render_upload_tab(db)

    elif app_mode == "🗑️ 登録データ管理":
        st.title("🗑️ 登録データ管理")
        st.caption("データベース内の全データを管理します。")
        from legal_system.ui.components.admin_tools import render_management_tab

        render_management_tab(db)


if __name__ == "__main__":
    main()
