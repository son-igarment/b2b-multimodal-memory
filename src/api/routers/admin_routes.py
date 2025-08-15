from fastapi import APIRouter, HTTPException
from ...core.cache import cache
from ...core.storage import get_qdrant_client, get_minio, get_es_client
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/admin/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        return cache.get_stats()
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache stats")


@router.delete("/admin/cache/clear")
async def clear_cache():
    """Clear all cache"""
    try:
        cache.clear()
        logger.info("Cache cleared by admin request")
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/admin/storage/qdrant/collections")
async def get_qdrant_collections():
    """Get Qdrant collections information"""
    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        return {
            "collections": [
                {
                    "name": c.name,
                    "vectors_count": c.vectors_count,
                    "points_count": c.points_count
                }
                for c in collections.collections
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get Qdrant collections: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Qdrant collections")


@router.get("/admin/storage/minio/buckets")
async def get_minio_buckets():
    """Get MinIO buckets information"""
    try:
        client = get_minio()
        buckets = client.list_buckets()
        bucket_info = []
        
        for bucket in buckets:
            try:
                objects = list(client.list_objects(bucket.name))
                bucket_info.append({
                    "name": bucket.name,
                    "creation_date": bucket.creation_date.isoformat(),
                    "objects_count": len(objects)
                })
            except Exception:
                bucket_info.append({
                    "name": bucket.name,
                    "creation_date": bucket.creation_date.isoformat(),
                    "objects_count": "unknown"
                })
        
        return {"buckets": bucket_info}
    except Exception as e:
        logger.error(f"Failed to get MinIO buckets: {e}")
        raise HTTPException(status_code=500, detail="Failed to get MinIO buckets")


@router.get("/admin/storage/elasticsearch/indices")
async def get_es_indices():
    """Get Elasticsearch indices information"""
    try:
        client = get_es_client()
        if client is None:
            return {"message": "Elasticsearch not configured"}
        
        indices = client.cat.indices(format="json")
        return {"indices": indices}
    except Exception as e:
        logger.error(f"Failed to get ES indices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ES indices")


@router.post("/admin/storage/qdrant/collection/{collection_name}/recreate")
async def recreate_qdrant_collection(collection_name: str):
    """Recreate Qdrant collection (dangerous operation)"""
    try:
        client = get_qdrant_client()
        
        # Check if collection exists
        collections = client.get_collections()
        if collection_name not in [c.name for c in collections.collections]:
            raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found")
        
        # Delete and recreate collection
        client.delete_collection(collection_name)
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                "size": 384,
                "distance": "Cosine"
            }
        )
        
        logger.warning(f"Collection {collection_name} recreated by admin")
        return {"message": f"Collection {collection_name} recreated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to recreate collection {collection_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to recreate collection {collection_name}")


@router.get("/admin/system/info")
async def get_system_info():
    """Get system information"""
    try:
        import psutil
        import platform
        
        return {
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "cpu": {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1)
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            }
        }
    except ImportError:
        return {"message": "psutil not installed - system info unavailable"}
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system info")
