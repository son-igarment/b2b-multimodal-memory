from __future__ import annotations

from typing import List, Optional
from ..api.schemas import ChunkResult


def generate_answer(query: str, chunks: List[ChunkResult]) -> Optional[str]:
    if not chunks:
        return None
    top = chunks[0]
    return f"Top match says: {top.text[:300]}..."


