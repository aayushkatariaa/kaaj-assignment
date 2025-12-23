"""
PDF Parser Service using OpenAI or Gemini
Extracts lender credit programs and policies from PDF documents using vision API
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import base64
from openai import OpenAI
import google.generativeai as genai

from app.configs.app_configs import settings
from app.utils.logger_utils import logger
from app.utils.image_utils import pdf_to_images_base64, pdf_to_images, cleanup_temp_images


class PDFParserService:
    """Service to parse lender policy PDFs using OpenAI or Gemini vision APIs."""
    
    def __init__(self, provider: str = "openai"):
        """
        Initialize PDF parser with specified AI provider.
        
        Args:
            provider: "openai" or "gemini"
        """
        self.provider = provider.lower()
        
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("Initialized PDF parser with OpenAI Vision")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                raise
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required for Gemini provider")
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.client = genai.GenerativeModel('gemini-3-flash-preview')
                logger.info("Initialized PDF parser with Gemini Vision")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise
        else:
            raise ValueError(f"Unsupported AI provider: {provider}. Use 'openai' or 'gemini'")
        
        self.pdfs_dir = Path(__file__).parent.parent.parent / "pdfs"
        self.pdfs_dir.mkdir(exist_ok=True)
    
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Parse a lender policy PDF and extract credit programs with all tiers and rates.
        
        Args:
            pdf_path: Path to the PDF file (relative to pdfs directory or absolute)
        
        Returns:
            Dict containing lender info and list of credit programs with their criteria
        """
        # Resolve path
        if not Path(pdf_path).is_absolute():
            pdf_path = self.pdfs_dir / pdf_path
        else:
            pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Parsing PDF with vision API: {pdf_path}")
        
        try:
            # Convert PDF to base64 images for vision API
            base64_images = pdf_to_images_base64(str(pdf_path), dpi=300)
            logger.info(f"Converted PDF to {len(base64_images)} page images")
            
            # Use appropriate extraction method based on provider
            if self.provider == "openai":
                extracted_data = self._extract_with_openai_vision(base64_images, pdf_path.name)
            elif self.provider == "gemini":
                extracted_data = self._extract_with_gemini_vision(base64_images, pdf_path.name)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            logger.info(f"Successfully extracted data from {pdf_path} using {self.provider} vision")
            return extracted_data
        except Exception as e:
            logger.error(f"Error parsing PDF {pdf_path}: {e}")
            raise
    
    def _extract_with_openai_vision(self, base64_images: List[str], filename: str) -> Dict[str, Any]:
        """
        Use OpenAI Vision API to extract structured data from PDF images.
        """
        import json
        
        # Build messages with all page images
        content = [
            {
                "type": "text",
                "text": self._get_extraction_prompt(filename)
            }
        ]
        
        # Add all page images
        for i, base64_image in enumerate(base64_images):
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{base64_image}",
                    "detail": "high"  # High detail for better extraction
                }
            })
        
        logger.info(f"Sending {len(base64_images)} page images to OpenAI Vision API")
        
        # Use OpenAI Vision API to structure the data
        response = self.client.chat.completions.create(
            model="gpt-4o",  # GPT-4 Vision
            messages=[
                {
                    "role": "system", 
                    "content": "You are a lender policy document expert. Extract ALL credit programs, tiers, rates, and underwriting criteria from policy documents. Return only valid JSON."
                },
                {
                    "role": "user", 
                    "content": content
                }
            ],
            temperature=0,
            max_tokens=16000,  # Increased for detailed extraction
            response_format={"type": "json_object"}
        )
        
        extracted_data = json.loads(response.choices[0].message.content)
        
        # Clean up and validate the data
        return self._clean_extracted_data(extracted_data)
    
    def _extract_with_gemini_vision(self, base64_images: List[str], filename: str) -> Dict[str, Any]:
        """
        Use Gemini Vision API to extract structured data from PDF images.
        """
        import json
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        
        # Convert base64 images to PIL Images for Gemini
        from PIL import Image
        import io
        
        pil_images = []
        for base64_image in base64_images:
            image_bytes = base64.b64decode(base64_image)
            pil_image = Image.open(io.BytesIO(image_bytes))
            pil_images.append(pil_image)
        
        logger.info(f"Sending {len(pil_images)} page images to Gemini Vision API")
        
        # Prepare content with prompt and all images
        content = [self._get_extraction_prompt(filename)]
        content.extend(pil_images)
        
        # Use Gemini Vision API
        response = self.client.generate_content(
            content,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        response_text = response.text
        
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        extracted_data = json.loads(response_text)
        
        # Clean up and validate the data
        return self._clean_extracted_data(extracted_data)
    
    def _get_extraction_prompt(self, filename: str) -> str:
        """Generate the extraction prompt for AI vision models."""
        return f"""
You are analyzing a lender policy document: {filename}

This document contains credit programs with different tiers, rates, and underwriting requirements.

CRITICAL EXTRACTION RULES:
1. Extract ALL credit programs, tiers, and rate information from EVERY PAGE
2. Each credit tier (A, B, C, D, E or similar) should be a SEPARATE program
3. For rate tables with multiple loan amount brackets, create a SEPARATE criteria entry for EACH bracket
4. ALL numeric values MUST go in numeric_value_min, numeric_value_max, or numeric_value fields - NOT in description
5. The description field should ONLY contain brief context, NOT the actual values

Return a JSON object with this EXACT structure:
{{
  "lender": {{
    "name": "Lender name from document",
    "display_name": "Display name",
    "description": "Brief description of lender",
    "source_pdf_name": "{filename}"
  }},
  "programs": [
    {{
      "name": "Credit Tier A",
      "description": "Top tier credit program",
      "is_active": true,
      "priority": 1,
      "criteria": [
        {{
          "criteria_type": "personal_credit",
          "criteria_name": "FICO Score",
          "operator": ">=",
          "numeric_value_min": 720,
          "numeric_value_max": null,
          "description": "Minimum FICO requirement",
          "is_required": true
        }},
        {{
          "criteria_type": "business_credit",
          "criteria_name": "PayNet Score",
          "operator": ">=",
          "numeric_value_min": 680,
          "numeric_value_max": null,
          "description": "Minimum PayNet requirement",
          "is_required": true
        }},
        {{
          "criteria_type": "business",
          "criteria_name": "Time in Business",
          "operator": ">=",
          "numeric_value_min": 36,
          "numeric_value_max": null,
          "description": "Months in business",
          "is_required": true
        }},
        {{
          "criteria_type": "loan",
          "criteria_name": "Minimum Loan Amount",
          "operator": ">=",
          "numeric_value_min": 15000,
          "numeric_value_max": null,
          "description": "Minimum financing",
          "is_required": true
        }},
        {{
          "criteria_type": "loan",
          "criteria_name": "Maximum Loan Amount",
          "operator": "<=",
          "numeric_value_min": null,
          "numeric_value_max": 500000,
          "description": "Maximum financing",
          "is_required": false
        }},
        {{
          "criteria_type": "rate",
          "criteria_name": "Rate for $15k-$50k",
          "operator": "=",
          "numeric_value": 9.0,
          "numeric_value_min": null,
          "numeric_value_max": null,
          "loan_amount_min": 15000,
          "loan_amount_max": 50000,
          "description": "Rate for small loans",
          "is_required": false
        }},
        {{
          "criteria_type": "rate",
          "criteria_name": "Rate for $50k-$150k",
          "operator": "=",
          "numeric_value": 8.25,
          "numeric_value_min": null,
          "numeric_value_max": null,
          "loan_amount_min": 50000,
          "loan_amount_max": 150000,
          "description": "Rate for medium loans",
          "is_required": false
        }},
        {{
          "criteria_type": "rate",
          "criteria_name": "Rate for $150k+",
          "operator": "=",
          "numeric_value": 7.75,
          "numeric_value_min": null,
          "numeric_value_max": null,
          "loan_amount_min": 150000,
          "loan_amount_max": null,
          "description": "Rate for large loans",
          "is_required": false
        }},
        {{
          "criteria_type": "equipment",
          "criteria_name": "Maximum Equipment Age",
          "operator": "<=",
          "numeric_value_min": null,
          "numeric_value_max": 10,
          "description": "Years",
          "is_required": false
        }},
        {{
          "criteria_type": "loan",
          "criteria_name": "Down Payment",
          "operator": ">=",
          "numeric_value_min": 10,
          "numeric_value_max": null,
          "description": "Percentage required",
          "is_required": false
        }},
        {{
          "criteria_type": "loan",
          "criteria_name": "LTV",
          "operator": "<=",
          "numeric_value_min": null,
          "numeric_value_max": 100,
          "description": "Loan to value percentage",
          "is_required": false
        }}
      ]
    }}
  ]
}}

ABSOLUTE REQUIREMENTS - FOLLOW EXACTLY:
1. numeric_value: Use for EXACT single values (e.g., a specific rate like 9.0%)
2. numeric_value_min: Use for minimum thresholds (e.g., min FICO 680, min loan $25000)
3. numeric_value_max: Use for maximum limits (e.g., max equipment age 10 years, max loan $500000)
4. description: SHORT label ONLY - DO NOT put numeric values here. Bad: "Rates vary by loan amount: $15k-$50k (9.00%)". Good: "Small loan rate bracket"

CRITERIA TYPES:
- personal_credit: FICO score, bankruptcy history, foreclosure
- business_credit: PayNet, PAYDEX, Experian business score
- business: Time in business (in MONTHS), annual revenue, industry type
- loan: Loan amount limits, LTV, down payment percentage, app-only limits
- equipment: Equipment age (in YEARS), equipment types, condition
- rate: Interest rates - CREATE SEPARATE ENTRY FOR EACH RATE BRACKET

OPERATORS:
- ">=": Greater than or equal (use numeric_value_min)
- "<=": Less than or equal (use numeric_value_max)
- "=": Exact value (use numeric_value)
- "between": Range (use both numeric_value_min AND numeric_value_max)
- "in": List of allowed values (use list_values array)
- "not_in": List of excluded values (use list_values array)

FOR RATE TABLES:
- If document shows rates varying by loan amount, create SEPARATE rate criteria for EACH bracket
- Example: "$15k-$50k: 9%", "$50k-$150k: 8.25%", "$150k+: 7.75%" = 3 separate rate criteria entries
- Put the actual rate percentage in numeric_value field

FOR INDUSTRY/STATE RESTRICTIONS:
- Use list_values array for lists (e.g., ["CA", "TX", "FL"] for allowed states)
- Use criteria_type "business" with operator "in" or "not_in"

IMPORTANT:
- Create SEPARATE programs for each credit tier (A, B, C, D, E, etc.)
- priority: Lower number = better tier (A=1, B=2, C=3, etc.)
- All time values in MONTHS, all percentages as numbers (10 not "10%")
- Extract EVERY numeric value from the document into proper fields
- If a value has a range, use both min and max fields

Return ONLY the JSON object, no additional text or markdown.
"""
    
    def _clean_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted lender and program data."""
        
        def safe_float(value):
            """Safely convert to float, return None if not possible."""
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_int(value):
            """Safely convert to int, return None if not possible."""
            if value is None or value == "":
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        cleaned = {}
        
        # Lender data
        if "lender" in data:
            lender = data["lender"]
            cleaned["lender"] = {
                "name": lender.get("name", "Unknown Lender").strip(),
                "display_name": lender.get("display_name", lender.get("name", "Unknown")).strip(),
                "description": lender.get("description"),
                "source_pdf_name": lender.get("source_pdf_name"),
            }
        else:
            # Default lender info if not provided
            cleaned["lender"] = {
                "name": "Unknown Lender",
                "display_name": "Unknown Lender",
                "description": None,
                "source_pdf_name": None,
            }
        
        # Programs data
        cleaned["programs"] = []
        if "programs" in data and isinstance(data["programs"], list):
            for program in data["programs"]:
                if not isinstance(program, dict):
                    continue
                
                cleaned_program = {
                    "name": program.get("name", "Unnamed Program").strip(),
                    "description": program.get("description"),
                    "is_active": bool(program.get("is_active", True)),
                    "priority": safe_int(program.get("priority")) or 0,
                    "criteria": []
                }
                
                # Extract min_fico, max_loan_amount etc. from criteria if present
                min_fico = None
                max_loan_amount = None
                min_loan_amount = None
                min_time_in_business = None
                min_rate = None
                max_rate = None
                
                # Process criteria
                if "criteria" in program and isinstance(program["criteria"], list):
                    for criterion in program["criteria"]:
                        if not isinstance(criterion, dict):
                            continue
                        
                        cleaned_criterion = {
                            "criteria_type": criterion.get("criteria_type", "other"),
                            "criteria_name": criterion.get("criteria_name", "Unknown").strip(),
                            "description": criterion.get("description"),
                            "operator": criterion.get("operator", ">="),
                            "numeric_value": safe_float(criterion.get("numeric_value")),
                            "numeric_value_min": safe_float(criterion.get("numeric_value_min")),
                            "numeric_value_max": safe_float(criterion.get("numeric_value_max")),
                            "string_value": criterion.get("string_value"),
                            "list_values": criterion.get("list_values"),
                            "is_required": bool(criterion.get("is_required", True)),
                            "weight": safe_float(criterion.get("weight")) or 1.0,
                            "failure_message": criterion.get("failure_message"),
                            "is_active": bool(criterion.get("is_active", True)),
                        }
                        
                        cleaned_program["criteria"].append(cleaned_criterion)
                        
                        # Extract summary fields
                        criteria_name_lower = criterion.get("criteria_name", "").lower()
                        if "fico" in criteria_name_lower and cleaned_criterion["numeric_value_min"]:
                            if min_fico is None or cleaned_criterion["numeric_value_min"] < min_fico:
                                min_fico = cleaned_criterion["numeric_value_min"]
                        
                        if "loan amount" in criteria_name_lower:
                            if cleaned_criterion["numeric_value_max"]:
                                if max_loan_amount is None or cleaned_criterion["numeric_value_max"] > max_loan_amount:
                                    max_loan_amount = cleaned_criterion["numeric_value_max"]
                            if cleaned_criterion["numeric_value_min"]:
                                if min_loan_amount is None or cleaned_criterion["numeric_value_min"] < min_loan_amount:
                                    min_loan_amount = cleaned_criterion["numeric_value_min"]
                        
                        if "time in business" in criteria_name_lower or "months in business" in criteria_name_lower or criteria_name_lower == "tib":
                            if cleaned_criterion["numeric_value_min"]:
                                if min_time_in_business is None or cleaned_criterion["numeric_value_min"] < min_time_in_business:
                                    min_time_in_business = cleaned_criterion["numeric_value_min"]
                        
                        # Extract rates - check all rate-related criteria
                        if cleaned_criterion["criteria_type"] == "rate" or "rate" in criteria_name_lower or "interest" in criteria_name_lower:
                            rate_value = cleaned_criterion["numeric_value"] or cleaned_criterion["numeric_value_min"] or cleaned_criterion["numeric_value_max"]
                            if rate_value:
                                if min_rate is None or rate_value < min_rate:
                                    min_rate = rate_value
                                if max_rate is None or rate_value > max_rate:
                                    max_rate = rate_value
                
                # Add summary fields to program
                cleaned_program["min_fico"] = safe_int(min_fico)
                cleaned_program["max_loan_amount"] = max_loan_amount
                cleaned_program["min_loan_amount"] = min_loan_amount
                cleaned_program["min_time_in_business_months"] = safe_int(min_time_in_business)
                cleaned_program["rate_type"] = "fixed"  # Default, can be extracted from criteria
                cleaned_program["min_rate"] = min_rate
                cleaned_program["max_rate"] = max_rate
                
                cleaned["programs"].append(cleaned_program)
        
        return cleaned
    
    def list_pdfs(self) -> list[str]:
        """List all PDF files in the pdfs directory."""
        return [f.name for f in self.pdfs_dir.glob("*.pdf")]


# Singleton instance - only create if API key is set
try:
    provider = settings.AI_PROVIDER.lower()
    
    if provider == "openai" and settings.OPENAI_API_KEY:
        pdf_parser = PDFParserService(provider="openai")
    elif provider == "gemini" and settings.GEMINI_API_KEY:
        pdf_parser = PDFParserService(provider="gemini")
    elif settings.OPENAI_API_KEY:  # Fallback to OpenAI if available
        pdf_parser = PDFParserService(provider="openai")
    elif settings.GEMINI_API_KEY:  # Fallback to Gemini if available
        pdf_parser = PDFParserService(provider="gemini")
    else:
        pdf_parser = None
        logger.warning("No AI provider configured for PDF parsing")
except Exception as e:
    logger.warning(f"PDF parser initialization failed: {e}")
    pdf_parser = None
