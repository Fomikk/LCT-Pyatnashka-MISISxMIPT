# ml/recommend/postprocess.py
from __future__ import annotations
from typing import Dict, Any, List

def _as_op(name: str, params: Dict[str, Any] | None) -> Dict[str, Any]:
    return {"op": name, "params": (params or {})}

def _fix_pipeline(pipeline: Dict[str, Any], target_store: str, table_name: str) -> Dict[str, Any]:
    """Приводим pipeline к виду {"dag":[{"op":..,"params":..}, ...]}."""
    dag: List[Dict[str, Any]] = []

    raw_dag = (pipeline or {}).get("dag")
    if isinstance(raw_dag, list) and raw_dag:
        # случай, когда в списке лежит один "толстый" объект с ключами Extract/Load/FilterByDate
        if isinstance(raw_dag[0], dict) and any(k in raw_dag[0] for k in ("Extract","Load","FilterByDate")):
            blob = raw_dag[0]
            if "Extract" in blob:
                dag.append(_as_op("Extract", blob.get("Extract")))
            if "FilterByDate" in blob and blob.get("FilterByDate"):
                dag.append(_as_op("FilterByDate", blob.get("FilterByDate")))
            if "Load" in blob:
                # иногда LLM запихивает целевой store/table внутрь "target"
                load_params = blob.get("Load") or {}
                target = load_params.get("target") or {}
                # нормализуем
                dag.append(_as_op("Load", {
                    "target": target_store,
                    "table": target.get("name") or table_name
                }))
        else:
            # может быть уже почти правильно
            for item in raw_dag:
                if isinstance(item, dict) and "op" in item and "params" in item:
                    dag.append({"op": str(item["op"]), "params": dict(item["params"])})
    else:
        # на всякий случай — минимальный DAG
        dag = [
            _as_op("Extract", {}),
            _as_op("Load", {"target": target_store, "table": table_name})
        ]

    return {"dag": dag}

def normalize_recommendation(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Чистим ответ LLM: pipeline, schedule, лишние поля, типы."""
    out = dict(rec)

    target_store = str(out.get("target_store") or "postgres")
    ddl = dict(out.get("ddl_hints") or {})
    table_name = str(ddl.get("table_name") or "data")

    # 1) Привести pipeline к канону
    out["pipeline"] = _fix_pipeline(out.get("pipeline") or {}, target_store, table_name)

    # 2) Переставить schedule, если он внезапно затесался внутрь dag
    schedule = dict(out.get("schedule") or {})
    if not schedule:
        # ищем в dag случайно попавший словарь вида {"cron":..., "reason":...}
        for item in list(out["pipeline"]["dag"]):
            if isinstance(item, dict) and "cron" in item and "reason" in item:
                schedule = {"cron": item.get("cron"), "reason": item.get("reason")}
                out["pipeline"]["dag"].remove(item)
                break
    # дефолт если так и не нашёлся
    if "cron" not in schedule:
        schedule = {"cron": "0 3 * * *", "reason": "daily default"}
    out["schedule"] = schedule

        # 3) чистим dag — оставляем только валидные операции + нормализуем Extract
    clean_dag = []
    for item in out["pipeline"]["dag"]:
        if not isinstance(item, dict):
            continue
        op = item.get("op")
        params = dict(item.get("params") or {})

        if op == "Extract":
            # Гарантируем структуру params = {"source": {...}}
            if "source" not in params or not isinstance(params["source"], dict):
                # соберём плоские поля (type/format/name/path/dsn) в source
                flat_keys = ("type", "format", "name", "path", "dsn", "host", "port", "database", "user", "password")
                flat = {k: params.pop(k) for k in list(params.keys()) if k in flat_keys}
                params = {"source": (flat or {})}
            clean_dag.append({"op": "Extract", "params": params})

        elif op == "FilterByDate":
            clean_dag.append({"op": "FilterByDate", "params": params or {}})

        elif op == "Load":
            # на всякий случай гарантируем target/table
            target = params.get("target")
            table  = params.get("table")
            if not target:
                target = target_store
            if not table:
                table = table_name
            clean_dag.append({"op": "Load", "params": {"target": target, "table": table}})

    # 3b) Гарантируем, что есть шаг Load
    have_load = any(it.get("op") == "Load" for it in clean_dag)
    if not have_load:
        clean_dag.append({"op": "Load", "params": {"target": target_store, "table": table_name}})

    out["pipeline"]["dag"] = clean_dag

    
    # 4) Гарантии типов для ddl_hints
    ddl.setdefault("primary_key", None)
    ddl.setdefault("partition_by", None)
    ddl.setdefault("order_by", [])
    ddl.setdefault("table_name", table_name)
    out["ddl_hints"] = ddl

    part = ddl.get("partition_by")
    if part:
        # есть ли колонка-подобная дате среди schema?
        # profile тут нет, поэтому простая эвристика: имя колонки содержит date/time/day/ts
        name = str(part).lower()
        if not any(key in name for key in ("date", "time", "day", "ts")):
            ddl["partition_by"] = None
    out["ddl_hints"] = ddl

    return out
