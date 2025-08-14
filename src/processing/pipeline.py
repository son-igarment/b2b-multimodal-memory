from __future__ import annotations

from typing import List
from fastapi import UploadFile
from ..api.schemas import IngestTextRequest
from ..core.models import embed_texts
from ..core.storage import upsert_vectors, upload_bytes
from .text_processor import clean_text, chunk_text
from .document_processor import extract_text_from_bytes


def execute_ingest_text(payload: IngestTextRequest) -> List[str]:
    cleaned: str = clean_text(payload.text)
    chunks: List[str] = chunk_text(cleaned)
    vectors: List[List[float]] = embed_texts(chunks)
    payloads = []
    for chunk in chunks:
        payloads.append(
            {
                "customer_id": payload.customer_id,
                "channel": payload.channel,
                "title": payload.title,
                "text": chunk,
            }
        )
    ids = upsert_vectors(vectors, payloads)
    return ids


async def execute_ingest_file(file: UploadFile) -> List[str]:
    raw_bytes: bytes = await file.read()
    s3_uri: str = upload_bytes(raw_bytes, object_name=file.filename or "upload.bin", content_type=file.content_type or "application/octet-stream")
    text: str = extract_text_from_bytes(raw_bytes, filename=file.filename or "upload")
    cleaned: str = clean_text(text)
    chunks: List[str] = chunk_text(cleaned)
    vectors: List[List[float]] = embed_texts(chunks)
    payloads = []
    for chunk in chunks:
        payloads.append(
            {
                "customer_id": None,
                "channel": "file",
                "title": file.filename,
                "file_name": file.filename,
                "text": chunk,
                "raw_content_path": s3_uri,
            }
        )
    ids = upsert_vectors(vectors, payloads)
    return ids


