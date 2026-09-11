from __future__ import annotations

from app.schemas.extraction import ExtractionResult
from app.schemas.financial_validation import (
    ValidationResult,
    ValidationStatus,
)


class BalanceSheetValidationService:
    """Contains deterministic validation rules specific to balance sheets."""

    def __init__(self, financial_service) -> None:
        self.financial_service = financial_service

    def validate_balance_sheet_equation(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate the fundamental balance sheet equation:

            Assets ≈ Liabilities + Equity

        Missing required values result in NOT_APPLICABLE.
        """

        assets_value = self.financial_service.get_field_value(
            extraction,
            "assets",
        )

        liabilities_value = self.financial_service.get_field_value(
            extraction,
            "liabilities",
        )

        equity_value = self.financial_service.get_field_value(
            extraction,
            "equity",
        )

        assets = self.financial_service.extract_numeric_value(
            assets_value
        )

        liabilities = self.financial_service.extract_numeric_value(
            liabilities_value
        )

        equity = self.financial_service.extract_numeric_value(
            equity_value
        )

        if (
            assets is None
            or liabilities is None
            or equity is None
        ):
            return ValidationResult(
                name="balance_sheet_equation_check",
                formula="liabilities + equity",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_assets = liabilities + equity

        return self.financial_service.create_check(
            name="balance_sheet_equation_check",
            formula="liabilities + equity",
            operands={
                "liabilities": liabilities,
                "equity": equity,
            },
            calculated_value=calculated_assets,
            reported_value=assets,
        )

    def validate_total_assets(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate total assets against the sum of meaningful
        asset components when available.

        Formula:

            current assets + non-current assets ≈ total assets

        The check is only performed when all required components
        are available.
        """

        current_assets_value = self.financial_service.get_field_value(
            extraction,
            "current_assets",
        )

        non_current_assets_value = self.financial_service.get_field_value(
            extraction,
            "non_current_assets",
        )

        total_assets_value = self.financial_service.get_field_value(
            extraction,
            "assets",
        )

        current_assets = self.financial_service.extract_numeric_value(
            current_assets_value
        )

        non_current_assets = (
            self.financial_service.extract_numeric_value(
                non_current_assets_value
            )
        )

        total_assets = self.financial_service.extract_numeric_value(
            total_assets_value
        )

        if (
            current_assets is None
            or non_current_assets is None
            or total_assets is None
        ):
            return ValidationResult(
                name="balance_sheet_total_assets_check",
                formula="current assets + non-current assets",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_assets = current_assets + non_current_assets

        return self.financial_service.create_check(
            name="balance_sheet_total_assets_check",
            formula="current assets + non-current assets",
            operands={
                "current_assets": current_assets,
                "non_current_assets": non_current_assets,
            },
            calculated_value=calculated_assets,
            reported_value=total_assets,
        )

    def validate_total_liabilities(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate total liabilities against the sum of
        current and non-current liabilities.

        Formula:

            current liabilities + non-current liabilities
            ≈ total liabilities
        """

        current_liabilities_value = self.financial_service.get_field_value(
            extraction,
            "current_liabilities",
        )

        non_current_liabilities_value = (
            self.financial_service.get_field_value(
                extraction,
                "non_current_liabilities",
            )
        )

        total_liabilities_value = self.financial_service.get_field_value(
            extraction,
            "liabilities",
        )

        current_liabilities = (
            self.financial_service.extract_numeric_value(
                current_liabilities_value
            )
        )

        non_current_liabilities = (
            self.financial_service.extract_numeric_value(
                non_current_liabilities_value
            )
        )

        total_liabilities = (
            self.financial_service.extract_numeric_value(
                total_liabilities_value
            )
        )

        if (
            current_liabilities is None
            or non_current_liabilities is None
            or total_liabilities is None
        ):
            return ValidationResult(
                name="balance_sheet_total_liabilities_check",
                formula=(
                    "current liabilities + "
                    "non-current liabilities"
                ),
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_liabilities = (
            current_liabilities + non_current_liabilities
        )

        return self.financial_service.create_check(
            name="balance_sheet_total_liabilities_check",
            formula=(
                "current liabilities + "
                "non-current liabilities"
            ),
            operands={
                "current_liabilities": current_liabilities,
                "non_current_liabilities": non_current_liabilities,
            },
            calculated_value=calculated_liabilities,
            reported_value=total_liabilities,
        )

    def validate_balance_sheet(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """
        Run all applicable balance sheet validations.
        """

        return [
            self.validate_balance_sheet_equation(extraction),
            self.validate_total_assets(extraction),
            self.validate_total_liabilities(extraction),
        ]