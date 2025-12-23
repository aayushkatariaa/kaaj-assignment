from logging.config import fileConfig
import os
import sys
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.datas.database import Base
from app.datas.models import (
    Lender, LenderProgram, PolicyCriteria,
    LoanApplication, Business, PersonalGuarantor, BusinessCredit,
    LoanRequest, MatchResult, CriteriaEvaluation, UnderwritingRun
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Get database URL from environment
def get_url():
    return os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/loan_underwriting")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import create_engine
    
    # Use sync driver for migrations
    url = get_url().replace("+asyncpg", "")
    
    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
