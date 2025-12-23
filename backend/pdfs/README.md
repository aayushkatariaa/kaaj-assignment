# PDFs Directory

This directory is for loan application PDFs that will be automatically ingested by the system.

## How It Works

1. **Place PDFs here**: Add your loan application PDFs to this folder
2. **Automatic Processing**: On startup, the system scans this directory
3. **AI Extraction**: Uses OpenAI GPT-4o to extract data from PDFs
4. **Draft Applications**: Creates draft loan applications in the database

## Setup Required

To enable PDF processing, you need to configure OpenAI API key:

```bash
# In the root .env file:
OPENAI_API_KEY=sk-your-actual-key-here
```

Then restart the backend:
```bash
docker-compose restart backend
```

## Features

### Automatic Ingestion on Startup
- System automatically processes new PDFs when backend starts
- Tracks processed files in `.processed_pdfs` to avoid duplicates
- Only processes unprocessed PDFs

### Manual Ingestion
You can also trigger ingestion manually:

1. **Via UI**: Go to http://localhost:5173/pdf-ingestion
   - View all PDFs and their status
   - Click "Ingest New PDFs" to process pending files
   - Click "Reprocess All" to force reprocessing

2. **Via API**:
   ```bash
   # Process new PDFs only
   curl -X POST http://localhost:8001/api/v1/applications/ingest-pdfs/
   
   # Reprocess all PDFs
   curl -X POST http://localhost:8001/api/v1/applications/ingest-pdfs/?force=true
   ```

## Extracted Data

The system extracts:
- **Business Information**: Legal name, state, industry, revenue, etc.
- **Guarantor Details**: Name, email, FICO score, bankruptcy history
- **Loan Request**: Amount, purpose, equipment details, term
- **Business Credit**: PayNet score, PAYDEX, DUNS number (if available)

## File Tracking

- `.processed_pdfs` - List of successfully processed PDF filenames
- This file is created automatically after first successful ingestion
- Delete this file to reprocess all PDFs

## Example PDFs

Place your loan application PDFs here. The system works best with:
- Clear, readable text (not scanned/image-only)
- Standard loan application format
- Contains borrower, business, and loan request information

## Troubleshooting

**PDFs not processing?**
- Check OpenAI API key is set in `.env`
- Restart backend: `docker-compose restart backend`
- View logs: `docker logs loan-underwriting-api`

**Want to reprocess a PDF?**
- Option 1: Remove it from `.processed_pdfs` file
- Option 2: Use "Reprocess All" button in UI
- Option 3: API with `force=true` parameter

## Status Check

Check ingestion status at any time:
```bash
curl http://localhost:8001/api/v1/applications/ingestion-status/
```

Returns:
- Total PDFs in directory
- Number processed
- Number pending
- List of all files with status
