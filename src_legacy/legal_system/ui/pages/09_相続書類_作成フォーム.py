# src/legal_system/ui/pages/09_相続書類_作成フォーム.py

import os
import sys
from io import BytesIO

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import black, red
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from sqlalchemy.orm import joinedload

# パス解決
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR)))
)
sys.path.append(ROOT_DIR)

from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Case,
    Deceased,
    FileRegistry,
    FinancialAsset,  # 追加
    H_AddressHistory,
    Heir,
    RealEstateAsset,  # 追加
)
from legal_system.utils.date_utils import convert_seireki_to_wareki  # 和暦変換用

# フォント設定 (変更なし)
FONT_PATH = os.path.join(ROOT_DIR, "data", "fonts", "ipaexg.ttf")
try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont("IPAexG", FONT_PATH))
except Exception:
    pass

st.set_page_config(page_title="書類作成 | 相続業務支援", page_icon="📄", layout="wide")


# ==========================================
# ★改良: データ置換ロジック (資産コンテキスト対応)
# ==========================================
def create_replacement_map(case_data, target_asset=None):
    """
    プレースホルダと実際の値のマッピングを作成する。
    target_asset: FinancialAsset または RealEstateAsset のインスタンス (任意)
    """
    map_dict = {}

    # 1. 案件基本情報
    map_dict["{case_number}"] = case_data.case_number
    map_dict["{client_name}"] = case_data.client_name

    # 2. 被相続人情報
    if case_data.deceased_ref:
        d = case_data.deceased_ref
        full_name = f"{d.name_last} {d.name_first}".strip()
        map_dict["{deceased_name}"] = full_name
        map_dict["{deceased_name_last}"] = d.name_last or ""
        map_dict["{deceased_name_first}"] = d.name_first or ""
        map_dict["{deceased_hometown}"] = d.hometown or ""

        # 生年月日
        if d.date_of_birth:
            map_dict["{deceased_birthday}"] = convert_seireki_to_wareki(d.date_of_birth)

        # 死亡日
        if d.date_of_death:
            map_dict["{death_date}"] = convert_seireki_to_wareki(d.date_of_death)
            map_dict["{death_year_seireki}"] = str(d.date_of_death.year)
            map_dict["{death_month}"] = str(d.date_of_death.month)
            map_dict["{death_day}"] = str(d.date_of_death.day)

            # 和暦年 (例: 昭和30) ※数字だけでなく元号含む
            dt = d.date_of_death
            if dt.year >= 2019:
                wareki_year = f"令和{dt.year - 2018}"
                if dt.year == 2019 and dt.month <= 4:
                    wareki_year = "平成31"  # 厳密な分岐が必要なら
            elif dt.year >= 1989:
                wareki_year = f"平成{dt.year - 1988}"
            elif dt.year >= 1926:
                wareki_year = f"昭和{dt.year - 1925}"
            elif dt.year >= 1912:
                wareki_year = f"大正{dt.year - 1911}"
            else:
                wareki_year = f"明治{dt.year - 1868}"

            # "令和1" を "令和元" にするかはお好みで調整
            if "令和1" in wareki_year and len(wareki_year) == 3:
                wareki_year = "令和元"

            map_dict["{death_year_wareki}"] = wareki_year

        # 最後の住所
        d_addr_str = ""
        if d.last_address:
            a = d.last_address
            d_addr_str = f"{a.prefecture}{a.city_ward_town}{a.street_address} {a.building_name or ''}".strip()
        map_dict["{deceased_address}"] = d_addr_str

    # 3. 相続人情報 (契約者を優先)
    heir = None
    if case_data.deceased_ref and case_data.deceased_ref.heirs:
        for h in case_data.deceased_ref.heirs:
            if h.is_contracting_party:
                heir = h
                break
        if not heir:
            heir = case_data.deceased_ref.heirs[0]

    if heir:
        full_name_h = f"{heir.name_last} {heir.name_first}".strip()
        map_dict["{heir_name}"] = full_name_h
        map_dict["{heir_name_last}"] = heir.name_last or ""
        map_dict["{heir_name_first}"] = heir.name_first or ""
        map_dict["{heir_rel}"] = heir.relationship_type or ""

        # ★追加: 生年月日の詳細分解ロジック
        if heir.date_of_birth:
            # 1. 和暦全 (例: 昭和30年1月1日)
            map_dict["{heir_birthday}"] = convert_seireki_to_wareki(heir.date_of_birth)

            # 2. 西暦年 (例: 1955)
            map_dict["{heir_birthday_year_seireki}"] = str(heir.date_of_birth.year)

            # 3. 和暦年 (例: 昭和30) ※数字だけでなく元号含む
            dt = heir.date_of_birth
            if dt.year >= 2019:
                wareki_year = f"令和{dt.year - 2018}"
                if dt.year == 2019 and dt.month <= 4:
                    wareki_year = "平成31"  # 厳密な分岐が必要なら
            elif dt.year >= 1989:
                wareki_year = f"平成{dt.year - 1988}"
            elif dt.year >= 1926:
                wareki_year = f"昭和{dt.year - 1925}"
            elif dt.year >= 1912:
                wareki_year = f"大正{dt.year - 1911}"
            else:
                wareki_year = f"明治{dt.year - 1868}"

            # "令和1" を "令和元" にするかはお好みで調整
            if "令和1" in wareki_year and len(wareki_year) == 3:
                wareki_year = "令和元"

            map_dict["{heir_birthday_year_wareki}"] = wareki_year

            # 4. 月・日
            map_dict["{heir_birthday_month}"] = str(dt.month)
            map_dict["{heir_birthday_day}"] = str(dt.day)

        # 住所
        addr_str = "（住所未登録）"
        pref, city, street, bldg = "", "", "", ""
        if heir.address_links:
            for link in heir.address_links:
                if link.is_current_address and link.address:
                    a = link.address
                    pref = a.prefecture or ""
                    city = a.city_ward_town or ""
                    street = a.street_address or ""
                    bldg = a.building_name or ""
                    addr_str = f"{pref}{city}{street} {bldg}".strip()
                    break

        map_dict["{heir_address}"] = addr_str
        map_dict["{heir_pref}"] = pref
        map_dict["{heir_city}"] = city
        map_dict["{heir_street}"] = street
        map_dict["{heir_building}"] = bldg

    # 4. ★追加: 対象資産情報 (コンテキスト)
    if target_asset:
        # 金融資産の場合
        if isinstance(target_asset, FinancialAsset):
            bank_name = target_asset.bank_ref.bank_name if target_asset.bank_ref else ""
            branch_name = (
                target_asset.branch_ref.branch_name if target_asset.branch_ref else ""
            )
            acc_type = (
                target_asset.account_type_ref.type_name
                if target_asset.account_type_ref
                else "普通"
            )

            map_dict["{bank_name}"] = bank_name
            map_dict["{branch_name}"] = branch_name
            map_dict["{account_type}"] = acc_type
            map_dict["{account_number}"] = target_asset.account_number or ""
            map_dict["{balance}"] = (
                f"{target_asset.balance:,.0f}" if target_asset.balance else "0"
            )
            # 口座名義人がもしAssetにあれば(現状はDeceased名が一般的だが、名寄せOCR結果等を使うならここ)
            map_dict["{account_holder}"] = (
                f"{d.name_last} {d.name_first}"  # 仮: 被相続人名
            )

        # 不動産資産の場合
        elif isinstance(target_asset, RealEstateAsset):
            map_dict["{prop_location}"] = target_asset.location or ""
            map_dict["{prop_number}"] = (
                target_asset.lot_number or target_asset.house_number or ""
            )
            map_dict["{prop_category}"] = (
                target_asset.land_category or target_asset.structure or ""
            )
            map_dict["{prop_area}"] = str(
                target_asset.land_area or target_asset.floor_area or ""
            )

    return map_dict


def generate_pdf(template_path, coords, replacement_map):
    # (変更なし: 既存のロジックをそのまま使用)
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
                    # 辞書から置換。なければ元の値をそのまま使う(固定文字など)
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

    # 1. 案件選択 (Home共有)
    target_case_id = st.session_state.get("selected_case_id")

    if not target_case_id:
        # 未選択時の選択UI
        st.warning("⚠️ 案件が選択されていません。")
        with st.expander("案件を選択する", expanded=True):
            cases = session.query(Case).all()
            opts = {f"{c.case_number}: {c.client_name}": c.case_id for c in cases}
            sel = st.selectbox("案件リスト", list(opts.keys()))
            if st.button("選択"):
                st.session_state["selected_case_id"] = opts[sel]
                st.rerun()
        return

    # データ一括ロード (FinancialAsset, RealEstateAsset も含める)
    target_case = (
        session.query(Case)
        .options(
            joinedload(Case.deceased_ref)
            .joinedload(Deceased.heirs)
            .joinedload(Heir.address_links)
            .joinedload(H_AddressHistory.address),
            joinedload(Case.deceased_ref).joinedload(Deceased.last_address),
            joinedload(Case.financial_assets).joinedload(FinancialAsset.bank_ref),
            joinedload(Case.financial_assets).joinedload(FinancialAsset.branch_ref),
            joinedload(Case.financial_assets).joinedload(
                FinancialAsset.account_type_ref
            ),
            joinedload(Case.real_estates),
        )
        .get(target_case_id)
    )

    if not target_case:
        st.error("案件情報の取得に失敗しました。")
        return

    d_name = (
        target_case.deceased_ref.name_last + " " + target_case.deceased_ref.name_first
        if target_case.deceased_ref
        else "未登録"
    )
    st.success(
        f"📂 対象案件: **{target_case.case_number} {target_case.client_name}** 様 (被相続人: {d_name})"
    )

    st.divider()

    # ------------------------------------
    # 2. 対象資産の選択 (Context Selection)
    # ------------------------------------
    col_asset, col_tpl = st.columns([1, 1])

    target_asset = None
    asset_description = "（資産指定なし）"

    with col_asset:
        st.markdown("##### 1. 対象資産を選択 (任意)")
        st.caption(
            "銀行の請求書など、特定の資産に関する書類を作る場合に選択してください。"
        )

        # 資産リストの作成
        asset_options = {"指定なし (基本情報のみ)": None}

        # 預貯金
        if target_case.financial_assets:
            for fa in target_case.financial_assets:
                b_name = fa.bank_ref.bank_name if fa.bank_ref else "不明銀行"
                br_name = fa.branch_ref.branch_name if fa.branch_ref else ""
                label = f"🏦 {b_name} {br_name} ({fa.account_number})"
                asset_options[label] = fa

        # 不動産
        if target_case.real_estates:
            for re_asset in target_case.real_estates:
                loc = (
                    re_asset.location
                    if len(re_asset.location or "") < 10
                    else (re_asset.location[:10] + "...")
                )
                label = f"🏘️ {re_asset.property_type}: {loc}"
                asset_options[label] = re_asset

        selected_asset_label = st.selectbox("資産リスト", list(asset_options.keys()))
        target_asset = asset_options[selected_asset_label]

        if target_asset:
            asset_description = selected_asset_label

    # ------------------------------------
    # 3. テンプレート選択
    # ------------------------------------
    with col_tpl:
        st.markdown("##### 2. テンプレートを選択")
        # 'data/templates/' ディレクトリ内のPDFファイルのみをテンプレートとして抽出
        template_dir_path_prefix = (
            os.path.join("data", "templates") + os.sep
        )  # os.sep を追加してディレクトリとしてのマッチを厳密にする
        files = (
            session.query(FileRegistry)
            .filter(
                FileRegistry.file_path.startswith(template_dir_path_prefix),
                FileRegistry.filename.ilike(
                    "%.pdf"
                ),  # 大文字・小文字を区別しないPDFフィルタ
            )
            .all()
        )

        if not files:
            st.warning("テンプレートがありません。")
        else:
            file_opts = {f.filename: f.file_hash for f in files}
            selected_file_name = st.selectbox(
                "テンプレート一覧", list(file_opts.keys())
            )
            target_hash = file_opts[selected_file_name]

    # ------------------------------------
    # 4. 作成実行
    # ------------------------------------
    st.divider()

    if st.button("🚀 PDFを作成する", type="primary", use_container_width=True):
        if not selected_file_name:
            st.error("テンプレートを選択してください")
        else:
            coords = db.get_coordinates_by_hash(target_hash)
            if not coords:
                st.error(
                    "このテンプレートには座標が登録されていません。「書式座標登録ツール」で設定してください。"
                )
            else:
                template_path = os.path.join(
                    ROOT_DIR, "data", "templates", selected_file_name
                )

                if not os.path.exists(template_path):
                    st.error("テンプレートファイルが見つかりません。")
                else:
                    # ★ここが重要: 選択された資産(Context)を渡してマッピングを作成
                    replace_map = create_replacement_map(target_case, target_asset)

                    pdf_data = generate_pdf(template_path, coords, replace_map)

                    if pdf_data:
                        st.success(f"✅ 作成完了！ ({asset_description})")

                        # ファイル名に資産名を含める
                        dl_filename = f"作成済_{selected_file_name}"
                        if (
                            target_asset
                            and isinstance(target_asset, FinancialAsset)
                            and target_asset.bank_ref
                        ):
                            dl_filename = f"{target_asset.bank_ref.bank_name}_{selected_file_name}"

                        st.download_button(
                            label="📥 PDFをダウンロード",
                            data=pdf_data,
                            file_name=dl_filename,
                            mime="application/pdf",
                        )

    session.close()


if __name__ == "__main__":
    main()
