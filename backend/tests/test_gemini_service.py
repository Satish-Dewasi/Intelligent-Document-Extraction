import pytest

from app.core.exceptions import AIExtractionError
from app.schemas.extraction import ExtractionResult
from app.services.gemini_service import GeminiService


def test_gemini_service_translates_api_errors(monkeypatch):
    service = GeminiService()

    def failing_generate_content(*args, **kwargs):
        raise RuntimeError("Gemini API unavailable")

    monkeypatch.setattr(
        service.client.models,
        "generate_content",
        failing_generate_content,
    )

    with pytest.raises(AIExtractionError):
        service.extract_structured(
            prompt="test",
            response_schema=ExtractionResult,
        )