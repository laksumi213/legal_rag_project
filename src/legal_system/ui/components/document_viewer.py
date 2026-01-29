# src/legal_system/ui/components/document_viewer.py

import base64
import streamlit as st
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_bytes

# キャッシュ関数もこちらに移動
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
    """
    with st.container(border=True):
        st.markdown("###### 📄 書類ビューワー")
        
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

        page_key = f"{key_prefix}_page"
        zoom_key = f"{key_prefix}_zoom"
        
        if page_key not in st.session_state: st.session_state[page_key] = 0
        if zoom_key not in st.session_state: st.session_state[zoom_key] = 100

        total_pages = len(images)
        current_page = st.session_state[page_key]

        col_nav, col_zoom = st.columns([1, 1])
        
        with col_nav:
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            if c_prev.button("◀", key=f"{key_prefix}_prev", disabled=(current_page <= 0)):
                st.session_state[page_key] -= 1
                st.rerun()
            
            c_info.markdown(f"<div style='text-align: center; line-height: 2.3;'>{current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
            
            if c_next.button("▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages - 1)):
                st.session_state[page_key] += 1
                st.rerun()

        with col_zoom:
            zoom = st.slider("拡大率 (%)", 50, 250, st.session_state[zoom_key], 10, key=f"{key_prefix}_slider")
            st.session_state[zoom_key] = zoom

        target_image = images[current_page]
        display_width = int(base_width * (zoom / 100))
        
        st.markdown(
            f"""
            <div style="
                overflow: auto; 
                height: 600px; 
                border: 1px solid #ddd; 
                border-radius: 5px; 
                padding: 10px;
                background-color: #f9f9f9;
                text-align: center;">
                {f'<img src="data:image/jpeg;base64,{base64.b64encode(image_to_bytes(target_image)).decode()}" width="{display_width}px" />'}
            </div>
            """,
            unsafe_allow_html=True
        )