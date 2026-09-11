from unittest.mock import AsyncMock, Mock

import pytest

from app.schemas.document_validation import (
    DocumentValidationResult,
    ValidationStatus,
)
from app.schemas.extraction import (
    DocumentType,
    ExtractionResult,
)
from app.schemas.financial_validation import (
    FinancialValidationResult,
)
from app.schemas.processing import ProcessingResult
from app.schemas.text_extraction import (
    TextExtractionResult,
)
from app.services.document_service import DocumentService


class FakeFile:
    filename = "test-invoice.pdf"

    def __init__(self):
        self.seek = AsyncMock()
        self.read = AsyncMock(return_value=b"fake pdf")


@pytest.mark.asyncio
async def test_document_service_processes_and_persists():
    validation_service = Mock()

    validation_service.validate = AsyncMock(
        return_value=DocumentValidationResult(
            valid=True,
            status=ValidationStatus.VALID,
            file_type="pdf",
            page_count=1,
        )
    )

    text_extraction_service = Mock()

    text_extraction_result = TextExtractionResult(
        pages=[]
    )

    text_extraction_service.extract.return_value = (
        text_extraction_result
    )

    extraction_service = Mock()

    extraction_result = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[],
        tables=[],
    )

    extraction_service.extract.return_value = extraction_result

    financial_validation_service = Mock()

    financial_validation_result = FinancialValidationResult(
        checks=[]
    )

    financial_validation_service.validate.return_value = (
        financial_validation_result
    )

    repository = Mock()

    service = DocumentService(
        validation_service=validation_service,
        text_extraction_service=text_extraction_service,
        extraction_service=extraction_service,
        financial_validation_service=(
            financial_validation_service
        ),
        repository=repository,
    )

    file = FakeFile()

    (
        validation,
        text_result,
        result,
        processing_time,
    ) = await service.process(
        file=file,
        document_type=DocumentType.INVOICE,
    )

    assert validation.valid is True
    assert text_result is text_extraction_result
    assert isinstance(result, ProcessingResult)
    assert result.extraction.document_type == DocumentType.INVOICE
    assert processing_time >= 0

    validation_service.validate.assert_awaited_once_with(file)

    text_extraction_service.extract.assert_called_once()

    extraction_service.extract.assert_called_once_with(
        document_type="invoice",
        extraction_result=text_extraction_result,
    )

    financial_validation_service.validate.assert_called_once_with(
        extraction_result
    )

    repository.create.assert_called_once()

    saved_kwargs = repository.create.call_args.kwargs

    assert saved_kwargs["document_name"] == "test-invoice.pdf"
    assert saved_kwargs["document_type"] == "invoice"

    # Empty checks correctly produce NOT_APPLICABLE.
    assert (
        saved_kwargs["processing_status"]
        == "NOT_APPLICABLE"
    )

    assert isinstance(
        saved_kwargs["result"],
        ProcessingResult,
    )


@pytest.mark.asyncio
async def test_document_service_does_not_process_invalid_file():
    validation_service = Mock()

    validation_service.validate = AsyncMock(
        return_value=DocumentValidationResult(
            valid=False,
            status=ValidationStatus.INVALID,
            file_type="exe",
        )
    )

    text_extraction_service = Mock()
    extraction_service = Mock()
    financial_validation_service = Mock()
    repository = Mock()

    service = DocumentService(
        validation_service=validation_service,
        text_extraction_service=text_extraction_service,
        extraction_service=extraction_service,
        financial_validation_service=(
            financial_validation_service
        ),
        repository=repository,
    )

    file = FakeFile()

    (
        validation,
        text_result,
        result,
        processing_time,
    ) = await service.process(
        file=file,
        document_type=DocumentType.INVOICE,
    )

    assert validation.valid is False
    assert text_result is None
    assert result is None
    assert processing_time == 0.0

    text_extraction_service.extract.assert_not_called()
    extraction_service.extract.assert_not_called()
    financial_validation_service.validate.assert_not_called()
    repository.create.assert_not_called()