import io

import fitz
import pytest
from fastapi import UploadFile
from PIL import Image

from app.schemas.document_validation import (
    ValidationErrorCode,
    ValidationStatus,
)
from app.services.document_validation_service import (
    DocumentValidationService,
)


@pytest.fixture
def validation_service():
    return DocumentValidationService()


def create_pdf(page_count: int) -> bytes:
    document = fitz.open()

    for _ in range(page_count):
        document.new_page()

    contents = document.tobytes()
    document.close()

    return contents


def create_image(format: str) -> bytes:
    image = Image.new("RGB", (100, 100), "white")

    buffer = io.BytesIO()
    image.save(buffer, format=format)

    return buffer.getvalue()


def create_upload_file(filename: str, contents: bytes) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(contents),
    )


@pytest.mark.asyncio
async def test_valid_pdf(validation_service):
    file = create_upload_file(
        "invoice.pdf",
        create_pdf(2),
    )

    result = await validation_service.validate(file)

    assert result.valid is True
    assert result.status == ValidationStatus.VALID
    assert result.file_type == "pdf"
    assert result.page_count == 2
    assert result.error_code is None


@pytest.mark.asyncio
async def test_valid_three_page_pdf(validation_service):
    file = create_upload_file(
        "invoice.pdf",
        create_pdf(3),
    )

    result = await validation_service.validate(file)

    assert result.valid is True
    assert result.page_count == 3


@pytest.mark.asyncio
async def test_pdf_exceeding_page_limit(validation_service):
    file = create_upload_file(
        "invoice.pdf",
        create_pdf(4),
    )

    result = await validation_service.validate(file)

    assert result.valid is False
    assert result.status == ValidationStatus.INVALID
    assert result.error_code == ValidationErrorCode.PAGE_LIMIT_EXCEEDED
    assert result.page_count == 4


@pytest.mark.asyncio
async def test_valid_jpg(validation_service):
    file = create_upload_file(
        "document.jpg",
        create_image("JPEG"),
    )

    result = await validation_service.validate(file)

    assert result.valid is True
    assert result.file_type == "jpg"
    assert result.error_code is None


@pytest.mark.asyncio
async def test_valid_png(validation_service):
    file = create_upload_file(
        "document.png",
        create_image("PNG"),
    )

    result = await validation_service.validate(file)

    assert result.valid is True
    assert result.file_type == "png"
    assert result.error_code is None


@pytest.mark.asyncio
async def test_empty_file(validation_service):
    file = create_upload_file(
        "invoice.pdf",
        b"",
    )

    result = await validation_service.validate(file)

    assert result.valid is False
    assert result.error_code == ValidationErrorCode.EMPTY_FILE


@pytest.mark.asyncio
async def test_unsupported_file_type(validation_service):
    file = create_upload_file(
        "document.txt",
        b"some text",
    )

    result = await validation_service.validate(file)

    assert result.valid is False
    assert result.error_code == ValidationErrorCode.UNSUPPORTED_FILE_TYPE


@pytest.mark.asyncio
async def test_corrupted_pdf(validation_service):
    file = create_upload_file(
        "invoice.pdf",
        b"This is not a valid PDF",
    )

    result = await validation_service.validate(file)

    assert result.valid is False
    assert result.error_code == ValidationErrorCode.CORRUPTED_FILE


@pytest.mark.asyncio
async def test_corrupted_image(validation_service):
    file = create_upload_file(
        "document.png",
        b"This is not a valid image",
    )

    result = await validation_service.validate(file)

    assert result.valid is False
    assert result.error_code == ValidationErrorCode.CORRUPTED_FILE