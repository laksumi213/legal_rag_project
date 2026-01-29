# src/legal_system/core/preload.py
import streamlit as st
import time

@st.cache_resource(show_spinner=False)
def warm_up_modules():
    """
    重いライブラリおよびメニューコンポーネントをバックグラウンドで事前にインポートし、
    sys.modules（Pythonのモジュールキャッシュ）に乗せておく関数。
    """
    try:
        # --- 1. 外部の重いライブラリ群 ---
        import pypdf
        import reportlab
        import pdf2image
        import PIL
        import docx  # python-docx
        import selenium
        
        # --- 2. メニュー別の独自コンポーネント群 ---
        # これらをインポートしておくことで、Home.py側でimportした瞬間にキャッシュから返されます
        from src.legal_system.ui.components.cases import basic_info
        from src.legal_system.ui.components.cases import asset_list
        from src.legal_system.ui.components.cases import nayose_registration
        from src.legal_system.ui.components.cases import registry_acquisition
        from src.legal_system.ui.components.cases import dashboard_widgets
        from src.legal_system.ui.components import label_printer_ui
        
        # --- 3. 重いAI関連 ---
        from src.legal_system.core import ai_factory
        from src.services import gmail_watcher_service
        from src.services import scanner_service

    except Exception as e:
        # バックグラウンドでの失敗は起動を妨げないようログに留める
        print(f"🐢 Warmup info: Some modules are still loading... {e}")
    
    return True