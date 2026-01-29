# src/legal_system/models/tables.py

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ==========================================
# 1. 共通マスタ (Core Master Data)
# ==========================================

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    windows_id = Column(String, unique=True, nullable=False, comment="PCログインID")
    name = Column(String, nullable=False, comment="表示名")
    role = Column(String, default="Operator", comment="権限: Manager/Operator")
    department = Column(String, nullable=True, comment="所属部署")
    phone = Column(String, nullable=True, comment="内線・連絡先")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class BankMaster(Base):
    __tablename__ = "bank_master"
    id = Column(Integer, primary_key=True, index=True)
    bank_name = Column(String, nullable=False)
    bank_code = Column(String, nullable=False)
    seal_cert_limit = Column(String, comment="印鑑証明期限")
    id_verify_rule = Column(String, comment="本人確認書類")
    transfer_rule = Column(String, comment="振込ルール")
    remarks = Column(Text, comment="特記事項")

    __table_args__ = (
        UniqueConstraint("bank_name", name="_bank_name_uc"),
        UniqueConstraint("bank_code", name="_bank_code_uc"),
    )
    branches = relationship("BranchMaster", back_populates="bank_ref", cascade="all, delete-orphan")
    financial_assets = relationship("FinancialAsset", back_populates="bank_ref")
    aliases = relationship("BankAlias", back_populates="bank_ref", cascade="all, delete-orphan")
    rag_files = relationship("FileRegistry", back_populates="bank_ref")

class BankAlias(Base):
    __tablename__ = "bank_aliases"
    id = Column(Integer, primary_key=True, index=True)
    alias_name = Column(String, unique=True, index=True, nullable=False)
    bank_id = Column(Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False)
    bank_ref = relationship("BankMaster", back_populates="aliases")

class BranchMaster(Base):
    __tablename__ = "branch_master"
    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(Integer, ForeignKey("bank_master.id", ondelete="CASCADE"), nullable=False)
    branch_name = Column(String, nullable=False)
    branch_code = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("bank_id", "branch_code", name="_bank_branch_code_uc"),)
    bank_ref = relationship("BankMaster", back_populates="branches")
    financial_assets = relationship("FinancialAsset", back_populates="branch_ref")

class AccountTypeMaster(Base):
    __tablename__ = "account_type_master"
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String, unique=True, nullable=False)
    financial_assets = relationship("FinancialAsset", back_populates="account_type_ref")

class DocumentType(Base):
    __tablename__ = "document_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

class ShippingMethod(Base):
    __tablename__ = "shipping_methods"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    tracking_base_url = Column(String, nullable=False)
    estimated_days = Column(Integer)

class SubmissionDocType(Base):
    __tablename__ = "submission_doc_types"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

# ==========================================
# 2. RAGシステム・ファイル管理
# ==========================================

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey("users.id"))
    action_type = Column(String)
    target = Column(String)
    details = Column(Text)
    user = relationship("User")

class FileRegistry(Base):
    __tablename__ = "file_registry"
    file_hash = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    doc_type = Column(String, default="その他")
    registered_at = Column(DateTime, default=datetime.now)
    security_level = Column(String, default="general")
    file_path = Column(String)
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="CONFIRMED")
    ai_confidence = Column(Float, default=0.0)
    extracted_data = Column(Text, nullable=True)

    bank_ref = relationship("BankMaster", back_populates="rag_files")
    case_ref = relationship("Case", back_populates="files")
    registrar = relationship("User")

# ==========================================
# 3. 個人情報管理テーブル
# ==========================================

class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    zip_code = Column(String)
    prefecture = Column(String, nullable=False)
    city_ward_town = Column(String)
    street_address = Column(String, nullable=False)
    building_name = Column(String)
    deceased_history = relationship("D_AddressHistory", back_populates="address", cascade="all, delete-orphan")
    heir_history = relationship("H_AddressHistory", back_populates="address", cascade="all, delete-orphan")

class Contact(Base):
    __tablename__ = "contact"
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    type = Column(String, nullable=False)
    sub_type = Column(String)

class Deceased(Base):
    __tablename__ = "deceased"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False, unique=True)
    name_last = Column(String)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    hometown = Column(String, comment="本籍地")
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    relationship_type = Column(String)
    last_address_id = Column(Integer, ForeignKey("address.id"))
    heirs = relationship("Heir", back_populates="deceased", cascade="all, delete-orphan")
    address_links = relationship("D_AddressHistory", back_populates="deceased", cascade="all, delete-orphan")
    contact_links = relationship("D_ContactLink", back_populates="deceased", cascade="all, delete-orphan")
    case = relationship("Case", back_populates="deceased_ref")
    last_address = relationship("Address", foreign_keys=[last_address_id])

class Heir(Base):
    """相続人"""
    __tablename__ = "heirs"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    name_last = Column(String, nullable=False)
    name_first = Column(String)
    name_last_kana = Column(String)
    name_first_kana = Column(String)
    
    # 本籍地として使用
    hometown = Column(String, comment="本籍地")
    
    # ★追加: 職業カラム
    occupation = Column(String, comment="職業")
    
    date_of_birth = Column(Date)
    date_of_death = Column(Date)
    relationship_type = Column(String)
    is_contracting_party = Column(Boolean, default=False)

    deceased = relationship("Deceased", back_populates="heirs")
    address_links = relationship("H_AddressHistory", back_populates="heir", cascade="all, delete-orphan")
    contact_links = relationship("H_ContactLink", back_populates="heir", cascade="all, delete-orphan")

# --- リンクテーブル ---

class D_AddressHistory(Base):
    __tablename__ = "d_address_history"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_last_address = Column(Boolean, nullable=False, default=False)
    deceased = relationship("Deceased", back_populates="address_links")
    address = relationship("Address", back_populates="deceased_history")

class H_AddressHistory(Base):
    __tablename__ = "h_address_history"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    is_current_address = Column(Boolean, nullable=False, default=False)
    heir = relationship("Heir", back_populates="address_links")
    address = relationship("Address", back_populates="heir_history")

class D_ContactLink(Base):
    __tablename__ = "d_contact_link"
    id = Column(Integer, primary_key=True)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    deceased = relationship("Deceased", back_populates="contact_links")
    contact = relationship("Contact")

class H_ContactLink(Base):
    __tablename__ = "h_contact_link"
    id = Column(Integer, primary_key=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contact.id"), nullable=False)
    heir = relationship("Heir", back_populates="contact_links")
    contact = relationship("Contact")

# ==========================================
# 4. 案件ハブテーブル
# ==========================================

class CaseStatus(Base):
    __tablename__ = "case_statuses"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    order_num = Column(Integer)

class Case(Base):
    __tablename__ = "cases"
    case_id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    folder_path = Column(String)
    client_name = Column(String, nullable=False)
    client_name_kana = Column(String)
    manager_id = Column(Integer, ForeignKey("users.id"))
    operator_id = Column(Integer, ForeignKey("users.id"))
    current_status_id = Column(Integer, ForeignKey("case_statuses.id"))
    kintone_record_id = Column(Integer, nullable=True)
    fee_contract_amount = Column(Float, default=0.0)
    deposit_required_amount = Column(Float, default=0.0)
    deposit_paid_amount = Column(Float, default=0.0)
    is_paid_in_full = Column(Boolean, default=False)
    certs_of_seal_count = Column(Integer, default=0)
    power_of_attorney_count = Column(Integer, default=0)
    date_of_death = Column(Date)
    interview_date = Column(DateTime)
    contract_date = Column(Date)
    tax_deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    sol_case_number = Column(String, nullable=True)
    introduction_date = Column(Date, nullable=True)
    referral_sec_branch_name = Column(String, nullable=True)
    referral_sec_rep_name = Column(String, nullable=True)
    consent_date = Column(Date, nullable=True)
    referral_sec_phone = Column(String, nullable=True)

    manager = relationship("User", foreign_keys=[manager_id])
    operator = relationship("User", foreign_keys=[operator_id])
    status_ref = relationship("CaseStatus")
    deceased_ref = relationship("Deceased", back_populates="case", uselist=False, cascade="all, delete-orphan")
    financial_assets = relationship("FinancialAsset", back_populates="case_ref", cascade="all, delete-orphan")
    real_estates = relationship("RealEstateAsset", back_populates="case_ref", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="case_ref", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="case_ref", cascade="all, delete-orphan")
    submitted_docs = relationship("CaseSubmissionDoc", back_populates="case_ref", cascade="all, delete-orphan")
    contact_logs = relationship("ContactLog", back_populates="case_ref", cascade="all, delete-orphan")
    insurance_assets = relationship("InsuranceAsset", back_populates="case_ref", cascade="all, delete-orphan")
    other_assets = relationship("OtherAsset", back_populates="case_ref", cascade="all, delete-orphan")
    liabilities = relationship("Liability", back_populates="case_ref", cascade="all, delete-orphan")
    contact_points = relationship("CaseContactPoint", back_populates="case_ref", cascade="all, delete-orphan")
    files = relationship("FileRegistry", back_populates="case_ref")

class CaseContactPoint(Base):
    __tablename__ = "case_contact_points"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_person_name = Column(String)
    relationship_to_client = Column(String)
    address_id = Column(Integer, ForeignKey("address.id"))
    contact_id = Column(Integer, ForeignKey("contact.id"))
    is_primary_contact = Column(Boolean, default=False)
    is_primary_mail_send_destination = Column(Boolean, default=False)
    case_ref = relationship("Case", back_populates="contact_points")
    address_ref = relationship("Address")
    contact_ref = relationship("Contact")

# ==========================================
# 5. タスク管理
# ==========================================

class TaskTemplate(Base):
    __tablename__ = "task_templates"
    template_id = Column(Integer, primary_key=True)
    description = Column(String, nullable=False)
    default_due_days = Column(Integer, default=1)
    is_manager_task = Column(Boolean, default=False)
    depends_on_template_id = Column(Integer, ForeignKey("task_templates.template_id"))
    depends_on = relationship("TaskTemplate", remote_side=[template_id])

class Task(Base):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    template_id = Column(Integer, ForeignKey("task_templates.template_id"))
    description = Column(String, nullable=False)
    last_updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    assigned_user_id = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    template_ref = relationship("TaskTemplate")
    document_logs = relationship("TaskDocumentLog", back_populates="task_ref", cascade="all, delete-orphan")
    case_ref = relationship("Case", back_populates="tasks")

class TaskDocumentLog(Base):
    __tablename__ = "task_document_logs"
    log_id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.task_id"), nullable=False)
    document_type_id = Column(Integer, ForeignKey("document_types.id"), nullable=False)
    shipping_method_id = Column(Integer, ForeignKey("shipping_methods.id"), nullable=False)
    sent_date = Column(DateTime, nullable=False)
    sent_to = Column(String, nullable=False)
    tracking_number = Column(String, unique=True)
    is_returned = Column(Boolean, default=False)
    document_type = relationship("DocumentType")
    shipping_method = relationship("ShippingMethod")
    task_ref = relationship("Task", back_populates="document_logs")

# ==========================================
# 6. 財産・トランザクション詳細
# ==========================================

class FinancialAsset(Base):
    __tablename__ = "financial_asset"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String, default="BANK")
    bank_id = Column(Integer, ForeignKey("bank_master.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch_master.id"))
    account_type_id = Column(Integer, ForeignKey("account_type_master.id"), nullable=True)
    account_number = Column(String)
    balance = Column(Float, default=0.0)
    status = Column(String, default="未確認")
    case_ref = relationship("Case", back_populates="financial_assets")
    bank_ref = relationship("BankMaster", back_populates="financial_assets")
    branch_ref = relationship("BranchMaster", back_populates="financial_assets")
    account_type_ref = relationship("AccountTypeMaster", back_populates="financial_assets")

class RealEstateAsset(Base):
    __tablename__ = "real_estate_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    property_type = Column(String, default="Land")
    location = Column(String, comment="所在")
    lot_number = Column(String, comment="地番")
    land_category = Column(String, comment="地目")
    land_area = Column(Float, comment="地積")
    house_number = Column(String, comment="家屋番号")
    structure = Column(String, comment="構造")
    floor_area = Column(String, comment="床面積")
    assessed_value = Column(Float, comment="固定資産税評価額", default=0.0)
    ownership_share = Column(String, nullable=True, comment="被相続人の持分")
    registry_pdf_path = Column(String, nullable=True, comment="登記情報PDFパス")
    registry_image_path = Column(String, nullable=True, comment="Word貼付用画像パス")
    case_ref = relationship("Case", back_populates="real_estates")

class InsuranceAsset(Base):
    __tablename__ = "insurance_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    insurance_company = Column(String)
    policy_number = Column(String)
    estimated_value = Column(Float)
    case_ref = relationship("Case", back_populates="insurance_assets")

class OtherAsset(Base):
    __tablename__ = "other_assets"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    estimated_value = Column(Float)
    case_ref = relationship("Case", back_populates="other_assets")

class Liability(Base):
    __tablename__ = "liability"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    is_debt = Column(Boolean, nullable=False, default=True)
    description = Column(String)
    amount = Column(Float, nullable=False)
    is_funeral_cost = Column(Boolean, nullable=False, default=False)
    case_ref = relationship("Case", back_populates="liabilities")

class Expense(Base):
    __tablename__ = "expenses"
    expense_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    description = Column(String)
    amount = Column(Float, nullable=False)
    expense_date = Column(Date)
    case_ref = relationship("Case", back_populates="expenses")

class ContactLog(Base):
    __tablename__ = "contact_logs"
    log_id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    contact_content = Column(String, nullable=False)
    is_thank_you_payment = Column(Boolean, default=False)
    case_ref = relationship("Case", back_populates="contact_logs")

class CaseSubmissionDoc(Base):
    __tablename__ = "case_submission_docs"
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    case_ref = relationship("Case", back_populates="submitted_docs")

class Coordinate(Base):
    __tablename__ = "coordinates"
    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String, index=True, nullable=False, comment="ファイル識別ハッシュ")
    label = Column(String, nullable=False, comment="項目名")
    x_point = Column(Float, nullable=False, comment="X座標")
    y_point = Column(Float, nullable=False, comment="Y座標")
    page_number = Column(Integer, default=1, comment="ページ番号")
    font_size = Column(Integer, default=10, comment="フォントサイズ")
    color = Column(String, default="black", comment="文字色")
    value = Column(String, nullable=True, comment="テスト値")
    description = Column(String, nullable=True, comment="備考")

# ==========================================
# 7. 遺言作成業務テーブル
# ==========================================

class WillCase(Base):
    __tablename__ = "will_cases"
    id = Column(Integer, primary_key=True)
    case_number = Column(String, unique=True, nullable=False)
    testator_name = Column(String, nullable=False)
    testator_birth = Column(Date)
    testator_address_id = Column(Integer, ForeignKey("address.id"))
    manager_id = Column(Integer, ForeignKey("users.id"))
    will_type = Column(String, default="公正証書", comment="公正証書/自筆証書")
    status = Column(String, default="ヒアリング中", comment="起案中/公証役場調整中/完了")
    notary_office_name = Column(String, nullable=True)
    draft_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    allocations = relationship("WillAllocation", back_populates="will_case")

class WillAllocation(Base):
    __tablename__ = "will_allocations"
    id = Column(Integer, primary_key=True)
    will_id = Column(Integer, ForeignKey("will_cases.id"), nullable=False)
    asset_description = Column(String, nullable=False, comment="例: ○○銀行の預金全額")
    beneficiary_name = Column(String, nullable=False)
    relationship_to_testator = Column(String, comment="続柄: 妻, 長男, 孫...")
    percentage = Column(Float, nullable=True, comment="割合指定の場合 (例: 0.5)")
    will_case = relationship("WillCase", back_populates="allocations")

class IncomingNoteBuffer(Base):
    __tablename__ = "incoming_note_buffer"
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, unique=True, nullable=False, comment="GmailのMessage-ID")
    received_at = Column(DateTime, nullable=False, default=datetime.now)
    subject = Column(String, nullable=True)
    body_text = Column(Text, nullable=False)
    detected_names = Column(String, nullable=True, comment="AIが抽出した氏名候補(JSON文字列)")
    ai_summary = Column(Text, nullable=True, comment="AIによる簡易要約")
    status = Column(String, default="PENDING", comment="PENDING(未紐付)/LINKED(紐付済)/IGNORED(対象外)")
    linked_case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=True)
    linked_case = relationship("Case")

class FamilyRegister(Base):
    __tablename__ = "family_registers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.case_id"), nullable=False)
    deceased_id = Column(Integer, ForeignKey("deceased.id"), nullable=True)
    heir_id = Column(Integer, ForeignKey("heirs.id"), nullable=True)
    doc_type = Column(String, comment="書類種別(戸籍謄本/除籍謄本/改製原戸籍)")
    issuing_authority = Column(String, comment="本籍地/発行元")
    head_of_family = Column(String, comment="筆頭者氏名")
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    file_registry_id = Column(String, ForeignKey("file_registry.file_hash"), nullable=True)
    case = relationship("Case")
    deceased = relationship("Deceased")
    heir = relationship("Heir")