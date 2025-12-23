"""
Pydantic schemas for Lender and Policy management
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============== Policy Criteria Schemas ==============

class PolicyCriteriaBase(BaseModel):
    criteria_type: str = Field(..., description="Type of criteria (fico_score, time_in_business, etc.)")
    criteria_name: str = Field(..., description="Human-readable name")
    description: Optional[str] = None
    operator: str = Field(..., description="Comparison operator (gt, gte, lt, lte, eq, in, not_in, between)")
    numeric_value: Optional[float] = None
    numeric_value_min: Optional[float] = None
    numeric_value_max: Optional[float] = None
    string_value: Optional[str] = None
    list_values: Optional[List[Any]] = None
    is_required: bool = True
    weight: float = 1.0
    failure_message: Optional[str] = None
    is_active: bool = True


class PolicyCriteriaCreate(PolicyCriteriaBase):
    pass


class PolicyCriteriaUpdate(BaseModel):
    criteria_type: Optional[str] = None
    criteria_name: Optional[str] = None
    description: Optional[str] = None
    operator: Optional[str] = None
    numeric_value: Optional[float] = None
    numeric_value_min: Optional[float] = None
    numeric_value_max: Optional[float] = None
    string_value: Optional[str] = None
    list_values: Optional[List[Any]] = None
    is_required: Optional[bool] = None
    weight: Optional[float] = None
    failure_message: Optional[str] = None
    is_active: Optional[bool] = None


class PolicyCriteriaResponse(PolicyCriteriaBase):
    id: int
    program_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============== Lender Program Schemas ==============

class LenderProgramBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 0
    min_fico: Optional[int] = None
    max_loan_amount: Optional[float] = None
    min_loan_amount: Optional[float] = None
    min_time_in_business_months: Optional[int] = None
    rate_type: Optional[str] = None
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None


class LenderProgramCreate(LenderProgramBase):
    criteria: Optional[List[PolicyCriteriaCreate]] = []


class LenderProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    min_fico: Optional[int] = None
    max_loan_amount: Optional[float] = None
    min_loan_amount: Optional[float] = None
    min_time_in_business_months: Optional[int] = None
    rate_type: Optional[str] = None
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None


class LenderProgramResponse(LenderProgramBase):
    id: int
    lender_id: int
    created_at: datetime
    updated_at: datetime
    criteria: List[PolicyCriteriaResponse] = []

    class Config:
        from_attributes = True


class LenderProgramSummary(BaseModel):
    id: int
    name: str
    is_active: bool
    priority: int
    min_fico: Optional[int] = None
    max_loan_amount: Optional[float] = None
    criteria_count: int = 0

    class Config:
        from_attributes = True


# ============== Lender Schemas ==============

class LenderBase(BaseModel):
    name: str = Field(..., max_length=255)
    display_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True
    logo_url: Optional[str] = None
    source_pdf_name: Optional[str] = None


class LenderCreate(LenderBase):
    programs: Optional[List[LenderProgramCreate]] = []


class LenderUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None
    logo_url: Optional[str] = None


class LenderResponse(LenderBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_policy_update: Optional[datetime] = None
    programs: List[LenderProgramResponse] = []

    class Config:
        from_attributes = True


class LenderSummary(BaseModel):
    id: int
    name: str
    display_name: str
    is_active: bool
    program_count: int = 0

    class Config:
        from_attributes = True


class LenderListResponse(BaseModel):
    lenders: List[LenderSummary]
    total: int
