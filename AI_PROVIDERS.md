# AI Provider Configuration

The PDF parsing service now supports multiple AI providers: **OpenAI** and **Gemini**.

## Configuration

In your `.env` file:

```env
# Choose your AI provider: "openai" or "gemini"
AI_PROVIDER=gemini

# OpenAI API Key (if using openai provider)
OPENAI_API_KEY=your-openai-key-here

# Gemini API Key (if using gemini provider)
GEMINI_API_KEY=your-gemini-key-here
```

## Getting API Keys

### OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Add billing credits at https://platform.openai.com/settings/organization/billing

### Gemini (Google AI)
1. Go to https://makersuite.google.com/app/apikey
2. Create a new API key
3. Free tier available with generous limits

## How It Works

The `PDFParserService` class accepts a `provider` parameter:
- When `AI_PROVIDER=openai`, it uses GPT-4o for extraction
- When `AI_PROVIDER=gemini`, it uses Gemini 1.5 Flash for extraction

Both providers:
- Extract text from PDFs using PyPDF2
- Use structured prompts for consistent extraction
- Return the same data format
- Are cost-effective and fast

## Usage

The service automatically initializes with your chosen provider on startup. No code changes needed - just configure your `.env` file.

```python
# The singleton is created automatically based on .env
from app.services.pdf_parser import pdf_parser

# Use it the same way regardless of provider
data = pdf_parser.parse_pdf("application.pdf")
```

## Switching Providers

To switch providers:
1. Update `AI_PROVIDER` in `.env`
2. Ensure you have the corresponding API key set
3. Restart the backend: `docker-compose restart backend`

## Provider Comparison

| Feature | OpenAI (GPT-4o) | Gemini (1.5 Flash) |
|---------|-----------------|-------------------|
| Cost | ~$0.01 per PDF | Free tier, then ~$0.001 per PDF |
| Speed | Fast (1-2 sec) | Very fast (<1 sec) |
| Accuracy | Excellent | Excellent |
| Rate Limits | Based on tier | 1500 requests/day free |
| JSON Format | Native support | Markdown wrapped |

Both providers work excellently for this use case.
