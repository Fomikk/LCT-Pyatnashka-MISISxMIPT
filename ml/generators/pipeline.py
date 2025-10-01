# ml/generators/pipeline.py

def simple_pipeline(profile: dict, target_store: str, hints: dict) -> dict:
    """
    Возвращает минимальный DAG: Extract -> (опц. FilterByDate) -> Load
    """
    dag = [
        {"op": "Extract", "params": {"source": profile.get("source")}}
    ]

    part_col = (hints or {}).get("partition_by")
    if part_col:
        dag.append({"op": "FilterByDate",
                    "params": {"column": part_col, "window": "last_30d"}})

    dag.append({"op": "Load",
                "params": {"target": target_store,
                           "table": (hints or {}).get("table_name", "data")}})
    return {"dag": dag}
