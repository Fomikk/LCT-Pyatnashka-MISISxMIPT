def test_root_ok(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert "message" in body
    assert "/api/docs" in body.get("docs", "/api/docs")

def test_docs_ui_served(client):
    # проверяем, что Swagger UI доступен на /api/docs
    r = client.get("/api/docs")
    assert r.status_code == 200
    assert "Swagger UI" in r.text or "swagger-ui" in r.text.lower()
