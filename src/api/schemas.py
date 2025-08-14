from typing import List, Optional
from pydantic import BaseModel, Field


class IngestTextRequest(BaseModel):
    title: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    channel: str = Field(default="text")
    thread_id: Optional[str] = None
    interaction_id: Optional[str] = None
    timestamp: Optional[str] = None
    participants: Optional[List[str]] = None


class IngestResponse(BaseModel):
    ids: List[str]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    customer_id: Optional[str] = None
    channel: Optional[str] = None
    thread_id: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class ChunkResult(BaseModel):
    id: str
    score: float
    text: str
    metadata: dict


class SearchResponse(BaseModel):
    results: List[ChunkResult]
    answer: Optional[str] = None


class IngestEmailRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    channel: str = Field(default="email")
    thread_id: Optional[str] = None
    interaction_id: Optional[str] = None
    timestamp: Optional[str] = None
    participants: Optional[List[str]] = None
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None


class IngestChatRequest(BaseModel):
    platform: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    customer_id: Optional[str] = None
    channel: str = Field(default="chat")
    thread_id: Optional[str] = None
    interaction_id: Optional[str] = None
    timestamp: Optional[str] = None
    participants: Optional[List[str]] = None
    message_id: Optional[str] = None


