from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from minio import Minio
from minio.error import S3Error

from .config import settings


def get_qdrant_client() -> QdrantClient:
    try:
        api_key = settings.qdrant_api_key if settings.qdrant_api_key else None
        if api_key:
            client = QdrantClient(url=settings.qdrant_url, api_key=api_key)
        else:
            client = QdrantClient(url=settings.qdrant_url)
        _ensure_collection(client)
        return client
    except Exception as err:
        raise RuntimeError(
            f"Cannot connect to Qdrant at {settings.qdrant_url}. Ensure docker is running (docker compose up -d). Details: {err}"
        )


def _ensure_collection(client: QdrantClient) -> None:
    collections = client.get_collections().collections
    names = {c.name for c in collections}
    if settings.qdrant_collection in names:
        return
    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qm.VectorParams(size=settings.vector_dim, distance=qm.Distance.COSINE),
    )


def _strip_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def upsert_vectors(vectors: List[List[float]], payloads: List[Dict[str, Any]]) -> List[str]:
    client = get_qdrant_client()
    points: List[qm.PointStruct] = []
    for i, vec in enumerate(vectors):
        point_id = str(uuid.uuid4())
        # Remove any pre-existing 'id' key from payload and strip None values
        raw_payload = payloads[i]
        clean_payload = {k: v for k, v in raw_payload.items() if k != "id" and v is not None}
        points.append(qm.PointStruct(id=point_id, vector=vec, payload=clean_payload))
    result = client.upsert(collection_name=settings.qdrant_collection, points=points)
    _ = result
    return [str(p.id) for p in points]


def search_vectors(query_vector: List[float], top_k: int, must: Optional[Dict[str, Any]] = None):
    client = get_qdrant_client()
    query_filter = None
    if must:
        conditions = []
        for key, value in must.items():
            conditions.append(qm.FieldCondition(key=key, match=qm.MatchValue(value=value)))
        query_filter = qm.Filter(must=conditions)
    hits = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
    )
    return hits


def get_minio() -> Minio:
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket(bucket: str) -> None:
    client = get_minio()
    found = client.bucket_exists(bucket)
    if not found:
        client.make_bucket(bucket)


def upload_bytes(content: bytes, object_name: str, content_type: str = "application/octet-stream") -> str:
    ensure_bucket(settings.minio_bucket)
    client = get_minio()
    try:
        client.put_object(
            bucket_name=settings.minio_bucket,
            object_name=object_name,
            data=content,
            length=len(content),
            content_type=content_type,
        )
        return f"s3://{settings.minio_bucket}/{object_name}"
    except S3Error as err:
        raise RuntimeError(f"MinIO upload failed: {err}")


