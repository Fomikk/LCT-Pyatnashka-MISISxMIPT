import json

def test_analyze_file_json_ok(client, monkeypatch, SAMPLE_PROFILE):
    # подменяем реальный анализатор стабом
    async def fake_analyze_file(req):
        # req: FileAnalysisRequest
        # проверим, что поля пришли
        assert req.file_path.endswith(".csv")
        assert req.file_type in {"csv", "auto"}
        return SAMPLE_PROFILE

    # важно: патчим функцию именно там, где она используется в роутере
    monkeypatch.setattr(
        "app.services.analysis_service.analyze_file",
        fake_analyze_file,
        raising=True,
    )

    payload = {
        "file_path": "ml/data/samples/example.csv",
        "file_type": "csv",
        "connection": {},
    }
    r = client.post(
        "/api/v1/analysis/file",
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 200
    body = r.json()
    # минимальные проверки формы ответа
    assert body["rows"] == 3
    assert isinstance(body["columns"], list)
    assert "data_quality" in body
