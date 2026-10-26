"""/api/v1 routes (Phase 2 surface). Every response that carries data includes a `provenance`."""

import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel

from app import models as m
from app.adapters import scenario
from app.config import get_settings
from app.deps import Container, get_container
from app.ribbon import build_ribbon

router = APIRouter()


def C() -> Container:
    return get_container()


def _must(store, col, id):
    doc = store.get(col, id)
    if not doc:
        raise HTTPException(404, f"{col}/{id} not found")
    return doc


def _loc(c: Container, location_id: str) -> m.Location:
    return m.Location(**_must(c.store, "locations", location_id))


@router.get("/personas", tags=["accounts"])
def personas(c: Container = Depends(C)):
    out = []
    for a in sorted(c.store.list("accounts"), key=lambda a: a["persona_id"]):
        pol = c.store.list("policies", account_id=a["id"])[0]
        loc = c.store.list("locations", account_id=a["id"])[0]
        out.append({**a, "policy_id": pol["id"], "lob": pol["lob"], "product_label": pol["product_label"],
                    "preview_flag": pol["preview_flag"], "location_id": loc["id"], "city": loc["city"],
                    "provenance": "SYNTHETIC"})
    return out


@router.get("/accounts/{account_id}", tags=["accounts"])
def account(account_id: str, c: Container = Depends(C)):
    a = _must(c.store, "accounts", account_id)
    agent = c.store.get("agents", a["agent_id"])
    return {**a, "agent": agent, "locations": c.store.list("locations", account_id=account_id)}


@router.get("/accounts/{account_id}/policies", tags=["policies"])
def policies(account_id: str, c: Container = Depends(C)):
    _must(c.store, "accounts", account_id)
    return c.store.list("policies", account_id=account_id)


@router.get("/policies/{policy_id}", tags=["policies"])
def policy(policy_id: str, c: Container = Depends(C)):
    p = _must(c.store, "policies", policy_id)
    notes = {n["key"]: n for n in c.store.list("coverage_notes")}
    return {**p, "coverage_notes": notes}


@router.get("/locations/{location_id}/weather", tags=["weather"])
def weather(location_id: str, c: Container = Depends(C)):
    loc = _loc(c, location_id)
    try:
        f = c.weather.forecast(loc)
        return {**f.model_dump(mode="json", exclude={"hourly"}), "hourly_count": len(f.hourly),
                "now_local": c.engine.now(loc.time_zone).isoformat(), "error": None}
    except Exception as e:  # noqa: BLE001
        return {"location_id": location_id, "daily": [], "provenance": None, "error": f"weather unavailable: {e}",
                "now_local": c.engine.now(loc.time_zone).isoformat()}


@router.get("/locations/{location_id}/alerts", tags=["weather"])
def location_alerts(location_id: str, c: Container = Depends(C)):
    loc = _loc(c, location_id)
    try:
        return {"alerts": [a.model_dump(mode="json") for a in c.weather.active_alerts(loc)], "error": None}
    except Exception as e:  # noqa: BLE001
        return {"alerts": [], "error": f"alerts unavailable: {e}"}


@router.get("/locations/{location_id}/history", tags=["history"])
def history(location_id: str, c: Container = Depends(C)):
    loc = _loc(c, location_id)
    storms = c.history.storms(loc)
    nri = c.history.nri(loc)
    tract = nri.get("tract") or nri["county"]
    return {"weather": c.history.stats(loc), "storm_events": storms,
            "risk_index": {"tract_id": nri.get("tract_id"), "risk_rating": tract["risk_rating"],
                           "social_vulnerability": tract["social_vulnerability"], "hazards": tract["hazards"],
                           "county_risk_rating": nri["county"]["risk_rating"]},
            "provenance": "HISTORIC"}


@router.get("/locations/{location_id}/risk-ribbon", tags=["weather"])
def risk_ribbon(location_id: str, c: Container = Depends(C)):
    loc = _loc(c, location_id)
    now = c.engine.now(loc.time_zone)
    try:
        forecast, alerts = c.weather.forecast(loc), c.weather.active_alerts(loc)
    except Exception:  # noqa: BLE001
        forecast, alerts = None, []
    tasks = c.store.list("tasks", location_id=location_id)
    return build_ribbon(forecast, alerts, tasks, now.date(), c.config.thresholds["risk_ribbon"])


@router.get("/accounts/{account_id}/tasks", tags=["tasks"])
def tasks(account_id: str, status: str | None = Query(None, description="do_now|coming_up|open|done|deferred|declined|expired"),
          c: Container = Depends(C)):
    _must(c.store, "accounts", account_id)
    rows = c.engine.tasks(account_id, status)
    hist = [h for h in c.store.list("task_history", account_id=account_id)] if status in (None, "done") else []
    return {"tasks": rows, "history": hist,
            "readiness": _readiness(c, account_id)}


def _readiness(c: Container, account_id: str) -> dict:
    rows = c.store.list("tasks", account_id=account_id)
    done = sum(t["status"] == "done" for t in rows)
    applicable = sum(t["status"] in ("open", "done", "deferred") for t in rows)
    return {"done": done, "applicable": applicable, "ratio": round(done / applicable, 3) if applicable else 1.0}


class CompleteBody(BaseModel):
    level: str = "E0"
    lat: float | None = None
    lon: float | None = None


@router.post("/tasks/{task_id}/complete", tags=["tasks"])
def complete(task_id: str, body: CompleteBody, c: Container = Depends(C)):
    try:
        return c.engine.complete(task_id, body.level, extra=body.model_dump(exclude={"level"}, exclude_none=True))
    except KeyError:
        raise HTTPException(404, "task not found") from None
    except ValueError as e:
        raise HTTPException(409, str(e)) from None


class DeferBody(BaseModel):
    hours: int = 24


@router.post("/tasks/{task_id}/defer", tags=["tasks"])
def defer(task_id: str, body: DeferBody | None = None, c: Container = Depends(C)):
    try:
        return c.engine.defer(task_id, (body or DeferBody()).hours)
    except KeyError:
        raise HTTPException(404, "task not found") from None
    except ValueError as e:
        raise HTTPException(409, str(e)) from None


@router.post("/tasks/{task_id}/decline", tags=["tasks"])
def decline(task_id: str, c: Container = Depends(C)):
    try:
        return c.engine.decline(task_id)
    except KeyError:
        raise HTTPException(404, "task not found") from None
    except ValueError as e:
        raise HTTPException(409, str(e)) from None


@router.get("/alerts", tags=["alerts"])
def alerts(account_id: str, kind: str | None = None, c: Container = Depends(C)):
    rows = c.store.list("alerts", account_id=account_id)
    rows = [a for a in rows if kind is None or a["kind"] == kind]
    return sorted(rows, key=lambda a: a["created_at"], reverse=True)


@router.post("/alerts/{alert_id}/read", tags=["alerts"])
def alert_read(alert_id: str, c: Container = Depends(C)):
    a = _must(c.store, "alerts", alert_id)
    a["read_at"] = c.engine.now().isoformat()
    c.store.put("alerts", alert_id, a)
    return a


@router.post("/accounts/{account_id}/evaluate", tags=["engine"])
def evaluate_account(account_id: str, c: Container = Depends(C)):
    _must(c.store, "accounts", account_id)
    return c.engine.evaluate_account(account_id)


@router.post("/internal/evaluate", tags=["engine"], description="Scheduler hook. Token-protected unless in demo mode.")
def internal_evaluate(x_scheduler_token: str | None = Header(None), c: Container = Depends(C)):
    s = get_settings()
    if not s.demo_mode and not (x_scheduler_token and hmac.compare_digest(x_scheduler_token, s.session_secret)):
        raise HTTPException(401, "scheduler token required")
    return {"evaluated": c.engine.evaluate_all()}


def _demo_only():
    if not get_settings().demo_mode:
        raise HTTPException(404, "not found")


class InjectBody(BaseModel):
    kind: str


@router.post("/director/inject", tags=["director"])
def director_inject(body: InjectBody, c: Container = Depends(C)):
    _demo_only()
    try:
        state = scenario.inject(c.store, body.kind, c.engine.now())
    except KeyError:
        raise HTTPException(422, f"unknown scenario; choose from {sorted(scenario.SCENARIOS)}") from None
    return {"state": state, "evaluated": c.engine.evaluate_all(), "provenance": "SIMULATED"}


class TimeTravelBody(BaseModel):
    to: datetime | None = None


@router.post("/director/time-travel", tags=["director"])
def director_time_travel(body: TimeTravelBody, c: Container = Depends(C)):
    _demo_only()
    state = scenario.time_travel(c.store, body.to)
    return {"state": state, "evaluated": c.engine.evaluate_all(), "provenance": "SIMULATED"}


@router.post("/director/reset", tags=["director"])
def director_reset(c: Container = Depends(C)):
    _demo_only()
    for col in ("tasks", "alerts", "events", "outbox"):
        for doc in c.store.list(col):
            c.store.delete(col, doc["id"])
    scenario.reset(c.store)
    return {"evaluated": c.engine.evaluate_all(), "provenance": "SIMULATED"}
