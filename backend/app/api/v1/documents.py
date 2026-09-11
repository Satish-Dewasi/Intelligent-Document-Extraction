import os
import tempfile

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.schemas.extraction import DocumentType
from app.services.document_validation_service import DocumentValidationService
from app.services.extraction_service import ExtractionService
from app.services.gemini_service import GeminiService
from app.services.text_extraction_service import TextExtractionService

router = APIRouter(prefix="/documents", tags=["Documents"])

validation_service = DocumentValidationService()
text_extraction_service = TextExtractionService()
gemini_service = GeminiService()
extraction_service = ExtractionService(gemini_service)


@router.post("/process")
async def process_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
):
    validation_result = await validation_service.validate(file)

    if not validation_result.valid:
        raise HTTPException(
            status_code=400,
            detail=validation_result.model_dump(mode="json"),
        )

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
        extraction_result = text_extraction_service.extract(
            temp_file_path
        )

        # Phase 4: structured AI extraction
        structured_result = extraction_service.extract(
            document_type=document_type.value,
            extraction_result=extraction_result,
        )

        return {
            "message": "Document processed successfully.",
            "validation": validation_result.model_dump(
                mode="json"
            ),
            "text_extraction": extraction_result.model_dump(
                mode="json"
            ),
            "structured_extraction": structured_result.model_dump(
                mode="json"
            ),
        }

    finally:
        os.unlink(temp_file_path)