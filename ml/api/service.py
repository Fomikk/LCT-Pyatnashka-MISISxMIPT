# ml/api/service.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from ml.recommend.orchestrator import make_recommendation
from ml.generators.ddl import generate_ddl

router = APIRouter(prefix="/ml", tags=["ml"])

# --------- модели запросов/ответов ---------
class PipelineIn(BaseModel):
    recommendation: Dict[str, Any] = Field(..., description="Объект из /ml/recommend")

class PipelineOut(BaseModel):
    pipeline: Dict[str, Any]

class ReportIn(BaseModel):
    recommendation: Dict[str, Any] = Field(..., description="Объект из /ml/recommend")
    profile: Optional[Dict[str, Any]] = Field(None, description="Опционально: профиль, чтобы дополнить отчёт")

class ReportOut(BaseModel):
    report: str

class RecommendIn(BaseModel):
    profile: Dict[str, Any]          # output профайлера
    user_prefs: Optional[Dict[str, Any]] = None

class RecommendOut(BaseModel):
    target_store: str
    ddl_hints: Dict[str, Any]
    pipeline: Dict[str, Any]
    schedule: Dict[str, Any]
    risks: list[str]

class DDLIn(BaseModel):
    target_store: str
    ddl_hints: Dict[str, Any]
    profile: Dict[str, Any]          # нужен для типов колонок

class DDLOut(BaseModel):
    sql: str

# --------- ручки ---------

@router.post("/recommend", response_model=RecommendOut)
def recommend(inp: RecommendIn):
    return make_recommendation(inp.profile, inp.user_prefs or {}, use_llm=True)

@router.post("/ddl", response_model=DDLOut)
def ddl(inp: DDLIn):
    sql = generate_ddl(inp.target_store, inp.profile, inp.ddl_hints)
    return {"sql": sql}

@router.post("/pipeline", response_model=PipelineOut, summary="Вернуть JSON-DAG пайплайна из recommendation")
def get_pipeline(body: PipelineIn):
    rec = body.recommendation or {}
    pipe = rec.get("pipeline")
    if not isinstance(pipe, dict) or "dag" not in pipe:
        # минимальная защита: если LLM/фронт не передали pipeline — сообщим 422
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="recommendation.pipeline.dag отсутствует")
    return {"pipeline": pipe}


# ——— простой генератор отчёта (markdown) ———
def _render_report_markdown(rec: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> str:
    store = rec.get("target_store", "?")
    hints = rec.get("ddl_hints", {}) or {}
    sched = rec.get("schedule", {}) or {}
    pipe = (rec.get("pipeline", {}) or {}).get("dag", []) or []
    risks = rec.get("risks", []) or []

    # инфа из профиля — по возможности
    rows = cols = None
    if profile and isinstance(profile.get("checks"), dict):
        rows = profile["checks"].get("rows")
        cols = profile["checks"].get("cols")

    lines = []
    lines.append(f"# Рекомендации по загрузке данных")
    if rows is not None and cols is not None:
        lines.append(f"_Профиль источника_: {rows} строк × {cols} колонок")
    lines.append("")
    lines.append(f"## Выбор хранилища")
    lines.append(f"- Рекомендовано: **{store}**")
    lines.append("")
    lines.append(f"## DDL-подсказки")
    lines.append(f"- Таблица: `{hints.get('table_name', 'table')}`")
    lines.append(f"- PRIMARY KEY: `{hints.get('primary_key')}`")
    part = hints.get("partition_by")
    lines.append(f"- Partition by: `{part}`" if part else "- Partition by: — (не требуется)")
    ob = hints.get("order_by") or []
    lines.append(f"- Order by: {', '.join(map(str, ob)) if ob else '—'}")
    lines.append("")
    lines.append(f"## Пайплайн")
    if pipe:
        ops = " → ".join(step.get("op", "?") for step in pipe if isinstance(step, dict))
        lines.append(f"- Шаги: {ops}")
    else:
        lines.append("- Шаги: —")
    lines.append("")
    lines.append("## Расписание")
    lines.append(f"- CRON: `{sched.get('cron', '-')}`")
    if sched.get("reason"):
        lines.append(f"- Обоснование: {sched['reason']}")
    lines.append("")
    if risks:
        lines.append("## Риски")
        for r in risks:
            lines.append(f"- {r}")
        lines.append("")
    lines.append("_Сгенерировано ML-ассистентом._")
    return "\n".join(lines)


@router.post("/report", response_model=ReportOut, summary="Сформировать короткий отчёт в Markdown")
def make_report(body: ReportIn):
    report_md = _render_report_markdown(body.recommendation, body.profile)
    return {"report": report_md}
