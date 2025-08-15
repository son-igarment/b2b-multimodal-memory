from fastapi import APIRouter, HTTPException
from ...core.health import get_health_status
from ...core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health")
async def health_check():
    """Health check endpoint cho load balancer"""
    try:
        return {"status": "healthy", "service": "b2b-multimodal-memory"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check cho tất cả services"""
    try:
        health_status = await get_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=500, detail="Detailed health check failed")


@router.get("/health/ready")
async def readiness_check():
    """Readiness probe cho Kubernetes"""
    try:
        health_status = await get_health_status()
        if health_status["status"] == "healthy":
            return {"status": "ready"}
        else:
            raise HTTPException(status_code=503, detail="Service not ready")
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/health/live")
async def liveness_check():
    """Liveness probe cho Kubernetes"""
    try:
        return {"status": "alive"}
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(status_code=500, detail="Service not alive")
