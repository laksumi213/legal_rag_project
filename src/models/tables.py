# src/models/tables.py

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 基底クラス"""

    pass


# ==========================================
# 1. 共通マスタ (Core Master Data)
# ==========================================


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    windows_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="PCログインID"
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="表示名")
    role: Mapped[str] = mapped_column(
        String(50), default="Operator", comment="権限: Manager/Operator"
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), comment="所属部署")
    phone: Mapped[Optional[str]] = mapped_column(String(50), comment="内線・連絡先")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class BankMaster(Base):
    __tablename__ = "bank_master"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_code: Mapped[str] = mapped_column(String(10), nullable=False)
    seal_cert_limit: Mapped[Optional[str]] = mapped_column(
        String(100), comment="印鑑証明期限"
    )
    id_verify_rule: Mapped[Optional[str]] = mapped_column(
        String(100), comment="本人確認書類"
    )
    transfer_rule: Mapped[Optional[str]] = mapped_column(
        String(100), comment="振込ルール"
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, comment="特記事項")

    __table_args__ = (
        UniqueConstraint("bank_name", name="_bank_name_uc"),
        UniqueConstraint("bank_code", name="_bank_code_uc"),
    )

    branches: Mapped[List["BranchMaster"]] = relationship(
        back_populates="bank_ref", cascade="all, delete-orphan"
    )
    financial_assets: Mapped[List["FinancialAsset"]] = relationship(
        back_populates="bank_ref"
    )
    aliases: Mapped[List["BankAlias"]] = relationship(
        back_populates="bank_ref", cascade="all, delete-orphan"
    )
    rag_files: Mapped[List["FileRegistry"]] = relationship(back_populates="bank_ref")


class BankAlias(Base):
    __tablename__ = "bank_aliases"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alias_name: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    bank_id: Mapped[int] = mapped_column(
        ForeignKey("bank_master.id", ondelete="CASCADE")
    )

    bank_ref: Mapped["BankMaster"] = relationship(back_populates="aliases")


class BranchMaster(Base):
    __tablename__ = "branch_master"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    bank_id: Mapped[int] = mapped_column(
        ForeignKey("bank_master.id", ondelete="CASCADE")
    )
    branch_name: Mapped[str] = mapped_column(String(100), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(10), nullable=False)

    __table_args__ = (
        UniqueConstraint("bank_id", "branch_code", name="_bank_branch_code_uc"),
    )
    bank_ref: Mapped["BankMaster"] = relationship(back_populates="branches")
    financial_assets: Mapped[List["FinancialAsset"]] = relationship(
        back_populates="branch_ref"
    )


class AccountTypeMaster(Base):
    __tablename__ = "account_type_master"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    type_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    financial_assets: Mapped[List["FinancialAsset"]] = relationship(
        back_populates="account_type_ref"
    )


class DocumentType(Base):
    __tablename__ = "document_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class ShippingMethod(Base):
    __tablename__ = "shipping_methods"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tracking_base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    estimated_days: Mapped[Optional[int]] = mapped_column(Integer)


class SubmissionDocType(Base):
    __tablename__ = "submission_doc_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


# ==========================================
# 2. RAGシステム・ファイル管理
# ==========================================


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    action_type: Mapped[Optional[str]] = mapped_column(String(100))
    target: Mapped[Optional[str]] = mapped_column(String(255))
    details: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped[Optional["User"]] = relationship()


class FileRegistry(Base):
    __tablename__ = "file_registry"
    file_hash: Mapped[str] = mapped_column(String(100), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    bank_id: Mapped[Optional[int]] = mapped_column(ForeignKey("bank_master.id"))
    case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.case_id"))
    doc_type: Mapped[str] = mapped_column(String(100), default="その他")
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    security_level: Mapped[str] = mapped_column(String(50), default="general")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    registered_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(50), default="CONFIRMED")
    ai_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    extracted_data: Mapped[Optional[str]] = mapped_column(Text)

    bank_ref: Mapped[Optional["BankMaster"]] = relationship(back_populates="rag_files")
    case_ref: Mapped[Optional["Case"]] = relationship(back_populates="files")
    registrar: Mapped[Optional["User"]] = relationship()


# ==========================================
# 3. 個人情報管理テーブル
# ==========================================


class Address(Base):
    __tablename__ = "address"
    id: Mapped[int] = mapped_column(primary_key=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(20))
    prefecture: Mapped[str] = mapped_column(String(50), nullable=False)
    city_ward_town: Mapped[Optional[str]] = mapped_column(String(100))
    street_address: Mapped[str] = mapped_column(String(255), nullable=False)
    building_name: Mapped[Optional[str]] = mapped_column(String(255))

    deceased_history: Mapped[List["D_AddressHistory"]] = relationship(
        back_populates="address", cascade="all, delete-orphan"
    )
    heir_history: Mapped[List["H_AddressHistory"]] = relationship(
        back_populates="address", cascade="all, delete-orphan"
    )


class Contact(Base):
    __tablename__ = "contact"
    id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_type: Mapped[Optional[str]] = mapped_column(String(50))


class Deceased(Base):
    __tablename__ = "deceased"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.case_id"), nullable=False, unique=True
    )
    name_last: Mapped[Optional[str]] = mapped_column(String(50))
    name_first: Mapped[Optional[str]] = mapped_column(String(50))
    name_last_kana: Mapped[Optional[str]] = mapped_column(String(50))
    name_first_kana: Mapped[Optional[str]] = mapped_column(String(50))
    hometown: Mapped[Optional[str]] = mapped_column(String(255), comment="本籍地")
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    date_of_death: Mapped[Optional[date]] = mapped_column(Date)
    relationship_type: Mapped[Optional[str]] = mapped_column(String(50))
    last_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"))

    heirs: Mapped[List["Heir"]] = relationship(
        back_populates="deceased", cascade="all, delete-orphan"
    )
    address_links: Mapped[List["D_AddressHistory"]] = relationship(
        back_populates="deceased", cascade="all, delete-orphan"
    )
    contact_links: Mapped[List["D_ContactLink"]] = relationship(
        back_populates="deceased", cascade="all, delete-orphan"
    )
    case: Mapped["Case"] = relationship(back_populates="deceased_ref")
    last_address: Mapped[Optional["Address"]] = relationship(
        foreign_keys=[last_address_id]
    )


class Heir(Base):
    """相続人"""

    __tablename__ = "heirs"
    id: Mapped[int] = mapped_column(primary_key=True)
    deceased_id: Mapped[int] = mapped_column(ForeignKey("deceased.id"), nullable=False)
    name_last: Mapped[str] = mapped_column(String(50), nullable=False)
    name_first: Mapped[Optional[str]] = mapped_column(String(50))
    name_last_kana: Mapped[Optional[str]] = mapped_column(String(50))
    name_first_kana: Mapped[Optional[str]] = mapped_column(String(50))
    hometown: Mapped[Optional[str]] = mapped_column(String(255), comment="本籍地")
    occupation: Mapped[Optional[str]] = mapped_column(String(100), comment="職業")
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    date_of_death: Mapped[Optional[date]] = mapped_column(Date)
    relationship_type: Mapped[Optional[str]] = mapped_column(String(50))
    is_contracting_party: Mapped[bool] = mapped_column(Boolean, default=False)

    deceased: Mapped["Deceased"] = relationship(back_populates="heirs")
    address_links: Mapped[List["H_AddressHistory"]] = relationship(
        back_populates="heir", cascade="all, delete-orphan"
    )
    contact_links: Mapped[List["H_ContactLink"]] = relationship(
        back_populates="heir", cascade="all, delete-orphan"
    )


# --- リンクテーブル ---


class D_AddressHistory(Base):
    __tablename__ = "d_address_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    deceased_id: Mapped[int] = mapped_column(ForeignKey("deceased.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("address.id"), nullable=False)
    is_last_address: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    deceased: Mapped["Deceased"] = relationship(back_populates="address_links")
    address: Mapped["Address"] = relationship(back_populates="deceased_history")


class H_AddressHistory(Base):
    __tablename__ = "h_address_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    heir_id: Mapped[int] = mapped_column(ForeignKey("heirs.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("address.id"), nullable=False)
    is_current_address: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    heir: Mapped["Heir"] = relationship(back_populates="address_links")
    address: Mapped["Address"] = relationship(back_populates="heir_history")


class D_ContactLink(Base):
    __tablename__ = "d_contact_link"
    id: Mapped[int] = mapped_column(primary_key=True)
    deceased_id: Mapped[int] = mapped_column(ForeignKey("deceased.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contact.id"), nullable=False)

    deceased: Mapped["Deceased"] = relationship(back_populates="contact_links")
    contact: Mapped["Contact"] = relationship()


class H_ContactLink(Base):
    __tablename__ = "h_contact_link"
    id: Mapped[int] = mapped_column(primary_key=True)
    heir_id: Mapped[int] = mapped_column(ForeignKey("heirs.id"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contact.id"), nullable=False)

    heir: Mapped["Heir"] = relationship(back_populates="contact_links")
    contact: Mapped["Contact"] = relationship()


# ==========================================
# 4. 案件ハブテーブル
# ==========================================


class CaseStatus(Base):
    __tablename__ = "case_statuses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_num: Mapped[Optional[int]] = mapped_column(Integer)


class Case(Base):
    __tablename__ = "cases"
    case_id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    folder_path: Mapped[Optional[str]] = mapped_column(String(500))
    client_name: Mapped[str] = mapped_column(String(100), nullable=False)
    client_name_kana: Mapped[Optional[str]] = mapped_column(String(100))

    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    current_status_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("case_statuses.id")
    )
    kintone_record_id: Mapped[Optional[int]] = mapped_column(Integer)

    fee_contract_amount: Mapped[float] = mapped_column(Float, default=0.0)
    deposit_required_amount: Mapped[float] = mapped_column(Float, default=0.0)
    deposit_paid_amount: Mapped[float] = mapped_column(Float, default=0.0)
    is_paid_in_full: Mapped[bool] = mapped_column(Boolean, default=False)

    certs_of_seal_count: Mapped[int] = mapped_column(Integer, default=0)
    power_of_attorney_count: Mapped[int] = mapped_column(Integer, default=0)

    date_of_death: Mapped[Optional[date]] = mapped_column(Date)
    interview_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    contract_date: Mapped[Optional[date]] = mapped_column(Date)
    tax_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    sol_case_number: Mapped[Optional[str]] = mapped_column(String(100))
    introduction_date: Mapped[Optional[date]] = mapped_column(Date)
    referral_sec_branch_name: Mapped[Optional[str]] = mapped_column(String(100))
    referral_sec_rep_name: Mapped[Optional[str]] = mapped_column(String(100))
    consent_date: Mapped[Optional[date]] = mapped_column(Date)
    referral_sec_phone: Mapped[Optional[str]] = mapped_column(String(50))

    manager: Mapped[Optional["User"]] = relationship(foreign_keys=[manager_id])
    operator: Mapped[Optional["User"]] = relationship(foreign_keys=[operator_id])
    status_ref: Mapped[Optional["CaseStatus"]] = relationship()

    deceased_ref: Mapped["Deceased"] = relationship(
        back_populates="case", uselist=False, cascade="all, delete-orphan"
    )
    financial_assets: Mapped[List["FinancialAsset"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    real_estates: Mapped[List["RealEstateAsset"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    expenses: Mapped[List["Expense"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    submitted_docs: Mapped[List["CaseSubmissionDoc"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    contact_logs: Mapped[List["ContactLog"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    insurance_assets: Mapped[List["InsuranceAsset"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    other_assets: Mapped[List["OtherAsset"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    liabilities: Mapped[List["Liability"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    contact_points: Mapped[List["CaseContactPoint"]] = relationship(
        back_populates="case_ref", cascade="all, delete-orphan"
    )
    files: Mapped[List["FileRegistry"]] = relationship(back_populates="case_ref")


class CaseContactPoint(Base):
    __tablename__ = "case_contact_points"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    contact_person_name: Mapped[Optional[str]] = mapped_column(String(100))
    relationship_to_client: Mapped[Optional[str]] = mapped_column(String(50))
    address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"))
    contact_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contact.id"))
    is_primary_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    is_primary_mail_send_destination: Mapped[bool] = mapped_column(
        Boolean, default=False
    )

    case_ref: Mapped["Case"] = relationship(back_populates="contact_points")
    address_ref: Mapped[Optional["Address"]] = relationship()
    contact_ref: Mapped[Optional["Contact"]] = relationship()


# ==========================================
# 5. タスク管理
# ==========================================


class TaskTemplate(Base):
    __tablename__ = "task_templates"
    template_id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    default_due_days: Mapped[int] = mapped_column(Integer, default=1)
    is_manager_task: Mapped[bool] = mapped_column(Boolean, default=False)
    depends_on_template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("task_templates.template_id")
    )

    depends_on: Mapped[Optional["TaskTemplate"]] = relationship(
        remote_side=[template_id]
    )


class Task(Base):
    __tablename__ = "tasks"
    task_id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("task_templates.template_id")
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    assigned_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    assigned_user: Mapped[Optional["User"]] = relationship(
        foreign_keys=[assigned_user_id]
    )
    template_ref: Mapped[Optional["TaskTemplate"]] = relationship()
    document_logs: Mapped[List["TaskDocumentLog"]] = relationship(
        back_populates="task_ref", cascade="all, delete-orphan"
    )
    case_ref: Mapped["Case"] = relationship(back_populates="tasks")


class TaskDocumentLog(Base):
    __tablename__ = "task_document_logs"
    log_id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.task_id"), nullable=False)
    document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id"), nullable=False
    )
    shipping_method_id: Mapped[int] = mapped_column(
        ForeignKey("shipping_methods.id"), nullable=False
    )
    sent_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent_to: Mapped[str] = mapped_column(String(200), nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    is_returned: Mapped[bool] = mapped_column(Boolean, default=False)

    document_type: Mapped["DocumentType"] = relationship()
    shipping_method: Mapped["ShippingMethod"] = relationship()
    task_ref: Mapped["Task"] = relationship(back_populates="document_logs")


# ==========================================
# 6. 財産・トランザクション詳細
# ==========================================


class FinancialAsset(Base):
    __tablename__ = "financial_asset"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.case_id", ondelete="CASCADE"), nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(20), default="BANK")
    bank_id: Mapped[int] = mapped_column(ForeignKey("bank_master.id"), nullable=False)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branch_master.id"))
    account_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("account_type_master.id")
    )
    account_number: Mapped[Optional[str]] = mapped_column(String(50))
    balance: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="未確認")

    case_ref: Mapped["Case"] = relationship(back_populates="financial_assets")
    bank_ref: Mapped["BankMaster"] = relationship(back_populates="financial_assets")
    branch_ref: Mapped[Optional["BranchMaster"]] = relationship(
        back_populates="financial_assets"
    )
    account_type_ref: Mapped[Optional["AccountTypeMaster"]] = relationship(
        back_populates="financial_assets"
    )


class RealEstateAsset(Base):
    __tablename__ = "real_estate_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    property_type: Mapped[str] = mapped_column(String(20), default="Land")
    location: Mapped[Optional[str]] = mapped_column(String(500), comment="所在")
    lot_number: Mapped[Optional[str]] = mapped_column(String(100), comment="地番")
    land_category: Mapped[Optional[str]] = mapped_column(String(50), comment="地目")
    land_area: Mapped[Optional[float]] = mapped_column(Float, comment="地積")
    house_number: Mapped[Optional[str]] = mapped_column(String(100), comment="家屋番号")
    structure: Mapped[Optional[str]] = mapped_column(String(200), comment="構造")
    floor_area: Mapped[Optional[str]] = mapped_column(String(100), comment="床面積")
    assessed_value: Mapped[float] = mapped_column(
        Float, default=0.0, comment="固定資産税評価額"
    )
    ownership_share: Mapped[Optional[str]] = mapped_column(
        String(50), comment="被相続人の持分"
    )
    registry_pdf_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="登記情報PDFパス"
    )
    registry_image_path: Mapped[Optional[str]] = mapped_column(
        String(500), comment="Word貼付用画像パス"
    )

    case_ref: Mapped["Case"] = relationship(back_populates="real_estates")


class InsuranceAsset(Base):
    __tablename__ = "insurance_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    insurance_company: Mapped[Optional[str]] = mapped_column(String(100))
    policy_number: Mapped[Optional[str]] = mapped_column(String(100))
    estimated_value: Mapped[Optional[float]] = mapped_column(Float)

    case_ref: Mapped["Case"] = relationship(back_populates="insurance_assets")


class OtherAsset(Base):
    __tablename__ = "other_assets"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    estimated_value: Mapped[Optional[float]] = mapped_column(Float)

    case_ref: Mapped["Case"] = relationship(back_populates="other_assets")


class Liability(Base):
    __tablename__ = "liability"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    is_debt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    is_funeral_cost: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    case_ref: Mapped["Case"] = relationship(back_populates="liabilities")


class Expense(Base):
    __tablename__ = "expenses"
    expense_id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    expense_date: Mapped[Optional[date]] = mapped_column(Date)

    case_ref: Mapped["Case"] = relationship(back_populates="expenses")


class ContactLog(Base):
    __tablename__ = "contact_logs"
    log_id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    contact_content: Mapped[str] = mapped_column(Text, nullable=False)
    is_thank_you_payment: Mapped[bool] = mapped_column(Boolean, default=False)

    case_ref: Mapped["Case"] = relationship(back_populates="contact_logs")


class CaseSubmissionDoc(Base):
    __tablename__ = "case_submission_docs"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)

    case_ref: Mapped["Case"] = relationship(back_populates="submitted_docs")


class Coordinate(Base):
    __tablename__ = "coordinates"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_hash: Mapped[str] = mapped_column(
        String(100), index=True, nullable=False, comment="ファイル識別ハッシュ"
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False, comment="項目名")
    x_point: Mapped[float] = mapped_column(Float, nullable=False, comment="X座標")
    y_point: Mapped[float] = mapped_column(Float, nullable=False, comment="Y座標")
    width: Mapped[Optional[float]] = mapped_column(Float, comment="幅")
    height: Mapped[Optional[float]] = mapped_column(Float, comment="高さ")
    page_number: Mapped[int] = mapped_column(Integer, default=1, comment="ページ番号")
    font_size: Mapped[int] = mapped_column(
        Integer, default=10, comment="フォントサイズ"
    )
    color: Mapped[str] = mapped_column(String(20), default="black", comment="文字色")
    value: Mapped[Optional[str]] = mapped_column(String(255), comment="テスト値")
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="備考")


# ==========================================
# 7. 遺言作成業務テーブル
# ==========================================


class WillCase(Base):
    __tablename__ = "will_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    testator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    testator_birth: Mapped[Optional[date]] = mapped_column(Date)
    testator_address_id: Mapped[Optional[int]] = mapped_column(ForeignKey("address.id"))
    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    will_type: Mapped[str] = mapped_column(
        String(20), default="公正証書", comment="公正証書/自筆証書"
    )
    status: Mapped[str] = mapped_column(
        String(50), default="ヒアリング中", comment="起案中/公証役場調整中/完了"
    )
    notary_office_name: Mapped[Optional[str]] = mapped_column(String(100))
    draft_date: Mapped[Optional[date]] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    allocations: Mapped[List["WillAllocation"]] = relationship(
        back_populates="will_case"
    )


class WillAllocation(Base):
    __tablename__ = "will_allocations"
    id: Mapped[int] = mapped_column(primary_key=True)
    will_id: Mapped[int] = mapped_column(ForeignKey("will_cases.id"), nullable=False)
    asset_description: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="例: ○○銀行の預金全額"
    )
    beneficiary_name: Mapped[str] = mapped_column(String(100), nullable=False)
    relationship_to_testator: Mapped[Optional[str]] = mapped_column(
        String(50), comment="続柄: 妻, 長男, 孫..."
    )
    percentage: Mapped[Optional[float]] = mapped_column(
        Float, comment="割合指定の場合 (例: 0.5)"
    )

    will_case: Mapped["WillCase"] = relationship(back_populates="allocations")


class IncomingNoteBuffer(Base):
    __tablename__ = "incoming_note_buffer"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="GmailのMessage-ID"
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    subject: Mapped[Optional[str]] = mapped_column(String(255))
    body_text: Mapped[str] = mapped_column(Text, nullable=False)
    detected_names: Mapped[Optional[str]] = mapped_column(
        String(500), comment="AIが抽出した氏名候補(JSON文字列)"
    )
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, comment="AIによる簡易要約")
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        comment="PENDING(未紐付)/LINKED(紐付済)/IGNORED(対象外)",
    )
    linked_case_id: Mapped[Optional[int]] = mapped_column(ForeignKey("cases.case_id"))

    linked_case: Mapped[Optional["Case"]] = relationship()


class FamilyRegister(Base):
    __tablename__ = "family_registers"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.case_id"), nullable=False)
    deceased_id: Mapped[Optional[int]] = mapped_column(ForeignKey("deceased.id"))
    heir_id: Mapped[Optional[int]] = mapped_column(ForeignKey("heirs.id"))
    doc_type: Mapped[Optional[str]] = mapped_column(
        String(50), comment="書類種別(戸籍謄本/除籍謄本/改製原戸籍)"
    )
    issuing_authority: Mapped[Optional[str]] = mapped_column(
        String(100), comment="本籍地/発行元"
    )
    head_of_family: Mapped[Optional[str]] = mapped_column(
        String(50), comment="筆頭者氏名"
    )
    valid_from: Mapped[Optional[date]] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date)
    file_registry_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("file_registry.file_hash")
    )

    case: Mapped["Case"] = relationship()
    deceased: Mapped[Optional["Deceased"]] = relationship()
    heir: Mapped[Optional["Heir"]] = relationship()
