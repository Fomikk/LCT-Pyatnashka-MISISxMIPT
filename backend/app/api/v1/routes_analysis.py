# backend/app/api/v1/routes_analysis.py

import os
import tempfile
from pathlib import Path
from fastapi import HTTPException
from datetime import datetime


from fastapi import APIRouter, UploadFile, File
from app.schemas.analysis import (
    SourceInput,
    DataProfile,
    FileAnalysisRequest,
    DBAnalysisRequest,
)
from app.services.analysis_service import analyze_source, analyze_file, analyze_db
from app.services.monitoring_service import monitor_performance

router = APIRouter()

# --- Upload файла (multipart/form-data) ---
# ВАЖНО: router для этого модуля подключается с prefix="/analysis" в router.py,
# поэтому здесь путь КОРОТКИЙ — "/profile"
@router.post("/profile", summary="Profile a file (upload)", response_model=None)
@monitor_performance("analyze_profile_upload")
async def profile_source_upload(
    file: UploadFile = File(...),
    delimiter: str | None = None,
    encoding: str | None = None,
):
    suffix = Path(file.filename or "").suffix or ".csv"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось сохранить загруженный файл: {e}")

    try:
        ext = (Path(file.filename or "").suffix or ".csv").lower()
        file_type = {".csv": "csv", ".json": "json", ".xml": "xml"}.get(ext, "csv")

        payload = FileAnalysisRequest(
            file_path=str(tmp_path),
            file_type=file_type,
            delimiter=delimiter,
            encoding=encoding,
        )
        result = await analyze_file(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать файл: {e}")
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


# --- Профиль по JSON-дескриптору источника ---
@router.post("/source", response_model=DataProfile, summary="Profile by source descriptor (JSON)")
@monitor_performance("analyze_profile_json")
async def profile_source_json(payload: SourceInput) -> DataProfile:
    return await analyze_source(payload)

# --- Профиль по пути к файлу ---
@router.post("/file", response_model=DataProfile, summary="Profile by file path (JSON)")
@monitor_performance("analyze_file")
async def analyze_file_source(payload: FileAnalysisRequest) -> DataProfile:
    return await analyze_file(payload)

# --- Анализ через БД ---
@router.post(
    "/db",
    response_model=DataProfile,
    summary="Analyze DB source (JSON)",
    response_model_exclude_none=True,   # <-- добавили
)
async def analyze_db_source(payload: DBAnalysisRequest) -> DataProfile:
    return await analyze_db(payload)


@router.post("/_debug/upload", response_model=None)
async def _debug_upload(file: UploadFile = File(...)):
    content = await file.read()
    return {"filename": file.filename, "size": len(content)}

@router.get("/ping", tags=["health"])
async def ping():
    return {
        "status": "ok",
        "service": "analysis",
        "time": datetime.utcnow().isoformat() + "Z",
    }