import json
from datetime import datetime, timezone

import pytest

from app.core.database import SessionLocal
from app.models import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.extraction import DocumentType, ExtractionResult
from app.schemas.financial_validation import FinancialValidationResult
from app.schemas.processing import ProcessingResult


TEST_DOCUMENT_NAMES = {
    "repository-create-test.pdf",
    "repository-latest-test.pdf",
    "repository-list-1.pdf",
    "repository-list-2.pdf",
}


@pytest.fixture(autouse=True)
def cleanup_test_documents():
    db = SessionLocal()

    try:
        db.query(Document).filter(
            Document.document_name.in_(TEST_DOCUMENT_NAMES)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()

    yield

    db = SessionLocal()

    try:
        db.query(Document).filter(
            Document.document_name.in_(TEST_DOCUMENT_NAMES)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


def create_processing_result() -> ProcessingResult:
    extraction = ExtractionResult(
        document_type=DocumentType.INVOICE,
        fields=[],
        tables=[],
    )

    financial_validation = FinancialValidationResult(
        checks=[],
    )

    return ProcessingResult(
        extraction=extraction,
        financial_validation=financial_validation,
    )


def test_create_document():
    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        saved_document = repository.create(
            document_name="repository-create-test.pdf",
            document_type="invoice",
            processing_status="PASS",
            processed_at=datetime.now(timezone.utc),
            processing_time_ms=150.5,
            result=create_processing_result(),
        )

        assert saved_document.id is not None
        assert saved_document.document_name == "repository-create-test.pdf"
        assert saved_document.document_type == "invoice"
        assert saved_document.processing_status == "PASS"
        assert saved_document.processing_time_ms == 150.5
        assert saved_document.result_json is not None

        stored_result = json.loads(saved_document.result_json)

        assert stored_result["extraction"]["document_type"] == "invoice"
        assert "financial_validation" in stored_result

    finally:
        db.close()


def test_get_latest_by_name():
    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        older_time = datetime(
            2026,
            9,
            11,
            10,
            0,
            tzinfo=timezone.utc,
        )

        newer_time = datetime(
            2026,
            9,
            11,
            12,
            0,
            tzinfo=timezone.utc,
        )

        older = repository.create(
            document_name="repository-latest-test.pdf",
            document_type="invoice",
            processing_status="PASS",
            processed_at=older_time,
            processing_time_ms=100.0,
            result=create_processing_result(),
        )

        newer = repository.create(
            document_name="repository-latest-test.pdf",
            document_type="invoice",
            processing_status="FAIL",
            processed_at=newer_time,
            processing_time_ms=200.0,
            result=create_processing_result(),
        )

        latest = repository.get_latest_by_name(
            "repository-latest-test.pdf"
        )

        assert latest is not None
        assert latest.id == newer.id
        assert latest.id != older.id
        assert latest.processed_at == newer.processed_at
        assert latest.processing_status == "FAIL"

    finally:
        db.close()


def test_get_latest_by_name_returns_none_when_missing():
    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        result = repository.get_latest_by_name(
            "does-not-exist.pdf"
        )

        assert result is None

    finally:
        db.close()


def test_list_documents_returns_all_records():
    db = SessionLocal()

    try:
        repository = DocumentRepository(db)

        first = repository.create(
            document_name="repository-list-1.pdf",
            document_type="invoice",
            processing_status="PASS",
            processed_at=datetime(
                2026,
                9,
                11,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            processing_time_ms=100.0,
            result=create_processing_result(),
        )

        second = repository.create(
            document_name="repository-list-2.pdf",
            document_type="invoice",
            processing_status="PASS",
            processed_at=datetime(
                2026,
                9,
                11,
                11,
                0,
                tzinfo=timezone.utc,
            ),
            processing_time_ms=120.0,
            result=create_processing_result(),
        )

        documents = repository.list_documents()

        names = [document.document_name for document in documents]

        assert first.document_name in names
        assert second.document_name in names

        matching_documents = [
            document
            for document in documents
            if document.document_name
            in {
                "repository-list-1.pdf",
                "repository-list-2.pdf",
            }
        ]

        assert len(matching_documents) == 2

    finally:
        db.close()

