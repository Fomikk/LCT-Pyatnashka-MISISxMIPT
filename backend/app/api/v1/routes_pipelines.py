from fastapi import APIRouter
from app.schemas.pipelines import PipelineDraftRequest, PipelineDraftResponse
from app.services.pipeline_service import create_pipeline_draft
from app.integrations.airflow_client import airflow_client


router = APIRouter()


@router.post("/draft", response_model=PipelineDraftResponse)
async def create_draft(payload: PipelineDraftRequest) -> PipelineDraftResponse:
    return await create_pipeline_draft(payload)


@router.post("/publish")
async def publish_dag(payload: PipelineDraftRequest) -> dict:
    draft = await create_pipeline_draft(payload)
    result = await airflow_client.create_dag(draft.dag_id, draft.dag_code)
    return {"publish": result}


@router.post("/trigger/{dag_id}")
async def trigger_dag(dag_id: str) -> dict:
    result = await airflow_client.trigger_dag(dag_id)
    return {"trigger": result}


@router.get("/status/{dag_id}")
async def dag_status(dag_id: str) -> dict:
    status = await airflow_client.get_dag_status(dag_id)
    return {"status": status}


