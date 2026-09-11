from __future__ import annotations

import re

from app.schemas.extraction import (
    DocumentType,
    ExtractedValue,
    ExtractionResult,
)

from app.schemas.financial_validation import (
    FinancialValidationResult,
    ValidationResult,
    ValidationStatus,
)

from app.schemas.extraction import ExtractedValue, ExtractionResult
from app.schemas.financial_validation import (
    ValidationResult,
)

from app.services.financial_validations.invoice_validation import (
    InvoiceValidationService,
)
from app.services.financial_validations.balance_sheet_validation import (
    BalanceSheetValidationService,
)
from app.services.financial_validations.profit_loss_validation import (
    ProfitLossValidationService,
)
from app.services.financial_validations.cash_flow_validation import (
    CashFlowValidationService,
)

class FinancialValidationService:
    """Performs deterministic financial validation on extracted data."""

    DEFAULT_TOLERANCE = 0.01

    def __init__(self, tolerance: float = DEFAULT_TOLERANCE) -> None:
        if tolerance < 0:
            raise ValueError("Tolerance cannot be negative.")

        self.tolerance = tolerance

        # Document-specific validators
        self.invoice_validator = InvoiceValidationService(self)
        self.balance_sheet_validator = BalanceSheetValidationService(self)
        self.profit_loss_validator = ProfitLossValidationService(self)
        self.cash_flow_validator = CashFlowValidationService(self)

    @staticmethod
    def normalize_number(
        value: str | int | float | None,
    ) -> float | None:
        """
        Convert a financial value into a numeric representation.

        Parentheses represent negative numbers:
            (1,250) -> -1250

        Currency symbols and thousands separators are ignored.
        """

        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        value = value.strip()

        if not value:
            return None

        is_negative = value.startswith("(") and value.endswith(")")

        cleaned = value.strip("()")
        cleaned = re.sub(r"[,$€£₹]", "", cleaned)
        cleaned = cleaned.replace(",", "")
        cleaned = cleaned.strip()

        try:
            number = float(cleaned)
        except ValueError:
            return None

        return -number if is_negative else number

    @staticmethod
    def extract_numeric_value(
        value: ExtractedValue | None,
    ) -> float | None:
        """
        Extract the numeric representation from an ExtractedValue.

        Priority:
        number -> text that can be parsed as a number
        """

        if value is None:
            return None

        if value.number is not None:
            return float(value.number)

        if value.text is not None:
            return FinancialValidationService.normalize_number(
                value.text
            )

        return None

    @staticmethod
    def values_match(
        calculated_value: float,
        reported_value: float,
        tolerance: float,
    ) -> bool:
        """Return True when two values are within the configured tolerance."""

        variance = abs(calculated_value - reported_value)

        return variance <= tolerance + 1e-9

    def create_check(
        self,
        *,
        name: str,
        formula: str,
        operands: dict[str, float | None],
        calculated_value: float | None,
        reported_value: float | None,
    ) -> ValidationResult:
        """
        Create a ValidationResult from a deterministic calculation.

        Missing required values result in NOT_APPLICABLE.
        """

        if (
            any(value is None for value in operands.values())
            or calculated_value is None
            or reported_value is None
        ):
            from app.schemas.financial_validation import ValidationStatus

            return ValidationResult(
                name=name,
                formula=formula,
                status=ValidationStatus.NOT_APPLICABLE,
            )

        variance = abs(calculated_value - reported_value)

        from app.schemas.financial_validation import ValidationStatus

        status = (
            ValidationStatus.PASS
            if self.values_match(
                calculated_value,
                reported_value,
                self.tolerance,
            )
            else ValidationStatus.FAIL
        )

        return ValidationResult(
            name=name,
            formula=formula,
            operands={
                key: float(value)
                for key, value in operands.items()
                if value is not None
            },
            calculated_value=calculated_value,
            reported_value=reported_value,
            variance=variance,
            status=status,
        )

    @staticmethod
    def get_field_value(
        extraction: ExtractionResult,
        field_name: str,
    ) -> ExtractedValue | None:
        """
        Find an extracted field by name.

        Returns None when the field does not exist.
        """

        target_name = field_name.strip().lower()

        for field in extraction.fields:
            if field.name.strip().lower() == target_name:
                return field.value

        return None

    # ------------------------------------------------------------------
    # Invoice validation delegation
    # ------------------------------------------------------------------

    def validate_invoice_line_items(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """Delegate invoice line-item validation."""

        return self.invoice_validator.validate_line_items(
            extraction
        )

    def validate_invoice_subtotal(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """Delegate invoice subtotal validation."""

        return self.invoice_validator.validate_subtotal(
            extraction
        )

    def validate_invoice_total(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """Delegate invoice total validation."""

        return self.invoice_validator.validate_total(
            extraction
        )

    def validate_invoice_change(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """Delegate invoice cash/change validation."""

        return self.invoice_validator.validate_change(
            extraction
        )



        # ------------------------------------------------------------------
    # Balance Sheet validation delegation
    # ------------------------------------------------------------------

    def validate_balance_sheet(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """Delegate balance sheet validation."""

        return self.balance_sheet_validator.validate_balance_sheet(
            extraction
        )


        # ------------------------------------------------------------------
    # Profit & Loss validation delegation
    # ------------------------------------------------------------------

    def validate_profit_loss(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """Delegate Profit & Loss validation."""

        return self.profit_loss_validator.validate_profit_loss(
            extraction
        )



    # ------------------------------------------------------------------
    # Cash Flow validation delegation
    # ------------------------------------------------------------------

    def validate_cash_flow(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """Delegate cash flow validation."""

        return self.cash_flow_validator.validate_cash_flow(
            extraction
        )



        # ------------------------------------------------------------------
    # Financial validation orchestration
    # ------------------------------------------------------------------

    def validate(
        self,
        extraction: ExtractionResult,
    ) -> FinancialValidationResult:
        """
        Validate extracted financial data based on document type.

        The document-specific validator performs the actual
        deterministic financial checks.

        Returns:
            FinancialValidationResult containing all checks
            and the derived overall status.
        """

        if extraction.document_type == DocumentType.INVOICE:
            checks = []

            checks.extend(
                self.invoice_validator.validate_line_items(
                    extraction
                )
            )

            checks.append(
                self.invoice_validator.validate_subtotal(
                    extraction
                )
            )

            checks.append(
                self.invoice_validator.validate_total(
                    extraction
                )
            )

            checks.append(
                self.invoice_validator.validate_change(
                    extraction
                )
            )

        elif extraction.document_type == DocumentType.BALANCE_SHEET:
            checks = self.balance_sheet_validator.validate_balance_sheet(
                extraction
            )

        elif extraction.document_type == DocumentType.PROFIT_AND_LOSS:
            checks = self.profit_loss_validator.validate_profit_loss(
                extraction
            )

        elif extraction.document_type == DocumentType.CASH_FLOW:
            checks = self.cash_flow_validator.validate_cash_flow(
                extraction
            )

        else:
            checks = []

        return FinancialValidationResult(
            checks=checks,
        )