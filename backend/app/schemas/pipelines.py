from pydantic import BaseModel, Field
from typing import Any, Optional


class PipelineDraftRequest(BaseModel):
    source: dict[str, Any]
    destination: dict[str, Any]
    transform: Optional[dict[str, Any]] = Field(default_factory=dict)
    schedule_cron: Optional[str] = None


class PipelineDraftResponse(BaseModel):
    dag_id: str
    dag_code: str
    schedule_cron: str
    preview_graph: dict[str, Any]


