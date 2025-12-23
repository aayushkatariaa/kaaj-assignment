"""
Database Models for Loan Underwriting System
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    ForeignKey, JSON, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.datas.database import Base
import enum


class ApplicationStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MatchStatusEnum(str, enum.Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


# ============== LENDER MODELS ==============

class Lender(Base):
    __tablename__ = "lenders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    website = Column(String(512), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    logo_url = Column(String(512), nullable=True)
    source_pdf_name = Column(String(255), nullable=True)
    last_policy_update = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    programs = relationship("LenderProgram", back_populates="lender", cascade="all, delete-orphan")


class LenderProgram(Base):
    __tablename__ = "lender_programs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lender_id = Column(Integer, ForeignKey("lenders.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    min_fico = Column(Integer, nullable=True)
    max_loan_amount = Column(Float, nullable=True)
    min_loan_amount = Column(Float, nullable=True)
    min_time_in_business_months = Column(Integer, nullable=True)
    rate_type = Column(String(50), nullable=True)
    min_rate = Column(Float, nullable=True)
    max_rate = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    lender = relationship("Lender", back_populates="programs")
    criteria = relationship("PolicyCriteria", back_populates="program", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('lender_id', 'name', name='uq_lender_program_name'),
    )


class PolicyCriteria(Base):
    __tablename__ = "policy_criteria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey("lender_programs.id", ondelete="CASCADE"), nullable=False)
    criteria_type = Column(String(100), nullable=False)
    criteria_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    operator = Column(String(20), nullable=False)
    numeric_value = Column(Float, nullable=True)
    numeric_value_min = Column(Float, nullable=True)
    numeric_value_max = Column(Float, nullable=True)
    string_value = Column(String(500), nullable=True)
    list_values = Column(JSON, nullable=True)
    is_required = Column(Boolean, default=True)
    weight = Column(Float, default=1.0)
    failure_message = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    program = relationship("LenderProgram", back_populates="criteria")


# ============== LOAN APPLICATION MODELS ==============

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reference_id = Column(String(64), nullable=False, unique=True, index=True)
    status = Column(String(32), default=ApplicationStatusEnum.DRAFT.value)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    business = relationship("Business", back_populates="application", uselist=False, cascade="all, delete-orphan")
    guarantor = relationship("PersonalGuarantor", back_populates="application", uselist=False, cascade="all, delete-orphan")
    business_credit = relationship("BusinessCredit", back_populates="application", uselist=False, cascade="all, delete-orphan")
    loan_request = relationship("LoanRequest", back_populates="application", uselist=False, cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="application", cascade="all, delete-orphan")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    legal_name = Column(String(255), nullable=False)
    dba_name = Column(String(255), nullable=True)
    entity_type = Column(String(50), nullable=True)
    state = Column(String(2), nullable=False)
    city = Column(String(100), nullable=True)
    zip_code = Column(String(10), nullable=True)
    address = Column(String(500), nullable=True)
    industry = Column(String(255), nullable=True)
    naics_code = Column(String(10), nullable=True)
    sic_code = Column(String(10), nullable=True)
    years_in_business = Column(Float, nullable=True)
    months_in_business = Column(Integer, nullable=True)
    annual_revenue = Column(Float, nullable=True)
    monthly_revenue = Column(Float, nullable=True)
    employee_count = Column(Integer, nullable=True)
    ein = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    application = relationship("LoanApplication", back_populates="business")


class PersonalGuarantor(Base):
    __tablename__ = "personal_guarantors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    ownership_percentage = Column(Float, nullable=True)
    fico_score = Column(Integer, nullable=True)
    has_bankruptcy = Column(Boolean, default=False)
    bankruptcy_discharge_date = Column(DateTime(timezone=True), nullable=True)
    years_since_bankruptcy = Column(Float, nullable=True)
    has_foreclosure = Column(Boolean, default=False)
    has_open_tax_liens = Column(Boolean, default=False)
    tax_lien_amount = Column(Float, nullable=True)
    has_judgments = Column(Boolean, default=False)
    has_collections = Column(Boolean, default=False)
    derogatory_marks = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    application = relationship("LoanApplication", back_populates="guarantor")


class BusinessCredit(Base):
    __tablename__ = "business_credits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    paynet_score = Column(Integer, nullable=True)
    paynet_master_score = Column(Integer, nullable=True)
    duns_number = Column(String(20), nullable=True)
    paydex_score = Column(Integer, nullable=True)
    experian_business_score = Column(Integer, nullable=True)
    number_of_trade_lines = Column(Integer, nullable=True)
    total_trade_line_balance = Column(Float, nullable=True)
    average_days_to_pay = Column(Integer, nullable=True)
    has_slow_pays = Column(Boolean, default=False)
    slow_pay_count = Column(Integer, nullable=True)
    has_charge_offs = Column(Boolean, default=False)
    charge_off_amount = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    application = relationship("LoanApplication", back_populates="business_credit")


class LoanRequest(Base):
    __tablename__ = "loan_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False, unique=True)
    requested_amount = Column(Float, nullable=False)
    loan_purpose = Column(String(255), nullable=True)
    term_months = Column(Integer, nullable=True)
    equipment_type = Column(String(100), nullable=True)
    equipment_description = Column(Text, nullable=True)
    equipment_cost = Column(Float, nullable=True)
    equipment_year = Column(Integer, nullable=True)
    equipment_age_years = Column(Float, nullable=True)
    equipment_condition = Column(String(50), nullable=True)
    is_titled = Column(Boolean, default=False)
    vendor_name = Column(String(255), nullable=True)
    vendor_invoice_available = Column(Boolean, default=False)
    down_payment_amount = Column(Float, nullable=True)
    down_payment_percent = Column(Float, nullable=True)
    use_case = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    application = relationship("LoanApplication", back_populates="loan_request")


# ============== MATCH RESULTS ==============

class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    lender_id = Column(Integer, ForeignKey("lenders.id", ondelete="CASCADE"), nullable=False)
    program_id = Column(Integer, ForeignKey("lender_programs.id", ondelete="CASCADE"), nullable=True)
    status = Column(String(32), nullable=False)
    fit_score = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    criteria_results = Column(JSON, nullable=True)
    criteria_met = Column(Integer, default=0)
    criteria_failed = Column(Integer, default=0)
    criteria_total = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    application = relationship("LoanApplication", back_populates="match_results")
    lender = relationship("Lender")
    program = relationship("LenderProgram")
    
    __table_args__ = (
        UniqueConstraint('application_id', 'program_id', name='uq_application_program'),
    )


class CriteriaEvaluation(Base):
    __tablename__ = "criteria_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_result_id = Column(Integer, ForeignKey("match_results.id", ondelete="CASCADE"), nullable=False)
    criteria_id = Column(Integer, ForeignKey("policy_criteria.id", ondelete="SET NULL"), nullable=True)
    criteria_type = Column(String(100), nullable=False)
    criteria_name = Column(String(255), nullable=False)
    passed = Column(Boolean, nullable=False)
    is_required = Column(Boolean, default=True)
    expected_value = Column(String(500), nullable=True)
    actual_value = Column(String(500), nullable=True)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    match_result = relationship("MatchResult")
    criteria = relationship("PolicyCriteria")


class UnderwritingRun(Base):
    __tablename__ = "underwriting_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    workflow_run_id = Column(String(255), nullable=True)
    status = Column(String(32), default="PENDING")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_lenders_evaluated = Column(Integer, default=0)
    eligible_lenders = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    application = relationship("LoanApplication")
