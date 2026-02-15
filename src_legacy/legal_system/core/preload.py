# src/legal_system/core/preload.py
import streamlit as st


@st.cache_resource(show_spinner=False)
def warm_up_modules():
    """
    重いライブラリおよびメニューコンポーネントをバックグラウンドで事前にインポートし、
    sys.modules（Pythonのモジュールキャッシュ）に乗せておく関数。
    """
    try:
        # --- 1. 外部の重いライブラリ群 ---

        # --- 2. メニュー別の独自コンポーネント群 ---
        # これらをインポートしておくことで、Home.py側でimportした瞬間にキャッシュから返されます

        # --- 3. 重いAI関連 ---
        pass

    except Exception as e:
        # バックグラウンドでの失敗は起動を妨げないようログに留める
        print(f"🐢 Warmup info: Some modules are still loading... {e}")

    return True
