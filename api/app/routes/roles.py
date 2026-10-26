"""Agent / Underwriter / sharing routes. See app/roles.py for the privacy rules these endpoints rely on."""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field

from app import roles
from app.deps import Container
from app.routes.v1 import C

router = APIRouter()


def role_of(x_demo_role: str | None = Header(None)) -> str:
    r = x_demo_role or "policyholder"
    if r not in roles.ROLES:
        raise HTTPException(400, "unknown role")
    return r


def need(role: str, *allowed: str) -> None:
    if role not in allowed:
        raise HTTPException(403, f"this view is for: {', '.join(allowed)}")


def now() -> datetime:
    return datetime.now(UTC)


def acct_or_404(c: Container, account_id: str) -> dict:
    a = c.store.get("accounts", account_id)
    if not a:
        raise HTTPException(404, "account not found")
    return a


@router.get("/agent/book", tags=["agent"])
def agent_book(agent_id: str | None = None, role: str = Depends(role_of), c: Container = Depends(C)):
    need(role, "agent")
    rows = [a for a in c.store.list("accounts") if agent_id is None or a["agent_id"] == agent_id]
    book = [roles.client_row(c, a["id"], now()) for a in sorted(rows, key=lambda a: a["persona_id"])]
    for b in book:
        b["agent"] = c.store.get("agents", b["agent_id"])
    return {"clients": book, "visibility_note": "Only items the policyholder shared, plus items issued by the insurer or agent.",
            "provenance": "SYNTHETIC"}


@router.get("/underwriting/portfolio", tags=["underwriting"])
def portfolio(role: str = Depends(role_of), c: Container = Depends(C)):
    need(role, "underwriter")
    accts = sorted(c.store.list("accounts"), key=lambda a: a["persona_id"])
    rows = [roles.client_row(c, a["id"], now()) for a in accts]
    done = sum(r["completion"]["done"] for r in rows)
    applicable = sum(r["completion"]["applicable"] for r in rows)
    mix: dict[str, int] = {}
    for r in rows:
        for k, v in r["proof_mix"].items():
            mix[k] = mix.get(k, 0) + v
    by_county: dict[str, list[str]] = {}
    for r in rows:
        for a in r["exposure"]["active_alerts"]:
            by_county.setdefault(r["county"], []).append(a["event"])
    cases = [x for a in accts for x in roles.shared_cases(c.store, a["id"])]
    participating = [r for r in rows if r["shares_by_default"]]
    return {
        "tiles": {
            "participation": {"participating": len(participating), "total": len(rows),
                              "pct": round(100 * len(participating) / len(rows)) if rows else None},
            "task_completion": {"done": done, "applicable": applicable, "pct": round(100 * done / applicable) if applicable else None},
            "proof_mix": dict(sorted(mix.items())),
            "alerts_by_county": {k: sorted(set(v)) for k, v in by_county.items()},
            "sense_cases": {"total": len(cases), "active": sum(x["state"] != "verified" for x in cases),
                            "verified": sum(x["state"] == "verified" for x in cases)},
        },
        "accounts": rows, "visibility_note": "Shared and insurer-issued items only. Private and declined items are never included.",
        "provenance": "SYNTHETIC",
    }


@router.get("/underwriting/accounts/{account_id}", tags=["underwriting"])
def underwriting_account(account_id: str, role: str = Depends(role_of), c: Container = Depends(C)):
    need(role, "underwriter", "agent")
    acct = acct_or_404(c, account_id)
    s = c.store
    pol = s.list("policies", account_id=account_id)[0]
    return {
        "row": roles.client_row(c, account_id, now()), "policy": {"id": pol["id"], "lob": pol["lob"], "product_label": pol["product_label"],
                                                                 "coverages": pol["coverages"], "endorsements": pol["endorsements"]},
        "tasks": sorted(roles.shared_tasks(s, account_id), key=lambda t: t["opened_at"], reverse=True),
        "history": roles.shared_history(s, account_id),
        "proofs": [{k: v for k, v in p.items() if k != "uri"} | {"file_url": f"/api/v1/proofs/{p['id']}/file" if p.get("uri") else None}
                   for p in roles.shared_proofs(s, account_id)],
        "cases": roles.shared_cases(s, account_id), "claims": s.list("claims", policy_id=pol["id"]),
        "packages": sorted(s.list("evidence_packages", account_id=account_id), key=lambda p: p["created_at"], reverse=True),
        "account": {"id": acct["id"], "display_name": acct["display_name"], "persona_id": acct["persona_id"]},
        "provenance": "SYNTHETIC",
    }


class IssueBody(BaseModel):
    account_id: str
    title: str = Field(min_length=5, max_length=140)
    why: str = Field(min_length=10, max_length=600)
    steps: list[str] = Field(min_length=1, max_length=8)
    priority: str = "medium"
    due_in_days: int = Field(14, ge=1, le=120)
    proof_accepted: list[str] = ["E0", "E1", "E2"]


@router.post("/tasks/issue", tags=["tasks"], description="Insurer-issued (underwriter) or agent-issued recommendation. Never hidden by the Do-now cap.")
def issue(body: IssueBody, role: str = Depends(role_of), c: Container = Depends(C)):
    need(role, "underwriter", "agent")
    acct_or_404(c, body.account_id)
    if body.priority not in ("high", "medium", "low"):
        raise HTTPException(422, "priority must be high, medium or low")
    t = roles.issue_task(c, body.account_id, role, body.model_dump(), now())
    c.engine.rebucket(body.account_id)
    return t


class VisibilityBody(BaseModel):
    visibility: str


@router.patch("/tasks/{task_id}/visibility", tags=["sharing"])
def set_visibility(task_id: str, body: VisibilityBody, c: Container = Depends(C)):
    if body.visibility not in ("private", "shared"):
        raise HTTPException(422, "visibility must be private or shared")
    t = c.store.get("tasks", task_id)
    if not t:
        raise HTTPException(404, "task not found")
    if t["source"] != "rule" and body.visibility == "private":
        raise HTTPException(409, "items issued by your insurer or agent are always visible to them")
    if t["status"] == "declined" and body.visibility == "shared":
        raise HTTPException(409, "declined items stay private")
    t["visibility"] = body.visibility
    c.store.put("tasks", task_id, t)
    for p in t["proof"]:
        doc = c.store.get("proofs", p["id"])
        if doc:
            doc["visibility"] = body.visibility
            c.store.put("proofs", p["id"], doc)
    return t


class PrefsBody(BaseModel):
    share_default: bool | None = None
    channels: list[str] | None = None
    quiet_hours: tuple[str, str] | None = None


@router.patch("/accounts/{account_id}/preferences", tags=["sharing"])
def set_prefs(account_id: str, body: PrefsBody, c: Container = Depends(C)):
    a = acct_or_404(c, account_id)
    if body.channels is not None and (not body.channels or not set(body.channels) <= {"in_app", "email"}):
        raise HTTPException(422, "channels must be a non-empty subset of in_app, email")
    patch = body.model_dump(exclude_none=True)
    a["preferences"].update(patch)
    c.store.put("accounts", account_id, a)
    return a["preferences"]


@router.post("/evidence/{policy_id}/export", tags=["evidence"],
             description="ZIP with manifest.json (SHA-256 per file) and manifest.sha256. Underwriter/agent exports contain shared items only.")
def export(policy_id: str, role: str = Depends(role_of), c: Container = Depends(C)):
    try:
        blob, pkg = roles.export_package(c, policy_id, role, now())
    except KeyError:
        raise HTTPException(404, "policy not found") from None
    return Response(blob, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="evidence_{policy_id}_{pkg.id}.zip"',
        "X-Manifest-SHA256": pkg.manifest_sha256, "X-Package-Id": pkg.id, "X-Package-Scope": pkg.scope})


@router.get("/evidence/packages/{package_id}/download", tags=["evidence"])
def download_package(package_id: str, c: Container = Depends(C)):
    pkg = c.store.get("evidence_packages", package_id)
    if not pkg:
        raise HTTPException(404, "package not found")
    blob = c.storage.read(f"packages/{package_id}.zip")
    return Response(blob, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="evidence_{pkg["policy_id"]}_{package_id}.zip"', "X-Manifest-SHA256": pkg["manifest_sha256"]})
