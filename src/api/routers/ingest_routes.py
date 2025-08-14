from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..schemas import IngestTextRequest, IngestResponse
from ...processing.pipeline import execute_ingest_text, execute_ingest_file

router = APIRouter()


@router.post("/text", response_model=IngestResponse)
def ingest_text(payload: IngestTextRequest) -> IngestResponse:
    try:
        ids: List[str] = execute_ingest_text(payload)
        return IngestResponse(ids=ids)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ingest text failed: {err}")


@router.post("/file", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)) -> IngestResponse:
    try:
        ids: List[str] = await execute_ingest_file(file)
        return IngestResponse(ids=ids)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ingest file failed: {err}")


