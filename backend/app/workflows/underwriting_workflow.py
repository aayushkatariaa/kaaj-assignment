"""
Hatchet Workflow for Loan Underwriting

This module defines the workflow orchestration using Hatchet.
The workflow handles:
1. Application validation
2. Feature derivation
3. Parallel lender evaluation
4. Results aggregation
"""

from hatchet_sdk import Hatchet, Context
from datetime import datetime, timezone
from typing import Dict, Any, List
import asyncio

from app.utils.logger_utils import logger


# Initialize Hatchet client (will be configured with token from env)
hatchet = Hatchet()


@hatchet.workflow(name="underwriting-workflow", on_events=["underwriting:start"])
class UnderwritingWorkflow:
    """
    Main underwriting workflow that orchestrates the evaluation process.
    
    Steps:
    1. validate_application - Ensures all required data is present
    2. derive_features - Calculates derived fields (equipment age, etc.)
    3. evaluate_lenders - Parallel evaluation against all lenders
    4. aggregate_results - Combines results and determines best matches
    """
    
    @hatchet.step(name="validate_application", timeout="30s", retries=2)
    async def validate_application(self, context: Context) -> Dict[str, Any]:
        """
        Validate that the application has all required information.
        """
        input_data = context.workflow_input()
        application_id = input_data.get("application_id")
        
        logger.info(f"Validating application {application_id}")
        
        from app.datas.database import db_context
        from app.datas.models import LoanApplication
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with db_context() as db:
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
                raise ValueError(f"Application {application_id} not found")
            
            errors = []
            
            # Validate required components
            if not application.business:
                errors.append("Business information is required")
            else:
                if not application.business.legal_name:
                    errors.append("Business legal name is required")
                if not application.business.state:
                    errors.append("Business state is required")
            
            if not application.guarantor:
                errors.append("Personal guarantor information is required")
            else:
                if not application.guarantor.fico_score:
                    errors.append("FICO score is required")
            
            if not application.loan_request:
                errors.append("Loan request information is required")
            else:
                if not application.loan_request.requested_amount:
                    errors.append("Requested loan amount is required")
            
            if errors:
                raise ValueError(f"Validation failed: {', '.join(errors)}")
            
            logger.info(f"Application {application_id} validated successfully")
            
            return {
                "application_id": application_id,
                "status": "validated",
                "business_state": application.business.state,
                "fico_score": application.guarantor.fico_score,
                "requested_amount": application.loan_request.requested_amount
            }
    
    @hatchet.step(name="derive_features", timeout="30s", parents=["validate_application"])
    async def derive_features(self, context: Context) -> Dict[str, Any]:
        """
        Derive additional features needed for evaluation.
        """
        validation_result = context.step_output("validate_application")
        application_id = validation_result["application_id"]
        
        logger.info(f"Deriving features for application {application_id}")
        
        from app.datas.database import db_context
        from app.datas.models import LoanApplication
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with db_context() as db:
            result = await db.execute(
                select(LoanApplication)
                .where(LoanApplication.id == application_id)
                .options(
                    selectinload(LoanApplication.business),
                    selectinload(LoanApplication.loan_request)
                )
            )
            application = result.scalar_one()
            
            # Derive time in business in months
            if application.business.years_in_business and not application.business.months_in_business:
                application.business.months_in_business = int(application.business.years_in_business * 12)
            elif application.business.months_in_business and not application.business.years_in_business:
                application.business.years_in_business = application.business.months_in_business / 12
            
            # Derive equipment age
            if application.loan_request.equipment_year and not application.loan_request.equipment_age_years:
                current_year = datetime.now().year
                application.loan_request.equipment_age_years = current_year - application.loan_request.equipment_year
            
            # Calculate down payment percent
            if application.loan_request.down_payment_amount and application.loan_request.equipment_cost:
                application.loan_request.down_payment_percent = (
                    application.loan_request.down_payment_amount / 
                    application.loan_request.equipment_cost * 100
                )
            
            await db.commit()
            
            logger.info(f"Features derived for application {application_id}")
            
            return {
                "application_id": application_id,
                "status": "features_derived",
                "months_in_business": application.business.months_in_business,
                "equipment_age_years": application.loan_request.equipment_age_years
            }
    
    @hatchet.step(name="get_active_lenders", timeout="30s", parents=["derive_features"])
    async def get_active_lenders(self, context: Context) -> Dict[str, Any]:
        """
        Get list of active lenders to evaluate against.
        """
        features_result = context.step_output("derive_features")
        application_id = features_result["application_id"]
        
        logger.info(f"Getting active lenders for application {application_id}")
        
        from app.datas.database import db_context
        from app.datas.models import Lender
        from sqlalchemy import select
        
        async with db_context() as db:
            result = await db.execute(
                select(Lender.id, Lender.name)
                .where(Lender.is_active == True)
            )
            lenders = result.all()
            
            lender_ids = [l.id for l in lenders]
            
            logger.info(f"Found {len(lender_ids)} active lenders")
            
            return {
                "application_id": application_id,
                "lender_ids": lender_ids,
                "lender_count": len(lender_ids)
            }
    
    @hatchet.step(name="evaluate_lenders", timeout="120s", parents=["get_active_lenders"], retries=3)
    async def evaluate_lenders(self, context: Context) -> Dict[str, Any]:
        """
        Evaluate application against all lenders in parallel.
        """
        lenders_result = context.step_output("get_active_lenders")
        application_id = lenders_result["application_id"]
        lender_ids = lenders_result["lender_ids"]
        
        logger.info(f"Evaluating application {application_id} against {len(lender_ids)} lenders")
        
        from app.datas.database import db_context
        from app.datas.models import LoanApplication, Lender, LenderProgram, MatchResult
        from app.services.matching_engine import MatchingEngine
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with db_context() as db:
            # Get application
            app_result = await db.execute(
                select(LoanApplication)
                .where(LoanApplication.id == application_id)
                .options(
                    selectinload(LoanApplication.business),
                    selectinload(LoanApplication.guarantor),
                    selectinload(LoanApplication.business_credit),
                    selectinload(LoanApplication.loan_request)
                )
            )
            application = app_result.scalar_one()
            
            # Get lenders with programs and criteria
            lenders_result = await db.execute(
                select(Lender)
                .where(Lender.id.in_(lender_ids))
                .options(
                    selectinload(Lender.programs).selectinload(LenderProgram.criteria)
                )
            )
            lenders = lenders_result.scalars().all()
            
            # Delete existing match results
            existing = await db.execute(
                select(MatchResult).where(MatchResult.application_id == application_id)
            )
            for m in existing.scalars().all():
                await db.delete(m)
            
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
            
            await db.commit()
            
            logger.info(f"Evaluation complete: {eligible_count}/{len(match_results)} eligible")
            
            return {
                "application_id": application_id,
                "total_evaluated": len(match_results),
                "eligible_count": eligible_count,
                "status": "evaluated"
            }
    
    @hatchet.step(name="finalize_results", timeout="30s", parents=["evaluate_lenders"])
    async def finalize_results(self, context: Context) -> Dict[str, Any]:
        """
        Finalize the underwriting run and update application status.
        """
        eval_result = context.step_output("evaluate_lenders")
        application_id = eval_result["application_id"]
        
        logger.info(f"Finalizing results for application {application_id}")
        
        from app.datas.database import db_context
        from app.datas.models import LoanApplication, UnderwritingRun, ApplicationStatusEnum
        from sqlalchemy import select
        
        async with db_context() as db:
            # Update application status
            app_result = await db.execute(
                select(LoanApplication).where(LoanApplication.id == application_id)
            )
            application = app_result.scalar_one()
            application.status = ApplicationStatusEnum.COMPLETED.value
            application.completed_at = datetime.now(timezone.utc)
            
            # Update underwriting run if exists
            run_result = await db.execute(
                select(UnderwritingRun)
                .where(UnderwritingRun.application_id == application_id)
                .order_by(UnderwritingRun.created_at.desc())
                .limit(1)
            )
            run = run_result.scalar_one_or_none()
            
            if run:
                run.status = "COMPLETED"
                run.completed_at = datetime.now(timezone.utc)
                run.total_lenders_evaluated = eval_result["total_evaluated"]
                run.eligible_lenders = eval_result["eligible_count"]
            
            await db.commit()
            
            logger.info(f"Results finalized for application {application_id}")
            
            return {
                "application_id": application_id,
                "status": "completed",
                "total_lenders": eval_result["total_evaluated"],
                "eligible_lenders": eval_result["eligible_count"],
                "completed_at": datetime.now(timezone.utc).isoformat()
            }


def get_hatchet_client() -> Hatchet:
    """Get the Hatchet client instance."""
    return hatchet


async def trigger_underwriting_workflow(application_id: int) -> str:
    """
    Trigger the underwriting workflow for an application.
    Returns the workflow run ID.
    """
    workflow_run = await hatchet.client.admin.run_workflow(
        "underwriting-workflow",
        {"application_id": application_id}
    )
    return workflow_run.workflow_run_id
