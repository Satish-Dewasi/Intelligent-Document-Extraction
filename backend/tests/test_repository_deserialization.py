from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.extraction import (
    DocumentType,
    ExtractedField,
    ExtractedValue,
    ExtractionResult,
)
from app.schemas.financial_validation import (
    FinancialValidationResult,
    ValidationResult,
    ValidationStatus,
)
from app.schemas.processing import ProcessingResult


TEST_DOCUMENT_NAME = "repository-deserialization-test.pdf"


def create_processing_result() -> ProcessingResult:
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=100.0),
                page_number=1,
                evidence="Subtotal: 100.00",
                confidence=0.99,
            )
        ],
        tables=[],
    )

    validation = FinancialValidationResult(
        checks=[
            ValidationResult(
                name="subtotal_check",
                formula="subtotal",
                operands={"subtotal": 100.0},
                calculated_value=100.0,
                reported_value=100.0,
                variance=0.0,
                status=ValidationStatus.PASS,
            )
        ]
    )

    return ProcessingResult(
        extraction=extraction,
        financial_validation=validation,
    )


def test_result_json_round_trip():
    db = SessionLocal()

    try:
        db.query(Document).filter(
            Document.document_name == TEST_DOCUMENT_NAME
        ).delete(synchronize_session=False)
        db.commit()

        repository = DocumentRepository(db)

        original_result = create_processing_result()

        document = repository.create(
            document_name=TEST_DOCUMENT_NAME,
            document_type="invoice",
            processing_status="PASS",
            processed_at=datetime.now(timezone.utc),
            processing_time_ms=150.0,
            result=original_result,
        )

        restored_result = repository.get_result(document)

        assert isinstance(restored_result, ProcessingResult)

        assert (
            restored_result.extraction.document_type
            == DocumentType.INVOICE
        )

        assert (
            restored_result.extraction.fields[0].name
            == "subtotal"
        )

        assert (
            restored_result.extraction.fields[0].value.number
            == 100.0
        )

        assert (
            restored_result.financial_validation.checks[0].status
            == ValidationStatus.PASS
        )

        assert (
            restored_result.financial_validation.checks[0].reported_value
            == 100.0
        )

    finally:
        db.query(Document).filter(
            Document.document_name == TEST_DOCUMENT_NAME
        ).delete(synchronize_session=False)
        db.commit()
        db.close()