# src/services/gmail_watcher_service.py

import os
import json
import time
import logging
import base64
import difflib
from datetime import datetime
from typing import List, Optional, Dict, Any

# Google API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# LangChain / AI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser

# データベース / SQL
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

# 内部モジュール
from legal_system.core.database_manager import DatabaseManager
from legal_system.core.ai_factory import AIFactory
from legal_system.models.tables import Case, Deceased, ContactLog, IncomingNoteBuffer, Heir

# ロガー設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Gmail API スコープ (読み取り専用)
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailWatcherService:
    def __init__(self):
        self.db = DatabaseManager()
        self.creds = self._authenticate_gmail()
        self.service = build('gmail', 'v1', credentials=self.creds) if self.creds else None
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

    def _authenticate_gmail(self):
        token_path = 'token.json'
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception: return None
            if creds:
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())
        return creds

    def _get_decoded_body(self, payload: dict) -> str:
        def decode_data(data):
            if not data: return ""
            return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        if 'body' in payload and 'data' in payload['body']:
            return decode_data(payload['body']['data'])
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    return decode_data(part['body']['data'])
        return ""

    def poll_and_process(self):
        if not self.service: return
        logger.info("📧 Gmail: 新着会議メモを確認中...")
        session = None
        try:
            query = 'from:gemini-notes@google.com subject:"メモ" newer_than:7d'
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            if not messages: return

            session = self.db._get_session()
            processed_count = 0

            for msg in messages:
                msg_id = msg['id']
                if session.query(IncomingNoteBuffer).filter_by(message_id=msg_id).first():
                    continue

                detail = self.service.users().messages().get(userId='me', id=msg_id).execute()
                payload = detail.get('payload', {})
                subject = next((h['value'] for h in payload.get('headers', []) if h['name'] == 'Subject'), 'No Subject')
                body_text = self._get_decoded_body(payload) or detail.get('snippet', '')

                logger.info(f"📥 新規メモ受信: {subject}")
                ai_result = self._analyze_email_with_ai(body_text)
                detected_names = ai_result.get("names", [])
                
                # --- ★修正点: summary が辞書で返ってきた場合に文字列へ変換 ---
                summary_raw = ai_result.get("summary", "（要約なし）")
                if isinstance(summary_raw, dict):
                    title = summary_raw.get('title', '会議メモ')
                    points = summary_raw.get('points', [])
                    summary_text = f"{title}\n" + "\n".join([f"- {p}" for p in points])
                else:
                    summary_text = str(summary_raw)

                # あいまい名寄せ実行
                linked_case = self._find_case_by_names_fuzzy(session, detected_names)
                
                status = "PENDING"
                linked_case_id = None
                formatted_content = f"【AI要約】{summary_text}\n\n--- 以下、メール全文 ---\n{body_text}"

                if linked_case:
                    logger.info(f"   ✅ 案件ヒット(Fuzzy): {linked_case.client_name}")
                    self._save_to_contact_log(session, linked_case.case_id, formatted_content)
                    status = "LINKED"
                    linked_case_id = linked_case.case_id
                else:
                    logger.info("   ⏳ 案件未登録 -> 保留バッファへ保存")

                new_note = IncomingNoteBuffer(
                    message_id=msg_id,
                    received_at=datetime.now(),
                    subject=subject,
                    body_text=formatted_content,
                    detected_names=json.dumps(detected_names, ensure_ascii=False),
                    ai_summary=summary_text, # 文字列として保存
                    status=status,
                    linked_case_id=linked_case_id
                )
                session.add(new_note)
                processed_count += 1
                
                if processed_count < len(messages):
                    logger.info("   💤 API負荷軽減のため10秒待機...")
                    time.sleep(10)
            
            session.commit()
            if processed_count > 0:
                logger.info(f"🎉 {processed_count}件のメモを処理しました。")

        except Exception as e:
            logger.error(f"Gmail Polling Error: {e}")
            if session: session.rollback()
        finally:
            if session: session.close()

    def _analyze_email_with_ai(self, text: str) -> Dict[str, Any]:
        prompt = f"""会議メモを解析し、以下のJSON形式で返してください。
        1. names: 会議に関わる顧客・被相続人の氏名リスト（行政書士名は除外）。
        2. summary: 会議の内容を「title（見出し）」と「points（3点の箇条書きリスト）」に分けて要約。
        本文: {text[:4000]}"""
        try:
            res = self.llm.invoke(prompt)
            content = res.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except:
            return {"names": [], "summary": "AI解析失敗"}

    def _find_case_by_names_fuzzy(self, session, names: List[str]) -> Optional[Case]:
        if not names: return None
        
        all_cases = session.query(Case).options(joinedload(Case.deceased_ref)).all()
        candidate_map = {}
        for c in all_cases:
            candidate_map[(c.client_name or "").replace(" ", "").replace("　", "")] = c
            if c.deceased_ref:
                d = c.deceased_ref
                d_full = ((d.name_last or "") + (d.name_first or "")).replace(" ", "").replace("　", "")
                if d_full: candidate_map[d_full] = c
                for h in (d.heirs or []):
                    h_full = ((h.name_last or "") + (h.name_first or "")).replace(" ", "").replace("　", "")
                    if h_full: candidate_map[h_full] = c

        for name in names:
            target = name.replace(" ", "").replace("　", "")
            if len(target) < 2: continue
            if target in candidate_map: return candidate_map[target]
            best_match = difflib.get_close_matches(target, candidate_map.keys(), n=1, cutoff=0.6)
            if best_match:
                return candidate_map[best_match[0]]
        return None

    def _save_to_contact_log(self, session, case_id, content):
        log = ContactLog(case_id=case_id, contact_content=content)
        session.add(log)

    def retry_linking_pending_notes(self):
        session = self.db._get_session()
        try:
            pendings = session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()
            for note in pendings:
                names = json.loads(note.detected_names or "[]")
                linked = self._find_case_by_names_fuzzy(session, names)
                if linked:
                    self._save_to_contact_log(session, linked.case_id, note.body_text)
                    note.status = "LINKED"
                    note.linked_case_id = linked.case_id
            session.commit()
        except Exception as e: logger.error(f"Retry error: {e}")
        finally: session.close()