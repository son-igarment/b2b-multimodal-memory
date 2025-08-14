from __future__ import annotations

from typing import List
from ..api.schemas import ChunkResult


def simple_rescore(query: str, results: List[ChunkResult]) -> List[ChunkResult]:
    if not results:
        return results
    q = query.lower()
    def score(item: ChunkResult) -> float:
        text = (item.text or "").lower()
        bonus = 0.0
        if any(token in text for token in q.split()):
            bonus += 0.05
        return item.score + bonus
    return sorted(results, key=score, reverse=True)


