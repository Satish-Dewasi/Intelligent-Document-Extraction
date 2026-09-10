import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.document_validation_service import DocumentValidationService
from app.services.text_extraction_service import TextExtractionService

router = APIRouter(prefix="/documents", tags=["Documents"])

validation_service = DocumentValidationService()
text_extraction_service = TextExtractionService()


@router.post("/process")
async def process_document(file: UploadFile = File(...)):
    validation_result = await validation_service.validate(file)

    if not validation_result.valid:
        raise HTTPException(
            status_code=400,
            detail=validation_result.model_dump(mode="json"),
        )

    await file.seek(0)

    suffix = os.path.splitext(file.filename or "")[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await file.read())
        temp_file_path = temp_file.name

    try:
        extraction_result = text_extraction_service.extract(temp_file_path)

        return {
            "message": "Document passed validation and text extraction.",
            "validation": validation_result.model_dump(mode="json"),
            "extraction": extraction_result.model_dump(mode="json"),
        }

    finally:
        os.unlink(temp_file_path)