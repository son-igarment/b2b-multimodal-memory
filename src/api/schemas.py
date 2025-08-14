from typing import List, Optional
from pydantic import BaseModel, Field


class IngestTextRequest(BaseModel):
    title: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    channel: str = Field(default="text")


class IngestResponse(BaseModel):
    ids: List[str]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    customer_id: Optional[str] = None


class ChunkResult(BaseModel):
    id: str
    score: float
    text: str
    metadata: dict


class SearchResponse(BaseModel):
    results: List[ChunkResult]
    answer: Optional[str] = None


