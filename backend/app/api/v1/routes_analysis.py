from fastapi import APIRouter
from app.schemas.analysis import SourceInput, DataProfile, FileAnalysisRequest, DBAnalysisRequest
from app.services.analysis_service import analyze_source, analyze_file, analyze_db
from app.services.monitoring_service import monitor_performance


router = APIRouter()


@router.post("/profile", response_model=DataProfile)
@monitor_performance("analyze_profile")
async def profile_source(payload: SourceInput) -> DataProfile:
    return await analyze_source(payload)


@router.post("/file", response_model=DataProfile)
@monitor_performance("analyze_file")
async def analyze_file_source(payload: FileAnalysisRequest) -> DataProfile:
    return await analyze_file(payload)


@router.post("/db", response_model=DataProfile)
async def analyze_db_source(payload: DBAnalysisRequest) -> DataProfile:
    return await analyze_db(payload)


