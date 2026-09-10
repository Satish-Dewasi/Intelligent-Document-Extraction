import io
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
import fitz

from app.schemas.document_validation import (
    DocumentValidationResult,
    ValidationErrorCode,
    ValidationStatus,
)


class DocumentValidationService:
    MAX_PDF_PAGES = 3
    SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

    async def validate(self, file: UploadFile) -> DocumentValidationResult:
        filename = file.filename or ""
        extension = Path(filename).suffix.lower()

        # 1. Check supported format
        if extension not in self.SUPPORTED_EXTENSIONS:
            return self._invalid(
                ValidationErrorCode.UNSUPPORTED_FILE_TYPE,
                "Only PDF, JPG, JPEG, and PNG files are supported.",
            )

        # Read file contents once
        contents = await file.read()

        # 2. Check empty file
        if not contents:
            return self._invalid(
                ValidationErrorCode.EMPTY_FILE,
                "The uploaded file is empty.",
            )

        # 3 + 4 + 5. Validate according to file type
        if extension == ".pdf":
            return self._validate_pdf(contents)

        return self._validate_image(contents, extension)

    def _validate_pdf(self, contents: bytes) -> DocumentValidationResult:
        try:
            document = fitz.open(stream=contents, filetype="pdf")

            page_count = len(document)

            if page_count == 0:
                document.close()
                return self._invalid(
                    ValidationErrorCode.UNREADABLE_FILE,
                    "The PDF contains no readable pages.",
                    file_type="pdf",
                )

            if page_count > self.MAX_PDF_PAGES:
                document.close()
                return self._invalid(
                    ValidationErrorCode.PAGE_LIMIT_EXCEEDED,
                    "PDF must contain no more than 3 pages.",
                    file_type="pdf",
                    page_count=page_count,
                )

            # Force access to every page to catch some malformed PDFs.
            for page in document:
                page.get_text()

            document.close()

            return DocumentValidationResult(
                valid=True,
                status=ValidationStatus.VALID,
                file_type="pdf",
                page_count=page_count,
            )

        except Exception:
            return self._invalid(
                ValidationErrorCode.CORRUPTED_FILE,
                "The PDF is corrupted or could not be read.",
                file_type="pdf",
            )

    def _validate_image(
        self,
        contents: bytes,
        extension: str,
    ) -> DocumentValidationResult:
        file_type = extension.lstrip(".")

        try:
            image = Image.open(io.BytesIO(contents))

            # Verify image integrity.
            image.verify()

            return DocumentValidationResult(
                valid=True,
                status=ValidationStatus.VALID,
                file_type=file_type,
            )

        except UnidentifiedImageError:
            return self._invalid(
                ValidationErrorCode.CORRUPTED_FILE,
                "The image is corrupted or is not a valid image file.",
                file_type=file_type,
            )

        except Exception:
            return self._invalid(
                ValidationErrorCode.UNREADABLE_FILE,
                "The image could not be read.",
                file_type=file_type,
            )

    @staticmethod
    def _invalid(
        error_code: ValidationErrorCode,
        message: str,
        file_type: str | None = None,
        page_count: int | None = None,
    ) -> DocumentValidationResult:
        return DocumentValidationResult(
            valid=False,
            status=ValidationStatus.INVALID,
            file_type=file_type,
            page_count=page_count,
            error_code=error_code,
            message=message,
        )