from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers.ingest_routes import router as ingest_router
from .routers.search_routes import router as search_router
from .routers.health_routes import router as health_router
from .routers.admin_routes import router as admin_router
# Tạm thời comment middleware để tránh lỗi
# from ..core.middleware import LoggingMiddleware, SecurityMiddleware, RateLimitMiddleware
from ..core.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="B2B Multimodal Memory", 
    version="0.1.0",
    description="Hệ thống bộ nhớ đa phương thức cho quy trình bán hàng B2B",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Tạm thời comment middleware để tránh lỗi
# app.add_middleware(LoggingMiddleware)
# app.add_middleware(SecurityMiddleware)
# app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, tags=["health"])
app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(search_router, prefix="/search", tags=["search"])
app.include_router(admin_router, tags=["admin"])


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("B2B Multimodal Memory API starting up...")
    logger.info("Available endpoints:")
    logger.info("  - Health: /health, /health/detailed, /health/ready, /health/live")
    logger.info("  - Ingest: /ingest/text, /ingest/file, /ingest/email, /ingest/chat, /ingest/audio, /ingest/image")
    logger.info("  - Search: /search/, /search/timeline")
    logger.info("  - Admin: /admin/cache/*, /admin/storage/*, /admin/system/*")
    logger.info("  - Documentation: /docs, /redoc")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("B2B Multimodal Memory API shutting down...")


