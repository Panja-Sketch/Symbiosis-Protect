"""Role views (Agent, Underwriter) and the sharing rules behind them.

Demo-grade authorization: the role comes from the X-Demo-Role header set by the web app from the signed demo-identity cookie.
A real deployment replaces this with Firebase Auth (AUTH_MODE=firebase). The privacy rule below is enforced here, in the API,
not only in the UI: private items never leave this module for the agent or underwriter."""

import hashlib
import io
import json
import re
import uuid
import zipfile
from datetime import datetime, timedelta

from app import models as m
from app.ribbon import build_ribbon

ROLES = ("policyholder", "agent", "underwriter")


def shared_task(t: dict) -> bool:
    """Visible to agent/underwriter: owner-shared items and anything the insurer/agent issued. Declined items are never visible."""
    return t["status"] != "declined" and (t["visibility"] == "shared" or t["source"] in ("insurer", "agent"))


def shared_tasks(store, account_id: str) -> list[dict]:
    return [t for t in store.list("tasks", account_id=account_id) if shared_task(t)]


def shared_history(store, account_id: str) -> list[dict]:
    return [h for h in store.list("task_history", account_id=account_id) if h["visibility"] == "shared" and h["status"] != "declined"]


def shared_proofs(store, account_id: str) -> list[dict]:
    return [p for p in store.list("proofs", account_id=account_id) if p.get("visibility") == "shared"]


def shared_cases(store, account_id: str) -> list[dict]:
    ok = {t["id"] for t in shared_tasks(store, account_id)}
    return [c for c in store.list("cases", account_id=account_id) if set(c["task_ids"]) & ok]


def completion(store, account_id: str) -> dict:
    live = shared_tasks(store, account_id)
    hist = shared_history(store, account_id)
    done = sum(t["status"] == "done" for t in live) + sum(h["status"] == "done" for h in hist)
    applicable = sum(t["status"] in ("open", "done", "expired", "deferred") for t in live) + sum(h["status"] in ("done", "expired") for h in hist)
    return {"done": done, "applicable": applicable, "pct": round(100 * done / applicable) if applicable else None}


def proof_mix(store, account_id: str) -> dict[str, int]:
    mix: dict[str, int] = {}
    for p in shared_proofs(store, account_id):
        mix[p["level"]] = mix.get(p["level"], 0) + 1
    for h in shared_history(store, account_id):
        if h["status"] == "done" and h.get("proof_level"):
            mix[h["proof_level"]] = mix.get(h["proof_level"], 0) + 1
    return dict(sorted(mix.items()))


def numbers_preserved(original: str, rewritten: str) -> bool:
    nums = lambda t: sorted(re.findall(r"\d[\d,\.]*", t))  # noqa: E731
    return nums(original) == nums(rewritten)


def talking_points(c, account_id: str) -> list[str]:
    s = c.store
    acct = s.get("accounts", account_id)
    pol = s.list("policies", account_id=account_id)[0]
    pts = []
    comp = completion(s, account_id)
    if comp["applicable"]:
        pts.append(f"{acct['display_name']} completed {comp['done']} of {comp['applicable']} shared prevention tasks ({comp['pct']}%) with evidence on file.")
    else:
        pts.append(f"{acct['display_name']} has not shared prevention tasks yet; ask about enabling sharing for the renewal conversation.")
    missing = [e["name_plain"] for e in pol["endorsements"] if not e["present"]]
    if missing:
        pts.append("Coverage gaps worth raising: " + "; ".join(missing) + " (not currently on the policy).")
    claims = s.list("claims", policy_id=pol["id"])
    if claims:
        top = max(claims, key=lambda x: x["paid_usd"])
        pts.append(f"Prior claim history (synthetic): {len(claims)} claim(s); largest was {top['peril']} on {top['date']} (${top['paid_usd']:,}).")
    cases = shared_cases(s, account_id)
    verified = sum(x["state"] == "verified" for x in cases)
    if cases:
        pts.append(f"Water/temperature sensing: {len(cases)} case(s), {verified} verified by sensor readings (simulated devices).")
    return pts


def build_zip(files: dict[str, bytes], meta: dict) -> tuple[bytes, dict]:
    """ZIP with manifest.json whose own SHA-256 is returned separately (manifest_sha256) so the package can be verified."""
    manifest_files = [{"path": path, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} for path, data in sorted(files.items())]
    manifest = {**meta, "files": manifest_files, "hash_algorithm": "SHA-256"}
    mbytes = json.dumps(manifest, indent=1, sort_keys=True, default=str).encode()
    digest = hashlib.sha256(mbytes).hexdigest()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", mbytes)
        z.writestr("manifest.sha256", f"{digest}  manifest.json\n")
        for path, data in sorted(files.items()):
            z.writestr(path, data)
    return buf.getvalue(), {"manifest_sha256": digest, "files": manifest_files}


def export_package(c, policy_id: str, role: str, now: datetime) -> tuple[bytes, m.EvidencePackage]:
    s = c.store
    pol = s.get("policies", policy_id)
    if not pol:
        raise KeyError(policy_id)
    account_id = pol["account_id"]
    scoped = role != "policyholder"
    tasks = shared_tasks(s, account_id) if scoped else s.list("tasks", account_id=account_id)
    proofs = shared_proofs(s, account_id) if scoped else s.list("proofs", account_id=account_id)
    hist = shared_history(s, account_id) if scoped else s.list("task_history", account_id=account_id)
    cases = shared_cases(s, account_id) if scoped else s.list("cases", account_id=account_id)
    files: dict[str, bytes] = {}
    dumps = lambda o: json.dumps(o, indent=1, sort_keys=True, default=str).encode()  # noqa: E731
    files["tasks.json"] = dumps(tasks)
    files["task_history.json"] = dumps(hist)
    files["proofs.json"] = dumps([{k: v for k, v in p.items() if k != "uri"} for p in proofs])
    for p in proofs:
        if p.get("uri"):
            files[f"proof_files/{p['id']}_{p.get('filename') or 'file'}"] = c.storage.read(p["uri"])
    for case in cases:
        files[f"cases/{case['id']}.json"] = dumps({"case": case, "evidence": s.get("case_evidence", case["id"])})
    files["README.txt"] = (
        "Evidence package (demo). Every file is listed in manifest.json with its SHA-256; manifest.sha256 is the hash of manifest.json.\n"
        "Data is SYNTHETIC or SIMULATED unless a task says LIVE. Scope: "
        + ("shared and insurer-issued items only; private items are excluded.\n" if scoped else "all items owned by the policyholder.\n")).encode()
    pid = f"pkg-{uuid.uuid4().hex[:8]}"
    meta = {"package_id": pid, "policy_id": policy_id, "account_id": account_id, "scope": "shared_only" if scoped else "all",
            "created_at": now.isoformat(), "created_by_role": role, "provenance": "SYNTHETIC"}
    blob, info = build_zip(files, meta)
    pkg = m.EvidencePackage(id=pid, policy_id=policy_id, account_id=account_id, scope=meta["scope"], files=info["files"],
                            manifest_sha256=info["manifest_sha256"], created_at=now, created_by_role=role,
                            shared_with=[role] if scoped else [])
    c.storage.save(f"packages/{pid}.zip", blob, "application/zip")
    s.put("evidence_packages", pid, pkg.model_dump(mode="json"))
    return blob, pkg


def client_row(c, account_id: str, now: datetime) -> dict:
    s = c.store
    acct = s.get("accounts", account_id)
    pol = s.list("policies", account_id=account_id)[0]
    loc = m.Location(**s.list("locations", account_id=account_id)[0])
    tasks = shared_tasks(s, account_id)
    open_high = [{"id": t["id"], "title": t["title"], "source": t["source"], "provenance": t["provenance"]}
                 for t in tasks if t["status"] == "open" and t["priority"] == "high"]
    stamps = [t["closed_at"] or t["opened_at"] for t in tasks] + [h["closed_at"] for h in shared_history(s, account_id)]
    try:
        forecast, alerts = c.weather.forecast(loc), c.weather.active_alerts(loc)
        err = None
    except Exception as e:  # noqa: BLE001
        forecast, alerts, err = None, [], f"weather unavailable: {e.__class__.__name__}"
    ribbon = build_ribbon(forecast, alerts, [], now.astimezone(loc_tz(loc)).date(), c.config.thresholds["risk_ribbon"])
    devices = s.list("devices", location_id=loc.id)
    cases = shared_cases(s, account_id)
    return {
        "account_id": account_id, "display_name": acct["display_name"], "headline": acct["headline"], "persona_id": acct["persona_id"],
        "lob": pol["lob"], "product_label": pol["product_label"], "preview_flag": pol["preview_flag"], "city": loc.city,
        "county": loc.county, "agent_id": acct["agent_id"], "shares_by_default": acct["preferences"].get("share_default", True),
        "open_high_priority": open_high, "completion": completion(s, account_id), "proof_mix": proof_mix(s, account_id),
        "last_activity": max(stamps) if stamps else None,
        "sense": {"connected": sum(d["status"] == "connected" for d in devices), "available": len(devices),
                  "active_cases": [x["id"] for x in cases if x["state"] != "verified"],
                  "verified_cases": sum(x["state"] == "verified" for x in cases)},
        "exposure": {"active_alerts": [{"event": a.event, "provenance": a.provenance, "ends": a.ends} for a in alerts],
                     "high_risk_days": [d["date"] for d in ribbon["days"] if d["risk"] == "high"],
                     "forecast_provenance": forecast.provenance if forecast else None, "error": err},
        "renewal_points": talking_points(c, account_id), "renewal_points_provenance": "SYNTHETIC",
    }


def loc_tz(loc: m.Location):
    from zoneinfo import ZoneInfo

    return ZoneInfo(loc.time_zone)


def issue_task(c, account_id: str, role: str, body: dict, now: datetime) -> dict:
    s = c.store
    pol = s.list("policies", account_id=account_id)[0]
    loc = s.list("locations", account_id=account_id)[0]
    codes = {x["code"] for k in ("coverages", "endorsements", "exclusions_plain") for x in pol[k]}
    src = "insurer" if role == "underwriter" else "agent"
    t = m.Task(
        id=f"task-{src}-{uuid.uuid4().hex[:8]}", rule_id=f"{src}.recommendation", account_id=account_id, policy_id=pol["id"],
        location_id=loc["id"], source=src, title=body["title"], why=body["why"], steps=body["steps"], priority=body.get("priority", "medium"),
        score=9.0, est_minutes=body.get("est_minutes"), peril=body.get("peril", "water"),
        coverage_codes=[x for x in body.get("coverage_codes", []) if x in codes], proof_default_level=body.get("proof_default_level", "E1"),
        proof_accepted=body.get("proof_accepted", ["E0", "E1", "E2"]), bucket="do_now", opened_at=now,
        due_at=now + timedelta(days=body.get("due_in_days", 14)), expires_after_hours=24 * 60, cooldown_days=0, relevant_date=now.date(),
        visibility="shared", provenance="SYNTHETIC",
        inputs_snapshot={"reasons": [f"Issued by your {'insurer risk-control team' if src == 'insurer' else 'agent'} on {now.date()}."],
                         "alert_ids": [], "asset_ids": [], "asset_facts": {}, "input_provenance": ["SYNTHETIC"],
                         "evaluated_at": now.isoformat(), "weather": {"provenance": None, "sources": []}, "coverage_keys": []})
    s.put("tasks", t.id, t.model_dump(mode="json"))
    acct = s.get("accounts", account_id)
    c.engine._raise(account_id, acct, now, kind="agent", severity="warning",
                    title=f"New recommendation from your {'insurer' if src == 'insurer' else 'agent'}: {t.title}", body=t.why[:240],
                    deep_link=f"/tasks?open={t.id}", dedupe=f"issued:{t.id}", provenance="SYNTHETIC", summary={"alerts": []})
    return t.model_dump(mode="json")
