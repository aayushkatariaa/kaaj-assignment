"""
Pydantic schemas for Match Results and Underwriting
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ============== Criteria Evaluation Schemas ==============

class CriteriaEvaluationResult(BaseModel):
    criteria_id: Optional[int] = None
    criteria_type: str
    criteria_name: str
    passed: bool
    is_required: bool = True
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    explanation: str
    weight: float = 1.0


class CriteriaEvaluationResponse(CriteriaEvaluationResult):
    id: int
    match_result_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============== Match Result Schemas ==============

class MatchResultBase(BaseModel):
    status: str  # ELIGIBLE, INELIGIBLE, NEEDS_REVIEW
    fit_score: Optional[float] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None


class MatchResultCreate(MatchResultBase):
    application_id: int
    lender_id: int
    program_id: Optional[int] = None
    criteria_results: Optional[List[CriteriaEvaluationResult]] = []
    criteria_met: int = 0
    criteria_failed: int = 0
    criteria_total: int = 0


class MatchResultResponse(MatchResultBase):
    id: int
    application_id: int
    lender_id: int
    program_id: Optional[int] = None
    lender_name: Optional[str] = None
    program_name: Optional[str] = None
    criteria_results: Optional[List[CriteriaEvaluationResult]] = []
    criteria_met: int = 0
    criteria_failed: int = 0
    criteria_total: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class MatchResultSummary(BaseModel):
    id: int
    lender_name: str
    program_name: Optional[str] = None
    status: str
    fit_score: Optional[float] = None
    criteria_met: int = 0
    criteria_failed: int = 0

    class Config:
        from_attributes = True


# ============== Underwriting Run Schemas ==============

class UnderwritingRunCreate(BaseModel):
    application_id: int


class UnderwritingRunResponse(BaseModel):
    id: int
    application_id: int
    workflow_run_id: Optional[str] = None
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_lenders_evaluated: int = 0
    eligible_lenders: int = 0
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnderwritingStatusResponse(BaseModel):
    run_id: int
    application_id: int
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_lenders_evaluated: int = 0
    eligible_lenders: int = 0
    match_results: List[MatchResultSummary] = []


# ============== Full Results Response ==============

class LenderMatchDetail(BaseModel):
    lender_id: int
    lender_name: str
    lender_display_name: str
    program_id: Optional[int] = None
    program_name: Optional[str] = None
    status: str
    fit_score: Optional[float] = None
    summary: Optional[str] = None
    recommendation: Optional[str] = None
    criteria_met: int
    criteria_failed: int
    criteria_total: int
    criteria_details: List[CriteriaEvaluationResult] = []


class UnderwritingResultsResponse(BaseModel):
    application_id: int
    reference_id: str
    status: str
    run_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    total_lenders: int
    eligible_lenders: int
    ineligible_lenders: int
    needs_review_lenders: int
    best_match: Optional[LenderMatchDetail] = None
    eligible_matches: List[LenderMatchDetail] = []
    ineligible_matches: List[LenderMatchDetail] = []
    needs_review_matches: List[LenderMatchDetail] = []
