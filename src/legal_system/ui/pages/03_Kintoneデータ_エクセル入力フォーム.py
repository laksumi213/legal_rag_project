# components/pages/03_Kintoneデータ_エクセル入力フォーム.py

import streamlit as st
import json
import io
from src.legal_system.ui.excel_generator import fill_initial_set_excel

def show_document_creation_page():
    """
    案件登録・書類作成画面を表示します。
    KintoneからのJSON貼り付けによるExcel自動作成を行います。
    """
    st.title("📑 案件登録・書類作成")
    st.markdown("Kintoneのデータを貼り付けて、「初回送付セット」Excelを作成します。")

    # --- 1. テンプレート選択エリア ---
    with st.expander("📂 Excelテンプレート設定", expanded=False):
        st.info("デフォルトではサーバー内の最新版テンプレートが使用されます。手元のファイルを修正して使いたい場合のみアップロードしてください。")
        uploaded_template = st.file_uploader(
            "テンプレートExcelをアップロード（任意）", 
            type=["xlsx"],
            key="template_uploader"
        )

    # --- 2. データ入力エリア ---
    st.subheader("1. Kintoneデータ取込")
    json_input = st.text_area(
        "KintoneブックマークレットでコピーしたJSONを貼り付けてください",
        height=300,
        placeholder='{"顧客コード": "Gxxxx", ...}'
    )

    if st.button("解析・Excel作成実行", type="primary"):
        if not json_input:
            st.error("JSONデータが入力されていません。")
            return

        try:
            # JSONパース
            data = json.loads(json_input)
            
            # データプレビュー（確認用）
            st.success("JSONの読み込みに成功しました。以下の内容でExcelを作成します。")
            
            # 主要項目のみ表示して確認
            preview_keys = ["顧客コード_2", "顧客名", "担当者①", "担当者②", "被相続人名"]
            preview_data = {k: data.get(k, "（未設定）") for k in preview_keys}
            st.json(preview_data, expanded=False)

            # --- 3. Excel生成処理 ---
            # アップロードがあればそれを、なければNone（デフォルト使用）を渡す
            template_source = uploaded_template if uploaded_template else None
            
            excel_binary = fill_initial_set_excel(data, template_source)
            
            # --- 4. ダウンロードボタン表示 ---
            st.subheader("2. 書類ダウンロード")
            
            # ファイル名の生成（顧客名を含める）
            customer_name = data.get("顧客名", "未設定").replace("　", "").replace(" ", "")
            filename = f"初回送付セット_{customer_name}様.xlsx"
            
            st.download_button(
                label="📥 作成されたExcelをダウンロード",
                data=excel_binary,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except json.JSONDecodeError:
            st.error("JSON形式の読み込みに失敗しました。コピー内容が正しいか確認してください。")
        except FileNotFoundError as e:
            st.error(f"システムエラー: {e}")
        except KeyError as e:
            st.error(f"Excelテンプレートエラー: {e}")
        except Exception as e:
            st.error(f"予期せぬエラーが発生しました: {e}")

# メイン実行ブロック（単体テスト用）
if __name__ == "__main__":
    show_document_creation_page()