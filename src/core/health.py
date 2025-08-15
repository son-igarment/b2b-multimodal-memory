import asyncio
from typing import Dict, Any, List
from .storage import get_qdrant_client, get_minio, get_es_client
from .logging import get_logger

logger = get_logger(__name__)


class HealthChecker:
    """Health checker cho tất cả external services"""
    
    @staticmethod
    async def check_qdrant() -> Dict[str, Any]:
        """Kiểm tra Qdrant connection"""
        try:
            client = get_qdrant_client()
            collections = client.get_collections()
            return {
                "status": "healthy",
                "service": "qdrant",
                "details": {
                    "collections_count": len(collections.collections),
                    "collections": [c.name for c in collections.collections]
                }
            }
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "qdrant",
                "error": str(e)
            }
    
    @staticmethod
    async def check_minio() -> Dict[str, Any]:
        """Kiểm tra MinIO connection"""
        try:
            client = get_minio()
            buckets = client.list_buckets()
            bucket_names = [b.name for b in buckets]
            return {
                "status": "healthy",
                "service": "minio",
                "details": {
                    "buckets_count": len(bucket_names),
                    "buckets": bucket_names
                }
            }
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "minio",
                "error": str(e)
            }
    
    @staticmethod
    async def check_elasticsearch() -> Dict[str, Any]:
        """Kiểm tra Elasticsearch connection"""
        try:
            client = get_es_client()
            if client is None:
                return {
                    "status": "disabled",
                    "service": "elasticsearch",
                    "message": "Elasticsearch not configured"
                }
            
            info = client.info()
            cluster_info = client.cluster.health()
            return {
                "status": "healthy",
                "service": "elasticsearch",
                "details": {
                    "version": info.get("version", {}).get("number"),
                    "cluster_name": cluster_info.get("cluster_name"),
                    "cluster_status": cluster_info.get("status"),
                    "node_count": cluster_info.get("number_of_nodes")
                }
            }
        except Exception as e:
            logger.error(f"Elasticsearch health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "elasticsearch",
                "error": str(e)
            }
    
    @staticmethod
    async def check_all() -> Dict[str, Any]:
        """Kiểm tra tất cả services"""
        logger.info("Starting health check for all services")
        
        # Run all health checks concurrently
        tasks = [
            HealthChecker.check_qdrant(),
            HealthChecker.check_minio(),
            HealthChecker.check_elasticsearch()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        services_status = []
        overall_status = "healthy"
        
        for result in results:
            if isinstance(result, Exception):
                services_status.append({
                    "status": "error",
                    "service": "unknown",
                    "error": str(result)
                })
                overall_status = "unhealthy"
            else:
                services_status.append(result)
                if result.get("status") == "unhealthy":
                    overall_status = "unhealthy"
        
        health_status = {
            "status": overall_status,
            "timestamp": asyncio.get_event_loop().time(),
            "services": services_status
        }
        
        logger.info(f"Health check completed. Overall status: {overall_status}")
        return health_status


async def get_health_status() -> Dict[str, Any]:
    """Get health status for all services"""
    return await HealthChecker.check_all()
