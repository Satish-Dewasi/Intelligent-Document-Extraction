import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Document
from app.schemas.processing import ProcessingResult


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        document_name: str,
        document_type: str,
        processing_status: str,
        processed_at: datetime,
        processing_time_ms: float | None,
        result: ProcessingResult,
    ) -> Document:
        document = Document(
            document_name=document_name,
            document_type=document_type,
            processing_status=processing_status,
            processed_at=processed_at,
            processing_time_ms=processing_time_ms,
            result_json=json.dumps(
                result.model_dump(mode="json")
            ),
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        return document

    def get_latest_by_name(
        self,
        document_name: str,
    ) -> Document | None:
        statement = (
            select(Document)
            .where(Document.document_name == document_name)
            .order_by(Document.processed_at.desc())
            .limit(1)
        )

        return self.db.scalars(statement).first()

    def get_result(
        self,
        document: Document,
    ) -> ProcessingResult:
        data = json.loads(document.result_json)

        return ProcessingResult.model_validate(data)

    def list_documents(self) -> list[Document]:
        statement = select(Document).order_by(
            Document.processed_at.desc()
        )

        return list(self.db.scalars(statement).all())