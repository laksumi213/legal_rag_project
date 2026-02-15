# src/legal_system/ui/components/document_viewer.py

import base64
import streamlit as st
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_bytes

# キャッシュ関数
@st.cache_data(show_spinner=False)
def convert_pdf_to_images_cached(file_bytes: bytes):
    try:
        return convert_from_bytes(file_bytes, dpi=200)
    except Exception:
        return None

def image_to_bytes(img: Image.Image, format: str = "JPEG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def render_enhanced_document_viewer(file_bytes: bytes, file_type: str, key_prefix: str, base_width: int = 700):
    """
    PDFまたは画像のビューワーを表示する共通コンポーネント
    拡大縮小(Zoom)とページ送り機能を提供します。
    """
    with st.container(border=True):
        # ツールバー（ページ送り & ズーム）
        col_nav, col_zoom = st.columns([1, 1])
        
        images = []
        if "pdf" in file_type:
            images = convert_pdf_to_images_cached(file_bytes)
            if not images:
                st.error("PDFの変換に失敗しました。")
                return
        else:
            try:
                img = Image.open(BytesIO(file_bytes))
                images = [img]
            except:
                st.error("画像の読み込みに失敗しました。")
                return

        # セッションステート管理
        page_key = f"{key_prefix}_page"
        zoom_key = f"{key_prefix}_zoom"
        
        if page_key not in st.session_state: st.session_state[page_key] = 0
        if zoom_key not in st.session_state: st.session_state[zoom_key] = 100

        total_pages = len(images)
        current_page = st.session_state[page_key]

        # ナビゲーションUI
        with col_nav:
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            if c_prev.button("◀", key=f"{key_prefix}_prev", disabled=(current_page <= 0)):
                st.session_state[page_key] -= 1
                st.rerun()
            
            c_info.markdown(f"<div style='text-align: center; line-height: 2.3; font-weight: bold;'>Page {current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
            
            if c_next.button("▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages - 1)):
                st.session_state[page_key] += 1
                st.rerun()

        # ズームスライダー
        with col_zoom:
            zoom = st.slider("拡大率 (%)", 50, 300, st.session_state[zoom_key], 10, key=f"{key_prefix}_slider")
            st.session_state[zoom_key] = zoom

        # 画像表示エリア
        target_image = images[current_page]
        display_width = int(base_width * (zoom / 100))
        
        img_b64 = base64.b64encode(image_to_bytes(target_image)).decode()
        
        # ★修正ポイント: max-width: none を指定し、親要素の幅制限を無視して拡大させる
        st.markdown(
            f"""
            <div style="
                overflow: auto; 
                height: 600px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 10px;
                background-color: #f0f2f6;
                text-align: center;
                display: flex;
                justify_content: center;
                align-items: flex-start;">
                <img src="data:image/jpeg;base64,{img_b64}" 
                     style="width: {display_width}px; max-width: none; height: auto;" />
            </div>
            """,
            unsafe_allow_html=True
        )