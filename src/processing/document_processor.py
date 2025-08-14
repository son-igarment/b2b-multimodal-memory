from __future__ import annotations

from typing import Optional
from pypdf import PdfReader
from docx import Document


def extract_text_from_bytes(data: bytes, filename: Optional[str] = None) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        return _extract_pdf(data)
    if name.endswith(".docx"):
        return _extract_docx(data)
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_pdf(data: bytes) -> str:
    from io import BytesIO
    bio = BytesIO(data)
    reader = PdfReader(bio)
    texts = []
    for page in reader.pages:
        texts.append(page.extract_text() or "")
    return "\n".join(texts)


def _extract_docx(data: bytes) -> str:
    from io import BytesIO
    bio = BytesIO(data)
    doc = Document(bio)
    texts = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(texts)


