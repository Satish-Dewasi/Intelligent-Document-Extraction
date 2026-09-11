
from app.schemas.extraction import (
    DocumentType,
    ExtractedField,
    ExtractedValue,
    ExtractionResult,
)
from app.schemas.text_extraction import (
    ExtractionMethod,
    PageText,
    TextExtractionResult,
)
from app.services.extraction_service import ExtractionService


class FakeGeminiService:
    def __init__(self):
        self.prompt = None
        self.response_schema = None

    def extract_structured(self, prompt, response_schema):
        self.prompt = prompt
        self.response_schema = response_schema

        return ExtractionResult(
            document_type=DocumentType.INVOICE,
            fields=[
                ExtractedField(
                    name="invoice_number",
                    value=ExtractedValue(text="INV-001"),
                    page_number=1,
                    evidence="Invoice Number: INV-001",
                )
            ],
            tables=[],
        )


def test_extraction_service_uses_phase_3_text():
    gemini_service = FakeGeminiService()
    service = ExtractionService(gemini_service)

    extraction_result = TextExtractionResult(
        pages=[
            PageText(
                page_number=1,
                text="Invoice Number: INV-001",
                extraction_method=ExtractionMethod.NATIVE,
            )
        ]
    )

    result = service.extract(
        document_type="invoice",
        extraction_result=extraction_result,
    )

    assert result.document_type == DocumentType.INVOICE
    assert result.fields[0].name == "invoice_number"
    assert result.fields[0].value.text == "INV-001"

    assert "Invoice Number: INV-001" in gemini_service.prompt
    assert gemini_service.response_schema is ExtractionResult
