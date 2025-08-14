from __future__ import annotations

from typing import Dict, List, Optional
from ..api.schemas import SearchRequest, ChunkResult
from ..core.models import embed_texts
from ..core.storage import search_vectors


def execute_semantic_search(payload: SearchRequest) -> List[ChunkResult]:
    vectors = embed_texts([payload.query])
    if not vectors:
        return []
    query_vec = vectors[0]
    must: Optional[Dict[str, str]] = None
    if payload.customer_id:
        must = {"customer_id": payload.customer_id}
    hits = search_vectors(query_vector=query_vec, top_k=payload.top_k, must=must)
    results: List[ChunkResult] = []
    for hit in hits:
        pl = hit.payload or {}
        results.append(
            ChunkResult(
                id=str(hit.id),
                score=float(hit.score or 0.0),
                text=pl.get("text", ""),
                metadata=pl,
            )
        )
    return results


