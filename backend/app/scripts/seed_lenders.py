"""
Seed script to populate database with sample lender policies
"""

import asyncio
from app.datas.database import db_context, init_db
from app.datas.models import Lender, LenderProgram, PolicyCriteria
from app.utils.logger_utils import logger


SAMPLE_LENDERS = [
    {
        "name": "stearns_bank",
        "display_name": "Stearns Bank",
        "description": "Equipment Finance Credit Box",
        "source_pdf_name": "Stearns Bank - Equipment Finance Credit Box.pdf",
        "programs": [
            {
                "name": "Standard Program",
                "description": "Standard equipment financing for established businesses",
                "priority": 1,
                "min_fico": 680,
                "min_loan_amount": 25000,
                "max_loan_amount": 500000,
                "min_time_in_business_months": 24,
                "criteria": [
                    {"criteria_type": "fico_score", "criteria_name": "Minimum FICO Score", "operator": "gte", "numeric_value": 680, "is_required": True, "weight": 2.0},
                    {"criteria_type": "time_in_business", "criteria_name": "Time in Business", "operator": "gte", "numeric_value": 24, "is_required": True, "weight": 1.5},
                    {"criteria_type": "loan_amount_min", "criteria_name": "Minimum Loan Amount", "operator": "gte", "numeric_value": 25000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "loan_amount_max", "criteria_name": "Maximum Loan Amount", "operator": "lte", "numeric_value": 500000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "bankruptcy_lookback", "criteria_name": "Bankruptcy Lookback", "operator": "gte", "numeric_value": 4, "is_required": True, "weight": 1.5},
                    {"criteria_type": "equipment_age", "criteria_name": "Equipment Age", "operator": "lte", "numeric_value": 15, "is_required": True, "weight": 1.0},
                    {"criteria_type": "industry_excluded", "criteria_name": "Excluded Industries", "operator": "not_in", "list_values": ["cannabis", "gambling", "adult_entertainment"], "is_required": True, "weight": 1.0},
                ]
            }
        ]
    },
    {
        "name": "apex_commercial",
        "display_name": "Apex Commercial Capital",
        "description": "Broker Guidelines",
        "source_pdf_name": "Apex Commercial Capital - Broker Guidelines.pdf",
        "programs": [
            {
                "name": "Prime Program",
                "description": "Best rates for strong credit",
                "priority": 2,
                "min_fico": 700,
                "min_loan_amount": 50000,
                "max_loan_amount": 1000000,
                "min_time_in_business_months": 36,
                "criteria": [
                    {"criteria_type": "fico_score", "criteria_name": "Minimum FICO Score", "operator": "gte", "numeric_value": 700, "is_required": True, "weight": 2.0},
                    {"criteria_type": "time_in_business", "criteria_name": "Time in Business", "operator": "gte", "numeric_value": 36, "is_required": True, "weight": 1.5},
                    {"criteria_type": "annual_revenue", "criteria_name": "Annual Revenue", "operator": "gte", "numeric_value": 500000, "is_required": True, "weight": 1.5},
                    {"criteria_type": "loan_amount_min", "criteria_name": "Minimum Loan Amount", "operator": "gte", "numeric_value": 50000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "loan_amount_max", "criteria_name": "Maximum Loan Amount", "operator": "lte", "numeric_value": 1000000, "is_required": True, "weight": 1.0},
                ]
            }
        ]
    },
    {
        "name": "advantage_plus",
        "display_name": "Advantage+ Financing",
        "description": "Broker ICP - $75K non-trucking",
        "source_pdf_name": "Advantage+ Financing - Broker ICP.pdf",
        "programs": [
            {
                "name": "Standard Non-Trucking",
                "description": "$75K+ for non-trucking equipment",
                "priority": 1,
                "min_fico": 650,
                "min_loan_amount": 75000,
                "max_loan_amount": 750000,
                "min_time_in_business_months": 24,
                "criteria": [
                    {"criteria_type": "fico_score", "criteria_name": "Minimum FICO Score", "operator": "gte", "numeric_value": 650, "is_required": True, "weight": 2.0},
                    {"criteria_type": "time_in_business", "criteria_name": "Time in Business", "operator": "gte", "numeric_value": 24, "is_required": True, "weight": 1.5},
                    {"criteria_type": "loan_amount_min", "criteria_name": "Minimum Loan Amount", "operator": "gte", "numeric_value": 75000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "loan_amount_max", "criteria_name": "Maximum Loan Amount", "operator": "lte", "numeric_value": 750000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "equipment_type", "criteria_name": "Equipment Type", "operator": "not_in", "list_values": ["trucking", "semi_truck"], "is_required": True, "weight": 1.0},
                ]
            }
        ]
    },
    {
        "name": "citizens_bank",
        "display_name": "Citizens Bank",
        "description": "2025 Equipment Finance Program",
        "source_pdf_name": "Citizens Bank - 2025 Equipment Finance Program.pdf",
        "programs": [
            {
                "name": "Premier Equipment Finance",
                "description": "Premium financing for established businesses",
                "priority": 2,
                "min_fico": 720,
                "min_loan_amount": 100000,
                "max_loan_amount": 2000000,
                "min_time_in_business_months": 48,
                "criteria": [
                    {"criteria_type": "fico_score", "criteria_name": "Minimum FICO Score", "operator": "gte", "numeric_value": 720, "is_required": True, "weight": 2.0},
                    {"criteria_type": "time_in_business", "criteria_name": "Time in Business", "operator": "gte", "numeric_value": 48, "is_required": True, "weight": 1.5},
                    {"criteria_type": "annual_revenue", "criteria_name": "Annual Revenue", "operator": "gte", "numeric_value": 1000000, "is_required": True, "weight": 2.0},
                    {"criteria_type": "loan_amount_min", "criteria_name": "Minimum Loan Amount", "operator": "gte", "numeric_value": 100000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "loan_amount_max", "criteria_name": "Maximum Loan Amount", "operator": "lte", "numeric_value": 2000000, "is_required": True, "weight": 1.0},
                ]
            }
        ]
    },
    {
        "name": "falcon_equipment",
        "display_name": "Falcon Equipment Finance",
        "description": "Rates & Programs",
        "source_pdf_name": "Falcon Equipment Finance - Rates & Programs.pdf",
        "programs": [
            {
                "name": "A-Credit Program",
                "description": "Best rates for A-credit borrowers",
                "priority": 2,
                "min_fico": 700,
                "min_loan_amount": 20000,
                "max_loan_amount": 500000,
                "min_time_in_business_months": 24,
                "criteria": [
                    {"criteria_type": "fico_score", "criteria_name": "Minimum FICO Score", "operator": "gte", "numeric_value": 700, "is_required": True, "weight": 2.0},
                    {"criteria_type": "time_in_business", "criteria_name": "Time in Business", "operator": "gte", "numeric_value": 24, "is_required": True, "weight": 1.5},
                    {"criteria_type": "loan_amount_min", "criteria_name": "Minimum Loan Amount", "operator": "gte", "numeric_value": 20000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "loan_amount_max", "criteria_name": "Maximum Loan Amount", "operator": "lte", "numeric_value": 500000, "is_required": True, "weight": 1.0},
                ]
            },
            {
                "name": "B-Credit Program",
                "description": "For B-credit borrowers",
                "priority": 1,
                "min_fico": 620,
                "min_loan_amount": 15000,
                "max_loan_amount": 250000,
                "min_time_in_business_months": 18,
                "criteria": [
                    {"criteria_type": "fico_score", "criteria_name": "Minimum FICO Score", "operator": "gte", "numeric_value": 620, "is_required": True, "weight": 2.0},
                    {"criteria_type": "time_in_business", "criteria_name": "Time in Business", "operator": "gte", "numeric_value": 18, "is_required": True, "weight": 1.5},
                    {"criteria_type": "loan_amount_min", "criteria_name": "Minimum Loan Amount", "operator": "gte", "numeric_value": 15000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "loan_amount_max", "criteria_name": "Maximum Loan Amount", "operator": "lte", "numeric_value": 250000, "is_required": True, "weight": 1.0},
                    {"criteria_type": "down_payment_percent", "criteria_name": "Down Payment", "operator": "gte", "numeric_value": 10, "is_required": False, "weight": 0.5},
                ]
            }
        ]
    }
]


async def seed_lenders():
    await init_db()
    
    async with db_context() as db:
        for lender_data in SAMPLE_LENDERS:
            from sqlalchemy import select
            existing = await db.execute(select(Lender).where(Lender.name == lender_data["name"]))
            if existing.scalar_one_or_none():
                logger.info(f"Lender {lender_data['name']} already exists, skipping")
                continue
            
            lender = Lender(
                name=lender_data["name"],
                display_name=lender_data["display_name"],
                description=lender_data["description"],
                source_pdf_name=lender_data.get("source_pdf_name"),
                is_active=True
            )
            
            for prog_data in lender_data["programs"]:
                program = LenderProgram(
                    name=prog_data["name"],
                    description=prog_data.get("description"),
                    priority=prog_data.get("priority", 0),
                    min_fico=prog_data.get("min_fico"),
                    min_loan_amount=prog_data.get("min_loan_amount"),
                    max_loan_amount=prog_data.get("max_loan_amount"),
                    min_time_in_business_months=prog_data.get("min_time_in_business_months"),
                    is_active=True
                )
                
                for crit_data in prog_data.get("criteria", []):
                    criteria = PolicyCriteria(
                        criteria_type=crit_data["criteria_type"],
                        criteria_name=crit_data["criteria_name"],
                        operator=crit_data["operator"],
                        numeric_value=crit_data.get("numeric_value"),
                        list_values=crit_data.get("list_values"),
                        is_required=crit_data.get("is_required", True),
                        weight=crit_data.get("weight", 1.0),
                        is_active=True
                    )
                    program.criteria.append(criteria)
                
                lender.programs.append(program)
            
            db.add(lender)
            logger.info(f"Created lender: {lender_data['display_name']}")
        
        await db.commit()
        logger.info("Seed data complete!")


if __name__ == "__main__":
    asyncio.run(seed_lenders())
