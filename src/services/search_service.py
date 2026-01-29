# src/services/search_service.py

import logging
import unicodedata
from typing import List, Dict, Any, Optional
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload

from legal_system.models.tables import Case, Deceased, Heir, Contact, H_ContactLink

logger = logging.getLogger(__name__)

def normalize_text_space(text: str) -> str:
    if not text: return ""
    return text.replace(" ", "　").strip()

def normalize_text(text: str) -> str:
    if not text: return ""
    return unicodedata.normalize("NFKC", text).strip()

def search_cases_enhanced(session, keyword: str) -> List[Case]:
    """
    案件検索ロジック（強化版）
    - 案件番号、依頼者名、被相続人名、電話番号などから検索
    """
    base_query = session.query(Case).options(
        joinedload(Case.deceased_ref).joinedload(Deceased.heirs),
        joinedload(Case.manager),
        joinedload(Case.operator)
    )
    
    if not keyword:
        # デフォルトは作成日順で直近10件
        return base_query.order_by(Case.created_at.desc()).limit(10).all()

    clean_key = f"%{keyword.strip()}%"
    
    # 検索クエリ構築
    # 関連テーブルを結合してフィルタリング
    return base_query.join(Case.deceased_ref)\
        .outerjoin(Deceased.heirs)\
        .outerjoin(Heir.contact_links)\
        .outerjoin(H_ContactLink.contact)\
        .filter(
            or_(
                # 1. 案件基本情報
                Case.case_number.ilike(clean_key),
                Case.client_name.ilike(clean_key),
                Case.client_name_kana.ilike(clean_key),
                Case.sol_case_number.ilike(clean_key),
                Case.referral_sec_phone.ilike(clean_key),
                
                # 2. 被相続人 (漢字・カナ・結合)
                Deceased.name_last.ilike(clean_key),
                Deceased.name_first.ilike(clean_key),
                # フルネーム結合検索 (姓+名)
                (Deceased.name_last + Deceased.name_first).ilike(clean_key),
                (Deceased.name_last + " " + Deceased.name_first).ilike(clean_key),
                (Deceased.name_last + "　" + Deceased.name_first).ilike(clean_key),
                # カナ検索
                Deceased.name_last_kana.ilike(clean_key),
                Deceased.name_first_kana.ilike(clean_key),
                (Deceased.name_last_kana + Deceased.name_first_kana).ilike(clean_key),

                # 3. 連絡先 (電話番号など)
                Contact.value.ilike(clean_key)
            )
        ).distinct().limit(20).all()