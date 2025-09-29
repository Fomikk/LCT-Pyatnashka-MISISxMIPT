from fastapi import APIRouter
from app.schemas.recommend import RecommendationRequest, RecommendationResponse
from app.services.recommendation_service import recommend_storage_and_schedule


router = APIRouter()


@router.post("/storage", response_model=RecommendationResponse)
async def recommend_storage(payload: RecommendationRequest) -> RecommendationResponse:
    return await recommend_storage_and_schedule(payload)


