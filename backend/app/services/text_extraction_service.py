import pymupdf
import pytesseract
from pathlib import Path
from PIL import Image
from app.core.exceptions import TextExtractionError

from app.schemas.text_extraction import (
    ExtractionMethod,
    PageText,
    TextExtractionResult,
)


class TextExtractionService:
    """Extract text from PDF and image documents."""

    def extract(self, file_path: str) -> TextExtractionResult:
        """Extract text from a supported PDF or image document."""

        extension = Path(file_path).suffix.lower()

        try:
            if extension == ".pdf":
                return self.extract_pdf(file_path)

            if extension in {".jpg", ".jpeg", ".png"}:
                return self.extract_image(file_path)

            raise TextExtractionError(
                f"Unsupported file extension: {extension}"
            )

        except TextExtractionError:
            raise

        except Exception as exc:
            raise TextExtractionError(
                f"Failed to extract text from document: {file_path}"
            ) from exc

    def extract_pdf(self, file_path: str) -> TextExtractionResult:
        pages = []

        document = pymupdf.open(file_path)

        try:
            for page_index, page in enumerate(document):
                page_number = page_index + 1

                if self.is_scanned_page(page):
                    matrix = pymupdf.Matrix(2, 2)
                    pixmap = page.get_pixmap(matrix=matrix)

                    image = Image.frombytes(
                        "RGB",
                        [pixmap.width, pixmap.height],
                        pixmap.samples,
                    )

                    text = pytesseract.image_to_string(image)
                    extraction_method = ExtractionMethod.OCR

                else:
                    text = page.get_text("text")
                    extraction_method = ExtractionMethod.NATIVE

                pages.append(
                    PageText(
                        page_number=page_number,
                        text=text,
                        extraction_method=extraction_method,
                    )
                )

        finally:
            document.close()

        return TextExtractionResult(pages=pages)

    def is_scanned_page(self, page) -> bool:
        """Return True when a PDF page has no meaningful native text."""

        text = page.get_text("text").strip()

        return not text

    def extract_image(self, file_path: str) -> TextExtractionResult:
        """Extract text from an image using Tesseract."""

        image_path = Path(file_path)

        with Image.open(image_path) as image:
            text = pytesseract.image_to_string(image)

        page = PageText(
            page_number=1,
            text=text,
            extraction_method=ExtractionMethod.OCR,
        )

        return TextExtractionResult(pages=[page])