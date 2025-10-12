def test_analyze_db_postgres_ok(client, monkeypatch, SAMPLE_PROFILE):
    async def fake_analyze_db(req):
        # req: DBAnalysisRequest
        assert req.db_type == "postgres"
        assert "dsn" in req.connection
        result = SAMPLE_PROFILE.copy()
        result.pop("file_metadata", None)  # имитируем отсутствие file_metadata
        return result

    # ВАЖНО: патчим символ в модуле роутера
    monkeypatch.setattr(
        "app.api.v1.routes_analysis.analyze_db",
        fake_analyze_db,
        raising=True,
    )

    payload = {
        "db_type": "postgres",
        "table": "public.my_table",
        "connection": {
            "dsn": "postgresql+psycopg2://user:pass@localhost:5432/dbname"
        },
    }
    r = client.post("/api/v1/analysis/db", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["rows"] == 3
    assert "file_metadata" not in body
