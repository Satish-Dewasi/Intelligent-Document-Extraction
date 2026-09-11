from app.schemas.financial_validation import (
    FinancialValidationResult,
    ValidationResult,
    ValidationStatus,
)

from app.schemas.extraction import (
    DocumentType,
    ExtractedField,
    ExtractionResult,
)


def test_validation_result_pass():
    result = ValidationResult(
        name="invoice_total_check",
        formula="subtotal + tax_amount - discount",
        operands={
            "subtotal": 12500,
            "tax_amount": 625,
            "discount": 0,
        },
        calculated_value=13125,
        reported_value=13125,
        variance=0,
        status=ValidationStatus.PASS,
    )

    assert result.status == ValidationStatus.PASS
    assert result.calculated_value == 13125
    assert result.reported_value == 13125
    assert result.variance == 0


def test_validation_result_not_applicable():
    result = ValidationResult(
        name="invoice_total_check",
        formula="subtotal + tax_amount - discount",
        status=ValidationStatus.NOT_APPLICABLE,
    )

    assert result.status == ValidationStatus.NOT_APPLICABLE
    assert result.calculated_value is None
    assert result.reported_value is None
    assert result.variance is None


def test_overall_status_fails_when_any_check_fails():
    validation = FinancialValidationResult(
        checks=[
            ValidationResult(
                name="check_1",
                formula="a + b",
                operands={"a": 10, "b": 20},
                calculated_value=30,
                reported_value=30,
                variance=0,
                status=ValidationStatus.PASS,
            ),
            ValidationResult(
                name="check_2",
                formula="x + y",
                operands={"x": 10, "y": 20},
                calculated_value=30,
                reported_value=40,
                variance=10,
                status=ValidationStatus.FAIL,
            ),
        ]
    )

    assert validation.overall_status == ValidationStatus.FAIL


def test_overall_status_is_pass_when_all_applicable_checks_pass():
    validation = FinancialValidationResult(
        checks=[
            ValidationResult(
                name="check_1",
                formula="a + b",
                operands={"a": 10, "b": 20},
                calculated_value=30,
                reported_value=30,
                variance=0,
                status=ValidationStatus.PASS,
            ),
            ValidationResult(
                name="check_2",
                formula="x - y",
                operands={"x": 50, "y": 20},
                calculated_value=30,
                reported_value=30,
                variance=0,
                status=ValidationStatus.PASS,
            ),
        ]
    )

    assert validation.overall_status == ValidationStatus.PASS


def test_overall_status_is_not_applicable_when_no_checks_are_applicable():
    validation = FinancialValidationResult(
        checks=[
            ValidationResult(
                name="check_1",
                formula="a + b",
                status=ValidationStatus.NOT_APPLICABLE,
            ),
            ValidationResult(
                name="check_2",
                formula="x - y",
                status=ValidationStatus.NOT_APPLICABLE,
            ),
        ]
    )

    assert validation.overall_status == ValidationStatus.NOT_APPLICABLE



import pytest

from app.schemas.extraction import ExtractedValue
from app.schemas.financial_validation import ValidationStatus
from app.services.financial_validation_service import FinancialValidationService


def test_normalize_positive_number():
    assert FinancialValidationService.normalize_number("1,250") == 1250


def test_normalize_currency_number():
    assert FinancialValidationService.normalize_number("$1,250.50") == 1250.50


def test_normalize_negative_parentheses():
    assert FinancialValidationService.normalize_number("(1,250)") == -1250


def test_normalize_negative_currency_parentheses():
    assert FinancialValidationService.normalize_number("($1,250.50)") == -1250.50


def test_normalize_empty_value():
    assert FinancialValidationService.normalize_number("") is None


def test_normalize_invalid_value():
    assert FinancialValidationService.normalize_number("not-a-number") is None


def test_extract_numeric_value_from_number():
    value = ExtractedValue(number=1250)

    assert FinancialValidationService.extract_numeric_value(value) == 1250


def test_extract_numeric_value_from_text():
    value = ExtractedValue(text="(1,250)")

    assert FinancialValidationService.extract_numeric_value(value) == -1250


def test_extract_numeric_value_missing():
    value = ExtractedValue()

    assert FinancialValidationService.extract_numeric_value(value) is None


def test_values_match_within_tolerance():
    assert FinancialValidationService.values_match(
        calculated_value=100.00,
        reported_value=100.01,
        tolerance=0.01,
    )


def test_values_do_not_match_outside_tolerance():
    assert not FinancialValidationService.values_match(
        calculated_value=100.00,
        reported_value=100.02,
        tolerance=0.01,
    )


def test_create_check_pass():
    service = FinancialValidationService(tolerance=0.01)

    result = service.create_check(
        name="invoice_total_check",
        formula="subtotal + tax_amount - discount",
        operands={
            "subtotal": 1000,
            "tax_amount": 100,
            "discount": 50,
        },
        calculated_value=1050,
        reported_value=1050,
    )

    assert result.status == ValidationStatus.PASS
    assert result.calculated_value == 1050
    assert result.reported_value == 1050
    assert result.variance == 0


def test_create_check_fail():
    service = FinancialValidationService(tolerance=0.01)

    result = service.create_check(
        name="invoice_total_check",
        formula="subtotal + tax_amount - discount",
        operands={
            "subtotal": 1000,
            "tax_amount": 100,
            "discount": 50,
        },
        calculated_value=1050,
        reported_value=1100,
    )

    assert result.status == ValidationStatus.FAIL
    assert result.variance == 50


def test_create_check_not_applicable_when_operand_missing():
    service = FinancialValidationService(tolerance=0.01)

    result = service.create_check(
        name="invoice_total_check",
        formula="subtotal + tax_amount - discount",
        operands={
            "subtotal": 1000,
            "tax_amount": None,
            "discount": 50,
        },
        calculated_value=None,
        reported_value=1050,
    )

    assert result.status == ValidationStatus.NOT_APPLICABLE
    assert result.calculated_value is None
    assert result.reported_value is None


def test_negative_tolerance_is_rejected():
    with pytest.raises(ValueError):
        FinancialValidationService(tolerance=-0.01)



def test_get_field_value_returns_existing_field():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=12500),
                page_number=1,
                evidence="Subtotal 12,500",
            )
        ],
    )

    result = FinancialValidationService.get_field_value(
        extraction,
        "subtotal",
    )

    assert result is not None
    assert result.number == 12500


def test_get_field_value_is_case_insensitive():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="Subtotal",
                value=ExtractedValue(number=12500),
                page_number=1,
                evidence="Subtotal 12,500",
            )
        ],
    )

    result = FinancialValidationService.get_field_value(
        extraction,
        "subtotal",
    )

    assert result is not None
    assert result.number == 12500


def test_get_field_value_returns_none_when_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[],
    )

    result = FinancialValidationService.get_field_value(
        extraction,
        "subtotal",
    )

    assert result is None



from app.schemas.extraction import ExtractedTable

def test_invoice_line_item_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        tables=[
            ExtractedTable(
                name="line_items",
                columns=[
                    "description",
                    "quantity",
                    "unit_price",
                    "line_total",
                ],
                rows=[
                    ["Service A", "2", "100", "200"],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    results = service.validate_invoice_line_items(extraction)

    assert len(results) == 1
    assert results[0].status == ValidationStatus.PASS
    assert results[0].calculated_value == 200
    assert results[0].reported_value == 200
    assert results[0].variance == 0


def test_invoice_line_item_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        tables=[
            ExtractedTable(
                name="line_items",
                columns=[
                    "description",
                    "quantity",
                    "unit_price",
                    "line_total",
                ],
                rows=[
                    ["Service A", "2", "100", "250"],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    results = service.validate_invoice_line_items(extraction)

    assert len(results) == 1
    assert results[0].status == ValidationStatus.FAIL
    assert results[0].calculated_value == 200
    assert results[0].reported_value == 250
    assert results[0].variance == 50


def test_invoice_line_item_is_not_applicable_when_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        tables=[
            ExtractedTable(
                name="line_items",
                columns=[
                    "description",
                    "quantity",
                    "unit_price",
                    "line_total",
                ],
                rows=[
                    ["Service A", "2", "100", ""],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    results = service.validate_invoice_line_items(extraction)

    assert len(results) == 1
    assert results[0].status == ValidationStatus.NOT_APPLICABLE


def test_invoice_multiple_line_items():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        tables=[
            ExtractedTable(
                name="line_items",
                columns=[
                    "description",
                    "quantity",
                    "unit_price",
                    "line_total",
                ],
                rows=[
                    ["Service A", "2", "100", "200"],
                    ["Service B", "3", "50", "150"],
                    ["Service C", "5", "20", "100"],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    results = service.validate_invoice_line_items(extraction)

    assert len(results) == 3
    assert all(
        result.status == ValidationStatus.PASS
        for result in results
    )



def test_invoice_subtotal_passes_when_line_totals_match():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=300.0),
                page_number=1,
                evidence="Subtotal: 300.00",
            )
        ],
        tables=[
            ExtractedTable(
                name="invoice_items",
                columns=["description", "quantity", "unit_price", "line_total"],
                rows=[
                    ["Item A", "2", "50", "100"],
                    ["Item B", "4", "50", "200"],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_subtotal(extraction)

    assert result.status == ValidationStatus.PASS
    assert result.calculated_value == 300.0
    assert result.reported_value == 300.0
    assert result.variance == 0.0


def test_invoice_subtotal_fails_when_line_totals_do_not_match():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=300.0),
                page_number=1,
                evidence="Subtotal: 300.00",
            )
        ],
        tables=[
            ExtractedTable(
                name="invoice_items",
                columns=["description", "quantity", "unit_price", "line_total"],
                rows=[
                    ["Item A", "2", "50", "100"],
                    ["Item B", "4", "40", "160"],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_subtotal(extraction)

    assert result.status == ValidationStatus.FAIL
    assert result.calculated_value == 260.0
    assert result.reported_value == 300.0
    assert result.variance == 40.0

def test_invoice_subtotal_is_not_applicable_when_subtotal_is_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[],
        tables=[
            ExtractedTable(
                name="invoice_items",
                columns=["description", "quantity", "unit_price", "line_total"],
                rows=[
                    ["Item A", "2", "50", "100"],
                    ["Item B", "4", "50", "200"],
                ],
                page_number=1,
            )
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_subtotal(extraction)

    assert result.status == ValidationStatus.NOT_APPLICABLE


def test_invoice_subtotal_is_not_applicable_when_line_total_is_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=300.0),
                page_number=1,
                evidence="Subtotal: 300.00",
            )
        ],
        tables=[
            ExtractedTable(
                name="invoice_items",
                columns=["description", "quantity", "unit_price", "line_total"],
                rows=[
                    ["Item A", "2", "50", "100"],
                    ["Item B", "4", "50", ""],
                ],
                page_number=1,
            )
        ],
        )

    service = FinancialValidationService()

    result = service.validate_invoice_subtotal(extraction)

    assert result.status == ValidationStatus.NOT_APPLICABLE



def test_invoice_total_passes_when_subtotal_tax_discount_match_total():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Subtotal: 10000",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=1800.0),
                page_number=1,
                evidence="Tax: 1800",
            ),
            ExtractedField(
                name="discount",
                value=ExtractedValue(number=500.0),
                page_number=1,
                evidence="Discount: 500",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=11300.0),
                page_number=1,
                evidence="Total: 11300",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_total(extraction)

    assert result.status == ValidationStatus.PASS
    assert result.calculated_value == 11300.0
    assert result.reported_value == 11300.0
    assert result.variance == 0.0


def test_invoice_total_fails_when_values_do_not_match():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Subtotal: 10000",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=1800.0),
                page_number=1,
                evidence="Tax: 1800",
            ),
            ExtractedField(
                name="discount",
                value=ExtractedValue(number=500.0),
                page_number=1,
                evidence="Discount: 500",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=12000.0),
                page_number=1,
                evidence="Total: 12000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_total(extraction)

    assert result.status == ValidationStatus.FAIL
    assert result.calculated_value == 11300.0
    assert result.reported_value == 12000.0
    assert result.variance == 700.0


def test_invoice_total_is_not_applicable_when_required_value_is_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Subtotal: 10000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_total(extraction)

    assert result.status == ValidationStatus.NOT_APPLICABLE


def test_invoice_total_passes_when_optional_tax_and_discount_are_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Subtotal: 10000",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Total: 10000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_total(extraction)

    assert result.status == ValidationStatus.PASS
    assert result.calculated_value == 10000.0



def test_invoice_change_passes_when_cash_and_change_match():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="cash_paid",
                value=ExtractedValue(number=12000.0),
                page_number=1,
                evidence="Cash Paid: 12000",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=11800.0),
                page_number=1,
                evidence="Total: 11800",
            ),
            ExtractedField(
                name="change",
                value=ExtractedValue(number=200.0),
                page_number=1,
                evidence="Change: 200",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_change(extraction)

    assert result.status == ValidationStatus.PASS
    assert result.calculated_value == 200.0
    assert result.reported_value == 200.0
    assert result.variance == 0.0


def test_invoice_change_fails_when_cash_and_change_do_not_match():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="cash_paid",
                value=ExtractedValue(number=12000.0),
                page_number=1,
                evidence="Cash Paid: 12000",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=11800.0),
                page_number=1,
                evidence="Total: 11800",
            ),
            ExtractedField(
                name="change",
                value=ExtractedValue(number=100.0),
                page_number=1,
                evidence="Change: 100",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_change(extraction)

    assert result.status == ValidationStatus.FAIL
    assert result.calculated_value == 200.0
    assert result.reported_value == 100.0
    assert result.variance == 100.0


def test_invoice_change_is_not_applicable_when_required_value_is_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="cash_paid",
                value=ExtractedValue(number=12000.0),
                page_number=1,
                evidence="Cash Paid: 12000",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=11800.0),
                page_number=1,
                evidence="Total: 11800",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_invoice_change(extraction)

    assert result.status == ValidationStatus.NOT_APPLICABLE


def test_balance_sheet_equation_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Total Assets: 100000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Total Liabilities: 60000",
            ),
            ExtractedField(
                name="equity",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Total Equity: 40000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[0].status == ValidationStatus.PASS
    assert result[0].calculated_value == 100000.0
    assert result[0].reported_value == 100000.0




def test_balance_sheet_equation_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Total Assets: 100000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Total Liabilities: 60000",
            ),
            ExtractedField(
                name="equity",
                value=ExtractedValue(number=30000.0),
                page_number=1,
                evidence="Total Equity: 30000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[0].status == ValidationStatus.FAIL
    assert result[0].calculated_value == 90000.0
    assert result[0].reported_value == 100000.0
    assert result[0].variance == 10000.0


def test_balance_sheet_equation_is_not_applicable_when_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Total Assets: 100000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Total Liabilities: 60000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[0].status == ValidationStatus.NOT_APPLICABLE


def test_balance_sheet_total_assets_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="current_assets",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Current Assets: 40000",
            ),
            ExtractedField(
                name="non_current_assets",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Non-current Assets: 60000",
            ),
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Total Assets: 100000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[1].status == ValidationStatus.PASS
    assert result[1].calculated_value == 100000.0


def test_balance_sheet_total_assets_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="current_assets",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Current Assets: 40000",
            ),
            ExtractedField(
                name="non_current_assets",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Non-current Assets: 50000",
            ),
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Total Assets: 100000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[1].status == ValidationStatus.FAIL
    assert result[1].calculated_value == 90000.0
    assert result[1].reported_value == 100000.0

def test_balance_sheet_total_liabilities_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="current_liabilities",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Current Liabilities: 25000",
            ),
            ExtractedField(
                name="non_current_liabilities",
                value=ExtractedValue(number=35000.0),
                page_number=1,
                evidence="Non-current Liabilities: 35000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Total Liabilities: 60000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[2].status == ValidationStatus.PASS
    assert result[2].calculated_value == 60000.0

def test_balance_sheet_total_liabilities_is_not_applicable_when_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="current_liabilities",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Current Liabilities: 25000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Total Liabilities: 60000",
            ),
        ],
    )

    service = FinancialValidationService()

    result = service.validate_balance_sheet(extraction)

    assert result[2].status == ValidationStatus.NOT_APPLICABLE




def test_profit_loss_gross_profit_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="revenue",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Revenue: 100000",
            ),
            ExtractedField(
                name="cogs",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="COGS: 60000",
            ),
            ExtractedField(
                name="gross_profit",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Gross Profit: 40000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[0].status == ValidationStatus.PASS
    assert result[0].calculated_value == 40000.0


def test_profit_loss_gross_profit_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="revenue",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Revenue: 100000",
            ),
            ExtractedField(
                name="cogs",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="COGS: 60000",
            ),
            ExtractedField(
                name="gross_profit",
                value=ExtractedValue(number=45000.0),
                page_number=1,
                evidence="Gross Profit: 45000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[0].status == ValidationStatus.FAIL
    assert result[0].calculated_value == 40000.0
    assert result[0].reported_value == 45000.0


def test_profit_loss_operating_income_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="gross_profit",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Gross Profit: 40000",
            ),
            ExtractedField(
                name="operating_expenses",
                value=ExtractedValue(number=15000.0),
                page_number=1,
                evidence="Operating Expenses: 15000",
            ),
            ExtractedField(
                name="operating_income",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Operating Income: 25000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[1].status == ValidationStatus.PASS
    assert result[1].calculated_value == 25000.0


def test_profit_loss_operating_income_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="gross_profit",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Gross Profit: 40000",
            ),
            ExtractedField(
                name="operating_expenses",
                value=ExtractedValue(number=15000.0),
                page_number=1,
                evidence="Operating Expenses: 15000",
            ),
            ExtractedField(
                name="operating_income",
                value=ExtractedValue(number=30000.0),
                page_number=1,
                evidence="Operating Income: 30000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[1].status == ValidationStatus.FAIL
    assert result[1].calculated_value == 25000.0
    assert result[1].reported_value == 30000.0


def test_profit_loss_net_income_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="operating_income",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Operating Income: 25000",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=5000.0),
                page_number=1,
                evidence="Tax: 5000",
            ),
            ExtractedField(
                name="net_income",
                value=ExtractedValue(number=20000.0),
                page_number=1,
                evidence="Net Income: 20000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[2].status == ValidationStatus.PASS
    assert result[2].calculated_value == 20000.0


def test_profit_loss_net_income_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="operating_income",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Operating Income: 25000",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=5000.0),
                page_number=1,
                evidence="Tax: 5000",
            ),
            ExtractedField(
                name="net_income",
                value=ExtractedValue(number=18000.0),
                page_number=1,
                evidence="Net Income: 18000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[2].status == ValidationStatus.FAIL
    assert result[2].calculated_value == 20000.0
    assert result[2].reported_value == 18000.0


def test_profit_loss_gross_profit_is_not_applicable_when_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="revenue",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Revenue: 100000",
            ),
            ExtractedField(
                name="cogs",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="COGS: 60000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[0].status == ValidationStatus.NOT_APPLICABLE


def test_profit_loss_operating_income_is_not_applicable_when_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="gross_profit",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Gross Profit: 40000",
            ),
            ExtractedField(
                name="operating_expenses",
                value=ExtractedValue(number=15000.0),
                page_number=1,
                evidence="Operating Expenses: 15000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[1].status == ValidationStatus.NOT_APPLICABLE


def test_profit_loss_net_income_is_not_applicable_when_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="operating_income",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Operating Income: 25000",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=5000.0),
                page_number=1,
                evidence="Tax: 5000",
            ),
        ],
    )

    result = FinancialValidationService().validate_profit_loss(
        extraction
    )

    assert result[2].status == ValidationStatus.NOT_APPLICABLE





def test_cash_flow_net_change_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="operating_cash_flow",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Operating Cash Flow: 50000",
            ),
            ExtractedField(
                name="investing_cash_flow",
                value=ExtractedValue(number=-20000.0),
                page_number=1,
                evidence="Investing Cash Flow: -20000",
            ),
            ExtractedField(
                name="financing_cash_flow",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Financing Cash Flow: 10000",
            ),
            ExtractedField(
                name="fx_adjustment",
                value=ExtractedValue(number=1000.0),
                page_number=1,
                evidence="FX Adjustment: 1000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=41000.0),
                page_number=1,
                evidence="Net Change in Cash: 41000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[0].status == ValidationStatus.PASS
    assert result[0].calculated_value == 41000.0
    assert result[0].reported_value == 41000.0


def test_cash_flow_net_change_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="operating_cash_flow",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Operating Cash Flow: 50000",
            ),
            ExtractedField(
                name="investing_cash_flow",
                value=ExtractedValue(number=-20000.0),
                page_number=1,
                evidence="Investing Cash Flow: -20000",
            ),
            ExtractedField(
                name="financing_cash_flow",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Financing Cash Flow: 10000",
            ),
            ExtractedField(
                name="fx_adjustment",
                value=ExtractedValue(number=1000.0),
                page_number=1,
                evidence="FX Adjustment: 1000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Net Change in Cash: 50000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[0].status == ValidationStatus.FAIL
    assert result[0].calculated_value == 41000.0
    assert result[0].reported_value == 50000.0
    assert result[0].variance == 9000.0


def test_cash_flow_net_change_passes_without_fx_adjustment():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="operating_cash_flow",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Operating Cash Flow: 50000",
            ),
            ExtractedField(
                name="investing_cash_flow",
                value=ExtractedValue(number=-20000.0),
                page_number=1,
                evidence="Investing Cash Flow: -20000",
            ),
            ExtractedField(
                name="financing_cash_flow",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Financing Cash Flow: 10000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Net Change in Cash: 40000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[0].status == ValidationStatus.PASS
    assert result[0].calculated_value == 40000.0


def test_cash_flow_net_change_is_not_applicable_when_required_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="operating_cash_flow",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Operating Cash Flow: 50000",
            ),
            ExtractedField(
                name="investing_cash_flow",
                value=ExtractedValue(number=-20000.0),
                page_number=1,
                evidence="Investing Cash Flow: -20000",
            ),
            ExtractedField(
                name="financing_cash_flow",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Financing Cash Flow: 10000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[0].status == ValidationStatus.NOT_APPLICABLE


def test_cash_flow_closing_cash_passes():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="opening_cash",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Opening Cash: 100000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=41000.0),
                page_number=1,
                evidence="Net Change in Cash: 41000",
            ),
            ExtractedField(
                name="closing_cash",
                value=ExtractedValue(number=141000.0),
                page_number=1,
                evidence="Closing Cash: 141000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[1].status == ValidationStatus.PASS
    assert result[1].calculated_value == 141000.0


def test_cash_flow_closing_cash_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="opening_cash",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Opening Cash: 100000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=41000.0),
                page_number=1,
                evidence="Net Change in Cash: 41000",
            ),
            ExtractedField(
                name="closing_cash",
                value=ExtractedValue(number=150000.0),
                page_number=1,
                evidence="Closing Cash: 150000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[1].status == ValidationStatus.FAIL
    assert result[1].calculated_value == 141000.0
    assert result[1].reported_value == 150000.0
    assert result[1].variance == 9000.0


def test_cash_flow_closing_cash_is_not_applicable_when_value_missing():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="opening_cash",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Opening Cash: 100000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=41000.0),
                page_number=1,
                evidence="Net Change in Cash: 41000",
            ),
        ],
    )

    result = FinancialValidationService().validate_cash_flow(
        extraction
    )

    assert result[1].status == ValidationStatus.NOT_APPLICABLE




def test_financial_validation_orchestrates_invoice():
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[
            ExtractedField(
                name="subtotal",
                value=ExtractedValue(number=300.0),
                page_number=1,
                evidence="Subtotal: 300",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=30.0),
                page_number=1,
                evidence="Tax: 30",
            ),
            ExtractedField(
                name="total",
                value=ExtractedValue(number=330.0),
                page_number=1,
                evidence="Total: 330",
            ),
        ],
        tables=[
            ExtractedTable(
                name="invoice_items",
                columns=[
                    "description",
                    "quantity",
                    "unit_price",
                    "line_total",
                ],
                rows=[
                    ["Item A", "2", "100", "200"],
                    ["Item B", "1", "100", "100"],
                ],
                page_number=1,
            )
        ],
    )

    result = FinancialValidationService().validate(extraction)

    assert isinstance(result, FinancialValidationResult)
    assert len(result.checks) == 5
    assert result.overall_status == ValidationStatus.PASS
    assert result.checks[-1].status == ValidationStatus.NOT_APPLICABLE

def test_financial_validation_orchestrates_balance_sheet():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Assets: 100000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Liabilities: 60000",
            ),
            ExtractedField(
                name="equity",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Equity: 40000",
            ),
        ],
    )

    result = FinancialValidationService().validate(extraction)

    assert isinstance(result, FinancialValidationResult)
    assert len(result.checks) == 3
    assert result.overall_status == ValidationStatus.PASS


def test_financial_validation_orchestrates_profit_loss():
    extraction = ExtractionResult(
        document_type=DocumentType.PROFIT_AND_LOSS,
        fields=[
            ExtractedField(
                name="revenue",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Revenue: 100000",
            ),
            ExtractedField(
                name="cogs",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="COGS: 60000",
            ),
            ExtractedField(
                name="gross_profit",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Gross Profit: 40000",
            ),
            ExtractedField(
                name="operating_expenses",
                value=ExtractedValue(number=15000.0),
                page_number=1,
                evidence="Operating Expenses: 15000",
            ),
            ExtractedField(
                name="operating_income",
                value=ExtractedValue(number=25000.0),
                page_number=1,
                evidence="Operating Income: 25000",
            ),
            ExtractedField(
                name="tax",
                value=ExtractedValue(number=5000.0),
                page_number=1,
                evidence="Tax: 5000",
            ),
            ExtractedField(
                name="net_income",
                value=ExtractedValue(number=20000.0),
                page_number=1,
                evidence="Net Income: 20000",
            ),
        ],
    )

    result = FinancialValidationService().validate(extraction)

    assert isinstance(result, FinancialValidationResult)
    assert len(result.checks) == 3
    assert result.overall_status == ValidationStatus.PASS


def test_financial_validation_orchestrates_cash_flow():
    extraction = ExtractionResult(
        document_type=DocumentType.CASH_FLOW,
        fields=[
            ExtractedField(
                name="operating_cash_flow",
                value=ExtractedValue(number=50000.0),
                page_number=1,
                evidence="Operating Cash Flow: 50000",
            ),
            ExtractedField(
                name="investing_cash_flow",
                value=ExtractedValue(number=-20000.0),
                page_number=1,
                evidence="Investing Cash Flow: -20000",
            ),
            ExtractedField(
                name="financing_cash_flow",
                value=ExtractedValue(number=10000.0),
                page_number=1,
                evidence="Financing Cash Flow: 10000",
            ),
            ExtractedField(
                name="net_change_in_cash",
                value=ExtractedValue(number=40000.0),
                page_number=1,
                evidence="Net Change in Cash: 40000",
            ),
            ExtractedField(
                name="opening_cash",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Opening Cash: 100000",
            ),
            ExtractedField(
                name="closing_cash",
                value=ExtractedValue(number=140000.0),
                page_number=1,
                evidence="Closing Cash: 140000",
            ),
        ],
    )

    result = FinancialValidationService().validate(extraction)

    assert isinstance(result, FinancialValidationResult)
    assert len(result.checks) == 2
    assert result.overall_status == ValidationStatus.PASS


def test_financial_validation_overall_status_is_fail_when_any_check_fails():
    extraction = ExtractionResult(
        document_type=DocumentType.BALANCE_SHEET,
        fields=[
            ExtractedField(
                name="assets",
                value=ExtractedValue(number=100000.0),
                page_number=1,
                evidence="Assets: 100000",
            ),
            ExtractedField(
                name="liabilities",
                value=ExtractedValue(number=60000.0),
                page_number=1,
                evidence="Liabilities: 60000",
            ),
            ExtractedField(
                name="equity",
                value=ExtractedValue(number=30000.0),
                page_number=1,
                evidence="Equity: 30000",
            ),
        ],
    )

    result = FinancialValidationService().validate(extraction)

    assert result.overall_status == ValidationStatus.FAIL