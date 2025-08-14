from fastapi import APIRouter, HTTPException
from ..schemas import SearchRequest, SearchResponse
from ...retrieval.search import execute_semantic_search
from ...retrieval.generator import generate_answer

router = APIRouter()


@router.post("/", response_model=SearchResponse)
def search(payload: SearchRequest) -> SearchResponse:
    try:
        results = execute_semantic_search(payload)
        answer = generate_answer(query=payload.query, chunks=results)
        return SearchResponse(results=results, answer=answer)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


