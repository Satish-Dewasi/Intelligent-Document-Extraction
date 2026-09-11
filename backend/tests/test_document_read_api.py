from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.extraction import DocumentType, ExtractionResult
from app.schemas.financial_validation import (
    FinancialValidationResult,
)
from app.schemas.processing import ProcessingResult


client = TestClient(app)

TEST_DOCUMENT_NAME = "api-read-test.pdf"


def create_result() -> ProcessingResult:
    return ProcessingResult(
        extraction=ExtractionResult(
            document_type=DocumentType.INVOICE,
            fields=[],
            tables=[],
        ),
        financial_validation=FinancialValidationResult(
            checks=[]
        ),
    )


def cleanup():
    db = SessionLocal()

    try:
        db.query(Document).filter(
            Document.document_name == TEST_DOCUMENT_NAME
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


def test_get_latest_document():
    cleanup()

    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        document = repository.create(
            document_name=TEST_DOCUMENT_NAME,
            document_type="invoice",
            processing_status="NOT_APPLICABLE",
            processed_at=datetime.now(timezone.utc),
            processing_time_ms=120.0,
            result=create_result(),
        )

        response = client.get(
            f"/api/v1/documents/{TEST_DOCUMENT_NAME}/latest"
        )

        assert response.status_code == 200

        data = response.json()

        assert data["id"] == document.id
        assert data["document_name"] == TEST_DOCUMENT_NAME
        assert data["document_type"] == "invoice"
        assert data["processing_status"] == "NOT_APPLICABLE"
        assert data["processing_time_ms"] == 120.0

        assert data["result"]["extraction"]["document_type"] == "invoice"
        assert "financial_validation" in data["result"]

    finally:
        db.close()
        cleanup()


def test_get_latest_document_returns_404():
    cleanup()

    response = client.get(
        "/api/v1/documents/does-not-exist.pdf/latest"
    )

    assert response.status_code == 404


def test_list_documents():
    cleanup()

    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        first = repository.create(
            document_name=TEST_DOCUMENT_NAME,
            document_type="invoice",
            processing_status="NOT_APPLICABLE",
            processed_at=datetime(
                2026,
                9,
                11,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            processing_time_ms=100.0,
            result=create_result(),
        )

        second = repository.create(
            document_name=TEST_DOCUMENT_NAME,
            document_type="invoice",
            processing_status="NOT_APPLICABLE",
            processed_at=datetime(
                2026,
                9,
                11,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            processing_time_ms=200.0,
            result=create_result(),
        )

        response = client.get(
            "/api/v1/documents"
        )

        assert response.status_code == 200

        data = response.json()

        matching = [
            item
            for item in data
            if item["document_name"] == TEST_DOCUMENT_NAME
        ]

        assert len(matching) == 2

        assert matching[0]["id"] == second.id
        assert matching[1]["id"] == first.id

    finally:
        db.close()
        cleanup()