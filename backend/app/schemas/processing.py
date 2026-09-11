from pydantic import BaseModel

from app.schemas.extraction import ExtractionResult
from app.schemas.financial_validation import FinancialValidationResult


class ProcessingResult(BaseModel):
    extraction: ExtractionResult
    financial_validation: FinancialValidationResult