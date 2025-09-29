import textwrap
from app.schemas.pipelines import PipelineDraftRequest, PipelineDraftResponse


def _render_airflow_dag(dag_id: str, schedule: str) -> str:
    code = f"""
from datetime import datetime
from airflow import DAG
from airflow.operators.empty import EmptyOperator

with DAG(
    dag_id='{dag_id}',
    schedule='{schedule}',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['etl-ai-assistant']
):
    start = EmptyOperator(task_id='start')
    extract = EmptyOperator(task_id='extract')
    load = EmptyOperator(task_id='load')
    end = EmptyOperator(task_id='end')

    start >> extract >> load >> end
"""
    return textwrap.dedent(code).strip()


async def create_pipeline_draft(req: PipelineDraftRequest) -> PipelineDraftResponse:
    dag_id = f"etl_{req.source.get('type', 'src')}_to_{req.destination.get('type', 'dst')}"
    schedule = req.schedule_cron or "0 * * * *"
    dag_code = _render_airflow_dag(dag_id, schedule)
    graph = {
        "nodes": [
            {"id": "start", "label": "Start"},
            {"id": "extract", "label": "Extract"},
            {"id": "load", "label": "Load"},
            {"id": "end", "label": "End"},
        ],
        "edges": [
            {"from": "start", "to": "extract"},
            {"from": "extract", "to": "load"},
            {"from": "load", "to": "end"},
        ],
    }
    return PipelineDraftResponse(dag_id=dag_id, dag_code=dag_code, schedule_cron=schedule, preview_graph=graph)


