from __future__ import annotations

from app.schemas.extraction import ExtractionResult
from app.schemas.financial_validation import (
    ValidationResult,
    ValidationStatus,
)


class ProfitLossValidationService:
    """Contains deterministic validation rules specific to P&L statements."""

    def __init__(self, financial_service) -> None:
        self.financial_service = financial_service

    def validate_gross_profit(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            Revenue - COGS ≈ Gross Profit
        """

        revenue_value = self.financial_service.get_field_value(
            extraction,
            "revenue",
        )
        cogs_value = self.financial_service.get_field_value(
            extraction,
            "cogs",
        )
        gross_profit_value = self.financial_service.get_field_value(
            extraction,
            "gross_profit",
        )

        revenue = self.financial_service.extract_numeric_value(
            revenue_value
        )
        cogs = self.financial_service.extract_numeric_value(
            cogs_value
        )
        gross_profit = self.financial_service.extract_numeric_value(
            gross_profit_value
        )

        if (
            revenue is None
            or cogs is None
            or gross_profit is None
        ):
            return ValidationResult(
                name="profit_loss_gross_profit_check",
                formula="revenue - cogs",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_gross_profit = revenue - cogs

        return self.financial_service.create_check(
            name="profit_loss_gross_profit_check",
            formula="revenue - cogs",
            operands={
                "revenue": revenue,
                "cogs": cogs,
            },
            calculated_value=calculated_gross_profit,
            reported_value=gross_profit,
        )

    def validate_operating_income(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            Gross Profit - Operating Expenses
            ≈ Operating Income
        """

        gross_profit_value = self.financial_service.get_field_value(
            extraction,
            "gross_profit",
        )
        operating_expenses_value = (
            self.financial_service.get_field_value(
                extraction,
                "operating_expenses",
            )
        )
        operating_income_value = (
            self.financial_service.get_field_value(
                extraction,
                "operating_income",
            )
        )

        gross_profit = self.financial_service.extract_numeric_value(
            gross_profit_value
        )
        operating_expenses = (
            self.financial_service.extract_numeric_value(
                operating_expenses_value
            )
        )
        operating_income = (
            self.financial_service.extract_numeric_value(
                operating_income_value
            )
        )

        if (
            gross_profit is None
            or operating_expenses is None
            or operating_income is None
        ):
            return ValidationResult(
                name="profit_loss_operating_income_check",
                formula="gross profit - operating expenses",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_operating_income = (
            gross_profit - operating_expenses
        )

        return self.financial_service.create_check(
            name="profit_loss_operating_income_check",
            formula="gross profit - operating expenses",
            operands={
                "gross_profit": gross_profit,
                "operating_expenses": operating_expenses,
            },
            calculated_value=calculated_operating_income,
            reported_value=operating_income,
        )

    def validate_net_income(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            Operating Income - Tax ≈ Net Income

        Interest/other income and expenses are included only
        when explicitly available.
        """

        operating_income_value = (
            self.financial_service.get_field_value(
                extraction,
                "operating_income",
            )
        )
        tax_value = self.financial_service.get_field_value(
            extraction,
            "tax",
        )
        net_income_value = self.financial_service.get_field_value(
            extraction,
            "net_income",
        )

        operating_income = (
            self.financial_service.extract_numeric_value(
                operating_income_value
            )
        )
        tax = self.financial_service.extract_numeric_value(
            tax_value
        )
        net_income = self.financial_service.extract_numeric_value(
            net_income_value
        )

        if (
            operating_income is None
            or tax is None
            or net_income is None
        ):
            return ValidationResult(
                name="profit_loss_net_income_check",
                formula="operating income - tax",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_net_income = operating_income - tax

        return self.financial_service.create_check(
            name="profit_loss_net_income_check",
            formula="operating income - tax",
            operands={
                "operating_income": operating_income,
                "tax": tax,
            },
            calculated_value=calculated_net_income,
            reported_value=net_income,
        )

    def validate_profit_loss(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """
        Run all applicable P&L validations.
        """

        return [
            self.validate_gross_profit(extraction),
            self.validate_operating_income(extraction),
            self.validate_net_income(extraction),
        ]