from __future__ import annotations

from typing import Optional
from PIL import Image
import pytesseract

from ..core.config import settings


def extract_text_from_image(image_bytes: bytes) -> str:
    try:
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
        text: str = pytesseract.image_to_string(img, lang="vie+eng")
        return text or ""
    except Exception:
        return ""


