from typing import Type, TypeVar

from google import genai
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import AIExtractionError


T = TypeVar("T", bound=BaseModel)


class GeminiService:
    """Wrapper around the Gemini API client."""

    def __init__(self) -> None:
        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )
        self.model = settings.gemini_model

    def extract_structured(
        self,
        prompt: str,
        response_schema: Type[T],
    ) -> T:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                },
            )

            return response_schema.model_validate_json(
                response.text
            )

        except Exception as exc:
            raise AIExtractionError(
                "Failed to extract structured data using Gemini."
            ) from exc