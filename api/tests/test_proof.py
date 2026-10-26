import base64
import hashlib

import pytest
from conftest import FakeWeather
from fastapi.testclient import TestClient

from app.adapters.storage import LocalStorage
from app.config import Settings
from app.deps import build_container
from app.main import create_app
from app.store import MemoryStore

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF"


@pytest.fixture
def client(tmp_path):
    c = build_container(Settings(scheduler_enabled=False), MemoryStore(), weather=FakeWeather(),
                        storage=LocalStorage(tmp_path / "blobs"))
    app = create_app()
    import app.routes.v1 as v1

    app.dependency_overrides[v1.C] = lambda: c
    tc = TestClient(app)
    tc.post("/api/v1/accounts/acct-p1/evaluate")
    tasks = tc.get("/api/v1/accounts/acct-p1/tasks?status=open").json()["tasks"]
    return tc, tasks, tmp_path


def task_with(tasks, rule):
    return next(t for t in tasks if rule in t["rule_id"])


def test_photo_proof_is_stored_hashed_and_redownloadable(client):
    tc, tasks, _ = client
    t = task_with(tasks, "hose_age")
    r = tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1", "lat": "33.3062", "lon": "-111.8413",
                "client_captured_at": "2026-10-25T15:01:02Z"}, files={"file": ("hoses.png", PNG, "image/png")})
    assert r.status_code == 200, r.text
    p = r.json()["proof"][0]
    assert p["sha256"] == hashlib.sha256(PNG).hexdigest() and p["level"] == "E1" and p["type"] == "photo"
    assert p["lat"] == 33.3062 and p["location_source"] == "device" and p["size_bytes"] == len(PNG)
    assert p["captured_at"] and p["client_captured_at"].startswith("2026-10-25T15:01:02")
    f = tc.get(f"/api/v1/proofs/{p['id']}/file")
    assert f.status_code == 200 and f.content == PNG and f.headers["x-content-sha256"] == p["sha256"]
    assert "attachment" in tc.get(f"/api/v1/proofs/{p['id']}/file?download=true").headers["content-disposition"]
    ev = tc.get("/api/v1/accounts/acct-p1/evidence").json()
    assert ev["level_mix"] == {"E1": 1} and ev["proofs"][0]["file_url"].endswith("/file")


def test_tampered_blob_is_detected(client):
    tc, tasks, root = client
    t = task_with(tasks, "hose_age")
    p = tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("a.png", PNG, "image/png")}).json()["proof"][0]
    next((root / "blobs").rglob(p["id"])).write_bytes(PNG + b"x")
    assert tc.get(f"/api/v1/proofs/{p['id']}/file").status_code == 409


def test_e1_requires_a_file_and_e0_rejects_one(client):
    tc, tasks, _ = client
    t = task_with(tasks, "hose_age")
    assert tc.post(f"/api/v1/tasks/{t['id']}/complete", json={"level": "E1"}).status_code == 409
    assert tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E0"}, files={"file": ("a.png", PNG, "image/png")}).status_code == 415


def test_file_type_is_sniffed_not_trusted(client):
    tc, tasks, _ = client
    t = task_with(tasks, "hose_age")
    bad = tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("x.png", b"<html>nope</html>", "image/png")})
    assert bad.status_code == 415
    pdf_as_photo = tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("x.pdf", PDF, "application/pdf")})
    assert pdf_as_photo.status_code == 415


def test_document_proof_pdf_for_e2(client):
    tc, tasks, _ = client
    t = task_with(tasks, "water_heater_age")
    r = tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E2"}, files={"file": ("invoice.pdf", PDF, "application/pdf")})
    assert r.status_code == 200 and r.json()["proof"][0]["type"] == "document"


def test_size_limit_and_bad_coordinates(client):
    tc, tasks, _ = client
    t = task_with(tasks, "hose_age")
    big = PNG + b"0" * 8_000_001
    assert tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1"}, files={"file": ("a.png", big, "image/png")}).status_code == 413
    assert tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1", "lat": "95", "lon": "0"}, files={"file": ("a.png", PNG, "image/png")}).status_code == 422
    assert tc.post(f"/api/v1/tasks/{t['id']}/complete", data={"level": "E1", "lat": "10"}, files={"file": ("a.png", PNG, "image/png")}).status_code == 422


def test_e0_attestation_has_no_file_and_hash(client):
    tc, tasks, _ = client
    t = task_with(tasks, "know_shutoff")
    p = tc.post(f"/api/v1/tasks/{t['id']}/complete", json={"level": "E0"}).json()["proof"][0]
    assert len(p["sha256"]) == 64 and p["uri"] is None
    assert tc.get(f"/api/v1/proofs/{p['id']}/file").status_code == 404
