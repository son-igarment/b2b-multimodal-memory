from __future__ import annotations

from typing import List


def clean_text(text: str) -> str:
    if not text:
        return ""
    cleaned: str = text.replace("\r", " ").strip()
    return " ".join(cleaned.split())


def chunk_text(text: str, max_tokens: int = 512) -> List[str]:
    if not text:
        return []
    words = text.split()
    chunks: List[str] = []
    current: List[str] = []
    count: int = 0
    for word in words:
        current.append(word)
        count += 1
        if count >= max_tokens:
            chunks.append(" ".join(current))
            current = []
            count = 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def summarize_stub(text: str, max_len: int = 200) -> str:
    if not text:
        return ""
    return (text[:max_len] + "...") if len(text) > max_len else text


def extract_entities_stub(text: str) -> List[str]:
    if not text:
        return []
    # very naive: return unique capitalized tokens
    tokens = {t.strip(",.;:!?()").strip() for t in text.split() if t[:1].isupper()}
    return [t for t in tokens if t]


