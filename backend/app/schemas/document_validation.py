from enum import Enum

from pydantic import BaseModel


class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"


class ValidationErrorCode(str, Enum):
    UNSUPPORTED_FILE_TYPE = "UNSUPPORTED_FILE_TYPE"
    EMPTY_FILE = "EMPTY_FILE"
    CORRUPTED_FILE = "CORRUPTED_FILE"
    UNREADABLE_FILE = "UNREADABLE_FILE"
    PAGE_LIMIT_EXCEEDED = "PAGE_LIMIT_EXCEEDED"


class DocumentValidationResult(BaseModel):
    valid: bool
    status: ValidationStatus
    file_type: str | None = None
    page_count: int | None = None
    error_code: ValidationErrorCode | None = None
    message: str | None = None