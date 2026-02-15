# src/services/gmail_watcher_service.py

import base64
import difflib
import json
import logging
import os
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, Generator, List, Optional

import google.generativeai as genai
from google.auth.transport.requests import Request

# Google API
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# LangChain / AI
# from langchain_core.output_parsers import JsonOutputParser # 未使用なら削除可
# データベース / SQL
from sqlalchemy.orm import joinedload

from legal_system.core.ai_factory import AIFactory
from legal_system.core.config import Config

# 内部モジュール
from legal_system.core.database_manager import DatabaseManager
from legal_system.models.tables import Case, ContactLog, IncomingNoteBuffer
from legal_system.utils.retry_decorator import retry_with_backoff

# ロガー設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Gmail API スコープ (読み取り専用)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailWatcherService:
    def __init__(self):
        self.db = DatabaseManager()
        self.creds = self._authenticate_gmail()
        self.service = (
            build("gmail", "v1", credentials=self.creds) if self.creds else None
        )

        # LangChain用
        self.llm = AIFactory.get_llm(mode="cloud", temperature=0.0)

        # 音声処理用に直接Geminiクライアントを設定
        if os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def _authenticate_gmail(self):
        token_path = "token.json"
        creds = None
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    return None
            if creds:
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
        return creds

    def _get_decoded_body(self, payload: dict) -> str:
        def decode_data(data):
            if not data:
                return ""
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        if "body" in payload and "data" in payload["body"]:
            return decode_data(payload["body"]["data"])

        # 本文探索も再帰的に行うのがベストだが、ここでは簡易的に text/plain を探す
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and "data" in part.get(
                    "body", {}
                ):
                    return decode_data(part["body"]["data"])
        return ""

    @retry_with_backoff(
        max_retries=3, backoff_factor=2.0, exceptions=(HttpError, TimeoutError)
    )
    def _get_attachment_data(self, msg_id: str, attachment_id: str) -> Optional[bytes]:
        """Gmailから添付ファイルの生データを取得（リトライ対応版）"""
        attachment = (
            self.service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=msg_id, id=attachment_id)
            .execute()
        )
        return base64.urlsafe_b64decode(attachment["data"])

    def _walk_parts(
        self, part: Dict[str, Any]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        メールのパートを再帰的に探索してフラットなリストにするヘルパー関数。
        これにより、multipart/alternative 内のネストされた添付ファイルも検出可能になる。
        """
        yield part
        if "parts" in part:
            for sub_part in part["parts"]:
                yield from self._walk_parts(sub_part)

    def poll_and_process(self):
        if not self.service:
            return
        logger.info("📧 Gmail: 新着会議メモを確認中...")
        session = None
        try:
            target_senders = ["gemini-notes@google.com"]
            target_keywords = ["録音", "ボイス"]

            if target_senders:
                senders_part = f"from:({' OR '.join(target_senders)} OR me)"
            else:
                senders_part = "from:(gemini-notes@google.com OR me)"

            conditions = ['subject:"メモ"']
            for kw in target_keywords:
                conditions.append(f"subject:{kw}")
                conditions.append(f"filename:{kw}")

            conditions_part = f"({' OR '.join(conditions)})"
            query = f"{senders_part} {conditions_part} newer_than:7d"

            logger.info(f"🔎 Generated Query: {query}")

            results = (
                self.service.users().messages().list(userId="me", q=query).execute()
            )
            messages = results.get("messages", [])
            if not messages:
                logger.info("   -> 対象のメールは見つかりませんでした。")
                return

            session = self.db._get_session()
            processed_count = 0

            for msg in messages:
                msg_id = msg["id"]
                if (
                    session.query(IncomingNoteBuffer)
                    .filter_by(message_id=msg_id)
                    .first()
                ):
                    continue

                detail = (
                    self.service.users()
                    .messages()
                    .get(userId="me", id=msg_id)
                    .execute()
                )
                payload = detail.get("payload", {})
                subject = next(
                    (
                        h["value"]
                        for h in payload.get("headers", [])
                        if h["name"] == "Subject"
                    ),
                    "No Subject",
                )
                body_text = self._get_decoded_body(payload) or detail.get("snippet", "")

                # --- 【修正】音声ファイルの検出と処理 (再帰対応) ---
                audio_summary = ""
                has_audio = False

                # _walk_partsを使って、ネストされたパートも含めて全てチェックする
                for part in self._walk_parts(payload):
                    fname = part.get("filename", "").lower()

                    # 音声ファイルの拡張子チェック
                    if fname and fname.endswith((".m4a", ".mp3", ".wav", ".aac")):
                        logger.info(f"   🎙️ 音声ファイルを検出: {fname}")
                        att_id = part["body"].get("attachmentId")

                        if att_id:
                            audio_data = self._get_attachment_data(msg_id, att_id)
                            if audio_data:
                                logger.info("   ⏳ 音声をAIに送信中(文字起こし)...")
                                try:
                                    # 音声解析の実行
                                    audio_summary_part = (
                                        self._transcribe_audio_with_gemini(
                                            audio_data, fname
                                        )
                                    )
                                    has_audio = True
                                    body_text += f"\n\n--- 🎙️ 音声解析結果 ({fname}) ---\n{audio_summary_part}"
                                    # 複数の音声ファイルがある場合も考慮して追記する形にする
                                except Exception as e:
                                    logger.error(f"   ❌ 音声解析失敗: {e}")
                                    body_text += f"\n\n（※音声解析エラー: {e}）"
                # ------------------------------------------------

                if not has_audio and not body_text.strip():
                    body_text = "（本文なし・音声ファイルなし）"

                logger.info(f"📥 新規メモ受信: {subject}")

                ai_result = self._analyze_email_with_ai(body_text)
                detected_names = ai_result.get("names", [])

                summary_raw = ai_result.get("summary", "（要約なし）")
                if isinstance(summary_raw, dict):
                    title = summary_raw.get("title", "会議メモ")
                    points = summary_raw.get("points", [])
                    summary_text = f"{title}\n" + "\n".join([f"- {p}" for p in points])
                else:
                    summary_text = str(summary_raw)

                linked_case = self._find_case_by_names_fuzzy(session, detected_names)

                status = "PENDING"
                linked_case_id = None
                formatted_content = f"【AI要約】{summary_text}\n\n--- 以下、メール全文・音声解析 ---\n{body_text}"

                if linked_case:
                    logger.info(f"   ✅ 案件ヒット(Fuzzy): {linked_case.client_name}")
                    self._save_to_contact_log(
                        session, linked_case.case_id, formatted_content
                    )
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
                    ai_summary=summary_text,
                    status=status,
                    linked_case_id=linked_case_id,
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
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    def _transcribe_audio_with_gemini(self, audio_data: bytes, filename: str) -> str:
        """Geminiを使って音声をテキスト化・要約する (Config参照版)"""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=os.path.splitext(filename)[1], delete=False
            ) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Geminiにアップロード
            myfile = genai.upload_file(tmp_path)

            # Configからモデル名を取得 (一元管理)
            target_model = Config.VISION_AUDIO_MODEL
            logger.info(f"   🤖 使用モデル: {target_model}")

            model = genai.GenerativeModel(target_model)

            prompt = "この音声ファイルは行政書士と依頼者の会議録音です。内容を詳細に文字起こしし、重要なポイントを要約してください。"

            response = model.generate_content([prompt, myfile])

            os.remove(tmp_path)
            return response.text

        except Exception as e:
            logger.error(f"Audio Transcribe Error: {e}")
            error_msg = str(e)

            # Configのモデル名が使えなかった場合のヒント
            if "404" in error_msg or "not found" in error_msg.lower():
                return f"（音声解析エラー: モデル '{Config.VISION_AUDIO_MODEL}' が見つかりません。src/legal_system/core/config.py の VISION_AUDIO_MODEL を 'gemini-1.5-flash-001' 等に変更してください。）"

            return f"（音声解析エラー: {e}）"

    def _analyze_email_with_ai(self, text: str) -> Dict[str, Any]:
        prompt = f"""会議メモ（または音声解析結果）を解析し、以下のJSON形式で返してください。
        1. names: 会議に関わる顧客・被相続人の氏名リスト（行政書士名は除外）。
        2. summary: 会議の内容を「title（見出し）」と「points（3点の箇条書きリスト）」に分けて要約。
        本文: {text[:40000]}"""
        try:
            res = self.llm.invoke(prompt)
            content = res.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except:
            return {"names": [], "summary": "AI解析失敗"}

    def _find_case_by_names_fuzzy(self, session, names: List[str]) -> Optional[Case]:
        if not names:
            return None
        all_cases = session.query(Case).options(joinedload(Case.deceased_ref)).all()
        candidate_map = {}
        for c in all_cases:
            candidate_map[(c.client_name or "").replace(" ", "").replace("　", "")] = c
            if c.deceased_ref:
                d = c.deceased_ref
                d_full = (
                    ((d.name_last or "") + (d.name_first or ""))
                    .replace(" ", "")
                    .replace("　", "")
                )
                if d_full:
                    candidate_map[d_full] = c
                for h in d.heirs or []:
                    h_full = (
                        ((h.name_last or "") + (h.name_first or ""))
                        .replace(" ", "")
                        .replace("　", "")
                    )
                    if h_full:
                        candidate_map[h_full] = c

        for name in names:
            target = name.replace(" ", "").replace("　", "")
            if len(target) < 2:
                continue
            if target in candidate_map:
                return candidate_map[target]
            best_match = difflib.get_close_matches(
                target, candidate_map.keys(), n=1, cutoff=0.6
            )
            if best_match:
                return candidate_map[best_match[0]]
        return None

    def _save_to_contact_log(self, session, case_id, content):
        log = ContactLog(case_id=case_id, contact_content=content)
        session.add(log)

    def retry_linking_pending_notes(self):
        session = self.db._get_session()
        try:
            pendings = (
                session.query(IncomingNoteBuffer).filter_by(status="PENDING").all()
            )
            for note in pendings:
                names = json.loads(note.detected_names or "[]")
                linked = self._find_case_by_names_fuzzy(session, names)
                if linked:
                    self._save_to_contact_log(session, linked.case_id, note.body_text)
                    note.status = "LINKED"
                    note.linked_case_id = linked.case_id
            session.commit()
        except Exception as e:
            logger.error(f"Retry error: {e}")
        finally:
            session.close()

    def get_pending_notes(self) -> List[IncomingNoteBuffer]:
        session = self.db._get_session()
        try:
            return (
                session.query(IncomingNoteBuffer)
                .filter_by(status="PENDING")
                .order_by(IncomingNoteBuffer.received_at.desc())
                .all()
            )
        finally:
            session.close()

    def link_note_to_case_manually(self, note_id: int, case_id: int) -> bool:
        session = self.db._get_session()
        try:
            note = session.query(IncomingNoteBuffer).get(note_id)
            case = session.query(Case).get(case_id)
            if not note or not case:
                return False

            log = ContactLog(case_id=case.case_id, contact_content=note.body_text)
            session.add(log)
            note.status = "LINKED"
            note.linked_case_id = case.case_id
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Manual Link Error: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def ignore_note(self, note_id: int) -> bool:
        session = self.db._get_session()
        try:
            note = session.query(IncomingNoteBuffer).get(note_id)
            if note:
                note.status = "IGNORED"
                session.commit()
                return True
            return False
        finally:
            session.close()
