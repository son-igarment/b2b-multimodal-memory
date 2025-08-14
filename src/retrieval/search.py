from __future__ import annotations

from typing import Dict, List, Optional
from ..api.schemas import SearchRequest, ChunkResult
from ..core.models import embed_texts
from ..core.storage import search_vectors, es_search
from .text_rank import simple_rescore


def execute_semantic_search(payload: SearchRequest) -> List[ChunkResult]:
    vectors = embed_texts([payload.query])
    if not vectors:
        return []
    query_vec = vectors[0]
    must: Dict[str, str] = {}
    if payload.customer_id:
        must["customer_id"] = payload.customer_id
    if payload.channel:
        must["channel"] = payload.channel
    # date range filtering can be added if timestamp normalized
    hits = search_vectors(query_vector=query_vec, top_k=payload.top_k, must=must or None)
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
    # Optional: enrich by BM25 keyword results from Elasticsearch
    es_hits = es_search(
        query=payload.query,
        top_k=payload.top_k,
        filters=must or None,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    # Merge naive: append ES hits that are not in vector results by id
    existing_ids = {r.id for r in results}
    for h in es_hits:
        hid = str(h.get("id"))
        if hid not in existing_ids:
            src = h.get("source", {})
            results.append(
                ChunkResult(
                    id=hid,
                    score=float(h.get("score", 0.0)),
                    text=src.get("text", ""),
                    metadata=src,
                )
            )
    return simple_rescore(payload.query, results)


