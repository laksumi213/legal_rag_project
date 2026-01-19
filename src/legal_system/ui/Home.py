# src/legal_system/ui/Home.py

import base64
import json
import os
import re
import sys
import threading
import time
import unicodedata
from datetime import date, datetime
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import HumanMessage
from pdf2image import convert_from_bytes
from PIL import Image
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from st_keyup import st_keyup

# ==========================================
# 1. パス解決 & 環境設定
# ==========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(ROOT_DIR, "src")

if src_dir not in sys.path:
    sys.path.append(src_dir)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ==========================================
# 2. ページ設定
# ==========================================
st.set_page_config(
    page_title="案件統合管理ホーム", 
    page_icon="🏠", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. バックグラウンドロード & JS機能
# ==========================================
def run_background_warmup():
    if "modules_warmed_up" in st.session_state:
        return
    try:
        from legal_system.core.preload import warm_up_modules
        warm_up_modules()
        from legal_system.core.ai_factory import AIFactory
        st.session_state["modules_warmed_up"] = True
    except Exception as e:
        print(f"⚠️ Background warmup warning: {e}")

if "warmup_thread_started" not in st.session_state:
    t = threading.Thread(target=run_background_warmup, daemon=True)
    t.start()
    st.session_state["warmup_thread_started"] = True

# ★改良版: 最強オートフォーカス (IDに依存せず、最初の入力欄を狙う)
def enable_autofocus_on_search():
    """
    ページロード時に、画面上にある「最初のテキスト入力欄」を見つけ次第、
    強制的にフォーカスを当てるJavaScript。
    """
    js_code = """
    <script>
        (function() {
            let attempts = 0;
            const maxAttempts = 60; // 6秒間粘る

            function forceFocus() {
                // 親フレーム(Streamlitアプリ本体)を取得
                const doc = window.parent.document;
                
                // すべてのテキスト入力を取得 (st_keyupも含む)
                const inputs = doc.querySelectorAll('input[type="text"]');
                
                for (let i = 0; i < inputs.length; i++) {
                    const el = inputs[i];
                    // 見えている、かつ無効化されていない最初の入力欄を狙う
                    // offsetParent !== null は要素が表示されているかどうかの判定に使えます
                    if (el.offsetParent !== null && !el.disabled) {
                        el.focus();
                        return true; 
                    }
                }
                return false;
            }

            const interval = setInterval(() => {
                if (forceFocus() || attempts > maxAttempts) {
                    clearInterval(interval);
                }
                attempts++;
            }, 100); // 0.1秒ごとにチェック
        })();
    </script>
    """
    components.html(js_code, height=0)

# ==========================================
# 4. 必要なモジュールのインポート
# ==========================================
from legal_system.core.ai_factory import AIFactory
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import (
    Address, Case, Contact, Deceased, FinancialAsset, 
    H_AddressHistory, H_ContactLink, Heir, RealEstateAsset, User
)
from legal_system.ui.label_generator import generate_advanced_label, get_branch_address
from services.deceased_service import (
    add_heir, delete_case_and_all_related_data, delete_heir,
    get_address_info, get_contact_info, update_case_assignment,
    update_case_folder_path, update_case_number, update_deceased, update_heir
)
from services.folder_service import find_case_folder, open_local_folder
from services.kintone_sync_service import get_kintone_data_as_dict, import_kintone_json
from utils.date_utils import convert_seireki_to_wareki

try:
    from services.automation.touki_service import touki_service
except ImportError:
    touki_service = None

try:
    from update_bank_master import (
        download_data, get_remote_last_commit_date, load_local_state, save_local_state
    )
except ImportError:
    get_remote_last_commit_date = None
    download_data = None

# ==========================================
# 5. ヘルパー関数
# ==========================================
@st.cache_resource(ttl=60)
def check_update_status():
    if not get_remote_last_commit_date:
        return 2, "更新スクリプトが見つかりません"
    banks_path = os.path.join(ROOT_DIR, "data", "zengin", "banks.json")
    if not os.path.exists(banks_path):
        return 1, "銀行データが未取得です"
    try:
        remote = get_remote_last_commit_date()
        local = load_local_state().get("last_commit_date", "")
        if remote and remote != local:
            return 1, f"新着データがあります ({remote})"
        return 0, "最新の状態です"
    except Exception:
        return 0, "確認できませんでした"

def search_cases_enhanced(session, keyword: str):
    base_query = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.manager),
        joinedload(Case.operator)
    )
    if not keyword:
        # デフォルトでは最近の更新案件を表示
        return base_query.order_by(Case.created_at.desc()).limit(10).all()

    clean_key = f"%{keyword.strip()}%"
    return base_query.join(Case.deceased_ref)\
        .outerjoin(Deceased.heirs)\
        .outerjoin(Heir.contact_links)\
        .outerjoin(H_ContactLink.contact)\
        .filter(
            or_(
                Case.case_number.ilike(clean_key),
                Case.client_name.ilike(clean_key),
                Case.client_name_kana.ilike(clean_key),
                Case.sol_case_number.ilike(clean_key),
                Case.referral_sec_phone.ilike(clean_key),
                Deceased.name_last.ilike(clean_key),
                Deceased.name_first.ilike(clean_key),
                Contact.value.ilike(clean_key)
            )
        ).distinct().limit(20).all()

def normalize_text_space(text: str) -> str:
    if not text: return ""
    return text.replace(" ", "　").strip()

def normalize_text(text: str) -> str:
    if not text: return ""
    return unicodedata.normalize("NFKC", text).strip()

def analyze_nayose_with_ai(image_bytes: bytes) -> dict:
    try:
        img_str = base64.b64encode(image_bytes).decode("utf-8")
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        prompt_text = """
        あなたは不動産登記の専門家です。
        名寄帳画像を読み取り、以下JSONを抽出してください。
        
        【重要: 所在地の補完】
        - 物件一覧の「所在」に都道府県や市区町村が省略されている場合、書類のヘッダーや発行元自治体名（例: 「横浜市」「千葉県」など）を探し、**必ず**それらを補完して正式な住所にしてください。
        - 例: 「江戸川台東4丁目...」 -> 「千葉県流山市江戸川台東4丁目...」

        【重要: 評価額の抽出】
        - 「価格」「評価額」「固定資産税評価額」などの欄から金額を抽出してください。
        - 千円単位や円単位の違いに注意し、数値（円単位）に直してください。

        【JSON構造】
        {
            "owner_name": "所有者氏名",
            "assets": [
                {
                    "type": "土地/家屋",
                    "location": "所在(都道府県から記載)",
                    "number": "番地/家屋番号",
                    "category_structure": "地目/構造",
                    "area": "地積/床面積(数値)",
                    "assessed_value": "評価額(数値)"
                }
            ]
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
        start = content.find("{")
        end = content.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(content[start:end])
        else:
            raise ValueError("JSON error")
    except Exception as e:
        return {"error": str(e)}

def get_probable_prefectures(session, case_id: int) -> list[str]:
    prefs = set()
    case = session.query(Case).get(case_id)
    if not case: return []
    if case.deceased_ref and case.deceased_ref.last_address_id:
        addr = session.query(Address).get(case.deceased_ref.last_address_id)
        if addr and addr.prefecture: prefs.add(addr.prefecture)
    if case.deceased_ref and case.deceased_ref.heirs:
        for h in case.deceased_ref.heirs:
            link = session.query(H_AddressHistory).filter_by(heir_id=h.id, is_current_address=True).first()
            if link:
                addr = session.query(Address).get(link.address_id)
                if addr and addr.prefecture: prefs.add(addr.prefecture)
    existing_assets = session.query(RealEstateAsset).filter_by(case_id=case_id).all()
    for a in existing_assets:
        m = re.match(r'(.{2,3}[都道府県])', a.location or "")
        if m: prefs.add(m.group(1))
    return list(prefs)

# コールバック関数 (SessionState更新用)
def update_touki_address_callback(new_address: str):
    st.session_state["touki_target_address"] = new_address

# ==========================================
# 6. メインアプリ処理
# ==========================================
def main():
    db = DatabaseManager()
    session = db._get_session()
    current_user_info = db.get_current_user_info()

    # --- サイドバー ---
    with st.sidebar:
        st.title("🗂️ 業務メニュー")
        st.info(f"👤 **{current_user_info['name']}**")
        st.caption(f"所属: {current_user_info['dept']}")

        with st.expander("⚙️ プロフィール編集"):
            with st.form("user_profile_form"):
                new_name = st.text_input("表示名", value=current_user_info["name"])
                new_dept = st.text_input("所属部署", value=current_user_info["dept"])
                new_phone = st.text_input("内線/直通", value=current_user_info["phone"])
                if st.form_submit_button("更新"):
                    try:
                        db.register_user(current_user_info["id"], new_name, new_dept, new_phone)
                        st.success("更新しました！"); time.sleep(0.5); st.rerun()
                    except Exception as e: st.error(f"エラー: {e}")

        with st.expander("➕ 担当者追加 (マスタ登録)"):
            with st.form("add_other_user_form"):
                au_name = st.text_input("氏名", placeholder="例: 鈴木 補助")
                au_id = st.text_input("ログインID (任意)", placeholder="PCのログインID等")
                au_dept = st.text_input("部署", placeholder="東京支店")
                au_phone = st.text_input("電話番号")
                if st.form_submit_button("登録実行"):
                    if not au_name: st.error("氏名は必須です")
                    else:
                        reg_id = au_id.strip() if au_id else au_name.strip()
                        try:
                            db.register_user(reg_id, au_name, au_dept, au_phone)
                            st.success(f"「{au_name}」さんを登録しました！"); time.sleep(1); st.rerun()
                        except Exception as e: st.error(f"登録エラー: {e}")

        st.divider()
        
        if "current_menu" not in st.session_state:
            st.session_state["current_menu"] = "🏠 案件概要・基本情報"

        menu = st.radio(
            "作業メニュー",
            [
                "🏠 案件概要・基本情報", 
                "🏦 銀行口座 登録", 
                "📈 証券・その他資産", 
                "🏘️ 不動産 登録", 
                "🌐 登記情報取得", 
                "🖨️ 宛名ラベル作成",
                "✅ タスク管理"
            ],
            key="menu_radio",
        )
        
        if "next_menu_action" in st.session_state and st.session_state["next_menu_action"]:
            target = st.session_state["next_menu_action"]
            st.session_state["next_menu_action"] = None
            menu = target
            st.toast(f"メニューを「{target}」に切り替えました", icon="🔄")

        st.divider()
        st.subheader("🏦 銀行マスタ管理")
        status_code, info = check_update_status()
        if status_code == 1: st.warning(f"💡 {info}")
        else: st.caption(f"✅ {info}")

        if st.button("🔄 マスタ強制更新", use_container_width=True):
            with st.status("更新中...", expanded=True) as s:
                if download_data:
                    download_data()
                    if get_remote_last_commit_date:
                        save_local_state(get_remote_last_commit_date())
                    s.update(label="完了！", state="complete")
                else: s.update(label="機能無効", state="error")
            time.sleep(1); st.rerun()

    # ------------------------------------------
    # メインエリア上部: リアルタイム案件検索
    # ------------------------------------------
    
    # ★ オートフォーカスJS注入 (汎用版)
    enable_autofocus_on_search()

    search_query = st_keyup(
        "🔍 案件を検索 (電話番号・氏名・案件番号など)", 
        placeholder="案件番号、氏名、電話番号で検索...",
        key="case_search_bar",
        debounce=300
    )

    filtered_cases = search_cases_enhanced(session, search_query)
    target_case_id = st.session_state.get("selected_case_id")

    # ★ 検索結果の表示ロジック (UI改善版)
    if search_query:
        # 1件ヒット時は自動遷移
        if len(filtered_cases) == 1:
            auto_target = filtered_cases[0].case_id
            if target_case_id != auto_target:
                st.session_state["selected_case_id"] = auto_target
                st.rerun()
        
        # リスト表示 (全幅ボタンでコンパクト＆左揃え風に)
        if filtered_cases:
            st.caption(f"検索結果: {len(filtered_cases)}件")
            # CSS for left alignment
            st.markdown(
                """
                <style>
                div[data-testid="stButton"] button {
                    text-align: left;
                    display: block;
                    width: 100%;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            for c in filtered_cases:
                # 詳細情報のテキスト生成 (1行にまとめる)
                d_name = f"{c.deceased_ref.name_last} {c.deceased_ref.name_first}" if c.deceased_ref else "未登録"
                label_text = f"【{c.case_number}】 {c.client_name} 様 (被相続人: {d_name})"
                
                # 選択中の案件はprimary色で強調
                btn_type = "primary" if target_case_id == c.case_id else "secondary"
                
                # ボタンクリックで選択 (枠全体がボタンになるため押しやすい)
                if st.button(label_text, key=f"sel_{c.case_id}", use_container_width=True, type=btn_type):
                    st.session_state["selected_case_id"] = c.case_id
                    st.rerun()
            st.divider()
        else:
            st.warning("該当する案件は見つかりませんでした。")
    
    # 未選択時
    if not target_case_id and filtered_cases and not search_query:
        target_case_id = filtered_cases[0].case_id
        st.session_state["selected_case_id"] = target_case_id

    # ターゲットが決まっていない場合
    if not target_case_id:
        st.info("👈 上部の検索バーから案件を検索するか、左のメニューを操作してください。")
        session.close()
        return

    # === 以下、詳細画面の表示 ===
    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).filter_by(case_id=target_case_id).first()

    if not current_case:
        st.error("案件データの取得に失敗しました。")
        session.close()
        return

    st.title(f"{current_case.case_number}: {current_case.client_name} 様")
    
    # ==========================================
    # A. 案件概要・基本情報
    # ==========================================
    if menu == "🏠 案件概要・基本情報":
        st.subheader("基本情報・操作")

        with st.container(border=True):
            st.caption("🚀 クイックアクセス")
            qc1, qc2 = st.columns([1, 2], gap="large")
            with qc1:
                KINTONE_DOMAIN = "chester-tax.cybozu.com"
                APP_ID = "242"
                rec_id = current_case.kintone_record_id
                if rec_id:
                    kintone_url = f"https://{KINTONE_DOMAIN}/k/{APP_ID}/show#record={rec_id}"
                    st.link_button("🔗 Kintoneで開く", kintone_url, type="primary", use_container_width=True)
                else:
                    st.button("🔗 Kintone連携なし", disabled=True, use_container_width=True)
            with qc2:
                curr_path = current_case.folder_path or ""
                c_path, c_act = st.columns([3, 2])
                new_path = c_path.text_input("フォルダパス", value=curr_path, label_visibility="collapsed", placeholder="フォルダパスを入力")
                c_open, c_search = c_act.columns(2)
                if c_open.button("📂 開く", use_container_width=True):
                    open_local_folder(new_path)
                    if new_path != curr_path: update_case_folder_path(target_case_id, new_path)
                if c_search.button("🔍 自動検索", use_container_width=True):
                    q = current_case.case_number if current_case.case_number.startswith("G") else current_case.client_name.replace(" ", "")
                    with st.spinner("検索中..."):
                        found = find_case_folder(q)
                        if found:
                            update_case_folder_path(target_case_id, found)
                            st.success("発見!"); time.sleep(0.5); st.rerun()
                        else: st.warning("なし")
                if new_path != curr_path: update_case_folder_path(target_case_id, new_path)

        st.write("") 

        contractor = None
        if current_case.deceased_ref and current_case.deceased_ref.heirs:
            contractor = next((h for h in current_case.deceased_ref.heirs if h.is_contracting_party), None)
            if not contractor: contractor = current_case.deceased_ref.heirs[0]

        con_phone = ""
        con_email = ""
        if contractor:
            contacts = get_contact_info("heir", contractor.id)
            con_phone = next((c["value"] for c in contacts if c["type"]=="PHONE"), "")
            con_email = next((c["value"] for c in contacts if c["type"]=="EMAIL"), "")

        with st.container(border=True):
            st.markdown("##### 👤 依頼者（契約者）情報")
            rc1, rc2 = st.columns(2)
            new_client_name = rc1.text_input("氏名", value=current_case.client_name)
            new_client_kana = rc2.text_input("フリガナ", value=current_case.client_name_kana or "")
            rc3, rc4, rc5 = st.columns([1.5, 2, 1])
            new_tel = rc3.text_input("電話番号", value=con_phone, key="client_tel_input")
            new_mail = rc4.text_input("メールアドレス", value=con_email, key="client_mail_input")
            
            rc5.write(""); rc5.write("")
            if rc5.button("依頼者更新", key="btn_upd_client", use_container_width=True):
                try:
                    fixed_name = normalize_text_space(new_client_name)
                    fixed_kana = normalize_text_space(new_client_kana)
                    current_case.client_name = fixed_name
                    current_case.client_name_kana = fixed_kana
                    if contractor:
                        update_heir(
                            contractor.id, 
                            name=fixed_name, 
                            rel=contractor.relationship_type,
                            kana_last=fixed_kana.split("　")[0] if "　" in fixed_kana else fixed_kana,
                            phone_contacts=[{"value": new_tel}] if new_tel else [],
                            email_contacts=[{"value": new_mail}] if new_mail else []
                        )
                    session.commit()
                    st.toast("更新しました", icon="✅"); time.sleep(0.5); st.rerun()
                except Exception as e: st.error(f"更新エラー: {e}")

        st.divider()
        # --- 担当者・連携・削除 ---
        with st.container(border=True):
            st.markdown("##### 👥 担当者情報")
            users = session.query(User).all()
            user_map = {u.name: u.id for u in users}
            user_map["未定"] = None
            curr_mgr_name = next((u.name for u in users if u.id == current_case.manager_id), "未定")
            curr_opr_name = next((u.name for u in users if u.id == current_case.operator_id), "未定")
            c1, c2, c3 = st.columns([2, 2, 1])
            new_mgr = c1.selectbox("担当者1 (進捗)", list(user_map.keys()), index=list(user_map.keys()).index(curr_mgr_name))
            new_opr = c2.selectbox("担当者2 (実務)", list(user_map.keys()), index=list(user_map.keys()).index(curr_opr_name))
            c3.write(""); c3.write("") 
            if c3.button("担当更新", use_container_width=True):
                if update_case_assignment(target_case_id, user_map[new_mgr], user_map[new_opr]):
                    st.toast("更新しました", icon="✅"); time.sleep(0.5); st.rerun()

        st.divider()
        with st.expander("🤝 紹介・SOL連携情報"):
            with st.form("edit_sol_info"):
                c_sol1, c_sol2 = st.columns(2)
                new_sol_no = c_sol1.text_input("SOL案件番号", value=current_case.sol_case_number or "")
                curr_intro = current_case.introduction_date
                new_intro = c_sol2.date_input("紹介日", value=curr_intro if curr_intro else None)
                if new_intro: c_sol2.caption(f"和暦: {convert_seireki_to_wareki(new_intro)}")
                st.markdown("---")
                c_br, c_rep, c_ph = st.columns(3)
                new_branch = c_br.text_input("紹介元支店", value=current_case.referral_sec_branch_name or "")
                new_rep = c_rep.text_input("紹介元担当者", value=current_case.referral_sec_rep_name or "")
                new_ref_phone = c_ph.text_input("紹介元電話番号", value=current_case.referral_sec_phone or "")
                if st.form_submit_button("連携情報を更新"):
                    current_case.sol_case_number = new_sol_no
                    current_case.introduction_date = new_intro
                    current_case.referral_sec_branch_name = new_branch
                    current_case.referral_sec_rep_name = new_rep
                    current_case.referral_sec_phone = new_ref_phone
                    session.commit(); st.toast("更新しました", icon="✅"); time.sleep(0.5); st.rerun()

        st.divider()
        c_k, c_d = st.columns([1, 1])
        with c_k:
            with st.expander("📥 Kintoneデータ取込 / JSON出力"):
                if st.button("Kintone用データをコピー (JSON)", icon="📋", use_container_width=True):
                    kintone_data = get_kintone_data_as_dict(target_case_id)
                    if kintone_data: st.code(json.dumps(kintone_data, ensure_ascii=False), language="json")
                st.write("---")
                ji = st.text_area("JSON貼り付け", height=100)
                if st.button("上書き実行"):
                    if ji:
                        try:
                            import_kintone_json(json.loads(ji), target_case_id=target_case_id)
                            st.success("更新しました"); time.sleep(1); st.rerun()
                        except: st.error("エラー")
        with c_d:
            with st.expander("🗑️ 案件削除メニュー"):
                st.error("※ 削除すると復元できません")
                if st.checkbox("削除確認") and st.button("実行: 削除", type="primary"):
                    delete_case_and_all_related_data(current_case.case_number)
                    st.rerun()

        st.divider()
        d = current_case.deceased_ref
        with st.expander(f"👤 家族情報編集 (被相続人: {d.name_last if d else ''})"):
            if d:
                with st.form("quick_fam_edit"):
                    new_dl = st.text_input("被相続人 姓", value=d.name_last)
                    new_df = st.text_input("被相続人 名", value=d.name_first)
                    if st.form_submit_button("保存"):
                        update_deceased(d.id, name_last=new_dl, name_first=new_df); st.rerun()
            else: st.warning("被相続人データがありません")

        st.markdown("#### 相続人・関係者リスト")
        if d and d.heirs:
            for h in d.heirs:
                icon = "👑" if h.is_contracting_party else "👤"
                label = f"{icon} {h.name_last} {h.name_first} ({h.relationship_type})"
                with st.expander(label):
                    with st.form(f"form_heir_{h.id}"):
                        c1, c2 = st.columns(2)
                        h_lname = c1.text_input("姓", value=h.name_last)
                        h_fname = c2.text_input("名", value=h.name_first)
                        c3, c4 = st.columns(2)
                        h_klname = c3.text_input("フリガナ(姓)", value=h.name_last_kana or "")
                        h_kfname = c4.text_input("フリガナ(名)", value=h.name_first_kana or "")
                        c5, c6 = st.columns(2)
                        h_rel = c5.text_input("続柄", value=h.relationship_type)
                        h_contract = c6.checkbox("契約者 (依頼主)", value=h.is_contracting_party)
                        h_dob = st.date_input("生年月日", value=h.date_of_birth if h.date_of_birth else None)
                        if h_dob: st.caption(f"和暦: {convert_seireki_to_wareki(h_dob)}")
                        h_addr = get_address_info("heir", h.id)
                        h_contacts = get_contact_info("heir", h.id)
                        h_phone = next((c["value"] for c in h_contacts if c["type"]=="PHONE"), "")
                        h_email = next((c["value"] for c in h_contacts if c["type"]=="EMAIL"), "")
                        st.markdown("---")
                        az, ap = st.columns(2)
                        h_zip = az.text_input("郵便番号", value=h_addr.get("zip_code",""))
                        h_pref = ap.text_input("都道府県", value=h_addr.get("prefecture",""))
                        h_city = st.text_input("市区町村・番地", value=f"{h_addr.get('city_ward_town') or ''}{h_addr.get('street_address') or ''}")
                        h_bldg = st.text_input("建物名", value=h_addr.get("building_name",""))
                        ct1, ct2 = st.columns(2)
                        h_tel = ct1.text_input("電話番号", value=h_phone)
                        h_eml = ct2.text_input("メールアドレス", value=h_email)
                        if st.form_submit_button("更新保存", type="primary"):
                            update_heir(h.id, name=f"{h_lname} {h_fname}", rel=h_rel, kana_last=h_klname, kana_first=h_kfname, dob=str(h_dob) if h_dob else None, zip_code=h_zip, pref=h_pref, city=h_city, street="", building=h_bldg, phone_contacts=[{"value": h_tel}] if h_tel else [], email_contacts=[{"value": h_eml}] if h_eml else [])
                            h.is_contracting_party = h_contract
                            if h_contract:
                                current_case.client_name = f"{h_lname}　{h_fname}"
                                current_case.client_name_kana = f"{h_klname}　{h_kfname}"
                            session.commit(); st.toast("更新しました", icon="✅"); time.sleep(1); st.rerun()
                    if st.button("削除する", key=f"del_heir_btn_{h.id}"):
                        delete_heir(h.id); st.toast("削除しました", icon="🗑️"); time.sleep(1); st.rerun()
        else: st.info("登録されている相続人はおられません。")
        if d:
            with st.expander("➕ 相続人を新規追加する"):
                with st.form("add_heir_form"):
                    na1, na2 = st.columns(2)
                    new_lname = na1.text_input("姓")
                    new_fname = na2.text_input("名")
                    new_rel = st.text_input("続柄 (例: 長男)")
                    if st.form_submit_button("追加"):
                        if new_lname and new_rel:
                            add_heir(d.id, f"{new_lname} {new_fname}", new_rel); st.toast("追加しました", icon="✅"); time.sleep(1); st.rerun()
                        else: st.error("姓と続柄は必須です")

    # ==========================================
    # B. 銀行口座登録
    # ==========================================
    elif menu == "🏦 銀行口座 登録":
        st.subheader("🏦 銀行・金融資産管理")
        assets = session.query(FinancialAsset).filter_by(case_id=target_case_id).all()
        if assets:
            for a in assets:
                b_name = a.bank_ref.bank_name if a.bank_ref else "不明"
                br_name = a.branch_ref.branch_name if a.branch_ref else "-"
                with st.expander(f"{b_name} {br_name} ({a.account_number})"):
                    nb = st.number_input("残高", value=int(a.balance), key=f"b_{a.id}")
                    ns = st.text_input("状況", value=a.status, key=f"s_{a.id}")
                    if st.button("更新", key=f"btn_{a.id}"):
                        a.balance = nb; a.status = ns; session.commit(); st.toast("保存しました")
        else: st.info("登録口座はありません。")
        st.info("👉 新規登録はサイドバーの「02_預貯金口座入力フォーム」をご利用ください")

    # ==========================================
    # C. 不動産登録
    # ==========================================
    elif menu == "🏘️ 不動産 登録":
        st.subheader("🏘️ 不動産・名寄帳読取")
        with st.expander("📄 名寄帳(PDF/画像)から自動登録する", expanded=False):
            uploaded_nayose = st.file_uploader("名寄帳をアップロード", type=["pdf", "png", "jpg"])
            if "nayose_result" not in st.session_state: st.session_state["nayose_result"] = None
            if uploaded_nayose:
                if st.button("AI解析実行", type="primary"):
                    with st.spinner("解析中..."):
                        file_bytes = uploaded_nayose.read()
                        target_bytes = file_bytes
                        if uploaded_nayose.type == "application/pdf":
                            try:
                                images = convert_from_bytes(file_bytes, dpi=200, first_page=1, last_page=1)
                                buf = BytesIO(); images[0].convert("RGB").save(buf, format="JPEG"); target_bytes = buf.getvalue()
                            except: pass
                        result = analyze_nayose_with_ai(target_bytes)
                        if "error" not in result:
                            st.session_state["nayose_result"] = result; st.success("解析完了")
                        else: st.error("解析失敗")
            if st.session_state["nayose_result"]:
                res = st.session_state["nayose_result"]
                df_assets = pd.DataFrame(res.get("assets", []))
                st.caption(f"所有者: {res.get('owner_name')}")
                
                column_config = {
                    "type": st.column_config.SelectboxColumn("種類", options=["土地", "家屋", "マンション"], required=True),
                    "location": st.column_config.TextColumn("所在", width="medium"),
                    "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                    "category_structure": st.column_config.TextColumn("地目/構造", width="small"),
                    "area": st.column_config.NumberColumn("地積/床面積"),
                    "assessed_value": st.column_config.NumberColumn("評価額 (円)", format="%d"),
                }
                edited_assets = st.data_editor(df_assets, column_config=column_config, num_rows="dynamic", use_container_width=True, key="nayose_editor")
                if st.button("💾 この内容で登録する"):
                    try:
                        count = 0
                        for index, row in edited_assets.iterrows():
                            if not row["location"]: continue
                            p_type = "Land"
                            if "家" in str(row["type"]) or "建" in str(row["type"]): p_type = "Building"
                            elif "マンション" in str(row["type"]): p_type = "Condo"
                            area_val = 0.0
                            try: area_val = float(str(row["area"]).replace(",", ""))
                            except: pass
                            val_val = 0.0
                            try: val_val = float(str(row["assessed_value"]).replace(",", ""))
                            except: pass

                            new_asset = RealEstateAsset(
                                case_id=target_case_id,
                                property_type=p_type,
                                location=normalize_text(row["location"]),
                                lot_number=normalize_text(row["number"]) if p_type == "Land" else None,
                                land_category=normalize_text(row["category_structure"]) if p_type == "Land" else None,
                                land_area=area_val if p_type == "Land" else None,
                                house_number=normalize_text(row["number"]) if p_type != "Land" else None,
                                structure=normalize_text(row["category_structure"]) if p_type != "Land" else None,
                                floor_area=str(area_val) if p_type != "Land" else None,
                                assessed_value=val_val
                            )
                            session.add(new_asset)
                            count += 1
                        session.commit()
                        st.success(f"{count}件登録しました")
                        st.info("💡 ヒント: 続けて登記情報を取得できます")
                        if st.button("🚀 続けて登記情報を取得する (自動画面遷移)", type="primary"):
                            st.session_state["next_menu_action"] = "🌐 登記情報取得"
                            st.session_state["nayose_result"] = None
                            st.rerun()
                        time.sleep(2)
                        st.session_state["nayose_result"] = None
                        st.rerun()
                    except Exception as e: st.error(f"エラー: {e}")
        st.divider()
        st.markdown("##### 📝 登録済み不動産一覧")
        real_estates = session.query(RealEstateAsset).filter_by(case_id=target_case_id).all()
        if real_estates:
            for re_asset in real_estates:
                label = f"[{re_asset.property_type}] {re_asset.location} {re_asset.lot_number or re_asset.house_number or ''}"
                with st.expander(label):
                    c1, c2, c3 = st.columns(3)
                    c1.write(f"**地目/構造:** {re_asset.land_category or re_asset.structure}")
                    c2.write(f"**面積:** {re_asset.land_area or re_asset.floor_area}")
                    c3.write(f"**評価額:** {re_asset.assessed_value:,.0f} 円" if re_asset.assessed_value else "-")
                    if st.button("削除", key=f"del_re_{re_asset.id}"):
                        session.delete(re_asset); session.commit(); st.rerun()
        else: st.info("登録されている不動産はありません。")

    # ==========================================
    # 🌐 登記情報取得
    # ==========================================
    elif menu == "🌐 登記情報取得":
        st.subheader("🌐 登記情報取得ツール")
        
        # ⚠️ コンテナ環境であることを警告
        if os.path.exists("/.dockerenv") or os.environ.get("IS_DOCKER"):
            st.warning("⚠️ 現在Docker(サーバー)環境で実行中です。自動操作ブラウザは画面に表示されません（バックグラウンド実行）。")
        else:
            st.info("自動操作ブラウザを起動し、登記情報提供サービスで検索を行います。")

        if not touki_service:
            st.error("機能が無効です (touki_service.py が見つかりません)")
        else:
            category = st.radio("請求カテゴリ", ["土地・建物", "商業・法人"], horizontal=True)
            input_mode = "manual"
            if category == "土地・建物":
                input_mode = st.radio("入力方法", ["登録済み不動産から選択", "手動入力"], horizontal=True, key="touki_input_mode")

            # Session State の初期化（なければ空文字）
            if "touki_target_address" not in st.session_state:
                st.session_state["touki_target_address"] = ""

            corp_name = ""

            if category == "商業・法人":
                corp_name = st.text_input("会社・法人名", placeholder="例: 株式会社チェスター")
                # 法人の場合も同じStateを使うか、分けるかは設計次第だが、ここでは共通利用
                target_addr_input = st.text_input("本店所在地", key="touki_target_address_corp", placeholder="都道府県 市区町村...")
                # 画面入力値をStateに反映させる場合、key指定しているので自動同期される
            else:
                target_type = "土地" # 初期値
                
                if input_mode == "登録済み不動産から選択":
                    assets = session.query(RealEstateAsset).filter_by(case_id=target_case_id).all()
                    if not assets: 
                        st.warning("登録された不動産がありません")
                    else:
                        asset_options = {f"【{a.property_type}】{a.location} {a.lot_number or a.house_number or ''}": a for a in assets}
                        selected_label = st.selectbox("取得対象を選択", list(asset_options.keys()))
                        
                        if selected_label:
                            sel_asset = asset_options[selected_label]
                            
                            # 選択されたアセットから基本住所を構築
                            base_addr = f"{sel_asset.location or ''}{sel_asset.lot_number or sel_asset.house_number or ''}"
                            
                            # セレクトボックス選択時にStateを更新
                            if "last_selected_asset_id" not in st.session_state:
                                st.session_state["last_selected_asset_id"] = None
                            
                            if st.session_state["last_selected_asset_id"] != sel_asset.id:
                                st.session_state["touki_target_address"] = base_addr
                                st.session_state["last_selected_asset_id"] = sel_asset.id
                                st.rerun()

                            if sel_asset.property_type in ["Building", "Condo"]: 
                                target_type = "建物"
                            
                            st.caption(f"種別: {target_type}")

                # === 共通の住所入力・補完エリア ===
                # 入力欄 (Stateと紐付け、disabled=Falseで常に編集可能)
                current_addr_val = st.text_input(
                    "検索する所在・地番 (編集可)", 
                    key="touki_target_address",
                    placeholder="例: 東京都中央区銀座1丁目1-1"
                )

                # 住所チェック & 補完ボタン
                if current_addr_val and not re.match(r'(東京都|北海道|(?:京都|大阪)府|.{2,3}県)', current_addr_val):
                    st.warning("⚠️ 住所に都道府県が含まれていません。以下から選択して追加してください。")
                    
                    prob_prefs = get_probable_prefectures(session, target_case_id)
                    if prob_prefs:
                        cols = st.columns(len(prob_prefs))
                        for idx, p in enumerate(prob_prefs):
                            # ★修正: on_click で安全にState更新
                            cols[idx].button(
                                f"+ {p}", 
                                key=f"add_pref_{idx}",
                                on_click=update_touki_address_callback,
                                args=(f"{p}{current_addr_val}",)
                            )
                    else:
                        st.info("候補が見つかりません。手動で都道府県を入力してください。")

                target_type_radio = st.radio("種別", ["土地", "建物"], index=0 if target_type == "土地" else 1, horizontal=True)

            # 実行ボタン
            if st.button("🚀 登記情報を取得 (ブラウザ起動)", type="primary"):
                # 入力欄の値を最終確認
                final_addr = st.session_state.get("touki_target_address", "")
                if category == "商業・法人":
                    # 法人の場合は別の変数(key)を使っているか、上で代入が必要
                    # ここでは簡易的にcorp用のロジック
                    final_addr = st.session_state.get("touki_target_address_corp", "")

                if not final_addr:
                    st.error("住所/所在が入力されていません")
                else:
                    with st.spinner("自動操作中... (ブラウザが起動します)"):
                        try:
                            msg = ""
                            if category == "商業・法人":
                                msg = touki_service.request_commercial(corp_name, final_addr)
                            else:
                                msg = touki_service.request_real_estate(final_addr, target_type_radio)
                            st.success(msg)
                        except Exception as e:
                            st.error(f"エラーが発生しました: {e}")

    # ==========================================
    # D. 宛名ラベル作成
    # ==========================================
    elif menu == "🖨️ 宛名ラベル作成":
        st.subheader("🖨️ 宛名ラベル出力")
        
        contractor = None
        c_address = None
        c_phone = ""
        
        if current_case.deceased_ref and current_case.deceased_ref.heirs:
            contractor = next((h for h in current_case.deceased_ref.heirs if h.is_contracting_party), None)
            if not contractor: contractor = current_case.deceased_ref.heirs[0]
            if contractor:
                al = session.query(H_AddressHistory).filter(H_AddressHistory.heir_id == contractor.id, H_AddressHistory.is_current_address == True).first()
                if al: c_address = session.query(Address).get(al.address_id)
                contacts = get_contact_info("heir", contractor.id)
                c_phone = next((c["value"] for c in contacts if c["type"]=="PHONE"), "")

        c_l, c_r = st.columns([1, 1.2])
        with c_l:
            st.markdown("##### 👤 宛先")
            with st.container(border=True):
                dn = f"{contractor.name_last} {contractor.name_first}" if contractor else ""
                dz = c_address.zip_code if c_address else ""
                da = f"{c_address.prefecture}{c_address.city_ward_town}{c_address.street_address} {c_address.building_name or ''}" if c_address else ""
                
                ln = st.text_input("氏名", value=dn)
                lh = st.selectbox("敬称", ["様", "殿", "御中"])
                lz = st.text_input("郵便番号", value=dz)
                la = st.text_area("住所", value=da, height=80)
                lt = st.text_input("電話番号 (ラベル用)", value=c_phone)
                inc_c = st.checkbox("✅ お客様ラベル印刷", value=True)

        with c_r:
            st.markdown("##### 🏢 差出人 & 設定")
            with st.container(border=True):
                inc_s = st.checkbox("差出人(自分)も印刷", value=True)
                if inc_s:
                    mb = "横浜" if "横浜" in current_user_info.get("dept","") else "東京"
                    ma = get_branch_address(mb)
                    sn = st.text_input("担当者名", value=current_user_info["name"])
                    s_tel = st.text_input("電話", value=current_user_info["phone"])
                    sa = st.text_area("差出人住所", value=ma, height=80)
                
                c_p1, c_p2 = st.columns(2)
                sp = c_p1.number_input("開始位置", 1, 30, 1)
                cp = c_p2.number_input("枚数", 1, 10, 1)

        st.divider()
        
        def_tpl = os.path.join(ROOT_DIR, "data", "templates", "ラベルシート -貼り付け用.docx")
        up_tpl = st.file_uploader("テンプレート変更(任意)", type=["docx"])
        
        if st.button("🚀 ラベル作成", type="primary"):
            tpl_b = None
            if up_tpl: tpl_b = up_tpl.read()
            elif os.path.exists(def_tpl):
                with open(def_tpl, "rb") as f: tpl_b = f.read()
            else: st.error(f"テンプレートがありません: {def_tpl}"); st.stop()

            plist = []
            c_data = {"type":"client","name":ln,"honorific":lh,"zip_code":lz,"address":la,"tel":lt}
            s_data = {
                "type": "sender",
                "name": f"行政書士法人チェスター　{sn}", 
                "honorific": "",
                "zip_code": sz if inc_s else "",
                "address": sad if inc_s else "",
                "tel": s_tel if inc_s else ""
            }

            for _ in range(cp):
                if inc_c: plist.append(c_data)
                if inc_s: plist.append(s_data)

            if not plist: st.warning("対象なし"); st.stop()

            try:
                io_data = generate_advanced_label(tpl_b, plist, start_position=sp)
                st.download_button("📥 ダウンロード", io_data, f"宛名ラベル_{ln.replace(' ','')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                st.success("完了！")
            except Exception as e: st.error(f"エラー: {e}")

    # ==========================================
    # その他メニュー
    # ==========================================
    else:
        st.subheader(menu)
        st.info("機能開発中")

    session.close()

if __name__ == "__main__":
    main()