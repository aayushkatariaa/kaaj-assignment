# Loan Underwriting System - Setup Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API Key (required for PDF parsing)

### Setup Steps

1. **Create environment file**
   ```bash
   cp .env.example .env
   ```

2. **Add your OpenAI API Key**
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

3. **Start the services**
   ```bash
   docker-compose up -d --build
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

## PDF Processing

### Manual PDF Upload via UI
1. Go to http://localhost:5173/applications/new
2. Click "Upload PDF Application"
3. Select your PDF file
4. Click "Process PDF"
5. The system will extract data using OpenAI and create a draft application

### Batch PDF Processing
1. Place your PDF files in `backend/pdfs/` directory
2. Use the API endpoint to process them:
   ```bash
   curl -X POST http://localhost:8001/api/v1/applications/upload-pdf/ \
     -F "file=@backend/pdfs/your-application.pdf"
   ```

## Application Flow

1. **Create Application** (Manual or PDF)
   - Manual: Fill out 3-step form
   - PDF: Upload and auto-extract with AI

2. **Submit Application**
   - Review extracted/entered data
   - Click "Submit Application"
   - Status changes to SUBMITTED

3. **Run Underwriting**
   - Click "Run Underwriting"
   - System evaluates against lender criteria
   - Results show eligible/ineligible lenders

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Applications
- `GET /api/v1/applications/` - List all applications
- `POST /api/v1/applications/` - Create application (manual)
- `POST /api/v1/applications/upload-pdf/` - Create from PDF
- `GET /api/v1/applications/{id}` - Get application details
- `POST /api/v1/applications/{id}/submit` - Submit for underwriting
- `GET /api/v1/applications/pdfs/` - List available PDFs

### Underwriting
- `POST /api/v1/underwriting/{id}/run` - Run underwriting
- `GET /api/v1/underwriting/{id}/results` - Get results

## Troubleshooting

### PDF Processing Not Working
- Ensure OPENAI_API_KEY is set in `.env`
- Check logs: `docker logs loan-underwriting-api`
- Verify PDF is readable (not encrypted/corrupted)

### Port Already in Use
Edit `docker-compose.yml` to change ports:
```yaml
backend:
  ports:
    - "8001:8000"  # Change 8001 to another port
```

### Database Issues
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| OPENAI_API_KEY | Yes* | - | OpenAI API key for PDF parsing |
| DB_HOST | No | localhost | PostgreSQL host |
| DB_USER | No | loan_user | Database user |
| DB_PASSWORD | No | loan_pass | Database password |
| HATCHET_CLIENT_TOKEN | No | - | Hatchet workflow token (optional) |

*Required only if using PDF upload feature
