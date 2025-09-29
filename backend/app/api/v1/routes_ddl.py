from fastapi import APIRouter
from app.schemas.ddl import DDLRequest, DDLResponse
from app.services.ddl_service import generate_ddl


router = APIRouter()


@router.post("/generate", response_model=DDLResponse)
async def ddl_generate(payload: DDLRequest) -> DDLResponse:
    return await generate_ddl(payload)


