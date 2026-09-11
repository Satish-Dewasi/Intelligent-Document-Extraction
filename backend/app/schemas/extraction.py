from enum import Enum

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    INVOICE = "invoice"
    BALANCE_SHEET = "balance_sheet"
    PROFIT_AND_LOSS = "profit_and_loss"
    CASH_FLOW = "cash_flow"


class ExtractedValue(BaseModel):
    """Structured value for an extracted field."""

    text: str | None = None
    number: float | None = None
    boolean: bool | None = None


class ExtractedField(BaseModel):
    """A single extracted field with provenance."""

    name: str = Field(..., min_length=1)
    value: ExtractedValue
    page_number: int = Field(..., ge=1)
    evidence: str = Field(..., min_length=1)
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class ExtractedTable(BaseModel):
    """A flexible table extracted from the document."""

    name: str = Field(..., min_length=1)
    columns: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    page_number: int = Field(..., ge=1)


class ExtractionResult(BaseModel):
    """Complete structured document extraction."""

    document_type: DocumentType
    fields: list[ExtractedField] = Field(default_factory=list)
    tables: list[ExtractedTable] = Field(default_factory=list)