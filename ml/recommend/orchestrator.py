from __future__ import annotations
from typing import Any, Dict
from pathlib import Path
import json

from ml.recommend.llm_yandex import yandex_llm_json, YandexLLMError
from ml.recommend.rules import choose_store, ddl_hints
from ml.generators.pipeline import simple_pipeline
from ml.generators.schedule import schedule as sched_rule
from ml.recommend.postprocess import normalize_recommendation

# каталог с промптами/схемами
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

def _render_prompt(profile: dict, prefs: dict) -> tuple[str, str, dict | None]:
    """
    Читает текстовый шаблон промпта из ml/prompts/recommendation.txt и
    извлекает блоки SYSTEM/USER. В USER подставляет JSON профиля/настроек.
    """
    tpl_path = PROMPTS_DIR / "recommendation.txt"
    tpl = tpl_path.read_text(encoding="utf-8")

    # Разделители в файле: "### SYSTEM" и "### USER"
    try:
        sys_part, user_part = tpl.split("### USER", 1)
        system = sys_part.replace("### SYSTEM", "").strip()
        user = user_part.strip()
    except ValueError:
        # fallback: весь шаблон в user, минимальный system
        system = "Следуй инструкции. Верни ТОЛЬКО JSON строго по схеме."
        user = tpl

    user = (
        user
        .replace("{{PROFILE_JSON}}", json.dumps(profile, ensure_ascii=False))
        .replace("{{PREFS_JSON}}",   json.dumps(prefs or {}, ensure_ascii=False))
    )

    # JSON-схема для строгого ответа
    schema_path = PROMPTS_DIR / "recommendation_schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8")) if schema_path.exists() else None
    return system, user, schema

def make_recommendation(profile: dict, user_prefs: dict | None, use_llm: bool = True) -> Dict[str, Any]:
    prefs = user_prefs or {}
    if use_llm:
        try:
            system, user, schema = _render_prompt(profile, prefs)
            rec = yandex_llm_json(system=system, user=user, json_schema=schema)

            # нормализуем ответ от LLM
            rec = normalize_recommendation(rec)

            # мини-валидация ключей
            for k in ("target_store", "ddl_hints", "pipeline", "schedule", "risks"):
                if k not in rec:
                    raise ValueError(f"missing key: {k}")
            if rec["target_store"] not in {"postgres", "clickhouse", "hdfs"}:
                raise ValueError("bad target_store")

            rec["_source"] = "llm"
            return rec

        except (YandexLLMError, ValueError) as e:
            print("[LLM ERROR]", e)
            # уходим в fallback


    # Fallback: правила
    store = choose_store(profile, prefs)
    hints = ddl_hints(profile, prefs)
    pipe  = simple_pipeline(profile, store, hints)
    sch   = sched_rule(prefs.get("latency_sla"))
    return {
        "target_store": store,
        "ddl_hints": hints,
        "pipeline": pipe,
        "schedule": sch,
        "risks": ["LLM недоступна/ответ невалиден — применены правила"],
    }
