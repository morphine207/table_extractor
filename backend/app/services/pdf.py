from __future__ import annotations

from PIL import Image
import fitz  # PyMuPDF


def pdf_to_images(pdf_bytes: bytes, password: str | None = None, *, dpi: int = 300) -> list[Image.Image]:
    """
    Convert a PDF (in bytes) to a list of PIL Image objects (one per page).
    If a password is provided and the PDF is encrypted, attempt to authenticate.
    """
    doc = fitz.open("pdf", pdf_bytes)
    if doc.is_encrypted:
        if not password:
            raise ValueError("PDF is encrypted and requires a password.")
        if not doc.authenticate(password):
            raise ValueError("Incorrect password for encrypted PDF.")

    # PyMuPDF default rasterization is ~72 DPI; for legal-tech accuracy we render higher.
    # zoom = dpi / 72
    zoom = max(1.0, float(dpi) / 72.0)
    mat = fitz.Matrix(zoom, zoom)

    images: list[Image.Image] = []
    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(image)
    return images


def pdf_num_pages(pdf_bytes: bytes, password: str | None = None) -> int:
    doc = fitz.open("pdf", pdf_bytes)
    if doc.is_encrypted:
        if not password:
            raise ValueError("PDF is encrypted and requires a password.")
        if not doc.authenticate(password):
            raise ValueError("Incorrect password for encrypted PDF.")
    return len(doc)


