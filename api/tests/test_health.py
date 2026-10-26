from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz_root_and_versioned():
    for path in ("/healthz", "/api/v1/healthz"):
        r = client.get(path)
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
