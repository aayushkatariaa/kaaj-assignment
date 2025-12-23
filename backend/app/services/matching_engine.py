"""
Matching Engine - Evaluates loan applications against lender policies

This is the core logic for determining eligibility and calculating fit scores.
The engine is designed to be extensible - new criteria types can be easily added.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.datas.models import (
    LoanApplication, Lender, LenderProgram, PolicyCriteria,
    Business, PersonalGuarantor, BusinessCredit, LoanRequest
)
from app.utils.logger_utils import logger


class CriteriaEvaluator:
    """
    Evaluates individual criteria against application data.
    
    This class is designed to be easily extensible:
    1. Add new criteria types by adding methods named `evaluate_{criteria_type}`
    2. Each method receives the application data and the criteria configuration
    3. Returns a tuple of (passed: bool, actual_value: str, explanation: str)
    """
    
    def __init__(self, application: LoanApplication):
        self.application = application
        self.business = application.business
        self.guarantor = application.guarantor
        self.business_credit = application.business_credit
        self.loan_request = application.loan_request
    
    def evaluate(self, criteria: PolicyCriteria) -> Dict[str, Any]:
        """
        Evaluate a single criteria against the application.
        Returns a dictionary with the evaluation result.
        """
        criteria_type = criteria.criteria_type.lower()
        
        # Try to find a specific evaluator method
        evaluator_method = getattr(self, f"evaluate_{criteria_type}", None)
        
        if evaluator_method:
            passed, actual_value, explanation = evaluator_method(criteria)
        else:
            # Fall back to generic comparison
            passed, actual_value, explanation = self.generic_evaluate(criteria)
        
        return {
            "criteria_id": criteria.id,
            "criteria_type": criteria.criteria_type,
            "criteria_name": criteria.criteria_name,
            "passed": passed,
            "is_required": criteria.is_required,
            "expected_value": self._format_expected_value(criteria),
            "actual_value": str(actual_value) if actual_value is not None else "Not provided",
            "explanation": explanation if not passed else f"✓ {criteria.criteria_name} requirement met",
            "weight": criteria.weight
        }
    
    def _format_expected_value(self, criteria: PolicyCriteria) -> str:
        """Format the expected value for display."""
        op = criteria.operator
        
        if op == "gte":
            return f"≥ {criteria.numeric_value}"
        elif op == "gt":
            return f"> {criteria.numeric_value}"
        elif op == "lte":
            return f"≤ {criteria.numeric_value}"
        elif op == "lt":
            return f"< {criteria.numeric_value}"
        elif op == "eq":
            return f"= {criteria.numeric_value or criteria.string_value}"
        elif op == "between":
            return f"{criteria.numeric_value_min} - {criteria.numeric_value_max}"
        elif op == "in":
            return f"One of: {', '.join(str(v) for v in (criteria.list_values or []))}"
        elif op == "not_in":
            return f"Not: {', '.join(str(v) for v in (criteria.list_values or []))}"
        else:
            return str(criteria.numeric_value or criteria.string_value or criteria.list_values)
    
    def _compare(self, actual: float, operator: str, criteria: PolicyCriteria) -> bool:
        """Perform numeric comparison based on operator."""
        if actual is None:
            return False
        
        if operator == "gte":
            return actual >= criteria.numeric_value
        elif operator == "gt":
            return actual > criteria.numeric_value
        elif operator == "lte":
            return actual <= criteria.numeric_value
        elif operator == "lt":
            return actual < criteria.numeric_value
        elif operator == "eq":
            return actual == criteria.numeric_value
        elif operator == "neq":
            return actual != criteria.numeric_value
        elif operator == "between":
            return criteria.numeric_value_min <= actual <= criteria.numeric_value_max
        return False
    
    def generic_evaluate(self, criteria: PolicyCriteria) -> tuple:
        """Generic evaluation for criteria without specific handlers."""
        return (False, None, f"No evaluator defined for criteria type: {criteria.criteria_type}")
    
    # ============== FICO Score Evaluators ==============
    
    def evaluate_fico_score(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate FICO score criteria."""
        if not self.guarantor:
            return (False, None, "No personal guarantor information provided")
        
        fico = self.guarantor.fico_score
        if fico is None:
            return (False, None, "FICO score not provided")
        
        passed = self._compare(fico, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"FICO score of {fico} does not meet the minimum requirement of {criteria.numeric_value}"
            )
        else:
            explanation = f"FICO score of {fico} meets requirement"
        
        return (passed, fico, explanation)
    
    # ============== PayNet Score Evaluators ==============
    
    def evaluate_paynet_score(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate PayNet score criteria."""
        if not self.business_credit:
            return (False, None, "No business credit information provided")
        
        paynet = self.business_credit.paynet_score
        if paynet is None:
            return (False, None, "PayNet score not provided")
        
        passed = self._compare(paynet, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"PayNet score of {paynet} does not meet the minimum requirement of {criteria.numeric_value}"
            )
        else:
            explanation = f"PayNet score of {paynet} meets requirement"
        
        return (passed, paynet, explanation)
    
    # ============== Time in Business Evaluators ==============
    
    def evaluate_time_in_business(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate time in business criteria (in months)."""
        if not self.business:
            return (False, None, "No business information provided")
        
        months = self.business.months_in_business
        if months is None and self.business.years_in_business:
            months = int(self.business.years_in_business * 12)
        
        if months is None:
            return (False, None, "Time in business not provided")
        
        passed = self._compare(months, criteria.operator, criteria)
        
        years_display = round(months / 12, 1)
        required_months = criteria.numeric_value
        required_years = round(required_months / 12, 1) if required_months else 0
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Business has been operating for {years_display} years ({months} months), "
                f"but minimum {required_years} years ({required_months} months) required"
            )
        else:
            explanation = f"Business operating for {years_display} years meets requirement"
        
        return (passed, months, explanation)
    
    # ============== Annual Revenue Evaluators ==============
    
    def evaluate_annual_revenue(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate annual revenue criteria."""
        if not self.business:
            return (False, None, "No business information provided")
        
        revenue = self.business.annual_revenue
        if revenue is None and self.business.monthly_revenue:
            revenue = self.business.monthly_revenue * 12
        
        if revenue is None:
            return (False, None, "Annual revenue not provided")
        
        passed = self._compare(revenue, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Annual revenue of ${revenue:,.0f} does not meet minimum of ${criteria.numeric_value:,.0f}"
            )
        else:
            explanation = f"Annual revenue of ${revenue:,.0f} meets requirement"
        
        return (passed, revenue, explanation)
    
    # ============== Loan Amount Evaluators ==============
    
    def evaluate_loan_amount_min(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate minimum loan amount criteria."""
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        amount = self.loan_request.requested_amount
        passed = self._compare(amount, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Requested amount of ${amount:,.0f} is below minimum of ${criteria.numeric_value:,.0f}"
            )
        else:
            explanation = f"Requested amount of ${amount:,.0f} meets minimum requirement"
        
        return (passed, amount, explanation)
    
    def evaluate_loan_amount_max(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate maximum loan amount criteria."""
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        amount = self.loan_request.requested_amount
        passed = self._compare(amount, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Requested amount of ${amount:,.0f} exceeds maximum of ${criteria.numeric_value:,.0f}"
            )
        else:
            explanation = f"Requested amount of ${amount:,.0f} within maximum limit"
        
        return (passed, amount, explanation)
    
    # ============== Equipment Evaluators ==============
    
    def evaluate_equipment_age(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate equipment age criteria."""
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        age = self.loan_request.equipment_age_years
        if age is None and self.loan_request.equipment_year:
            current_year = datetime.now().year
            age = current_year - self.loan_request.equipment_year
        
        if age is None:
            return (False, None, "Equipment age not provided")
        
        passed = self._compare(age, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Equipment age of {age} years exceeds maximum of {criteria.numeric_value} years"
            )
        else:
            explanation = f"Equipment age of {age} years meets requirement"
        
        return (passed, age, explanation)
    
    def evaluate_equipment_type(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate equipment type criteria (allowed/excluded types)."""
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        eq_type = self.loan_request.equipment_type
        if not eq_type:
            return (False, None, "Equipment type not provided")
        
        # Normalize equipment type: lowercase and replace spaces with underscores
        eq_type_normalized = eq_type.lower().replace(' ', '_')
        list_values = [v.lower().replace(' ', '_') for v in (criteria.list_values or [])]
        
        logger.info(f"Equipment type evaluation: '{eq_type}' -> '{eq_type_normalized}', list={list_values}, operator={criteria.operator}")
        
        if criteria.operator == "in":
            passed = eq_type_normalized in list_values
            if not passed:
                explanation = criteria.failure_message or (
                    f"Equipment type '{eq_type}' is not in the approved list: {', '.join(criteria.list_values or [])}"
                )
            else:
                explanation = f"Equipment type '{eq_type}' is approved"
        elif criteria.operator == "not_in":
            passed = eq_type_normalized not in list_values
            if not passed:
                explanation = criteria.failure_message or (
                    f"Equipment type '{eq_type}' is in the excluded list"
                )
            else:
                explanation = f"Equipment type '{eq_type}' is not excluded"
        else:
            passed = False
            explanation = f"Invalid operator for equipment type: {criteria.operator}"
        
        return (passed, eq_type, explanation)
    
    # ============== Geographic Evaluators ==============
    
    def evaluate_state_allowed(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate if business state is in allowed list."""
        if not self.business:
            return (False, None, "No business information provided")
        
        state = self.business.state
        if not state:
            return (False, None, "Business state not provided")
        
        state_upper = state.upper()
        allowed_states = [s.upper() for s in (criteria.list_values or [])]
        
        passed = state_upper in allowed_states
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Business state '{state}' is not in the approved states"
            )
        else:
            explanation = f"Business state '{state}' is approved"
        
        return (passed, state, explanation)
    
    def evaluate_state_excluded(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate if business state is NOT in excluded list."""
        if not self.business:
            return (False, None, "No business information provided")
        
        state = self.business.state
        if not state:
            return (False, None, "Business state not provided")
        
        state_upper = state.upper()
        excluded_states = [s.upper() for s in (criteria.list_values or [])]
        
        passed = state_upper not in excluded_states
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Business state '{state}' is in the excluded states list"
            )
        else:
            explanation = f"Business state '{state}' is not excluded"
        
        return (passed, state, explanation)
    
    # ============== Industry Evaluators ==============
    
    def evaluate_industry_allowed(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate if industry is in allowed list."""
        if not self.business:
            return (False, None, "No business information provided")
        
        industry = self.business.industry
        if not industry:
            return (False, None, "Industry not provided")
        
        industry_lower = industry.lower()
        allowed = [i.lower() for i in (criteria.list_values or [])]
        
        # Check for partial matches as well
        passed = industry_lower in allowed or any(a in industry_lower for a in allowed)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Industry '{industry}' is not in the approved industries"
            )
        else:
            explanation = f"Industry '{industry}' is approved"
        
        return (passed, industry, explanation)
    
    def evaluate_industry_excluded(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate if industry is NOT in excluded list."""
        if not self.business:
            return (False, None, "No business information provided")
        
        industry = self.business.industry
        if not industry:
            # If no industry provided, assume not excluded
            return (True, None, "Industry not provided - assuming not excluded")
        
        industry_lower = industry.lower()
        excluded = [i.lower() for i in (criteria.list_values or [])]
        
        # Check for partial matches
        passed = not (industry_lower in excluded or any(e in industry_lower for e in excluded))
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Industry '{industry}' is in the excluded industries list"
            )
        else:
            explanation = f"Industry '{industry}' is not excluded"
        
        return (passed, industry, explanation)
    
    # ============== Credit History Evaluators ==============
    
    def evaluate_bankruptcy_lookback(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate bankruptcy history criteria."""
        if not self.guarantor:
            return (False, None, "No personal guarantor information provided")
        
        if not self.guarantor.has_bankruptcy:
            return (True, "No bankruptcy", "No bankruptcy on record")
        
        years_since = self.guarantor.years_since_bankruptcy
        if years_since is None:
            return (False, "Bankruptcy - unknown date", "Bankruptcy on record but discharge date unknown")
        
        # criteria.numeric_value is the lookback period in years
        passed = years_since >= criteria.numeric_value
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Bankruptcy discharged {years_since:.1f} years ago, "
                f"but must be at least {criteria.numeric_value} years"
            )
        else:
            explanation = f"Bankruptcy discharged {years_since:.1f} years ago, meets {criteria.numeric_value} year requirement"
        
        return (passed, f"{years_since:.1f} years since discharge", explanation)
    
    def evaluate_tax_lien_max(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate tax lien criteria."""
        if not self.guarantor:
            return (False, None, "No personal guarantor information provided")
        
        if not self.guarantor.has_open_tax_liens:
            return (True, "$0", "No open tax liens")
        
        lien_amount = self.guarantor.tax_lien_amount or 0
        passed = self._compare(lien_amount, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Open tax liens of ${lien_amount:,.0f} exceed maximum of ${criteria.numeric_value:,.0f}"
            )
        else:
            explanation = f"Tax liens of ${lien_amount:,.0f} within acceptable limit"
        
        return (passed, f"${lien_amount:,.0f}", explanation)
    
    # ============== Down Payment Evaluators ==============
    
    def evaluate_down_payment_percent(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate down payment percentage criteria."""
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        down_pct = self.loan_request.down_payment_percent
        if down_pct is None:
            # Calculate from amounts if available
            if self.loan_request.down_payment_amount and self.loan_request.equipment_cost:
                down_pct = (self.loan_request.down_payment_amount / self.loan_request.equipment_cost) * 100
            else:
                return (False, None, "Down payment information not provided")
        
        passed = self._compare(down_pct, criteria.operator, criteria)
        
        if not passed:
            explanation = criteria.failure_message or (
                f"Down payment of {down_pct:.1f}% does not meet minimum of {criteria.numeric_value}%"
            )
        else:
            explanation = f"Down payment of {down_pct:.1f}% meets requirement"
        
        return (passed, f"{down_pct:.1f}%", explanation)

    # ============== Generic Type Evaluators (for PDF-extracted criteria) ==============
    
    def evaluate_personal_credit(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate personal credit criteria based on criteria_name."""
        criteria_name = criteria.criteria_name.lower()
        
        # FICO score check
        if "fico" in criteria_name:
            if not self.guarantor:
                return (False, None, "No personal guarantor information provided")
            
            fico = self.guarantor.fico_score
            if fico is None:
                return (False, None, "FICO score not provided")
            
            # Get the threshold value
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold is None:
                return (True, fico, f"FICO score: {fico}")
            
            passed = fico >= threshold
            if not passed:
                explanation = f"FICO score {fico} is below minimum {threshold}"
            else:
                explanation = f"FICO score {fico} meets minimum {threshold}"
            return (passed, fico, explanation)
        
        # Bankruptcy check
        if "bankruptcy" in criteria_name:
            if not self.guarantor:
                return (False, None, "No personal guarantor information provided")
            
            if not self.guarantor.has_bankruptcy:
                return (True, "No bankruptcy", "No bankruptcy history")
            
            # Check years since bankruptcy
            years_since = self.guarantor.years_since_bankruptcy
            if years_since is None:
                return (False, "Bankruptcy on record", "Bankruptcy history exists but discharge date not provided")
            
            # Threshold is in months
            threshold_months = criteria.numeric_value or criteria.numeric_value_min
            if threshold_months:
                threshold_years = threshold_months / 12
                passed = years_since >= threshold_years
                if not passed:
                    explanation = f"Bankruptcy discharged {years_since:.1f} years ago, requires {threshold_years:.1f}+ years"
                else:
                    explanation = f"Bankruptcy discharged {years_since:.1f} years ago meets requirement"
                return (passed, f"{years_since:.1f} years", explanation)
            
            return (True, f"{years_since:.1f} years", "Bankruptcy history evaluated")
        
        # Default - pass if no specific check
        return (True, "N/A", f"Personal credit criteria '{criteria.criteria_name}' not specifically evaluated")
    
    def evaluate_business_credit(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate business credit criteria based on criteria_name."""
        criteria_name = criteria.criteria_name.lower()
        
        if not self.business_credit:
            return (False, None, "No business credit information provided")
        
        # PayNet score check
        if "paynet" in criteria_name:
            paynet = self.business_credit.paynet_score or self.business_credit.paynet_master_score
            if paynet is None:
                return (False, None, "PayNet score not provided")
            
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold is None:
                return (True, paynet, f"PayNet score: {paynet}")
            
            passed = paynet >= threshold
            if not passed:
                explanation = f"PayNet score {paynet} is below minimum {threshold}"
            else:
                explanation = f"PayNet score {paynet} meets minimum {threshold}"
            return (passed, paynet, explanation)
        
        # PAYDEX score check  
        if "paydex" in criteria_name:
            paydex = self.business_credit.paydex_score
            if paydex is None:
                return (False, None, "PAYDEX score not provided")
            
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold is None:
                return (True, paydex, f"PAYDEX score: {paydex}")
            
            passed = paydex >= threshold
            if not passed:
                explanation = f"PAYDEX score {paydex} is below minimum {threshold}"
            else:
                explanation = f"PAYDEX score {paydex} meets minimum {threshold}"
            return (passed, paydex, explanation)
        
        # Experian business score check
        if "experian" in criteria_name:
            experian = self.business_credit.experian_business_score
            if experian is None:
                return (False, None, "Experian business score not provided")
            
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold is None:
                return (True, experian, f"Experian score: {experian}")
            
            passed = experian >= threshold
            if not passed:
                explanation = f"Experian score {experian} is below minimum {threshold}"
            else:
                explanation = f"Experian score {experian} meets minimum {threshold}"
            return (passed, experian, explanation)
        
        return (True, "N/A", f"Business credit criteria '{criteria.criteria_name}' not specifically evaluated")
    
    def evaluate_business(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate business criteria based on criteria_name."""
        criteria_name = criteria.criteria_name.lower()
        
        if not self.business:
            return (False, None, "No business information provided")
        
        # Time in business check
        if "time in business" in criteria_name or "tib" in criteria_name or "years in business" in criteria_name:
            months = self.business.months_in_business
            if months is None and self.business.years_in_business:
                months = int(self.business.years_in_business * 12)
            
            if months is None:
                return (False, None, "Time in business not provided")
            
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold is None:
                return (True, f"{months} months", f"Business operating for {months/12:.1f} years")
            
            passed = months >= threshold
            years_display = months / 12
            threshold_years = threshold / 12
            
            if not passed:
                explanation = f"Business operating {years_display:.1f} years ({months} months), requires {threshold_years:.1f}+ years ({threshold} months)"
            else:
                explanation = f"Business operating {years_display:.1f} years meets {threshold_years:.1f} year requirement"
            return (passed, f"{months} months", explanation)
        
        # Revenue check
        if "revenue" in criteria_name:
            revenue = self.business.annual_revenue
            if revenue is None:
                return (False, None, "Annual revenue not provided")
            
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold is None:
                return (True, f"${revenue:,.0f}", f"Annual revenue: ${revenue:,.0f}")
            
            passed = revenue >= threshold
            if not passed:
                explanation = f"Annual revenue ${revenue:,.0f} is below minimum ${threshold:,.0f}"
            else:
                explanation = f"Annual revenue ${revenue:,.0f} meets requirement"
            return (passed, f"${revenue:,.0f}", explanation)
        
        # Industry check
        if "industry" in criteria_name or "restricted" in criteria_name:
            industry = self.business.industry
            if not industry:
                return (True, "Not specified", "Industry not specified, assuming eligible")
            
            # Check for excluded industries
            if criteria.list_values:
                excluded = [x.lower() for x in criteria.list_values]
                if industry.lower() in excluded:
                    return (False, industry, f"Industry '{industry}' is restricted")
            
            return (True, industry, f"Industry '{industry}' is eligible")
        
        # Fleet size (for trucking)
        if "fleet" in criteria_name or "truck" in criteria_name:
            # We don't have fleet size in our schema, so skip
            return (True, "N/A", "Fleet size not evaluated (not in application)")
        
        return (True, "N/A", f"Business criteria '{criteria.criteria_name}' not specifically evaluated")
    
    def evaluate_loan(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate loan-related criteria based on criteria_name."""
        criteria_name = criteria.criteria_name.lower()
        
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        amount = self.loan_request.requested_amount
        
        # Loan amount checks
        if "loan amount" in criteria_name or "app only" in criteria_name or "app-only" in criteria_name:
            if amount is None:
                return (False, None, "Loan amount not provided")
            
            # Check minimum
            if "min" in criteria_name:
                threshold = criteria.numeric_value or criteria.numeric_value_min
                if threshold:
                    passed = amount >= threshold
                    if not passed:
                        return (False, f"${amount:,.0f}", f"Requested ${amount:,.0f} is below minimum ${threshold:,.0f}")
                    return (True, f"${amount:,.0f}", f"Requested amount meets minimum")
            
            # Check maximum (app-only limits)
            threshold = criteria.numeric_value or criteria.numeric_value_max
            if threshold:
                passed = amount <= threshold
                if not passed:
                    return (False, f"${amount:,.0f}", f"Requested ${amount:,.0f} exceeds limit ${threshold:,.0f}")
                return (True, f"${amount:,.0f}", f"Requested amount within limit")
            
            return (True, f"${amount:,.0f}", f"Loan amount: ${amount:,.0f}")
        
        # LTV check
        if "ltv" in criteria_name:
            if self.loan_request.equipment_cost and self.loan_request.equipment_cost > 0:
                ltv = (amount / self.loan_request.equipment_cost) * 100
                threshold = criteria.numeric_value or criteria.numeric_value_max
                if threshold:
                    passed = ltv <= threshold
                    if not passed:
                        return (False, f"{ltv:.1f}%", f"LTV {ltv:.1f}% exceeds maximum {threshold}%")
                    return (True, f"{ltv:.1f}%", f"LTV {ltv:.1f}% within limit")
            return (True, "N/A", "LTV not calculable (no equipment cost)")
        
        # Down payment check
        if "down payment" in criteria_name:
            down_pct = self.loan_request.down_payment_percent
            if down_pct is None and self.loan_request.down_payment_amount and self.loan_request.equipment_cost:
                down_pct = (self.loan_request.down_payment_amount / self.loan_request.equipment_cost) * 100
            
            if down_pct is None:
                return (True, "N/A", "Down payment not specified")
            
            threshold = criteria.numeric_value or criteria.numeric_value_min
            if threshold:
                passed = down_pct >= threshold
                if not passed:
                    return (False, f"{down_pct:.1f}%", f"Down payment {down_pct:.1f}% below required {threshold}%")
                return (True, f"{down_pct:.1f}%", f"Down payment {down_pct:.1f}% meets requirement")
            return (True, f"{down_pct:.1f}%", f"Down payment: {down_pct:.1f}%")
        
        # Comparable credit (skip - we don't track this)
        if "comparable" in criteria_name:
            return (True, "N/A", "Comparable credit history not tracked in application")
        
        return (True, "N/A", f"Loan criteria '{criteria.criteria_name}' not specifically evaluated")
    
    def evaluate_equipment(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate equipment-related criteria based on criteria_name."""
        criteria_name = criteria.criteria_name.lower()
        
        if not self.loan_request:
            return (False, None, "No loan request information provided")
        
        # Equipment age check
        if "age" in criteria_name or "year" in criteria_name:
            age = self.loan_request.equipment_age_years
            if age is None and self.loan_request.equipment_year:
                age = datetime.now().year - self.loan_request.equipment_year
            
            if age is None:
                return (True, "N/A", "Equipment age not provided")
            
            threshold = criteria.numeric_value or criteria.numeric_value_max
            if threshold:
                passed = age <= threshold
                if not passed:
                    return (False, f"{age} years", f"Equipment age {age} years exceeds maximum {threshold} years")
                return (True, f"{age} years", f"Equipment age {age} years within limit")
            return (True, f"{age} years", f"Equipment age: {age} years")
        
        # Equipment type check
        if "type" in criteria_name:
            eq_type = self.loan_request.equipment_type
            if not eq_type:
                return (True, "N/A", "Equipment type not specified")
            
            if criteria.list_values:
                allowed = [x.lower() for x in criteria.list_values]
                if eq_type.lower() in allowed:
                    return (True, eq_type, f"Equipment type '{eq_type}' is allowed")
                return (False, eq_type, f"Equipment type '{eq_type}' not in allowed list")
            
            return (True, eq_type, f"Equipment type: {eq_type}")
        
        # Equipment condition check
        if "condition" in criteria_name:
            condition = self.loan_request.equipment_condition
            if not condition:
                return (True, "N/A", "Equipment condition not specified")
            return (True, condition, f"Equipment condition: {condition}")
        
        return (True, "N/A", f"Equipment criteria '{criteria.criteria_name}' not specifically evaluated")
    
    def evaluate_rate(self, criteria: PolicyCriteria) -> tuple:
        """Evaluate rate criteria - these are informational, not pass/fail."""
        rate = criteria.numeric_value or criteria.numeric_value_min or criteria.numeric_value_max
        if rate:
            return (True, f"{rate}%", f"Rate: {rate}%")
        return (True, "N/A", "Rate information")


class MatchingEngine:
    """
    Main matching engine that evaluates applications against all lenders.
    """
    
    def evaluate_all_lenders(
        self, 
        application: LoanApplication, 
        lenders: List[Lender]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate an application against all lenders and their programs.
        Returns a list of match results.
        """
        results = []
        
        for lender in lenders:
            if not lender.is_active:
                continue
            
            # Find the best matching program for this lender
            best_program_result = None
            best_fit_score = -1
            
            for program in lender.programs:
                if not program.is_active:
                    continue
                
                program_result = self.evaluate_program(application, lender, program)
                
                # Keep track of the best program
                if program_result["fit_score"] > best_fit_score:
                    best_fit_score = program_result["fit_score"]
                    best_program_result = program_result
            
            if best_program_result:
                results.append(best_program_result)
            else:
                # No programs found, add a generic ineligible result
                results.append({
                    "lender_id": lender.id,
                    "program_id": None,
                    "status": "INELIGIBLE",
                    "fit_score": 0,
                    "summary": "No active programs available for this lender",
                    "recommendation": None,
                    "criteria_results": [],
                    "criteria_met": 0,
                    "criteria_failed": 0,
                    "criteria_total": 0
                })
        
        return results
    
    def evaluate_program(
        self,
        application: LoanApplication,
        lender: Lender,
        program: LenderProgram
    ) -> Dict[str, Any]:
        """
        Evaluate an application against a specific lender program.
        """
        evaluator = CriteriaEvaluator(application)
        criteria_results = []
        
        required_passed = 0
        required_failed = 0
        optional_passed = 0
        optional_failed = 0
        total_weight = 0
        weighted_score = 0
        
        for criteria in program.criteria:
            if not criteria.is_active:
                continue
            
            result = evaluator.evaluate(criteria)
            criteria_results.append(result)
            
            if result["is_required"]:
                if result["passed"]:
                    required_passed += 1
                else:
                    required_failed += 1
            else:
                if result["passed"]:
                    optional_passed += 1
                else:
                    optional_failed += 1
            
            # Calculate weighted score
            total_weight += result["weight"]
            if result["passed"]:
                weighted_score += result["weight"]
        
        # Determine eligibility
        total_criteria = len(criteria_results)
        criteria_met = required_passed + optional_passed
        criteria_failed = required_failed + optional_failed
        
        # Calculate fit score (0-100)
        if total_weight > 0:
            fit_score = (weighted_score / total_weight) * 100
        else:
            fit_score = 100 if required_failed == 0 else 0
        
        # Determine status
        if required_failed > 0:
            status = "INELIGIBLE"
            # Find the failed required criteria for summary
            failed_criteria = [r for r in criteria_results if r["is_required"] and not r["passed"]]
            summary = f"Failed {required_failed} required criteria: " + ", ".join(
                r["criteria_name"] for r in failed_criteria[:3]
            )
            if len(failed_criteria) > 3:
                summary += f" and {len(failed_criteria) - 3} more"
            recommendation = None
        elif optional_failed > 0:
            status = "NEEDS_REVIEW"
            summary = f"Met all required criteria but failed {optional_failed} optional criteria"
            recommendation = "Manual review recommended"
        else:
            status = "ELIGIBLE"
            summary = f"Meets all {total_criteria} criteria for {program.name}"
            recommendation = f"Strong candidate for {lender.display_name} - {program.name}"
        
        return {
            "lender_id": lender.id,
            "program_id": program.id,
            "status": status,
            "fit_score": round(fit_score, 1),
            "summary": summary,
            "recommendation": recommendation,
            "criteria_results": criteria_results,
            "criteria_met": criteria_met,
            "criteria_failed": criteria_failed,
            "criteria_total": total_criteria
        }
