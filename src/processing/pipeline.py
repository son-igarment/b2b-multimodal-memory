from __future__ import annotations

from typing import List
from fastapi import UploadFile
from ..api.schemas import IngestTextRequest, IngestEmailRequest, IngestChatRequest
from ..core.models import embed_texts
from ..core.storage import upsert_vectors, upload_bytes, es_index_documents
from .text_processor import clean_text, chunk_text, summarize_stub, extract_entities_stub
from .document_processor import extract_text_from_bytes
from .audio_processor import transcribe_audio
from .image_processor import extract_text_from_image


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
                "org_id": payload.org_id,
                "owner_id": payload.owner_id,
                "summary": summarize_stub(chunk),
                "entities": extract_entities_stub(chunk),
            }
        )
    ids = upsert_vectors(vectors, payloads)
    es_index_documents(ids, payloads)
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
                "summary": summarize_stub(chunk),
                "entities": extract_entities_stub(chunk),
            }
        )
    ids = upsert_vectors(vectors, payloads)
    es_index_documents(ids, payloads)
    return ids


def _build_common_payload(
    *,
    customer_id: str | None,
    channel: str,
    title: str | None,
    text: str,
    thread_id: str | None = None,
    interaction_id: str | None = None,
    timestamp: str | None = None,
    participants: List[str] | None = None,
    extra: dict | None = None,
):
    payload = {
        "customer_id": customer_id,
        "channel": channel,
        "title": title,
        "text": text,
        "thread_id": thread_id,
        "interaction_id": interaction_id,
        "timestamp": timestamp,
        "participants": participants,
    }
    if extra:
        payload.update(extra)
    return payload


def execute_ingest_email(payload: IngestEmailRequest) -> List[str]:
    cleaned: str = clean_text(payload.body)
    chunks: List[str] = chunk_text(cleaned)
    vectors: List[List[float]] = embed_texts(chunks)
    payloads = []
    for chunk in chunks:
        payloads.append(
            _build_common_payload(
                customer_id=payload.customer_id,
                channel=payload.channel,
                title=payload.subject,
                text=chunk,
                thread_id=payload.thread_id,
                interaction_id=payload.interaction_id,
                timestamp=payload.timestamp,
                participants=payload.participants,
                extra={
                    "message_id": payload.message_id,
                    "in_reply_to": payload.in_reply_to,
                    "org_id": payload.org_id,
                    "owner_id": payload.owner_id,
                    "summary": summarize_stub(chunk),
                    "entities": extract_entities_stub(chunk),
                },
            )
        )
    ids = upsert_vectors(vectors, payloads)
    es_index_documents(ids, payloads)
    return ids


def execute_ingest_chat(payload: IngestChatRequest) -> List[str]:
    cleaned: str = clean_text(payload.text)
    chunks: List[str] = chunk_text(cleaned)
    vectors: List[List[float]] = embed_texts(chunks)
    payloads = []
    for chunk in chunks:
        payloads.append(
            _build_common_payload(
                customer_id=payload.customer_id,
                channel=payload.channel,
                title=f"chat:{payload.platform}",
                text=chunk,
                thread_id=payload.thread_id,
                interaction_id=payload.interaction_id,
                timestamp=payload.timestamp,
                participants=payload.participants,
                extra={
                    "platform": payload.platform,
                    "org_id": payload.org_id,
                    "owner_id": payload.owner_id,
                    "summary": summarize_stub(chunk),
                    "entities": extract_entities_stub(chunk),
                },
            )
        )
    ids = upsert_vectors(vectors, payloads)
    es_index_documents(ids, payloads)
    return ids


async def execute_ingest_audio(file: UploadFile) -> List[str]:
    raw_bytes: bytes = await file.read()
    s3_uri: str = upload_bytes(raw_bytes, object_name=file.filename or "audio.bin", content_type=file.content_type or "audio/mpeg")
    text, _segments = transcribe_audio(raw_bytes)
    cleaned: str = clean_text(text)
    chunks: List[str] = chunk_text(cleaned)
    if not chunks:
        # Không đẩy rỗng để tránh 500 do upstream lỗi
        return []
    vectors: List[List[float]] = embed_texts(chunks)
    payloads = []
    for chunk in chunks:
        payloads.append(
            {
                "customer_id": None,
                "channel": "audio",
                "title": file.filename,
                "file_name": file.filename,
                "text": chunk,
                "raw_content_path": s3_uri,
                "summary": summarize_stub(chunk),
                "entities": extract_entities_stub(chunk),
            }
        )
    ids = upsert_vectors(vectors, payloads)
    es_index_documents(ids, payloads)
    return ids


async def execute_ingest_image(file: UploadFile) -> List[str]:
    raw_bytes: bytes = await file.read()
    s3_uri: str = upload_bytes(raw_bytes, object_name=file.filename or "image.bin", content_type=file.content_type or "image/png")
    text: str = extract_text_from_image(raw_bytes)
    cleaned: str = clean_text(text)
    chunks: List[str] = chunk_text(cleaned)
    vectors: List[List[float]] = embed_texts(chunks)
    payloads = []
    for chunk in chunks:
        payloads.append(
            {
                "customer_id": None,
                "channel": "image",
                "title": file.filename,
                "file_name": file.filename,
                "text": chunk,
                "raw_content_path": s3_uri,
                "summary": summarize_stub(chunk),
                "entities": extract_entities_stub(chunk),
            }
        )
    ids = upsert_vectors(vectors, payloads)
    es_index_documents(ids, payloads)
    return ids


