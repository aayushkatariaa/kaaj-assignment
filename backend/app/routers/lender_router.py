"""
Lender management API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.datas.database import get_db
from app.datas.models import Lender, LenderProgram, PolicyCriteria
from app.schemas.lender_schema import (
    LenderCreate, LenderUpdate, LenderResponse, LenderSummary, LenderListResponse,
    LenderProgramCreate, LenderProgramUpdate, LenderProgramResponse,
    PolicyCriteriaCreate, PolicyCriteriaUpdate, PolicyCriteriaResponse
)
from app.utils.request_utils import success_response, created_response, not_found_response
from app.utils.logger_utils import logger
from datetime import datetime, timezone

router = APIRouter()


# ============== Lender CRUD ==============

@router.get("/", response_model=LenderListResponse)
async def list_lenders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """List all lenders with pagination."""
    query = select(Lender)
    if is_active is not None:
        query = query.where(Lender.is_active == is_active)
    
    # Get total count
    count_query = select(func.count(Lender.id))
    if is_active is not None:
        count_query = count_query.where(Lender.is_active == is_active)
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query.options(selectinload(Lender.programs)))
    lenders = result.scalars().all()
    
    lender_summaries = [
        LenderSummary(
            id=l.id,
            name=l.name,
            display_name=l.display_name,
            is_active=l.is_active,
            program_count=len(l.programs)
        ) for l in lenders
    ]
    
    return LenderListResponse(lenders=lender_summaries, total=total)


@router.get("/{lender_id}", response_model=LenderResponse)
async def get_lender(lender_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific lender with all programs and criteria."""
    result = await db.execute(
        select(Lender)
        .where(Lender.id == lender_id)
        .options(
            selectinload(Lender.programs).selectinload(LenderProgram.criteria)
        )
    )
    lender = result.scalar_one_or_none()
    
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    
    return LenderResponse.model_validate(lender)


@router.post("/", response_model=LenderResponse, status_code=201)
async def create_lender(lender_data: LenderCreate, db: AsyncSession = Depends(get_db)):
    """Create a new lender with optional programs and criteria."""
    # Check if lender name already exists
    existing = await db.execute(select(Lender).where(Lender.name == lender_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Lender with this name already exists")
    
    lender = Lender(
        name=lender_data.name,
        display_name=lender_data.display_name,
        description=lender_data.description,
        website=lender_data.website,
        contact_email=lender_data.contact_email,
        contact_phone=lender_data.contact_phone,
        is_active=lender_data.is_active,
        logo_url=lender_data.logo_url,
        source_pdf_name=lender_data.source_pdf_name,
        last_policy_update=datetime.now(timezone.utc)
    )
    
    # Add programs if provided
    for prog_data in lender_data.programs or []:
        program = LenderProgram(
            name=prog_data.name,
            description=prog_data.description,
            is_active=prog_data.is_active,
            priority=prog_data.priority,
            min_fico=prog_data.min_fico,
            max_loan_amount=prog_data.max_loan_amount,
            min_loan_amount=prog_data.min_loan_amount,
            min_time_in_business_months=prog_data.min_time_in_business_months,
            rate_type=prog_data.rate_type,
            min_rate=prog_data.min_rate,
            max_rate=prog_data.max_rate
        )
        
        # Add criteria if provided
        for crit_data in prog_data.criteria or []:
            criteria = PolicyCriteria(
                criteria_type=crit_data.criteria_type,
                criteria_name=crit_data.criteria_name,
                description=crit_data.description,
                operator=crit_data.operator,
                numeric_value=crit_data.numeric_value,
                numeric_value_min=crit_data.numeric_value_min,
                numeric_value_max=crit_data.numeric_value_max,
                string_value=crit_data.string_value,
                list_values=crit_data.list_values,
                is_required=crit_data.is_required,
                weight=crit_data.weight,
                failure_message=crit_data.failure_message,
                is_active=crit_data.is_active
            )
            program.criteria.append(criteria)
        
        lender.programs.append(program)
    
    db.add(lender)
    await db.commit()
    await db.refresh(lender)
    
    # Reload with relationships
    result = await db.execute(
        select(Lender)
        .where(Lender.id == lender.id)
        .options(selectinload(Lender.programs).selectinload(LenderProgram.criteria))
    )
    lender = result.scalar_one()
    
    logger.info(f"Created lender: {lender.name}")
    return LenderResponse.model_validate(lender)


@router.put("/{lender_id}", response_model=LenderResponse)
async def update_lender(
    lender_id: int, 
    lender_data: LenderUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Update a lender's basic information."""
    result = await db.execute(
        select(Lender).where(Lender.id == lender_id)
        .options(selectinload(Lender.programs).selectinload(LenderProgram.criteria))
    )
    lender = result.scalar_one_or_none()
    
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    
    update_data = lender_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lender, field, value)
    
    lender.last_policy_update = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(lender)
    
    logger.info(f"Updated lender: {lender.name}")
    return LenderResponse.model_validate(lender)


@router.delete("/{lender_id}")
async def delete_lender(lender_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a lender and all associated programs/criteria."""
    result = await db.execute(select(Lender).where(Lender.id == lender_id))
    lender = result.scalar_one_or_none()
    
    if not lender:
        raise HTTPException(status_code=404, detail="Lender not found")
    
    await db.delete(lender)
    await db.commit()
    
    logger.info(f"Deleted lender: {lender.name}")
    return {"message": f"Lender '{lender.name}' deleted successfully"}


# ============== Program CRUD ==============

@router.get("/{lender_id}/programs", response_model=List[LenderProgramResponse])
async def list_programs(lender_id: int, db: AsyncSession = Depends(get_db)):
    """List all programs for a lender."""
    result = await db.execute(
        select(LenderProgram)
        .where(LenderProgram.lender_id == lender_id)
        .options(selectinload(LenderProgram.criteria))
    )
    programs = result.scalars().all()
    return [LenderProgramResponse.model_validate(p) for p in programs]


@router.post("/{lender_id}/programs", response_model=LenderProgramResponse, status_code=201)
async def create_program(
    lender_id: int, 
    program_data: LenderProgramCreate, 
    db: AsyncSession = Depends(get_db)
):
    """Create a new program for a lender."""
    # Verify lender exists
    lender_result = await db.execute(select(Lender).where(Lender.id == lender_id))
    if not lender_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lender not found")
    
    program = LenderProgram(
        lender_id=lender_id,
        name=program_data.name,
        description=program_data.description,
        is_active=program_data.is_active,
        priority=program_data.priority,
        min_fico=program_data.min_fico,
        max_loan_amount=program_data.max_loan_amount,
        min_loan_amount=program_data.min_loan_amount,
        min_time_in_business_months=program_data.min_time_in_business_months,
        rate_type=program_data.rate_type,
        min_rate=program_data.min_rate,
        max_rate=program_data.max_rate
    )
    
    # Add criteria if provided
    for crit_data in program_data.criteria or []:
        criteria = PolicyCriteria(
            criteria_type=crit_data.criteria_type,
            criteria_name=crit_data.criteria_name,
            description=crit_data.description,
            operator=crit_data.operator,
            numeric_value=crit_data.numeric_value,
            numeric_value_min=crit_data.numeric_value_min,
            numeric_value_max=crit_data.numeric_value_max,
            string_value=crit_data.string_value,
            list_values=crit_data.list_values,
            is_required=crit_data.is_required,
            weight=crit_data.weight,
            failure_message=crit_data.failure_message,
            is_active=crit_data.is_active
        )
        program.criteria.append(criteria)
    
    db.add(program)
    await db.commit()
    await db.refresh(program)
    
    # Reload with criteria
    result = await db.execute(
        select(LenderProgram)
        .where(LenderProgram.id == program.id)
        .options(selectinload(LenderProgram.criteria))
    )
    program = result.scalar_one()
    
    logger.info(f"Created program: {program.name} for lender_id: {lender_id}")
    return LenderProgramResponse.model_validate(program)


@router.put("/{lender_id}/programs/{program_id}", response_model=LenderProgramResponse)
async def update_program(
    lender_id: int,
    program_id: int,
    program_data: LenderProgramUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a program."""
    result = await db.execute(
        select(LenderProgram)
        .where(LenderProgram.id == program_id, LenderProgram.lender_id == lender_id)
        .options(selectinload(LenderProgram.criteria))
    )
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    update_data = program_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(program, field, value)
    
    await db.commit()
    await db.refresh(program)
    
    logger.info(f"Updated program: {program.name}")
    return LenderProgramResponse.model_validate(program)


@router.delete("/{lender_id}/programs/{program_id}")
async def delete_program(
    lender_id: int,
    program_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a program."""
    result = await db.execute(
        select(LenderProgram)
        .where(LenderProgram.id == program_id, LenderProgram.lender_id == lender_id)
    )
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    await db.delete(program)
    await db.commit()
    
    logger.info(f"Deleted program: {program.name}")
    return {"message": f"Program '{program.name}' deleted successfully"}


# ============== Criteria CRUD ==============

@router.get("/{lender_id}/programs/{program_id}/criteria", response_model=List[PolicyCriteriaResponse])
async def list_criteria(
    lender_id: int,
    program_id: int,
    db: AsyncSession = Depends(get_db)
):
    """List all criteria for a program."""
    # Verify program belongs to lender
    prog_result = await db.execute(
        select(LenderProgram)
        .where(LenderProgram.id == program_id, LenderProgram.lender_id == lender_id)
    )
    if not prog_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")
    
    result = await db.execute(
        select(PolicyCriteria).where(PolicyCriteria.program_id == program_id)
    )
    criteria = result.scalars().all()
    return [PolicyCriteriaResponse.model_validate(c) for c in criteria]


@router.post("/{lender_id}/programs/{program_id}/criteria", response_model=PolicyCriteriaResponse, status_code=201)
async def create_criteria(
    lender_id: int,
    program_id: int,
    criteria_data: PolicyCriteriaCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new criteria for a program."""
    # Verify program belongs to lender
    prog_result = await db.execute(
        select(LenderProgram)
        .where(LenderProgram.id == program_id, LenderProgram.lender_id == lender_id)
    )
    if not prog_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Program not found")
    
    criteria = PolicyCriteria(
        program_id=program_id,
        criteria_type=criteria_data.criteria_type,
        criteria_name=criteria_data.criteria_name,
        description=criteria_data.description,
        operator=criteria_data.operator,
        numeric_value=criteria_data.numeric_value,
        numeric_value_min=criteria_data.numeric_value_min,
        numeric_value_max=criteria_data.numeric_value_max,
        string_value=criteria_data.string_value,
        list_values=criteria_data.list_values,
        is_required=criteria_data.is_required,
        weight=criteria_data.weight,
        failure_message=criteria_data.failure_message,
        is_active=criteria_data.is_active
    )
    
    db.add(criteria)
    await db.commit()
    await db.refresh(criteria)
    
    logger.info(f"Created criteria: {criteria.criteria_name} for program_id: {program_id}")
    return PolicyCriteriaResponse.model_validate(criteria)


@router.put("/{lender_id}/programs/{program_id}/criteria/{criteria_id}", response_model=PolicyCriteriaResponse)
async def update_criteria(
    lender_id: int,
    program_id: int,
    criteria_id: int,
    criteria_data: PolicyCriteriaUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a criteria."""
    result = await db.execute(
        select(PolicyCriteria)
        .where(PolicyCriteria.id == criteria_id, PolicyCriteria.program_id == program_id)
    )
    criteria = result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    update_data = criteria_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(criteria, field, value)
    
    await db.commit()
    await db.refresh(criteria)
    
    logger.info(f"Updated criteria: {criteria.criteria_name}")
    return PolicyCriteriaResponse.model_validate(criteria)


@router.delete("/{lender_id}/programs/{program_id}/criteria/{criteria_id}")
async def delete_criteria(
    lender_id: int,
    program_id: int,
    criteria_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a criteria."""
    result = await db.execute(
        select(PolicyCriteria)
        .where(PolicyCriteria.id == criteria_id, PolicyCriteria.program_id == program_id)
    )
    criteria = result.scalar_one_or_none()
    
    if not criteria:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    await db.delete(criteria)
    await db.commit()
    
    logger.info(f"Deleted criteria: {criteria.criteria_name}")
    return {"message": f"Criteria '{criteria.criteria_name}' deleted successfully"}
