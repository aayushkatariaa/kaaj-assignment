"""
PDF Ingestion Service
Automatically processes lender policy PDFs and creates/updates lenders and programs
"""

from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.services.pdf_parser import pdf_parser
from app.datas.models import Lender, LenderProgram, PolicyCriteria
from app.utils.logger_utils import logger
import uuid


class PDFIngestionService:
    """Service to automatically ingest and process lender policy PDFs."""
    
    def __init__(self):
        self.pdfs_dir = Path(__file__).parent.parent.parent / "pdfs"
        self.processed_file = self.pdfs_dir / ".processed_pdfs"
        self.pdfs_dir.mkdir(exist_ok=True)
    
    def _load_processed_files(self) -> set:
        """Load list of already processed PDF filenames."""
        if not self.processed_file.exists():
            return set()
        with open(self.processed_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    
    def _mark_as_processed(self, filename: str):
        """Mark a PDF as processed."""
        with open(self.processed_file, 'a') as f:
            f.write(f"{filename}\n")
    
    def _generate_reference_id(self) -> str:
        """Generate a unique reference ID for the application."""
        return f"APP-{uuid.uuid4().hex[:8].upper()}"
    
    async def ingest_pdfs(self, db: AsyncSession, force: bool = False) -> Dict[str, Any]:
        """
        Ingest all lender policy PDFs from the pdfs directory.
        
        Args:
            db: Database session
            force: If True, reprocess all PDFs even if already processed
        
        Returns:
            Dict with statistics about the ingestion
        """
        if not pdf_parser:
            logger.warning("PDF parser not available (OPENAI_API_KEY not set)")
            return {
                "status": "skipped",
                "reason": "PDF parser not configured",
                "processed": 0,
                "errors": 0
            }
        
        # Get list of PDF files
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            logger.info("No PDF files found in pdfs directory")
            return {
                "status": "success",
                "processed": 0,
                "skipped": 0,
                "errors": 0,
                "files": []
            }
        
        # Load already processed files
        processed_files = set() if force else self._load_processed_files()
        
        stats = {
            "status": "success",
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "files": []
        }
        
        for pdf_path in pdf_files:
            filename = pdf_path.name
            
            # Skip if already processed (unless force=True)
            if filename in processed_files:
                logger.info(f"Skipping already processed PDF: {filename}")
                stats["skipped"] += 1
                continue
            
            try:
                logger.info(f"Processing lender policy PDF: {filename}")
                
                # Extract lender and program data from PDF
                extracted_data = pdf_parser.parse_pdf(pdf_path)
                
                # Create/update lender and programs
                lender, program_count = await self._create_lender_from_data(
                    db, extracted_data, filename
                )
                
                # Mark as processed
                self._mark_as_processed(filename)
                
                stats["processed"] += 1
                stats["files"].append({
                    "filename": filename,
                    "status": "success",
                    "lender_id": lender.id,
                    "lender_name": lender.name,
                    "programs_created": program_count
                })
                
                logger.info(f"Successfully created/updated lender {lender.name} with {program_count} programs from {filename}")
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}", exc_info=True)
                stats["errors"] += 1
                stats["files"].append({
                    "filename": filename,
                    "status": "error",
                    "error": str(e)
                })
        
        return stats
    
    async def _create_lender_from_data(
        self, 
        db: AsyncSession, 
        data: Dict[str, Any],
        source_filename: str
    ) -> tuple[Lender, int]:
        """Create or update a lender and its programs from extracted PDF data."""
        
        lender_data = data.get("lender", {})
        lender_name = lender_data.get("name", f"Lender from {source_filename}")
        
        # Check if lender already exists
        result = await db.execute(
            select(Lender).where(Lender.name == lender_name)
        )
        lender = result.scalars().first()
        
        if lender:
            logger.info(f"Updating existing lender: {lender_name}")
            # Update lender info
            lender.display_name = lender_data.get("display_name", lender_name)
            lender.description = lender_data.get("description")
            lender.source_pdf_name = source_filename
            lender.last_policy_update = datetime.now(timezone.utc)
            lender.updated_at = datetime.now(timezone.utc)
        else:
            logger.info(f"Creating new lender: {lender_name}")
            # Create new lender
            lender = Lender(
                name=lender_name,
                display_name=lender_data.get("display_name", lender_name),
                description=lender_data.get("description"),
                source_pdf_name=source_filename,
                last_policy_update=datetime.now(timezone.utc),
                is_active=True
            )
            db.add(lender)
            await db.flush()  # Get lender ID
        
        # Delete existing programs for this lender (we'll recreate them)
        if lender.id:
            result = await db.execute(
                select(LenderProgram).where(LenderProgram.lender_id == lender.id)
            )
            existing_programs = result.scalars().all()
            for program in existing_programs:
                await db.delete(program)
            await db.flush()
        
        # Create programs
        program_count = 0
        programs_data = data.get("programs", [])
        
        for program_data in programs_data:
            program = LenderProgram(
                lender_id=lender.id,
                name=program_data.get("name", "Unnamed Program"),
                description=program_data.get("description"),
                is_active=program_data.get("is_active", True),
                priority=program_data.get("priority", 0),
                min_fico=program_data.get("min_fico"),
                max_loan_amount=program_data.get("max_loan_amount"),
                min_loan_amount=program_data.get("min_loan_amount"),
                min_time_in_business_months=program_data.get("min_time_in_business_months"),
                rate_type=program_data.get("rate_type"),
                min_rate=program_data.get("min_rate"),
                max_rate=program_data.get("max_rate"),
            )
            db.add(program)
            await db.flush()  # Get program ID
            
            # Create criteria
            criteria_data = program_data.get("criteria", [])
            for criterion_data in criteria_data:
                criterion = PolicyCriteria(
                    program_id=program.id,
                    criteria_type=criterion_data.get("criteria_type", "other"),
                    criteria_name=criterion_data.get("criteria_name", "Unknown"),
                    description=criterion_data.get("description"),
                    operator=criterion_data.get("operator", ">="),
                    numeric_value=criterion_data.get("numeric_value"),
                    numeric_value_min=criterion_data.get("numeric_value_min"),
                    numeric_value_max=criterion_data.get("numeric_value_max"),
                    string_value=criterion_data.get("string_value"),
                    list_values=criterion_data.get("list_values"),
                    is_required=criterion_data.get("is_required", True),
                    weight=criterion_data.get("weight", 1.0),
                    failure_message=criterion_data.get("failure_message"),
                    is_active=criterion_data.get("is_active", True),
                )
                db.add(criterion)
            
            program_count += 1
        
        await db.commit()
        await db.refresh(lender)
        
        return lender, program_count
    
    async def get_ingestion_status(self) -> Dict[str, Any]:
        """Get status of PDF ingestion."""
        pdf_files = list(self.pdfs_dir.glob("*.pdf"))
        processed_files = self._load_processed_files()
        
        # Get AI provider name from pdf_parser
        ai_provider = "unknown"
        if pdf_parser is not None:
            ai_provider = getattr(pdf_parser, 'provider', 'gemini')  # Default to gemini since that's what we use
        
        return {
            "total_pdfs": len(pdf_files),
            "processed": len(processed_files),
            "pending": len(pdf_files) - len(processed_files),
            "pdf_parser_available": pdf_parser is not None,
            "ai_provider": ai_provider,
            "pdfs_directory": str(self.pdfs_dir),
            "files": [
                {
                    "filename": f.name,
                    "size_kb": f.stat().st_size / 1024,
                    "processed": f.name in processed_files
                }
                for f in pdf_files
            ]
        }


# Singleton instance
pdf_ingestion_service = PDFIngestionService()
