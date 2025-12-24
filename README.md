# Kaaj.ai Loan Underwriting & Lender Matching System

A comprehensive system for evaluating business loan applications against multiple lenders' credit policies. Built with extensibility in mind, making it easy to add new lenders, modify criteria, and customize the matching logic.

## 🎯 Features

- **Multi-AI PDF Processing**: Extract loan application data from PDFs using OpenAI GPT-4o or Gemini 3 flash preview
- **Intelligent Matching Engine**: Evaluate applications against lender criteria with detailed pass/fail reasons
- **Extensible Policy System**: 15+ criteria types with easy additions via method-based pattern
- **Complete REST APIs**: Full CRUD for applications, lenders, programs, and criteria
- **Modern React UI**: Application forms, lender management, match results visualization
- **Workflow Orchestration**: Optional Hatchet integration for complex workflows
- **Docker Ready**: Complete containerization with PostgreSQL, backend, and frontend

## Architecture Overview

```
loan-underwriting/
├── backend/          # FastAPI Python backend
│   ├── app/
│   │   ├── configs/  # Configuration management
│   │   ├── datas/    # Database models & connection
│   │   ├── routers/  # API endpoints (applications, lenders, underwriting)
│   │   ├── schemas/  # Pydantic models for API
│   │   ├── services/ # Business logic (matching engine, PDF parser)
│   │   ├── scripts/  # Seed data utilities
│   │   ├── workflows/# Hatchet workflow orchestration (optional)
│   │   └── utils/    # Logging and utilities
├── frontend/         # React TypeScript with Vite
│   └── src/
│       ├── components/ # Layout components
│       ├── pages/      # Dashboard, Applications, Lenders, etc.
│       ├── services/   # API client (axios)
│       └── types/      # TypeScript definitions
└── docker-compose.yml  # 3 services: postgres, backend, frontend
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API Key or Google Gemini API Key
- (Optional) Hatchet Cloud account for workflow orchestration

### 1. Clone and Setup Environment

```bash
cd loan-underwriting

# Create .env file in the project root
cat > .env << 'EOF'
# Database
POSTGRES_DB=loan_underwriting
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# AI Provider (choose one: "openai" or "gemini")
AI_PROVIDER=gemini
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# Optional: Hatchet workflow orchestration
# HATCHET_CLIENT_TOKEN=your_hatchet_token
EOF

# Edit .env with your actual API keys
```

### 2. Start Services with Docker

```bash
# Start all services (postgres, backend, frontend)
docker-compose up -d

# Check logs
docker-compose logs -f backend
```

**Services will be available at:**
- Frontend UI: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- PostgreSQL: localhost:5432

### 3. Seed Lenders with Real Policies

The system comes with 5 lenders pre-configured from real guideline PDFs:

```bash
# Seed the database with lenders, programs, and criteria
docker exec loan-underwriting-api python -m app.scripts.seed_lenders
```

**Seeded Lenders:**
- **Stearns Bank**: Standard Program (FICO ≥680, $25K-$500K, 2+ years in business)
- **Apex Commercial**: Prime Program (FICO ≥700, $50K-$1M, $500K+ revenue)
- **Advantage+ Financing**: Non-Trucking Program (FICO ≥650, $75K-$750K)
- **Citizens Bank**: Premier Program (FICO ≥720, $100K-$2M, $1M+ revenue)
- **Falcon Equipment**: A-Credit (FICO ≥700) & B-Credit (FICO ≥620) Programs

### 4. Verify Setup

```bash
# Check if lenders are loaded
curl http://localhost:8001/api/v1/lenders/ | python3 -m json.tool

# Check if applications exist (from PDF ingestion)
curl http://localhost:8001/api/v1/applications/ | python3 -m json.tool
```

### 5. Access the Application

- **Frontend**: Open http://localhost:5173 in your browser
- **API Docs**: Visit http://localhost:8001/docs for interactive API documentation

## End-to-End Testing Workflow

### 1. Submit a Test Application

```bash
# Submit an existing draft application
curl -X POST 'http://localhost:8001/api/v1/applications/3/submit' | python3 -m json.tool
```

### 2. Run Underwriting

```bash
# Start underwriting evaluation against all lenders
curl -X POST 'http://localhost:8001/api/v1/underwriting/3/run' | python3 -m json.tool
```

### 3. Check Results

```bash
# Wait a few seconds, then fetch results
curl 'http://localhost:8001/api/v1/underwriting/3/results' | python3 -m json.tool
```

**Expected Output:**
- Eligible lenders with 100% fit scores
- Ineligible lenders with specific failure reasons
- "Needs Review" lenders (met required but failed optional criteria)
- Detailed criteria evaluation for each lender program

## API Endpoints

### Applications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/applications` | List all applications |
| POST | `/api/v1/applications` | Create new application |
| GET | `/api/v1/applications/{id}` | Get application details |
| PUT | `/api/v1/applications/{id}` | Update application |
| POST | `/api/v1/applications/{id}/submit` | Submit for underwriting |
| DELETE | `/api/v1/applications/{id}` | Delete application |
| POST | `/api/v1/applications/upload-pdf` | Upload PDF for extraction |

### Lenders

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/lenders` | List all lenders |
| POST | `/api/v1/lenders` | Create new lender |
| GET | `/api/v1/lenders/{id}` | Get lender details with programs |
| PUT | `/api/v1/lenders/{id}` | Update lender |
| DELETE | `/api/v1/lenders/{id}` | Delete lender |
| POST | `/api/v1/lenders/{id}/programs` | Add program to lender |
| POST | `/api/v1/lenders/{id}/programs/{pid}/criteria` | Add criteria to program |

### Underwriting

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/underwriting/{app_id}/run` | Start underwriting run |
| GET | `/api/v1/underwriting/{app_id}/status` | Get run status |
| GET | `/api/v1/underwriting/{app_id}/results` | Get match results with details |

## Matching Engine

The matching engine evaluates applications against lender criteria using an extensible evaluator pattern.

### Supported Criteria Types (15+)

| Type | Description | Example Config |
|------|-------------|----------------|
| `fico_score` | Personal FICO score | `{"min_value": 680}` |
| `paynet_score` | Business credit score | `{"min_value": 70}` |
| `time_in_business` | Months in operation | `{"min_months": 24}` |
| `annual_revenue` | Business revenue | `{"min_revenue": 500000}` |
| `loan_amount_min` | Minimum loan size | `{"min_amount": 25000}` |
| `loan_amount_max` | Maximum loan size | `{"max_amount": 500000}` |
| `equipment_type` | Equipment categories | `{"excluded_types": ["trucking"]}` |
| `equipment_age` | Age in years | `{"max_age": 15}` |
| `state_coverage` | Eligible states | `{"states": ["CA", "TX", "NY"]}` |
| `industry_excluded` | Prohibited industries | `{"excluded": ["cannabis", "gambling"]}` |
| `bankruptcy_lookback` | Years since bankruptcy | `{"min_years": 4}` |
| `foreclosure_lookback` | Years since foreclosure | `{"min_years": 3}` |
| `down_payment_percent` | Required down payment | `{"min_percent": 10}` |
| `debt_service_coverage` | DSCR ratio | `{"min_ratio": 1.25}` |
| `collateral_coverage` | LTV ratio | `{"max_ltv": 80}` |

### How Matching Works

1. Application is submitted via API or UI
2. User initiates underwriting run
3. System fetches all active lenders and programs
4. For each program, evaluates all policy criteria
5. Calculates fit score (0-100) based on criteria weights
6. Returns results:
   - **ELIGIBLE**: Passed all required criteria (fit score 90-100)
   - **INELIGIBLE**: Failed one or more required criteria
   - **NEEDS_REVIEW**: Passed required but failed optional criteria

### Extensibility

Add new criteria types by creating a method in [matching_engine.py](backend/app/services/matching_engine.py):

```python
def _evaluate_new_criteria_type(
    self,
    application: LoanApplication,
    config: dict,
    is_required: bool
) -> CriteriaEvaluationResult:
    # Your custom logic here
    passed = your_evaluation_logic(application, config)
    return CriteriaEvaluationResult(
        passed=passed,
        expected_value="...",
        actual_value="...",
        explanation="..."
    )
```

## Adding New Lenders

### Method 1: Via Seed Script (Recommended)

Edit [seed_lenders.py](backend/app/scripts/seed_lenders.py) and add your lender:

```python
new_lender = Lender(
    name="my_lender",
    display_name="My Lender Inc.",
    is_active=True
)
db.add(new_lender)

# Add programs and criteria...
```

### Method 2: Via API

```bash
# Create lender
curl -X POST http://localhost:8001/api/v1/lenders \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my_lender",
    "display_name": "My Lender Inc.",
    "is_active": true
  }'

# Add program
curl -X POST http://localhost:8001/api/v1/lenders/1/programs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Standard Program",
    "description": "Prime credit program",
    "is_active": true
  }'

# Add criteria
curl -X POST http://localhost:8001/api/v1/lenders/1/programs/1/criteria \
  -H "Content-Type: application/json" \
  -d '{
    "criteria_type": "fico_score",
    "criteria_name": "Minimum FICO Score",
    "is_required": true,
    "config": {"min_value": 680},
    "weight": 2.0
  }'
```

### Method 3: Via Frontend UI

1. Navigate to http://localhost:5173/lenders
2. Click "Add New Lender"
3. Fill in lender details
4. Add programs and criteria through the UI

## Sample Lenders (Pre-Configured)

The seed script includes 5 real lenders based on actual guideline PDFs:

1. **Stearns Bank** - Standard Program (FICO ≥680, $25K-$500K, 4-year bankruptcy lookback)
2. **Apex Commercial Capital** - Prime Program (FICO ≥700, $50K-$1M, $500K+ revenue)
3. **Advantage+ Financing** - Non-Trucking Program (FICO ≥650, $75K-$750K, excludes trucking)
4. **Citizens Bank** - Premier Program (FICO ≥720, $100K-$2M, $1M+ revenue, 4+ years in business)
5. **Falcon Equipment Finance** - A-Credit & B-Credit Programs (tiered credit structure)

## Optional: Hatchet Workflow Orchestration

The system includes a Hatchet workflow for complex underwriting orchestration. This is **optional** and the system works with background tasks by default.

### Workflow Architecture

```
validate_application → derive_features → evaluate_lenders → aggregate_results
```

**Steps:**
1. **Validate Application**: Ensures all required data present
2. **Derive Features**: Calculate equipment age, time in business, down payment %
3. **Evaluate Lenders**: Parallel evaluation against all active lender programs
4. **Aggregate Results**: Compile match results and fit scores

### Setting Up Hatchet (Optional)

1. **Sign up for Hatchet Cloud**
   - Visit https://cloud.onhatchet.run
   - Create account and get API token

2. **Configure Environment**
   ```bash
   # Add to .env
   HATCHET_CLIENT_TOKEN=your_token_here
   ```

3. **Start Hatchet Worker**
   ```bash
   docker exec -it loan-underwriting-api python -m hatchet_sdk worker --config app/workflows
   ```

4. **Update Underwriting Router** (optional)
   - Modify [underwriting_router.py](backend/app/routers/underwriting_router.py)
   - Replace background task with Hatchet workflow trigger
   - See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for details

### Why Hatchet is Optional

- System works with FastAPI BackgroundTasks by default
- Hatchet adds value for complex multi-step workflows with retries
- Requires external service signup and API token
- Recommended for production, not required for development/testing

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `POSTGRES_DB` | PostgreSQL database name | Yes |
| `POSTGRES_USER` | PostgreSQL username | Yes |
| `POSTGRES_PASSWORD` | PostgreSQL password | Yes |
| `AI_PROVIDER` | AI provider ("openai" or "gemini") | Yes |
| `OPENAI_API_KEY` | OpenAI API key | If using OpenAI |
| `GEMINI_API_KEY` | Google Gemini API key | If using Gemini |
| `HATCHET_CLIENT_TOKEN` | Hatchet API token | No (optional) |
| `CORS_ORIGINS` | Allowed CORS origins | No (default: *) |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

## Development

### Local Development (Without Docker)

If you prefer to run services individually:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
# Inside backend container or local environment
docker exec -it loan-underwriting-api alembic upgrade head

# Create new migration
docker exec -it loan-underwriting-api alembic revision --autogenerate -m "description"

# Rollback
docker exec -it loan-underwriting-api alembic downgrade -1
```

### Testing

The system has been tested with real-world scenarios:

**Test Application Example:**
- Business: "abcd" company in CA
- 5 years in business, $500K annual revenue
- Guarantor FICO: 680, no bankruptcy/foreclosure
- Loan Request: $100K for steel equipment (2021, 4 years old)
- 5-month term

**Expected Results:**
- ✅ **Stearns Bank**: Eligible (100% fit score) - Meets all 7 criteria
- ✅ **Advantage+ Financing**: Eligible (100% fit score) - Meets all 5 criteria
- ❌ **Apex Commercial**: Ineligible - FICO 680 < 700 required
- ❌ **Citizens Bank**: Ineligible - FICO 680 < 720, Revenue $500K < $1M
- ⚠️ **Falcon B-Credit**: Needs Review - Missing down payment info

### Code Quality

- Backend: Python 3.11, FastAPI async patterns, type hints
- Frontend: TypeScript, React 18, Tailwind CSS
- Database: PostgreSQL with JSONB for flexible criteria
- API: RESTful design with OpenAPI documentation

## Implementation Status

✅ **90% Complete** - Production Ready

**Completed:**
- Data models for applications, lenders, criteria, matches
- PDF ingestion with multi-AI provider support (OpenAI/Gemini)
- Complete CRUD APIs for all entities
- Extensible matching engine with 15+ criteria types
- Fit scoring algorithm (0-100 scale)
- Detailed match results with pass/fail explanations
- React UI with all required pages
- Docker containerization
- Real lender policies from guideline PDFs

**Optional Enhancements:**
- Hatchet workflow orchestration (requires external setup)
- Unit/integration test coverage
- Authentication & authorization (JWT)
- Rate limiting & request validation
- Webhook notifications for match results
- Email notifications
- Advanced reporting & analytics

See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) for detailed feature breakdown.

## Troubleshooting

**Issue**: Frontend can't connect to backend
```bash
# Check if backend is running
docker logs loan-underwriting-api

# Check if port 8001 is accessible
curl http://localhost:8001/api/v1/health
```

**Issue**: Database connection errors
```bash
# Restart postgres
docker-compose restart postgres

# Check logs
docker logs loan-underwriting-postgres
```

**Issue**: PDF extraction fails
```bash
# Check AI provider configuration
docker exec loan-underwriting-api env | grep -E "(AI_PROVIDER|OPENAI|GEMINI)"

# Check API key validity
# Try switching provider in .env
```

**Issue**: Lenders not showing up
```bash
# Re-run seed script
docker exec loan-underwriting-api python -m app.scripts.seed_lenders

# Verify in database
docker exec -it loan-underwriting-postgres psql -U postgres -d loan_underwriting -c "SELECT COUNT(*) FROM lenders;"
```
