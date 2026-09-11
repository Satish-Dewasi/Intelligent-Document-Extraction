from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.document_repository import DocumentRepository
from app.schemas.extraction import DocumentType
from app.services.document_service import DocumentService
from app.services.document_validation_service import (
    DocumentValidationService,
)
from app.services.extraction_service import ExtractionService
from app.services.financial_validation_service import (
    FinancialValidationService,
)
from app.services.gemini_service import GeminiService
from app.services.text_extraction_service import TextExtractionService


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


validation_service = DocumentValidationService()
text_extraction_service = TextExtractionService()
gemini_service = GeminiService()
extraction_service = ExtractionService(gemini_service)
financial_validation_service = FinancialValidationService()


@router.post("/process")
async def process_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    db: Session = Depends(get_db),
):
    repository = DocumentRepository(db)

    document_service = DocumentService(
        validation_service=validation_service,
        text_extraction_service=text_extraction_service,
        extraction_service=extraction_service,
        financial_validation_service=financial_validation_service,
        repository=repository,
    )

    (
        validation_result,
        text_extraction_result,
        processing_result,
        processing_time_ms,
    ) = await document_service.process(
        file=file,
        document_type=document_type,
    )

    if not validation_result.valid:
        raise HTTPException(
            status_code=400,
            detail=validation_result.model_dump(
                mode="json"
            ),
        )

    return {
        "message": "Document processed successfully.",
        "validation": validation_result.model_dump(
            mode="json"
        ),
        "text_extraction": text_extraction_result.model_dump(
            mode="json"
        ),
        "structured_extraction": (
            processing_result.extraction.model_dump(
                mode="json"
            )
        ),
        "financial_validation": (
            processing_result.financial_validation.model_dump(
                mode="json"
            )
        ),
        "processing_time_ms": processing_time_ms,
    }


@router.get("/{document_name}/latest")
def get_latest_document(
    document_name: str,
    db: Session = Depends(get_db),
):
    repository = DocumentRepository(db)

    document = repository.get_latest_by_name(
        document_name
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document processing record not found.",
        )

    result = repository.get_result(document)

    return {
        "id": document.id,
        "document_name": document.document_name,
        "document_type": document.document_type,
        "processing_status": document.processing_status,
        "processed_at": document.processed_at,
        "processing_time_ms": document.processing_time_ms,
        "result": result.model_dump(mode="json"),
    }


@router.get("")
def list_documents(
    db: Session = Depends(get_db),
):
    repository = DocumentRepository(db)

    documents = repository.list_documents()

    return [
        {
            "id": document.id,
            "document_name": document.document_name,
            "document_type": document.document_type,
            "processing_status": document.processing_status,
            "processed_at": document.processed_at,
            "processing_time_ms": document.processing_time_ms,
            "result": repository.get_result(
                document
            ).model_dump(mode="json"),
        }
        for document in documents
    ]