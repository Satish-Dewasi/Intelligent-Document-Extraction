from __future__ import annotations

from app.schemas.extraction import ExtractionResult
from app.schemas.financial_validation import (
    ValidationResult,
    ValidationStatus,
)


class InvoiceValidationService:
    """Contains deterministic validation rules specific to invoices."""

    def __init__(self, financial_service) -> None:
        self.financial_service = financial_service

    def validate_line_items(
        self,
        extraction: ExtractionResult,
    ) -> list[ValidationResult]:
        """
        Validate invoice line items using:

            quantity × unit_price ≈ line_total
        """

        results: list[ValidationResult] = []

        for table in extraction.tables:
            column_map = {
                column.strip().lower(): index
                for index, column in enumerate(table.columns)
            }

            quantity_index = column_map.get("quantity")
            unit_price_index = column_map.get("unit_price")
            line_total_index = column_map.get("line_total")

            if (
                quantity_index is None
                or unit_price_index is None
                or line_total_index is None
            ):
                continue

            for row_number, row in enumerate(table.rows, start=1):
                required_indexes = (
                    quantity_index,
                    unit_price_index,
                    line_total_index,
                )

                if any(index >= len(row) for index in required_indexes):
                    results.append(
                        ValidationResult(
                            name=f"invoice_line_{row_number}_total_check",
                            formula="quantity × unit_price",
                            status=ValidationStatus.NOT_APPLICABLE,
                        )
                    )
                    continue

                quantity = self.financial_service.normalize_number(
                    row[quantity_index]
                )

                unit_price = self.financial_service.normalize_number(
                    row[unit_price_index]
                )

                line_total = self.financial_service.normalize_number(
                    row[line_total_index]
                )

                calculated_total = (
                    quantity * unit_price
                    if quantity is not None
                    and unit_price is not None
                    else None
                )

                results.append(
                    self.financial_service.create_check(
                        name=f"invoice_line_{row_number}_total_check",
                        formula="quantity × unit_price",
                        operands={
                            "quantity": quantity,
                            "unit_price": unit_price,
                        },
                        calculated_value=calculated_total,
                        reported_value=line_total,
                    )
                )

        return results

    def validate_subtotal(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            sum(line totals) ≈ subtotal
        """

        subtotal_value = self.financial_service.get_field_value(
            extraction,
            "subtotal",
        )

        subtotal = self.financial_service.extract_numeric_value(
            subtotal_value
        )

        if subtotal is None:
            return ValidationResult(
                name="invoice_subtotal_check",
                formula="sum(line totals)",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        line_totals: list[float] = []

        for table in extraction.tables:
            column_map = {
                column.strip().lower(): index
                for index, column in enumerate(table.columns)
            }

            line_total_index = column_map.get("line_total")

            if line_total_index is None:
                continue

            for row in table.rows:
                if line_total_index >= len(row):
                    return ValidationResult(
                        name="invoice_subtotal_check",
                        formula="sum(line totals)",
                        status=ValidationStatus.NOT_APPLICABLE,
                    )

                line_total = self.financial_service.normalize_number(
                    row[line_total_index]
                )

                if line_total is None:
                    return ValidationResult(
                        name="invoice_subtotal_check",
                        formula="sum(line totals)",
                        status=ValidationStatus.NOT_APPLICABLE,
                    )

                line_totals.append(line_total)

        if not line_totals:
            return ValidationResult(
                name="invoice_subtotal_check",
                formula="sum(line totals)",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_subtotal = sum(line_totals)

        return self.financial_service.create_check(
            name="invoice_subtotal_check",
            formula="sum(line totals)",
            operands={
                f"line_total_{index + 1}": value
                for index, value in enumerate(line_totals)
            },
            calculated_value=calculated_subtotal,
            reported_value=subtotal,
        )

    def validate_total(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            subtotal + tax - discount ≈ total
        """

        subtotal_value = self.financial_service.get_field_value(
            extraction,
            "subtotal",
        )
        tax_value = self.financial_service.get_field_value(
            extraction,
            "tax",
        )
        discount_value = self.financial_service.get_field_value(
            extraction,
            "discount",
        )
        total_value = self.financial_service.get_field_value(
            extraction,
            "total",
        )

        subtotal = self.financial_service.extract_numeric_value(
            subtotal_value
        )
        tax = self.financial_service.extract_numeric_value(
            tax_value
        )
        discount = self.financial_service.extract_numeric_value(
            discount_value
        )
        total = self.financial_service.extract_numeric_value(
            total_value
        )

        if subtotal is None or total is None:
            return ValidationResult(
                name="invoice_total_check",
                formula="subtotal + tax - discount",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        tax = 0.0 if tax is None else tax
        discount = 0.0 if discount is None else discount

        calculated_total = subtotal + tax - discount

        return self.financial_service.create_check(
            name="invoice_total_check",
            formula="subtotal + tax - discount",
            operands={
                "subtotal": subtotal,
                "tax": tax,
                "discount": discount,
            },
            calculated_value=calculated_total,
            reported_value=total,
        )

    def validate_change(
        self,
        extraction: ExtractionResult,
    ) -> ValidationResult:
        """
        Validate:

            cash_paid - total ≈ change
        """

        cash_paid_value = self.financial_service.get_field_value(
            extraction,
            "cash_paid",
        )
        total_value = self.financial_service.get_field_value(
            extraction,
            "total",
        )
        change_value = self.financial_service.get_field_value(
            extraction,
            "change",
        )

        cash_paid = self.financial_service.extract_numeric_value(
            cash_paid_value
        )
        total = self.financial_service.extract_numeric_value(
            total_value
        )
        change = self.financial_service.extract_numeric_value(
            change_value
        )

        if (
            cash_paid is None
            or total is None
            or change is None
        ):
            return ValidationResult(
                name="invoice_change_check",
                formula="cash paid - total",
                status=ValidationStatus.NOT_APPLICABLE,
            )

        calculated_change = cash_paid - total

        return self.financial_service.create_check(
            name="invoice_change_check",
            formula="cash paid - total",
            operands={
                "cash_paid": cash_paid,
                "total": total,
            },
            calculated_value=calculated_change,
            reported_value=change,
        )