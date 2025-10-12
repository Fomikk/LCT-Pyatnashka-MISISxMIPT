import io

def test_profile_upload_ok(client, monkeypatch, SAMPLE_PROFILE):
    async def fake_analyze_file(req):
        # проверяем, что временный путь передан и тип адекватный
        assert getattr(req, "file_path", "")  # непустой
        assert getattr(req, "file_type", "auto") in {"csv", "auto"}
        return SAMPLE_PROFILE

    # ВАЖНО: патчим символ в модуле роутера, а не в analysis_service
    monkeypatch.setattr(
        "app.api.v1.routes_analysis.analyze_file",
        fake_analyze_file,
        raising=True,
    )

    csv_bytes = b"id,name\n1,Alex\n2,Ivan\n"
    files = {"file": ("example.csv", io.BytesIO(csv_bytes), "text/csv")}
    r = client.post("/api/v1/analysis/profile", files=files)

    assert r.status_code == 200
    body = r.json()
    assert body["rows"] == 3
    assert body["data_quality"]["completeness_score"] == 100.0
