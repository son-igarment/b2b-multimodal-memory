from __future__ import annotations

from typing import Any, Dict, List, Optional
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from minio import Minio
from minio.error import S3Error
from typing import Tuple

try:
    from elasticsearch import Elasticsearch, helpers  # type: ignore
except Exception:  # pragma: no cover
    Elasticsearch = None  # type: ignore
    helpers = None  # type: ignore

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


# Elasticsearch helpers

def get_es_client():
    if settings.es_url is None or Elasticsearch is None:
        return None
    if settings.es_username and settings.es_password:
        client = Elasticsearch(
            settings.es_url,
            basic_auth=(settings.es_username, settings.es_password),
            verify_certs=False,
        )
    else:
        client = Elasticsearch(settings.es_url, verify_certs=False)
    _ensure_es_index(client)
    return client


def _ensure_es_index(client) -> None:
    if client is None:
        return
    idx = settings.es_index
    if client.indices.exists(index=idx):
        return
    mapping = {
        "mappings": {
            "properties": {
                "customer_id": {"type": "keyword"},
                "channel": {"type": "keyword"},
                "title": {"type": "text"},
                "text": {"type": "text"},
                "thread_id": {"type": "keyword"},
                "interaction_id": {"type": "keyword"},
                "timestamp": {"type": "date", "ignore_malformed": True},
                "participants": {"type": "keyword"},
                "raw_content_path": {"type": "keyword"},
                "file_name": {"type": "keyword"},
                "platform": {"type": "keyword"},
                "message_id": {"type": "keyword"},
                "in_reply_to": {"type": "keyword"},
            }
        }
    }
    client.indices.create(index=idx, body=mapping)


def es_index_documents(ids: List[str], payloads: List[Dict[str, Any]]) -> None:
    client = get_es_client()
    if client is None or helpers is None:
        return
    actions = []
    idx = settings.es_index
    for i, payload in enumerate(payloads):
        doc_id = ids[i]
        actions.append({
            "_op_type": "index",
            "_index": idx,
            "_id": doc_id,
            "_source": _strip_none(payload),
        })
    helpers.bulk(client, actions)


def es_search(query: str, top_k: int, filters: Optional[Dict[str, Any]] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
    client = get_es_client()
    if client is None:
        return []
    must = []
    if filters:
        for k, v in filters.items():
            must.append({"term": {k: v}})
    if date_from or date_to:
        range_filter = {"range": {"timestamp": {}}}
        if date_from:
            range_filter["range"]["timestamp"]["gte"] = date_from
        if date_to:
            range_filter["range"]["timestamp"]["lte"] = date_to
        must.append(range_filter)
    body = {
        "query": {
            "bool": {
                "must": [{"multi_match": {"query": query, "fields": ["title^2", "text"]}}],
                "filter": must,
            }
        },
        "size": top_k,
    }
    resp = client.search(index=settings.es_index, body=body)
    results = []
    for hit in resp.get("hits", {}).get("hits", []):
        results.append({
            "id": hit.get("_id"),
            "score": float(hit.get("_score", 0.0)),
            "source": hit.get("_source", {}),
        })
    return results


