from enum import Enum

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Status of a financial validation check."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ValidationResult(BaseModel):
    """Result of a single deterministic financial validation."""

    name: str
    formula: str
    operands: dict[str, float] = Field(default_factory=dict)

    calculated_value: float | None = None
    reported_value: float | None = None
    variance: float | None = None

    status: ValidationStatus


class FinancialValidationResult(BaseModel):
    """Collection of financial validation checks for a document."""

    checks: list[ValidationResult] = Field(default_factory=list)

    @property
    def overall_status(self) -> ValidationStatus:
        """Return the overall status of all validation checks."""

        if any(check.status == ValidationStatus.FAIL for check in self.checks):
            return ValidationStatus.FAIL

        applicable_checks = [
            check
            for check in self.checks
            if check.status != ValidationStatus.NOT_APPLICABLE
        ]

        if not applicable_checks:
            return ValidationStatus.NOT_APPLICABLE

        return ValidationStatus.PASS