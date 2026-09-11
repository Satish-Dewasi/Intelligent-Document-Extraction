from fastapi.testclient import TestClient

from app.main import app
from app.schemas.extraction import (
    DocumentType,
    ExtractedField,
    ExtractedValue,
    ExtractionResult,
)
from app.schemas.text_extraction import (
    ExtractionMethod,
    PageText,
    TextExtractionResult,
)


client = TestClient(app)


class FakeValidationResult:
    valid = True

    def model_dump(self, mode="json"):
        return {
            "valid": True,
            "status": "VALID",
            "file_type": "pdf",
            "page_count": 1,
            "error_code": None,
            "message": None,
        }


class FakeValidationService:
    async def validate(self, file):
        return FakeValidationResult()


class FakeTextExtractionService:
    def extract(self, file_path):
        return TextExtractionResult(
            pages=[
                PageText(
                    page_number=1,
                    text="Invoice Number: INV-001",
                    extraction_method=ExtractionMethod.NATIVE,
                )
            ]
        )


class FakeGeminiService:
    def extract_structured(self, prompt, response_schema):
        return ExtractionResult(
            document_type=DocumentType.INVOICE,
            fields=[
                ExtractedField(
                    name="invoice_number",
                    value=ExtractedValue(
                        text="INV-001"
                    ),
                    page_number=1,
                    evidence="Invoice Number: INV-001",
                    confidence=0.98,
                )
            ],
            tables=[],
        )


def test_process_document_complete_pipeline(monkeypatch):
    import app.api.v1.documents as documents

    monkeypatch.setattr(
        documents,
        "validation_service",
        FakeValidationService(),
    )

    monkeypatch.setattr(
        documents,
        "text_extraction_service",
        FakeTextExtractionService(),
    )

    monkeypatch.setattr(
        documents,
        "gemini_service",
        FakeGeminiService(),
    )

    # Rebuild ExtractionService with fake Gemini.
    monkeypatch.setattr(
        documents,
        "extraction_service",
        documents.ExtractionService(
            documents.gemini_service
        ),
    )

    response = client.post(
        "/api/v1/documents/process",
        data={
            "document_type": "invoice",
        },
        files={
            "file": (
                "invoice.pdf",
                b"fake pdf content",
                "application/pdf",
            )
        },
    
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Document processed successfully."

    # Phase 2
    assert data["validation"]["valid"] is True

    # Phase 3
    assert len(data["text_extraction"]["pages"]) == 1
    assert (
        data["text_extraction"]["pages"][0]["text"]
        == "Invoice Number: INV-001"
    )

    # Phase 4
    assert data["structured_extraction"]["document_type"] == "invoice"

    fields = data["structured_extraction"]["fields"]

    assert len(fields) == 1
    assert fields[0]["name"] == "invoice_number"
    assert fields[0]["value"]["text"] == "INV-001"
    assert fields[0]["page_number"] == 1
    assert fields[0]["evidence"] == "Invoice Number: INV-001"
    assert fields[0]["confidence"] == 0.98