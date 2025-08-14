from fastapi import FastAPI
from .routers.ingest_routes import router as ingest_router
from .routers.search_routes import router as search_router

app = FastAPI(title="B2B Multimodal Memory", version="0.1.0")

app.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
app.include_router(search_router, prefix="/search", tags=["search"])


