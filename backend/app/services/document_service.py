import os
import tempfile
import time
from datetime import datetime, timezone
from typing import Optional

from app.repositories.document_repository import DocumentRepository
from app.schemas.document_validation import DocumentValidationResult
from app.schemas.extraction import DocumentType, ExtractionResult
from app.schemas.financial_validation import FinancialValidationResult
from app.schemas.processing import ProcessingResult
from app.schemas.text_extraction import TextExtractionResult
from app.services.document_validation_service import (
    DocumentValidationService,
)
from app.services.extraction_service import ExtractionService
from app.services.financial_validation_service import (
    FinancialValidationService,
)
from app.services.text_extraction_service import TextExtractionService


class DocumentService:
    """Orchestrates document processing and persistence."""

    def __init__(
        self,
        validation_service: DocumentValidationService,
        text_extraction_service: TextExtractionService,
        extraction_service: ExtractionService,
        financial_validation_service: FinancialValidationService,
        repository: DocumentRepository,
    ) -> None:
        self.validation_service = validation_service
        self.text_extraction_service = text_extraction_service
        self.extraction_service = extraction_service
        self.financial_validation_service = (
            financial_validation_service
        )
        self.repository = repository

    async def process(
        self,
        file,
        document_type: DocumentType,
    ) -> tuple[
        DocumentValidationResult,
        Optional[TextExtractionResult],
        Optional[ProcessingResult],
        float,
    ]:
        start_time = time.perf_counter()

        # Phase 2: document validation
        validation_result = await self.validation_service.validate(file)

        if not validation_result.valid:
            return validation_result, None, None, 0.0

        await file.seek(0)

        suffix = os.path.splitext(file.filename or "")[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(await file.read())
            temp_file_path = temp_file.name

        try:
            # Phase 3: text extraction / OCR
            text_extraction_result = (
                self.text_extraction_service.extract(
                    temp_file_path
                )
            )

            # Phase 4: Gemini structured extraction
            extraction_result: ExtractionResult = (
                self.extraction_service.extract(
                    document_type=document_type.value,
                    extraction_result=text_extraction_result,
                )
            )

            # Phase 5: deterministic financial validation
            financial_validation_result: FinancialValidationResult = (
                self.financial_validation_service.validate(
                    extraction_result
                )
            )

            processing_result = ProcessingResult(
                extraction=extraction_result,
                financial_validation=financial_validation_result,
            )

            processing_time_ms = (
                time.perf_counter() - start_time
            ) * 1000

            # Phase 6: persistence
            self.repository.create(
                document_name=file.filename or "unknown",
                document_type=document_type.value,
                processing_status=(
                    financial_validation_result
                    .overall_status
                    .value
                ),
                processed_at=datetime.now(timezone.utc),
                processing_time_ms=processing_time_ms,
                result=processing_result,
            )

            return (
                validation_result,
                text_extraction_result,
                processing_result,
                processing_time_ms,
            )

        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)