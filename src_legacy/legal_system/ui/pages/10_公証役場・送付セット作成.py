# src/legal_system/ui/pages/10_公証役場・送付セット作成.py

import os
import random
import string
import sys
import tempfile  # ★追加: 一時フォルダ作成用
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

import streamlit as st
from pdf2image import convert_from_bytes

# import pyzipper  <-- 削除またはコメントアウト
from PIL import Image

# ==========================================
# 1. パス解決 & インポート
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# 会社書類テンプレートのパス
TEMPLATES_DIR = os.path.join(ROOT_DIR, "data", "templates")

# ★追加: 暗号化サービスのインポート
from legal_system.services.encryption_service import EncryptionService

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, Deceased

# ページ設定
st.set_page_config(page_title="公証役場連携", page_icon="⚖️", layout="wide")


# セッションステート初期化
if "force_rerun_checkboxes" not in st.session_state:
    st.session_state["force_rerun_checkboxes"] = False

# ==========================================
# 2. ロジッククラス定義
# ==========================================


def _iter_detected_files(detected_files_map: dict[str, list[Path]]) -> Iterable[Path]:
    for _, path_list in detected_files_map.items():
        for p in path_list:
            yield p


def _get_selected_auto_files_from_state(
    detected_files_map: dict[str, list[Path]],
) -> list[Path]:
    selected: list[Path] = []
    for p in _iter_detected_files(detected_files_map):
        key_str = f"auto_{p}"
        if bool(st.session_state.get(key_str, False)):
            selected.append(p)
    return selected


def _get_selected_company_docs_from_state(
    primary_docs: list[str], other_docs: list[str]
) -> list[str]:
    selected: list[str] = []
    for doc in primary_docs:
        key_str = f"chk_{doc}"
        if bool(st.session_state.get(key_str, True)):
            selected.append(doc)
    for doc in other_docs:
        key_str = f"chk_other_{doc}"
        if bool(st.session_state.get(key_str, False)):
            selected.append(doc)
    return selected


class AutoFileCollector:
    """フォルダから関連ファイルを自動収集・分類するクラス"""

    KEYWORDS = {
        "戸籍・住民票・身分証": [
            "戸籍",
            "除籍",
            "住民票",
            "除票",
            "附票",
            "原戸籍",
            "身分証明書",
            "印鑑証明",
            "印鑑登録証明書",
            "マイナンバー",
            "免許証",
            "保険証",
        ],
        "不動産・登記": [
            "不動産",
            "登記",
            "全部事項証明書",
            "名寄",
            "固定資産税",
            "評価証明",
            "公図",
            "測量図",
            "建物図面",
        ],
        "金融資産（通帳・証券）": [
            "通帳",
            "残高証明",
            "証券",
            "取引推移",
            "定期",
            "配当",
            "株式",
        ],
        "遺言_文案": ["文案", "遺言書案", "遺言ドラフト"],
        "遺言_要旨": ["要旨", "遺言概要", "遺言メモ"],
    }

    # 除外キーワード
    EXCLUDE_KEYWORDS = [
        "引継書",
        "通帳のコピー箇所のご説明",
        "試算",
        "委任",
        "約定書",
        "テンプレート",
        "ご案内",
        "送付状",
        "文言説明",
        "仮",
    ]

    @staticmethod
    def collect_files(folder_path: str) -> dict:
        # 各カテゴリとファイル名ごとに最新のファイルを保持する (「遺言_文案」「遺言_要旨」以外)
        category_files_temp = {k: {} for k in AutoFileCollector.KEYWORDS.keys()}

        latest_will_draft = None
        latest_will_draft_mtime = 0

        latest_will_summary = None
        latest_will_summary_mtime = 0

        if not folder_path or not os.path.exists(folder_path):
            return {}

        try:
            root_path_in_collector = Path(folder_path)
            for p in root_path_in_collector.rglob("*"):
                if p.is_file():
                    if p.name.startswith("~$") or p.name.startswith("."):
                        continue
                    if p.suffix.lower() not in [
                        ".pdf",
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".docx",
                        ".doc",
                        ".xlsx",
                        ".xls",
                    ]:
                        continue

                    if any(ex in p.name for ex in AutoFileCollector.EXCLUDE_KEYWORDS):
                        continue

                    current_mtime = os.path.getmtime(p)

                    # 遺言_文案の処理: 全ての文案ファイルの中から最新のもの1つだけを選択
                    if any(
                        k in p.name
                        for k in AutoFileCollector.KEYWORDS.get("遺言_文案", [])
                    ):
                        if current_mtime > latest_will_draft_mtime:
                            latest_will_draft = p
                            latest_will_draft_mtime = current_mtime
                        continue  # このファイルは処理済みなので次へ

                    # 遺言_要旨の処理: 全ての要旨ファイルの中から最新のもの1つだけを選択
                    if any(
                        k in p.name
                        for k in AutoFileCollector.KEYWORDS.get("遺言_要旨", [])
                    ):
                        if current_mtime > latest_will_summary_mtime:
                            latest_will_summary = p
                            latest_will_summary_mtime = current_mtime
                        continue  # このファイルは処理済みなので次へ

                    # それ以外のカテゴリの処理 (既存ロジック: ファイル名ごとに最新を保持)
                    matched_category = None
                    for category, keywords in AutoFileCollector.KEYWORDS.items():
                        # 「遺言_文案」と「遺言_要旨」は既に上で処理されているため、ここではスキップ
                        if category not in ["遺言_文案", "遺言_要旨"]:
                            if any(k in p.name for k in keywords):
                                matched_category = category
                                break

                    if matched_category:
                        file_name = p.name
                        # 既に同じファイル名のファイルが登録されているかチェックし、更新日時が新しい方を採用
                        if file_name not in category_files_temp[
                            matched_category
                        ] or current_mtime > os.path.getmtime(
                            category_files_temp[matched_category][file_name]
                        ):
                            category_files_temp[matched_category][file_name] = p

            # category_files_temp と最新の遺言ファイルから最終的な結果を構築
            results = {}
            if latest_will_draft:
                results["遺言_文案"] = [latest_will_draft]
            if latest_will_summary:
                results["遺言_要旨"] = [latest_will_summary]

            for category, files_dict in category_files_temp.items():
                if (
                    category not in ["遺言_文案", "遺言_要旨"] and files_dict
                ):  # 遺言系カテゴリは既に処理済み
                    results[category] = list(files_dict.values())

        except Exception as e:
            print(f"ファイル収集エラー: {e}")  # エラーをログに出力
            pass
        return {k: v for k, v in results.items() if v}


class DocumentProcessor:
    """ドキュメントの軽量化処理を行うクラス"""

    @staticmethod
    def convert_to_monochrome_pdf(
        file_bytes: bytes, file_name: str, strong_compression: bool = False
    ) -> bytes:
        original_size = len(file_bytes)
        dpi = 100 if strong_compression else 150
        quality = 50 if strong_compression else 75

        images = []
        if file_name.lower().endswith(".pdf"):
            try:
                images = convert_from_bytes(file_bytes, dpi=dpi, grayscale=True)
            except Exception:
                return file_bytes
        else:
            try:
                img = Image.open(BytesIO(file_bytes)).convert("L")
                images = [img]
            except Exception:
                return file_bytes

        if not images:
            return file_bytes

        output = BytesIO()
        try:
            images[0].save(
                output,
                "PDF",
                resolution=float(dpi),
                save_all=True,
                append_images=images[1:],
                optimize=True,
                quality=quality,
            )
            processed_data = output.getvalue()
            if len(processed_data) >= original_size:
                return file_bytes
            return processed_data
        except Exception:
            return file_bytes


class ZipManager:
    """暗号化ZIP作成クラス (分割対応・7-Zip版)"""

    @staticmethod
    def create_split_encrypted_zips(
        files: dict, password: str, max_mb: int = 20
    ) -> list:
        zip_list = []
        current_zip_files = {}
        current_size = 0
        current_vol = 1
        limit_bytes = max_mb * 1024 * 1024
        filenames = list(files.keys())

        for fname in filenames:
            data = files[fname]
            size = len(data)

            if (current_size + size > limit_bytes) and (len(current_zip_files) > 0):
                zip_bytes = ZipManager._make_zip_bytes(current_zip_files, password)
                zip_list.append(
                    {
                        "name": f"送付資料_Vol{current_vol}.zip",
                        "data": zip_bytes,
                        "files": list(current_zip_files.keys()),
                    }
                )
                current_vol += 1
                current_zip_files = {}
                current_size = 0

            current_zip_files[fname] = data
            current_size += size

        if current_zip_files:
            zip_bytes = ZipManager._make_zip_bytes(current_zip_files, password)
            name = (
                f"送付資料_Vol{current_vol}.zip"
                if current_vol > 1
                else "送付資料一式.zip"
            )
            zip_list.append(
                {
                    "name": name,
                    "data": zip_bytes,
                    "files": list(current_zip_files.keys()),
                }
            )
        return zip_list

    @staticmethod
    def _make_zip_bytes(files_dict, password) -> bytes:
        """
        7za.exe を使用して、ZipCrypto方式(Windows標準機能互換)の暗号化ZIPを作成する。
        """
        # 一時ディレクトリを作成して作業する
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_paths_for_7z = []

            # 1. メモリ上のデータを一時ファイルとして書き出す
            for fname, fdata in files_dict.items():
                # ファイル名の安全化
                safe_name = os.path.basename(fname)
                file_path = os.path.join(tmp_dir, safe_name)

                with open(file_path, "wb") as f:
                    f.write(fdata)

                file_paths_for_7z.append(file_path)

            # 2. 出力先のZIPパス
            output_zip_path = os.path.join(tmp_dir, "output.zip")

            # 3. 7za.exe を呼び出してZIP作成
            try:
                EncryptionService.create_encrypted_zip(
                    file_paths_for_7z, output_zip_path, password
                )
            except FileNotFoundError:
                st.error(
                    "【構成エラー】7za.exe が見つかりません。システム管理者に連絡してください。"
                )
                return b""
            except Exception as e:
                st.error(f"ZIP作成エラー: {e}")
                return b""

            # 4. 作成されたZIPをバイト列として読み込む
            if os.path.exists(output_zip_path):
                with open(output_zip_path, "rb") as f:
                    zip_bytes = f.read()
                return zip_bytes
            else:
                return b""


class EmailGenerator:
    """公証役場向けメール生成"""

    @staticmethod
    def generate_drafts_split(
        case, notary_name: str, password: str, zip_list: list, user_name: str
    ):
        # 遺言者名の取得 (安全な取得ロジック)
        d_name = ""
        if case.deceased_ref:
            d_name = (
                f"{case.deceased_ref.name_last} {case.deceased_ref.name_first}".strip()
            )

        # 被相続人がいない場合はクライアント名(契約者)を使用
        if not d_name or d_name == "未登録":
            contractor = None
            if case.deceased_ref and case.deceased_ref.heirs:
                contractor = next(
                    (h for h in case.deceased_ref.heirs if h.is_contracting_party), None
                )

            if contractor:
                d_name = f"{contractor.name_last} {contractor.name_first}".strip()
            else:
                d_name = (
                    case.client_name.strip() if case.client_name else "（名称不明）"
                )

        total_vols = len(zip_list)
        drafts = []

        # 1. ファイル送付メール
        for i, z_info in enumerate(zip_list):
            vol_num = i + 1

            subject_base = f"【新規依頼】公正証書遺言作成のご依頼（遺言者：{d_name}様）／行政書士法人チェスター{user_name}"
            if total_vols > 1:
                subject = f"{subject_base}（{vol_num}/{total_vols}）"
            else:
                subject = subject_base

            files_str = "\n".join([f"・{f}" for f in z_info["files"]])

            body = """{notary_name}　御中

いつも大変お世話になっております。
行政書士法人チェスターの{user_name}でございます。

この度、弊社クライアントの公正証書遺言作成につきまして、次の通り作成依頼をいたしたく、必要書類を添付にて送付申し上げます。
{file_capacity_note}

お忙しいところ恐縮ですが、内容のご確認と今後の段取りについてご教示いただけますと幸いです。

【案件概要】
遺言者氏名： {d_name}
嘱託の種類： 公正証書遺言
証人の手配： 1名依頼いたします。（もう1名は私、{user_name}がお伺いいたします。）
作成希望場所：{notary_name}

【添付書類 ({zip_name})】
{files_str}

個人情報保護のため、ファイルにはパスワードを設定しております。パスワードは後ほど別メールにてお送りいたします。
※ZIPファイルはWindows標準機能で解凍可能です。

何卒よろしくお願い申し上げます。""".format(
                notary_name=notary_name,
                user_name=user_name,
                file_capacity_note=(
                    "※ファイル容量の関係で、"
                    + str(total_vols)
                    + "通に分けてお送りいたします。本メールはその"
                    + str(vol_num)
                    + "通目です。"
                )
                if total_vols > 1
                else "",
                d_name=d_name,
                zip_name=z_info["name"],
                files_str=files_str,
            )
            drafts.append(
                {
                    "subject": subject,
                    "body": body,
                    "type": "file",
                    "zip_name": z_info["name"],
                }
            )

        # 2. パスワード通知メール
        pass_subject = f"【パスワード送付】公正証書遺言作成のご依頼/ 遺言者：{d_name}様"

        pass_body = """{notary_name}　御中

いつも大変お世話になっております。
行政書士法人チェスターの{user_name}でございます。

先ほどお送りいたしました添付ファイルのパスワードをご案内いたします。
{file_common_pass_note}

パスワード：{password}

お手数をおかけいたしますが、ご査収のほどよろしくお願い申し上げます。""".format(
            notary_name=notary_name,
            user_name=user_name,
            file_common_pass_note=("（全ファイル共通です）") if total_vols > 1 else "",
            password=password,
        )
        drafts.append({"subject": pass_subject, "body": pass_body, "type": "pass"})
        return drafts


# ==========================================
# 3. メイン画面 UI
# ==========================================
def main():

    # コールバックからの強制再実行トリガー
    if st.session_state.get("force_rerun_checkboxes", False):
        st.session_state["force_rerun_checkboxes"] = False
        st.rerun()
    st.title("⚖️ 公証役場連携・送付セット作成")
    st.caption(
        "フォルダからの自動ファイル収集、軽量化、暗号化(Windows互換)、分割ZIP作成を一括で行います。"
    )

    db = DatabaseManager()
    session = db._get_session()

    current_user_info = db.get_current_user_info()
    user_name = current_user_info["name"]

    # 1. 案件選択
    target_case_id = st.session_state.get("selected_case_id")
    if not target_case_id:
        st.warning(
            "⚠️ 案件が選択されていません。サイドバーまたはHomeから選択してください。"
        )
        return

    current_case = (
        session.query(Case)
        .options(joinedload(Case.deceased_ref).joinedload(Deceased.heirs))
        .get(target_case_id)
    )

    d_name_display = "未登録"
    if current_case.deceased_ref:
        d_name_display = f"{current_case.deceased_ref.name_last} {current_case.deceased_ref.name_first}"

    st.success(
        f"📂 対象案件: **{current_case.client_name}** 様 (被相続人: {d_name_display})"
    )

    st.divider()

    col_L, col_R = st.columns([1, 1.2])

    # --- 左カラム: ファイル選択 & 設定 ---
    with col_L:
        st.subheader("1. 送付資料の準備")

        # 全選択/全解除ボタン
        col_chk_all, col_chk_none = st.columns(2)
        # Placeholders for lists, filled later in the script
        # These lists need to be populated *before* the buttons are clicked
        # to correctly update session state for all checkboxes.
        if "all_detected_files_keys" not in st.session_state:
            st.session_state["all_detected_files_keys"] = []
        if "all_company_docs_keys" not in st.session_state:
            st.session_state["all_company_docs_keys"] = []
        if "all_other_docs_keys" not in st.session_state:
            st.session_state["all_other_docs_keys"] = []

        def update_all_checkbox_states(target_state):
            for key in st.session_state["all_detected_files_keys"]:
                st.session_state[key] = target_state
            for key in st.session_state["all_company_docs_keys"]:
                st.session_state[key] = target_state
            for key in st.session_state["all_other_docs_keys"]:
                st.session_state[key] = target_state
            st.toast(
                f"全てのチェックボックスを{'選択' if target_state else '解除'}しました。"
            )
            st.session_state["force_rerun_checkboxes"] = True

        if col_chk_all.button(
            "✅ 全て選択",
            use_container_width=True,
            on_click=update_all_checkbox_states,
            args=(True,),
        ):
            pass  # Handled by on_click
        if col_chk_none.button(
            "⬜ 全て解除",
            use_container_width=True,
            on_click=update_all_checkbox_states,
            args=(False,),
        ):
            pass  # Handled by on_click

        st.markdown("--- # ① フォルダから自動検出されたファイル")
        # === A. フォルダ自動収集機能 ===
        st.markdown("###### ① フォルダから自動検出されたファイル")
        case_folder_path = current_case.folder_path

        detected_files_map: dict[str, list[Path]] = {}
        if case_folder_path and os.path.exists(case_folder_path):
            root_path = Path(case_folder_path)
            st.caption(f"検索先: `{case_folder_path}`")
            detected_files_map = AutoFileCollector.collect_files(case_folder_path)

            if not detected_files_map:
                st.info("関連しそうなファイルは見つかりませんでした。")

            st.session_state["all_detected_files_keys"] = []
            for category, path_list in detected_files_map.items():
                with st.expander(f"📁 {category} ({len(path_list)}件)", expanded=True):
                    for p in path_list:
                        relative_path_display = (
                            p.relative_to(root_path)
                            if p.is_relative_to(root_path)
                            else Path(p.name)
                        )
                        label = (
                            f"{p.name} ({relative_path_display.parent})"
                            if relative_path_display.parent != Path(".")
                            else p.name
                        )

                        key_str = f"auto_{p}"
                        st.session_state["all_detected_files_keys"].append(key_str)
                        if st.checkbox(
                            label,
                            value=st.session_state.get(key_str, False),
                            key=key_str,
                        ):
                            pass

        else:
            st.warning(
                "⚠️ 案件フォルダパスが登録されていないか、アクセスできません。Home画面で設定してください。"
            )
            st.session_state["all_detected_files_keys"] = []

        # === B. 手動アップロード ===
        st.markdown("###### ② 手動追加（フォルダにない場合）")
        uploaded_files = st.file_uploader(
            "ファイルを選択",
            type=["pdf", "png", "jpg", "jpeg", "docx", "doc", "xlsx", "xls"],
            accept_multiple_files=True,
        )
        uploaded_files_list: list[Any] = uploaded_files or []

        use_strong_compression = st.checkbox(
            "🔥 強力圧縮 (画質を落としてサイズ優先)", value=False
        )

        # === C. 会社書類・身分証の自動同梱 ===
        st.markdown("###### ③ 会社書類・身分証の同梱")
        company_docs_selected: list[str] = []
        if os.path.exists(TEMPLATES_DIR):
            all_templates = [
                f for f in os.listdir(TEMPLATES_DIR) if f.lower().endswith(".pdf")
            ]
            clean_user_name = user_name.replace(" ", "").replace("　", "")

            primary_docs: list[str] = []
            other_docs: list[str] = []

            for tpl in all_templates:
                clean_tpl = tpl.replace(" ", "").replace("　", "")
                is_target = False
                if "履歴事項全部証明書" in clean_tpl:
                    is_target = True
                elif "行政書士証票" in clean_tpl and clean_user_name in clean_tpl:
                    is_target = True
                elif "免許証" in clean_tpl and clean_user_name in clean_tpl:
                    is_target = True

                if is_target:
                    primary_docs.append(tpl)
                else:
                    other_docs.append(tpl)

            st.session_state["all_company_docs_keys"] = []
            for doc in primary_docs:
                key_str = f"chk_{doc}"
                st.session_state["all_company_docs_keys"].append(key_str)
                if st.checkbox(
                    f"📄 {doc}", value=st.session_state.get(key_str, True), key=key_str
                ):
                    pass

            with st.expander("その他のファイルを選択"):
                st.session_state["all_other_docs_keys"] = []
                for doc in other_docs:
                    key_str = f"chk_other_{doc}"
                    st.session_state["all_other_docs_keys"].append(key_str)
                    if st.checkbox(
                        f"📄 {doc}",
                        value=st.session_state.get(key_str, False),
                        key=key_str,
                    ):
                        pass
        else:
            st.warning("テンプレートフォルダなし")
            st.session_state["all_company_docs_keys"] = []
            st.session_state["all_other_docs_keys"] = []
            primary_docs = []
            other_docs = []

        # === D. 設定 ===
        st.markdown("###### ④ 送付設定")
        notary_name = st.text_input("公証役場名", placeholder="例: 京橋公証役場")

        if "zip_password" not in st.session_state:
            chars = string.ascii_letters + string.digits
            st.session_state["zip_password"] = "".join(
                random.choice(chars) for _ in range(10)
            )

        password = st.text_input(
            "ZIPパスワード", value=st.session_state["zip_password"]
        )
        if st.button("パスワード再生成"):
            chars = string.ascii_letters + string.digits
            st.session_state["zip_password"] = "".join(
                random.choice(chars) for _ in range(10)
            )
            st.rerun()

        st.markdown("---")

        # 実行ボタン
        if st.button(
            "🚀 送付セットを作成する", type="primary", use_container_width=True
        ):
            # ボタン押下時点のチェック状態を、session_stateから確定させる
            # （描画時に作った一時リストが古い状態のまま混入するのを防ぐ）
            selected_auto_files = _get_selected_auto_files_from_state(
                detected_files_map
            )
            company_docs_selected = _get_selected_company_docs_from_state(
                primary_docs, other_docs
            )

            if (
                not uploaded_files_list
                and not company_docs_selected
                and not selected_auto_files
            ):
                st.error("ファイルが1つも選択されていません。")
            else:
                progress_text = "処理中..."
                my_bar = st.progress(0, text=progress_text)

                files_to_zip: dict[str, bytes] = {}
                processor = DocumentProcessor()

                total_files = (
                    len(uploaded_files_list)
                    + len(company_docs_selected)
                    + len(selected_auto_files)
                )
                processed_cnt = 0

                # 1. 自動収集ファイルの読み込み & 軽量化
                for p in selected_auto_files:
                    try:
                        with open(p, "rb") as f:
                            bytes_data = f.read()

                        fname = p.name
                        fname_lower = fname.lower()

                        if fname_lower.endswith((".pdf", ".png", ".jpg", ".jpeg")):
                            optimized_bytes = processor.convert_to_monochrome_pdf(
                                bytes_data,
                                fname,
                                strong_compression=use_strong_compression,
                            )
                            base_name = os.path.splitext(fname)[0]
                            final_name = f"{base_name}.pdf"
                            files_to_zip[final_name] = optimized_bytes
                        else:
                            files_to_zip[fname] = bytes_data

                    except Exception as e:
                        st.error(f"ファイル読込エラー ({p.name}): {e}")

                    processed_cnt += 1
                    my_bar.progress(
                        processed_cnt / total_files, text=f"処理中: {p.name}"
                    )

                # 2. 手動アップロードファイルの処理
                for f in uploaded_files_list:
                    bytes_data = f.getvalue()
                    fname_lower = f.name.lower()

                    if fname_lower.endswith((".pdf", ".png", ".jpg", ".jpeg")):
                        optimized_bytes = processor.convert_to_monochrome_pdf(
                            bytes_data,
                            f.name,
                            strong_compression=use_strong_compression,
                        )
                        base_name = os.path.splitext(f.name)[0]
                        final_name = f"{base_name}.pdf"
                        files_to_zip[final_name] = optimized_bytes
                    else:
                        files_to_zip[f.name] = bytes_data

                    processed_cnt += 1
                    my_bar.progress(
                        processed_cnt / total_files, text=f"処理中: {f.name}"
                    )

                # 3. 会社書類の読み込み
                for doc_name in company_docs_selected:
                    path = os.path.join(TEMPLATES_DIR, doc_name)
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            files_to_zip[doc_name] = f.read()
                    processed_cnt += 1
                    my_bar.progress(
                        processed_cnt / total_files, text=f"同梱中: {doc_name}"
                    )

                # 4. 分割ZIP作成 (20MB制限)
                my_bar.progress(0.9, text="Windows互換ZIP作成中 (7-Zip)...")

                # ★修正: ここで7za.exeを使ったZipManagerを呼び出す
                zip_list = ZipManager.create_split_encrypted_zips(
                    files_to_zip, password, max_mb=20
                )

                # 5. メール生成
                drafts = EmailGenerator.generate_drafts_split(
                    current_case, notary_name, password, zip_list, user_name
                )

                st.session_state["zip_list"] = zip_list
                st.session_state["email_drafts"] = drafts

                # 自動保存処理 (案件フォルダへ)
                if case_folder_path and os.path.exists(case_folder_path):
                    try:
                        for z in zip_list:
                            save_path = os.path.join(case_folder_path, z["name"])
                            with open(save_path, "wb") as f:
                                f.write(z["data"])
                        st.success(
                            f"✅ ZIPファイルを案件フォルダに保存しました: {case_folder_path}"
                        )
                    except Exception as e:
                        st.warning(f"案件フォルダへの自動保存に失敗しました: {e}")

                my_bar.empty()
                st.success("作成完了！ 下にスクロールしてご確認ください 👇")

    # --- 右カラム: 結果表示 ---
    with col_R:
        st.subheader("2. 生成物ダウンロード")

        if "zip_list" in st.session_state:
            zip_list = st.session_state["zip_list"]
            drafts = st.session_state["email_drafts"]

            st.markdown("##### 📦 送付ファイル (パスワード付)")
            st.caption("※Windows標準機能で解凍可能")

            for i, z_info in enumerate(zip_list):
                col_z1, col_z2 = st.columns([3, 1])
                col_z1.write(
                    f"**{z_info['name']}** ({len(z_info['data']) / 1024 / 1024:.1f} MB)"
                )
                with col_z2:
                    st.download_button(
                        label="📥 DL",
                        data=z_info["data"],
                        file_name=z_info["name"],
                        mime="application/zip",
                        key=f"dl_zip_{i}",
                        type="primary",
                    )
                with st.expander("含まれるファイル"):
                    for inner_f in z_info["files"]:
                        st.caption(f"- {inner_f}")

            st.caption(f"パスワード: `{password}`")
            st.divider()

            st.markdown("##### 📧 メール下書き")
            tabs = st.tabs([f"通番 {i + 1}" for i in range(len(drafts))])

            for i, draft in enumerate(drafts):
                with tabs[i]:
                    label = (
                        "📎 ファイル送付"
                        if draft["type"] == "file"
                        else "🔑 パスワード通知"
                    )
                    st.info(label)

                    st.text_input("件名", value=draft["subject"], key=f"subj_{i}")
                    # コピーしやすいUI
                    st.code(draft["body"], language="text")

                    with st.expander("本文を編集する"):
                        new_body = st.text_area(
                            "本文編集", value=draft["body"], height=300, key=f"body_{i}"
                        )
                        if new_body != draft["body"]:
                            draft["body"] = new_body
                            st.rerun()

        else:
            st.info("👈 左側で設定を行い、「送付セットを作成する」を押してください。")
            st.markdown("""
            **特徴:**
            - **自動収集**: 案件フォルダから戸籍や登記情報を自動検出します。
            - **Windows互換**: 7-Zipエンジンを使用し、公証役場のPCでも標準機能で開けるZIPを作成します。
            - **容量対策**: 20MB制限を超える場合は自動分割します。
            - **自動保存**: 作成されたZIPは案件フォルダにも保存されます。
            """)

    session.close()


if __name__ == "__main__":
    main()
