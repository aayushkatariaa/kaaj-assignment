"""
Loan Application API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
import uuid
from datetime import datetime, timezone
from pathlib import Path
import shutil

from app.datas.database import get_db
from app.datas.models import (
    LoanApplication, Business, PersonalGuarantor, 
    BusinessCredit, LoanRequest, ApplicationStatusEnum
)
from app.schemas.application_schema import (
    LoanApplicationCreate, LoanApplicationUpdate, 
    LoanApplicationResponse, LoanApplicationListResponse, LoanApplicationSummary
)
from app.utils.logger_utils import logger
from app.services.pdf_parser import pdf_parser
from app.services.pdf_ingestion import pdf_ingestion_service

router = APIRouter()


def generate_reference_id() -> str:
    """Generate a unique reference ID for the application."""
    return f"APP-{uuid.uuid4().hex[:8].upper()}"


@router.get("/", response_model=LoanApplicationListResponse)
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all loan applications with pagination."""
    query = select(LoanApplication).options(
        selectinload(LoanApplication.business),
        selectinload(LoanApplication.loan_request)
    )
    
    if status:
        query = query.where(LoanApplication.status == status)
    
    # Get total count
    count_query = select(func.count(LoanApplication.id))
    if status:
        count_query = count_query.where(LoanApplication.status == status)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results ordered by created_at desc
    query = query.order_by(LoanApplication.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    applications = result.scalars().all()
    
    summaries = [
        LoanApplicationSummary(
            id=app.id,
            reference_id=app.reference_id,
            status=app.status,
            business_name=app.business.legal_name if app.business else None,
            requested_amount=app.loan_request.requested_amount if app.loan_request else None,
            created_at=app.created_at
        ) for app in applications
    ]
    
    return LoanApplicationListResponse(applications=summaries, total=total)


@router.get("/{application_id}", response_model=LoanApplicationResponse)
async def get_application(application_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific loan application with all details."""
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
    
    return LoanApplicationResponse.model_validate(application)


@router.get("/ref/{reference_id}", response_model=LoanApplicationResponse)
async def get_application_by_ref(reference_id: str, db: AsyncSession = Depends(get_db)):
    """Get a loan application by reference ID."""
    result = await db.execute(
        select(LoanApplication)
        .where(LoanApplication.reference_id == reference_id)
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
    
    return LoanApplicationResponse.model_validate(application)


@router.post("/", response_model=LoanApplicationResponse, status_code=201)
async def create_application(
    app_data: LoanApplicationCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new loan application."""
    # Create the application
    application = LoanApplication(
        reference_id=generate_reference_id(),
        status=ApplicationStatusEnum.DRAFT.value
    )
    
    # Create business
    business = Business(
        **app_data.business.model_dump()
    )
    application.business = business
    
    # Create guarantor
    guarantor = PersonalGuarantor(
        **app_data.guarantor.model_dump()
    )
    application.guarantor = guarantor
    
    # Create business credit if provided
    if app_data.business_credit:
        business_credit = BusinessCredit(
            **app_data.business_credit.model_dump()
        )
        application.business_credit = business_credit
    
    # Create loan request
    loan_request = LoanRequest(
        **app_data.loan_request.model_dump()
    )
    application.loan_request = loan_request
    
    # Derive some fields
    if business.years_in_business and not business.months_in_business:
        business.months_in_business = int(business.years_in_business * 12)
    elif business.months_in_business and not business.years_in_business:
        business.years_in_business = business.months_in_business / 12
    
    # Calculate equipment age if year is provided
    if loan_request.equipment_year and not loan_request.equipment_age_years:
        current_year = datetime.now().year
        loan_request.equipment_age_years = current_year - loan_request.equipment_year
    
    # Calculate down payment percent if amounts provided
    if loan_request.down_payment_amount and loan_request.equipment_cost:
        loan_request.down_payment_percent = (
            loan_request.down_payment_amount / loan_request.equipment_cost * 100
        )
    
    db.add(application)
    await db.commit()
    await db.refresh(application)
    
    logger.info(f"Created application: {application.reference_id}")
    
    # Reload with all relationships
    result = await db.execute(
        select(LoanApplication)
        .where(LoanApplication.id == application.id)
        .options(
            selectinload(LoanApplication.business),
            selectinload(LoanApplication.guarantor),
            selectinload(LoanApplication.business_credit),
            selectinload(LoanApplication.loan_request)
        )
    )
    application = result.scalar_one()
    
    return LoanApplicationResponse.model_validate(application)


@router.put("/{application_id}", response_model=LoanApplicationResponse)
async def update_application(
    application_id: int,
    app_data: LoanApplicationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a loan application."""
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
    
    if application.status not in [ApplicationStatusEnum.DRAFT.value, ApplicationStatusEnum.SUBMITTED.value]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot update application in current status"
        )
    
    # Update business
    if app_data.business:
        for field, value in app_data.business.model_dump(exclude_unset=True).items():
            setattr(application.business, field, value)
    
    # Update guarantor
    if app_data.guarantor:
        for field, value in app_data.guarantor.model_dump(exclude_unset=True).items():
            setattr(application.guarantor, field, value)
    
    # Update business credit
    if app_data.business_credit:
        if application.business_credit:
            for field, value in app_data.business_credit.model_dump(exclude_unset=True).items():
                setattr(application.business_credit, field, value)
        else:
            business_credit = BusinessCredit(
                application_id=application.id,
                **app_data.business_credit.model_dump()
            )
            db.add(business_credit)
    
    # Update loan request
    if app_data.loan_request:
        for field, value in app_data.loan_request.model_dump(exclude_unset=True).items():
            setattr(application.loan_request, field, value)
    
    await db.commit()
    await db.refresh(application)
    
    logger.info(f"Updated application: {application.reference_id}")
    return LoanApplicationResponse.model_validate(application)


@router.post("/{application_id}/submit", response_model=LoanApplicationResponse)
async def submit_application(application_id: int, db: AsyncSession = Depends(get_db)):
    """Submit an application for underwriting."""
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
    
    if application.status != ApplicationStatusEnum.DRAFT.value:
        raise HTTPException(
            status_code=400, 
            detail="Only draft applications can be submitted"
        )
    
    # Validate completeness
    errors = []
    if not application.business:
        errors.append("Business information is required")
    else:
        if not application.business.legal_name or not application.business.legal_name.strip():
            errors.append("Business legal name is required")
        if not application.business.state or not application.business.state.strip():
            errors.append("Business state is required")
    
    if not application.guarantor:
        errors.append("Personal guarantor information is required")
    else:
        if not application.guarantor.fico_score:
            errors.append("FICO score is required for the personal guarantor")
        elif application.guarantor.fico_score < 300 or application.guarantor.fico_score > 850:
            errors.append(f"FICO score must be between 300 and 850 (provided: {application.guarantor.fico_score})")
    
    if not application.loan_request:
        errors.append("Loan request information is required")
    else:
        if not application.loan_request.requested_amount or application.loan_request.requested_amount <= 0:
            errors.append("Requested loan amount must be greater than $0")
    
    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})
    
    application.status = ApplicationStatusEnum.SUBMITTED.value
    application.submitted_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(application)
    
    logger.info(f"Submitted application: {application.reference_id}")
    return LoanApplicationResponse.model_validate(application)


@router.delete("/{application_id}")
async def delete_application(application_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a loan application."""
    result = await db.execute(
        select(LoanApplication).where(LoanApplication.id == application_id)
    )
    application = result.scalar_one_or_none()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status not in [ApplicationStatusEnum.DRAFT.value]:
        raise HTTPException(
            status_code=400, 
            detail="Only draft applications can be deleted"
        )
    
    await db.delete(application)
    await db.commit()
    
    logger.info(f"Deleted application: {application.reference_id}")
    return {"message": f"Application '{application.reference_id}' deleted successfully"}


@router.post("/upload-pdf/", response_model=LoanApplicationResponse, status_code=201)
async def create_application_from_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a PDF and create a loan application from extracted data.
    Requires OpenAI API key to be configured.
    """
    if not pdf_parser:
        raise HTTPException(
            status_code=500, 
            detail="PDF parsing is not configured. Please set OPENAI_API_KEY environment variable."
        )
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save PDF to pdfs directory
    pdfs_dir = Path(__file__).parent.parent.parent / "pdfs"
    pdfs_dir.mkdir(exist_ok=True)
    
    pdf_path = pdfs_dir / file.filename
    try:
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded PDF: {file.filename}")
        
        # Parse PDF and extract data
        extracted_data = pdf_parser.parse_pdf(pdf_path)
        
        # Create application from extracted data
        app_data = LoanApplicationCreate(**extracted_data)
        
        # Create the application (reuse existing logic)
        application = LoanApplication(
            reference_id=generate_reference_id(),
            status=ApplicationStatusEnum.DRAFT.value
        )
        
        business = Business(**app_data.business.model_dump())
        application.business = business
        
        guarantor = PersonalGuarantor(**app_data.guarantor.model_dump())
        application.guarantor = guarantor
        
        if app_data.business_credit:
            business_credit = BusinessCredit(**app_data.business_credit.model_dump())
            application.business_credit = business_credit
        
        loan_request = LoanRequest(**app_data.loan_request.model_dump())
        application.loan_request = loan_request
        
        # Derive fields
        if business.years_in_business and not business.months_in_business:
            business.months_in_business = int(business.years_in_business * 12)
        
        if loan_request.equipment_year and not loan_request.equipment_age_years:
            current_year = datetime.now().year
            loan_request.equipment_age_years = current_year - loan_request.equipment_year
        
        db.add(application)
        await db.commit()
        await db.refresh(application)
        
        logger.info(f"Created application from PDF: {application.reference_id}")
        
        # Reload with relationships
        result = await db.execute(
            select(LoanApplication)
            .where(LoanApplication.id == application.id)
            .options(
                selectinload(LoanApplication.business),
                selectinload(LoanApplication.guarantor),
                selectinload(LoanApplication.business_credit),
                selectinload(LoanApplication.loan_request)
            )
        )
        application = result.scalar_one()
        
        return LoanApplicationResponse.model_validate(application)
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        if pdf_path.exists():
            pdf_path.unlink()  # Clean up on error
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        file.file.close()


@router.get("/pdfs/", response_model=dict)
async def list_pdfs():
    """List available PDF files for processing."""
    if not pdf_parser:
        return {"pdfs": []}
    return {"pdfs": pdf_parser.list_pdfs()}


@router.post("/ingest-pdfs/", response_model=dict)
async def ingest_pdfs(
    force: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest all PDFs from the pdfs directory and create draft applications.
    
    Args:
        force: If True, reprocess all PDFs even if already processed
    
    Returns:
        Statistics about the ingestion process
    """
    logger.info(f"Starting PDF ingestion (force={force})")
    stats = await pdf_ingestion_service.ingest_pdfs(db, force=force)
    return stats


@router.get("/ingestion-status/", response_model=dict)
async def get_ingestion_status():
    """Get the status of PDF ingestion (processed vs pending)."""
    return await pdf_ingestion_service.get_ingestion_status()
