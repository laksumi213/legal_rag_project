# src/legal_system/tools/coord_tool.py

import hashlib
import os
import sys
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from pdf2image import convert_from_bytes
from PIL import ImageDraw, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from streamlit_image_coordinates import streamlit_image_coordinates

# パス解決
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.append(BASE_DIR)

from legal_system.core.database_manager import DatabaseManager

# フォント設定
FONT_PATH = os.path.join(BASE_DIR, "data", "fonts", "ipaexg.ttf")
try:
    pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(layout="wide", page_title="座標登録ツール (DB連携対応版)")
st.title("📍 PDF座標 登録 & 編集ツール")

db = DatabaseManager()
user_info = db.get_current_user_info()


# ==========================================
# 0. ヘルパー関数 & プリセット
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
    "----- ★DB連携用タグ (自動差込)★ -----": {"label": "", "val": ""},
    "{被相続人 氏名}": {
        "label": "被相続人氏名",
        "val": "{deceased_name}",
        "desc": "DBから被相続人名を自動取得",
    },
    "{被相続人 死亡日}": {
        "label": "被相続人死亡日",
        "val": "{death_date}",
        "desc": "DBから死亡日を自動取得",
    },
    "{相続人 氏名}": {
        "label": "相続人氏名",
        "val": "{heir_name}",
        "desc": "DBから相続人名を自動取得",
    },
    "{相続人 住所}": {
        "label": "相続人住所",
        "val": "{heir_address}",
        "desc": "DBから住所を自動取得",
    },
    "----- 図形・記号 -----": {"label": "", "val": ""},
    "四角形枠 (サイズ指定)": {
        "label": "枠線",
        "val": "RECT:30x30",
        "desc": "RECT:幅x高さ (pt単位)",
    },
    "数字「1」": {"label": "数字1", "val": "1", "size": 11},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14},
    "----- 日付関連 (固定値) -----": {"label": "", "val": ""},
    "今日 (令和〇年)": {"label": "記入日_和暦年", "val": wareki_year},
    "今日 (20XX年)": {"label": "記入日_西暦年", "val": str(today.year)},
    "----- 担当者・会社 (固定値) -----": {"label": "", "val": ""},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]},
    "代理人 (肩書)": {"label": "代理人肩書", "val": "代理人"},
    "電話番号 (市外局番)": {"label": "担当者TEL_1", "val": user_phone_parts[0]},
    "電話番号 (市内局番)": {"label": "担当者TEL_2", "val": user_phone_parts[1]},
    "電話番号 (加入者)": {"label": "担当者TEL_3", "val": user_phone_parts[2]},
    "会社郵便番号 (3桁)": {"label": "会社郵便番号1", "val": COMPANY_INFO["zip1"]},
    "会社郵便番号 (4桁)": {"label": "会社郵便番号2", "val": COMPANY_INFO["zip2"]},
    "会社住所": {"label": "会社住所", "val": COMPANY_INFO["address"]},
    "代表者名": {"label": "代表者名", "val": COMPANY_INFO["rep_name"]},
    "相続人 代理人": {"label": "相続人代理人署名", "val": "相続人 相続 花子 代理人"},
}

# セッション初期化
if "last_x" not in st.session_state:
    st.session_state["last_x"] = 0
if "last_y" not in st.session_state:
    st.session_state["last_y"] = 0
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1

if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 10.5
if "input_color" not in st.session_state:
    st.session_state["input_color"] = "black"
if "input_desc" not in st.session_state:
    st.session_state["input_desc"] = ""

# ==========================================
# 1. サイドバー: ファイル管理エリア
# ==========================================
with st.sidebar:
    st.header("📂 対象ファイル")
    uploaded_file = st.file_uploader("帳票PDFをアップロード", type="pdf")

    file_hash = None
    existing_coords = []
    df_existing = pd.DataFrame()

    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_hash = calculate_hash(file_bytes)
        st.caption(f"File ID: {file_hash[:8]}...")

        # データベースから座標を取得
        existing_coords = db.get_coordinates_by_hash(file_hash)
        if existing_coords:
            df_existing = pd.DataFrame(existing_coords)

        st.success(f"登録済み: {len(existing_coords)} 件")
    else:
        st.warning(
            "左記でファイルをアップロードしてください。\n(再編集の場合も同じファイルをアップロードが必要です)"
        )

    st.divider()
    st.header("⚙️ 設定")

    def on_def_size_change():
        st.session_state["input_size"] = st.session_state["def_font_size_key"]

    def_font_size = st.number_input(
        "基本フォントサイズ (pt)",
        4.0,
        72.0,
        10.5,
        step=0.5,
        key="def_font_size_key",
        on_change=on_def_size_change,
    )

# ==========================================
# 2. メインエリア
# ==========================================
col_img, col_ctrl = st.columns([1.8, 1.2])

if not uploaded_file:
    st.info("👈 サイドバーからPDFをアップロードしてください。")
    st.stop()

# --- プレビュー用準備 ---
reader = PdfReader(BytesIO(file_bytes))
# 1ページ目のサイズを取得 (Point単位)
media_box = reader.pages[0].mediabox
pdf_w_pt = float(media_box.width)
pdf_h_pt = float(media_box.height)

images = convert_from_bytes(file_bytes)
total_pages = len(images)
img_w_px, img_h_px = images[0].size
# プレビュー拡大率
preview_scale = img_h_px / pdf_h_pt


# データ更新用コールバック関数
def on_data_editor_change():
    changes = st.session_state["editor"]
    if changes["edited_rows"]:
        for idx, row_changes in changes["edited_rows"].items():
            target_id = df_existing.iloc[int(idx)]["id"]
            db.update_coordinate_direct(int(target_id), row_changes)
        st.toast("✅ 変更を保存しました")

    if changes["deleted_rows"]:
        for idx in changes["deleted_rows"]:
            target_id = df_existing.iloc[int(idx)]["id"]
            db.delete_coordinate(int(target_id))
        st.toast("🗑️ 削除しました")


# --- 右カラム: 入力 & リスト編集 ---
with col_ctrl:
    st.subheader("2. 設定と登録")

    # プリセット選択
    def on_preset():
        sel = st.session_state["preset_sel"]
        if sel and PRESETS[sel]["val"]:
            p = PRESETS[sel]
            st.session_state["input_label"] = p["label"]
            st.session_state["input_val"] = p["val"]
            if "size" in p:
                st.session_state["input_size"] = float(p["size"])
            if "desc" in p:
                st.session_state["input_desc"] = p["desc"]

    st.selectbox(
        "⚡️ プリセット", list(PRESETS.keys()), key="preset_sel", on_change=on_preset
    )

    # 入力フォーム
    c1, c2 = st.columns([2, 1])
    label_in = c1.text_input(
        "項目名 (必須)", key="input_label", placeholder="例: 被相続人氏名"
    )
    val_in = c2.text_input(
        "テスト値",
        key="input_val",
        help="矩形: 'RECT:幅x高さ', DB連携: '{deceased_name}'",
    )

    c3, c4 = st.columns(2)
    size_in = c3.number_input(
        "サイズ(pt)", 0.5, 100.0, key="input_size", step=0.5, format="%.1f"
    )
    color_in = c4.selectbox("色", ["black", "red"], key="input_color")

    desc_in = st.text_input("備考", key="input_desc")

    st.write(
        f"📍 座標: X={st.session_state['last_x']} / Y={st.session_state['last_y']} (P.{st.session_state['current_page']})"
    )

    if st.button("💾 新規登録 / 上書き保存", type="primary"):
        if not label_in:
            st.error("項目名は必須です")
        elif st.session_state["last_x"] == 0:
            st.error("左の画像をクリックして位置を決めてください")
        else:
            success = db.register_coordinate(
                file_hash=file_hash,
                label=label_in,
                x=st.session_state["last_x"],
                y=st.session_state["last_y"],
                page_number=st.session_state["current_page"],
                description=desc_in,
                font_size=size_in,
                color=color_in,
                test_value=val_in,
            )
            if success:
                st.toast(f"✅ 「{label_in}」を登録しました！")
                import time

                time.sleep(0.5)
                st.rerun()

    st.divider()

    # ▼▼▼ 登録済みリスト (width='stretch'対応) ▼▼▼
    st.subheader("📋 登録済みリスト (直接修正可)")
    if not df_existing.empty:
        column_order = [
            "label",
            "x",
            "y",
            "page",
            "font_size",
            "color",
            "value",
            "desc",
            "id",
        ]
        # 存在するカラムのみフィルタリング
        df_display = df_existing[[c for c in column_order if c in df_existing.columns]]

        st.data_editor(
            df_display,
            column_config={
                "id": None,
                "label": st.column_config.TextColumn("項目名", width="medium"),
                "x": st.column_config.NumberColumn("X", format="%.1f", step=0.1),
                "y": st.column_config.NumberColumn("Y", format="%.1f", step=0.1),
                "page": st.column_config.NumberColumn("頁", width="small"),
                "font_size": st.column_config.NumberColumn(
                    "pt", width="small", format="%.1f", step=0.5
                ),
                "color": st.column_config.SelectboxColumn(
                    "色", options=["black", "red"], width="small"
                ),
                "value": st.column_config.TextColumn("値/RECT", width="medium"),
                "desc": st.column_config.TextColumn("備考", width="large"),
            },
            hide_index=True,
            width="stretch",  # use_container_width=True の代わり
            key="editor",
            num_rows="dynamic",
            on_change=on_data_editor_change,
        )
    else:
        st.info("まだ登録データはありません")

    # ▼▼▼ PDF作成ロジック (リスト下の配置 & 全件出力) ▼▼▼
    st.divider()
    st.subheader("🖨️ PDF作成 (登録済み全件出力)")

    if st.button("現在のリスト内容でPDFを作成"):
        if df_existing.empty:
            st.error("登録されたデータがありません。先に座標を登録してください。")
        else:
            try:
                # ベースPDFの読み込み
                packet = BytesIO()
                # ReportLabキャンバス作成
                can = canvas.Canvas(packet, pagesize=(pdf_w_pt, pdf_h_pt))

                # 登録済みデータを全件ループ
                for index, row in df_existing.iterrows():
                    # ページ番号が違う場合はスキップ（今回は簡易的に1ページずつ出力ではなく、全ページマージする前提）
                    # 実際にはページごとにCanvasを分けるか、ページ移動が必要だが、
                    # 簡易実装として「座標があるページに移動して描く」方式をとる

                    target_page = int(row["page"])
                    val = row["value"]
                    x = float(row["x"])
                    y = float(row["y"])
                    f_size = float(row["font_size"])
                    clr = row["color"]

                    # ページ設定 (ReportLabはページ概念が少し特殊なので、今回は
                    # シンプルに「全ページ処理するPDFWriter」側で合成する方式をとるため
                    # ここではページごとにCanvasを作るのが正しいが、
                    # 簡易的に「ページごとにPDFを作って合成」するループにする)
                    pass

                # --- 修正版PDF生成ロジック (ページ対応) ---
                output = PdfWriter()

                # 1ページずつ処理
                for i, page_obj in enumerate(reader.pages):
                    page_num = i + 1

                    # このページの座標データのみ抽出
                    page_coords = df_existing[df_existing["page"] == page_num]

                    if not page_coords.empty:
                        # このページ用のオーバーレイPDFを作成
                        packet_page = BytesIO()
                        # ページサイズ取得
                        pw = float(page_obj.mediabox.width)
                        ph = float(page_obj.mediabox.height)

                        can_page = canvas.Canvas(packet_page, pagesize=(pw, ph))

                        # 描画ループ
                        for _, row in page_coords.iterrows():
                            val = row["value"]
                            if not val:
                                continue  # 値がなければスキップ

                            x = float(row["x"])
                            y = float(row["y"])
                            f_size = float(row["font_size"])

                            # 色設定
                            c_obj = red if row["color"] == "red" else black
                            can_page.setFillColor(c_obj)
                            can_page.setStrokeColor(c_obj)

                            # 座標変換 (画像クリック(左上) -> PDF(左下))
                            # 登録されているX,Yは「画像上のピクセル」
                            # ここでPDF上のポイントに変換する必要がある
                            # preview_scale = img_h_px / pdf_h_pt なので
                            # pdf_pt = img_px / preview_scale

                            # ★重要: DBの座標はクリック時のもの(Pixel相当)
                            # ここで再計算する
                            # 厳密にはページごとにサイズが違う可能性もあるが、今回は1ページ目の比率を使用

                            scale_x = pw / img_w_px
                            scale_y = ph / img_h_px

                            draw_x = x * scale_x
                            draw_y_base = ph - (y * scale_y)

                            if str(val).startswith("RECT:"):
                                try:
                                    dims = val.replace("RECT:", "").split("x")
                                    w_pt = float(dims[0])
                                    h_pt = float(dims[1])
                                    rect_y = draw_y_base - h_pt
                                    can_page.setLineWidth(f_size)
                                    can_page.rect(
                                        draw_x, rect_y, w_pt, h_pt, stroke=1, fill=0
                                    )
                                except:
                                    pass
                            else:
                                can_page.setFont("IPAexG", f_size)
                                text_y = draw_y_base - (f_size * 0.8)
                                can_page.drawString(draw_x, text_y, str(val))

                        can_page.save()
                        packet_page.seek(0)
                        overlay = PdfReader(packet_page)
                        page_obj.merge_page(overlay.pages[0])

                    output.add_page(page_obj)

                # 出力
                out_stream = BytesIO()
                output.write(out_stream)

                st.success("PDF作成完了！")
                st.download_button(
                    label="📥 作成したPDFをダウンロード",
                    data=out_stream,
                    file_name="filled_result.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF作成中にエラーが発生しました: {e}")
                st.exception(e)  # 詳細エラー表示

# --- 左カラム: 画像プレビュー ---
with col_img:
    st.subheader("1. 座標指定")

    new_page = st.number_input(
        "ページ", 1, total_pages, st.session_state["current_page"]
    )
    if new_page != st.session_state["current_page"]:
        st.session_state["current_page"] = new_page
        st.rerun()

    bg_image = images[st.session_state["current_page"] - 1].copy()
    draw = ImageDraw.Draw(bg_image)

    def draw_on_image(draw_obj, x, y, val, size_pt, color_name):
        color_rgba = (255, 0, 0, 255) if color_name == "red" else (0, 0, 0, 255)
        if not val:
            return

        if str(val).startswith("RECT:"):
            try:
                dims = val.replace("RECT:", "").split("x")
                w_pt = float(dims[0])
                h_pt = float(dims[1])
                w_px = w_pt * preview_scale
                h_px = h_pt * preview_scale
                line_width = int(max(1, size_pt * (preview_scale / 2)))
                draw_obj.rectangle(
                    [x, y, x + w_px, y + h_px], outline=color_rgba, width=line_width
                )
            except:
                pass
        else:
            try:
                px_size = size_pt * preview_scale
                font = ImageFont.truetype(FONT_PATH, int(px_size))
                draw_obj.text((x, y), str(val), font=font, fill=color_rgba)
            except:
                pass

    # A. 入力中のプレビュー
    if val_in:
        draw_on_image(
            draw,
            st.session_state["last_x"],
            st.session_state["last_y"],
            val_in,
            size_in,
            color_in,
        )
        if not str(val_in).startswith("RECT:"):
            try:
                px_size = size_in * preview_scale
                font = ImageFont.truetype(FONT_PATH, int(px_size))
                bbox = draw.textbbox(
                    (st.session_state["last_x"], st.session_state["last_y"]),
                    val_in,
                    font=font,
                )
                draw.rectangle(bbox, outline="blue", width=2)
            except:
                pass

    # B. 登録済みデータのプレビュー
    current_page_coords = [
        c for c in existing_coords if c["page"] == st.session_state["current_page"]
    ]
    for c in current_page_coords:
        draw_on_image(draw, c["x"], c["y"], c["value"], c["font_size"], c["color"])

    # 座標取得
    value = streamlit_image_coordinates(
        bg_image, key=f"canvas_p{st.session_state['current_page']}"
    )
    if value:
        if (
            value["x"] != st.session_state["last_x"]
            or value["y"] != st.session_state["last_y"]
        ):
            st.session_state["last_x"] = value["x"]
            st.session_state["last_y"] = value["y"]
            st.rerun()
