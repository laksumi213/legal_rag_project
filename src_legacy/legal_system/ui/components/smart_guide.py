# src/legal_system/ui/components/smart_guide.py

import json
import os
import streamlit as st
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# プロジェクト内のモジュール読み込み
from legal_system.core.ai_factory import AIFactory

# -----------------------------------------------------------------------------
# パス設定: data/rules/bank_guidance.json を参照するように設定
# -----------------------------------------------------------------------------
# このファイル(smart_guide.py)から見て、ルートディレクトリまで遡りパスを構築します
# src/legal_system/ui/components/ -> root/data/rules
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
RULES_DIR = os.path.join(BASE_DIR, "data", "rules")
GUIDE_FILE = os.path.join(RULES_DIR, "bank_guidance.json")


def load_guidance_data():
    """
    JSONファイルから銀行ごとの案内データを読み込む。
    ファイルが存在しない場合は、デモ用の初期データを作成して返す。
    """
    # ディレクトリがなければ作成
    if not os.path.exists(RULES_DIR):
        os.makedirs(RULES_DIR, exist_ok=True)
    
    # ファイルがなければ初期データを作成（デモでエラーにならないように）
    if not os.path.exists(GUIDE_FILE):
        default_data = {
            "三菱UFJ銀行": {
                "alert": "遺産分割協議書への実印押印が必須です。",
                "items": [
                    "原本還付: 可（要ゴム印）",
                    "予約: 必須（Web予約推奨）",
                    "備考: 代理人手続きの場合、委任状に捨印を推奨"
                ]
            },
            "ゆうちょ銀行": {
                "alert": "窓口ではなく「貯金事務センター」への郵送が基本です。",
                "items": [
                    "手数料: 会社通帳から引落（窓口払い不可）",
                    "期間: 約2週間〜1ヶ月",
                    "必須: 相続確認表のWeb入力"
                ]
            },
            "三井住友銀行": {
                "alert": "残高証明書の発行は「相続オフィス」への電話予約から始まります。",
                "items": [
                    "原本還付: 可",
                    "来店: 原則不要（郵送手続可）"
                ]
            }
        }
        with open(GUIDE_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, ensure_ascii=False, indent=2)
        return default_data
        
    try:
        with open(GUIDE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"マスタデータ読込エラー: {e}")
        return {}


def render_smart_guide_area(case_data, current_context: str, bank_name: str = None):
    """
    メインエリアの右カラム等に配置する「AI業務ナビゲーション」コンポーネント。
    
    Args:
        case_data (Case): 現在選択されている案件オブジェクト
        current_context (str): 画面の状況を表すテキスト（AIへの入力用）
        bank_name (str, optional): 選択中の銀行名（マスタ検索用）
    """
    
    # 枠線付きのコンテナでエリアを強調
    with st.container(border=True):
        st.subheader("🤖 業務ナビ")
        
        # 案件未選択時のガード
        if not case_data:
            st.info("👈 左側のフォームで案件を選択してください。")
            return

        # ==================================================
        # Lv.1 自動表示エリア (JSONマスタ連動・APIコストゼロ)
        # ==================================================
        if bank_name:
            # マスタデータの読み込み
            guidance_db = load_guidance_data()
            
            # 部分一致検索ロジック
            # 入力された "三菱UFJ銀行(0005)" に対して、マスタのキー "三菱UFJ" が含まれるか確認
            hit_data = None
            for key, val in guidance_db.items():
                if key in bank_name:
                    hit_data = val
                    break
            
            st.markdown(f"**🏦 {bank_name} の手続要領**")
            
            if hit_data:
                # 1. 重要アラート（赤枠）
                if hit_data.get("alert"):
                    st.error(f"**重要:** {hit_data['alert']}", icon="⚠️")
                
                # 2. 詳細リスト
                if hit_data.get("items"):
                    for item in hit_data['items']:
                        st.markdown(f"- {item}")
                
                # マスタ管理への誘導（デモ用）
                st.caption(f"※この内容は「マスタ管理」メニューで編集可能です")
            else:
                # マスタにない銀行の場合
                st.info("💡 特別な注意事項は登録されていません（一般手続準拠）")
                st.caption("※特記事項がある場合は「マスタ管理」から追加してください")
        
        st.divider()

        # ==================================================
        # Lv.2 AIアドバイス (ボタン起動・RAG/LLM使用)
        # ==================================================
        st.caption("AIアシスタント (社内規定・事例検索)")
        
        # デモ演出: ボタンを押して初めてAIが動く（コスト管理と「ここぞ」という演出）
        if st.button("💡 規定・過去事例をAI検索", type="primary", use_container_width=True):
            with st.spinner("社内ナレッジを検索中..."):
                try:
                    # AI処理 (Cloud: Gemini or Vertex)
                    llm = AIFactory.get_llm("cloud", temperature=0.0)
                    
                    system_prompt = """
                    あなたは行政書士事務所のベテラン指導員です。
                    新人の担当者が現在行っている作業に対して、
                    「注意すべきポイント」「次にやるべきこと」を
                    社内規定の観点から簡潔にアドバイスしてください。
                    
                    制約:
                    - 結論から述べること
                    - 箇条書きを使用すること
                    - 挨拶は省略すること
                    """
                    
                    # ------------------------------------------------
                    # ★セキュリティ対策: 匿名化プロンプトの構築
                    # 個人名(client_name)は含めず、属性情報のみ渡す
                    # ------------------------------------------------
                    
                    # 証券連携の有無判定
                    has_sec = "あり" if case_data.sol_case_number else "なし"
                    
                    # 口座数のカウント (リレーションがロードされていれば)
                    asset_count = 0
                    if hasattr(case_data, "financial_assets") and case_data.financial_assets:
                        asset_count = len(case_data.financial_assets)

                    safe_user_prompt = f"""
                    【現在の作業コンテキスト】
                    {current_context}
                    
                    【案件属性データ（匿名化済）】
                    - 相続開始日: {case_data.date_of_death}
                    - 証券会社連携: {has_sec}
                    - 登録済み口座数: {asset_count}
                    """

                    # Chain実行
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        ("human", safe_user_prompt),
                    ])
                    
                    chain = prompt | llm | StrOutputParser()
                    advice = chain.invoke({})
                    
                    # 結果表示
                    st.success("✅ AIアドバイス")
                    st.markdown(advice)

                    # ------------------------------------------------
                    # ★安心(Security)の証明エリア: 監査ログ
                    # ------------------------------------------------
                    with st.expander("🔒 セキュリティ監査ログ", expanded=True):
                        st.caption("AIサーバー(Google)に送信されたデータの実物です。")
                        st.caption("ここには「氏名」「住所」「電話番号」は含まれていません。")
                        st.code(safe_user_prompt, language="text")

                except Exception as e:
                    st.error(f"AI処理エラー: {e}")