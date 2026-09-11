from app.schemas.extraction import ExtractionResult
from app.schemas.text_extraction import (
    ExtractionMethod,
    PageText,
    TextExtractionResult,
)
from app.services.extraction_service import ExtractionService
from app.services.gemini_service import GeminiService


def test_real_gemini_invoice_extraction():
    pages = TextExtractionResult(
        pages=[
            PageText(
                page_number=1,
                text="""
                INVOICE

                Invoice Number: INV-001
                Invoice Date: 2026-09-10
                Vendor: ABC Technologies Pvt Ltd
                Customer: NeoStats
                Currency: INR

                Item           Quantity    Unit Price    Amount
                Software       2           5000         10000

                Subtotal: 10000
                Tax: 1800
                Total: 11800
                """,
                extraction_method=ExtractionMethod.NATIVE,
            )
        ]
    )

    gemini_service = GeminiService()
    extraction_service = ExtractionService(gemini_service)

    result = extraction_service.extract(
        document_type="invoice",
        extraction_result=pages,
    )

    assert isinstance(result, ExtractionResult)
    assert result.document_type.value == "invoice"

    assert len(result.fields) > 0

    field_names = {
        field.name.lower()
        for field in result.fields
    }

    assert any(
        name in field_names
        for name in {
            "invoice_number",
            "invoice number",
        }
    )

    invoice_field = next(
        field
        for field in result.fields
        if field.name.lower() in {
            "invoice_number",
            "invoice number",
        }
    )

    assert invoice_field.value.text == "INV-001"
    assert invoice_field.page_number == 1
    assert invoice_field.evidence

    assert len(result.tables) > 0

    table = result.tables[0]

    assert table.name
    assert len(table.columns) > 0
    assert len(table.rows) > 0
    assert table.page_number == 1

