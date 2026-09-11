from __future__ import annotations

from app.schemas.extraction import ExtractionResult
from app.schemas.financial_validation import (
    ValidationResult,
    ValidationStatus,
)


class CashFlowValidationService:
    """Contains deterministic validation rules specific to cash flow statements."""

    def __init__(self, financial_service) -> None:
        self.financial_service = financial_service

    def validate_net_change_in_cash(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            Operating Cash Flow
            + Investing Cash Flow
            + Financing Cash Flow
            + FX Adjustment
            ≈ Net Change in Cash

        FX adjustment is optional. When it is absent, it contributes
        zero because there is no reported FX component.
        """

        operating_value = self.financial_service.get_field_value(
            extraction,
            "operating_cash_flow",
        )

        investing_value = self.financial_service.get_field_value(
            extraction,
            "investing_cash_flow",
        )

        financing_value = self.financial_service.get_field_value(
            extraction,
            "financing_cash_flow",
        )

        fx_value = self.financial_service.get_field_value(
            extraction,
            "fx_adjustment",
        )

        net_change_value = self.financial_service.get_field_value(
            extraction,
            "net_change_in_cash",
        )

        operating_cash_flow = (
            self.financial_service.extract_numeric_value(
                operating_value
            )
        )

        investing_cash_flow = (
            self.financial_service.extract_numeric_value(
                investing_value
            )
        )

        financing_cash_flow = (
            self.financial_service.extract_numeric_value(
                financing_value
            )
        )

        fx_adjustment = (
            self.financial_service.extract_numeric_value(
                fx_value
            )
        )

        net_change_in_cash = (
            self.financial_service.extract_numeric_value(
                net_change_value
            )
        )

        if (
            operating_cash_flow is None
            or investing_cash_flow is None
            or financing_cash_flow is None
            or net_change_in_cash is None
        ):
            return ValidationResult(
                name="cash_flow_net_change_check",
                formula=(
                    "operating cash flow + "
                    "investing cash flow + "
                    "financing cash flow + "
                    "fx adjustment"
                ),
                status=ValidationStatus.NOT_APPLICABLE,
            )

        fx_adjustment = (
            0.0 if fx_adjustment is None else fx_adjustment
        )

        calculated_net_change = (
            operating_cash_flow
            + investing_cash_flow
            + financing_cash_flow
            + fx_adjustment
        )

        return self.financial_service.create_check(
            name="cash_flow_net_change_check",
            formula=(
                "operating cash flow + "
                "investing cash flow + "
                "financing cash flow + "
                "fx adjustment"
            ),
            operands={
                "operating_cash_flow": operating_cash_flow,
                "investing_cash_flow": investing_cash_flow,
                "financing_cash_flow": financing_cash_flow,
                "fx_adjustment": fx_adjustment,
            },
            calculated_value=calculated_net_change,
            reported_value=net_change_in_cash,
        )

    def validate_closing_cash(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            Opening Cash + Net Change in Cash
            ≈ Closing Cash
        """

        opening_value = self.financial_service.get_field_value(
            extraction,
            "opening_cash",
        )

        net_change_value = self.financial_service.get_field_value(
            extraction,
            "net_change_in_cash",
        )

        closing_value = self.financial_service.get_field_value(
            extraction,
            "closing_cash",
        )

        opening_cash = self.financial_service.extract_numeric_value(
            opening_value
        )

        net_change_in_cash = (
            self.financial_service.extract_numeric_value(
                net_change_value
            )
        )

        closing_cash = self.financial_service.extract_numeric_value(
            closing_value
        )

        if (
            opening_cash is None
            or net_change_in_cash is None
            or closing_cash is None
        ):
            return ValidationResult(
                name="cash_flow_closing_cash_check",
                formula="opening cash + net change in cash",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_closing_cash = (
            opening_cash + net_change_in_cash
        )

        return self.financial_service.create_check(
            name="cash_flow_closing_cash_check",
            formula="opening cash + net change in cash",
            operands={
                "opening_cash": opening_cash,
                "net_change_in_cash": net_change_in_cash,
            },
            calculated_value=calculated_closing_cash,
            reported_value=closing_cash,
        )

    def validate_cash_flow(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """Run all applicable cash flow validations."""

        return [
            self.validate_net_change_in_cash(extraction),
            self.validate_closing_cash(extraction),
        ]