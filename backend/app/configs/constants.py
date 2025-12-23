# Application Status Constants
class ApplicationStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Match Result Constants
class MatchStatus:
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


# Criteria Types for Policy Rules
class CriteriaType:
    FICO_SCORE = "fico_score"
    PAYNET_SCORE = "paynet_score"
    TIME_IN_BUSINESS = "time_in_business"
    ANNUAL_REVENUE = "annual_revenue"
    LOAN_AMOUNT_MIN = "loan_amount_min"
    LOAN_AMOUNT_MAX = "loan_amount_max"
    EQUIPMENT_AGE = "equipment_age"
    EQUIPMENT_TYPE = "equipment_type"
    STATE_ALLOWED = "state_allowed"
    STATE_EXCLUDED = "state_excluded"
    INDUSTRY_ALLOWED = "industry_allowed"
    INDUSTRY_EXCLUDED = "industry_excluded"
    BANKRUPTCY_LOOKBACK = "bankruptcy_lookback"
    TAX_LIEN_MAX = "tax_lien_max"
    DOWN_PAYMENT_PERCENT = "down_payment_percent"


# Comparison Operators for Rules
class ComparisonOperator:
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    EQUAL = "eq"
    NOT_EQUAL = "neq"
    IN_LIST = "in"
    NOT_IN_LIST = "not_in"
    BETWEEN = "between"


# Equipment Types
EQUIPMENT_TYPES = [
    "construction",
    "trucking",
    "medical",
    "manufacturing",
    "agricultural",
    "restaurant",
    "office",
    "technology",
    "vehicles",
    "trailers",
    "titled_vehicles",
    "titled_trailers",
    "heavy_equipment",
    "yellow_iron",
    "other"
]

# US States
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
]

# Common Excluded Industries
DEFAULT_EXCLUDED_INDUSTRIES = [
    "adult_entertainment",
    "cannabis",
    "gambling",
    "weapons_firearms",
    "payday_lending",
    "cryptocurrency",
    "telemarketing"
]

# NAICS Code Categories
NAICS_CATEGORIES = {
    "agriculture": ["11"],
    "mining": ["21"],
    "construction": ["23"],
    "manufacturing": ["31", "32", "33"],
    "transportation": ["48", "49"],
    "retail": ["44", "45"],
    "healthcare": ["62"],
    "hospitality": ["72"],
    "professional_services": ["54"],
    "finance": ["52"]
}
