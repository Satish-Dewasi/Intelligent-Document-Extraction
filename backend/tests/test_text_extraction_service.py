import pymupdf
from app.core.exceptions import TextExtractionError
from app.schemas.text_extraction import ExtractionMethod
from app.services.text_extraction_service import TextExtractionService


def create_test_pdf(file_path):
    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text((72, 72), "Hello from page one")

    page2 = document.new_page()
    page2.insert_text((72, 72), "Hello from page two")

    document.save(file_path)
    document.close()


def test_extract_native_pdf_text(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    create_test_pdf(pdf_path)

    service = TextExtractionService()
    result = service.extract_pdf(str(pdf_path))

    assert len(result.pages) == 2

    assert result.pages[0].page_number == 1
    assert "Hello from page one" in result.pages[0].text
    assert result.pages[0].extraction_method == ExtractionMethod.NATIVE

    assert result.pages[1].page_number == 2
    assert "Hello from page two" in result.pages[1].text
    assert result.pages[1].extraction_method == ExtractionMethod.NATIVE



def test_detect_native_text_page():
    document = pymupdf.open()

    page = document.new_page()
    page.insert_text((72, 72), "This page contains native text")

    service = TextExtractionService()

    assert service.is_scanned_page(page) is False

    document.close()


def test_detect_scanned_page():
    document = pymupdf.open()

    page = document.new_page()

    service = TextExtractionService()

    assert service.is_scanned_page(page) is True

    document.close()



from PIL import Image, ImageDraw


def create_test_image(file_path):
    image = Image.new("RGB", (800, 300), "white")

    draw = ImageDraw.Draw(image)
    draw.text(
        (50, 100),
        "Invoice Number: INV-001",
        fill="black",
    )

    image.save(file_path)


def test_extract_text_from_image(tmp_path):
    image_path = tmp_path / "invoice.png"

    create_test_image(image_path)

    service = TextExtractionService()
    result = service.extract_image(str(image_path))

    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].extraction_method == ExtractionMethod.OCR

    assert "Invoice Number" in result.pages[0].text
    assert "INV" in result.pages[0].text
    assert "001" in result.pages[0].text



def create_scanned_pdf(file_path):
    image = Image.new("RGB", (800, 300), "white")

    draw = ImageDraw.Draw(image)
    draw.text(
        (50, 100),
        "Invoice Number: INV 001",
        fill="black",
    )

    image_path = file_path.with_suffix(".png")
    image.save(image_path)

    document = pymupdf.open()
    page = document.new_page()

    page.insert_image(
        page.rect,
        filename=str(image_path),
    )

    document.save(file_path)
    document.close()



def test_extract_scanned_pdf(tmp_path):
    pdf_path = tmp_path / "scanned.pdf"

    create_scanned_pdf(pdf_path)

    service = TextExtractionService()
    result = service.extract_pdf(str(pdf_path))

    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert result.pages[0].extraction_method == ExtractionMethod.OCR

    assert "Invoice" in result.pages[0].text
    assert "Number" in result.pages[0].text
    assert "INV" in result.pages[0].text



def test_extract_missing_file_raises_extraction_error(tmp_path):
    missing_file = tmp_path / "missing.pdf"

    service = TextExtractionService()

    try:
        service.extract(str(missing_file))
        assert False, "Expected TextExtractionError"
    except TextExtractionError as exc:
        assert "Failed to extract text" in str(exc)