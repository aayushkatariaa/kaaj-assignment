"""
FastAPI Application Entry Point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.configs.app_configs import settings
from app.datas.database import test_db_connection, init_db, db_context
from app.routers import common_routes, lender_router, application_router, underwriting_router
from app.utils.logger_utils import logger
from app.utils.request_utils import error_response
from app.services.pdf_ingestion import pdf_ingestion_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Loan Underwriting Service...")
    
    if await test_db_connection():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
    
    await init_db()
    logger.info("Database tables initialized")
    
    # Auto-ingest PDFs from /pdfs directory on startup
    try:
        logger.info("Running automatic PDF ingestion...")
        async with db_context() as db:
            stats = await pdf_ingestion_service.ingest_pdfs(db)
            logger.info(f"PDF ingestion complete: {stats}")
            if stats.get("processed", 0) > 0:
                logger.info(f"Auto-ingested {stats['processed']} PDFs on startup")
            elif stats.get("skipped", 0) > 0:
                logger.info(f"Skipped {stats['skipped']} already processed PDFs")
            if stats.get("errors", 0) > 0:
                logger.warning(f"Failed to process {stats['errors']} PDFs")
    except Exception as e:
        logger.warning(f"PDF auto-ingestion failed: {e}", exc_info=True)
    
    yield
    
    logger.info("Shutting down Loan Underwriting Service...")


app = FastAPI(
    title="Loan Underwriting API",
    version="1.0.0",
    description="Loan underwriting and lender matching system",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(common_routes.router)
app.include_router(lender_router.router, prefix="/api/v1/lenders", tags=["Lenders"])
app.include_router(application_router.router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(underwriting_router.router, prefix="/api/v1/underwriting", tags=["Underwriting"])


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return error_response(f"Internal server error: {str(exc)}", 500)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
