from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RecommendationRequest(BaseModel):
    profile_summary: str = Field(description="Краткое описание данных")
    workload: str = Field(description="analytical|operational|streaming|mixed")
    latency_sla_seconds: Optional[int] = Field(default=None, description="SLA задержки в секундах")
    data_volume: Optional[str] = Field(default=None, description="Объем данных (small|medium|large|huge)")
    update_frequency: Optional[str] = Field(default=None, description="Частота обновления (real-time|hourly|daily|batch)")
    budget_constraints: Optional[str] = Field(default=None, description="Ограничения бюджета")
    team_expertise: Optional[List[str]] = Field(default=None, description="Экспертиза команды")


class RecommendationResponse(BaseModel):
    storage: str = Field(description="Рекомендуемое хранилище")
    rationale: str = Field(description="Обоснование выбора")
    refresh_cron: str = Field(description="Расписание обновления")
    additional_recommendations: Optional[List[str]] = Field(default=None, description="Дополнительные рекомендации")
    performance_estimates: Optional[Dict[str, Any]] = Field(default=None, description="Оценки производительности")
    cost_estimates: Optional[Dict[str, Any]] = Field(default=None, description="Оценки стоимости")
    implementation_steps: Optional[List[str]] = Field(default=None, description="Шаги реализации")


