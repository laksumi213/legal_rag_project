# src/legal_system/ui/components/inbox.py
import json
import time
import streamlit as st
from src.services.deceased_service import find_cases_by_attributes
from src.legal_system.models.tables import Case
from src.legal_system.core.database_manager import DatabaseManager

# ★修正: 自動更新(30秒)に対応するため、TTLを短く(5秒)設定
# これにより、リフレッシュ時に古いキャッシュが表示され続けるのを防ぐ
@st.cache_data(ttl=5, show_spinner="新着通知を確認中...")
def _get_cached_pendings(_gmail_service):
    return _gmail_service.get_pending_notes()

def render_inbox(session, gmail_service=None, scanner_service=None):
    if not gmail_service:
        return

    try:
        # キャッシュされた通知リストを取得
        pendings = _get_cached_pendings(gmail_service)
        if not pendings:
            return

        st.warning(f"📨 未処理の通知が {len(pendings)} 件あります")
        
        with st.expander("📥 受信トレイを確認 (未紐付け)", expanded=bool(len(pendings) > 0)):
            for n in pendings:
                is_file = n.message_id and n.message_id.startswith("FILE-")
                icon = "📄" if is_file else "🎙️" if "録音" in (n.subject or "") else "✉️"
                date_str = n.received_at.strftime('%m/%d %H:%M')
                
                st.markdown(f"**{icon} {n.subject}** ({date_str})")
                if n.ai_summary:
                    st.caption(n.ai_summary.replace("\n", "  \n"))

                with st.container(border=True):
                    candidates = []
                    try:
                        if is_file:
                            info = json.loads(n.body_text)
                            analysis = info.get("analysis", {})
                            candidates = analysis.get("case_candidates", [])
                        else:
                            names = json.loads(n.detected_names or "[]")
                            for nm in names:
                                hits = find_cases_by_attributes(client_name=nm) or find_cases_by_attributes(deceased_name=nm)
                                for h in hits:
                                    if not any(c['case_id'] == h['case_id'] for c in candidates):
                                        candidates.append(h)
                    except Exception:
                        pass

                    cols_act = st.columns([3, 1])
                    with cols_act[0]:
                        target_id = None
                        
                        if candidates:
                            st.info(f"💡 {len(candidates)} 件の候補が見つかりました。")
                            cand_opts = {f"【{c['case_number']}】 {c['client_name']}": c['case_id'] for c in candidates}
                            # デフォルトで先頭を選択
                            sel_cand_label = st.radio("紐付け先を選択", list(cand_opts.keys()), key=f"rad_{n.id}")
                            target_id = cand_opts[sel_cand_label]
                        else:
                            st.warning("自動マッチする案件が見つかりませんでした。手動で選択してください。")
                            
                            # 全案件から検索するセレクトボックス
                            recent_cases = session.query(Case).order_by(Case.created_at.desc()).limit(50).all()
                            case_map = {f"【{c.case_number}】 {c.client_name}": c.case_id for c in recent_cases}
                            
                            # ★ポイント: keyをユニークにして状態を維持
                            selected_label = st.selectbox(
                                "案件を検索・選択", 
                                ["(選択してください)"] + list(case_map.keys()),
                                key=f"manual_sel_{n.id}"
                            )
                            
                            if selected_label != "(選択してください)":
                                target_id = case_map[selected_label]

                    with cols_act[1]:
                        st.write("")
                        # 登録ボタン
                        if st.button("✅ 登録", key=f"btn_proc_{n.id}", type="primary", use_container_width=True):
                            if target_id:
                                try:
                                    success = False
                                    if is_file:
                                        if scanner_service:
                                            # process_pending_bufferの呼び出し
                                            success = scanner_service.process_pending_buffer(n.id, target_id)
                                        else:
                                            st.error("スキャナーサービスが無効です")
                                    else:
                                        success = gmail_service.link_note_to_case_manually(n.id, target_id)
                                    
                                    if success:
                                        st.success("完了")
                                        st.cache_data.clear() # キャッシュを破棄して最新化
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("処理に失敗しました (詳細はログを確認)")
                                except Exception as e:
                                    st.error(f"システムエラー: {e}")
                            else:
                                st.error("案件を選択してください")
                        
                        if st.button("無視", key=f"ign_{n.id}", use_container_width=True):
                            gmail_service.ignore_note(n.id)
                            st.cache_data.clear()
                            st.rerun()
                st.divider()

    except Exception as e:
        st.error(f"通知取得エラー: {e}")