from app.schemas.processing import ProcessingResult
from app.schemas.extraction import (
    DocumentType,
    ExtractionResult,
)
from app.schemas.financial_validation import (
    FinancialValidationResult,
)


def test_processing_result_contains_extraction_and_validation():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[],
        tables=[],
    )

    financial_validation = FinancialValidationResult(
        checks=[],
    )

    result = ProcessingResult(
        extraction=extraction,
        financial_validation=financial_validation,
    )

    assert result.extraction == extraction
    assert result.financial_validation == financial_validation