# ml/generators/schedule.py

def schedule(latency_sla: str | None) -> dict:
    """
    Простейший выбор cron по SLA.
    hour/day/week -> cron + причина
    """
    sla = (latency_sla or "day").lower()
    if sla == "hour":
        return {"cron": "0 * * * *", "reason": "часовая свежесть"}
    if sla == "week":
        return {"cron": "0 3 * * 1", "reason": "еженедельный запуск по понедельникам"}
    return {"cron": "0 3 * * *", "reason": "ежедневно в 03:00"}
