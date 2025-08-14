from fastapi import APIRouter, HTTPException
from ..schemas import SearchRequest, SearchResponse, TimelineRequest, TimelineResponse, TimelineItem, DeleteResponse
from ...retrieval.search import execute_semantic_search
from ...retrieval.generator import generate_answer
from ...core.storage import get_es_client

router = APIRouter()


@router.post("/", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    try:
        results = execute_semantic_search(payload)
        answer = generate_answer(query=payload.query, chunks=results)
        return SearchResponse(results=results, answer=answer)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@router.post("/timeline", response_model=TimelineResponse)
def timeline(payload: TimelineRequest) -> TimelineResponse:
    try:
        es = get_es_client()
        if es is None:
            raise HTTPException(status_code=400, detail="Elasticsearch is not configured")
        must = [{"term": {"customer_id": payload.customer_id}}]
        if payload.thread_id:
            must.append({"term": {"thread_id": payload.thread_id}})
        if payload.org_id:
            must.append({"term": {"org_id": payload.org_id}})
        if payload.owner_id:
            must.append({"term": {"owner_id": payload.owner_id}})
        body = {
            "query": {"bool": {"filter": must}},
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": payload.limit,
        }
        idx = es.options(ignore_status=[404])
        resp = idx.search(index="mm_memory", body=body)
        items = []
        for hit in resp.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            items.append(
                TimelineItem(
                    id=str(hit.get("_id")),
                    timestamp=src.get("timestamp"),
                    channel=src.get("channel"),
                    title=src.get("title"),
                    text=src.get("text", ""),
                    metadata=src,
                )
            )
        return TimelineResponse(items=items)
    except HTTPException:
        raise
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Timeline failed: {err}")


@router.delete("/{doc_id}", response_model=DeleteResponse)
def delete_doc(doc_id: str) -> DeleteResponse:
    try:
        es = get_es_client()
        if es is not None:
            es.delete(index="mm_memory", id=doc_id, ignore=[404])
        # Note: Qdrant delete by id could be added here if needed
        return DeleteResponse(id=doc_id, deleted=True)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Delete failed: {err}")


