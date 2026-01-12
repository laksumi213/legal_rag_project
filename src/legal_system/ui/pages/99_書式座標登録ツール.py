# src/legal_system/ui/pages/99_書式座標登録ツール.py

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
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from streamlit_image_coordinates import streamlit_image_coordinates

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
st.set_page_config(layout="wide", page_title="書式座標登録", page_icon="📍")
st.title("📍 銀行書式・座標登録ツール")
st.caption("PDF書式に文字を入れる位置（座標）を設定・修正するツールです。")

# フォント設定
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

db = DatabaseManager()
user_info = db.get_current_user_info()


# ==========================================
# 2. ヘルパー関数 & プリセット定義
# ==========================================
def calculate_hash(file_bytes):
    """ファイルのMD5ハッシュ値を計算"""
    return hashlib.md5(file_bytes).hexdigest()


def get_wareki(dt):
    """日付を和暦(令和)に変換"""
    if dt.year >= 2019:
        return f"令和{dt.year - 2018}"
    return str(dt.year)


def split_phone_number(phone_str):
    """電話番号をハイフンで3つに分割"""
    parts = ["", "", ""]
    if phone_str:
        phone_str = phone_str.replace("ー", "-").replace("−", "-")
        splits = phone_str.split("-")
        for i in range(min(len(splits), 3)):
            parts[i] = splits[i]
    return parts


user_phone_parts = split_phone_number(user_info.get("phone", ""))
COMPANY_INFO = {
    "zip1": "103",
    "zip2": "0028",
    "address": "東京都中央区八重洲",
    "name": "行政書士法人チェスター",
    "rep_name": "代表社員 清水 茜作",
}
today = datetime.now()
wareki_year = get_wareki(today)

# プリセット定義 (よく使う項目)
PRESETS = {
    "（選択なし）": {"label": "", "val": ""},
    "----- ★DB連携: 氏名 -----": {"label": "", "val": ""},
    "{被相続人 氏名(全)}": {"label": "被相続人氏名", "val": "{deceased_name}"},
    "{被相続人 氏(姓)}": {"label": "被相続人_姓", "val": "{deceased_name_last}"},
    "{被相続人 名}": {"label": "被相続人_名", "val": "{deceased_name_first}"},
    "{相続人 氏名(全)}": {"label": "相続人氏名", "val": "{heir_name}"},
    "{相続人 氏(姓)}": {"label": "相続人_姓", "val": "{heir_name_last}"},
    "{相続人 名}": {"label": "相続人_名", "val": "{heir_name_first}"},
    "----- ★DB連携: 死亡日 -----": {"label": "", "val": ""},
    "{死亡日 (和暦全)}": {"label": "被相続人死亡日", "val": "{death_date}"},
    "{死亡日 年(西暦)}": {"label": "死亡日_西暦年", "val": "{death_year_seireki}"},
    "{死亡日 年(和暦)}": {"label": "死亡日_和暦年", "val": "{death_year_wareki}"},
    "{死亡日 月}": {"label": "死亡日_月", "val": "{death_month}"},
    "{死亡日 日}": {"label": "死亡日_日", "val": "{death_day}"},
    "----- ★DB連携: 住所 -----": {"label": "", "val": ""},
    "{相続人 住所(全)}": {"label": "相続人住所", "val": "{heir_address}"},
    "{相続人 都道府県}": {"label": "相続人_都道府県", "val": "{heir_pref}"},
    "{相続人 市区町村}": {"label": "相続人_市区町村", "val": "{heir_city}"},
    "{相続人 番地}": {"label": "相続人_番地", "val": "{heir_street}"},
    "{相続人 建物名}": {"label": "相続人_建物", "val": "{heir_building}"},
    "----- 図形・記号 -----": {"label": "", "val": ""},
    "四角形枠": {"label": "枠線", "val": "RECT:30x30"},
    "数字「1」": {"label": "数字1", "val": "1", "size": 11},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14},
    "----- 担当者・会社 -----": {"label": "", "val": ""},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]},
    "相続人 ◯◯": {"label": "相続人 ◯◯", "val": "相続人 " + "heir_name", "size": 10},
    "代理人 全部記載": {
        "label": "代理人",
        "val": "代理人 行政書士法人チェスター 代表社員 清水 茜作",
        "size": 8,
    },
    "代理人 会社名のみ記載": {
        "label": "代理人 行政書士法人チェスター",
        "val": "代理人 行政書士法人チェスター",
        "size": 10,
    },
    "代理人 代表社員のみ記載": {
        "label": "代理人 代表社員",
        "val": "代表社員 清水 茜作",
        "size": 10,
    },
    "会社住所": {"label": "会社住所", "val": COMPANY_INFO["address"]},
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

if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 11.0
if "input_desc" not in st.session_state:
    st.session_state["input_desc"] = ""
if "preset_sel" not in st.session_state:
    st.session_state["preset_sel"] = "（選択なし）"


# ==========================================
# 3. サイドバー: ファイル管理 & 設定
# ==========================================
target_file_bytes = st.session_state["target_file_bytes"]
target_file_name = st.session_state["target_file_name"]
file_hash = None
existing_coords = []
df_existing = pd.DataFrame()

with st.sidebar:
    st.header("📂 対象ファイル")

    mode = st.radio(
        "ソース選択",
        ("📂 新規アップロード", "🗂 登録済み雛形から選択"),
        index=1,
        horizontal=True,
    )

    if mode == "📂 新規アップロード":
        uploaded_file = st.file_uploader("帳票PDFをアップロード", type="pdf")
        if uploaded_file:
            bytes_data = uploaded_file.read()
            if st.session_state["target_file_bytes"] != bytes_data:
                st.session_state["target_file_bytes"] = bytes_data
                st.session_state["target_file_name"] = uploaded_file.name
                st.rerun()
    else:
        all_files = db.get_all_files()
        if all_files:
            file_options = {f"{f['filename']}": f for f in all_files}
            idx = 0
            if target_file_name:
                keys = list(file_options.keys())
                for i, k in enumerate(keys):
                    if target_file_name in k:
                        idx = i
                        break

            selected_label = st.selectbox(
                "ファイルを選択", list(file_options.keys()), index=idx
            )

            if selected_label:
                selected_data = file_options[selected_label]
                fname = selected_data["filename"]

                if st.session_state["target_file_name"] != fname:
                    file_path = os.path.join(TEMPLATES_DIR, fname)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            st.session_state["target_file_bytes"] = f.read()
                        st.session_state["target_file_name"] = fname
                        st.session_state["current_page"] = 1
                        st.rerun()

    target_file_bytes = st.session_state["target_file_bytes"]
    target_file_name = st.session_state["target_file_name"]

    if target_file_bytes:
        try:
            tmp_reader = PdfReader(BytesIO(target_file_bytes))
            total_pages = len(tmp_reader.pages)
            st.divider()
            st.write("📄 **ページ切替**")
            if total_pages > 1:
                new_p = st.number_input(
                    f"表示ページ (全{total_pages}枚)",
                    1,
                    total_pages,
                    st.session_state["current_page"],
                )
                if new_p != st.session_state["current_page"]:
                    st.session_state["current_page"] = new_p
                    st.rerun()
            else:
                st.caption("1ページのみ")
        except Exception:
            pass

    st.divider()
    st.subheader("🔍 表示設定")
    zoom_rate = st.slider("プレビュー倍率", 0.1, 1.5, 0.3, 0.05)

    if target_file_bytes:
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

    st.divider()
    st.header("⚙️ フォント設定")

    def on_def_size_change():
        st.session_state["input_size"] = st.session_state["def_font_size_key"]

    def_font_size = st.number_input(
        "基本フォントサイズ (pt)",
        4.0,
        72.0,
        11.0,
        step=0.5,
        key="def_font_size_key",
        on_change=on_def_size_change,
    )

# ==========================================
# 4. メインエリア (解析 & 表示)
# ==========================================
if not target_file_bytes:
    st.info("👈 サイドバーからファイルを選択してください。")
    st.stop()

# --- PDF解析 ---
try:
    reader = PdfReader(BytesIO(target_file_bytes))
    media_box = reader.pages[0].mediabox
    pdf_w_pt, pdf_h_pt = float(media_box.width), float(media_box.height)

    # 画像変換 (DPI 200)
    images = convert_from_bytes(target_file_bytes, dpi=200)

    p_idx = st.session_state["current_page"] - 1
    if p_idx >= len(images):
        p_idx = 0

    original_image = images[p_idx]
    orig_w_px, orig_h_px = original_image.size
    preview_scale = orig_h_px / pdf_h_pt
    display_image = original_image.resize(
        (int(orig_w_px * zoom_rate), int(orig_h_px * zoom_rate))
    )
except Exception as e:
    st.error(f"解析エラー: {e}")
    st.stop()


# ---------------------------------------------------------
# ★コールバック関数
# ---------------------------------------------------------
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
                file_hash=file_hash,
                label=new_label,
                x=float(new_row.get("x", 100.0)),
                y=float(new_row.get("y", 100.0)),
                page_number=int(new_row.get("page", st.session_state["current_page"])),
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
# レイアウト (2カラム)
# ==========================================
col_img, col_ctrl = st.columns([1.8, 1.2])

# --- 右カラム: 入力パネル ---
with col_ctrl:
    st.subheader("2. 設定と登録")

    def on_preset_change():
        sel = st.session_state["preset_sel"]
        if sel in PRESETS and PRESETS[sel]["val"]:
            p = PRESETS[sel]
            base_label = p["label"]

            # DBから最新リストを取得して重複チェック
            current_hash = st.session_state.get("current_file_hash")
            existing_labels = []
            if current_hash:
                coords = db.get_coordinates_by_hash(current_hash)
                existing_labels = [c["label"] for c in coords]

            new_label = base_label
            count = 1
            while new_label in existing_labels:
                count += 1
                new_label = f"{base_label}_{count}"

            st.session_state["input_label"] = new_label
            st.session_state["input_val"] = p["val"]
            if "size" in p:
                st.session_state["input_size"] = float(p["size"])

    st.selectbox(
        "⚡️ プリセット",
        list(PRESETS.keys()),
        key="preset_sel",
        on_change=on_preset_change,
    )

    c1, c2 = st.columns([2, 1])
    label_in = c1.text_input("項目名", key="input_label")
    val_in = c2.text_input("テスト値/タグ", key="input_val")
    c3, c4 = st.columns(2)
    size_in = c3.number_input("サイズ(pt)", 0.5, 100.0, key="input_size")
    color_in = c4.selectbox("文字色", ["black", "red"], key="input_color")
    desc_in = st.text_input("備考", key="input_desc")

    st.write(
        f"📍 座標(原寸): X={st.session_state['last_x']:.1f} / Y={st.session_state['last_y']:.1f}"
    )

    if st.button("💾 登録する", type="primary", use_container_width=True):
        if not label_in:
            st.error("項目名は必須です")
        elif st.session_state["last_x"] == 0:
            st.error("画像をクリックしてください")
        else:
            success = db.register_coordinate(
                file_hash=file_hash,
                label=label_in,
                x=st.session_state["last_x"],
                y=st.session_state["last_y"],
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

    st.divider()
    st.subheader("📋 登録済みリスト")

    # 表示用カラム定義
    cols = ["label", "x", "y", "page", "font_size", "color", "value", "desc", "id"]

    if not df_existing.empty:
        # DBにカラムがない場合のガード処理
        for c in cols:
            if c not in df_existing.columns:
                df_existing[c] = None  # またはデフォルト値

        df_show = df_existing[cols]
    else:
        df_show = pd.DataFrame(columns=cols)

    # データエディタ設定
    column_config = {
        "label": st.column_config.TextColumn("項目名", width="medium", required=True),
        "x": st.column_config.NumberColumn("X", format="%.1f", required=True),
        "y": st.column_config.NumberColumn("Y", format="%.1f", required=True),
        "page": st.column_config.NumberColumn("P", width="small", min_value=1, step=1),
        "font_size": st.column_config.NumberColumn(
            "サイズ", width="small", min_value=1.0, step=0.5, format="%.1f"
        ),
        "color": st.column_config.SelectboxColumn(
            "色", width="small", options=["black", "red"], default="black"
        ),
        "value": st.column_config.TextColumn("値/タグ", width="medium"),
        "desc": st.column_config.TextColumn("備考", width="large"),
        "id": None,  # ID列は隠す
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

    # テスト出力
    st.divider()
    if st.button("テストPDF作成", use_container_width=True):
        if df_existing.empty:
            st.error("座標なし")
        else:
            try:
                output = PdfWriter()
                for i, page_obj in enumerate(reader.pages):
                    page_num = i + 1
                    page_coords = df_existing[df_existing["page"] == page_num]

                    if not page_coords.empty:
                        packet_page = BytesIO()
                        pw = float(page_obj.mediabox.width)
                        ph = float(page_obj.mediabox.height)
                        can_page = canvas.Canvas(packet_page, pagesize=(pw, ph))

                        for _, row in page_coords.iterrows():
                            val = row["value"]
                            if not val:
                                continue

                            scale_x = pw / orig_w_px
                            scale_y = ph / orig_h_px

                            x = float(row["x"])
                            y = float(row["y"])
                            f_size = float(row["font_size"])
                            c_obj = red if row["color"] == "red" else black
                            can_page.setFillColor(c_obj)
                            can_page.setStrokeColor(c_obj)

                            draw_x = x * scale_x
                            draw_y_base = ph - (y * scale_y)

                            if str(val).startswith("RECT:"):
                                try:
                                    dims = val.replace("RECT:", "").split("x")
                                    w_pt, h_pt = float(dims[0]), float(dims[1])
                                    can_page.setLineWidth(f_size)
                                    can_page.rect(
                                        draw_x,
                                        draw_y_base - h_pt,
                                        w_pt,
                                        h_pt,
                                        stroke=1,
                                        fill=0,
                                    )
                                except:
                                    pass
                            else:
                                can_page.setFont("IPAexG", f_size)
                                can_page.drawString(
                                    draw_x, draw_y_base - (f_size * 0.8), str(val)
                                )

                        can_page.save()
                        packet_page.seek(0)
                        overlay = PdfReader(packet_page)
                        page_obj.merge_page(overlay.pages[0])
                    output.add_page(page_obj)

                out_stream = BytesIO()
                output.write(out_stream)
                st.download_button(
                    "📥 ダウンロード", out_stream, "test_filled.pdf", "application/pdf"
                )
            except Exception as e:
                st.error(f"作成エラー: {e}")

# --- 左カラム: 画像表示 ---
with col_img:
    st.subheader("1. 座標指定")
    draw_bg = display_image.copy()
    draw = ImageDraw.Draw(draw_bg)

    def draw_mark(raw_x, raw_y, val, sz, clr):
        # ★修正: リサイズ後の画像の幅を超えないようにする
        dx = raw_x * zoom_rate
        dy = raw_y * zoom_rate

        vsz = int(float(sz) * preview_scale * zoom_rate)
        c = (255, 0, 0) if clr == "red" else (0, 0, 0)

        if not val:
            return

        if str(val).startswith("RECT:"):
            try:
                dims = val.replace("RECT:", "").split("x")
                w_pt, h_pt = float(dims[0]), float(dims[1])
                w_px = w_pt * preview_scale * zoom_rate
                h_px = h_pt * preview_scale * zoom_rate
                lw = max(1, int(vsz / 10))
                draw.rectangle([dx, dy, dx + w_px, dy + h_px], outline=c, width=lw)
            except:
                pass
        else:
            try:
                font = ImageFont.truetype(FONT_PATH, max(8, vsz))
                draw.text((dx, dy), str(val), font=font, fill=c)
            except:
                pass

    # プレビュー描画
    if st.session_state["input_val"]:
        draw_mark(
            st.session_state["last_x"],
            st.session_state["last_y"],
            st.session_state["input_val"],
            size_in,
            color_in,
        )

    # リスト描画
    for _, c in df_existing.iterrows():
        if c["page"] == st.session_state["current_page"]:
            draw_mark(c["x"], c["y"], c["value"], c["font_size"], c["color"])

    # ★修正: widthを明示的に指定してズレを防ぐ
    value = streamlit_image_coordinates(
        draw_bg,
        width=display_image.width,
        key=f"c_{st.session_state['current_page']}_{zoom_rate}",
    )

    if value:
        ox = value["x"] / zoom_rate
        oy = value["y"] / zoom_rate

        if (
            abs(ox - st.session_state["last_x"]) > 1.0
            or abs(oy - st.session_state["last_y"]) > 1.0
        ):
            st.session_state["last_x"] = ox
            st.session_state["last_y"] = oy
            st.rerun()
