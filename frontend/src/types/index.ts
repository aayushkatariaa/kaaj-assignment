export interface Business {
  legal_name: string
  dba_name?: string
  entity_type?: string
  state: string
  city?: string
  zip_code?: string
  address?: string
  industry?: string
  naics_code?: string
  years_in_business?: number
  months_in_business?: number
  annual_revenue?: number
  monthly_revenue?: number
  employee_count?: number
  ein?: string
}

export interface PersonalGuarantor {
  first_name: string
  last_name: string
  email?: string
  phone?: string
  ownership_percentage?: number
  fico_score?: number
  has_bankruptcy?: boolean
  bankruptcy_discharge_date?: string
  years_since_bankruptcy?: number
  has_foreclosure?: boolean
  has_open_tax_liens?: boolean
  tax_lien_amount?: number
  has_judgments?: boolean
  has_collections?: boolean
}

export interface BusinessCredit {
  paynet_score?: number
  paynet_master_score?: number
  duns_number?: string
  paydex_score?: number
  number_of_trade_lines?: number
  has_slow_pays?: boolean
  has_charge_offs?: boolean
}

export interface LoanRequest {
  requested_amount: number
  loan_purpose?: string
  term_months?: number
  equipment_type?: string
  equipment_description?: string
  equipment_cost?: number
  equipment_year?: number
  equipment_age_years?: number
  equipment_condition?: string
  is_titled?: boolean
  vendor_name?: string
  down_payment_amount?: number
  down_payment_percent?: number
  use_case?: string
}

export interface LoanApplication {
  id: number
  reference_id: string
  status: string
  created_at: string
  updated_at: string
  submitted_at?: string
  completed_at?: string
  business?: Business
  guarantor?: PersonalGuarantor
  business_credit?: BusinessCredit
  loan_request?: LoanRequest
}

export interface CriteriaEvaluation {
  criteria_id?: number
  criteria_type: string
  criteria_name: string
  passed: boolean
  is_required: boolean
  expected_value?: string
  actual_value?: string
  explanation: string
  weight: number
}

export interface LenderMatchDetail {
  lender_id: number
  lender_name: string
  lender_display_name: string
  program_id?: number
  program_name?: string
  status: string
  fit_score?: number
  summary?: string
  recommendation?: string
  criteria_met: number
  criteria_failed: number
  criteria_total: number
  criteria_details: CriteriaEvaluation[]
}

export interface UnderwritingResults {
  application_id: number
  reference_id: string
  status: string
  run_id?: number
  completed_at?: string
  total_lenders: number
  eligible_lenders: number
  ineligible_lenders: number
  needs_review_lenders: number
  best_match?: LenderMatchDetail
  eligible_matches: LenderMatchDetail[]
  ineligible_matches: LenderMatchDetail[]
  needs_review_matches: LenderMatchDetail[]
}

export interface PolicyCriteria {
  id: number
  program_id: number
  criteria_type: string
  criteria_name: string
  description?: string
  operator: string
  numeric_value?: number
  numeric_value_min?: number
  numeric_value_max?: number
  string_value?: string
  list_values?: any[]
  is_required: boolean
  weight: number
  failure_message?: string
  is_active: boolean
}

export interface LenderProgram {
  id: number
  lender_id: number
  name: string
  description?: string
  is_active: boolean
  priority: number
  min_fico?: number
  max_loan_amount?: number
  min_loan_amount?: number
  min_time_in_business_months?: number
  rate_type?: string
  min_rate?: number
  max_rate?: number
  criteria: PolicyCriteria[]
}

export interface Lender {
  id: number
  name: string
  display_name: string
  description?: string
  website?: string
  contact_email?: string
  contact_phone?: string
  is_active: boolean
  logo_url?: string
  source_pdf_name?: string
  programs: LenderProgram[]
}
