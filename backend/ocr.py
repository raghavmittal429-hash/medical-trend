import os
import importlib.util


def extract_text(file_path: str) -> str:
    """
    Extract text from image or PDF file
    Supports: JPG, JPEG, PNG, PDF
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf':
        return extract_from_pdf(file_path)
    else:
        return extract_from_image(file_path)


def extract_from_image(image_path: str) -> str:
    """Extract text from an image file."""
    file_name = os.path.basename(image_path)
    file_size = os.path.getsize(image_path) if os.path.exists(image_path) else 0

    try:
        from PIL import Image
        import pytesseract

        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        if text.strip():
            return text
        else:
            return f"No text found in image {file_name} ({file_size} bytes). The image may not contain readable text."

    except Exception as e:
        return f"Image text extraction failed for {file_name} ({file_size} bytes): {str(e)}. The image may be corrupted or in an unsupported format."


def extract_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file using fallback methods."""
    # Get file info for better error messages
    file_name = os.path.basename(pdf_path)
    file_size = os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0

    # First try PDF text extraction (for text-based PDFs)
    try:
        reader = None

        if importlib.util.find_spec("pypdf") is not None:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
        elif importlib.util.find_spec("PyPDF2") is not None:
            import PyPDF2
            reader = PyPDF2.PdfReader(pdf_path)

        if reader is not None:
            full_text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                full_text += page_text + "\n"

            if full_text.strip():
                return full_text

    except Exception as e:
        pdf_text_error = f"PDF text extraction failed for {file_name} ({file_size} bytes): {str(e)}"

    # Fallback to image-based OCR if libraries are available
    try:
        if importlib.util.find_spec("pdf2image") is not None and importlib.util.find_spec("pytesseract") is not None:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(pdf_path)
            full_text = ""
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image)
                full_text += f"\n--- Page {i+1} ---\n{text}"

            if full_text.strip():
                return full_text

    except Exception as e:
        ocr_error = f"PDF image-based OCR failed for {file_name} ({file_size} bytes): {str(e)}"

    # Return combined error information
    error_msg = f"Text extraction failed for {file_name} ({file_size} bytes).\n"
    if 'pdf_text_error' in locals():
        error_msg += f"PDF text extraction: {pdf_text_error}\n"
    if 'ocr_error' in locals():
        error_msg += f"OCR extraction: {ocr_error}\n"
    error_msg += "The document may be image-based, corrupted, or require different processing libraries."

    return error_msg

