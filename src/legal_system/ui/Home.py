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
from typing import List, Union

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

# ★修正版: キーボードショートカット (ポーリング強化・st_keyup特定版)
def enable_keyboard_shortcuts():
    # 検索バーのプレースホルダーの一部
    SEARCH_KEYWORD = "案件番号"; 
    BTN_OPEN_TEXT = "📂 開く"
    BTN_KINTONE_TEXT = "🔗 Kintoneで開く"

    js_code = f"""
    <script>
        (function() {{
            const SEARCH_KW = "{SEARCH_KEYWORD}";
            const TEXT_OPEN = "{BTN_OPEN_TEXT}";
            const TEXT_KINTONE = "{BTN_KINTONE_TEXT}";

            // --- Iframe内も含めてInputを探す関数 ---
            function findTargetInput() {{
                const doc = window.parent.document;
                
                // 1. すべてのIframeを取得
                const iframes = doc.getElementsByTagName('iframe');
                
                for (let i = 0; i < iframes.length; i++) {{
                    try {{
                        const frame = iframes[i];
                        const fDoc = frame.contentDocument || frame.contentWindow.document;
                        
                        // Iframe内の全inputを取得
                        const inputs = fDoc.getElementsByTagName('input');
                        for (let j = 0; j < inputs.length; j++) {{
                            const input = inputs[j];
                            // プレースホルダーまたはaria-labelで判定
                            const txt = (input.placeholder || "") + (input.getAttribute('aria-label') || "");
                            if (txt.includes(SEARCH_KW)) {{
                                return input; // 発見
                            }}
                        }}
                    }} catch(e) {{
                        // Cross-originエラーは無視
                    }}
                }}
                return null;
            }}

            // --- ボタンクリック関数 ---
            function triggerButton(textLabel) {{
                const doc = window.parent.document;
                // button, a, [role="button"] を広範囲に探索
                const elements = doc.querySelectorAll('button, a, [role="button"]');
                for (let el of elements) {{
                    if (el.textContent && el.textContent.includes(textLabel)) {{
                        el.click();
                        // 視覚フィードバック
                        const originalBorder = el.style.border;
                        el.style.border = "3px solid #d33682"; 
                        setTimeout(() => el.style.border = originalBorder, 300);
                        return true;
                    }}
                }}
                return false;
            }}

            // --- フォーカス実行処理 ---
            function doFocus() {{
                const input = findTargetInput();
                if (input) {{
                    input.focus();
                    input.select();
                    // 視覚フィードバック
                    input.style.transition = "box-shadow 0.2s";
                    input.style.boxShadow = "0 0 0 4px rgba(211, 54, 130, 0.5)";
                    setTimeout(() => input.style.boxShadow = "", 800);
                    return true;
                }}
                return false;
            }}

            // --- キーボードイベントハンドラ ---
            const doc = window.parent.document;
            
            // 重複登録防止
            if (window.parent._legalAppKeyHandler_v2) {{
                doc.removeEventListener('keydown', window.parent._legalAppKeyHandler_v2, true);
            }}

            window.parent._legalAppKeyHandler_v2 = function(e) {{
                // Altキー必須
                if (!e.altKey) return;
                const key = e.key.toLowerCase();

                // [Alt + S] 検索バー
                if (key === 's') {{
                    e.preventDefault(); 
                    e.stopPropagation();
                    doFocus();
                }}
                
                // [Alt + O] フォルダ
                if (key === 'o') {{
                    if (triggerButton(TEXT_OPEN)) {{
                        e.preventDefault(); e.stopPropagation();
                    }}
                }}

                // [Alt + K] Kintone
                if (key === 'k') {{
                    if (triggerButton(TEXT_KINTONE)) {{
                        e.preventDefault(); e.stopPropagation();
                    }}
                }}
            }};

            // Captureフェーズ(true)で登録して優先度を上げる
            doc.addEventListener('keydown', window.parent._legalAppKeyHandler_v2, true);

            // --- 初期フォーカスのためのポーリング ---
            // st_keyupは遅延ロードされるため、見つかるまでリトライする
            let attempt = 0;
            const maxAttempts = 20; // 0.2s * 20 = 4秒間試行
            
            const initFocusTimer = setInterval(() => {{
                // すでにフォーカスが当たっているか確認
                const active = window.parent.document.activeElement;
                const isInputActive = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'IFRAME');
                
                // まだ入力欄にフォーカスがない場合のみ実行
                if (!isInputActive) {{
                    if (doFocus()) {{
                        console.log("Initial focus set successfully.");
                        clearInterval(initFocusTimer);
                    }}
                }} else {{
                    // 既にどこかにフォーカスがあれば終了
                    clearInterval(initFocusTimer);
                }}

                attempt++;
                if (attempt >= maxAttempts) {{
                    clearInterval(initFocusTimer);
                }}
            }}, 200); // 200msごとにチェック

        }})();
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
    H_AddressHistory, H_ContactLink, Heir, RealEstateAsset, User, ContactLog
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
# 5. ヘルパー関数 (ビューワー & AI解析)
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

@st.cache_data(show_spinner=False)
def convert_pdf_to_images_cached(file_bytes: bytes):
    """PDFを画像リストに変換しキャッシュする"""
    try:
        return convert_from_bytes(file_bytes, dpi=200) # 解像度200dpiで変換
    except Exception as e:
        return None

def render_enhanced_document_viewer(file_bytes: bytes, file_type: str, key_prefix: str, base_width: int = 700):
    """
    汎用ドキュメントビューワー (拡大縮小・ページ送り機能付き)
    """
    with st.container(border=True):
        st.markdown("###### 📄 書類ビューワー")
        
        # 1. 画像化処理
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

        # 2. コントロールステートの初期化
        page_key = f"{key_prefix}_page"
        zoom_key = f"{key_prefix}_zoom"
        
        if page_key not in st.session_state: st.session_state[page_key] = 0
        if zoom_key not in st.session_state: st.session_state[zoom_key] = 100

        total_pages = len(images)
        current_page = st.session_state[page_key]

        # 3. ツールバー (ページ送り & ズーム)
        col_nav, col_zoom = st.columns([1, 1])
        
        with col_nav:
            # ページ送りボタン
            c_prev, c_info, c_next = st.columns([1, 2, 1])
            if c_prev.button("◀", key=f"{key_prefix}_prev", disabled=(current_page <= 0)):
                st.session_state[page_key] -= 1
                st.rerun()
            
            c_info.markdown(f"<div style='text-align: center; line-height: 2.3;'>{current_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
            
            if c_next.button("▶", key=f"{key_prefix}_next", disabled=(current_page >= total_pages - 1)):
                st.session_state[page_key] += 1
                st.rerun()

        with col_zoom:
            # ズームスライダー (50% ~ 200%)
            zoom = st.slider("拡大率 (%)", 50, 250, st.session_state[zoom_key], 10, key=f"{key_prefix}_slider")
            st.session_state[zoom_key] = zoom

        # 4. 画像表示 (スクロールコンテナ内)
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

def image_to_bytes(img: Image.Image, format: str = "JPEG") -> bytes:
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def search_cases_enhanced(session, keyword: str):
    """
    案件検索ロジック (被相続人氏名検索強化版)
    """
    base_query = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.manager),
        joinedload(Case.operator)
    )
    if not keyword:
        return base_query.order_by(Case.created_at.desc()).limit(10).all()

    clean_key = f"%{keyword.strip()}%"
    
    return base_query.join(Case.deceased_ref)\
        .outerjoin(Deceased.heirs)\
        .outerjoin(Heir.contact_links)\
        .outerjoin(H_ContactLink.contact)\
        .filter(
            or_(
                # 案件情報
                Case.case_number.ilike(clean_key),
                Case.client_name.ilike(clean_key),
                Case.client_name_kana.ilike(clean_key),
                Case.sol_case_number.ilike(clean_key),
                Case.referral_sec_phone.ilike(clean_key),
                
                # 被相続人情報 (個別フィールド + フルネーム結合検索)
                Deceased.name_last.ilike(clean_key),
                Deceased.name_first.ilike(clean_key),
                # フルネーム (スペースなし)
                (Deceased.name_last + Deceased.name_first).ilike(clean_key),
                # フルネーム (半角スペース)
                (Deceased.name_last + " " + Deceased.name_first).ilike(clean_key),
                # フルネーム (全角スペース)
                (Deceased.name_last + "　" + Deceased.name_first).ilike(clean_key),
                
                # 連絡先
                Contact.value.ilike(clean_key)
            )
        ).distinct().limit(20).all()

def normalize_text_space(text: str) -> str:
    if not text: return ""
    return text.replace(" ", "　").strip()

def normalize_text(text: str) -> str:
    if not text: return ""
    return unicodedata.normalize("NFKC", text).strip()

# ★修正: 名寄帳専用の強化プロンプト
def analyze_nayose_with_ai(image_inputs: Union[bytes, List[bytes]]) -> dict:
    try:
        llm = AIFactory.get_llm(mode="cloud", temperature=0.0)
        
        prompt_text = """
        あなたは日本の不動産登記・固定資産税の専門家（司法書士補助者）です。
        提供された画像は自治体が発行した「名寄帳（固定資産税課税明細書）」の複数ページにわたる一連の書類です。
        以下の高度な抽出・整形ルールに従い、全資産情報を網羅したJSONデータを作成してください。

        ## 前提条件と処理ルール
        1. **レイアウトの多様性**: この文書は自治体によってフォーマットが異なります。表のヘッダー（項目名）を探し、列と行の関係を視覚的に解析してください。
        2. **用語のゆらぎ吸収**: 以下の項目名は自治体によって表記が異なる場合があります。文脈から判断してマッピングしてください。
           - 所在地 (例: 所在、土地の所在、家屋の所在、所 在 地、所　在　地)
           - 地番/家屋番号 (例: 番地、地番、家屋番号)
           - 地目/種類 (例: 現況地目、登記地目、種類、構造)
           - 地積/床面積 (例: 登記地積、現況地積、課税地積、現況地目、登記地目、床面積) ※隣の列に「計」の列があればその値の方のみを読み取る
           - 評価額 (例: 価格、価 格、価　格、決定価格、評価額)
           - 課税標準額 (例: 課標、本則課税標準額)
        3. **複数行の処理**: 1つの物件情報が2行以上にまたがって記載されている場合があります。区切り線や行間隔に注意して1つのオブジェクトに結合してください。
        4. **所有者情報**: 文書のヘッダーまたは各行にある「所有者（納税義務者）」の氏名と住所も抽出してください。
        5. **ノイズ除去**: ページ番号、発行日、公印などの付帯情報は無視してください。不明瞭な文字は無理に推測せず `null` としてください。
        6. **空白スペースの除去**: 所在地や地目/種類など前後の関係を見て空白スペースを除いて出力してください。

        【重要：読み取りとデータ整形のルール】
        1. **行の認識と物件の特定（最重要）**:
           - 登録する不動産の数は所在地数が基本となります。2行にまたがって記載があるものは、基本的には所在地の記載がある行のものが正しい値になります。
             ただし、建物の地積/床面積は2行分を足した値の合計値（所在地の記載がある行の値とその上に記載がある値で例として45.54と60.45で105.99）となり計の列があればそこを読み取り、地目/種類は木造などではなく居宅などになります。
             また、建物の評価額は土地とは違う列にあるため注意すること。
           - 物件番号の列が一番左にあれば、その物件番号の記載の行のものが出力する不動産数となります。

        2. **誤読・OCRノイズの修正**:
           - 文字間の不自然なスペースは必ず除去してください。（例：「公　園」→「公園」、「宅　地」→「宅地」、「木　造」→「木造」、「居　宅」→「居宅」）
           - 地目で「公」一文字だけはなく「公園」や「公衆用道路」の読み取り漏れです。前後の文脈から補正してください。

        3. **必要のない値**:
           - 課税標準額の列にある固定資産税や都市計画税は必要ありませんので値として無視してください。

        4. **ページ跨ぎの処理**:
           - 2ページ目以降の先頭行の「所在」が空欄に見える場合でも、1ページ目の最後の住所を安易にコピーしないでください。
           - 2ページ目のヘッダーや、その行自体に記載されている所在（「同上」や「〜番地」など）を正確に読み取ってください。
           - ページが変わると、全く異なる所在（例：別の町名）の物件が始まっている可能性があります。

        5. **地番/家屋番号**:
           - 〇-〇の形（例：416-9など）になっていることがほとんどで、何丁目などの漢字はありません。
        
        6. **出力項目**:
           - 所在は、都道府県・市区町村が省略されている場合、書類全体のヘッダー等から補完して「完全な住所」にしてください。

        【都道府県ごとのルール】 
        1. 千葉県流山市東深井山ノ越〇〇〇は「千葉県流山市東深井」として読み取り、〇〇は地番として読み取る
        

        【出力JSONフォーマット】
        {
            "owner_name": "所有者氏名",
            "assets": [
                {
                    "type": "土地" または "家屋",
                    "location": "所在（都道府県から）",
                    "number": "地番 または 家屋番号",
                    "category_structure": "地目 または 家屋構造",
                    "area": "地積 または 床面積(合計値)",
                    "assessed_value": "評価額(円単位の数値)"
                }
            ]
        }
        """
        
        if isinstance(image_inputs, bytes):
            image_inputs = [image_inputs]
            
        content_list = [{"type": "text", "text": prompt_text}]
        
        for img_bytes in image_inputs:
            img_str = base64.b64encode(img_bytes).decode("utf-8")
            content_list.append({
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{img_str}"
            })

        message = HumanMessage(content=content_list)
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
    # メインエリア上部
    # ------------------------------------------
    enable_keyboard_shortcuts()
    st.caption("⌨️ ショートカット: [Alt+S] 検索 | [Alt+O] フォルダを開く | [Alt+K] Kintone連携")

    search_query = st_keyup(
        "🔍 案件を検索 (電話番号・氏名・案件番号など)", 
        placeholder="案件番号、氏名、電話番号で検索...",
        key="case_search_bar",
        debounce=300
    )

    filtered_cases = search_cases_enhanced(session, search_query)
    target_case_id = st.session_state.get("selected_case_id")

    if search_query:
        if len(filtered_cases) == 1:
            auto_target = filtered_cases[0].case_id
            if target_case_id != auto_target:
                st.session_state["selected_case_id"] = auto_target
                st.rerun()
        
        if filtered_cases:
            st.caption(f"検索結果: {len(filtered_cases)}件")
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
                d_name = f"{c.deceased_ref.name_last} {c.deceased_ref.name_first}" if c.deceased_ref else "未登録"
                label_text = f"【{c.case_number}】 {c.client_name} 様 (被相続人: {d_name})"
                btn_type = "primary" if target_case_id == c.case_id else "secondary"
                if st.button(label_text, key=f"sel_{c.case_id}", use_container_width=True, type=btn_type):
                    st.session_state["selected_case_id"] = c.case_id
                    st.rerun()
            st.divider()
        else:
            st.warning("該当する案件は見つかりませんでした。")
    
    if not target_case_id and filtered_cases and not search_query:
        target_case_id = filtered_cases[0].case_id
        st.session_state["selected_case_id"] = target_case_id

    if not target_case_id:
        st.info("👈 上部の検索バーから案件を検索するか、左のメニューを操作してください。")
        session.close()
        return

    # === 詳細画面 ===
    current_case = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs)
    ).filter_by(case_id=target_case_id).first()

    if not current_case:
        st.error("案件データの取得に失敗しました。")
        session.close()
        return

    st.title(f"{current_case.case_number}: {current_case.client_name} 様")

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
    
    # ==========================================
    # A. 案件概要・基本情報
    # ==========================================
    if menu == "🏠 案件概要・基本情報":
        st.subheader("基本情報・操作")

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
                            # ==========================================
                            # ★修正: 電話番号・メールアドレスの除外処理
                            # ==========================================
                            data = json.loads(ji)
                            data.pop("TEL", None)
                            data.pop("メールアドレス", None)
                            
                            import_kintone_json(data, target_case_id=target_case_id)
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
                d_addr = get_address_info("deceased", d.id)
                with st.form("quick_fam_edit"):
                    st.caption("基本情報")
                    c1, c2 = st.columns(2)
                    new_dl = c1.text_input("被相続人 姓", value=d.name_last)
                    new_df = c2.text_input("被相続人 名", value=d.name_first)
                    c3, c4 = st.columns(2)
                    new_dl_k = c3.text_input("フリガナ (姓)", value=d.name_last_kana or "")
                    new_df_k = c4.text_input("フリガナ (名)", value=d.name_first_kana or "")
                    st.caption("日付情報")
                    c5, c6 = st.columns(2)
                    new_dob = c5.date_input("生年月日", value=d.date_of_birth if d.date_of_birth else None)
                    if new_dob: c5.caption(f"和暦: {convert_seireki_to_wareki(new_dob)}")
                    new_dod = c6.date_input("死亡日", value=d.date_of_birth if d.date_of_death else None)
                    if new_dod: c6.caption(f"和暦: {convert_seireki_to_wareki(new_dod)}")
                    st.caption("住所・本籍")
                    new_honseki = st.text_input("本籍地", value=d.hometown or "")
                    z, p = st.columns([1, 2])
                    new_zip = z.text_input("郵便番号", value=d_addr.get("zip_code", ""))
                    new_pref = p.text_input("都道府県", value=d_addr.get("prefecture", ""))
                    new_city = st.text_input("市区町村・番地", value=f"{d_addr.get('city_ward_town') or ''}{d_addr.get('street_address') or ''}")
                    new_bldg = st.text_input("建物名", value=d_addr.get("building_name", ""))
                    if st.form_submit_button("保存"):
                        update_deceased(
                            d.id, name_last=new_dl, name_first=new_df,
                            kana_last=new_dl_k, kana_first=new_df_k,
                            dob=str(new_dob) if new_dob else None, dod=str(new_dod) if new_dod else None,
                            hometown=new_honseki, last_zip_code=new_zip, last_pref=new_pref,
                            last_city=new_city, last_street="", last_building=new_bldg
                        )
                        st.toast("更新しました", icon="✅"); time.sleep(0.5); st.rerun()
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

        # ==================================================
        # ★ 追加: AI自動取込メモ・対応履歴の表示エリア
        # ==================================================
        st.divider()
        st.subheader("📝 会議メモ・対応履歴 (AI自動連携)")
        
        # データベースからこの案件の履歴を取得
        logs = session.query(ContactLog).filter_by(case_id=target_case_id).order_by(ContactLog.log_id.desc()).all()
        
        if logs:
            for log in logs:
                # 自動取込かどうかでアイコンを変える
                icon = "🤖" if "【自動取込】" in log.contact_content else "🗒️"
                # タイトル用に本文の1行目を切り出す
                title = log.contact_content.split('\n')[0]
                if len(title) > 40: title = title[:40] + "..."
                
                with st.expander(f"{icon} {title}", expanded=True):
                    st.text(log.contact_content)  # 本文をそのまま表示
        else:
            st.info("まだ履歴はありません。")
            st.caption("※ Gmailから「メモ」が届くと、ここに自動で追加されます。")

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
    # C. 不動産登録 (★修正: 縦積みレイアウト)
    # ==========================================
    elif menu == "🏘️ 不動産 登録":
        st.subheader("🏘️ 不動産・名寄帳読取")
        
        # 1. ファイルアップロード (メインエリア上部)
        uploaded_nayose = st.file_uploader("名寄帳(PDF/画像)をアップロード", type=["pdf", "png", "jpg"], key="up_nayose")
        
        # 2. プレビュー & 解析 (アップロードされたら表示)
        if uploaded_nayose:
            file_bytes = uploaded_nayose.getvalue()
            
            # ビューワー (幅広設定: base_width=1000)
            render_enhanced_document_viewer(file_bytes, uploaded_nayose.type, "nayose_view", base_width=1000)
            
            # 自動解析
            if "nayose_file_name" not in st.session_state or st.session_state["nayose_file_name"] != uploaded_nayose.name:
                with st.spinner("AIが書類を解析中..."):
                    target_images_bytes = []
                    if uploaded_nayose.type == "application/pdf":
                        try:
                            images = convert_from_bytes(file_bytes, dpi=200)
                            for img in images:
                                buf = BytesIO()
                                img.convert("RGB").save(buf, format="JPEG")
                                target_images_bytes.append(buf.getvalue())
                        except: pass
                    else:
                        target_images_bytes.append(file_bytes)
                    
                    if target_images_bytes:
                        result = analyze_nayose_with_ai(target_images_bytes)
                        if "error" not in result:
                            st.session_state["nayose_result"] = result
                            st.session_state["nayose_file_name"] = uploaded_nayose.name
                            st.toast("解析完了！内容を確認してください", icon="✅")
                        else: st.error("解析失敗")
        else:
            st.info("☝️ 書類をアップロードすると、ここにプレビューが表示されます。")

        # 3. 編集・登録フォーム (その下)
        if "nayose_result" in st.session_state and st.session_state["nayose_result"]:
            st.divider()
            st.markdown("##### 📝 解析結果・編集")
            res = st.session_state["nayose_result"]
            df_assets = pd.DataFrame(res.get("assets", []))
            
            st.markdown(f"**所有者:** `{res.get('owner_name')}`")
            st.caption("AI解析結果です。修正して登録してください。")

            column_config = {
                "type": st.column_config.SelectboxColumn("種類", options=["土地", "家屋", "マンション"], required=True),
                "location": st.column_config.TextColumn("所在", width="medium"),
                "number": st.column_config.TextColumn("地番/家屋番号", width="small"),
                "category_structure": st.column_config.TextColumn("地目/構造", width="small"),
                "area": st.column_config.NumberColumn("地積/床面積"),
                "assessed_value": st.column_config.NumberColumn("評価額 (円)", format="%d"),
            }
            edited_assets = st.data_editor(df_assets, column_config=column_config, num_rows="dynamic", use_container_width=True, key="nayose_editor")
            
            if st.button("💾 この内容で登録する", type="primary", use_container_width=True):
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
                    st.success(f"{count}件登録しました！")
                    time.sleep(1)
                    st.session_state["nayose_result"] = None
                    st.rerun()
                except Exception as e: st.error(f"エラー: {e}")

        # 4. 登録済み一覧 (最下部)
        st.divider()
        st.subheader("📋 登録済み不動産一覧")
        real_estates = session.query(RealEstateAsset).filter_by(case_id=target_case_id).all()
        if real_estates:
            for re_asset in real_estates:
                label = f"[{re_asset.property_type}] {re_asset.location} {re_asset.lot_number or re_asset.house_number or ''}"
                with st.expander(label):
                    is_edit = st.toggle("編集モード", key=f"toggle_re_{re_asset.id}")
                    if is_edit:
                        with st.form(f"edit_re_{re_asset.id}"):
                            col_e1, col_e2 = st.columns(2)
                            e_loc = col_e1.text_input("所在", value=re_asset.location)
                            e_num = col_e2.text_input("地番/家屋番号", value=re_asset.lot_number or re_asset.house_number or "")
                            col_e3, col_e4 = st.columns(2)
                            e_cat = col_e3.text_input("地目/構造", value=re_asset.land_category or re_asset.structure or "")
                            e_area = col_e4.text_input("地積/床面積", value=str(re_asset.land_area or re_asset.floor_area or ""))
                            e_val = st.number_input("評価額", value=int(re_asset.assessed_value or 0))
                            if st.form_submit_button("変更を保存"):
                                re_asset.location = e_loc
                                if re_asset.property_type == "Land":
                                    re_asset.lot_number = e_num
                                    re_asset.land_category = e_cat
                                    try: re_asset.land_area = float(e_area)
                                    except: pass
                                else:
                                    re_asset.house_number = e_num
                                    re_asset.structure = e_cat
                                    re_asset.floor_area = e_area
                                re_asset.assessed_value = e_val
                                session.commit(); st.toast("保存しました", icon="💾"); time.sleep(0.5); st.rerun()
                    else:
                        c1, c2, c3 = st.columns(3)
                        c1.write(f"**地目/構造:** {re_asset.land_category or re_asset.structure}")
                        c2.write(f"**面積:** {re_asset.land_area or re_asset.floor_area}")
                        val_display = getattr(re_asset, 'assessed_value', 0)
                        c3.write(f"**評価額:** {val_display:,.0f} 円" if val_display else "-")
                        if st.button("削除", key=f"del_re_{re_asset.id}"):
                            session.delete(re_asset); session.commit(); st.toast("削除しました", icon="🗑️"); time.sleep(0.5); st.rerun()
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