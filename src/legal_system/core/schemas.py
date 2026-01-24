# src/legal_system/core/schemas.py

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class WillArticle(BaseModel):
    """遺言書の個別の条文"""
    article_number: str = Field(..., description="条数表記（例: 第１条）")
    title: Optional[str] = Field(None, description="条文の見出し（例: 不動産の遺贈）")
    content: str = Field(..., description="条文の本文")

class WillDraftStructure(BaseModel):
    """遺言書全体の構成データ"""
    testator_name: str = Field(..., description="遺言者（依頼主）の氏名")
    articles: List[WillArticle] = Field(..., description="条文のリスト")
    supplementary_provisions: Optional[str] = Field(None, description="付言事項")


# --- 追加: 案件検索用の軽量モデル ---
class CaseSearchKeys(BaseModel):
    """
    案件特定のために書類から抽出するキー情報。
    """

    client_name: Optional[str] = Field(
        None, description="依頼者（相続人代表）と思われる氏名"
    )
    deceased_name: Optional[str] = Field(
        None, description="被相続人（亡くなった方）と思われる氏名"
    )
    date_hint: Optional[str] = Field(
        None, description="書類に記載されている日付（死亡日や発行日など）"
    )
    summary_for_search: str = Field(..., description="検索のヒントになる短い要約")


# --- 以下、既存の検証用モデル (変更なし) ---
class VerificationField(BaseModel):
    field_label: str = Field(..., description="項目名（例: 被相続人氏名）")
    expected_value: Optional[str] = Field(None, description="Kintone上の値（期待値）")
    actual_value: Optional[str] = Field(
        None, description="書類から読み取った値（実測値）"
    )
    is_consistent: bool = Field(
        ..., description="矛盾がないか (True: 一致/許容範囲, False: 不一致)"
    )
    reasoning: str = Field(
        ..., description="判定の理由（例: '表記揺れ（斎藤/斉藤）だが同一人物と判断'）"
    )
    confidence_score: float = Field(..., description="AIの自信度 (0.0 - 1.0)")


class MissingDocAlert(BaseModel):
    doc_name: str = Field(..., description="不足している、または不備がある書類名")
    issue_type: Literal["MISSING", "EXPIRED", "INVALID_SEAL", "OTHER"] = Field(
        ..., description="不備の種類"
    )
    description: str = Field(..., description="詳細な指摘内容")


class DocumentAnalysisResult(BaseModel):
    summary: str = Field(..., description="解析全体の要約（監査ログ用）")
    document_type: str = Field(
        ..., description="書類種別（例: '残高証明書', '戸籍謄本'）"
    )
    verifications: List[VerificationField] = Field(
        default_factory=list, description="各項目の照合結果リスト"
    )
    alerts: List[MissingDocAlert] = Field(
        default_factory=list, description="検出された不備・不足"
    )
    extracted_data: dict = Field(
        default_factory=dict, description="DB保存用の正規化済みデータ(JSON)"
    )
    overall_status: Literal["APPROVED", "WARNING", "REJECTED"] = Field(
        ...,
        description="AIによる一次判定。不整合がなければAPPROVED、要確認はWARNING。",
    )

# --- ★新規追加: スキャナー読取用モデル ---
class ScannedHeirInfo(BaseModel):
    """スキャンデータから読み取った相続人1人分の情報"""
    name: str = Field(..., description="相続人の氏名")
    relationship: str = Field(..., description="続柄（例: 長男、妻）")
    address: Optional[str] = Field(None, description="住所（手書き文字を読み取る）")
    phone: Optional[str] = Field(None, description="電話番号")

class HeirListAnalysisResult(BaseModel):
    """「推定相続人連絡先一覧」の詳細解析結果"""
    # ★修正点: 遺言者を特定するためのフィールドを追加
    testator_name: Optional[str] = Field(None, description="書類下部の「遺言者様に関する情報」欄に記載されている氏名")
    
    case_number_hint: Optional[str] = Field(None, description="記載されている案件番号(G番号)")
    deceased_name_hint: Optional[str] = Field(None, description="記載されている被相続人名")
    heirs: List[ScannedHeirInfo] = Field(default_factory=list, description="リストアップされている相続人情報")