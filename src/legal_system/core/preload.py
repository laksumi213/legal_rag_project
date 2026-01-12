# src/legal_system/core/preload.py
import streamlit as st


@st.cache_resource(show_spinner=False)
def warm_up_modules():
    """
    重いライブラリをHome画面の裏で事前にメモリに読み込んでおく関数。
    初回のみ実行され、キャッシュされます。
    """
    print("🐢 バックグラウンドで重いモジュールをロード中...")

    # # noqa: F401 をつけることで、Ruffに「未使用でも無視しろ」と指示します

    # 1. 管理ツール (LangChain, PDF処理などを含む)
    import pypdf  # noqa: F401

    # 2. PDF生成・操作系
    import reportlab  # noqa: F401
    from reportlab.pdfbase import pdfmetrics  # noqa: F401
    from reportlab.pdfbase.ttfonts import TTFont  # noqa: F401

    # 3. DBモデル (SQLAlchemyの初期化コスト削減)
    import legal_system.models.tables  # noqa: F401
    import legal_system.ui.components.admin_tools  # noqa: F401

    # 4. AI系
    from legal_system.core.ai_factory import AIFactory  # noqa: F401

    print("🐇 モジュールのウォームアップ完了。次ページへの遷移が高速化されました。")
    return True
