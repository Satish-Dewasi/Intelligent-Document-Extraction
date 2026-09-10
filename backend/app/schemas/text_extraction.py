from enum import Enum

from pydantic import BaseModel, Field


class ExtractionMethod(str, Enum):
    """Method used to extract text from a document page."""

    NATIVE = "native"
    OCR = "ocr"


class PageText(BaseModel):
    """Text extracted from a single document page."""

    page_number: int = Field(..., ge=1)
    text: str
    extraction_method: ExtractionMethod


class TextExtractionResult(BaseModel):
    """Page-aware text extraction result for a document."""

    pages: list[PageText]