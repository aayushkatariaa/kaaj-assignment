"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lenders table
    op.create_table(
        'lenders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('source_pdf_name', sa.String(length=500), nullable=True),
        sa.Column('source_pdf_url', sa.String(length=1000), nullable=True),
        sa.Column('policy_version', sa.String(length=50), nullable=True),
        sa.Column('policy_effective_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_lenders_name', 'lenders', ['name'])
    op.create_index('ix_lenders_is_active', 'lenders', ['is_active'])

    # Create lender_programs table
    op.create_table(
        'lender_programs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lender_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('min_loan_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('max_loan_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('min_fico', sa.Integer(), nullable=True),
        sa.Column('equipment_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('excluded_industries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('eligible_states', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['lender_id'], ['lenders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lender_programs_lender_id', 'lender_programs', ['lender_id'])

    # Create policy_criteria table
    op.create_table(
        'policy_criteria',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('criteria_type', sa.String(length=100), nullable=False),
        sa.Column('criteria_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('operator', sa.String(length=20), nullable=False),
        sa.Column('numeric_value', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('numeric_value_min', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('numeric_value_max', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('string_value', sa.String(length=500), nullable=True),
        sa.Column('list_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('fail_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['program_id'], ['lender_programs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_policy_criteria_program_id', 'policy_criteria', ['program_id'])
    op.create_index('ix_policy_criteria_criteria_type', 'policy_criteria', ['criteria_type'])

    # Create loan_applications table
    op.create_table(
        'loan_applications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('reference_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('reference_id')
    )
    op.create_index('ix_loan_applications_reference_id', 'loan_applications', ['reference_id'])
    op.create_index('ix_loan_applications_status', 'loan_applications', ['status'])

    # Create businesses table
    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('legal_name', sa.String(length=500), nullable=False),
        sa.Column('dba_name', sa.String(length=500), nullable=True),
        sa.Column('state', sa.String(length=2), nullable=True),
        sa.Column('city', sa.String(length=200), nullable=True),
        sa.Column('zip_code', sa.String(length=20), nullable=True),
        sa.Column('industry', sa.String(length=200), nullable=True),
        sa.Column('naics_code', sa.String(length=20), nullable=True),
        sa.Column('sic_code', sa.String(length=20), nullable=True),
        sa.Column('formation_date', sa.Date(), nullable=True),
        sa.Column('years_in_business', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('annual_revenue', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('has_tax_liens', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_businesses_application_id', 'businesses', ['application_id'], unique=True)

    # Create personal_guarantors table
    op.create_table(
        'personal_guarantors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('ssn_last_four', sa.String(length=4), nullable=True),
        sa.Column('ownership_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('fico_score', sa.Integer(), nullable=True),
        sa.Column('has_bankruptcy', sa.Boolean(), nullable=True),
        sa.Column('bankruptcy_discharge_date', sa.Date(), nullable=True),
        sa.Column('has_foreclosure', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_personal_guarantors_application_id', 'personal_guarantors', ['application_id'], unique=True)

    # Create business_credits table
    op.create_table(
        'business_credits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('duns_number', sa.String(length=20), nullable=True),
        sa.Column('paynet_score', sa.Integer(), nullable=True),
        sa.Column('experian_intelliscore', sa.Integer(), nullable=True),
        sa.Column('dnb_paydex', sa.Integer(), nullable=True),
        sa.Column('total_trade_lines', sa.Integer(), nullable=True),
        sa.Column('credit_utilization', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_business_credits_application_id', 'business_credits', ['application_id'], unique=True)

    # Create loan_requests table
    op.create_table(
        'loan_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('requested_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('down_payment_percent', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('term_months', sa.Integer(), nullable=True),
        sa.Column('equipment_type', sa.String(length=200), nullable=True),
        sa.Column('equipment_description', sa.Text(), nullable=True),
        sa.Column('equipment_year', sa.Integer(), nullable=True),
        sa.Column('equipment_new_or_used', sa.String(length=20), nullable=True),
        sa.Column('vendor_name', sa.String(length=300), nullable=True),
        sa.Column('use_of_funds', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_loan_requests_application_id', 'loan_requests', ['application_id'], unique=True)

    # Create underwriting_runs table
    op.create_table(
        'underwriting_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('workflow_run_id', sa.String(length=200), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('lenders_evaluated', sa.Integer(), nullable=True),
        sa.Column('eligible_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_underwriting_runs_application_id', 'underwriting_runs', ['application_id'])

    # Create match_results table
    op.create_table(
        'match_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('lender_id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=True),
        sa.Column('run_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('fit_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('criteria_met', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('criteria_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_met', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('required_total', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('recommendation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['application_id'], ['loan_applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lender_id'], ['lenders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['program_id'], ['lender_programs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['run_id'], ['underwriting_runs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_match_results_application_id', 'match_results', ['application_id'])
    op.create_index('ix_match_results_lender_id', 'match_results', ['lender_id'])

    # Create criteria_evaluations table
    op.create_table(
        'criteria_evaluations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('match_result_id', sa.Integer(), nullable=False),
        sa.Column('criteria_id', sa.Integer(), nullable=True),
        sa.Column('criteria_type', sa.String(length=100), nullable=False),
        sa.Column('criteria_name', sa.String(length=200), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('expected_value', sa.String(length=500), nullable=True),
        sa.Column('actual_value', sa.String(length=500), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['match_result_id'], ['match_results.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['criteria_id'], ['policy_criteria.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_criteria_evaluations_match_result_id', 'criteria_evaluations', ['match_result_id'])


def downgrade() -> None:
    op.drop_table('criteria_evaluations')
    op.drop_table('match_results')
    op.drop_table('underwriting_runs')
    op.drop_table('loan_requests')
    op.drop_table('business_credits')
    op.drop_table('personal_guarantors')
    op.drop_table('businesses')
    op.drop_table('loan_applications')
    op.drop_table('policy_criteria')
    op.drop_table('lender_programs')
    op.drop_table('lenders')
