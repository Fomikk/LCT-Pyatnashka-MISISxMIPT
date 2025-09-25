from pydantic import BaseModel, Field
from typing import Optional


class RecommendationRequest(BaseModel):
    profile_summary: str = Field(description="Краткое описание данных")
    workload: str = Field(description="analytical|operational|streaming|mixed")
    latency_sla_seconds: Optional[int] = None


class RecommendationResponse(BaseModel):
    storage: str
    rationale: str
    refresh_cron: str


