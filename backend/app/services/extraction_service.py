from app.schemas.extraction import ExtractionResult
from app.schemas.text_extraction import TextExtractionResult
from app.services.gemini_service import GeminiService


class ExtractionService:
    """Extract structured document data using Gemini."""

    def __init__(self, gemini_service: GeminiService) -> None:
        self.gemini_service = gemini_service

    def extract(
        self,
        document_type: str,
        extraction_result: TextExtractionResult,
    ) -> ExtractionResult:
        prompt = self._build_prompt(
            document_type,
            extraction_result,
        )

        return self.gemini_service.extract_structured(
            prompt=prompt,
            response_schema=ExtractionResult,
        )

    @staticmethod
    def _build_prompt(
        document_type: str,
        extraction_result: TextExtractionResult,
    ) -> str:
        document_text = "\n\n".join(
            (
                f"--- Page {page.page_number} ---\n"
                f"{page.text}"
            )
            for page in extraction_result.pages
        )

        document_guidance = {
            "invoice": """
Focus on invoice and receipt information including:
- invoice/receipt number
- invoice/receipt date and time
- vendor/supplier information
- customer/buyer information
- addresses
- telephone/fax/contact information
- tax information
- currency
- payment terms
- subtotal
- discounts
- taxes
- rounding adjustments
- total amount
- cash/payment amount
- change
- payment information
- purchase/order references
- membership/customer references
- line items
- quantities
- unit prices
- line-item amounts
- any other meaningful information
""",
            "balance_sheet": """
Focus on:
- reporting period/date
- currency
- assets
- liabilities
- equity
- current/non-current classifications
- subtotals and totals
- comparative periods
- every meaningful financial line item
""",
            "profit_and_loss": """
Focus on:
- reporting period
- currency
- revenue
- cost of goods sold
- gross profit
- operating expenses
- operating income
- non-operating items
- taxes
- net income/profit
- comparative periods
- every meaningful financial line item
""",
            "cash_flow": """
Focus on:
- reporting period
- currency
- operating activities
- investing activities
- financing activities
- opening cash
- net change in cash
- closing cash
- comparative periods
- every meaningful financial line item
""",
        }

        guidance = document_guidance.get(
            document_type.lower(),
            "Extract all meaningful information visible in the document.",
        )

        return f"""
You are a financial document information extraction system.

Document type:
{document_type}

Your task is to extract ALL meaningful information explicitly
present in the supplied document text.

Document-specific guidance:
{guidance}

IMPORTANT OCR HANDLING RULES:

1. The supplied text may contain OCR errors, missing characters,
   incorrect spacing, or misrecognized characters.

2. Use surrounding context and nearby text to understand OCR
   corruption, but DO NOT invent information.

3. When a value can be clearly recovered from the OCR text using
   strong contextual evidence, extract the recovered value.

4. When a value cannot be reliably determined, use null instead
   of guessing.

5. Never derive a value solely because it would make a financial
   calculation balance.

6. Preserve the original meaning of negative values. Values in
   parentheses or preceded by a minus sign represent negative
   values.

7. Preserve currencies and units when explicitly present.

8. Extract information even when its field name is not included
   in the document-specific guidance.

9. Extract all meaningful line items and tables.

10. Do not discard fields simply because they are uncommon.

11. Keep information from different pages distinguishable.

EXTRACTION RULES:

12. Extract only information supported by the supplied document.

13. Do NOT use outside knowledge.

14. Do NOT invent missing values.

15. Do NOT perform financial validation or reconciliation.

16. Do NOT calculate totals, taxes, quantities, or other values
    that are not explicitly present.

17. Financial calculations and validation will be performed
    separately by the application.

18. Every extracted field must contain:
    - field name
    - value
    - page number
    - supporting evidence
    - confidence when possible

19. Evidence must be copied from or directly supported by the
    supplied document text.

20. Keep evidence short and relevant to the extracted value.

21. Confidence must be a number between 0 and 1.
    Use a lower confidence when OCR corruption makes the value
    uncertain. Use null only when confidence cannot reasonably
    be determined.

TABLE RULES:

22. Extract tables whenever tabular information is present.

23. Preserve the table columns and row order.

24. Do not create values for cells that are missing or unreadable.

25. If a row contains a discount, tax, subtotal, or adjustment,
    preserve it as part of the table when appropriate.

Document text:

{document_text}
""".strip()