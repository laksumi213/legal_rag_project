This file is a merged representation of the entire codebase, combined into a single document by Repomix.

# File Summary

## Purpose
This file contains a packed representation of the entire repository's contents.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Files matching patterns in .gitignore are excluded
- Files matching default ignore patterns are excluded
- Files are sorted by Git change count (files with more changes are at the bottom)

# Directory Structure
```
.dockerignore
.gitignore
.python-version
.streamlit/config.toml
■初回送付セット【20251218版】　.xlsx
bank_master.json
create_rule_master.py
data/db/chroma/.keep
data/db/chroma/local_rag_db/7ec55c3c-907b-4922-a7e0-989eb818156f/data_level0.bin
data/db/chroma/local_rag_db/7ec55c3c-907b-4922-a7e0-989eb818156f/header.bin
data/db/chroma/local_rag_db/7ec55c3c-907b-4922-a7e0-989eb818156f/length.bin
data/db/chroma/local_rag_db/7ec55c3c-907b-4922-a7e0-989eb818156f/link_lists.bin
data/db/chroma/local_rag_db/chroma.sqlite3
data/db/chroma/local_rag_db/d50e1e10-53e2-4aea-ac5d-95f27e67e86d/data_level0.bin
data/db/chroma/local_rag_db/d50e1e10-53e2-4aea-ac5d-95f27e67e86d/header.bin
data/db/chroma/local_rag_db/d50e1e10-53e2-4aea-ac5d-95f27e67e86d/length.bin
data/db/chroma/local_rag_db/d50e1e10-53e2-4aea-ac5d-95f27e67e86d/link_lists.bin
data/db/sql/.keep
data/db/sql/legal_system.db
data/fonts/ipaexg.ttf
data/legal_system.db
data/rules/bank_master.csv
data/rules/company_rules.md
data/templates/.keep
docker-compose.yml
Dockerfile
export_code.py
pyproject.toml
README.md
register_existing_templates.py
requirements-dev.lock
requirements.lock
requirements.txt
reset_db.py
run_watcher.py
src/__init__.py
src/chains/bank_procedure_chain.py
src/legal_system/__init__.py
src/legal_system/core/__init__.py
src/legal_system/core/ai_factory.py
src/legal_system/core/config.py
src/legal_system/core/data_sync.py
src/legal_system/core/database_manager.py
src/legal_system/core/engines.py
src/legal_system/core/ocr_engine.py
src/legal_system/core/pdf_processor.py
src/legal_system/core/preload.py
src/legal_system/main.py
src/legal_system/models/__init__.py
src/legal_system/models/base.py
src/legal_system/models/tables.py
src/legal_system/tools/__init__.py
src/legal_system/tools/coord_tool.py
src/legal_system/ui/__init__.py
src/legal_system/ui/components/admin_tools.py
src/legal_system/ui/excel_generator.py
src/legal_system/ui/Home.py
src/legal_system/ui/pages/01_Kintoneデータ_エクセル入力フォーム.py
src/legal_system/ui/pages/02_預貯金口座入力フォーム.py
src/legal_system/ui/pages/03_相続書類_作成フォーム.py
src/legal_system/ui/pages/04_法定相続情報_読取.py
src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py
src/legal_system/ui/pages/06_案件登録_手動.py
src/legal_system/ui/pages/07_案件詳細_統合管理.py
src/legal_system/ui/pages/99_書式座標登録ツール.py
src/legal_system/ui/pages/backup/98_Llama実験室.py
src/legal_system/ui/pages/backup/99_Gemini実験室.py
src/legal.egg-info/dependency_links.txt
src/legal.egg-info/PKG-INFO
src/legal.egg-info/requires.txt
src/legal.egg-info/SOURCES.txt
src/legal.egg-info/top_level.txt
src/services/folder_service.py
src/views/client_register.py
src/views/detail.py
update_bank_master.py
```

# Files

## File: src/legal_system/ui/pages/01_Kintoneデータ_エクセル入力フォーム.py
````python
# components/pages/01_Kintoneデータ_エクセル入力フォーム.py

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
````

## File: src/legal_system/ui/pages/02_預貯金口座入力フォーム.py
````python
import json
import os
import sys

import streamlit as st

# --- パス解決 ---
# このファイルの場所: src/legal_system/ui/pages/99_預貯金口座入力フォーム.py
# ROOT_DIR: プロジェクトルート
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# pages -> ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    AccountTypeMaster,
    BankMaster,
    BranchMaster,
    Case,
    FinancialAsset,
)

# --- Zengin-Code のローカルキャッシュパス ---
DATA_DIR = os.path.join(ROOT_DIR, "data", "zengin")


# ★修正: キャッシュ(st.cache_data)を削除しました。
# JSONの読み込みは十分に高速であり、ファイル更新を即座に反映させるためです。
def get_bank_master():
    """ローカルのJSONファイルから銀行マスタ(Zengin)を読み込む"""
    json_path = os.path.join(DATA_DIR, "banks.json")

    # デバッグ用: パスが合っているか確認したい場合は以下のコメントを外す
    # print(f"Looking for banks at: {json_path}")

    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading banks.json: {e}")
        return {}


# ★修正: こちらもキャッシュを削除、またはTTLを設定
def get_branch_master(bank_code):
    """ローカルのJSONファイルから支店マスタを読み込む"""
    json_path = os.path.join(DATA_DIR, "branches", f"{bank_code}.json")
    if not os.path.exists(json_path):
        return {}
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def ensure_master_records(
    session, bank_name, bank_code, branch_name, branch_code, type_name
):
    """マスタテーブルに存在しなければ作成するヘルパー関数"""
    # 1. 銀行マスタ
    bank = session.query(BankMaster).filter_by(bank_code=bank_code).first()
    if not bank:
        bank = BankMaster(bank_name=bank_name, bank_code=bank_code)
        session.add(bank)
        session.flush()

    # 2. 支店マスタ
    branch = None
    if branch_code:
        branch = (
            session.query(BranchMaster)
            .filter_by(bank_id=bank.id, branch_code=branch_code)
            .first()
        )
        if not branch:
            branch = BranchMaster(
                bank_id=bank.id, branch_name=branch_name, branch_code=branch_code
            )
            session.add(branch)
            session.flush()

    # 3. 口座種別マスタ
    ac_type = session.query(AccountTypeMaster).filter_by(type_name=type_name).first()
    if not ac_type:
        ac_type = AccountTypeMaster(type_name=type_name)
        session.add(ac_type)
        session.flush()

    return bank, branch, ac_type


def main():
    st.set_page_config(page_title="口座情報入力", page_icon="🏦", layout="centered")
    st.title("🏦 預貯金口座 入力ツール")
    st.caption(
        "案件ごとの口座情報を登録します。ここで登録したデータが書類作成に使用されます。"
    )

    # 1. 銀行選択
    banks = get_bank_master()

    if not banks:
        st.error(
            "⚠️ 銀行データ(Zengin)が見つかりません。Home画面の「更新」ボタンを押してください。"
        )
        # デバッグ用にパスを表示
        st.caption(f"参照パス: {os.path.join(DATA_DIR, 'banks.json')}")
        return

    # 銀行リスト作成 (辞書型かリスト型かで処理を分ける)
    if isinstance(banks, dict):
        bank_list = [f"{v['name']} ({k})" for k, v in banks.items()]
    else:
        # 想定外のフォーマットの場合のガード
        bank_list = []

    selected_bank_str = st.selectbox(
        "銀行名", options=[""] + bank_list, placeholder="銀行名を入力または選択..."
    )

    # 2. 支店選択
    selected_branch_str = ""
    bank_code = ""
    bank_name = ""

    if selected_bank_str:
        # 文字列 "三菱UFJ銀行 (0005)" からコードと名前を抽出
        try:
            # 右側の括弧内のコードを取得
            bank_code = selected_bank_str.split("(")[-1].replace(")", "")
            # コード部分を除いた名前を取得
            bank_name = selected_bank_str.replace(f"({bank_code})", "").strip()

            branches = get_branch_master(bank_code)
            if branches:
                branch_list = [f"{v['name']} ({k})" for k, v in branches.items()]
                selected_branch_str = st.selectbox("支店名", options=[""] + branch_list)
            else:
                st.warning("支店データがありません（手入力してください）")
                selected_branch_str = st.text_input("支店名 (手入力)")
        except Exception:
            st.error("銀行名のパースに失敗しました")

    # 3. 口座詳細入力
    c1, c2 = st.columns(2)
    account_type = c1.selectbox("預金種別", ["普通", "定期", "当座", "貯蓄", "その他"])
    account_num = c2.text_input("口座番号 (7桁)", max_chars=7)

    holder_name = st.text_input("口座名義人 (カタカナ)", placeholder="ヤマダ タロウ")

    # 案件番号入力
    case_number = st.text_input(
        "案件番号 (G番号)", value="G0001", help="既存の案件番号を入力してください"
    )

    st.divider()

    if st.button("💾 データを確定する", type="primary"):
        if not (bank_name and case_number):
            st.error("銀行名と案件番号は必須です。")
            return

        # 支店情報のパース
        branch_name = ""
        branch_code = "000"

        if selected_branch_str:
            if "(" in selected_branch_str and ")" in selected_branch_str:
                try:
                    branch_code = selected_branch_str.split("(")[-1].replace(")", "")
                    branch_name = selected_branch_str.replace(
                        f"({branch_code})", ""
                    ).strip()
                except:
                    branch_name = selected_branch_str
            else:
                branch_name = selected_branch_str

        try:
            db = DatabaseManager()
            session = db._get_session()

            # 1. 案件の確保
            case = session.query(Case).filter_by(case_number=case_number).first()
            if not case:
                # 案件がない場合は簡易作成
                case = Case(case_number=case_number, client_name=f"案件{case_number}")
                session.add(case)
                session.flush()

            # 2. マスタの確保
            bank_obj, branch_obj, type_obj = ensure_master_records(
                session, bank_name, bank_code, branch_name, branch_code, account_type
            )

            # 3. 資産データの登録
            new_asset = FinancialAsset(
                case_id=case.case_id,
                bank_id=bank_obj.id,
                branch_id=branch_obj.id if branch_obj else None,
                account_type_id=type_obj.id,
                account_number=account_num,
                status=f"名義:{holder_name}",
            )
            session.add(new_asset)
            session.commit()

            st.success(f"✅ {bank_name} {branch_name} の口座情報を登録しました！")
            # 完了後、セッションを閉じる
            session.close()

        except Exception as e:
            st.error(f"DB保存エラー: {e}")
            return


if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/03_相続書類_作成フォーム.py
````python
# src/legal_system/ui/pages/03_相続書類_作成フォーム.py

import os
import sys
from io import BytesIO

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# パス解決
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, FileRegistry

# フォント設定
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(page_title="書類作成 | 相続業務支援", page_icon="📄", layout="wide")


# ==========================================
# データ置換ロジック
# ==========================================
def create_replacement_map(case_data):
    map_dict = {}

    # 基本情報
    map_dict["{case_number}"] = case_data.case_number
    map_dict["{client_name}"] = case_data.client_name

    # 被相続人情報
    if case_data.deceased_ref:
        d = case_data.deceased_ref
        full_name = f"{d.name_last} {d.name_first}".strip()
        map_dict["{deceased_name}"] = full_name
        map_dict["{deceased_name_last}"] = d.name_last or ""
        map_dict["{deceased_name_first}"] = d.name_first or ""

        if d.date_of_death:
            map_dict["{death_date}"] = d.date_of_death.strftime("%Y年%m月%d日")
            map_dict["{death_year_seireki}"] = str(d.date_of_death.year)
            if d.date_of_death.year >= 2019:
                map_dict["{death_year_wareki}"] = f"令和{d.date_of_death.year - 2018}"
            else:
                map_dict["{death_year_wareki}"] = str(d.date_of_death.year)
            map_dict["{death_month}"] = str(d.date_of_death.month)
            map_dict["{death_day}"] = str(d.date_of_death.day)

    # 相続人情報 (簡易実装)
    if case_data.deceased_ref and case_data.deceased_ref.heirs:
        h = case_data.deceased_ref.heirs[0]
        full_name_h = f"{h.name_last} {h.name_first}".strip()
        map_dict["{heir_name}"] = full_name_h
        map_dict["{heir_name_last}"] = h.name_last or ""
        map_dict["{heir_name_first}"] = h.name_first or ""
        map_dict["{heir_address}"] = "（住所未登録）"
        map_dict["{heir_pref}"] = ""
        map_dict["{heir_city}"] = ""
        map_dict["{heir_street}"] = ""
        map_dict["{heir_building}"] = ""

    return map_dict


def generate_pdf(template_path, coords, replacement_map):
    try:
        reader = PdfReader(template_path)
        output = PdfWriter()
        SCALE_FACTOR = 72.0 / 200.0

        for i, page_obj in enumerate(reader.pages):
            page_num = i + 1
            page_coords = [c for c in coords if c["page"] == page_num]

            if page_coords:
                packet = BytesIO()
                pw = float(page_obj.mediabox.width)
                ph = float(page_obj.mediabox.height)
                can = canvas.Canvas(packet, pagesize=(pw, ph))

                for c in page_coords:
                    raw_val = c["value"]
                    text_to_draw = replacement_map.get(raw_val, raw_val)
                    if not text_to_draw:
                        continue

                    draw_x = c["x"] * SCALE_FACTOR
                    top_y = ph - (c["y"] * SCALE_FACTOR)
                    c_obj = red if c["color"] == "red" else black
                    can.setStrokeColor(c_obj)
                    can.setFillColor(c_obj)
                    font_sz = float(c["font_size"])

                    if str(text_to_draw).startswith("RECT:"):
                        try:
                            dims = text_to_draw.replace("RECT:", "").split("x")
                            w_pt, h_pt = float(dims[0]), float(dims[1])
                            can.rect(draw_x, top_y - h_pt, w_pt, h_pt, stroke=1, fill=0)
                        except:
                            pass
                    else:
                        baseline_y = top_y - (font_sz * 0.9)
                        can.setFont("IPAexG", font_sz)
                        can.drawString(draw_x, baseline_y, str(text_to_draw))

                can.save()
                packet.seek(0)
                overlay = PdfReader(packet)
                page_obj.merge_page(overlay.pages[0])

            output.add_page(page_obj)

        out_stream = BytesIO()
        output.write(out_stream)
        return out_stream

    except Exception as e:
        st.error(f"PDF生成エラー: {e}")
        return None


# ==========================================
# メイン画面
# ==========================================
def main():
    st.title("🖨️ 書類自動作成")
    st.caption("登録済みの案件データを選択し、PDFを作成します。")

    db = DatabaseManager()
    session = db._get_session()

    # 1. 案件選択
    cases = session.query(Case).all()
    if not cases:
        st.warning("案件データがありません。")
        session.close()
        return

    case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}

    default_idx = 0
    if "current_case_id" in st.session_state:
        cid = st.session_state["current_case_id"]
        keys = list(case_options.keys())
        for i, k in enumerate(keys):
            if case_options[k] == cid:
                default_idx = i
                break

    selected_label = st.selectbox(
        "📂 案件選択", list(case_options.keys()), index=default_idx
    )

    if selected_label:
        cid = case_options[selected_label]
        st.session_state["current_case_id"] = cid
        target_case = session.query(Case).filter_by(case_id=cid).first()

        d_name = (
            target_case.deceased_ref.name_last
            + " "
            + target_case.deceased_ref.name_first
            if target_case.deceased_ref
            else "未登録"
        )
        st.info(f"被相続人: **{d_name}**")

        st.divider()

        # 2. テンプレート選択
        files = (
            session.query(FileRegistry)
            .filter(FileRegistry.filename.like("%.pdf"))
            .all()
        )

        if not files:
            st.warning(
                "テンプレート(PDF)が登録されていません。「書式座標登録ツール」のメニューから登録してください。"
            )
        else:
            file_opts = {f.filename: f.file_hash for f in files}
            selected_file_name = st.selectbox(
                "使用するテンプレート", list(file_opts.keys())
            )

            if selected_file_name:
                target_hash = file_opts[selected_file_name]

                # 3. 作成ボタン
                if st.button("🚀 PDFを作成する", type="primary"):
                    coords = db.get_coordinates_by_hash(target_hash)
                    if not coords:
                        st.error(
                            "このファイルには座標データが登録されていません。「書式座標登録ツール」で設定してください。"
                        )
                    else:
                        template_path = os.path.join(
                            ROOT_DIR, "data", "templates", selected_file_name
                        )

                        if not os.path.exists(template_path):
                            st.error(
                                f"テンプレートファイルが見つかりません: {template_path}"
                            )
                        else:
                            replace_map = create_replacement_map(target_case)
                            pdf_data = generate_pdf(template_path, coords, replace_map)

                            if pdf_data:
                                st.success("✅ 作成完了！")
                                st.download_button(
                                    label="📥 作成されたPDFをダウンロード",
                                    data=pdf_data,
                                    file_name=f"作成済_{selected_file_name}",
                                    mime="application/pdf",
                                )
    session.close()


if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/04_法定相続情報_読取.py
````python
# src/legal_system/ui/pages/04_法定相続情報_読取.py

import base64
import json
import logging
import os
import sys
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.config import Config
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, Deceased, Heir

logger = logging.getLogger(__name__)

st.set_page_config(page_title="法定相続情報 読取", page_icon="👪", layout="wide")


# -----------------------------------------------------------------------------
# AI解析ロジック
# -----------------------------------------------------------------------------
def analyze_heir_document_with_ai(image_bytes: bytes) -> dict:
    """Gemini Visionを利用して法定相続情報一覧図を解析"""
    try:
        img_str = base64.b64encode(image_bytes).decode("utf-8")
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

        prompt_text = """
        あなたは熟練した行政書士補助者です。
        提供された「法定相続情報一覧図」の画像を読み取り、被相続人と相続人の情報を構造化データ(JSON)として抽出してください。
        
        【抽出項目とJSON構造】
        {
            "deceased": {
                "name": "被相続人の氏名",
                "death_date": "死亡日(YYYY-MM-DD)",
                "last_address": "最後の住所"
            },
            "heirs": [
                {
                    "name": "相続人氏名",
                    "relationship": "続柄(妻, 長男, 二女 等)",
                    "birth_date": "生年月日(YYYY-MM-DD)",
                    "address": "住所"
                },
                ...
            ]
        }
        
        【注意点】
        - 縦書き、横書き、罫線の有無に関わらず、位置関係から論理的に読み取ってください。
        - 続柄は「被相続人との続柄」です。
        - 日付は和暦の場合、西暦に変換してください（例: 令和1年5月1日 -> 2019-05-01）。
        - JSONのみを出力し、挨拶やコードブロック(```json)は含めないでください。
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"},
            ]
        )

        response = llm.invoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        
        # 稀にJSONの前後に文字が入る場合があるため、{ } で切り出す
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
        else:
            raise ValueError("有効なJSONが見つかりませんでした")

    except Exception as e:
        logger.error(f"Heir Analysis Error: {e}")
        return {"error": str(e)}


# -----------------------------------------------------------------------------
# メイン画面
# -----------------------------------------------------------------------------
def main():
    st.title("👪 法定相続情報 読取・登録")
    
    # プロバイダー表示
    if Config.is_vertex_enabled():
        st.success(f"🔒 Secure Mode: Vertex AI で解析します。")
    else:
        st.warning("⚠️ Development Mode: Studio API (Key) で解析します。本番データ使用禁止。")

    db = DatabaseManager()
    session = db._get_session()

    # --- サイドバー: 案件選択 ---
    with st.sidebar:
        st.header("📂 対象案件")
        cases = session.query(Case).all()
        # 案件がない場合のガード
        if not cases:
            st.error("登録された案件がありません。先に案件を作成してください。")
            session.close()
            return

        case_opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
        selected_case_label = st.selectbox("案件選択", list(case_opts.keys()))
        
        current_case_id = case_opts[selected_case_label]
        st.divider()
        uploaded_file = st.file_uploader("一覧図(PDF/画像)をアップロード", type=["pdf", "png", "jpg"])

    # --- メインエリア ---
    if not uploaded_file:
        st.info("👈 サイドバーから「法定相続情報一覧図」をアップロードしてください。")
        session.close()
        return

    # ファイル読込 & 画像化
    file_bytes = uploaded_file.read()
    display_img = None
    target_bytes = None

    try:
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
            display_img = images[0]
        else:
            display_img = Image.open(BytesIO(file_bytes))
        
        buf = BytesIO()
        display_img.convert("RGB").save(buf, format="JPEG")
        target_bytes = buf.getvalue()

    except Exception as e:
        st.error(f"画像変換エラー: {e}")
        session.close()
        return

    # --- 解析実行ボタン ---
    if "heir_result" not in st.session_state or st.session_state.get("heir_file") != uploaded_file.name:
        st.session_state["heir_result"] = None
        st.session_state["heir_file"] = uploaded_file.name

    col_btn, col_status = st.columns([1, 4])
    with col_btn:
        analyze_btn = st.button("🔍 AI解析実行", type="primary", use_container_width=True)

    if analyze_btn:
        with st.spinner("🤖 家系図構造を解析中..."):
            result = analyze_heir_document_with_ai(target_bytes)
            if "error" in result:
                st.error(f"解析失敗: {result['error']}")
            else:
                st.session_state["heir_result"] = result
                st.toast("✅ 解析完了しました！", icon="🎉")

    st.divider()

    # --- 2カラムレイアウト ---
    col_img, col_data = st.columns([1, 1.2])

    with col_img:
        st.subheader("📄 原本プレビュー")
        st.image(display_img, use_container_width=True)

    with col_data:
        st.subheader("📝 データ確認・編集")

        if st.session_state["heir_result"]:
            data = st.session_state["heir_result"]

            # 1. 被相続人
            st.markdown("##### 1. 被相続人")
            with st.container(border=True):
                d_info = data.get("deceased", {})
                d_name = st.text_input("氏名", value=d_info.get("name", ""))
                c1, c2 = st.columns(2)
                d_date = c1.text_input("死亡日", value=d_info.get("death_date", ""))
                d_addr = st.text_input("最後の住所", value=d_info.get("last_address", ""))

            # 2. 相続人 (DataEditor)
            st.markdown("##### 2. 相続人一覧")
            heirs_raw = data.get("heirs", [])
            
            # DataFrame化
            df_heirs = pd.DataFrame(heirs_raw)
            if df_heirs.empty:
                df_heirs = pd.DataFrame(columns=["name", "relationship", "birth_date", "address"])

            # カラム設定
            column_config = {
                "name": st.column_config.TextColumn("氏名", required=True),
                "relationship": st.column_config.SelectboxColumn(
                    "続柄", options=["妻", "夫", "長男", "二男", "長女", "二女", "養子", "兄弟姉妹"], required=True
                ),
                "birth_date": st.column_config.TextColumn("生年月日"),
                "address": st.column_config.TextColumn("住所", width="large"),
            }

            edited_df = st.data_editor(
                df_heirs,
                column_config=column_config,
                num_rows="dynamic",
                use_container_width=True,
                key="heir_grid"
            )

            st.divider()

            # 3. 保存ボタン
            if st.button("💾 データベースに保存・更新", type="primary", use_container_width=True):
                try:
                    target_case = session.query(Case).filter_by(case_id=current_case_id).first()

                    # A. 被相続人のUpsert
                    deceased = target_case.deceased_ref
                    if not deceased:
                        deceased = Deceased(case_id=target_case.case_id)
                        session.add(deceased)

                    # 氏名分割 (簡易)
                    if d_name:
                        parts = d_name.replace("　", " ").split(" ")
                        deceased.name_last = parts[0]
                        deceased.name_first = parts[1] if len(parts) > 1 else ""

                    # 日付
                    if d_date:
                        try:
                            deceased.date_of_death = datetime.strptime(d_date, "%Y-%m-%d").date()
                        except:
                            pass
                    
                    # 住所 (Addressテーブルへの登録とリンク)
                    # 本来はAddressテーブルにInsertしIDを取得するが、今回はDeceasedのフィールドがないため
                    # Deceasedテーブルに直接住所カラムがない場合はAddress経由で保存が必要。
                    # repomixの定義では last_address_id があるため、Addressを作成する。
                    if d_addr:
                        new_addr = Address(prefecture="", street_address=d_addr)
                        session.add(new_addr)
                        session.flush()
                        deceased.last_address_id = new_addr.id

                    # B. 相続人の洗い替え (既存削除 -> 新規登録)
                    # IDが変わるため実運用では注意が必要だが、要件の「Upsert」の精神に則り
                    # 名前と生年月日で一致判定してUpdateするのが理想。ここでは簡易実装として洗い替え。
                    for h in deceased.heirs:
                        session.delete(h)

                    for index, row in edited_df.iterrows():
                        if not row["name"]: continue

                        # 氏名分割
                        full_name = row["name"]
                        parts = full_name.replace("　", " ").split(" ")
                        lname = parts[0]
                        fname = parts[1] if len(parts) > 1 else ""

                        b_date = None
                        try:
                            b_date = datetime.strptime(str(row["birth_date"]), "%Y-%m-%d").date()
                        except:
                            pass

                        new_heir = Heir(
                            deceased=deceased,
                            name_last=lname,
                            name_first=fname,
                            relationship_type=row["relationship"],
                            date_of_birth=b_date
                        )
                        session.add(new_heir)
                        
                        # 相続人の住所も同様にAddressテーブルへ... (省略せず実装)
                        if row["address"]:
                            h_addr = Address(prefecture="", street_address=row["address"])
                            session.add(h_addr)
                            session.flush()
                            # 中間テーブル H_AddressHistory への登録が必要
                            from legal_system.models.tables import H_AddressHistory
                            # flushされているのでnew_heir.idが欲しいが、add段階では未確定の可能性あり
                            # commit直前に再度relationで紐付けるか、Heir登録後にflushが必要
                            
                    session.commit()
                    st.success(f"✅ 案件「{target_case.client_name}」の家族情報を更新しました！")
                    
                except Exception as e:
                    session.rollback()
                    st.error(f"保存エラー: {e}")

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py
````python
# src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py

import base64
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.config import Config
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Address, Case, CaseContactPoint, Contact, User

# ログ設定
logger = logging.getLogger(__name__)

st.set_page_config(page_title="顧客紹介連絡表 読取", page_icon="🤝", layout="wide")


# -----------------------------------------------------------------------------
# ヘルパー関数
# -----------------------------------------------------------------------------
def katakana_to_hiragana(text: str) -> str:
    """カタカナをひらがなに変換する簡易関数"""
    if not text:
        return ""
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            result += chr(code - 0x60)
        else:
            result += char
    return result

def get_next_provisional_number(session) -> str:
    """
    DB内の案件番号から最大値を探し、'G'なし4桁の数字（仮登録用）を返す。
    """
    cases = session.query(Case.case_number).all()
    max_num = 0
    pattern = re.compile(r"(\d+)")
    
    for (c_num,) in cases:
        if c_num:
            match = pattern.search(c_num)
            if match:
                try:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
    
    return f"{max_num + 1:04d}"


def ensure_user_exists(session, name_str: str) -> None:
    """担当者名の仮登録"""
    if not name_str or name_str == "未定":
        return

    existing = session.query(User).filter(User.name == name_str).first()
    if not existing:
        tmp_id = f"TMP_{datetime.now().strftime('%M%S')}"
        new_user = User(
            windows_id=tmp_id,
            name=name_str,
            department="未設定(AI取込)",
            role="Operator",
        )
        session.add(new_user)
        session.flush()
        st.toast(f"ℹ️ 新しい担当者「{name_str}」を仮登録しました。")


def analyze_image_with_ai(image_bytes: bytes) -> dict:
    """Gemini Visionによる解析"""
    try:
        img_str = base64.b64encode(image_bytes).decode("utf-8")
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

        # 3. プロンプト定義 (精度向上版)
        prompt_text = """
        あなたは熟練したデータ入力オペレーターです。
        提供された「顧客紹介連絡表」の画像を読み取り、以下の情報を抽出してJSON形式のみを出力してください。
        
        【重要：氏名の抽出ルール】
        - 「顧客名」および「フリガナ」の姓と名の間は、必ず『全角スペース』を入れてください。ただし、姓の中と氏の中はスペースは開けないこと
          例: "山田　太郎" (OK), "山田 太郎" (NG), "山田太郎" (NG), "山 田　太 郎" (NG),, "山田　太 郎" (NG), "山 田　太郎" (NG)

        【重要：電話番号の抽出ルール】
        1. **禁止事項**: 帳票の下部にある「SMBC日興証券」「担当者」「紹介元」欄に記載されている電話番号は、**絶対に**顧客の電話番号として抽出しないでください。
           これは紹介元の連絡先であり、顧客の連絡先ではありません。
        2. 顧客情報欄（上部または中部）にある電話番号のみを抽出してください。
        3. 携帯電話（090/080/070等）の記載がない場合は、無理に他の番号を入れず、空文字 "" にしてください。
        4. **郵便番号と住所**:
           - 記載された住所から郵便番号を推測し、"zip_code" フィールドに出力してください（例: "270-0101"）。
           - **重要**: "prefecture" (都道府県) と "street_address" (それ以降の住所) を分けて出力してください。
           
        【その他の抽出ルール】
        - 項目が見つからない場合は空文字 "" を設定してください。
        - JSON以外の解説文は一切不要です。
        
        【出力JSONスキーマ】
        {
            "client_name": "顧客氏名(全角スペース区切り)",
            "client_name_kana": "顧客フリガナ(全角スペース区切り)",
            "client_phone_1": "固定電話またはメインの連絡先",
            "client_phone_2": "携帯電話またはサブの連絡先(なければ空文字)",
            "client_address": "住所(都道府県から)",
            "sol_case_number": "SOL案件番号(英数字)",
            "introduction_date": "紹介日(YYYY-MM-DD形式に補正)",
            "referral_sec_branch_name": "紹介元支店名",
            "referral_sec_rep_name": "紹介元担当者名",
            "consent_date": "同意書取得日(YYYY-MM-DD形式)"
        }
        """

        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt_text},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"},
            ]
        )

        response = llm.invoke([message])
        content = response.content.replace("```json", "").replace("```", "").strip()
        data = json.loads(content)
        return data

    except Exception as e:
        logger.error(f"AI Vision Analysis Error: {e}")
        st.error(f"AI解析エラー: {e}")
        return {}


# -----------------------------------------------------------------------------
# メイン画面
# -----------------------------------------------------------------------------
def main():
    st.title("🤝 顧客紹介連絡表 読取・登録")
    
    provider = Config.AI_PROVIDER.upper()
    if provider == "VERTEX":
        st.success(f"🔒 Secure Mode: Vertex AI ({Config.GOOGLE_CLOUD_PROJECT}) が有効です。")
    else:
        st.warning(
            "⚠️ Development Mode: Google AI Studio (API Key) を使用中。\n"
            "個人情報(PII)を含む本番データのアップロードは禁止されています。ダミーデータのみを使用してください。"
        )

    db = DatabaseManager()
    session = db._get_session()

    # 1. アップロードエリア
    with st.container(border=True):
        col_file, col_mode = st.columns([1.5, 1])
        with col_file:
            uploaded_file = st.file_uploader("📂 PDFまたは画像をアップロード", type=["pdf", "png", "jpg", "jpeg"])
        with col_mode:
            st.write("⚙️ **登録モード**")
            mode = st.radio("選択", ["🆕 新規登録", "📂 既存案件に追加"], label_visibility="collapsed")

    if not uploaded_file:
        session.close()
        return

    # 2. 画像変換
    file_bytes = uploaded_file.read()
    display_img = None
    target_img_bytes = None

    try:
        if uploaded_file.type == "application/pdf":
            images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
            display_img = images[0]
        else:
            display_img = Image.open(BytesIO(file_bytes))
        
        buf = BytesIO()
        display_img.convert("RGB").save(buf, format="JPEG")
        target_img_bytes = buf.getvalue()

    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        session.close()
        return

    # 3. 解析実行
    if "ocr_res_05" not in st.session_state or st.session_state.get("current_file_05") != uploaded_file.name:
        st.session_state["ocr_res_05"] = None
        st.session_state["current_file_05"] = uploaded_file.name

    col_btn, _ = st.columns([1, 4])
    with col_btn:
        if st.button("🔍 AI解析を実行 (Gemini)", type="primary", use_container_width=True):
            with st.spinner("AIが帳票を視覚的に解析中..."):
                res = analyze_image_with_ai(target_img_bytes)
                st.session_state["ocr_res_05"] = res
                if res:
                    st.toast("✅ 読み取り完了", icon="✨")
                else:
                    st.error("データの抽出に失敗しました。")

    # 4. 結果表示 & 編集フォーム
    st.divider()
    ocr_data = st.session_state.get("ocr_res_05") or {}

    col_img, col_form = st.columns([1, 1.2])

    with col_img:
        st.subheader("📄 原本プレビュー")
        st.image(display_img, use_container_width=True)

    with col_form:
        st.subheader("📝 データ確認・登録")
        
        with st.form("referral_form"):
            col1, col2 = st.columns(2)
            
            # 案件番号
            case_no = get_next_provisional_number(session) if mode == "🆕 新規登録" else ""
            c_no_input = col1.text_input("案件番号 (仮登録用4桁)", value=case_no)
            
            # 氏名
            raw_kana = ocr_data.get("client_name_kana", "")
            clean_kana = katakana_to_hiragana(raw_kana)
            
            name = col1.text_input("顧客名", value=ocr_data.get("client_name", ""))
            kana = col2.text_input("フリガナ (ひらがな)", value=clean_kana)
            
            # 電話番号
            phone1 = col1.text_input("電話番号1 (固定)", value=ocr_data.get("client_phone_1", ""))
            phone2 = col2.text_input("電話番号2 (携帯)", value=ocr_data.get("client_phone_2", ""))
            
            # 住所 (郵便番号なしで表示)
            # AIが分割に失敗している場合のフォールバック
            ai_pref = ocr_data.get("client_prefecture", "")
            ai_street = ocr_data.get("client_street_address", "")
            full_addr_ai = ocr_data.get("client_address_full", "")
            
            # 画面表示用の初期値
            display_addr = full_addr_ai if full_addr_ai else f"{ai_pref}{ai_street}"
            
            addr = st.text_input("住所 (郵便番号なし)", value=display_addr)
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            sol = c1.text_input("SOL案件番号", value=ocr_data.get("sol_case_number", ""))
            branch = c2.text_input("支店名", value=ocr_data.get("referral_sec_branch_name", ""))
            rep = c3.text_input("担当者名", value=ocr_data.get("referral_sec_rep_name", ""))
            
            intro_date = st.text_input("紹介日", value=ocr_data.get("introduction_date", ""))

            submitted = st.form_submit_button("💾 データベースに保存", type="primary")

        if submitted:
            try:
                # 担当者仮登録
                if rep:
                    ensure_user_exists(session, rep)

                if mode == "🆕 新規登録":
                    # 日付変換
                    intro_dt = None
                    if intro_date:
                        try:
                            intro_dt = datetime.strptime(intro_date, "%Y-%m-%d").date()
                        except:
                            pass

                    # 1. 案件(Case)の作成
                    new_case = Case(
                        case_number=c_no_input,
                        client_name=name,
                        client_name_kana=kana,
                        sol_case_number=sol,
                        referral_sec_branch_name=branch,
                        referral_sec_rep_name=rep,
                        introduction_date=intro_dt,
                        created_at=datetime.now()
                    )
                    session.add(new_case)
                    session.flush() # ID確定

                    # 2. 住所(Address)の作成
                    ai_zip = ocr_data.get("client_zip_code", "")
                    # 画面で編集された住所を都道府県とそれ以外に分割 (簡易的)
                    # 本来は正規表現等で厳密にやるべきだが、ここではAIが取れたPrefectureを使うか、なければ空にする
                    save_pref = ai_pref if ai_pref in addr else ""
                    save_street = addr.replace(save_pref, "") if save_pref else addr

                    new_address = Address(
                        zip_code=ai_zip,
                        prefecture=save_pref if save_pref else "未判定", # Not Null制約のため
                        street_address=save_street,
                    )
                    session.add(new_address)
                    session.flush()

                    # 3. 電話番号(Contact)の作成
                    # 携帯番号優先ロジック
                    primary_phone_val = phone1
                    secondary_phone_val = phone2
                    
                    if phone2: # 携帯があればそれをプライマリ候補に
                        primary_phone_val = phone2
                        secondary_phone_val = phone1
                    
                    # メイン連絡先の登録
                    primary_contact_id = None
                    if primary_phone_val:
                        contact1 = Contact(value=primary_phone_val, type="PHONE", sub_type="Main")
                        session.add(contact1)
                        session.flush()
                        primary_contact_id = contact1.id
                    
                    # サブ連絡先の登録
                    secondary_contact_id = None
                    if secondary_phone_val:
                        contact2 = Contact(value=secondary_phone_val, type="PHONE", sub_type="Sub")
                        session.add(contact2)
                        session.flush()
                        secondary_contact_id = contact2.id

                    # 4. 紐付け(CaseContactPoint)の作成
                    if primary_contact_id:
                        # 本人の連絡先として登録
                        ccp1 = CaseContactPoint(
                            case_id=new_case.case_id,
                            contact_person_name=name,
                            relationship_to_client="本人",
                            address_id=new_address.id,
                            contact_id=primary_contact_id,
                            is_primary_contact=True
                        )
                        session.add(ccp1)
                    
                    if secondary_contact_id:
                        # 2つ目の連絡先があれば追加 (Addressは同じものを紐付ける)
                        ccp2 = CaseContactPoint(
                            case_id=new_case.case_id,
                            contact_person_name=name,
                            relationship_to_client="本人",
                            address_id=new_address.id,
                            contact_id=secondary_contact_id,
                            is_primary_contact=False
                        )
                        session.add(ccp2)

                    session.commit()
                    
                    st.toast("✅ 登録が完了しました", icon="check")
                    st.success(f"案件 {c_no_input} ({name}様) を登録しました。")
                    
                    time.sleep(1.5)
                    st.session_state["ocr_res_05"] = None
                    st.rerun()
                else:
                    st.info("既存案件への追加機能は現在開発中です。")

            except Exception as e:
                session.rollback()
                st.error(f"DB保存エラー: {e}")
                st.info("※ Addressテーブルの制約違反(Not Null等)の可能性があります。")

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/06_案件登録_手動.py
````python
# src/legal_system/ui/pages/06_案件登録_手動.py

import os
import sys
import time
from datetime import datetime

import streamlit as st

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, User
from src.services.folder_service import find_case_folder

st.set_page_config(page_title="新規案件 手動登録", page_icon="✍️", layout="wide")

def get_next_case_number_preview(session):
    """次の仮番号(数字4桁)をプレビュー"""
    # 実際にはDBManager等の共通関数を使うのが良いですが、ここでは簡易実装
    # "G"がつかない数字のみの最大値を探すロジックが必要
    return "0001" # 仮実装

def main():
    st.title("✍️ 新規案件 手動登録")
    st.caption("紹介連絡票を使わず、手動で案件を作成します。")

    db = DatabaseManager()
    session = db._get_session()

    # ユーザー一覧取得
    users = session.query(User).all()
    user_options = {u.name: u.id for u in users}
    user_options["未定"] = None

    with st.form("manual_register_form"):
        # --- 1. 案件情報 ---
        st.subheader("1. 案件基本情報")
        c1, c2, c3 = st.columns(3)
        
        # 仮番号の自動採番ロジックがあればそれを初期値にする
        case_num = c1.text_input("案件番号 (仮4桁 or G番号)", placeholder="例: 0101")
        
        manager_name = c2.selectbox("担当者1 (進捗)", list(user_options.keys()))
        operator_name = c3.selectbox("担当者2 (実務)", list(user_options.keys()))

        # --- 2. 契約者(顧客)情報 ---
        st.subheader("2. 契約者（顧客）情報")
        col_name1, col_name2 = st.columns(2)
        name_last = col_name1.text_input("氏名 (姓)")
        name_first = col_name2.text_input("氏名 (名)")
        
        col_kana1, col_kana2 = st.columns(2)
        kana_last = col_kana1.text_input("フリガナ (姓)")
        kana_first = col_kana2.text_input("フリガナ (名)")

        # --- 3. フォルダパス (自動検索機能付き) ---
        st.subheader("3. サーバーフォルダ")
        st.caption("顧客名からサーバー内のフォルダを検索します。")
        
        # フォーム内だとボタン操作でリロードされるため、検索ボタンはフォーム外に置くのが定石ですが、
        # ここではsession_stateを使って連携させます。
        
        folder_path_input = st.text_input("フォルダパス", key="folder_path_manual")
        
        # --- 登録ボタン ---
        submitted = st.form_submit_button("💾 案件を登録する", type="primary")

    # フォーム外のツール: フォルダ検索
    st.markdown("---")
    c_search, c_res = st.columns([1, 3])
    if c_search.button("🔍 氏名でフォルダを検索"):
        if name_last:
            full_name = name_last + (name_first or "")
            found = find_case_folder(full_name)
            if found:
                st.success(f"見つかりました: {found}")
                st.info("上の「フォルダパス」欄にコピー＆ペーストしてください。")
                st.code(found, language="text")
            else:
                st.error("フォルダが見つかりませんでした。")
        else:
            st.warning("先に「氏名 (姓)」を入力してください。")

    # 登録処理
    if submitted:
        if not case_num or not name_last:
            st.error("「案件番号」と「氏名(姓)」は必須です。")
        else:
            try:
                # 重複チェック (簡易)
                existing = session.query(Case).filter_by(case_number=case_num).first()
                if existing:
                    st.error(f"案件番号 {case_num} は既に登録されています。")
                else:
                    client_name = f"{name_last} {name_first}".strip()
                    client_kana = f"{kana_last} {kana_first}".strip()
                    
                    new_case = Case(
                        case_number=case_num,
                        client_name=client_name,
                        client_name_kana=client_kana,
                        folder_path=folder_path_input,
                        manager_id=user_options[manager_name],
                        operator_id=user_options[operator_name],
                        created_at=datetime.now()
                    )
                    session.add(new_case)
                    session.commit()
                    
                    st.success(f"案件 {case_num} ({client_name}様) を登録しました！")
                    time.sleep(1)
                    # 詳細画面へ遷移させたい場合、session_stateにIDを入れてリダイレクト等の工夫が必要
                    # Streamlitはページ遷移が苦手なので、トーストを出して終了が無難
                    
            except Exception as e:
                session.rollback()
                st.error(f"登録エラー: {e}")
            finally:
                session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/07_案件詳細_統合管理.py
````python
# src/legal_system/ui/pages/07_案件詳細_統合管理.py

import json
import os
import sys
import time

import streamlit as st

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased, Heir, User
from src.services.folder_service import open_local_folder
from src.services.deceased_service import update_case_number # 既存のサービス関数利用想定

st.set_page_config(page_title="案件詳細・管理", page_icon="🗂️", layout="wide")

def main():
    db = DatabaseManager()
    session = db._get_session()

    # --- 1. 案件選択エリア (サイドバー上部) ---
    st.sidebar.title("🗂️ 案件切替")
    
    # 全案件取得
    cases = session.query(Case).order_by(Case.case_number.desc()).all()
    if not cases:
        st.warning("案件が登録されていません。")
        session.close()
        return

    # セレクトボックス用ラベル作成
    case_options = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
    
    # session_stateで選択状態を保持
    if "selected_case_id" not in st.session_state:
        st.session_state["selected_case_id"] = list(case_options.values())[0]

    # 現在のインデックスを特定
    current_ids = list(case_options.values())
    try:
        current_index = current_ids.index(st.session_state["selected_case_id"])
    except ValueError:
        current_index = 0

    selected_label = st.sidebar.selectbox(
        "対象案件を選択", 
        list(case_options.keys()), 
        index=current_index
    )
    
    # ID更新
    case_id = case_options[selected_label]
    st.session_state["selected_case_id"] = case_id
    
    # DBから対象案件を取得
    current_case = session.query(Case).filter_by(case_id=case_id).first()

    st.sidebar.divider()

    # --- 2. メニュー選択 (サイドバー) ---
    menu = st.sidebar.radio(
        "メニュー",
        ["🏠 案件概要・基本情報", "🏦 銀行口座 登録", "📈 証券・その他資産", "🏘️ 不動産 登録", "✅ タスク管理"],
    )

    # --- 3. メインコンテンツ表示 ---
    st.title(f"{current_case.case_number}: {current_case.client_name} 様")

    # ==========================================
    # A. 案件概要・基本情報 (G番号修正・Kintoneコピーなど)
    # ==========================================
    if menu == "🏠 案件概要・基本情報":
        st.subheader("基本情報・操作")
        
        # --- Kintoneコピー & フォルダ操作 ---
        col_tool1, col_tool2 = st.columns(2)
        
        with col_tool1:
            st.info("📋 **Kintone連携データ**")
            # Kintone用JSONデータの作成 (簡易版)
            kintone_data = {
                "顧客コード": current_case.case_number,
                "顧客名": current_case.client_name,
                "フリガナ": current_case.client_name_kana or "",
                # ... 必要な項目を追加
            }
            json_str = json.dumps(kintone_data, ensure_ascii=False, indent=2)
            st.code(json_str, language="json")
            st.caption("👆 右上のコピーボタンでKintone用のデータを取得できます。")

        with col_tool2:
            st.warning("📂 **フォルダ操作**")
            path_val = current_case.folder_path or "未設定"
            st.text_input("現在のパス", value=path_val, disabled=True)
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.button("📂 フォルダを開く(Server)"):
                if open_local_folder(path_val):
                    st.success("サーバー側でフォルダを開きました。")
                else:
                    st.error("フォルダを開けませんでした。パスを確認してください。")
            
            # クリップボードコピー用 (st.codeを利用)
            if path_val != "未設定":
                st.code(path_val, language="text")
                st.caption("👆 パスをコピーしてエクスプローラーに貼り付けてください")

        st.divider()

        # --- 案件番号修正 (仮 -> 本番) ---
        with st.expander("✏️ 案件番号の修正 (G番号付与など)"):
            new_num = st.text_input("新しい案件番号", value=current_case.case_number)
            if st.button("更新する"):
                if new_num != current_case.case_number:
                    # 重複チェック等を行い更新
                    try:
                        current_case.case_number = new_num
                        session.commit()
                        st.success("案件番号を更新しました！リロードします。")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新エラー: {e}")

        # --- 被相続人・相続人情報 ---
        st.subheader("👤 被相続人・相続人情報")
        
        # 被相続人情報の表示・編集
        d = current_case.deceased_ref
        if not d:
            st.info("被相続人情報が未登録です。")
            if st.button("➕ 被相続人を登録"):
                new_d = Deceased(case_id=current_case.case_id)
                session.add(new_d)
                session.commit()
                st.rerun()
        else:
            with st.container(border=True):
                st.markdown(f"**被相続人: {d.name_last} {d.name_first}**")
                st.text(f"死亡日: {d.date_of_death}")
                # 編集フォーム等をここに配置可能

        # 相続人リスト
        st.markdown("##### 👨‍👩‍👧‍👦 相続人リスト")
        if d and d.heirs:
            for h in d.heirs:
                st.text(f"- {h.name_last} {h.name_first} ({h.relationship_type})")
        else:
            st.caption("登録なし")
        
        if st.button("➕ 相続人を追加 (編集画面へ)"):
            st.info("相続人追加機能は開発中です")

    # ==========================================
    # B. 銀行口座登録
    # ==========================================
    elif menu == "🏦 銀行口座 登録":
        st.subheader("🏦 銀行・金融資産管理")
        st.caption("この案件に紐づく金融資産を登録・編集します。")
        
        # 既存の資産一覧
        assets = current_case.financial_assets
        if assets:
            for a in assets:
                with st.expander(f"{a.bank_ref.bank_name} ({a.branch_ref.branch_name if a.branch_ref else '-'})"):
                    st.write(f"口座番号: {a.account_number}")
                    st.write(f"残高: {a.balance}")
        else:
            st.info("登録された口座はありません。")

        st.divider()
        st.markdown("#### 🆕 新規登録")
        # ここに `02_預貯金口座入力フォーム.py` のロジックをコンポーネント化して埋め込むと綺麗です
        st.info("※ ここに銀行登録フォームを表示します")

    # ==========================================
    # C. 不動産登録
    # ==========================================
    elif menu == "🏘️ 不動産 登録":
        st.subheader("🏘️ 不動産管理")
        st.info("不動産情報の登録画面です。（開発中）")

    session.close()

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/99_書式座標登録ツール.py
````python
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
st.set_page_config(layout="wide", page_title="書式・座標管理", page_icon="🛠️")

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
    "----- ★DB連携: 氏名 -----": {"label": "", "val": ""},
    "{被相続人 氏名(全)}": {"label": "被相続人氏名", "val": "{deceased_name}"},
    "{被相続人 氏(姓)}": {"label": "被相続人_姓", "val": "{deceased_name_last}"},
    "{被相続人 名}": {"label": "被相続人_名", "val": "{deceased_name_first}"},
    "{相続人 氏名(全)}": {"label": "相続人氏名", "val": "{heir_name}"},
    "{相続人 氏(姓)}": {"label": "相続人_姓", "val": "{heir_name_last}"},
    "{相続人 名}": {"label": "相続人_名", "val": "{heir_name_first}"},
    "{相続人 代理人氏名}": {"label": "相続人_代理人", "val": "{heir_name} 代理人"},
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
    "数字「1」": {"label": "数字1", "val": "1", "size": 11.0},
    "チェック (✓)": {"label": "チェック", "val": "✓", "size": 14.0},
    "丸 (◯)": {"label": "丸", "val": "◯", "size": 14.0},
    "----- 担当者・会社 -----": {"label": "", "val": ""},
    "担当者名": {"label": "担当者氏名", "val": user_info["name"]},
    "代理人肩書": {"label": "代理人肩書", "val": "代理人"},
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

# 入力フォーム用
if "input_label" not in st.session_state:
    st.session_state["input_label"] = ""
if "input_val" not in st.session_state:
    st.session_state["input_val"] = ""
if "input_size" not in st.session_state:
    st.session_state["input_size"] = 11.0  # ★初期値11.0
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
# ★座標エディタ画面のロジック
# ==========================================
def render_coordinate_editor():
    # サイドバー: ファイル選択（新規アップロードは廃止）
    st.sidebar.header("📂 対象ファイル")
    all_files = db.get_all_files()
    if not all_files:
        st.sidebar.warning("登録済みのファイルがありません。")
        st.info(
            "👈 サイドバーで「📥 雛形ファイル登録」を選んでファイルを登録してください。"
        )
        return

    file_options = {f"{f['filename']}": f for f in all_files}

    current_fname = st.session_state.get("target_file_name")
    idx = 0
    if current_fname:
        keys = list(file_options.keys())
        for i, k in enumerate(keys):
            if current_fname in k:
                idx = i
                break

    selected_label = st.sidebar.selectbox(
        "編集するファイルを選択", list(file_options.keys()), index=idx
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
    if not target_file_bytes:
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

        def draw_mark(raw_x, raw_y, val, sz, clr):
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

        if st.session_state["input_val"]:
            draw_mark(
                st.session_state["last_x"],
                st.session_state["last_y"],
                st.session_state["input_val"],
                size_in,
                color_in,
            )

        if not df_existing.empty:
            for _, c in df_existing.iterrows():
                if c["page"] == st.session_state["current_page"]:
                    draw_mark(c["x"], c["y"], c["value"], c["font_size"], c["color"])

        # width指定でズレ防止
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

    # --- 下部: リストエリア ---
    st.divider()
    st.subheader("📋 登録済みリスト")

    cols = ["label", "x", "y", "page", "font_size", "color", "value", "desc", "id"]
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
                            # 簡易プレビュー用スケール (72/200)
                            scale = 72.0 / 200.0
                            draw_x = float(row["x"]) * scale
                            top_y = ph - (float(row["y"]) * scale)
                            f_size = float(row["font_size"])
                            c_obj = red if row["color"] == "red" else black
                            can_page.setFillColor(c_obj)
                            can_page.setStrokeColor(c_obj)

                            val = row["value"]
                            if str(val).startswith("RECT:"):
                                try:
                                    dims = val.replace("RECT:", "").split("x")
                                    w_pt, h_pt = float(dims[0]), float(dims[1])
                                    can_page.rect(
                                        draw_x,
                                        top_y - h_pt,
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
                                    draw_x, top_y - (f_size * 0.9), str(val)
                                )

                        can_page.save()
                        packet_page.seek(0)
                        overlay = PdfReader(packet_page)
                        page_obj.merge_page(overlay.pages[0])
                    output.add_page(page_obj)
                out_stream = BytesIO()
                output.write(out_stream)
                st.download_button(
                    "📥 テストPDFダウンロード",
                    out_stream,
                    "test.pdf",
                    "application/pdf",
                )
            except Exception as e:
                st.error(f"エラー: {e}")


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
````

## File: src/legal_system/ui/pages/backup/98_Llama実験室.py
````python
# src/legal_system/ui/pages/98_Llama実験室.py

import base64
import os
import sys
from io import BytesIO

import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

st.set_page_config(page_title="Llama Vision 実験室", page_icon="🦙", layout="wide")

def main():
    st.title("🦙 Llama(Local) Vision 実験室")
    st.markdown("""
    クラウドを使わず、**ローカルPC内のAI（Ollama）**で画像を読み取る実験ページです。
    個人情報を含むファイルでも安全にテストできます。
    
    ※ 事前にターミナルで `ollama pull llava` を実行して、視覚対応モデルを入れておく必要があります。
    """)

    # サイドバーでモデル選択
    model_name = st.sidebar.selectbox(
        "使用するVisionモデル",
        ["llava", "llama3.2-vision", "moondream"],
        index=0
    )

    # 1. ファイルアップロード
    uploaded_file = st.file_uploader(
        "帳票画像/PDFをアップロード", type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file:
        pil_image = None
        
        # PDFか画像かで読み込み処理を分岐
        if uploaded_file.type == "application/pdf":
            try:
                with st.spinner("PDFを画像に変換中..."):
                    # 1ページ目のみ取得
                    images = convert_from_bytes(uploaded_file.read(), dpi=150, first_page=1, last_page=1)
                    pil_image = images[0]
            except Exception as e:
                st.error(f"PDF変換エラー: {e}")
                return
        else:
            pil_image = Image.open(uploaded_file)

        if pil_image:
            # 2. 画像プレビュー
            st.divider()
            col_img, col_result = st.columns([1, 1])
            
            with col_img:
                st.subheader("📄 対象画像")
                st.image(pil_image, use_container_width=True)

            # 3. 解析実行
            with col_result:
                st.subheader("🤖 Local AI解析結果")
                
                if st.button("🚀 Llama(Ollama)で読み取る", type="primary", use_container_width=True):
                    # 画像をBase64化
                    buffered = BytesIO()
                    # JPEGに変換して軽量化（ローカルLLMは重いため）
                    pil_image.convert("RGB").save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    with st.spinner(f"ローカルAI ({model_name}) が画像を解析中... PCが重くなる可能性があります"):
                        try:
                            # Ollamaの初期化
                            llm = ChatOllama(
                                model=model_name,
                                temperature=0.0,
                                # JSONモードを強制しないほうがVisionモデルでは安定することがあるが、
                                # 構造化データが欲しいので指示で頑張らせる
                            )

                            # プロンプト作成
                            # ローカルモデルは日本語指示よりも英語指示の方が精度が出る傾向があるため、
                            # 内部プロンプトは英語にしつつ、出力は日本語JSONを要求するテクニックを使います。
                            prompt_text = """
                            You are an OCR assistant. Look at this document image and extract the following information into a JSON format.
                            If a field is not found, use an empty string "".
                            
                            Fields to extract:
                            - ClientName (顧客名)
                            - ClientNameKana (フリガナ)
                            - PhoneNumber (電話番号)
                            - Address (住所)
                            - SOL_CaseNumber (SOL案件番号)
                            - ReferralDate (紹介日)
                            - BranchName (紹介元支店名)
                            - RepName (紹介元担当者名)

                            Output must be valid JSON only. Do not add any explanation.
                            """

                            message = HumanMessage(content=[
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}
                            ])

                            # 実行
                            response = llm.invoke([message])
                            
                            # 結果表示
                            st.success("解析完了")
                            st.write(response.content)
                            
                            # JSONパースを試みる（ローカルAIは余計な挨拶を入れることがあるため）
                            try:
                                import json
                                # 最初の { から 最後の } までを切り出す簡易抽出
                                content = response.content
                                start = content.find("{")
                                end = content.rfind("}") + 1
                                if start != -1 and end != 0:
                                    json_str = content[start:end]
                                    data = json.loads(json_str)
                                    st.json(data)
                            except:
                                st.caption("※完全なJSON形式ではありませんでしたが、上記テキストに含まれています。")

                        except Exception as e:
                            st.error(f"解析エラーが発生しました: {e}")
                            st.warning("考えられる原因: 指定したモデルが `ollama pull` されていない、またはPCのメモリ不足。")

if __name__ == "__main__":
    main()
````

## File: src/legal_system/ui/pages/backup/99_Gemini実験室.py
````python
# src/legal_system/ui/pages/99_Gemini実験室.py

import base64
import os
import sys
from io import BytesIO

import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pdf2image import convert_from_bytes
from PIL import Image

# パス解決
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
sys.path.append(ROOT_DIR)

st.set_page_config(page_title="Gemini実験室", page_icon="🧪", layout="wide")

def main():
    st.title("🧪 Gemini Vision 実験室 (シンプル読取版)")
    st.markdown("""
    OCRエンジンを使わず、**Geminiに直接「画像」を見せて**情報を読み取らせる実験ページです。
    
    ⚠️ **注意**
    マスキング機能はありません。
    **必ず「架空の人物」や「ダミーデータ」のPDF/画像のみを使用してください。**
    """)

    # APIキー確認
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("❌ GOOGLE_API_KEY が設定されていません。")
        return

    # 1. ファイルアップロード
    uploaded_file = st.file_uploader(
        "帳票画像/PDFをアップロード (ダミーデータ限定)", type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file:
        pil_image = None
        
        # PDFか画像かで読み込み処理を分岐
        if uploaded_file.type == "application/pdf":
            try:
                with st.spinner("PDFを画像に変換中..."):
                    # 1ページ目のみ取得
                    images = convert_from_bytes(uploaded_file.read(), dpi=200, first_page=1, last_page=1)
                    pil_image = images[0]
            except Exception as e:
                st.error(f"PDF変換エラー: {e}")
                st.info("Windowsの場合はPopplerがインストールされているか確認してください。")
                return
        else:
            pil_image = Image.open(uploaded_file)

        if pil_image:
            # 2. 画像プレビュー
            st.divider()
            col_img, col_result = st.columns([1, 1])
            
            with col_img:
                st.subheader("📄 アップロード画像")
                st.image(pil_image, use_container_width=True)

            # 3. 解析実行
            with col_result:
                st.subheader("🤖 AI解析結果")
                
                if st.button("🚀 Geminiで読み取る", type="primary", use_container_width=True):
                    # 画像をBase64化 (API送信のため)
                    buffered = BytesIO()
                    # 形式をJPEGに統一して軽量化
                    pil_image.convert("RGB").save(buffered, format="JPEG")
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    
                    with st.spinner("Geminiが画像を解析中..."):
                        try:
                            # モデル初期化 (Gemini 1.5 Flash 推奨)
                            llm = ChatGoogleGenerativeAI(
                                model="gemini-2.5-flash", 
                                temperature=0.0
                            )

                            # プロンプト作成
                            prompt_text = """
                            この帳票画像を読み取り、以下の項目を抽出してJSON形式で出力してください。
                            項目が見つからない、または空欄の場合は空文字にしてください。

                            {
                                "顧客名": "",
                                "フリガナ": "",
                                "電話番号1": "",
                                "電話番号2": "",
                                "住所": "",
                                "SOL案件番号": "",
                                "紹介日": "",
                                "紹介元支店名": "",
                                "紹介元担当者名": ""
                            }
                            """

                            message = HumanMessage(content=[
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_str}"}
                            ])

                            # 実行
                            response = llm.invoke([message])
                            
                            # 結果表示
                            st.success("解析完了")
                            st.code(response.content, language="json")

                        except Exception as e:
                            st.error(f"解析エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
````

## File: src/services/folder_service.py
````python
# src/services/folder_service.py
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

# サーバーの基準パス (Windowsのネットワークパス形式)
SERVER_BASE_PATH = r"\\192.168.11.20\行政書士法人チェスター\01.個別ＪＯＢ"

def find_case_folder(search_term: str) -> Optional[str]:
    """
    基準パス配下から、search_term (顧客名など) を含むフォルダを検索してパスを返す。
    """
    if not search_term:
        return None

    target_path = Path(SERVER_BASE_PATH)
    
    if not target_path.exists():
        # ローカルテスト用に一時フォルダをフォールバックとして設定する場合の例
        # target_path = Path(r"C:\TestFolder") 
        return None

    try:
        # 空白除去
        query = search_term.replace(" ", "").replace("　", "")
        # 直下のフォルダを走査
        for item in target_path.iterdir():
            if item.is_dir():
                folder_name = item.name.replace(" ", "").replace("　", "")
                if query in folder_name:
                    return str(item.absolute())
    except Exception as e:
        print(f"Folder search error: {e}")
        return None

def open_local_folder(path: str):
    """
    サーバー側(Streamlit実行環境)でフォルダを開く試み。
    クライアントPCで開くわけではない点に注意が必要ですが、社内LAN(オンプレ)なら機能する場合が多いです。
    """
    if not path or not os.path.exists(path):
        return False
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False
````

## File: src/views/client_register.py
````python
# src/views/client_register.py
from flet import (
    AppBar, Colors, Column, Container, Divider, Dropdown, ElevatedButton,
    FilePicker, FilePickerResultEvent, FontWeight, Icon, Icons, Page,
    Row, ScrollMode, SnackBar, Text, TextField, View, border, padding,
    ButtonStyle, dropdown, MainAxisAlignment,
)
from typing import Dict, List

# サービス
from src.services.deceased_service import (
    add_new_case_for_client_registration,
    get_all_users,
    get_case_id_by_deceased_id,
    get_next_case_number_service,
    update_case_folder_path,
    is_case_number_duplicate,
)
from src.services.folder_service import find_case_folder # 追加
from src.components.business.contact_controls import (
    add_new_contact_row, collect_contacts, create_contact_input_row
)

class ClientRegisterView(View):
    def __init__(self, page: Page):
        super().__init__(route="/client_register", scroll=ScrollMode.AUTO)
        self.page = page
        self._init_components()

        self.appbar = AppBar(
            title=Text("✨ 新規案件 手動登録"),
            bgcolor="surfaceVariant",
            color="onSurfaceVariant",
        )

        self.controls = [
            Container(
                padding=padding.all(30),
                content=Column([
                    Text("手動で新しい案件を登録します。", size=16),
                    Divider(),

                    # --- 1. 案件・担当者 ---
                    Text("案件情報", weight=FontWeight.BOLD, size=18, color="primary"),
                    Row([self.case_number_field, self.manager_field, self.operator_field]),
                    Divider(),

                    # --- 2. 顧客（契約者）情報 ---
                    Text("👤 契約者（依頼者）情報", weight=FontWeight.BOLD, size=18, color="primary"),
                    Row([self.name_last_field, self.name_first_field]),
                    Row([self.kana_last_field, self.kana_first_field]),
                    Divider(),

                    # --- 3. フォルダ設定（自動検索付き） ---
                    Text("📁 案件フォルダ", weight=FontWeight.BOLD, size=18, color="primary"),
                    Row([
                        self.path_field,
                        ElevatedButton(
                            "サーバーから自動検索",
                            icon=Icons.SEARCH,
                            on_click=self.auto_search_folder,
                            bgcolor="secondaryContainer",
                            color="onSecondaryContainer",
                            tooltip="顧客名でサーバー上のフォルダを探します"
                        ),
                        ElevatedButton(
                            "選択",
                            icon=Icons.FOLDER_OPEN,
                            on_click=self.open_folder_dialog,
                        ),
                    ]),
                    Divider(),

                    # --- 保存ボタン ---
                    Row([
                        ElevatedButton("キャンセル", on_click=lambda _: self.page.go("/")),
                        ElevatedButton(
                            "登録して詳細へ",
                            icon=Icons.SAVE,
                            on_click=self.save_case,
                            style=ButtonStyle(bgcolor="primary", color="onPrimary", padding=20)
                        ),
                    ], alignment=MainAxisAlignment.END),
                ], spacing=20)
            )
        ]

    def _init_components(self):
        self.folder_picker = FilePicker(on_result=self.get_directory_result)
        self.page.overlay.append(self.folder_picker)

        # 案件番号 (初期値は連番の仮番号)
        self.case_number_field = TextField(
            label="案件番号 (仮/G)", width=200, 
            value=get_next_case_number_service()
        )

        # 担当者プルダウン
        self.user_map = get_all_users()
        opts = [dropdown.Option(str(u), n) for u, n in self.user_map.items()]
        opts.insert(0, dropdown.Option("", "未割当"))
        self.manager_field = Dropdown(label="担当者1", width=200, options=opts)
        self.operator_field = Dropdown(label="担当者2", width=200, options=opts)

        # 氏名
        self.name_last_field = TextField(label="姓", width=200)
        self.name_first_field = TextField(label="名", width=200)
        self.kana_last_field = TextField(label="せい", width=200)
        self.kana_first_field = TextField(label="めい", width=200)

        # フォルダパス
        self.path_field = TextField(label="フォルダパス", width=500)

    # --- フォルダ関連 ---
    def get_directory_result(self, e: FilePickerResultEvent):
        if e.path:
            self.path_field.value = e.path
            self.page.update()

    def open_folder_dialog(self, e):
        self.folder_picker.get_directory_path("フォルダを選択")

    def auto_search_folder(self, e):
        """顧客名を使ってサーバーフォルダを検索"""
        name = self.name_last_field.value + self.name_first_field.value
        if not name:
            self.page.open(SnackBar(Text("先に氏名を入力してください"), bgcolor=Colors.RED))
            return
        
        self.page.open(SnackBar(Text(f"「{name}」でフォルダを検索中...")))
        self.page.update()

        found_path = find_case_folder(name)
        if found_path:
            self.path_field.value = found_path
            self.page.open(SnackBar(Text(f"見つかりました: {found_path}"), bgcolor=Colors.GREEN))
        else:
            self.page.open(SnackBar(Text("フォルダが見つかりませんでした。手動で選択してください。"), bgcolor=Colors.ORANGE))
        self.page.update()

    # --- 保存処理 ---
    def save_case(self, e):
        # 必須チェック
        if not self.case_number_field.value or not self.name_last_field.value:
            self.page.open(SnackBar(Text("案件番号と氏名(姓)は必須です"), bgcolor=Colors.RED))
            return

        # 重複チェック
        if is_case_number_duplicate(self.case_number_field.value):
            self.page.open(SnackBar(Text("この案件番号は既に存在します"), bgcolor=Colors.RED))
            return

        try:
            # 登録処理 (add_new_case_for_client_registration は既存のまま利用可能)
            # ※ 担当者IDの変換などは省略せず実装してください
            m_id = int(self.manager_field.value) if self.manager_field.value else None
            o_id = int(self.operator_field.value) if self.operator_field.value else None
            
            new_id = add_new_case_for_client_registration(
                case_number=self.case_number_field.value,
                name=f"{self.name_last_field.value} {self.name_first_field.value}",
                kana_last=self.kana_last_field.value,
                kana_first=self.kana_first_field.value,
                # ... 他の引数は空で渡すか、フォームを追加して渡す
                manager_id=m_id,
                operator_id=o_id,
                phone_contacts=[], email_contacts=[], # 簡易版のため空
                rel="", hometown="", zip_code="", pref="", city="", street="", building="", dob=None, dod=None
            )

            if new_id > 0:
                case_id = get_case_id_by_deceased_id(new_id)
                # パス更新
                if self.path_field.value:
                    update_case_folder_path(case_id, self.path_field.value)
                
                self.page.open(SnackBar(Text("登録しました！"), bgcolor=Colors.GREEN))
                # 詳細画面へ遷移 (CaseHub)
                self.page.go(f"/case/{case_id}/overview")
            
        except Exception as ex:
            self.page.open(SnackBar(Text(f"エラー: {ex}"), bgcolor=Colors.RED))
````

## File: src/views/detail.py
````python
# src/views/detail.py

import threading
import time
import os
import tkinter as tk
from tkinter import messagebox
from typing import Optional, Dict, Any, List

# Flet Imports
from flet import (
    AlertDialog,
    ButtonStyle,
    Colors,
    Column,
    Container,
    CrossAxisAlignment,
    Divider,
    Dropdown,
    ElevatedButton,
    FilePicker,
    FilePickerResultEvent,
    FontWeight,
    IconButton,
    Icons,
    MainAxisAlignment,
    Page,
    Row,
    ScrollMode,
    SnackBar,
    Text,
    TextButton,
    TextField,
    View,
    border,
    dropdown,
    padding,
)

# Selenium / Automation Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from dotenv import load_dotenv

# Internal Imports
from src.utils.date_utils import (
    convert_seireki_to_wareki,
)
from src.utils.ui_utils import show_confirm_dialog

from src.services.deceased_service import (
    get_all_users,
    get_address_by_id,
    get_address_info,
    get_case_by_id,
    get_case_folder_path,
    get_contact_info,
    get_deceased_by_case_id,
    get_deceased_by_id,
    get_kintone_integration_data,
    update_case_assignment,
    update_case_folder_path,
    delete_case_and_all_related_data,
    delete_heir,
    update_case_number,
    normalize_folder_path,
)

from src.utils.file_system import open_folder_in_explorer # フォルダを開くユーティリティ(要実装)
from src.services.folder_service import find_case_folder
from src.services.kintone_sync_service import copy_kintone_data_to_clipboard

def DeceasedDetailView(page: Page, case_id: int) -> View:
    # 既存のデータ取得ロジック...
    case = get_case_by_id(case_id)
    deceased = get_deceased_by_case_id(case_id)
    
    # --- 案件番号編集 (仮 -> G番号) ---
    def save_case_number(e):
        new_num = case_number_field.value.strip()
        # ここでDB更新処理を呼ぶ
        if update_case_number(case.case_id, new_num):
            page.open(SnackBar(Text(f"案件番号を {new_num} に変更しました"), bgcolor=Colors.GREEN))
            # 画面リフレッシュが必要ならここに記述
        else:
            page.open(SnackBar(Text("更新失敗：重複している可能性があります"), bgcolor=Colors.RED))

    case_number_field = TextField(
        label="案件番号", value=case.case_number, width=150,
        suffix=IconButton(Icons.SAVE, on_click=save_case_number, tooltip="番号を保存")
    )

    # --- フォルダパス操作 ---
    path_field = TextField(label="フォルダパス", value=get_case_folder_path(case_id), expand=True)

    def open_folder(e):
        path = path_field.value
        if path:
            open_folder_in_explorer(path) # エクスプローラーで開く
        else:
            page.open(SnackBar(Text("パスが設定されていません"), bgcolor=Colors.RED))

    def auto_find_folder(e):
        # 顧客名で再検索
        if deceased:
            name = f"{deceased.name_last}{deceased.name_first}"
            found = find_case_folder(name)
            if found:
                path_field.value = found
                update_case_folder_path(case_id, found) # DB保存
                page.open(SnackBar(Text("フォルダを特定し保存しました"), bgcolor=Colors.GREEN))
                page.update()
            else:
                page.open(SnackBar(Text("見つかりませんでした"), bgcolor=Colors.ORANGE))

    # --- Kintoneコピー ---
    def copy_kintone(e):
        if copy_kintone_data_to_clipboard(case_id):
            page.open(SnackBar(Text("Kintone用データをクリップボードにコピーしました！"), bgcolor=Colors.GREEN))
        else:
            page.open(SnackBar(Text("データコピーに失敗しました"), bgcolor=Colors.RED))

    # --- レイアウト ---
    # ヘッダー部分のみ抜粋
    header_section = Container(
        padding=10,
        bgcolor="surfaceVariant",
        border_radius=10,
        content=Column([
            Row([
                Icon(Icons.FOLDER_SHARED, size=30),
                Text("案件情報・操作", size=20, weight=FontWeight.BOLD),
                Container(expand=True),
                ElevatedButton("Kintone用コピー", icon=Icons.COPY, on_click=copy_kintone, bgcolor=Colors.AMBER_100, color=Colors.BROWN_900),
                ElevatedButton("案件削除", icon=Icons.DELETE, bgcolor=Colors.RED_100, color=Colors.RED_900), # 削除ロジックは既存流用
            ]),
            Divider(),
            Row([
                case_number_field,
                Container(width=20),
                path_field,
                IconButton(Icons.FOLDER_OPEN, on_click=open_folder, tooltip="フォルダを開く"),
                IconButton(Icons.sync, on_click=auto_find_folder, tooltip="フォルダ自動再検索"),
            ])
        ])
    )

    # 相続人リストセクション (既存のheirs_controlsロジックを利用)
    # 追加ボタンで /heir_edit/new?deceased_id=... へ遷移させる
    
    return Column([
        header_section,
        # ... 被相続人情報、相続人リスト、その他既存コンポーネント ...
    ], scroll=ScrollMode.AUTO)
````

## File: .dockerignore
````
.git
.venv
.rye
__pycache__
*.pyc
.env
.DS_Store
data/db/chroma  # ローカルDBはホスト側からマウントするためコピー不要
data/db/sql
repomix-output.md
````

## File: .python-version
````
3.12.4
````

## File: .streamlit/config.toml
````toml
[theme]
# ベースとなるテーマ（"light" または "dark"）
base = "light"

# メインのアクセントカラー（ボタンなど）
primaryColor = "#d33682"

# 背景色
backgroundColor = "#ffffff"

# サイドバーなどの背景色
secondaryBackgroundColor = "#f0f2f6"

# 文字色
textColor = "#262730"

# フォント
font = "sans serif"
````

## File: bank_master.json
````json
[
    {
        "bank_name": "三菱UFJ銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "遺産分割協議書（実印押印）",
            "相続人全員の印鑑証明書（6ヶ月以内）",
            "被相続人の出生から死亡までの連続した戸籍謄本",
            "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
            "【代理人】行政書士証票のコピー（原本照合済）",
            "【代理人】委任状（銀行所定様式または実印押印のある任意様式）"
        ],
        "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
        "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）"
    },
    {
        "bank_name": "ゆうちょ銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "相続確認表（Web入力可）",
            "貯金等相続手続請求書（代理人による署名・実印）",
            "【代理人】特定事務任用カード（提示のみ）",
            "【代理人】委任状（実印押印必須）"
        ],
        "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
        "original_return_policy": "原則として原本還付可。コピーの提出が必要。"
    },
    {
        "bank_name": "三井住友銀行",
        "procedure_type": "相続手続（代理人）",
        "required_documents": [
            "相続手続依頼書（代理人署名）",
            "【代理人】実印および印鑑証明書（6ヶ月以内）",
            "【代理人】行政書士証票または識別カード",
            "被相続人の全戸籍（出生〜死亡）"
        ],
        "notes": "※Web予約をしてからの来店が推奨される。",
        "original_return_policy": "原本還付可"
    }
]
````

## File: create_rule_master.py
````python
import json
from typing import Any, Dict, List

# プロジェクトルートに作成される手続要件マスタ
DATA_FILE: str = "bank_master.json"


def create_initial_bank_data() -> List[Dict[str, Any]]:
    """
    行政書士業務に特化した銀行マスタデータの初期セットを生成する。
    """
    banks = [
        {
            "bank_name": "三菱UFJ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "遺産分割協議書（実印押印）",
                "相続人全員の印鑑証明書（6ヶ月以内）",
                "被相続人の出生から死亡までの連続した戸籍謄本",
                "【代理人】行政書士の印鑑証明書（発行後6ヶ月以内）",
                "【代理人】行政書士証票のコピー（原本照合済）",
                "【代理人】委任状（銀行所定様式または実印押印のある任意様式）",
            ],
            "notes": "※任意様式の委任状を使用する場合、捨印および『解約金の受領権限』の明記が必須。",
            "original_return_policy": "戸籍等の原本還付可（要・原本還付請求のゴム印）",
        },
        {
            "bank_name": "ゆうちょ銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続確認表（Web入力可）",
                "貯金等相続手続請求書（代理人による署名・実印）",
                "【代理人】特定事務任用カード（提示のみ）",
                "【代理人】委任状（実印押印必須）",
            ],
            "notes": "※窓口ではなく相続センターへの郵送対応が基本となるケースが多い。要事前確認。",
            "original_return_policy": "原則として原本還付可。コピーの提出が必要。",
        },
        {
            "bank_name": "三井住友銀行",
            "procedure_type": "相続手続（代理人）",
            "required_documents": [
                "相続手続依頼書（代理人署名）",
                "【代理人】実印および印鑑証明書（6ヶ月以内）",
                "【代理人】行政書士証票または識別カード",
                "被相続人の全戸籍（出生〜死亡）",
            ],
            "notes": "※Web予約をしてからの来店が推奨される。",
            "original_return_policy": "原本還付可",
        },
    ]
    return banks


def save_bank_master(data: List[Dict[str, Any]]) -> None:
    try:
        # プロジェクトルートに保存
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"✅ 成功: '{DATA_FILE}' を作成しました。")
        print("   これで『01_銀行手続要件_確認』ページが動作します。")
    except IOError as e:
        print(f"❌ エラー: ファイルの書き込みに失敗しました。詳細: {e}")


if __name__ == "__main__":
    bank_data = create_initial_bank_data()
    save_bank_master(bank_data)
````

## File: data/db/chroma/.keep
````

````

## File: data/db/sql/.keep
````

````

## File: data/rules/company_rules.md
````markdown
# 弊社（行政書士法人）共通業務ルール
## 回答のスタイル
- 挨拶や前置き（「ご案内します」等）は一切不要。結論と箇条書きのみで出力すること。
- 語尾は「です・ます」調だが、簡潔にすること。
- 申請主体は不要（自明のため省略）。
- 証明日はすべて「被相続人の死亡日」を記載すること。（法定相続情報一覧図で確認）
- 既経過利息証明の必要有無：定期預金の口座があれば必ず「必要」とする。
- 取引明細の申請：税申告案件のみ必要。税理士へ有無と期間を確認するよう案内すること。
- 残高証明書の申請提出書類：
  1. 法定相続情報一覧図
  2. 委任状（代表相続人のみ）
  3. 印鑑証明書（代表相続人と弊社分）
  4. 履歴事項証明（弊社分）
  5. 弊社代表の行政書士証票と運転免許証のコピー [参照ファイル](https://example.cybozu.com/k/123/edit)

## 申請書類の共通仕様
- **申請書への押印**: 弊社の「実印（代表印）」を使用する。（認印は不可）
- **戸籍書類**: 原則として「法定相続情報一覧図」の原本還付請求付き提出とする。
  - ※急ぎで一覧図がない場合のみ「被相続人の出生〜死亡の除籍謄本＋相続人の現在戸籍」とする。
- **印鑑証明書**: 
  - 顧客（相続人）のものと、弊社（代理人）のものが必要。
  - 有効期限は銀行の規定に従うが、指定がない場合は「6ヶ月以内」のものを準備する。

## 手数料の支払い
- 原則として「銀行振込」を選択する。（相続人口座からの引落しは選択しない）
- 振込手続きは経理へ依頼すること。
- **経理依頼URL**: [Kintone経理アプリ](https://example.cybozu.com/k/123/edit) （ここから申請レコードを作成）

## ゆうちょ銀行特有のルール
- ゆうちょ銀行の残高証明手数料は、窓口支払ではなく「会社通帳からの引落とし」となる。
- **【必須表示】ゆうちょ銀行の残高証明書は、回答の最後に必ず以下のリンクを表示**:
  - [ゆうちょ引落管理スプレッドシート](https://example.cybozu.com/k/123/edit)
````

## File: data/templates/.keep
````

````

## File: docker-compose.yml
````yaml
# docker-compose.yml
services:
  # --- 1. アプリケーションサーバー (Streamlit) ---
  app:
    build: .
    container_name: legal_app
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "8501:8501"  # ブラウザからアクセスするポート
    environment:
    - POSTGRES_HOST=db
    - POSTGRES_PORT=5432
    - POSTGRES_DB=${POSTGRES_DB}        # ★ .envから読み込み
    - POSTGRES_USER=${POSTGRES_USER}    # ★ .envから読み込み
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD} # ★ .envから読み込み
    - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    # environment:
    #   - POSTGRES_HOST=db
    #   - POSTGRES_PORT=5432
    #   - POSTGRES_DB=legal_db
    #   - POSTGRES_USER=postgres
    #   - POSTGRES_PASSWORD=password
    #   # 本番ではGoogle API Key等はここで渡すか、.envファイルを読み込ませます
    #   - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    depends_on:
      - db
    volumes:
      # ホストのソースコードをコンテナにマウント (開発中は変更が即反映されるように)
      - ./src:/app/src
      - ./data:/app/data
    restart: always

  # --- 2. データベースサーバー (PostgreSQL) ---
  db:
    image: postgres:15
    container_name: legal_db
    environment:
      - POSTGRES_DB=${POSTGRES_DB}        # ★ .envから読み込み
      - POSTGRES_USER=${POSTGRES_USER}    # ★ .envから読み込み
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD} # ★ .envから読み込み
    ports:
      - "5432:5432"
  # db:
  #   image: postgres:15
  #   container_name: legal_db
  #   environment:
  #     - POSTGRES_DB=legal_db
  #     - POSTGRES_USER=postgres
  #     - POSTGRES_PASSWORD=password
  #   ports:
  #     - "5432:5432"
    volumes:
      # DBのデータをDockerボリュームに保存 (コンテナを消してもデータは残る)
      - postgres_data:/var/lib/postgresql/data
    restart: always

# データの永続化領域定義
volumes:
  postgres_data:
````

## File: Dockerfile
````dockerfile
# ベースイメージ: Python 3.12 (軽量版)
FROM python:3.12-slim

# 1. OSレベルの依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-jpn \
    libtesseract-dev \
    poppler-utils \
    libgl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. 作業ディレクトリの設定
WORKDIR /app

# 3. 依存関係ファイルのコピーとインストール
# エラー回避のため、設定ファイル(pyproject.toml)と説明書(README.md)を先にコピーします
COPY requirements.lock pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.lock

# 4. ソースコード全体をコピー
COPY . .

# 5. 環境変数の設定 (Streamlit用)
ENV PYTHONUNBUFFERED=1

# 6. アプリケーションの起動コマンド
CMD ["python", "src/legal_system/main.py"]
````

## File: export_code.py
````python
import subprocess


def run_repomix():
    print("🚀 ソースコードの集約を開始します...")

    # Repomixを実行するコマンド
    # --style markdown : Geminiが読みやすいマークダウン形式で出力
    # --ignore "**/*.json,**/*.lock" : 不要なファイルを除外（必要に応じて追加）
    command = "npx -y repomix --style markdown"

    try:
        # コマンドを実行
        # shell=True はWindows/Mac両対応のため
        subprocess.run(command, shell=True, check=True)

        print("\n✅ 完了しました！")
        print("📁 'repomix-output.md' というファイルが作成されています。")
        print("🤖 これをGeminiにアップロードしてください。")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    run_repomix()
````

## File: README.md
````markdown
# legal-rag-project

Describe your project here.
````

## File: register_existing_templates.py
````python
import hashlib
import os
import sys

# パス解決
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager


def calculate_file_hash(file_path: str) -> str:
    """ファイルのMD5ハッシュを計算"""
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    return hashlib.md5(file_bytes).hexdigest()


def main():
    print("🚀 既存テンプレートのDB登録を開始します...")

    # パス設定
    base_dir = os.getcwd()
    template_dir = os.path.join(base_dir, "data", "templates")

    if not os.path.exists(template_dir):
        print(f"❌ フォルダが見つかりません: {template_dir}")
        return

    # DB接続
    db = DatabaseManager()

    # 登録処理
    files = [f for f in os.listdir(template_dir) if f.lower().endswith(".pdf")]
    count = 0

    print(f"📂 対象フォルダ: {template_dir}")
    print(f"📄 PDFファイル数: {len(files)}")

    for filename in files:
        file_path = os.path.join(template_dir, filename)
        file_hash = calculate_file_hash(file_path)

        # 既に登録済みかチェック
        if db.is_file_registered(file_hash):
            print(f"SKIP (登録済): {filename}")
            continue

        # 簡易的な種別判定 (ファイル名から推測)
        doc_type = "その他"
        if "残高証明" in filename:
            doc_type = "残高証明"
        elif "相続届" in filename or "手続" in filename:
            doc_type = "相続届"
        elif "委任状" in filename:
            doc_type = "委任状"

        # DBへ登録
        db.register_file_hash(file_hash=file_hash, filename=filename, doc_type=doc_type)
        print(f"✅ REGISTERED: {filename} ({doc_type})")
        count += 1

    print("------------------------------------------------")
    print(f"🎉 完了しました。新規登録: {count} 件")
    print("画面をリロードして確認してください。")


if __name__ == "__main__":
    main()
````

## File: requirements.txt
````
# 📂 遺言・遺産整理業務支援システム 要件定義書 (Ver 1.0)

## 1. プロジェクト概要
* **目的:** 遺言書作成および遺産整理業務の効率化。
* **コアコンセプト:** 「個人情報の完全オフライン管理」と「生成AIによる業務支援」のハイブリッド構成。
* **利用規模:** 本社20名で開始、将来的には全拠点100名以上（年間1000件規模）。

## 2. 技術スタック選定
以下のライブラリ・ツールを標準とする。

| カテゴリ | 技術名 | 選定理由 |
| :--- | :--- | :--- |
| **言語** | **Python 3.10+** | AI/データ処理のエコシステムが最強であるため。 |
| **アプリFW** | **Streamlit** | 社内Webアプリ化が高速。各PCへのインストール不要。 |
| **DB** | **PostgreSQL** | 100人規模の同時接続・排他制御に耐える堅牢性（無料）。 |
| **ORM** | **SQLAlchemy** | DB操作の抽象化。保守性向上のため必須。 |
| **OCR** | **PaddleOCR** | 金融機関書類（日本語・罫線あり）の認識精度が高いため。 |
| **生成AI** | **Google Gemini API** | マニュアル検索、文書案作成用。(google-generativeai) |
| **PDF処理** | **PyMuPDF (fitz)** | PDFの読み込み、加工用。 |

## 3. システムアーキテクチャ
物理的なデータ保管場所と、外部AIへのデータフローを厳密に分離する。

* **サーバー構成:** オンプレミス（社内）サーバー1台にDockerコンテナ等でDBとアプリをホスト。
* **クライアント:** 社員PCのブラウザからイントラネット経由でアクセス。
* **ネットワーク分離:**
    * **Zone A (Secure/Local):** PostgreSQL, OCR処理, 個人情報（氏名, 口座番号）の保存。インターネットへは出さない。
    * **Zone B (Cloud/AI):** Gemini API。ここには「匿名化されたテキスト」と「マニュアル」のみ送信する。

## 4. 機能要件

### A. 顧客・案件管理機能
* 顧客情報（被相続人、相続人）のCRUD処理。
* PostgreSQLを使用し、排他制御を行う。

### B. 帳票OCR取り込み機能
* Streamlit画面から画像/PDFをアップロード。
* PaddleOCRでテキスト化。
* OCR結果と元画像を並べて表示し、人間が修正してDB保存するUI。

### C. 生成AI支援機能（RAG/Drafting）
* **マスキング処理:** 相談内容をGeminiに投げる前に、正規表現等で個人情報（氏名、住所、電話番号、口座番号）をプレースホルダ（例: `[NAME_A]`, `[BANK_ID]`）に置換するロジックを実装すること。
* **マニュアル検索:** 社内規定や金融機関手続きマニュアルをベクトル化、またはコンテキストとして渡し、質問に回答させる。

### D. バックアップ機能
* `pg_dump` を使用し、毎日深夜にDBのダンプファイルを作成。
* 外部ストレージ（NAS等）への転送スクリプト。

## 5. データベース設計指針（ER図イメージ）
* **usersテーブル:** 社員アカウント管理（権限管理用）。
* **customersテーブル:** 顧客基本情報。
* **mattersテーブル:** 案件情報（遺言作成、遺産整理など）。
* **documentsテーブル:** OCR読み取り結果、生成された文書データ。ファイルパス管理。

## 6. セキュリティ・コンプライアンス規定
* **原則:** 顧客のPII（個人特定情報）は、いかなる場合もGemini APIのエンドポイントへ送信してはならない。
* **API設定:** Gemini API利用時は、学習データとして利用されない設定（Enterprise利用またはオプトアウト設定）を確認する。
````

## File: reset_db.py
````python
# file: reset_db.py
import os
import sys

from sqlalchemy import text

# パスを通す
sys.path.append(os.path.join(os.getcwd(), "src"))

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Base


def reset_database():
    print("🔄 データベースの完全リセットを開始します...")

    db = DatabaseManager()
    engine = db.engine

    # 1. スキーマごと強制削除 (DROP SCHEMA public CASCADE)
    # これにより、テーブル間の依存関係を無視して全てを消し去ります。
    print("💣 既存のスキーマ(public)を破棄中...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()

    # 2. テーブルを再作成
    # 最新の tables.py の定義に基づいて作成されます
    print("🔨 テーブルを再作成中...")
    Base.metadata.create_all(engine)

    print("✅ 完了しました！")
    print(
        "   PostgreSQLは完全に初期化され、最新の定義(client_name含む)と一致しました。"
    )


if __name__ == "__main__":
    print("⚠️ 【警告】PostgreSQLの全データを物理的に破壊・初期化します。")
    check = input("実行してよろしいですか？ (y/n): ")
    if check.lower() == "y":
        try:
            reset_database()
        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")
            print("Dockerが起動しているか、.envの設定が正しいか確認してください。")
    else:
        print("中止しました。")
````

## File: src/__init__.py
````python

````

## File: src/chains/bank_procedure_chain.py
````python
# src/chains/bank_procedure_chain.py

import logging
from typing import Any, Dict, Optional

import pandas as pd
from langchain_community.document_loaders import TextLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.ai_factory import AIFactory

logger = logging.getLogger(__name__)


class BankMasterRetriever:
    """
    銀行マスタCSVから特定の銀行情報を検索するクラス
    """

    def __init__(self, csv_path: str):
        try:
            # CSV読み込み。文字化け防止のためencoding指定推奨（状況に合わせて cp932 or utf-8）
            self.df = pd.read_csv(csv_path, encoding="utf-8")
            # 銀行名の揺らぎ吸収のため空白除去
            self.df["銀行名"] = self.df["銀行名"].astype(str).str.strip()
        except FileNotFoundError:
            logger.error(f"銀行マスタファイルが見つかりません: {csv_path}")
            # エラー時も動作するように空のDataFrameを作成
            self.df = pd.DataFrame(
                columns=[
                    "銀行名",
                    "印鑑証明期限",
                    "代理人本人確認書類",
                    "振込ルール",
                    "備考",
                ]
            )
        except Exception as e:
            logger.error(f"CSV読み込みエラー: {e}")
            self.df = pd.DataFrame()

    def get_bank_info(self, query: str) -> Optional[Dict[str, Any]]:
        """
        ユーザーの質問文から対象銀行を特定し、マスタ情報を辞書形式で返す
        """
        if not query or self.df.empty:
            return None

        # 単純なキーワードマッチング（実務ではより高度なEntity抽出も検討可）
        for bank_name in self.df["銀行名"]:
            if bank_name in query:
                try:
                    row = self.df[self.df["銀行名"] == bank_name].iloc[0]
                    return row.fillna("特になし").to_dict()
                except IndexError:
                    continue
        return None


def create_inheritance_chain(
    rules_path: str = "data/company_rules.txt",  # パスは環境に合わせて調整してください
    master_path: str = "data/bank_master.csv",
):
    """
    相続手続きRAGチェーンを作成して返す関数
    """

    # 1. 共通ルールの読み込み
    try:
        loader = TextLoader(rules_path, encoding="utf-8")
        docs = loader.load()
        general_rules = "\n".join([d.page_content for d in docs])
    except Exception as e:
        logger.warning(f"共通ルールファイル読み込み失敗: {e}")
        general_rules = "（共通ルール読み込みエラー）"

    # 2. マスタ検索インスタンス
    master_retriever = BankMasterRetriever(master_path)

    # 3. LLMの初期化 (Factory経由でキーローテーション)
    llm = AIFactory.create_model(temperature=0.0)

    # 4. プロンプト定義
    # ここで「ゆうちょ」等の他行ルールを除外する強い指示を与えます
    template_str = """
    あなたは行政書士法人の実務支援AIです。
    ユーザーの質問に対し、以下の情報源を組み合わせて回答を作成してください。

    【情報源の優先順位】
    1. **対象銀行マスタ情報 (最優先)**: 期限や支払方法は必ずこれに従うこと。
    2. **共通業務ルール**: マスタに記載がない事項について参照すること。

    【対象銀行マスタ情報】
    {specific_rules}

    【共通業務ルール（参考）】
    {general_rules}

    【回答作成の厳格なルール】
    1. **対象銀行の特定**: 今回の手続き対象は「{target_bank_name}」です。
    2. **情報の除外**: 共通ルール内に含まれる**「{target_bank_name}」以外の銀行（特にゆうちょ銀行など）に関する記述は完全に無視**してください。
       - 例: 対象が「みずほ銀行」の場合、ゆうちょ銀行の「スプレッドシート」や「会社通帳からの引落とし」の記述は絶対に回答に含めないでください。
    3. **支払方法**: マスタ情報の「振込/引落」に従ってください。
       - 「振込」の場合 → 「経理へ依頼（Kintone経理アプリ）」と案内。
       - 「引落」の場合 → 指定された管理シート等を案内。
    4. **証明書の期限**: マスタ情報の「印鑑証明期限」を正として回答してください（共通ルールの6ヶ月という記述で上書きしないこと）。

    【出力フォーマット】
    - 結論のみを箇条書きで記載。
    - 挨拶や前置きは不要。
    
    質問: {question}
    """

    prompt = ChatPromptTemplate.from_template(template_str)

    # 5. チェーン実行用関数
    def run_chain(inputs: Dict[str, Any]) -> str:
        question = inputs.get("question", "")

        # 銀行情報の取得
        bank_info = master_retriever.get_bank_info(question)

        if bank_info:
            target_bank_name = bank_info.get("銀行名", "指定なし")
            # マスタ情報を文字列化してプロンプトに埋め込む
            specific_rules_str = (
                f"- 銀行名: {target_bank_name}\n"
                f"- 印鑑証明期限: {bank_info.get('印鑑証明期限', '規定なし')}\n"
                f"- 本人確認書類: {bank_info.get('代理人本人確認書類', '規定なし')}\n"
                f"- 支払方法(振込/引落): {bank_info.get('振込ルール', '規定なし')}\n"
                f"- 備考: {bank_info.get('備考', '')}"
            )
        else:
            target_bank_name = "特定できない銀行"
            specific_rules_str = (
                "（マスタに該当する銀行が見つかりません。共通ルールのみを参照します）"
            )

        # チェーン構築
        chain = prompt | llm | StrOutputParser()

        try:
            return chain.invoke(
                {
                    "general_rules": general_rules,
                    "specific_rules": specific_rules_str,
                    "target_bank_name": target_bank_name,
                    "question": question,
                }
            )
        except Exception as e:
            logger.error(f"チェーン実行エラー: {e}")
            return "システムエラーが発生しました。"

    return run_chain
````

## File: src/legal_system/__init__.py
````python

````

## File: src/legal_system/core/__init__.py
````python

````

## File: src/legal_system/core/engines.py
````python
# src/legal_system/core/engines.py

import gzip
import os
import time
from typing import Optional

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Google Gemini / LangChain 関連
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter

# 設定読み込み
from src.legal_system.core.config import Config, KeyManager


class BankRepository:
    """
    銀行マスタCSVの読み込みと検索を担当
    """

    def __init__(self, csv_path: str):
        # CSV読み込み時も圧縮やエンコーディングの問題を回避するロジックを使用
        self.df = self._load_csv_safe(csv_path)

    def _load_csv_safe(self, path: str) -> pd.DataFrame:
        """CSVファイルを安全に読み込む（GZIP対応 / エンコーディング自動判別）"""
        if not os.path.exists(path):
            return pd.DataFrame()

        try:
            # GZIP判定
            is_gzipped = False
            with open(path, "rb") as f:
                header = f.read(2)
                if header == b"\x1f\x8b":
                    is_gzipped = True

            # Pandasで読み込み
            if is_gzipped:
                try:
                    return pd.read_csv(
                        path, compression="gzip", encoding="utf-8"
                    ).fillna("")
                except UnicodeDecodeError:
                    return pd.read_csv(
                        path, compression="gzip", encoding="cp932"
                    ).fillna("")
            else:
                try:
                    return pd.read_csv(path, encoding="utf-8").fillna("")
                except UnicodeDecodeError:
                    return pd.read_csv(path, encoding="cp932").fillna("")

        except Exception as e:
            print(f"CSV読み込み警告: {e}")
            return pd.DataFrame()  # エラー時は空のDFを返す

    def search(self, query: str) -> Optional[dict]:
        """クエリ内の銀行名を特定し、行データを辞書として返す"""
        if self.df.empty:
            return None

        for _, row in self.df.iterrows():
            bank_name = str(row.get("銀行名", ""))
            if bank_name and bank_name in query:
                return row.to_dict()
        return None

    def format_rule(self, row: dict) -> str:
        """LLMへの注入用にフォーマット"""
        return f"""
        【特定された銀行の必須ルール (最優先適用)】
        - 銀行名: {row.get("銀行名")}
        - 印鑑証明期限: {row.get("印鑑証明期限")}
        - 代理人本人確認: {row.get("代理人本人確認書類")}
        - 手数料支払: {row.get("振込ルール")}
        - 備考: {row.get("備考")}
        """


class RAGEngine:
    """
    Google Gemini + キーローテーション対応エンジン
    ファイルのGZIP圧縮/文字コードズレを自動吸収する機能付き
    """

    def __init__(self, rules_path: str, bank_repo: BankRepository):
        self.bank_repo = bank_repo
        self.rules_path = rules_path
        self.vector_store = None  # 遅延初期化
        self.embeddings = None
        self.llm = None

        # 初回のクライアント構築
        self._refresh_client()

    def _refresh_client(self):
        """APIキーを取得してクライアントを再生成"""
        try:
            new_key = KeyManager.get_next_key()

            # Embeddingsモデル更新
            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=Config.EMBEDDING_MODEL, google_api_key=new_key
            )

            # LLMモデル更新
            self.llm = ChatGoogleGenerativeAI(
                model=Config.MODEL_NAME,
                temperature=Config.TEMPERATURE,
                google_api_key=new_key,
                convert_system_message_to_human=True,
            )

            # ベクトルストア構築（または更新）
            if self.vector_store is None:
                self.vector_store = self._build_vector_store(self.rules_path)
            else:
                self.vector_store.embeddings = self.embeddings

        except Exception as e:
            print(f"クライアント初期化エラー: {e}")
            # エラー発生時もNoneのままにしておき、ask時に再トライさせるかエラーを返す

    def _read_file_safe(self, path: str) -> str:
        """
        ファイルを安全に読み込むヘルパー関数
        - GZIP圧縮されていれば自動解凍
        - UTF-8 で失敗したら CP932 (Shift-JIS) を試行
        """
        if not os.path.exists(path):
            return ""

        content_bytes = b""

        # 1. バイナリとして読み込み、GZIPヘッダー(1f 8b)をチェック
        with open(path, "rb") as f:
            raw_data = f.read()
            if raw_data.startswith(b"\x1f\x8b"):
                # GZIP解凍
                content_bytes = gzip.decompress(raw_data)
            else:
                content_bytes = raw_data

        # 2. 文字コード判別 (utf-8 -> cp932)
        try:
            return content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                return content_bytes.decode("cp932")
            except UnicodeDecodeError:
                # それでもだめならエラー無視で強引に読む
                return content_bytes.decode("utf-8", errors="ignore")

    def _build_vector_store(self, path: str) -> FAISS:
        """ベクトルストア構築"""
        # 安全な読み込み関数を使用
        text = self._read_file_safe(path)

        if not text:
            # ファイルが空、または読めない場合はダミーデータで落ちないようにする
            text = "共通ルールファイルが読み込めませんでした。"

        headers = [("#", "h1"), ("##", "h2"), ("###", "h3")]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers)
        docs = splitter.split_text(text)

        if not docs:
            # 分割結果が空の場合のガード
            from langchain_core.documents import Document

            docs = [Document(page_content="ルール情報なし")]

        return FAISS.from_documents(docs, self.embeddings)

    def ask(self, user_query: str, retry_count=0) -> str:
        """質問への回答（自動リトライ機能付き）"""
        if not self.llm:
            return "AIエンジンの初期化に失敗しています。APIキー設定を確認してください。"

        try:
            return self._execute_chain(user_query)
        except Exception as e:
            error_msg = str(e)
            # 429 (Resource Exhausted) などのエラー判定
            if "429" in error_msg or "Resource has been exhausted" in error_msg:
                if retry_count < 3:
                    print(
                        f"⚠️ API制限検知。キーを切り替えてリトライします... ({retry_count + 1}/3)"
                    )
                    self._refresh_client()
                    time.sleep(1)
                    return self.ask(user_query, retry_count + 1)

            return f"エラーが発生しました: {error_msg}"

    def _execute_chain(self, user_query: str) -> str:
        """実際のChain実行処理"""
        # STEP 1: CSV検索
        bank_data = self.bank_repo.search(user_query)
        bank_context = ""
        if bank_data:
            bank_context = self.bank_repo.format_rule(bank_data)

        # STEP 2: ベクトル検索
        enhanced_query = f"{user_query} 代理人 行政書士 手続き"
        docs = self.vector_store.similarity_search(enhanced_query, k=4)
        rule_context = "\n\n".join([d.page_content for d in docs])

        # STEP 3: プロンプト構築
        system_prompt = """
        あなたは行政書士法人の実務支援AIです。
        
        # 行動指針
        1. **結論ファースト**: 挨拶不要。箇条書きで簡潔に答える。
        2. **代理人視点**: 「行政書士（代理人）」の手続きのみ回答する。
        3. **優先順位**: 【銀行別ルール】を最優先する。
        4. **リンク表示**: ゆうちょ銀行や参照ファイルの指示がある場合はURLを表示する。
        
        # 参照情報
        ## 共通業務ルール
        {rule_context}
        
        ## 銀行別ルール (Override)
        {bank_context}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", "{question}")]
        )

        chain = prompt | self.llm | StrOutputParser()
        return chain.invoke(
            {
                "rule_context": rule_context,
                "bank_context": bank_context,
                "question": user_query,
            }
        )
````

## File: src/legal_system/core/pdf_processor.py
````python
# src/legal_system/core/pdf_processor.py

import re
import logging
import fitz  # PyMuPDF
import unicodedata
import numpy as np
from typing import Dict, Any, Tuple, List

from src.legal_system.core.ocr_engine import OCREngine

logger = logging.getLogger(__name__)

class ReferralSheetParser:
    """
    紹介連絡表（フォーマット固定）の解析クラス。
    テキスト抽出を試み、値が取れなければOCRへフォールバックするロジックを搭載。
    """

    def __init__(self):
        self.ocr_engine = OCREngine()

    def parse_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """
        PDFバイナリを受け取り、解析結果の辞書を返すメインメソッド。
        """
        # Step 1: まず高速なテキスト抽出(PyMuPDF)を試す
        raw_text_1 = self._extract_text_only(file_bytes)
        parsed_data_1 = self._process_text_to_data(raw_text_1)
        
        # Step 2: 判定ロジック
        # 顧客名などの主要項目が空の場合、テキスト抽出では「枠線（ラベル）」しか取れていないと判断し、
        # 強制的にOCR(画像解析)を実行する。
        if not parsed_data_1.get("client_name"):
            logger.info("テキスト抽出で値が取得できないため、OCR(画像解析)を実行します。")
            ocr_text = self._perform_ocr(file_bytes)
            
            # OCR結果で再パース
            parsed_data_2 = self._process_text_to_data(ocr_text)
            parsed_data_2["_debug_mode"] = "OCR_FALLBACK (Auto)"
            parsed_data_2["_debug_raw_text"] = ocr_text
            return parsed_data_2
        
        # テキスト抽出で成功していればそれを返す
        parsed_data_1["_debug_mode"] = "TEXT_LAYER (High Speed)"
        parsed_data_1["_debug_raw_text"] = raw_text_1
        return parsed_data_1

    def _process_text_to_data(self, raw_text: str) -> Dict[str, Any]:
        """テキスト正規化と正規表現抽出の共通処理"""
        # 正規化 (NFKC)
        norm_text = unicodedata.normalize("NFKC", raw_text)
        # 抽出実行
        return self._extract_fields_via_regex(norm_text)

    def _extract_text_only(self, file_bytes: bytes) -> str:
        """PyMuPDFによるテキスト抽出のみ"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text

    def _perform_ocr(self, file_bytes: bytes) -> str:
        """PyMuPDFで画像化 -> PaddleOCRで解析"""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        full_ocr_text = []
        import cv2

        for page in doc:
            # 精度向上のためzoom=2.0で画像化
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            img_array = np.frombuffer(pix.samples, dtype=np.uint8)
            
            # PaddleOCR用にBGR変換
            if pix.n == 4:
                img = img_array.reshape(pix.height, pix.width, 4)
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:
                img = img_array.reshape(pix.height, pix.width, 3)
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            else:
                img = img_array.reshape(pix.height, pix.width, pix.n)

            result = self.ocr_engine.ocr.ocr(img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    full_ocr_text.append(line[1][0])
        
        doc.close()
        # OCR結果は行ごとに分かれているため改行で結合
        return "\n".join(full_ocr_text)

    def _clean_name_spacing(self, text: str) -> str:
        """氏名のスペース整理"""
        if not text: return ""
        text = text.strip()
        text = re.sub(r"[\s　]{2,}", "###", text)
        text = re.sub(r"[\s　]", "", text)
        return text.replace("###", " ")

    def _extract_fields_via_regex(self, text: str) -> Dict[str, Any]:
        """正規表現による項目抽出"""
        data = {}
        
        # 被相続人情報の除外ロジック
        ignore_keywords = ["被相続人", "死亡日", "相続開始", "遺言信託"]
        target_text = text
        
        # 最も上にあるキーワードでカットする
        min_idx = len(text)
        cut_flag = False
        for kw in ignore_keywords:
            idx = text.find(kw)
            if idx != -1 and idx < min_idx:
                min_idx = idx
                cut_flag = True
        
        if cut_flag:
            target_text = text[:min_idx]

        # パターン定義
        patterns = {
            "client_name": r"顧客名(?:\([^)]*\))?[\s:：]*([^\n]+)",
            "client_name_kana": r"フリガナ(?:\([^)]*\))?[\s:：]*([^\n]+)",
            "referral_sec_branch_name": r"(?:支店|部店)名[\s:：]*([^\n]+)",
            "referral_sec_rep_name": r"担当(?:部店)?者名?[\s:：]*([^\n]+)",
            "sol_case_number": r"SOL案件No\.?[\s:：]*([A-Z0-9-]+)",
            "introduction_date": r"紹介日[\s:：]*(\d{4}[\s年/-]\d{1,2}[\s月/-]\d{1,2})",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, target_text)
            if match:
                val = match.group(1).strip()
                # ラベル自体を誤って拾ってしまうケースの除外 ("顧客名" という値が入っていたら空にする)
                if val in ["顧客名", "フリガナ", "住所", "支店名", "担当者名"]:
                    data[key] = ""
                else:
                    data[key] = self._clean_name_spacing(val) if "name" in key else val
            else:
                data[key] = ""

        # 電話番号の抽出
        phones = re.findall(r"[\d-]{10,13}", target_text)
        unique_phones = list(dict.fromkeys(phones))
        data["client_phone_1"] = unique_phones[0] if len(unique_phones) > 0 else ""
        data["client_phone_2"] = unique_phones[1] if len(unique_phones) > 1 else ""

        # 住所抽出
        addr_match = re.search(r"住所[\s:：]*([\s\S]+?)(?:\n\s*(?:ニーズ|電話|TEL|氏名|フリガナ)|$)", target_text)
        if addr_match:
            data["client_address"] = addr_match.group(1).replace("\n", "").strip()
        else:
            data["client_address"] = ""

        return data

def analyze_referral_pdf(file_bytes: bytes) -> Dict[str, Any]:
    return ReferralSheetParser().parse_pdf(file_bytes)
````

## File: src/legal_system/core/preload.py
````python
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
````

## File: src/legal_system/models/__init__.py
````python

````

## File: src/legal_system/models/base.py
````python

````

## File: src/legal_system/tools/__init__.py
````python
def hello() -> str:
    return "Hello from legal-rag-system!"
````

## File: src/legal_system/tools/coord_tool.py
````python
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
````

## File: src/legal_system/ui/__init__.py
````python

````

## File: src/legal_system/ui/components/admin_tools.py
````python
# src/legal_system/ui/components/admin_tools.py

import hashlib
import json
import os
import random
import re
import time
from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# パス解決 (プロジェクト構成に合わせて調整)
ROOT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)

from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ocr_engine import extract_text_from_scanned_pdf

# PDFプレビュー用
try:
    from pdf2image import convert_from_bytes
except ImportError:
    convert_from_bytes = None


# ---------------------------------------------------------
# ヘルパー関数群
# ---------------------------------------------------------
def calculate_file_hash(file_bytes: bytes) -> str:
    """ファイルの重複登録を防ぐためのハッシュ計算"""
    return hashlib.md5(file_bytes).hexdigest()


def extract_text_safe(file_bytes: bytes) -> str:
    """PDFからテキストを抽出。テキスト情報がない場合はOCRエンジンを使用"""
    text = ""
    try:
        pdf = PdfReader(BytesIO(file_bytes))
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t
    except:
        pass
    # テキストが極端に少ない場合はスキャンデータとみなしてOCRを実行
    if len(text.strip()) < 50:
        text = extract_text_from_scanned_pdf(file_bytes)
    return text


def _rule_based_classify(text_content: str) -> dict:
    """
    【高速化・コスト削減】
    AIに投げる前に、強力なルールベースで分類を試みる。
    戻り値: {"filename": ..., "bank_name": ..., "doc_type": ...} または None
    """
    if not text_content:
        return None

    # 正規化（改行・空白削除）
    normalized_text = text_content.replace("\n", "").replace(" ", "").replace("　", "")

    # 1. 銀行名の特定（マスタ等からキーワード拡張可能）
    bank_name = "その他"
    known_banks = ["三菱UFJ", "三井住友", "みずほ", "ゆうちょ", "りそな", "横浜銀行"]
    for bank in known_banks:
        if bank in normalized_text:
            bank_name = f"{bank}銀行" if "銀行" not in bank else bank
            break

    # 2. 書類種別の特定
    doc_type = "その他"
    if "残高証明書" in normalized_text:
        doc_type = "残高証明"
    elif "取引推移" in normalized_text or "入出金明細" in normalized_text:
        doc_type = "取引明細"
    elif "相続届" in normalized_text or "相続手続請求書" in normalized_text:
        doc_type = "相続届"
    elif "委任状" in normalized_text:
        doc_type = "委任状"
    elif "手引" in normalized_text or "ご案内" in normalized_text:
        doc_type = "手引き"

    # 銀行と種別の両方が「その他」でなければ、一定の信頼度で採用
    if bank_name != "その他" or doc_type != "その他":
        filename = f"{bank_name}_{doc_type}"
        return {"filename": filename, "bank_name": bank_name, "doc_type": doc_type}

    return None


def analyze_document_info(text_content: str, llm):
    """
    文書の種類や銀行名を推定するハイブリッドロジック
    Priority 1: ルールベース判定 (高速・無料)
    Priority 2: AI判定 (低速・高コスト・高精度)
    """
    if not text_content:
        return {"filename": "", "bank_name": "", "doc_type": ""}

    # Priority 1: ルールベース
    rule_result = _rule_based_classify(text_content)
    if rule_result:
        # ルールベースで判定できた場合、ここで終了
        return rule_result

    # Priority 2: AI判定
    prompt = """
    以下のドキュメント冒頭を読み、3つの情報をJSON形式で出力してください。
    1. filename: {金融機関名}_{書類名}
    2. bank_name: 金融機関名 (特定できなければ"その他")
    3. doc_type: "手引き", "残高証明", "相続届", "委任状", "その他" から選択
    
    【ドキュメント冒頭】
    """ + text_content[:1500]

    try:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass

    return {"filename": "解析失敗", "bank_name": "その他", "doc_type": "その他"}


def js_scroll_to_bottom():
    js = """<script>
        var mainParams = window.parent.document.querySelector('section.main');
        if (mainParams) { mainParams.scrollTo({ top: mainParams.scrollHeight, behavior: 'smooth' }); }
    </script>"""
    st.components.v1.html(js, height=0)


# ---------------------------------------------------------
# メイン機能: アップロードタブの描画
# ---------------------------------------------------------
def render_upload_tab(db_manager: DatabaseManager):
    st.subheader("📂 雛形・記入例の登録 (OCR)")
    st.caption("PDFを解析し、RAGデータベースとファイルサーバーに登録します。")

    s_norm, s_sec = st.tabs(["🟦 一般雛形", "🟥 記入例 (機密)"])

    # ==========================================
    # 1. 一般用タブ (クラウドAI使用)
    # ==========================================
    with s_norm:
        st.info("個人情報を含まない手引き等")

        # 案件紐付け
        session = db_manager._get_session()
        target_case_id = None
        try:
            from legal_system.models.tables import Case

            cases = session.query(Case).all()
            case_opts = {"（全案件共通の雛形として登録）": None}
            for c in cases:
                case_opts[f"{c.case_number}: {c.client_name}"] = c.case_id
            selected = st.selectbox(
                "紐付ける案件 (任意)", list(case_opts.keys()), key="up_case_sel"
            )
            target_case_id = case_opts[selected]
        finally:
            session.close()

        files_n = st.file_uploader(
            "PDFアップロード (一般)", accept_multiple_files=True, key="up_n"
        )

        if files_n:
            if st.button("🔍 クラウド解析", key="btn_n"):
                # ステータスコンテナで進捗を表示
                with st.status(
                    "🚀 ハイブリッド解析中 (ルールベース + AI)...", expanded=True
                ) as status:
                    st.session_state.upload_stage = []

                    st.write("🧠 AIモデルを初期化中...")
                    try:
                        llm_cloud = AIFactory.get_llm("cloud")
                    except Exception as e:
                        status.update(label="❌ エラー発生", state="error")
                        st.error(f"AIモデルの準備に失敗しました: {e}")
                        st.stop()

                    total_files = len(files_n)
                    progress_bar = st.progress(0)

                    for i, f in enumerate(files_n):
                        st.write(f"📄 読込中 ({i + 1}/{total_files}): {f.name}")
                        fb = f.read()

                        # ハッシュチェック
                        f_hash = calculate_file_hash(fb)
                        if db_manager.is_file_registered(f_hash):
                            st.warning(
                                f"⚠️ {f.name} は既に登録されています。スキップします。"
                            )
                            time.sleep(0.5)
                            continue

                        # 解析処理
                        text = extract_text_safe(fb)
                        if not text:
                            st.warning(
                                f"⚠️ {f.name} からテキストを抽出できませんでした。"
                            )

                        # ハイブリッド判定 (ルール -> AI)
                        meta = analyze_document_info(text, llm_cloud)
                        st.write(
                            f"   ↳ 判定: {meta.get('doc_type', '不明')} / {meta.get('bank_name', '不明')}"
                        )

                        st.session_state.upload_stage.append(
                            {
                                "old": f.name,
                                "new": meta.get("filename", f.name),
                                "bank_name": meta.get("bank_name", "その他"),
                                "doc_type": meta.get("doc_type", "その他"),
                                "data": fb,
                                "text": text,
                                "type": "general",
                                "hash": f_hash,
                                "case_id": target_case_id,
                            }
                        )
                        # プログレスバー更新
                        progress_bar.progress((i + 1) / total_files)

                    # 完了時はexpanded=Trueのままにして、rerunしない（結果を表示し続ける）
                    status.update(
                        label="✅ 解析完了！内容を確認して、下の「登録実行」を押してください。",
                        state="complete",
                        expanded=True,
                    )
                # ここで st.rerun() はしない

    # ==========================================
    # 2. 機密用タブ (ローカルAI使用)
    # ==========================================
    with s_sec:
        st.warning("個人情報を含む書類 (ローカル処理)")
        # 案件紐付け
        session = db_manager._get_session()
        target_case_id_sec = None
        try:
            from legal_system.models.tables import Case

            cases = session.query(Case).all()
            case_opts_s = {"（全案件共通の雛形として登録）": None}
            for c in cases:
                case_opts_s[f"{c.case_number}: {c.client_name}"] = c.case_id
            selected_s = st.selectbox(
                "紐付ける案件 (任意)", list(case_opts_s.keys()), key="up_case_sel_sec"
            )
            target_case_id_sec = case_opts_s[selected_s]
        finally:
            session.close()

        file_s = st.file_uploader(
            "PDFアップロード (機密)", accept_multiple_files=False, key="up_s"
        )

        if file_s:
            fb_s = file_s.read()
            f_hash = calculate_file_hash(fb_s)

            if db_manager.is_file_registered(f_hash):
                st.error(f"⛔ {file_s.name} は既に登録済みです。")
            else:
                if convert_from_bytes:
                    try:
                        images = convert_from_bytes(fb_s, first_page=1, last_page=1)
                        if images:
                            st.image(images[0], width=400)
                    except:
                        pass

                if st.checkbox(
                    "機密書類であることを確認しました", key="check_s"
                ) and st.button("🔒 ローカル解析", key="btn_s"):
                    with st.status(
                        "🔒 ローカルAI (Ollama) で解析中...", expanded=True
                    ) as status:
                        st.session_state.upload_stage = []

                        st.write("🧠 ローカルモデル(Llama)をロード中...")
                        try:
                            llm_local = AIFactory.get_llm("local")
                        except Exception as e:
                            status.update(label="❌ エラー発生", state="error")
                            st.error(f"ローカルモデルの起動に失敗: {e}")
                            st.stop()

                        st.write("📄 テキスト抽出中...")
                        text_s = extract_text_safe(fb_s)

                        st.write("🔍 文書解析中 (ルールベース + Llama)...")
                        meta = analyze_document_info(text_s, llm_local)
                        if "記入例" not in meta["filename"]:
                            meta["filename"] += "_記入例"

                        st.session_state.upload_stage.append(
                            {
                                "old": file_s.name,
                                "new": meta.get("filename", file_s.name),
                                "bank_name": meta.get("bank_name", "その他"),
                                "doc_type": meta.get("doc_type", "その他"),
                                "data": fb_s,
                                "text": text_s,
                                "type": "secure",
                                "hash": f_hash,
                                "case_id": target_case_id_sec,
                            }
                        )
                        status.update(
                            label="✅ 解析完了！下の「登録実行」へ進んでください。",
                            state="complete",
                            expanded=True,
                        )
                # ここで st.rerun() はしない

    # ==========================================
    # 3. 保存確認フォーム (解析結果がある場合のみ表示)
    # ==========================================
    if st.session_state.get("upload_stage"):
        st.divider()
        st.subheader("💾 登録確認")
        st.info("解析結果を確認し、必要であれば修正してから登録してください。")

        with st.form("save_form"):
            configs = []
            for i, item in enumerate(st.session_state.upload_stage):
                c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
                c1.text(item["old"])
                new_name = c2.text_input("登録名", value=item["new"], key=f"fn_{i}")
                new_bank = c3.text_input(
                    "銀行タグ", value=item["bank_name"], key=f"bk_{i}"
                )

                opts = [
                    "手引き",
                    "残高証明",
                    "取引明細",
                    "顧客勘定元帳",
                    "相続届",
                    "委任状",
                    "その他",
                ]
                curr = item.get("doc_type", "その他")
                idx = opts.index(curr) if curr in opts else 6
                new_type = c4.selectbox("種別", opts, index=idx, key=f"dt_{i}")

                configs.append(
                    {
                        **item,
                        "name": new_name,
                        "bank_name": new_bank,
                        "doc_type": new_type,
                    }
                )

            if st.form_submit_button("✅ 登録実行"):
                _execute_registration(configs, db_manager)


# ---------------------------------------------------------
# 登録実行ロジック (リトライ処理付き)
# ---------------------------------------------------------
def _execute_registration(configs, db_manager):
    vector_store = AIFactory.get_vector_store()
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    cnt = 0
    today = datetime.now().strftime("%Y%m%d")
    templates_dir = os.path.join(ROOT_DIR, "data", "templates")
    os.makedirs(templates_dir, exist_ok=True)

    # 登録時もステータス表示
    with st.status("💾 データベースに登録中...", expanded=True) as status:
        progress_bar = st.progress(0)
        total_configs = len(configs)

        for idx, c in enumerate(configs):
            fname = f"{c['name']}_{today}.pdf"
            st.write(f"📝 登録中 ({idx + 1}/{total_configs}): {fname}")

            save_path = os.path.join(templates_dir, fname)

            # 1. 物理ファイル保存
            with open(save_path, "wb") as f:
                f.write(c["data"])

            # 2. DBへのハッシュ登録
            db_manager.register_file_hash(
                c["hash"], fname, c["doc_type"], case_id=c.get("case_id")
            )

            # 3. Vector Store Registration
            enriched_text = f"【ファイル名】{fname}\n【銀行名】{c['bank_name']}\n【書類種別】{c['doc_type']}\n\n{c['text']}"
            chunks = splitter.split_text(enriched_text)
            metadatas = [
                {
                    "source": fname,
                    "path": save_path,
                    "security_level": c["type"],
                    "bank_name": c["bank_name"],
                    "doc_type": c["doc_type"],
                }
                for _ in chunks
            ]

            # バッチ処理とリトライロジック (API制限対策)
            # 無料枠対策としてバッチサイズを小さく設定
            batch_size = 2
            total_chunks = len(chunks)

            for i in range(0, total_chunks, batch_size):
                batch_chunks = chunks[i : i + batch_size]
                batch_metas = metadatas[i : i + batch_size]

                # 最大5回のリトライロジック (指数バックオフ)
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        vector_store.add_texts(batch_chunks, metadatas=batch_metas)
                        # 成功したら少し待機して次へ (連打防止)
                        time.sleep(1.0)
                        break
                    except Exception as e:
                        error_str = str(e)
                        # 429(Resource Exhausted) または 400(Bad Request: e.g. Key expired) を検知
                        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                            if attempt < max_retries - 1:
                                wait_time = (2**attempt) + random.random() * 2
                                st.warning(
                                    f"⚠️ API制限を検知。{wait_time:.1f}秒待機して再試行します... ({attempt + 1}/{max_retries})"
                                )
                                time.sleep(wait_time)
                            else:
                                st.error(
                                    f"❌ リトライ上限に達しました。登録失敗: {fname}"
                                )
                                raise e
                        else:
                            # その他のエラーは即座に上げる
                            raise e

            cnt += 1
            progress_bar.progress((idx + 1) / total_configs)

        status.update(label="✅ 全件登録完了！", state="complete", expanded=False)

    st.success(f"{cnt}件の学習・登録が完了しました！")
    st.session_state.upload_stage = []
    time.sleep(1.5)
    st.rerun()


# ---------------------------------------------------------
# メイン機能: データ管理タブの描画
# ---------------------------------------------------------
def render_management_tab(db_manager: DatabaseManager):
    st.subheader("🗑️ 登録済みファイルの管理")
    files = db_manager.get_all_files()

    if not files:
        st.info("登録されているファイルはありません。")
    else:
        df_files = pd.DataFrame(files)
        # カラム名のマッピング調整
        df_files.columns = [
            "ファイル名",
            "登録日時",
            "ハッシュ値",
            "書類種別",
            "案件",
            "doc_type_raw",
            "uploaded_at_raw",
        ]
        st.dataframe(
            df_files[["登録日時", "案件", "書類種別", "ファイル名"]],
            use_container_width=True,
        )

        st.divider()
        st.warning("【削除エリア】")
        selected_file = st.selectbox(
            "削除するファイルを選択", [f["filename"] for f in files]
        )

        if st.button("選択したファイルを完全に削除する"):
            templates_dir = os.path.join(ROOT_DIR, "data", "templates")
            target_path = os.path.join(templates_dir, selected_file)

            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except OSError:
                    pass

            db_manager.delete_file_registry(selected_file)
            st.success(f"{selected_file} を削除しました。")
            time.sleep(1)
            st.rerun()
````

## File: src/legal_system/ui/excel_generator.py
````python
# components/utils/excel_generator.py
import openpyxl
from openpyxl.worksheet.worksheet import Worksheet
import io
from typing import Dict, Union, List, Optional
import os

# デフォルトのテンプレートファイルパス（配置場所に合わせて変更してください）
DEFAULT_TEMPLATE_PATH = "■初回送付セット【20251218版】　.xlsx"

def fill_initial_set_excel(
    json_data: Dict[str, str], 
    template_file: Optional[Union[str, io.BytesIO]] = None
) -> io.BytesIO:
    """
    KintoneのJSONデータを基に、初回送付セットExcelの「基本情報入力」シートに値を転記します。

    Args:
        json_data (Dict[str, str]): Kintoneから取得したJSONデータ（辞書型）
        template_file (Optional[Union[str, io.BytesIO]]): テンプレートExcelファイル。
            指定がない場合はデフォルトパスを使用。

    Returns:
        io.BytesIO: 編集後のExcelバイナリデータ（ダウンロード用）
    
    Raises:
        FileNotFoundError: テンプレートファイルが見つからない場合
        KeyError: 指定されたシートが存在しない場合
    """
    
    # テンプレートの読み込み元を決定
    source = template_file if template_file else DEFAULT_TEMPLATE_PATH
    
    if isinstance(source, str) and not os.path.exists(source):
        raise FileNotFoundError(f"テンプレートファイルが見つかりません: {source}")

    # Excelブックを開く
    wb = openpyxl.load_workbook(source)
    
    target_sheet_name = "基本情報入力"
    if target_sheet_name not in wb.sheetnames:
        raise KeyError(f"テンプレート内に '{target_sheet_name}' シートが見つかりません。")
    
    ws: Worksheet = wb[target_sheet_name]

    # マッピング定義
    # JSONのキー : Excelのセル番地（単一文字列 または 文字列のリスト）
    mapping: Dict[str, Union[str, List[str]]] = {
        "顧客コード_2": "B9",
        "顧客名": ["B10", "C24"],  # 複数セルへの転記
        "◎提案項目": "B11",
        "拠点": "B12",
        "担当者①": "B13",
        "担当者②": "D13",
        "被相続人名": "C23",
        "被相続人名（ふりがな）": "D23",
        "相続開始日": "F23",
        "顧客名(ふりがな)": "D24",
        "郵便番号": "G24",
        "住所": "H24",
        "TEL": "J24"
    }

    # データの転記処理
    for json_key, cell_target in mapping.items():
        # JSONから値を取得（キーがない場合は空文字）
        value = json_data.get(json_key, "")
        
        # 転記実行
        if isinstance(cell_target, list):
            for cell_address in cell_target:
                ws[cell_address].value = value
        else:
            ws[cell_target].value = value

    # メモリ上のバイナリとして保存
    output_buffer = io.BytesIO()
    wb.save(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer
````

## File: src/legal.egg-info/dependency_links.txt
````

````

## File: src/legal_system/core/data_sync.py
````python
# file: src/legal_system/core/data_sync.py

import json
import logging
from typing import Any, Dict

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import BankMaster, Case, FinancialAsset

logger = logging.getLogger(__name__)


class DataSyncEngine:
    """
    外部データ（Kintone JSON等）とPostgreSQLの同期を管理するエンジン。
    """

    def __init__(self):
        self.db = DatabaseManager()

    def sync_from_kintone_json(self, json_path: str) -> bool:
        """
        JSONファイルを読み込み、PostgreSQLへUpsert処理を行う。
        """
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"JSON読み込み失敗: {e}")
            return False

        session = self.db._get_session()
        try:
            # 1. 案件 (Case) の同期 - ビジネスID「G番号」をキーにする
            case_num = data.get("顧客コード_2") or data.get("case_number")
            if not case_num:
                logger.warning("案件番号(G番号)がないためスキップします。")
                return False

            case = session.query(Case).filter_by(case_number=case_num).first()
            if not case:
                case = Case(
                    case_number=case_num,
                    client_name=data.get("顧客名", "名称未設定"),
                    created_at=datetime.now(),
                )
                session.add(case)
                session.flush()  # IDを確定させる

            # 2. 資産データ (FinancialAsset) の Upsert
            # 同一案件内の「銀行名・支店名・口座番号」の組み合わせが一致すれば更新する
            assets_list = data.get("assets", [])  # JSON構造に合わせて調整
            for a in assets_list:
                self._upsert_financial_asset(session, case.case_id, a)

            session.commit()
            logger.info(f"✅ 同期完了: {case_num}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"❌ 同期エラー: {e}")
            return False
        finally:
            session.close()

    def _upsert_financial_asset(
        self, session, case_id: int, asset_data: Dict[str, Any]
    ):
        """
        PostgreSQLの機能を活用した資産情報のUpsert処理
        """
        # 銀行・支店IDの解決（簡易化のため名称一致で検索）
        bank = (
            session.query(BankMaster)
            .filter(BankMaster.bank_name == asset_data.get("bank_name"))
            .first()
        )
        if not bank:
            return

        # 既存レコードの確認
        existing_asset = (
            session.query(FinancialAsset)
            .filter(
                FinancialAsset.case_id == case_id,
                FinancialAsset.bank_id == bank.id,
                FinancialAsset.account_number == asset_data.get("account_number"),
            )
            .first()
        )

        if existing_asset:
            # 更新 (Update)
            existing_asset.balance = asset_data.get("balance", 0.0)
            existing_asset.status = asset_data.get("status", "更新あり")
        else:
            # 新規登録 (Insert)
            new_asset = FinancialAsset(
                case_id=case_id,
                bank_id=bank.id,
                account_number=asset_data.get("account_number"),
                balance=asset_data.get("balance", 0.0),
                status="新規取込",
            )
            session.add(new_asset)
````

## File: src/legal_system/main.py
````python
# ファイルパス: src/legal_system/main.py

import subprocess
import sys
from pathlib import Path


def main():
    """
    Streamlitアプリとフォルダ監視(Watcher)を同時に起動するランチャー
    """
    current_dir = Path(__file__).parent.absolute()
    app_path = current_dir / "ui" / "Home.py"

    # プロジェクトルートにある run_watcher.py のパス
    # src/legal_system/main.py -> src/legal_system -> src -> root
    root_dir = current_dir.parent.parent
    watcher_path = root_dir / "run_watcher.py"

    print("🚀 Legal RAG System を起動します...")

    # 1. 監視プロセスをバックグラウンドで起動
    watcher_process = None
    if watcher_path.exists():
        print("👀 フォルダ監視(Watcher)を開始します...")
        watcher_process = subprocess.Popen([sys.executable, str(watcher_path)])
    else:
        print("⚠️ run_watcher.py が見つからないため、監視機能はスキップします。")

    # 2. Streamlitをメインプロセスとして起動 (これが終わるまで待機)
    print(f"📂 UI起動: {app_path}")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]

    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 システムを終了します。")
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
    finally:
        # アプリが終了したら、監視プロセスも終了させる
        if watcher_process:
            print("🛑 監視プロセスを停止中...")
            watcher_process.terminate()
            watcher_process.wait()
            print("✅ 完了")


if __name__ == "__main__":
    main()
````

## File: src/legal_system/models/tables.py
````python
# ファイル名: src/legal_system/models/tables.py

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

# ==========================================
# 0. データベース基盤設定 (Base Definition)
# ==========================================
Base = declarative_base()

# ==========================================
# 1. 共通マスタ (Core Master Data)
# ==========================================


class User(Base):
    """
    ユーザー・担当者マスタ
    RAGシステムの「利用者」と、業務システムの「担当者」を兼ねます。
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # RAGのpc_username と 業務のwindows_id を統合
    windows_id = Column(String, unique=True, nullable=False, comment="PCログインID")
    name = Column(String, nullable=False, comment="表示名")
    role = Column(String, default="Operator", comment="権限: Manager/Operator")

    # --- RAG用拡張カラム ---
    department = Column(String, nullable=True, comment="所属部署")
    phone = Column(String, nullable=True, comment="内線・連絡先")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class BankMaster(Base):
    """
    銀行マスタ
    業務管理の「振込先」と、RAGの「検索対象」を兼ねます。
    """

    __tablename__ = "bank_master"

    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    bank_code = Column(String, nullable=False)

    # --- RAG検索用拡張 (CSVの内容をDB化) ---
    seal_cert_limit = Column(String, comment="印鑑証明期限")  # 例: 3ヶ月以内
    id_verify_rule = Column(String, comment="本人確認書類")  # 例: 原本提示
    transfer_rule = Column(String, comment="振込ルール")  # 例: 引落しのみ
    remarks = Column(Text, comment="特記事項")  # RAGが参照する備考

    __table_args__ = (
        UniqueConstraint("bank_name", name="_bank_name_uc"),
        UniqueConstraint("bank_code", name="_bank_code_uc"),
    )

    # リレーションシップ定義
    branches = relationship(
        "BranchMaster", back_populates="bank_ref", cascade="all, delete-orphan"
    )
    financial_assets = relationship("FinancialAsset", back_populates="bank_ref")
    aliases = relationship(
        "BankAlias", back_populates="bank_ref", cascade="all, delete-orphan"
    )

    # RAGのファイルとも紐付け (銀行ごとの手引き等)
    rag_files = relationship("FileRegistry", back_populates="bank_ref")


class BankAlias(Base):
    """
    銀行名ゆらぎ吸収用テーブル
    OCRやAIが「三菱UFJ」「MUFG」などを同一視するために使用します。
    """

    __tablename__ = "bank_aliases"

    id = Column(Integer, primary_key=True, index=True)
    alias_name = Column(String, unique=True, index=True, nullable=False)
    bank_id = Column(
        Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False
    )

    bank_ref = relationship("BankMaster", back_populates="aliases")


class BranchMaster(Base):
    """支店マスタ"""

    __tablename__ = "branch_master"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(
        Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False
    )
    branch_name = Column(String, nullable=False)
    branch_code = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("bank_id", "branch_code", name="_bank_branch_code_uc"),
    )

    bank_ref = relationship("BankMaster", back_populates="branches")
    financial_assets = relationship("FinancialAsset", back_populates="branch_ref")


class AccountTypeMaster(Base):
    """口座種類マスタ (普通、定期、当座など)"""

    __tablename__ = "account_type_master"

    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String, unique=True, nullable=False)

    financial_assets = relationship("FinancialAsset", back_populates="account_type_ref")


class DocumentType(Base):
    """書類種別マスタ (戸籍謄本、印鑑証明書など)"""

    __tablename__ = "document_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class ShippingMethod(Base):
    """郵送方法マスタ (簡易書留、レターパックなど)"""

    __tablename__ = "shipping_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tracking_base_url = Column(String, nullable=False)
    estimated_days = Column(Integer)


class SubmissionDocType(Base):
    """提出書類種別マスタ"""

    __tablename__ = "submission_doc_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


# ==========================================
# 2. RAGシステム用テーブル (Knowledge Base)
# ==========================================


class AuditLog(Base):
    """
    AI検索・操作ログ
    「誰が」「いつ」「何を検索したか」を記録します。
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)

    # Userテーブルと紐付けることで、担当者ごとの利用履歴を管理
    user_id = Column(Integer, ForeignKey("users.id"))

    action_type = Column(String)  # SEARCH, UPLOAD, DELETE
    target = Column(String)  # ファイル名や検索クエリ
    details = Column(Text)  # 詳細内容

    user = relationship("User")


class FileRegistry(Base):
    """
    RAG雛形ファイルの管理テーブル
    VectorStore (ChromaDB) 上のデータと物理ファイルを紐付けます。
    """

    __tablename__ = "file_registry"

    file_hash = Column(String, primary_key=True)  # MD5ハッシュ (重複防止)
    filename = Column(String, nullable=False)

    # 銀行マスタと紐付けることで、銀行ごとの書類検索を高速化
    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=True)

    # 【追加】案件(Case)との紐付け (NULL許容 = 共通テンプレート)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)

    doc_type = Column(String, default="その他")  # 手引き, 委任状, 残高証明...
    registered_at = Column(DateTime, default=datetime.now)
    security_level = Column(String, default="general")  # general / secure

    # 物理ファイルのパス (相対パス推奨)
    file_path = Column(String)

    # 登録者
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    bank_ref = relationship("BankMaster", back_populates="rag_files")

    # 【追加】案件リレーション
    case_ref = relationship("Case")
    registrar = relationship("User")


# ==========================================
# 3. 個人情報管理テーブル (Contacts & Addresses)
# ==========================================


class Address(Base):
    """住所マスタ"""

    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    zip_code = Column(String)
    prefecture = Column(String, nullable=False)
    city_ward_town = Column(String)
    street_address = Column(String, nullable=False)
    building_name = Column(String)

    deceased_history = relationship(
        "D_AddressHistory", back_populates="address", cascade="all, delete-orphan"
    )
    heir_history = relationship(
        "H_AddressHistory", back_populates="address", cascade="all, delete-orphan"
    )


class Contact(Base):
    """連絡先マスタ (電話、メール)"""

    __tablename__ = "contact"
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    type = Column(String, nullable=False)  # PHONE, EMAIL
    sub_type = Column(String)


class Deceased(Base):
    """被相続人 (亡くなった方)"""

    __tablename__ = "deceased"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, unique=True)
    name_last = Column(String)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    hometown = Column(String)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    relationship_type = Column(String)
    last_address_id = Column(Integer, ForeignKey("address.id"))

    heirs = relationship(
        "Heir", back_populates="deceased", cascade="all, delete-orphan"
    )
    address_links = relationship(
        "D_AddressHistory", back_populates="deceased", cascade="all, delete-orphan"
    )
    contact_links = relationship(
        "D_ContactLink", back_populates="deceased", cascade="all, delete-orphan"
    )
    case = relationship("Case", back_populates="deceased_ref")
    last_address = relationship("Address", foreign_keys=[last_address_id])


class Heir(Base):
    """相続人"""

    __tablename__ = "heirs"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    name_last = Column(String, nullable=False)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    hometown = Column(String)
    date_of_birth = Column(Date)
    date_of_death = Column(Date)  # 代襲相続などの場合用
    relationship_type = Column(String)
    is_contracting_party = Column(Boolean, default=False)

    deceased = relationship("Deceased", back_populates="heirs")
    address_links = relationship(
        "H_AddressHistory", back_populates="heir", cascade="all, delete-orphan"
    )
    contact_links = relationship(
        "H_ContactLink", back_populates="heir", cascade="all, delete-orphan"
    )


# --- リンクテーブル群 (中間テーブル) ---


class D_AddressHistory(Base):
    __tablename__ = "d_address_history"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_last_address = Column(Boolean, nullable=False, default=False)
    deceased = relationship("Deceased", back_populates="address_links")
    address = relationship("Address", back_populates="deceased_history")


class H_AddressHistory(Base):
    __tablename__ = "h_address_history"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_current_address = Column(Boolean, nullable=False, default=False)
    heir = relationship("Heir", back_populates="address_links")
    address = relationship("Address", back_populates="heir_history")


class D_ContactLink(Base):
    __tablename__ = "d_contact_link"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    deceased = relationship("Deceased", back_populates="contact_links")
    contact = relationship("Contact")


class H_ContactLink(Base):
    __tablename__ = "h_contact_link"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    heir = relationship("Heir", back_populates="contact_links")
    contact = relationship("Contact")


# ==========================================
# 4. 案件ハブテーブル (Core Case Management)
# ==========================================


class CaseStatus(Base):
    """案件ステータス (受任、調査中、完了など)"""

    __tablename__ = "case_statuses"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    order_num = Column(Integer)


class Case(Base):
    """相続案件テーブル"""

    __tablename__ = "cases"
    case_id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)  # G0001
    folder_path = Column(String)
    client_name = Column(String, nullable=False)
    client_name_kana = Column(String)

    manager_id = Column(Integer, ForeignKey("users.id"))
    operator_id = Column(Integer, ForeignKey("users.id"))
    current_status_id = Column(Integer, ForeignKey("case_statuses.id"))

    # 金額・契約情報
    fee_contract_amount = Column(Float, default=0.0)
    deposit_required_amount = Column(Float, default=0.0)
    deposit_paid_amount = Column(Float, default=0.0)
    is_paid_in_full = Column(Boolean, default=False)
    certs_of_seal_count = Column(Integer, default=0)
    power_of_attorney_count = Column(Integer, default=0)

    # 日付関連
    date_of_death = Column(Date)
    interview_date = Column(DateTime)
    contract_date = Column(Date)
    tax_deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

    # 紹介情報・SOL連携
    sol_case_number = Column(String, nullable=True, comment="SOL案件No")
    introduction_date = Column(Date, nullable=True, comment="紹介日")
    referral_sec_branch_name = Column(String, nullable=True, comment="証券会社支店名")
    referral_sec_rep_name = Column(String, nullable=True, comment="証券会社担当者名")
    consent_date = Column(Date, nullable=True, comment="同意書日付")

    # リレーション定義
    manager = relationship("User", foreign_keys=[manager_id])
    operator = relationship("User", foreign_keys=[operator_id])
    status_ref = relationship("CaseStatus")

    deceased_ref = relationship(
        "Deceased", back_populates="case", uselist=False, cascade="all, delete-orphan"
    )
    financial_assets = relationship(
        "FinancialAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    real_estates = relationship(
        "RealEstateAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    tasks = relationship(
        "Task", back_populates="case_ref", cascade="all, delete-orphan"
    )
    expenses = relationship(
        "Expense", back_populates="case_ref", cascade="all, delete-orphan"
    )
    submitted_docs = relationship(
        "CaseSubmissionDoc", back_populates="case_ref", cascade="all, delete-orphan"
    )
    contact_logs = relationship(
        "ContactLog", back_populates="case_ref", cascade="all, delete-orphan"
    )
    insurance_assets = relationship(
        "InsuranceAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    other_assets = relationship(
        "OtherAsset", back_populates="case_ref", cascade="all, delete-orphan"
    )
    liabilities = relationship(
        "Liability", back_populates="case_ref", cascade="all, delete-orphan"
    )
    contact_points = relationship(
        "CaseContactPoint", back_populates="case_ref", cascade="all, delete-orphan"
    )


class CaseContactPoint(Base):
    """案件ごとの連絡窓口"""

    __tablename__ = "case_contact_points"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_person_name = Column(String)
    relationship_to_client = Column(String)
    address_id = Column(Integer, ForeignKey("address.id"))
    contact_id = Column(Integer, ForeignKey("contact.id"))

    is_primary_contact = Column(Boolean, default=False)
    is_primary_mail_send_destination = Column(Boolean, default=False)

    case_ref = relationship("Case", back_populates="contact_points")
    address_ref = relationship("Address")
    contact_ref = relationship("Contact")


# ==========================================
# 5. タスク管理 (Task Management)
# ==========================================


class TaskTemplate(Base):
    """タスク雛形"""

    __tablename__ = "task_templates"
    template_id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    default_due_days = Column(Integer, default=1)
    is_manager_task = Column(Boolean, default=False)
    depends_on_template_id = Column(Integer, ForeignKey("task_templates.template_id"))

    depends_on = relationship("TaskTemplate", remote_side=[template_id])


class Task(Base):
    """実行タスク"""

    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    template_id = Column(Integer, ForeignKey("task_templates.template_id"))
    description = Column(String, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)

    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    template_ref = relationship("TaskTemplate")
    document_logs = relationship(
        "TaskDocumentLog", back_populates="task_ref", cascade="all, delete-orphan"
    )
    case_ref = relationship("Case", back_populates="tasks")


class TaskDocumentLog(Base):
    """書類郵送ログ"""

    __tablename__ = "task_document_logs"
    log_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    shipping_method_id = Column(
        Integer, ForeignKey("shipping_methods.id"), nullable=False
    )
    sent_date = Column(DateTime, nullable=False)
    sent_to = Column(String, nullable=False)
    tracking_number = Column(String, unique=True)
    is_returned = Column(Boolean, default=False)

    document_type = relationship("DocumentType")
    shipping_method = relationship("ShippingMethod")
    task_ref = relationship("Task", back_populates="document_logs")


# ==========================================
# 6. 財産・トランザクション詳細テーブル
# ==========================================


class FinancialAsset(Base):
    """金融資産 (預貯金)"""

    __tablename__ = "financial_asset"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(
        Integer, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False
    )
    asset_type = Column(String, default="BANK")

    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch_master.id"))
    account_type_id = Column(
        Integer, ForeignKey("account_type_master.id"), nullable=True
    )

    account_number = Column(String)
    balance = Column(Float, default=0.0)
    status = Column(String, default="未確認")

    case_ref = relationship("Case", back_populates="financial_assets")
    bank_ref = relationship("BankMaster", back_populates="financial_assets")
    branch_ref = relationship("BranchMaster", back_populates="financial_assets")
    account_type_ref = relationship(
        "AccountTypeMaster", back_populates="financial_assets"
    )


class RealEstateAsset(Base):
    """不動産資産"""

    __tablename__ = "real_estate_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)

    property_type = Column(
        String, default="Land"
    )  # Land(土地) / Building(建物) / Condo(区分所有)

    # 登記簿上の表示
    location = Column(String, comment="所在")
    lot_number = Column(String, comment="地番")
    land_category = Column(String, comment="地目")
    land_area = Column(Float, comment="地積")
    house_number = Column(String, comment="家屋番号")
    structure = Column(String, comment="構造")
    floor_area = Column(String, comment="床面積")

    ownership_share = Column(String, nullable=True, comment="被相続人の持分")

    registry_pdf_path = Column(String, nullable=True, comment="登記情報PDFパス")
    registry_image_path = Column(String, nullable=True, comment="Word貼付用画像パス")

    case_ref = relationship("Case", back_populates="real_estates")


class InsuranceAsset(Base):
    """保険資産"""

    __tablename__ = "insurance_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    insurance_company = Column(String)
    policy_number = Column(String)
    estimated_value = Column(Float)

    case_ref = relationship("Case", back_populates="insurance_assets")


class OtherAsset(Base):
    """その他の資産 (株式、自動車など)"""

    __tablename__ = "other_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    estimated_value = Column(Float)

    case_ref = relationship("Case", back_populates="other_assets")


class Liability(Base):
    """負債・葬儀費用"""

    __tablename__ = "liability"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    is_debt = Column(Boolean, nullable=False, default=True)
    description = Column(String)
    amount = Column(Float, nullable=False)
    is_funeral_cost = Column(Boolean, nullable=False, default=False)

    case_ref = relationship("Case", back_populates="liabilities")


class Expense(Base):
    """立替経費"""

    __tablename__ = "expenses"
    expense_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    amount = Column(Float, nullable=False)
    expense_date = Column(Date)

    case_ref = relationship("Case", back_populates="expenses")


class ContactLog(Base):
    """対応履歴 (電話メモなど)"""

    __tablename__ = "contact_logs"
    log_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_content = Column(String, nullable=False)
    is_thank_you_payment = Column(Boolean, default=False)

    case_ref = relationship("Case", back_populates="contact_logs")


class CaseSubmissionDoc(Base):
    """提出書類管理"""

    __tablename__ = "case_submission_docs"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)

    case_ref = relationship("Case", back_populates="submitted_docs")


class Coordinate(Base):
    """PDF印字用の座標データモデル"""

    __tablename__ = "coordinates"

    id = Column(Integer, primary_key=True, index=True)

    # どのファイルの座標かを識別するためのID (ファイルのMD5ハッシュ) 【新規追加】
    file_hash = Column(
        String, index=True, nullable=False, comment="ファイル識別ハッシュ"
    )

    label = Column(String, nullable=False, comment="項目名")
    x_point = Column(Float, nullable=False, comment="X座標")
    y_point = Column(Float, nullable=False, comment="Y座標")
    page_number = Column(Integer, default=1, comment="ページ番号")

    font_size = Column(Integer, default=10, comment="フォントサイズ")
    color = Column(String, default="black", comment="文字色")

    value = Column(String, nullable=True, comment="テスト値")
    description = Column(String, nullable=True, comment="備考")


# ==========================================
# 7. 遺言作成業務テーブル (Will Creation - Future)
# ==========================================


class WillCase(Base):
    """
    遺言作成案件テーブル (将来拡張用)
    相続案件(Case)とは別に管理します。
    """

    __tablename__ = "will_cases"

    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)  # 例: W0001

    # 遺言者情報 (生存顧客のためDeceasedとは区別)
    testator_name = Column(String, nullable=False)
    testator_birth = Column(Date)
    testator_address_id = Column(Integer, ForeignKey("address.id"))

    # 担当者リンク
    manager_id = Column(Integer, ForeignKey("users.id"))

    # 遺言の種類
    will_type = Column(String, default="公正証書", comment="公正証書/自筆証書")
    status = Column(
        String, default="ヒアリング中", comment="起案中/公証役場調整中/完了"
    )

    # 公証役場情報
    notary_office_name = Column(String, nullable=True)
    draft_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.now)

    # 財産配分 (既存のAsset構造とは別に、配分ロジックを持つ)
    allocations = relationship("WillAllocation", back_populates="will_case")


class WillAllocation(Base):
    """
    遺言による財産配分テーブル
    「誰に」「何を」「どれだけ」渡すかを定義します。
    """

    __tablename__ = "will_allocations"

    id = Column(Integer, primary_key=True)
    will_id = Column(Integer, ForeignKey("will_cases.id"), nullable=False)

    # 財産の内容 (テキストで柔軟に記述)
    asset_description = Column(String, nullable=False, comment="例: ○○銀行の預金全額")

    # 受取人 (Beneficiary)
    beneficiary_name = Column(String, nullable=False)
    relationship_to_testator = Column(String, comment="続柄: 妻, 長男, 孫...")

    # 配分詳細
    percentage = Column(Float, nullable=True, comment="割合指定の場合 (例: 0.5)")

    will_case = relationship("WillCase", back_populates="allocations")
````

## File: update_bank_master.py
````python
# File: update_bank_master.py

import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import urllib3

# SSL警告を非表示にする（ローカル開発用）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# 設定エリア (絶対パス化)
# ==========================================
ROOT_DIR = Path(__file__).parent.absolute()
BASE_DIR = ROOT_DIR / "data" / "zengin"
BRANCH_DIR = BASE_DIR / "branches"
STATE_FILE = BASE_DIR / "last_updated.json"

# API & URL
REPO_API_URL = (
    "https://api.github.com/repos/zengin-code/source-data/commits?path=data&per_page=1"
)
BANKS_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/banks.json"
)
BRANCH_BASE_URL = (
    "https://raw.githubusercontent.com/zengin-code/source-data/master/data/branches/"
)


def download_data(progress_callback=None):
    print(f"🚀 [Start] データ保存先を確認: {BASE_DIR}")

    # フォルダ作成
    os.makedirs(BRANCH_DIR, exist_ok=True)

    # 1. 銀行一覧
    if progress_callback:
        progress_callback(0, 100, "銀行一覧を取得中...")

    try:
        # verify=False でSSLエラーを回避
        print(f"connecting to {BANKS_URL} ...")
        resp = requests.get(BANKS_URL, timeout=15, verify=False)
        resp.raise_for_status()
        banks = resp.json()

        with open(BASE_DIR / "banks.json", "w", encoding="utf-8") as f:
            json.dump(banks, f, ensure_ascii=False, indent=2)

        print(f"✅ 銀行マスタ保存完了: {len(banks)}件")

    except Exception as e:
        print(f"❌ 銀行一覧の取得に失敗: {e}")
        return False, None

    # 2. 支店データ
    total_banks = len(banks)
    print(f"🔄 支店データ取得開始: 対象 {total_banks} 行")

    success_count = 0
    # 全件取得（エラーが出ても止まらないようにする）
    for i, bank_code in enumerate(list(banks.keys())):
        branch_url = f"{BRANCH_BASE_URL}{bank_code}.json"
        save_path = BRANCH_DIR / f"{bank_code}.json"

        try:
            r = requests.get(branch_url, timeout=10, verify=False)
            if r.status_code == 200:
                with open(save_path, "w", encoding="utf-8") as f:
                    json.dump(r.json(), f, ensure_ascii=False, indent=2)
                success_count += 1

            # プログレスバー更新 (10件に1回更新で負荷軽減)
            if i % 10 == 0 and progress_callback:
                progress_callback(i + 1, total_banks, f"支店データ取得中: {bank_code}")

            # サーバー負荷軽減のためのスリープ
            time.sleep(0.01)

        except Exception:
            # 個別の失敗は無視して続行
            pass

    print(f"✅ 全ダウンロード完了 (成功: {success_count}件)")
    return True, banks


# --- 以下の関数は変更なし ---
def get_remote_last_commit_date():
    try:
        resp = requests.get(REPO_API_URL, timeout=10, verify=False)
        if resp.status_code == 200:
            return resp.json()[0]["commit"]["committer"]["date"]
    except:
        pass
    return None


def load_local_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"last_commit_date": ""}


def save_local_state(commit_date):
    os.makedirs(BASE_DIR, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "last_commit_date": commit_date,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    download_data()
````

## File: run_watcher.py
````python
# file: run_watcher.py
import logging
import os
import sys
import time

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# パス解決
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

# WatcherプロセスではStreamlit環境ではないことを明示するためのフラグ
os.environ["IS_WATCHER_PROCESS"] = "true"

from legal_system.core.data_sync import DataSyncEngine

# ★修正ポイント: コンテナ内でも確実に見えるデータフォルダを監視対象にする
WATCH_DIR = os.path.join(BASE_DIR, "data", "kintone_watch")


class JsonHandler(FileSystemEventHandler):
    def __init__(self):
        time.sleep(2)
        # DataSyncEngine内でDB接続が行われる
        self.syncer = DataSyncEngine()

    def on_created(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)

        if filename.startswith("G") and filename.endswith(".json"):
            logger.info(f"📥 連携JSONを検知: {filename}")
            # ファイルの書き込み完了を待機
            time.sleep(1.5)
            success = self.syncer.sync_from_kintone_json(event.src_path)
            if success:
                logger.info(f"✅ DB同期完了: {filename}")
                # 処理済みファイルは削除または移動すると良いが、今回はログ出力のみ
            else:
                logger.error(f"❌ 同期失敗: {filename}")


if __name__ == "__main__":
    # ★修正ポイント: フォルダが存在しない場合は自動作成する
    if not os.path.exists(WATCH_DIR):
        logger.info(f"監視ディレクトリを作成します: {WATCH_DIR}")
        os.makedirs(WATCH_DIR, exist_ok=True)

    logger.info(f"🚀 監視開始: {WATCH_DIR}")
    logger.info("G番号(Gxxxx.json)のファイルをこのフォルダに置くと、自動で取り込まれます。")

    event_handler = JsonHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 監視を停止します。")
        observer.stop()
    observer.join()
````

## File: src/legal_system/core/ocr_engine.py
````python
"""
OCR処理エンジン・モジュール
PaddleOCRおよびPyMuPDFを使用してPDFからテキストを抽出します。
"""

import logging
import numpy as np
import os
from typing import List, Dict, Any, Optional

# PyMuPDF (fitz) のインポート
import fitz

# PaddleOCR のインポート
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

# OpenCV (cv2) のインポートガード
# コンテナ環境でのインストール漏れに対応
try:
    import cv2
except ImportError:
    cv2 = None

logger = logging.getLogger(__name__)

class OCREngine:
    """
    PaddleOCRを使用した帳票OCR取り込み機能を提供するクラス。
    """

    def __init__(self, lang: str = "japan"):
        """
        OCRエンジンの初期化。
        
        Args:
            lang (str): 言語設定（デフォルトは日本語 'japan'）。
        """
        if cv2 is None:
            logger.error("OpenCV (cv2) がインストールされていません。")
        
        if PaddleOCR is None:
            logger.error("PaddleOCR がインストールされていません。")
            self.ocr = None
        else:
            # PaddleOCRの初期化 (GUIがない環境を想定して use_angle_cls=True)
            self.ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        PDFファイルからテキストと座標情報を抽出する。
        
        Args:
            pdf_path (str): PDFファイルのフルパス。
            
        Returns:
            List[Dict[str, Any]]: 認識結果のリスト。
        """
        if cv2 is None or self.ocr is None:
            raise RuntimeError("OCRエンジンの依存ライブラリ (OpenCV または PaddleOCR) が不足しています。")

        results = []
        doc = None
        try:
            doc = fitz.open(pdf_path)
            for page_index in range(len(doc)):
                page = doc.load_page(page_index)
                pix = page.get_pixmap()
                
                # PyMuPDFの画像をNumPy配列(OpenCV形式)に変換
                img_array = np.frombuffer(pix.samples, dtype=np.uint8)
                
                # 画像のチャンネル数に合わせてリサイズ/変換
                if pix.n == 4:  # RGBA
                    img = img_array.reshape(pix.height, pix.width, 4)
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n == 3:  # RGB
                    img = img_array.reshape(pix.height, pix.width, 3)
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                else:
                    img = img_array.reshape(pix.height, pix.width, pix.n)

                # PaddleOCRで解析
                page_result = self.ocr.ocr(img, cls=True)
                
                if not page_result:
                    continue

                for line in page_result:
                    if not line:
                        continue
                    for res in line:
                        results.append({
                            "page": page_index + 1,
                            "coords": res[0],
                            "text": res[1][0],
                            "confidence": res[1][1]
                        })
        except Exception as e:
            logger.error(f"OCR処理中に予期せぬエラーが発生しました: {e}")
            raise e
        finally:
            if doc:
                doc.close()
            
        return results

# -----------------------------------------------------------------------------
# 重要: 外部(admin_tools.py)から関数として呼び出すためのエクスポート
# -----------------------------------------------------------------------------
def extract_text_from_scanned_pdf(file_path: str) -> List[Dict[str, Any]]:
    """
    既存のUIコンポーネントとの互換性を維持するためのラッパー関数。
    """
    engine = OCREngine()
    return engine.process_pdf(file_path)
````

## File: src/legal.egg-info/top_level.txt
````
__init__
chains
legal_system
````

## File: .gitignore
````
# --- Python & Rye ---
__pycache__/
*.pyc
.venv/
.rye/

# --- 環境変数 & 機密情報 (絶対にGitにあげない) ---
.env
.streamlit/secrets.toml

# --- データベース & ログ ---
# 監査ログやベクターDBはローカルで生成されるため除外
db/sql/*.db
db/chroma/
*.log

# --- 生成されたファイル・アップロードデータ ---
# テンプレートPDFやアップロードされた一時ファイル
data/templates/*.pdf
data/uploads/
data/generated/
data/zengin

# ※フォントファイル(ipaexg.ttf)などはアプリの動作に必要なので
#   除外せず、Gitに含めるのが一般的です

# --- AI Context / Repomix ---
# ソースコードをまとめたファイルは除外
repomix-output.*
all_code_context.txt

# --- IDE / エディタ ---
.vscode/
.idea/

# --- Python Testing / Caching ---
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage

# --- OS ---
.DS_Store
Thumbs.db

bootstrap.py
````

## File: src/legal_system/core/ai_factory.py
````python
# src/legal_system/core/ai_factory.py

import os
import logging
import requests
from typing import Any, Optional

# LangChain - Community / Local
from langchain_community.chat_models import ChatOllama

# LangChain - Google Studio
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# LangChain - Google Vertex AI
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

from .config import Config, KeyManager

logger = logging.getLogger(__name__)

class AIFactory:
    """
    AIモデル（LLM）、Embeddings、VectorStoreのインスタンス生成を一元管理するファクトリークラス。
    AI_PROVIDERの設定に基づき、Google AI Studio または Vertex AI を切り替えます。
    """

    @staticmethod
    def _check_ollama_server(base_url: str) -> bool:
        """Ollamaサーバーの生存確認"""
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=1.0)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def get_llm(cls, mode: str = "cloud", temperature: Optional[float] = None) -> Any:
        """
        LLMインスタンスを取得します。
        
        Args:
            mode (str): "cloud" (Gemini/Vertex) または "local" (Ollama/Llama)
            temperature (float): 生成温度。Noneの場合はConfig値を使用。
        """
        temp = temperature if temperature is not None else Config.TEMPERATURE

        # --- Local Mode (Ollama) ---
        if mode == "local":
            base_url = "http://host.docker.internal:11434"
            
            # 接続チェック（開発時の利便性のため、失敗時はエラーログを出してフォールバック検討等は実装依存）
            if not cls._check_ollama_server(base_url):
                # Docker内通信がだめな場合、localhostも試行(開発環境用)
                base_url = "http://localhost:11434"
                if not cls._check_ollama_server(base_url):
                    raise ConnectionError("❌ Ollamaサーバーに接続できません。")

            # 軽量モデルを指定
            model_name = "llama3.2:1b"
            logger.info(f"🤖 Local LLM Mode: {model_name}")

            return ChatOllama(
                base_url=base_url,
                model=model_name,
                temperature=temp,
                format="json",
                timeout=120,
            )
        
        # --- Cloud Mode (Gemini / Vertex) ---
        else:
            if Config.is_vertex_enabled():
                # Vertex AI (Enterprise)
                logger.info(f"☁️ Cloud LLM Mode: Vertex AI ({Config.GOOGLE_MODEL_NAME})")
                
                # VertexAIはADC(Application Default Credentials)を利用するためAPIキー指定は不要
                # Project/RegionはConfigまたは環境変数から自動取得されるが、明示も可能
                return ChatVertexAI(
                    model_name=Config.GOOGLE_MODEL_NAME,
                    project=Config.GOOGLE_CLOUD_PROJECT,
                    location=Config.GOOGLE_CLOUD_REGION,
                    temperature=temp,
                    convert_system_message_to_human=True,
                    max_retries=2
                )
            else:
                # Google AI Studio (Personal / API Key)
                logger.info(f"☁️ Cloud LLM Mode: AI Studio ({Config.GOOGLE_MODEL_NAME})")
                api_key = KeyManager.get_next_key()
                
                return ChatGoogleGenerativeAI(
                    model=Config.GOOGLE_MODEL_NAME,
                    google_api_key=api_key,
                    temperature=temp,
                    convert_system_message_to_human=True,
                    max_retries=2
                )

    @classmethod
    def get_embeddings(cls) -> Any:
        """埋め込みモデル（Embeddings）を返します。"""
        
        if Config.is_vertex_enabled():
            # Vertex AI Embeddings
            # モデル名は text-embedding-004 などが望ましいが、Configに従う
            return VertexAIEmbeddings(
                model_name="text-embedding-004", # Vertex推奨モデルに固定
                project=Config.GOOGLE_CLOUD_PROJECT,
                location=Config.GOOGLE_CLOUD_REGION,
            )
        else:
            # AI Studio Embeddings
            api_key = KeyManager.get_next_key()
            return GoogleGenerativeAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                google_api_key=api_key
            )

    @classmethod
    def get_vector_store(cls):
        """永続化されたChromaベクトルストアのインスタンスを返します。"""
        from langchain_chroma import Chroma
        
        embeddings = cls.get_embeddings()

        if not Config.VECTOR_STORE_PATH.exists():
            os.makedirs(Config.VECTOR_STORE_PATH, exist_ok=True)

        return Chroma(
            persist_directory=str(Config.VECTOR_STORE_PATH),
            embedding_function=embeddings,
        )
````

## File: src/legal_system/ui/Home.py
````python
# src/legal_system/ui/Home.py

import os
import sys
import time

import streamlit as st
from dotenv import load_dotenv

# パス解決
current_dir = os.path.dirname(os.path.abspath(__file__))

# Home.py から見て3つ上がプロジェクトのルート(ROOT)になります
# ui -> legal_system -> src -> ROOT
ROOT_DIR = os.path.abspath(os.path.join(current_dir, "../../../"))

# Pythonにプログラムの場所を教える(srcフォルダを追加)
src_path = os.path.abspath(os.path.join(current_dir, "../../"))
if src_path not in sys.path:
    sys.path.append(src_path)

from legal_system.core.database_manager import DatabaseManager

# 環境変数の読み込み
load_dotenv()

# ==========================================
# 1. アプリケーションの初期設定
# ==========================================
st.set_page_config(page_title="実務Q&A | 法務RAG", layout="wide", page_icon="⚖️")

# ==========================================
# 2. 起動時プリロード処理 (真っ白画面・フリーズ対策)
# ==========================================
# 画面が真っ白になるのを防ぐため、重いモジュールを読み込む前にタイトルを即座に表示します
if "is_initialized" not in st.session_state:
    st.title("💬 金融機関手続 Q&A")
    st.info("🚀 システムを起動しています。しばらくお待ちください...")

    # statusコンポーネントでロードの進捗を可視化します
    with st.status("📦 業務モジュールをロード中...", expanded=True) as status:
        # 重いライブラリをバックグラウンドでロード
        from legal_system.core.preload import warm_up_modules

        st.write("🔧 重いライブラリ（PDF/AI系）を展開しています...")
        warm_up_modules()

        st.write("🧠 AIエンジン（Gemini/Ollama）を準備中...")
        from legal_system.core.ai_factory import AIFactory

        st.write("🗄️ データベース接続を確認中...")
        db_manager = DatabaseManager()

        status.update(label="✅ 準備完了！", state="complete", expanded=False)

    st.session_state["is_initialized"] = True
    time.sleep(0.5)
    st.rerun()

# --- 初期化完了後の実体取得 ---
db_manager = DatabaseManager()
current_user = db_manager.get_current_user_info()

# AI関連のインポート（キャッシュされているため高速）
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from legal_system.core.ai_factory import AIFactory

# 銀行マスタ更新スクリプトのインポート
try:
    from update_bank_master import (
        download_data,
        get_remote_last_commit_date,
        load_local_state,
        save_local_state,
    )
except ImportError:
    get_remote_last_commit_date = None

# ==========================================
# 3. ヘルパー関数
# ==========================================


@st.cache_resource(ttl=60)
def check_update_status():
    """銀行データの更新が必要か判定"""
    if not get_remote_last_commit_date:
        return 2, "更新スクリプトが見つかりません"
    banks_path = os.path.join(ROOT_DIR, "data", "zengin", "banks.json")
    if not os.path.exists(banks_path):
        return 1, "銀行データが未取得です"
    remote = get_remote_last_commit_date()
    local = load_local_state().get("last_commit_date", "")
    if remote and remote != local:
        return 1, f"新着データがあります ({remote})"
    return 0, "最新の状態です"


def load_company_rules():
    """社内規定ファイルを読み込む"""
    path = os.path.join(ROOT_DIR, "data", "rules", "company_rules.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "規定ファイルが見つかりません。"


def run_rag_search(query, mode, llm):
    """RAGによる検索と回答生成"""
    vector_store = AIFactory.get_vector_store()
    docs = vector_store.similarity_search(query, k=4)
    context = "\n".join([d.page_content for d in docs])

    # 結論と箇条書きのみを求めるプロンプト
    prompt = ChatPromptTemplate.from_template(
        "結論と箇条書きのみで回答してください。挨拶は不要です。\n\n"
        "【社内ルール】\n{rules}\n\n"
        "【参照資料】\n{context}\n\n"
        "質問: {question}"
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {"rules": load_company_rules(), "context": context, "question": query}
    ), docs


# ==========================================
# 4. メイン UI
# ==========================================
def main():
    # --- サイドバー ---
    with st.sidebar:
        st.title("⚖️ 業務メニュー")
        
        # ユーザー情報の表示
        st.info(f"👤 **{current_user['name']}**")
        st.caption(f"所属: {current_user['dept']} | Tel: {current_user['phone']}")

        # ▼▼▼ ユーザー編集機能 (追加) ▼▼▼
        with st.expander("⚙️ プロフィール編集"):
            with st.form("user_profile_form"):
                new_name = st.text_input("表示名", value=current_user["name"])
                new_dept = st.text_input("所属部署", value=current_user["dept"])
                new_phone = st.text_input("内線/直通", value=current_user["phone"])
                
                submitted = st.form_submit_button("更新する")
                if submitted:
                    try:
                        db_manager.register_user(
                            windows_id=current_user["id"],
                            display_name=new_name,
                            department=new_dept,
                            phone=new_phone
                        )
                        st.success("更新しました！")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e:
                        st.error(f"更新エラー: {e}")
        # ▲▲▲ ここまで ▲▲▲

        st.divider()

        # 銀行データ更新セクション
        st.subheader("🏦 銀行マスタ管理")
        status_code, info = check_update_status()

        if status_code == 1:
            st.warning(f"💡 {info}")
        else:
            st.success(f"✅ {info}")

        # 強制更新ボタンを常駐
        if st.button("🔄 銀行データを強制更新", use_container_width=True):
            with st.status("🔄 銀行データを更新中...", expanded=True) as s:
                progress_bar = st.progress(0)

                def cb(cur, tot, msg):
                    progress_bar.progress(min(cur / tot, 1.0))

                download_data(progress_callback=cb)
                if get_remote_last_commit_date:
                    save_local_state(get_remote_last_commit_date())
                s.update(label="✅ 更新が完了しました！", state="complete")
            st.rerun()

    # --- メインチャットエリア ---
    st.title("💬 金融機関手続 Q&A")

    ai_mode = st.radio(
        "AIモード選択",
        ("☁️ Cloud (Gemini) - 一般用", "🔒 Secure (Local) - 個人情報用"),
        horizontal=True,
        label_visibility="collapsed",
    )

    # モードに応じたモデル取得
    mode_key = "cloud" if "Cloud" in ai_mode else "local"
    llm = AIFactory.get_llm(mode_key)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 履歴の表示
    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.write(m["content"])

    # 質問入力
    if prompt := st.chat_input(
        "調べたい内容を入力してください（例：三菱UFJ銀行の印鑑証明書期限）"
    ):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                response, docs = run_rag_search(prompt, mode_key, llm)
                st.write(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )


if __name__ == "__main__":
    main()
````

## File: src/legal_system/core/config.py
````python
# file: src/legal_system/core/config.py

import os
import random
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# .env ファイルの読み込み
load_dotenv()

# ==========================================
# 1. パス設定 (モジュールレベル定数)
# ==========================================
BASE_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BASE_DIR / "data"

# DB関連パス
DB_FILE_SQLITE = DATA_DIR / "db" / "sql" / "legal_system.db"
DB_DIR_CHROMA = DATA_DIR / "db" / "chroma" / "local_rag_db"

# データ一時保存先
DATA_DIR_TEMPLATES = DATA_DIR / "templates"
VECTOR_STORE_PATH = DB_DIR_CHROMA

# RAG関連パス
RULES_DIR = DATA_DIR / "rules"
BANK_MASTER_PATH = RULES_DIR / "bank_master.csv"
COMPANY_RULES_PATH = RULES_DIR / "company_rules.txt"


# ==========================================
# 2. 設定管理クラス (Config)
# ==========================================
class Config:
    """
    システム全体の設定定数を管理するクラス。
    """

    # --- パス設定 ---
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    TEMPLATES_DIR = DATA_DIR_TEMPLATES

    # RAG関連パス
    BANK_MASTER_PATH = BANK_MASTER_PATH
    COMPANY_RULES_PATH = COMPANY_RULES_PATH
    VECTOR_STORE_PATH = VECTOR_STORE_PATH

    # --- データベース設定 (PostgreSQL) ---
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "legal_db")

    DATABASE_URL = (
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # --- AIプロバイダー設定 (New) ---
    # "studio" (API Key) or "vertex" (Google Cloud)
    AI_PROVIDER = os.getenv("AI_PROVIDER", "studio").lower()

    # --- Vertex AI 設定 ---
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION", "asia-northeast1")

    # --- モデル設定 ---
    # Vertex利用時はPublisher Model IDとして扱われる
    GOOGLE_MODEL_NAME = "gemini-2.5-flash-lite"
    MODEL_NAME = "gemini-2.5-flash-lite"
    
    # Embedding Model
    # Vertex利用時は "text-embedding-004" 等が推奨されるが、ここでは互換性のため一旦共通化
    EMBEDDING_MODEL = "models/embedding-001"
    
    TEMPERATURE = 0.0

    # APIキー管理 (Studio用)
    _keys_str = os.getenv("GOOGLE_API_KEYS", "")
    GOOGLE_API_KEYS: List[str] = [k.strip() for k in _keys_str.split(",") if k.strip()]

    if not GOOGLE_API_KEYS and os.getenv("GOOGLE_API_KEY"):
        GOOGLE_API_KEYS = [os.getenv("GOOGLE_API_KEY")]

    @classmethod
    def validate_paths(cls) -> None:
        """必須ディレクトリの存在確認"""
        if not cls.DATA_DIR.exists():
            os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not cls.TEMPLATES_DIR.exists():
            os.makedirs(cls.TEMPLATES_DIR, exist_ok=True)
        
    @classmethod
    def is_vertex_enabled(cls) -> bool:
        return cls.AI_PROVIDER == "vertex"


# ==========================================
# 3. キー管理クラス (KeyManager)
# ==========================================
class KeyManager:
    @staticmethod
    def get_next_key() -> str:
        # Vertexの場合はキー不要（ADC利用）だが、Config互換性のために実装維持
        if Config.is_vertex_enabled():
            return "vertex-managed"
            
        keys = Config.GOOGLE_API_KEYS
        if not keys:
            env_key = os.getenv("GOOGLE_API_KEY")
            if env_key:
                return env_key
            raise ValueError("❌ 有効な Google API Key が見つかりません。")
        return random.choice(keys)
````

## File: src/legal_system/core/database_manager.py
````python
# file: src/legal_system/core/database_manager.py

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from sqlalchemy import create_engine, desc
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

# テーブル定義
from src.legal_system.models.tables import (
    AuditLog,
    Base,
    Case,
    Coordinate,
    FileRegistry,
    User,
)

# Config
from .config import Config


# ==========================================
# エンジン生成の共通ロジック (キャッシュなし)
# ==========================================
def _create_new_engine() -> Engine:
    """
    SQLAlchemyエンジンを新規作成する内部関数。
    Streamlitへの依存を含みません。
    """
    # 【修正ポイント】 Windows環境での文字コードエラー(0x83)を防ぐため
    # client_encoding='utf8' を明示的に指定します。
    engine = create_engine(
        Config.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        connect_args={"client_encoding": "utf8"}  # Windows対策: 文字化けクラッシュ防止
    )

    # テーブル作成 (初回のみ)
    try:
        Base.metadata.create_all(engine)
    except Exception as e:
        # Streamlit環境下であればエラー表示、そうでなければ標準出力へ
        msg = f"❌ データベース接続エラー: {e}"
        # Watcherプロセスかどうかの判定
        if os.environ.get("IS_WATCHER_PROCESS") != "true":
            st.error(msg)
            st.info("PostgreSQLサーバー設定(.env)を確認してください。")
        else:
            print(msg)
        raise e

    return engine


# ==========================================
# Streamlit用 キャッシュ付きエンジン取得
# ==========================================
@st.cache_resource(show_spinner="データベースに接続中...")
def _get_cached_engine() -> Engine:
    """Streamlitのキャッシュ機能を利用してエンジンを保持する"""
    return _create_new_engine()


# ==========================================
# 公開アクセサ (環境判定ロジック付き)
# ==========================================
def get_db_engine() -> Engine:
    """
    実行環境に応じて適切なエンジン取得方法を選択するファクトリー関数。
    - Watcherプロセス (IS_WATCHER_PROCESS=true): キャッシュなしで新規作成
    - Streamlitアプリ: st.cache_resourceを利用して高速化
    """
    if os.environ.get("IS_WATCHER_PROCESS") == "true":
        # バックグラウンド処理ではStreamlitのキャッシュ機能を使わない
        return _create_new_engine()
    else:
        # UIスレッドではキャッシュを使う
        return _get_cached_engine()


class DatabaseManager:
    """
    データベース操作を一元管理するクラス。
    環境に応じたエンジン取得戦略を内部で自動解決します。
    """

    def __init__(self):
        # 環境判定済みのエンジン取得関数を呼び出し
        self.engine = get_db_engine()

        # セッションファクトリの作成
        self.session_factory = sessionmaker(bind=self.engine)

        # スレッドセーフなセッション
        self.Session = scoped_session(self.session_factory)

    def _get_session(self):
        """新しいセッションを発行"""
        return self.Session()

    # ---------------------------------------------------------
    # ユーザー管理
    # ---------------------------------------------------------
    def get_current_user_info(self) -> Dict[str, str]:
        """Windowsログインユーザー情報を取得または作成"""
        # Streamlit Cloud等でOSユーザーが取れない場合のフォールバック
        pc_user = os.environ.get("USERNAME", "guest_user")

        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=pc_user).first()
            if user:
                return {
                    "id": user.windows_id,
                    "name": user.name,
                    "dept": user.department if user.department else "",
                    "phone": user.phone if user.phone else "",
                }
            else:
                # 新規自動登録
                default_name = f"{pc_user}"
                default_dept = "未設定"
                new_user = User(
                    windows_id=pc_user,
                    name=default_name,
                    department=default_dept,
                    role="Operator",
                )
                session.add(new_user)
                session.commit()
                return {
                    "id": pc_user,
                    "name": default_name,
                    "dept": default_dept,
                    "phone": "",
                }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return {"id": pc_user, "name": pc_user, "dept": "Error", "phone": ""}
        finally:
            session.close()

    def register_user(
        self, windows_id: str, display_name: str, department: str, phone: str
    ):
        session = self._get_session()
        try:
            user = session.query(User).filter_by(windows_id=windows_id).first()
            if user:
                user.name = display_name
                user.department = department
                user.phone = phone
                user.updated_at = datetime.now()
            else:
                user = User(
                    windows_id=windows_id,
                    name=display_name,
                    department=department,
                    phone=phone,
                    role="Operator",
                )
                session.add(user)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------------------------------------------------------
    # ログ管理
    # ---------------------------------------------------------
    def log_action(self, user_id: str, action: str, target: str, details: str = ""):
        session = self._get_session()
        try:
            # user_id (windows_id) から内部IDを引く
            db_user = session.query(User).filter_by(windows_id=user_id).first()
            u_id = db_user.id if db_user else None

            log = AuditLog(
                user_id=u_id,
                action_type=action,
                target=target,
                details=details,
                timestamp=datetime.now(),
            )
            session.add(log)
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()

    # ---------------------------------------------------------
    # ファイル管理
    # ---------------------------------------------------------
    def is_file_registered(self, file_hash: str) -> bool:
        session = self._get_session()
        try:
            exists = session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            return exists is not None
        finally:
            session.close()

    def register_file_hash(
        self,
        file_hash: str,
        filename: str,
        doc_type: str = "その他",
        case_id: Optional[int] = None,
    ):
        session = self._get_session()
        try:
            file_reg = (
                session.query(FileRegistry).filter_by(file_hash=file_hash).first()
            )
            if file_reg:
                file_reg.filename = filename
                file_reg.doc_type = doc_type
                if case_id is not None:
                    file_reg.case_id = case_id
                file_reg.registered_at = datetime.now()
            else:
                file_reg = FileRegistry(
                    file_hash=file_hash,
                    filename=filename,
                    doc_type=doc_type,
                    case_id=case_id,
                    registered_at=datetime.now(),
                )
                session.add(file_reg)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_files(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            results = (
                session.query(FileRegistry, Case)
                .outerjoin(Case, FileRegistry.case_id == Case.case_id)
                .order_by(desc(FileRegistry.registered_at))
                .all()
            )
            output = []
            for f, c in results:
                case_label = f"{c.case_number}" if c else "（共通雛形）"
                output.append(
                    {
                        "filename": f.filename,
                        "date": f.registered_at.strftime("%Y-%m-%d %H:%M:%S")
                        if f.registered_at
                        else "",
                        "hash": f.file_hash,
                        "type": f.doc_type if f.doc_type else "その他",
                        "case": case_label,
                        "doc_type": f.doc_type,
                        "uploaded_at": f.registered_at,
                    }
                )
            return output
        finally:
            session.close()

    def delete_file_registry(self, filename: str):
        session = self._get_session()
        try:
            session.query(FileRegistry).filter_by(filename=filename).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ---------------------------------------------------------
    # 座標管理 (Coordinate Tool)
    # ---------------------------------------------------------
    def register_coordinate(
        self,
        file_hash,
        label,
        x,
        y,
        page_number=1,
        description="",
        font_size=10,
        color="black",
        test_value="",
    ):
        session = self._get_session()
        try:
            coord = (
                session.query(Coordinate)
                .filter_by(file_hash=file_hash, label=label)
                .first()
            )
            if not coord:
                coord = Coordinate(file_hash=file_hash, label=label)
                session.add(coord)

            coord.x_point = x
            coord.y_point = y
            coord.page_number = page_number
            coord.description = description
            coord.font_size = font_size
            coord.color = color
            coord.value = test_value
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def get_coordinates_by_hash(self, file_hash: str) -> List[Dict]:
        session = self._get_session()
        try:
            coords = session.query(Coordinate).filter_by(file_hash=file_hash).all()
            return [
                {
                    "id": c.id,
                    "label": c.label,
                    "x": c.x_point,
                    "y": c.y_point,
                    "page": c.page_number,
                    "desc": c.description,
                    "font_size": c.font_size,
                    "color": c.color,
                    "value": c.value,
                }
                for c in coords
            ]
        finally:
            session.close()

    def update_coordinate_direct(self, coord_id: int, updates: Dict):
        session = self._get_session()
        try:
            coord = session.query(Coordinate).filter_by(id=coord_id).first()
            if coord:
                for k, v in updates.items():
                    if k == "x":
                        coord.x_point = v
                    elif k == "y":
                        coord.y_point = v
                    elif k == "desc":
                        coord.description = v
                    # 必要に応じて他のフィールドも追加
                    elif hasattr(coord, k):
                        setattr(coord, k, v)
                session.commit()
                return True
            return False
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()

    def delete_coordinate(self, coordinate_id: int):
        session = self._get_session()
        try:
            session.query(Coordinate).filter_by(id=coordinate_id).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False
        finally:
            session.close()
````

## File: src/legal.egg-info/PKG-INFO
````
Metadata-Version: 2.4
Name: legal
Version: 0.1.1
Summary: Administrative Scrivener RAG System
Author-email: Admin <admin@example.com>
Requires-Python: >=3.10
Description-Content-Type: text/markdown
Requires-Dist: streamlit>=1.34.0
Requires-Dist: langchain>=0.1.0
Requires-Dist: langchain-community>=0.0.20
Requires-Dist: langchain-core>=0.1.25
Requires-Dist: langchain-google-genai>=0.0.9
Requires-Dist: langchain-google-vertexai>=0.0.5
Requires-Dist: google-cloud-aiplatform>=1.38.0
Requires-Dist: langchain-huggingface>=0.0.1
Requires-Dist: langchain-chroma>=0.1.0
Requires-Dist: chromadb>=0.4.24
Requires-Dist: pypdf>=4.0.1
Requires-Dist: pdf2image>=1.17.0
Requires-Dist: pytesseract>=0.3.10
Requires-Dist: python-dotenv>=1.0.1
Requires-Dist: pandas>=2.3.3
Requires-Dist: openpyxl>=3.1.2
Requires-Dist: sentence-transformers>=5.2.0
Requires-Dist: numpy<2.0
Requires-Dist: streamlit-image-coordinates>=0.4.0
Requires-Dist: reportlab>=4.4.7
Requires-Dist: watchdog>=6.0.0
Requires-Dist: psycopg2-binary>=2.9.11
Requires-Dist: opencv-python<4.9
Requires-Dist: opencv-python-headless<4.9
Requires-Dist: pymupdf>=1.26.7
Requires-Dist: streamlit-drawable-canvas>=0.9.3

# legal-rag-project

Describe your project here.
````

## File: src/legal.egg-info/requires.txt
````
streamlit>=1.34.0
langchain>=0.1.0
langchain-community>=0.0.20
langchain-core>=0.1.25
langchain-google-genai>=0.0.9
langchain-google-vertexai>=0.0.5
google-cloud-aiplatform>=1.38.0
langchain-huggingface>=0.0.1
langchain-chroma>=0.1.0
chromadb>=0.4.24
pypdf>=4.0.1
pdf2image>=1.17.0
pytesseract>=0.3.10
python-dotenv>=1.0.1
pandas>=2.3.3
openpyxl>=3.1.2
sentence-transformers>=5.2.0
numpy<2.0
streamlit-image-coordinates>=0.4.0
reportlab>=4.4.7
watchdog>=6.0.0
psycopg2-binary>=2.9.11
opencv-python<4.9
opencv-python-headless<4.9
pymupdf>=1.26.7
streamlit-drawable-canvas>=0.9.3
````

## File: src/legal.egg-info/SOURCES.txt
````
README.md
pyproject.toml
src/__init__.py
src/chains/bank_procedure_chain.py
src/legal.egg-info/PKG-INFO
src/legal.egg-info/SOURCES.txt
src/legal.egg-info/dependency_links.txt
src/legal.egg-info/requires.txt
src/legal.egg-info/top_level.txt
src/legal_system/__init__.py
src/legal_system/main.py
src/legal_system/core/__init__.py
src/legal_system/core/ai_factory.py
src/legal_system/core/config.py
src/legal_system/core/data_sync.py
src/legal_system/core/database_manager.py
src/legal_system/core/engines.py
src/legal_system/core/ocr_engine.py
src/legal_system/core/pdf_processor.py
src/legal_system/core/preload.py
src/legal_system/models/__init__.py
src/legal_system/models/base.py
src/legal_system/models/tables.py
src/legal_system/tools/__init__.py
src/legal_system/tools/coord_tool.py
src/legal_system/ui/Home.py
src/legal_system/ui/__init__.py
src/legal_system/ui/excel_generator.py
src/legal_system/ui/components/admin_tools.py
src/legal_system/ui/pages/01_Kintoneデータ_エクセル入力フォーム.py
src/legal_system/ui/pages/02_預貯金口座入力フォーム.py
src/legal_system/ui/pages/03_相続書類_作成フォーム.py
src/legal_system/ui/pages/04_法定相続情報_読取.py
src/legal_system/ui/pages/05_顧客紹介連絡表_読取.py
src/legal_system/ui/pages/99_書式座標登録ツール.py
src/legal_system/ui/pages/backup/98_Llama実験室.py
src/legal_system/ui/pages/backup/99_Gemini実験室.py
````

## File: pyproject.toml
````toml
[project]
name = "legal"
version = "0.1.1"
description = "Administrative Scrivener RAG System"
authors = [
    { name = "Admin", email = "admin@example.com" }
]
dependencies = [
    "streamlit>=1.34.0",
    "langchain>=0.1.0",
    "langchain-community>=0.0.20",
    "langchain-core>=0.1.25",
    "langchain-google-genai>=0.0.9",
    "langchain-google-vertexai>=0.0.5",  # Added for Vertex AI
    "google-cloud-aiplatform>=1.38.0",   # Added for Vertex AI
    "langchain-huggingface>=0.0.1",
    "langchain-chroma>=0.1.0",
    "chromadb>=0.4.24",
    "pypdf>=4.0.1",
    "pdf2image>=1.17.0",
    "pytesseract>=0.3.10",
    "python-dotenv>=1.0.1",
    "pandas>=2.3.3",
    "openpyxl>=3.1.2",
    "sentence-transformers>=5.2.0",
    "numpy<2.0",
    "streamlit-image-coordinates>=0.4.0",
    "reportlab>=4.4.7",
    "watchdog>=6.0.0",
    "psycopg2-binary>=2.9.11",
    "opencv-python<4.9",
    "opencv-python-headless<4.9",
    "pymupdf>=1.26.7",
    "streamlit-drawable-canvas>=0.9.3",
]
readme = "README.md"
requires-python = ">= 3.10"

[tool.rye]
managed = true
dev-dependencies = []

[tool.rye.scripts]
start = "rye run python src/legal_system/main.py"
pdf = "rye run streamlit run src/legal_system/tools/coord_tool.py"
exp = "rye run python export_code.py"
````

## File: requirements-dev.lock
````
# generated by rye
# use `rye lock` or `rye sync` to update this lockfile
#
# last locked with the following flags:
#   pre: false
#   features: []
#   all-features: false
#   with-sources: false
#   generate-hashes: false
#   universal: false

-e file:.
aiohappyeyeballs==2.6.1
    # via aiohttp
aiohttp==3.13.2
    # via langchain-community
aiosignal==1.4.0
    # via aiohttp
altair==6.0.0
    # via streamlit
annotated-types==0.7.0
    # via pydantic
anyio==4.12.0
    # via google-genai
    # via httpx
    # via watchfiles
attrs==25.4.0
    # via aiohttp
    # via jsonschema
    # via referencing
backoff==2.2.1
    # via posthog
bcrypt==5.0.0
    # via chromadb
blinker==1.9.0
    # via streamlit
bottleneck==1.6.0
    # via langchain-google-vertexai
build==1.3.0
    # via chromadb
cachetools==6.2.4
    # via streamlit
certifi==2025.11.12
    # via httpcore
    # via httpx
    # via kubernetes
    # via requests
charset-normalizer==3.4.4
    # via reportlab
    # via requests
chromadb==1.4.0
    # via langchain-chroma
    # via legal
click==8.3.1
    # via streamlit
    # via typer
    # via uvicorn
colorama==0.4.6
    # via build
    # via click
    # via tqdm
    # via uvicorn
coloredlogs==15.0.1
    # via onnxruntime
dataclasses-json==0.6.7
    # via langchain-community
distro==1.9.0
    # via google-genai
    # via posthog
docstring-parser==0.17.0
    # via google-cloud-aiplatform
durationpy==0.10
    # via kubernetes
et-xmlfile==2.0.0
    # via openpyxl
filelock==3.20.1
    # via huggingface-hub
    # via torch
    # via transformers
filetype==1.2.0
    # via langchain-google-genai
flatbuffers==25.12.19
    # via onnxruntime
frozenlist==1.8.0
    # via aiohttp
    # via aiosignal
fsspec==2025.12.0
    # via huggingface-hub
    # via torch
gitdb==4.0.12
    # via gitpython
gitpython==3.1.45
    # via streamlit
google-api-core==2.29.0
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
google-auth==2.47.0
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
    # via google-genai
    # via kubernetes
google-cloud-aiplatform==1.133.0
    # via langchain-google-vertexai
    # via legal
google-cloud-bigquery==3.40.0
    # via google-cloud-aiplatform
google-cloud-core==2.5.0
    # via google-cloud-bigquery
    # via google-cloud-storage
google-cloud-resource-manager==1.15.0
    # via google-cloud-aiplatform
google-cloud-storage==3.8.0
    # via google-cloud-aiplatform
    # via langchain-google-vertexai
google-crc32c==1.8.0
    # via google-cloud-storage
    # via google-resumable-media
google-genai==1.56.0
    # via google-cloud-aiplatform
    # via langchain-google-genai
google-resumable-media==2.8.0
    # via google-cloud-bigquery
    # via google-cloud-storage
googleapis-common-protos==1.72.0
    # via google-api-core
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
greenlet==3.3.0
    # via sqlalchemy
grpc-google-iam-v1==0.14.3
    # via google-cloud-resource-manager
grpcio==1.76.0
    # via chromadb
    # via google-api-core
    # via google-cloud-resource-manager
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
grpcio-status==1.76.0
    # via google-api-core
h11==0.16.0
    # via httpcore
    # via uvicorn
httpcore==1.0.9
    # via httpx
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via chromadb
    # via google-genai
    # via langchain-google-vertexai
    # via langgraph-sdk
    # via langsmith
httpx-sse==0.4.3
    # via langchain-community
    # via langchain-google-vertexai
huggingface-hub==0.36.0
    # via langchain-huggingface
    # via sentence-transformers
    # via tokenizers
    # via transformers
humanfriendly==10.0
    # via coloredlogs
idna==3.11
    # via anyio
    # via httpx
    # via requests
    # via yarl
importlib-metadata==8.7.1
    # via opentelemetry-api
importlib-resources==6.5.2
    # via chromadb
jinja2==3.1.6
    # via altair
    # via pydeck
    # via torch
joblib==1.5.3
    # via scikit-learn
jsonpatch==1.33
    # via langchain-core
jsonpointer==3.0.0
    # via jsonpatch
jsonschema==4.25.1
    # via altair
    # via chromadb
jsonschema-specifications==2025.9.1
    # via jsonschema
kubernetes==34.1.0
    # via chromadb
langchain==1.2.0
    # via legal
langchain-chroma==1.1.0
    # via legal
langchain-classic==1.0.1
    # via langchain-community
langchain-community==0.4.1
    # via legal
langchain-core==1.2.5
    # via langchain
    # via langchain-chroma
    # via langchain-classic
    # via langchain-community
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langchain-huggingface
    # via langchain-text-splitters
    # via langgraph
    # via langgraph-checkpoint
    # via langgraph-prebuilt
    # via legal
langchain-google-genai==4.1.2
    # via legal
langchain-google-vertexai==3.2.1
    # via legal
langchain-huggingface==1.2.0
    # via legal
langchain-text-splitters==1.1.0
    # via langchain-classic
langgraph==1.0.5
    # via langchain
langgraph-checkpoint==3.0.1
    # via langgraph
    # via langgraph-prebuilt
langgraph-prebuilt==1.0.5
    # via langgraph
langgraph-sdk==0.3.1
    # via langgraph
langsmith==0.5.2
    # via langchain-classic
    # via langchain-community
    # via langchain-core
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==3.26.2
    # via dataclasses-json
mdurl==0.1.2
    # via markdown-it-py
mmh3==5.2.0
    # via chromadb
mpmath==1.3.0
    # via sympy
multidict==6.7.0
    # via aiohttp
    # via yarl
mypy-extensions==1.1.0
    # via typing-inspect
narwhals==2.14.0
    # via altair
networkx==3.6.1
    # via torch
numexpr==2.14.1
    # via langchain-google-vertexai
numpy==1.26.4
    # via bottleneck
    # via chromadb
    # via langchain-chroma
    # via langchain-community
    # via legal
    # via numexpr
    # via onnxruntime
    # via opencv-python
    # via opencv-python-headless
    # via pandas
    # via pydeck
    # via scikit-learn
    # via scipy
    # via streamlit
    # via streamlit-drawable-canvas
    # via transformers
oauthlib==3.3.1
    # via requests-oauthlib
onnxruntime==1.23.2
    # via chromadb
opencv-python==4.8.1.78
    # via legal
opencv-python-headless==4.8.1.78
    # via legal
openpyxl==3.1.5
    # via legal
opentelemetry-api==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
opentelemetry-exporter-otlp-proto-common==1.39.1
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-otlp-proto-grpc==1.39.1
    # via chromadb
opentelemetry-proto==1.39.1
    # via opentelemetry-exporter-otlp-proto-common
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-sdk==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-semantic-conventions==0.60b1
    # via opentelemetry-sdk
orjson==3.11.5
    # via chromadb
    # via langgraph-sdk
    # via langsmith
ormsgpack==1.12.1
    # via langgraph-checkpoint
overrides==7.7.0
    # via chromadb
packaging==25.0
    # via altair
    # via build
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via huggingface-hub
    # via langchain-core
    # via langsmith
    # via marshmallow
    # via onnxruntime
    # via pytesseract
    # via streamlit
    # via transformers
pandas==2.3.3
    # via legal
    # via streamlit
pdf2image==1.17.0
    # via legal
pillow==12.0.0
    # via pdf2image
    # via pytesseract
    # via reportlab
    # via streamlit
    # via streamlit-drawable-canvas
posthog==5.4.0
    # via chromadb
propcache==0.4.1
    # via aiohttp
    # via yarl
proto-plus==1.27.0
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
protobuf==6.33.2
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via onnxruntime
    # via opentelemetry-proto
    # via proto-plus
    # via streamlit
psycopg2-binary==2.9.11
    # via legal
pyarrow==22.0.0
    # via langchain-google-vertexai
    # via streamlit
pyasn1==0.6.1
    # via pyasn1-modules
    # via rsa
pyasn1-modules==0.4.2
    # via google-auth
pybase64==1.4.3
    # via chromadb
pydantic==2.12.5
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via langchain
    # via langchain-classic
    # via langchain-core
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langgraph
    # via langsmith
    # via pydantic-settings
pydantic-core==2.41.5
    # via pydantic
pydantic-settings==2.12.0
    # via langchain-community
pydeck==0.9.1
    # via streamlit
pygments==2.19.2
    # via rich
pymupdf==1.26.7
    # via legal
pypdf==6.5.0
    # via legal
pypika==0.48.9
    # via chromadb
pyproject-hooks==1.2.0
    # via build
pyreadline3==3.5.4
    # via humanfriendly
pytesseract==0.3.13
    # via legal
python-dateutil==2.9.0.post0
    # via google-cloud-bigquery
    # via kubernetes
    # via pandas
    # via posthog
python-dotenv==1.2.1
    # via legal
    # via pydantic-settings
    # via uvicorn
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via chromadb
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langchain-core
    # via transformers
    # via uvicorn
referencing==0.37.0
    # via jsonschema
    # via jsonschema-specifications
regex==2025.11.3
    # via transformers
reportlab==4.4.7
    # via legal
requests==2.32.5
    # via google-api-core
    # via google-auth
    # via google-cloud-bigquery
    # via google-cloud-storage
    # via google-genai
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langsmith
    # via posthog
    # via requests-oauthlib
    # via requests-toolbelt
    # via streamlit
    # via transformers
requests-oauthlib==2.0.0
    # via kubernetes
requests-toolbelt==1.0.0
    # via langsmith
rich==14.2.0
    # via chromadb
    # via typer
rpds-py==0.30.0
    # via jsonschema
    # via referencing
rsa==4.9.1
    # via google-auth
safetensors==0.7.0
    # via transformers
scikit-learn==1.8.0
    # via sentence-transformers
scipy==1.16.3
    # via scikit-learn
    # via sentence-transformers
sentence-transformers==5.2.0
    # via legal
shellingham==1.5.4
    # via typer
six==1.17.0
    # via kubernetes
    # via posthog
    # via python-dateutil
smmap==5.0.2
    # via gitdb
sniffio==1.3.1
    # via google-genai
sqlalchemy==2.0.45
    # via langchain-classic
    # via langchain-community
streamlit==1.52.2
    # via legal
    # via streamlit-drawable-canvas
    # via streamlit-image-coordinates
streamlit-drawable-canvas==0.9.3
    # via legal
streamlit-image-coordinates==0.4.0
    # via legal
sympy==1.14.0
    # via onnxruntime
    # via torch
tenacity==9.1.2
    # via chromadb
    # via google-genai
    # via langchain-community
    # via langchain-core
    # via streamlit
threadpoolctl==3.6.0
    # via scikit-learn
tokenizers==0.22.1
    # via chromadb
    # via langchain-huggingface
    # via transformers
toml==0.10.2
    # via streamlit
torch==2.2.2
    # via sentence-transformers
tornado==6.5.4
    # via streamlit
tqdm==4.67.1
    # via chromadb
    # via huggingface-hub
    # via sentence-transformers
    # via transformers
transformers==4.57.3
    # via sentence-transformers
typer==0.21.0
    # via chromadb
typing-extensions==4.15.0
    # via aiosignal
    # via altair
    # via anyio
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via grpcio
    # via huggingface-hub
    # via langchain-core
    # via opentelemetry-api
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
    # via pydantic
    # via pydantic-core
    # via referencing
    # via sentence-transformers
    # via sqlalchemy
    # via streamlit
    # via torch
    # via typer
    # via typing-inspect
    # via typing-inspection
typing-inspect==0.9.0
    # via dataclasses-json
typing-inspection==0.4.2
    # via pydantic
    # via pydantic-settings
tzdata==2025.3
    # via pandas
urllib3==2.3.0
    # via kubernetes
    # via requests
uuid-utils==0.12.0
    # via langchain-core
    # via langsmith
uvicorn==0.40.0
    # via chromadb
validators==0.35.0
    # via langchain-google-vertexai
watchdog==6.0.0
    # via legal
    # via streamlit
watchfiles==1.1.1
    # via uvicorn
websocket-client==1.9.0
    # via kubernetes
websockets==15.0.1
    # via google-genai
    # via uvicorn
xxhash==3.6.0
    # via langgraph
yarl==1.22.0
    # via aiohttp
zipp==3.23.0
    # via importlib-metadata
zstandard==0.25.0
    # via langsmith
````

## File: requirements.lock
````
# generated by rye
# use `rye lock` or `rye sync` to update this lockfile
#
# last locked with the following flags:
#   pre: false
#   features: []
#   all-features: false
#   with-sources: false
#   generate-hashes: false
#   universal: false

-e file:.
aiohappyeyeballs==2.6.1
    # via aiohttp
aiohttp==3.13.2
    # via langchain-community
aiosignal==1.4.0
    # via aiohttp
altair==6.0.0
    # via streamlit
annotated-types==0.7.0
    # via pydantic
anyio==4.12.0
    # via google-genai
    # via httpx
    # via watchfiles
attrs==25.4.0
    # via aiohttp
    # via jsonschema
    # via referencing
backoff==2.2.1
    # via posthog
bcrypt==5.0.0
    # via chromadb
blinker==1.9.0
    # via streamlit
bottleneck==1.6.0
    # via langchain-google-vertexai
build==1.3.0
    # via chromadb
cachetools==6.2.4
    # via streamlit
certifi==2025.11.12
    # via httpcore
    # via httpx
    # via kubernetes
    # via requests
charset-normalizer==3.4.4
    # via reportlab
    # via requests
chromadb==1.4.0
    # via langchain-chroma
    # via legal
click==8.3.1
    # via streamlit
    # via typer
    # via uvicorn
colorama==0.4.6
    # via build
    # via click
    # via tqdm
    # via uvicorn
coloredlogs==15.0.1
    # via onnxruntime
dataclasses-json==0.6.7
    # via langchain-community
distro==1.9.0
    # via google-genai
    # via posthog
docstring-parser==0.17.0
    # via google-cloud-aiplatform
durationpy==0.10
    # via kubernetes
et-xmlfile==2.0.0
    # via openpyxl
filelock==3.20.1
    # via huggingface-hub
    # via torch
    # via transformers
filetype==1.2.0
    # via langchain-google-genai
flatbuffers==25.12.19
    # via onnxruntime
frozenlist==1.8.0
    # via aiohttp
    # via aiosignal
fsspec==2025.12.0
    # via huggingface-hub
    # via torch
gitdb==4.0.12
    # via gitpython
gitpython==3.1.45
    # via streamlit
google-api-core==2.29.0
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
google-auth==2.47.0
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via google-cloud-core
    # via google-cloud-resource-manager
    # via google-cloud-storage
    # via google-genai
    # via kubernetes
google-cloud-aiplatform==1.133.0
    # via langchain-google-vertexai
    # via legal
google-cloud-bigquery==3.40.0
    # via google-cloud-aiplatform
google-cloud-core==2.5.0
    # via google-cloud-bigquery
    # via google-cloud-storage
google-cloud-resource-manager==1.15.0
    # via google-cloud-aiplatform
google-cloud-storage==3.8.0
    # via google-cloud-aiplatform
    # via langchain-google-vertexai
google-crc32c==1.8.0
    # via google-cloud-storage
    # via google-resumable-media
google-genai==1.56.0
    # via google-cloud-aiplatform
    # via langchain-google-genai
google-resumable-media==2.8.0
    # via google-cloud-bigquery
    # via google-cloud-storage
googleapis-common-protos==1.72.0
    # via google-api-core
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
greenlet==3.3.0
    # via sqlalchemy
grpc-google-iam-v1==0.14.3
    # via google-cloud-resource-manager
grpcio==1.76.0
    # via chromadb
    # via google-api-core
    # via google-cloud-resource-manager
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via opentelemetry-exporter-otlp-proto-grpc
grpcio-status==1.76.0
    # via google-api-core
h11==0.16.0
    # via httpcore
    # via uvicorn
httpcore==1.0.9
    # via httpx
httptools==0.7.1
    # via uvicorn
httpx==0.28.1
    # via chromadb
    # via google-genai
    # via langchain-google-vertexai
    # via langgraph-sdk
    # via langsmith
httpx-sse==0.4.3
    # via langchain-community
    # via langchain-google-vertexai
huggingface-hub==0.36.0
    # via langchain-huggingface
    # via sentence-transformers
    # via tokenizers
    # via transformers
humanfriendly==10.0
    # via coloredlogs
idna==3.11
    # via anyio
    # via httpx
    # via requests
    # via yarl
importlib-metadata==8.7.1
    # via opentelemetry-api
importlib-resources==6.5.2
    # via chromadb
jinja2==3.1.6
    # via altair
    # via pydeck
    # via torch
joblib==1.5.3
    # via scikit-learn
jsonpatch==1.33
    # via langchain-core
jsonpointer==3.0.0
    # via jsonpatch
jsonschema==4.25.1
    # via altair
    # via chromadb
jsonschema-specifications==2025.9.1
    # via jsonschema
kubernetes==34.1.0
    # via chromadb
langchain==1.2.0
    # via legal
langchain-chroma==1.1.0
    # via legal
langchain-classic==1.0.1
    # via langchain-community
langchain-community==0.4.1
    # via legal
langchain-core==1.2.5
    # via langchain
    # via langchain-chroma
    # via langchain-classic
    # via langchain-community
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langchain-huggingface
    # via langchain-text-splitters
    # via langgraph
    # via langgraph-checkpoint
    # via langgraph-prebuilt
    # via legal
langchain-google-genai==4.1.2
    # via legal
langchain-google-vertexai==3.2.1
    # via legal
langchain-huggingface==1.2.0
    # via legal
langchain-text-splitters==1.1.0
    # via langchain-classic
langgraph==1.0.5
    # via langchain
langgraph-checkpoint==3.0.1
    # via langgraph
    # via langgraph-prebuilt
langgraph-prebuilt==1.0.5
    # via langgraph
langgraph-sdk==0.3.1
    # via langgraph
langsmith==0.5.2
    # via langchain-classic
    # via langchain-community
    # via langchain-core
markdown-it-py==4.0.0
    # via rich
markupsafe==3.0.3
    # via jinja2
marshmallow==3.26.2
    # via dataclasses-json
mdurl==0.1.2
    # via markdown-it-py
mmh3==5.2.0
    # via chromadb
mpmath==1.3.0
    # via sympy
multidict==6.7.0
    # via aiohttp
    # via yarl
mypy-extensions==1.1.0
    # via typing-inspect
narwhals==2.14.0
    # via altair
networkx==3.6.1
    # via torch
numexpr==2.14.1
    # via langchain-google-vertexai
numpy==1.26.4
    # via bottleneck
    # via chromadb
    # via langchain-chroma
    # via langchain-community
    # via legal
    # via numexpr
    # via onnxruntime
    # via opencv-python
    # via opencv-python-headless
    # via pandas
    # via pydeck
    # via scikit-learn
    # via scipy
    # via streamlit
    # via streamlit-drawable-canvas
    # via transformers
oauthlib==3.3.1
    # via requests-oauthlib
onnxruntime==1.23.2
    # via chromadb
opencv-python==4.8.1.78
    # via legal
opencv-python-headless==4.8.1.78
    # via legal
openpyxl==3.1.5
    # via legal
opentelemetry-api==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
opentelemetry-exporter-otlp-proto-common==1.39.1
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-otlp-proto-grpc==1.39.1
    # via chromadb
opentelemetry-proto==1.39.1
    # via opentelemetry-exporter-otlp-proto-common
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-sdk==1.39.1
    # via chromadb
    # via opentelemetry-exporter-otlp-proto-grpc
opentelemetry-semantic-conventions==0.60b1
    # via opentelemetry-sdk
orjson==3.11.5
    # via chromadb
    # via langgraph-sdk
    # via langsmith
ormsgpack==1.12.1
    # via langgraph-checkpoint
overrides==7.7.0
    # via chromadb
packaging==25.0
    # via altair
    # via build
    # via google-cloud-aiplatform
    # via google-cloud-bigquery
    # via huggingface-hub
    # via langchain-core
    # via langsmith
    # via marshmallow
    # via onnxruntime
    # via pytesseract
    # via streamlit
    # via transformers
pandas==2.3.3
    # via legal
    # via streamlit
pdf2image==1.17.0
    # via legal
pillow==12.0.0
    # via pdf2image
    # via pytesseract
    # via reportlab
    # via streamlit
    # via streamlit-drawable-canvas
posthog==5.4.0
    # via chromadb
propcache==0.4.1
    # via aiohttp
    # via yarl
proto-plus==1.27.0
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
protobuf==6.33.2
    # via google-api-core
    # via google-cloud-aiplatform
    # via google-cloud-resource-manager
    # via googleapis-common-protos
    # via grpc-google-iam-v1
    # via grpcio-status
    # via onnxruntime
    # via opentelemetry-proto
    # via proto-plus
    # via streamlit
psycopg2-binary==2.9.11
    # via legal
pyarrow==22.0.0
    # via langchain-google-vertexai
    # via streamlit
pyasn1==0.6.1
    # via pyasn1-modules
    # via rsa
pyasn1-modules==0.4.2
    # via google-auth
pybase64==1.4.3
    # via chromadb
pydantic==2.12.5
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via langchain
    # via langchain-classic
    # via langchain-core
    # via langchain-google-genai
    # via langchain-google-vertexai
    # via langgraph
    # via langsmith
    # via pydantic-settings
pydantic-core==2.41.5
    # via pydantic
pydantic-settings==2.12.0
    # via langchain-community
pydeck==0.9.1
    # via streamlit
pygments==2.19.2
    # via rich
pymupdf==1.26.7
    # via legal
pypdf==6.5.0
    # via legal
pypika==0.48.9
    # via chromadb
pyproject-hooks==1.2.0
    # via build
pyreadline3==3.5.4
    # via humanfriendly
pytesseract==0.3.13
    # via legal
python-dateutil==2.9.0.post0
    # via google-cloud-bigquery
    # via kubernetes
    # via pandas
    # via posthog
python-dotenv==1.2.1
    # via legal
    # via pydantic-settings
    # via uvicorn
pytz==2025.2
    # via pandas
pyyaml==6.0.3
    # via chromadb
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langchain-core
    # via transformers
    # via uvicorn
referencing==0.37.0
    # via jsonschema
    # via jsonschema-specifications
regex==2025.11.3
    # via transformers
reportlab==4.4.7
    # via legal
requests==2.32.5
    # via google-api-core
    # via google-auth
    # via google-cloud-bigquery
    # via google-cloud-storage
    # via google-genai
    # via huggingface-hub
    # via kubernetes
    # via langchain-classic
    # via langchain-community
    # via langsmith
    # via posthog
    # via requests-oauthlib
    # via requests-toolbelt
    # via streamlit
    # via transformers
requests-oauthlib==2.0.0
    # via kubernetes
requests-toolbelt==1.0.0
    # via langsmith
rich==14.2.0
    # via chromadb
    # via typer
rpds-py==0.30.0
    # via jsonschema
    # via referencing
rsa==4.9.1
    # via google-auth
safetensors==0.7.0
    # via transformers
scikit-learn==1.8.0
    # via sentence-transformers
scipy==1.16.3
    # via scikit-learn
    # via sentence-transformers
sentence-transformers==5.2.0
    # via legal
shellingham==1.5.4
    # via typer
six==1.17.0
    # via kubernetes
    # via posthog
    # via python-dateutil
smmap==5.0.2
    # via gitdb
sniffio==1.3.1
    # via google-genai
sqlalchemy==2.0.45
    # via langchain-classic
    # via langchain-community
streamlit==1.52.2
    # via legal
    # via streamlit-drawable-canvas
    # via streamlit-image-coordinates
streamlit-drawable-canvas==0.9.3
    # via legal
streamlit-image-coordinates==0.4.0
    # via legal
sympy==1.14.0
    # via onnxruntime
    # via torch
tenacity==9.1.2
    # via chromadb
    # via google-genai
    # via langchain-community
    # via langchain-core
    # via streamlit
threadpoolctl==3.6.0
    # via scikit-learn
tokenizers==0.22.1
    # via chromadb
    # via langchain-huggingface
    # via transformers
toml==0.10.2
    # via streamlit
torch==2.2.2
    # via sentence-transformers
tornado==6.5.4
    # via streamlit
tqdm==4.67.1
    # via chromadb
    # via huggingface-hub
    # via sentence-transformers
    # via transformers
transformers==4.57.3
    # via sentence-transformers
typer==0.21.0
    # via chromadb
typing-extensions==4.15.0
    # via aiosignal
    # via altair
    # via anyio
    # via chromadb
    # via google-cloud-aiplatform
    # via google-genai
    # via grpcio
    # via huggingface-hub
    # via langchain-core
    # via opentelemetry-api
    # via opentelemetry-exporter-otlp-proto-grpc
    # via opentelemetry-sdk
    # via opentelemetry-semantic-conventions
    # via pydantic
    # via pydantic-core
    # via referencing
    # via sentence-transformers
    # via sqlalchemy
    # via streamlit
    # via torch
    # via typer
    # via typing-inspect
    # via typing-inspection
typing-inspect==0.9.0
    # via dataclasses-json
typing-inspection==0.4.2
    # via pydantic
    # via pydantic-settings
tzdata==2025.3
    # via pandas
urllib3==2.3.0
    # via kubernetes
    # via requests
uuid-utils==0.12.0
    # via langchain-core
    # via langsmith
uvicorn==0.40.0
    # via chromadb
validators==0.35.0
    # via langchain-google-vertexai
watchdog==6.0.0
    # via legal
    # via streamlit
watchfiles==1.1.1
    # via uvicorn
websocket-client==1.9.0
    # via kubernetes
websockets==15.0.1
    # via google-genai
    # via uvicorn
xxhash==3.6.0
    # via langgraph
yarl==1.22.0
    # via aiohttp
zipp==3.23.0
    # via importlib-metadata
zstandard==0.25.0
    # via langsmith
````
