"""
Pydantic schemas for Loan Applications
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============== Business Schemas ==============

class BusinessBase(BaseModel):
    legal_name: str = Field(..., max_length=255)
    dba_name: Optional[str] = None
    entity_type: Optional[str] = None
    state: str = Field(..., max_length=2)
    city: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    naics_code: Optional[str] = None
    sic_code: Optional[str] = None
    years_in_business: Optional[float] = None
    months_in_business: Optional[int] = None
    annual_revenue: Optional[float] = None
    monthly_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    ein: Optional[str] = None


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    legal_name: Optional[str] = None
    dba_name: Optional[str] = None
    entity_type: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    address: Optional[str] = None
    industry: Optional[str] = None
    naics_code: Optional[str] = None
    sic_code: Optional[str] = None
    years_in_business: Optional[float] = None
    months_in_business: Optional[int] = None
    annual_revenue: Optional[float] = None
    monthly_revenue: Optional[float] = None
    employee_count: Optional[int] = None
    ein: Optional[str] = None


class BusinessResponse(BusinessBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Personal Guarantor Schemas ==============

class PersonalGuarantorBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    ownership_percentage: Optional[float] = None
    fico_score: Optional[int] = None
    has_bankruptcy: bool = False
    bankruptcy_discharge_date: Optional[datetime] = None
    years_since_bankruptcy: Optional[float] = None
    has_foreclosure: bool = False
    has_open_tax_liens: bool = False
    tax_lien_amount: Optional[float] = None
    has_judgments: bool = False
    has_collections: bool = False
    derogatory_marks: Optional[List[str]] = None


class PersonalGuarantorCreate(PersonalGuarantorBase):
    pass


class PersonalGuarantorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    ownership_percentage: Optional[float] = None
    fico_score: Optional[int] = None
    has_bankruptcy: Optional[bool] = None
    bankruptcy_discharge_date: Optional[datetime] = None
    years_since_bankruptcy: Optional[float] = None
    has_foreclosure: Optional[bool] = None
    has_open_tax_liens: Optional[bool] = None
    tax_lien_amount: Optional[float] = None
    has_judgments: Optional[bool] = None
    has_collections: Optional[bool] = None
    derogatory_marks: Optional[List[str]] = None


class PersonalGuarantorResponse(PersonalGuarantorBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Business Credit Schemas ==============

class BusinessCreditBase(BaseModel):
    paynet_score: Optional[int] = None
    paynet_master_score: Optional[int] = None
    duns_number: Optional[str] = None
    paydex_score: Optional[int] = None
    experian_business_score: Optional[int] = None
    number_of_trade_lines: Optional[int] = None
    total_trade_line_balance: Optional[float] = None
    average_days_to_pay: Optional[int] = None
    has_slow_pays: bool = False
    slow_pay_count: Optional[int] = None
    has_charge_offs: bool = False
    charge_off_amount: Optional[float] = None


class BusinessCreditCreate(BusinessCreditBase):
    pass


class BusinessCreditUpdate(BaseModel):
    paynet_score: Optional[int] = None
    paynet_master_score: Optional[int] = None
    duns_number: Optional[str] = None
    paydex_score: Optional[int] = None
    experian_business_score: Optional[int] = None
    number_of_trade_lines: Optional[int] = None
    total_trade_line_balance: Optional[float] = None
    average_days_to_pay: Optional[int] = None
    has_slow_pays: Optional[bool] = None
    slow_pay_count: Optional[int] = None
    has_charge_offs: Optional[bool] = None
    charge_off_amount: Optional[float] = None


class BusinessCreditResponse(BusinessCreditBase):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Loan Request Schemas ==============

class LoanRequestBase(BaseModel):
    requested_amount: float = Field(..., gt=0)
    loan_purpose: Optional[str] = None
    term_months: Optional[int] = None
    equipment_type: Optional[str] = None
    equipment_description: Optional[str] = None
    equipment_cost: Optional[float] = None
    equipment_year: Optional[int] = None
    equipment_age_years: Optional[float] = None
    equipment_condition: Optional[str] = None
    is_titled: bool = False
    vendor_name: Optional[str] = None
    vendor_invoice_available: bool = False
    down_payment_amount: Optional[float] = None
    down_payment_percent: Optional[float] = None
    use_case: Optional[str] = None


class LoanRequestCreate(LoanRequestBase):
    pass


class LoanRequestUpdate(BaseModel):
    requested_amount: Optional[float] = None
    loan_purpose: Optional[str] = None
    term_months: Optional[int] = None
    equipment_type: Optional[str] = None
    equipment_description: Optional[str] = None
    equipment_cost: Optional[float] = None
    equipment_year: Optional[int] = None
    equipment_age_years: Optional[float] = None
    equipment_condition: Optional[str] = None
    is_titled: Optional[bool] = None
    vendor_name: Optional[str] = None
    vendor_invoice_available: Optional[bool] = None
    down_payment_amount: Optional[float] = None
    down_payment_percent: Optional[float] = None
    use_case: Optional[str] = None


class LoanRequestResponse(BaseModel):
    id: int
    application_id: int
    created_at: datetime
    updated_at: datetime
    requested_amount: Optional[float] = None  # Allow 0 or None for draft applications
    loan_purpose: Optional[str] = None
    term_months: Optional[int] = None
    equipment_type: Optional[str] = None
    equipment_description: Optional[str] = None
    equipment_cost: Optional[float] = None
    equipment_year: Optional[int] = None
    equipment_age_years: Optional[float] = None
    equipment_condition: Optional[str] = None
    is_titled: bool = False
    vendor_name: Optional[str] = None
    vendor_invoice_available: bool = False
    down_payment_amount: Optional[float] = None
    down_payment_percent: Optional[float] = None
    use_case: Optional[str] = None

    class Config:
        from_attributes = True


# ============== Full Application Schemas ==============

class LoanApplicationCreate(BaseModel):
    business: BusinessCreate
    guarantor: PersonalGuarantorCreate
    business_credit: Optional[BusinessCreditCreate] = None
    loan_request: LoanRequestCreate


class LoanApplicationUpdate(BaseModel):
    business: Optional[BusinessUpdate] = None
    guarantor: Optional[PersonalGuarantorUpdate] = None
    business_credit: Optional[BusinessCreditUpdate] = None
    loan_request: Optional[LoanRequestUpdate] = None


class LoanApplicationResponse(BaseModel):
    id: int
    reference_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    business: Optional[BusinessResponse] = None
    guarantor: Optional[PersonalGuarantorResponse] = None
    business_credit: Optional[BusinessCreditResponse] = None
    loan_request: Optional[LoanRequestResponse] = None

    class Config:
        from_attributes = True


class LoanApplicationSummary(BaseModel):
    id: int
    reference_id: str
    status: str
    business_name: Optional[str] = None
    requested_amount: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoanApplicationListResponse(BaseModel):
    applications: List[LoanApplicationSummary]
    total: int
