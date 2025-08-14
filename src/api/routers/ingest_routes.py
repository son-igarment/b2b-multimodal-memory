from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from ..schemas import IngestTextRequest, IngestResponse, IngestEmailRequest, IngestChatRequest
from ...processing.pipeline import (
    execute_ingest_text,
    execute_ingest_file,
    execute_ingest_email,
    execute_ingest_chat,
    execute_ingest_audio,
    execute_ingest_image,
)

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


@router.post("/email", response_model=IngestResponse)
def ingest_email(payload: IngestEmailRequest) -> IngestResponse:
    try:
        ids: List[str] = execute_ingest_email(payload)
        return IngestResponse(ids=ids)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ingest email failed: {err}")


@router.post("/chat", response_model=IngestResponse)
def ingest_chat(payload: IngestChatRequest) -> IngestResponse:
    try:
        ids: List[str] = execute_ingest_chat(payload)
        return IngestResponse(ids=ids)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ingest chat failed: {err}")


@router.post("/audio", response_model=IngestResponse)
async def ingest_audio(file: UploadFile = File(...)) -> IngestResponse:
    try:
        ids: List[str] = await execute_ingest_audio(file)
        return IngestResponse(ids=ids)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ingest audio failed: {err}")


@router.post("/image", response_model=IngestResponse)
async def ingest_image(file: UploadFile = File(...)) -> IngestResponse:
    try:
        ids: List[str] = await execute_ingest_image(file)
        return IngestResponse(ids=ids)
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Ingest image failed: {err}")


