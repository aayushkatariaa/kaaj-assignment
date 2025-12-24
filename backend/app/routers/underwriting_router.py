"""
Underwriting API routes - initiates and tracks underwriting runs

Uses Hatchet for workflow orchestration with fallback to BackgroundTasks
if Hatchet is not configured or unavailable.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import Optional
import os

from app.datas.database import get_db
from app.datas.models import (
    LoanApplication, UnderwritingRun, MatchResult,
    ApplicationStatusEnum, Lender, LenderProgram
)
from app.schemas.match_schema import (
    UnderwritingRunResponse, UnderwritingStatusResponse,
    UnderwritingResultsResponse, LenderMatchDetail, CriteriaEvaluationResult,
    MatchResultSummary
)
from app.services.matching_engine import MatchingEngine
from app.utils.logger_utils import logger

router = APIRouter()

# Check if Hatchet is configured
HATCHET_ENABLED = bool(os.getenv("HATCHET_CLIENT_TOKEN"))
logger.info(f"Hatchet configuration: ENABLED={HATCHET_ENABLED}, TOKEN={'SET' if os.getenv('HATCHET_CLIENT_TOKEN') else 'NOT SET'}")


@router.post("/{application_id}/run", response_model=UnderwritingRunResponse)
async def start_underwriting(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start an underwriting run for an application.
    
    Uses Hatchet workflow orchestration if configured, otherwise falls back
    to FastAPI BackgroundTasks for processing.
    """
    # Get the application
    result = await db.execute(
        select(LoanApplication)
        .where(LoanApplication.id == application_id)
        .options(
            selectinload(LoanApplication.business),
            selectinload(LoanApplication.guarantor),
            selectinload(LoanApplication.business_credit),
            selectinload(LoanApplication.loan_request)
        )
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status not in [
        ApplicationStatusEnum.SUBMITTED.value,
        ApplicationStatusEnum.COMPLETED.value
    ]:
        raise HTTPException(
            status_code=400,
            detail="Application must be submitted before underwriting"
        )
    
    # Create underwriting run
    run = UnderwritingRun(
        application_id=application_id,
        status="RUNNING",
        started_at=datetime.now(timezone.utc)
    )
    db.add(run)
    
    # Update application status
    application.status = ApplicationStatusEnum.PROCESSING.value
    
    await db.commit()
    await db.refresh(run)
    
    if HATCHET_ENABLED:
        logger.info(f"Attempting to use Hatchet for application {application_id}")
        try:
            from app.workflows.underwriting_workflow import trigger_underwriting_workflow
            workflow_run_id = await trigger_underwriting_workflow(application_id)
            logger.info(f"✓ Started Hatchet workflow {workflow_run_id} for application {application.reference_id}")
        except Exception as e:
            logger.error(f"✗ Hatchet workflow failed, falling back to BackgroundTasks: {e}")
            background_tasks.add_task(
                run_matching_process,
                application_id=application_id,
                run_id=run.id
            )
    else:
        logger.info(f"Using BackgroundTasks for application {application_id} (Hatchet not configured)")
        #fallback
        background_tasks.add_task(
            run_matching_process,
            application_id=application_id,
            run_id=run.id
        )
        logger.info(f"Started BackgroundTasks for application {application.reference_id} (Hatchet not configured)")
    
    logger.info(f"Started underwriting run {run.id} for application {application.reference_id}")
    
    return UnderwritingRunResponse.model_validate(run)


async def run_matching_process(application_id: int, run_id: int):
    """Background task to run the matching process."""
    from app.datas.database import db_context
    
    async with db_context() as db:
        try:
            # Get application with all related data
            result = await db.execute(
                select(LoanApplication)
                .where(LoanApplication.id == application_id)
                .options(
                    selectinload(LoanApplication.business),
                    selectinload(LoanApplication.guarantor),
                    selectinload(LoanApplication.business_credit),
                    selectinload(LoanApplication.loan_request)
                )
            )
            application = result.scalar_one()
            
            # Get the run
            run_result = await db.execute(
                select(UnderwritingRun).where(UnderwritingRun.id == run_id)
            )
            run = run_result.scalar_one()
            
            # Get all active lenders with their programs and criteria
            lenders_result = await db.execute(
                select(Lender)
                .where(Lender.is_active == True)
                .options(
                    selectinload(Lender.programs).selectinload(LenderProgram.criteria)
                )
            )
            lenders = lenders_result.scalars().all()
            
            # Delete any existing match results for this application
            await db.execute(
                select(MatchResult).where(MatchResult.application_id == application_id)
            )
            existing_results = await db.execute(
                select(MatchResult).where(MatchResult.application_id == application_id)
            )
            for existing in existing_results.scalars().all():
                await db.delete(existing)
            
            # Run matching engine
            engine = MatchingEngine()
            match_results = engine.evaluate_all_lenders(application, lenders)
            
            # Save results
            eligible_count = 0
            for match_data in match_results:
                match_result = MatchResult(
                    application_id=application_id,
                    lender_id=match_data["lender_id"],
                    program_id=match_data.get("program_id"),
                    status=match_data["status"],
                    fit_score=match_data.get("fit_score"),
                    summary=match_data.get("summary"),
                    recommendation=match_data.get("recommendation"),
                    criteria_results=match_data.get("criteria_results"),
                    criteria_met=match_data.get("criteria_met", 0),
                    criteria_failed=match_data.get("criteria_failed", 0),
                    criteria_total=match_data.get("criteria_total", 0)
                )
                db.add(match_result)
                
                if match_data["status"] == "ELIGIBLE":
                    eligible_count += 1
            
            # Update run status
            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
            run.total_lenders_evaluated = len(match_results)
            run.eligible_lenders = eligible_count
            
            # Update application status
            application.status = ApplicationStatusEnum.COMPLETED.value
            application.completed_at = datetime.now(timezone.utc)
            
            await db.commit()
            
            logger.info(f"Completed underwriting run {run_id}: {eligible_count}/{len(match_results)} eligible")
            
        except Exception as e:
            logger.exception(f"Error in underwriting run {run_id}")
            
            # Update run with error
            run_result = await db.execute(
                select(UnderwritingRun).where(UnderwritingRun.id == run_id)
            )
            run = run_result.scalar_one()
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.now(timezone.utc)
            
            # Update application status
            app_result = await db.execute(
                select(LoanApplication).where(LoanApplication.id == application_id)
            )
            application = app_result.scalar_one()
            application.status = ApplicationStatusEnum.FAILED.value
            
            await db.commit()


@router.get("/{application_id}/status", response_model=UnderwritingStatusResponse)
async def get_underwriting_status(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get the status of the most recent underwriting run."""
    result = await db.execute(
        select(UnderwritingRun)
        .where(UnderwritingRun.application_id == application_id)
        .order_by(UnderwritingRun.created_at.desc())
        .limit(1)
    )
    run = result.scalar_one_or_none()
    
    if not run:
        raise HTTPException(status_code=404, detail="No underwriting run found")
    
    # Get match results if completed
    match_summaries = []
    if run.status == "COMPLETED":
        matches_result = await db.execute(
            select(MatchResult)
            .where(MatchResult.application_id == application_id)
            .options(
                selectinload(MatchResult.lender),
                selectinload(MatchResult.program)
            )
        )
        matches = matches_result.scalars().all()
        
        match_summaries = [
            MatchResultSummary(
                id=m.id,
                lender_name=m.lender.display_name if m.lender else "Unknown",
                program_name=m.program.name if m.program else None,
                status=m.status,
                fit_score=m.fit_score,
                criteria_met=m.criteria_met,
                criteria_failed=m.criteria_failed
            ) for m in matches
        ]
    
    return UnderwritingStatusResponse(
        run_id=run.id,
        application_id=application_id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_lenders_evaluated=run.total_lenders_evaluated,
        eligible_lenders=run.eligible_lenders,
        match_results=match_summaries
    )


@router.get("/{application_id}/results", response_model=UnderwritingResultsResponse)
async def get_underwriting_results(
    application_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed underwriting results for an application."""
    # Get application
    app_result = await db.execute(
        select(LoanApplication).where(LoanApplication.id == application_id)
    )
    application = app_result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Get the most recent run
    run_result = await db.execute(
        select(UnderwritingRun)
        .where(UnderwritingRun.application_id == application_id)
        .order_by(UnderwritingRun.created_at.desc())
        .limit(1)
    )
    run = run_result.scalar_one_or_none()
    
    # Get all match results
    matches_result = await db.execute(
        select(MatchResult)
        .where(MatchResult.application_id == application_id)
        .options(
            selectinload(MatchResult.lender),
            selectinload(MatchResult.program)
        )
        .order_by(MatchResult.fit_score.desc().nullslast())
    )
    matches = matches_result.scalars().all()
    
    # Build detailed response
    eligible_matches = []
    ineligible_matches = []
    needs_review_matches = []
    
    for match in matches:
        criteria_details = []
        if match.criteria_results:
            for cr in match.criteria_results:
                criteria_details.append(CriteriaEvaluationResult(
                    criteria_id=cr.get("criteria_id"),
                    criteria_type=cr.get("criteria_type", "unknown"),
                    criteria_name=cr.get("criteria_name", "Unknown Criteria"),
                    passed=cr.get("passed", False),
                    is_required=cr.get("is_required", True),
                    expected_value=cr.get("expected_value"),
                    actual_value=cr.get("actual_value"),
                    explanation=cr.get("explanation", ""),
                    weight=cr.get("weight", 1.0)
                ))
        
        detail = LenderMatchDetail(
            lender_id=match.lender_id,
            lender_name=match.lender.name if match.lender else "Unknown",
            lender_display_name=match.lender.display_name if match.lender else "Unknown",
            program_id=match.program_id,
            program_name=match.program.name if match.program else None,
            status=match.status,
            fit_score=match.fit_score,
            summary=match.summary,
            recommendation=match.recommendation,
            criteria_met=match.criteria_met,
            criteria_failed=match.criteria_failed,
            criteria_total=match.criteria_total,
            criteria_details=criteria_details
        )
        
        if match.status == "ELIGIBLE":
            eligible_matches.append(detail)
        elif match.status == "INELIGIBLE":
            ineligible_matches.append(detail)
        else:
            needs_review_matches.append(detail)
    
    # Sort eligible by fit score
    eligible_matches.sort(key=lambda x: x.fit_score or 0, reverse=True)
    
    best_match = eligible_matches[0] if eligible_matches else None
    
    return UnderwritingResultsResponse(
        application_id=application_id,
        reference_id=application.reference_id,
        status=application.status,
        run_id=run.id if run else None,
        completed_at=run.completed_at if run else None,
        total_lenders=len(matches),
        eligible_lenders=len(eligible_matches),
        ineligible_lenders=len(ineligible_matches),
        needs_review_lenders=len(needs_review_matches),
        best_match=best_match,
        eligible_matches=eligible_matches,
        ineligible_matches=ineligible_matches,
        needs_review_matches=needs_review_matches
    )
