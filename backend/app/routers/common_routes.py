"""
Common routes - health checks, etc.
"""

from fastapi import APIRouter
from app.datas.database import test_db_connection

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Loan Underwriting API", "version": "1.0.0"}


@router.get("/healthcheck")
async def healthcheck():
    db_ok = await test_db_connection()
    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "disconnected"
    }
