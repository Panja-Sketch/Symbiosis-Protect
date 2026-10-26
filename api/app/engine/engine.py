"""Engine: evaluate rules per account, reconcile task lifecycle, bucket, raise alerts."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app import models as m
from app.adapters.scenario import clock
from app.engine import prioritize
from app.engine.context import Ctx
from app.engine.playbooks import Config, Rule
from app.engine.rules import Candidate, evaluate_all, render

ALERT_GROUPS = ("heat", "freeze", "thunderstorm", "flood", "dust")
SEVERITY = {"Extreme": "critical", "Severe": "warning", "Moderate": "watch", "Minor": "info"}


class Engine:
    def __init__(self, store, weather, history, notifier, rules: list[Rule], config: Config):
        self.store, self.weather, self.history = store, weather, history
        self.notifier, self.rules, self.config = notifier, rules, config
        self.rule_by_id = {r.id: r for r in rules}

    # ---- context ----------------------------------------------------------------------------
    def now(self, tz: str | None = None) -> datetime:
        n = clock(self.store)
        return n.astimezone(ZoneInfo(tz)) if tz else n

    def build_ctx(self, loc: m.Location, policy: m.Policy, now: datetime) -> Ctx:
        s = self.store
        forecast, alerts, err = None, [], None
        try:
            forecast = self.weather.forecast(loc)
        except Exception as e:  # noqa: BLE001 - never let an outage stop the engine
            err = f"forecast: {e.__class__.__name__}"
        try:
            alerts = self.weather.active_alerts(loc)
        except Exception as e:  # noqa: BLE001
            err = (err + "; " if err else "") + f"alerts: {e.__class__.__name__}"
        return Ctx(
            now=now.astimezone(ZoneInfo(loc.time_zone)), loc=loc,
            profile=m.PropertyProfile(**s.get("property_profiles", loc.id)),
            assets=[m.Asset(**a) for a in s.list("assets", location_id=loc.id)],
            policy=policy, forecast=forecast, alerts=alerts,
            history=s.get("derived", f"history_{loc.id}") or {},
            nri=(s.get("derived", "nri_az") or {}).get("locations", {}).get(loc.id, {}),
            claims=[m.Claim(**c) for c in s.list("claims", policy_id=policy.id)],
            events=s.list("events", location_id=loc.id), config=self.config, weather_error=err)

    def account_parts(self, account_id: str):
        locs = [m.Location(**x) for x in self.store.list("locations", account_id=account_id)]
        pols = [m.Policy(**x) for x in self.store.list("policies", account_id=account_id)]
        return locs, pols

    # ---- evaluation + lifecycle ---------------------------------------------------------------
    def evaluate_account(self, account_id: str) -> dict:
        locs, pols = self.account_parts(account_id)
        policy = pols[0]
        summary = {"account_id": account_id, "created": [], "refreshed": [], "expired": [], "alerts": [],
                   "weather_errors": []}
        for loc in locs:
            now = self.now(loc.time_zone)
            ctx = self.build_ctx(loc, policy, now)
            if ctx.weather_error:
                summary["weather_errors"].append(ctx.weather_error)
            self._reconcile(ctx, account_id, summary)
            self._weather_alerts(ctx, account_id, summary)
        self.rebucket(account_id)
        return summary

    def evaluate_all(self) -> list[dict]:
        return [self.evaluate_account(a["id"]) for a in self.store.list("accounts")]

    def _closed_before(self, account_id: str, loc_id: str) -> list[dict]:
        done = [t for t in self.store.list("tasks", account_id=account_id)
                if t["status"] in ("done", "declined") and t["location_id"] == loc_id]
        hist = [{**h, "rule_id": h["rule_id"]} for h in self.store.list("task_history", account_id=account_id)
                if h["status"] in ("done", "declined")]
        return done + hist

    def _last_closed(self, closed: list[dict], cand: Candidate, tz, now) -> datetime | None:
        best = None
        for t in closed:
            if t["rule_id"] != cand.rule.id:
                continue
            if cand.asset and t.get("asset_id") and t["asset_id"] != cand.asset.id:
                continue
            ts = t.get("closed_at")
            ts = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
            if ts is None:
                continue
            ts = ts.replace(tzinfo=tz) if ts.tzinfo is None else ts
            if ts > now:
                continue  # closed 'in the future' relative to Director time-travel
            best = ts if best is None or ts > best else best
        return best

    def _reconcile(self, ctx: Ctx, account_id: str, summary: dict) -> None:
        cands = evaluate_all(ctx, self.rules)
        tasks = [t for t in self.store.list("tasks", account_id=account_id) if t["location_id"] == ctx.loc.id]
        open_by_key = {(t["rule_id"], t.get("asset_id") or "-"): t for t in tasks
                       if t["status"] in ("open", "deferred") and t["source"] == "rule"}
        closed = self._closed_before(account_id, ctx.loc.id)
        live_keys = set()
        for c in cands:
            key = c.key
            live_keys.add(key)
            last = self._last_closed(closed, c, ctx.tz, ctx.now)
            existing = open_by_key.get(key)
            if existing:
                if existing["status"] == "deferred":
                    until = existing.get("defer_until")
                    until = datetime.fromisoformat(until) if isinstance(until, str) else until
                    if until and until <= ctx.now:
                        existing["status"], existing["defer_until"] = "open", None
                    else:
                        self.store.put("tasks", existing["id"], existing)
                        continue
                existing.update(self._refresh(ctx, c, last))
                self.store.put("tasks", existing["id"], existing)
                summary["refreshed"].append(existing["id"])
                continue
            if last and (ctx.now - last).days < c.rule.cooldown_days:
                continue  # in cooldown after a completed/declined task
            task = self._new_task(ctx, account_id, c, last)
            self.store.put("tasks", task.id, task.model_dump(mode="json"))
            summary["created"].append(task.id)
        for key, t in open_by_key.items():
            if key in live_keys:
                continue
            opened = datetime.fromisoformat(t["opened_at"])
            if ctx.now >= opened + timedelta(hours=t["expires_after_hours"]):
                t.update(status="expired", closed_at=ctx.now.isoformat())
                self.store.put("tasks", t["id"], t)
                summary["expired"].append(t["id"])

    def _snapshot(self, ctx: Ctx, c: Candidate) -> dict:
        daily = [d.model_dump(mode="json") for d in (ctx.forecast.daily[:7] if ctx.forecast else [])]
        return {
            "reasons": c.hit.reasons, "alert_ids": c.hit.alert_ids, "asset_ids": c.hit.asset_ids,
            "asset_facts": {k: c.facts.get(k) for k in ("asset_label", "age_text", "age_years", "threshold_years",
                                                        "last_service", "months_since_service", "units")
                            if c.facts.get(k) is not None},
            "weather": {"forecast_days": daily, "provenance": ctx.forecast.provenance if ctx.forecast else None,
                        "sources": ctx.forecast.sources if ctx.forecast else []},
            "coverage_keys": ([c.rule.coverage_note_key] if c.rule.coverage_note_key else []),
            "input_provenance": sorted(c.hit.provenance), "evaluated_at": ctx.now.isoformat(),
        }

    def _text(self, c: Candidate) -> dict:
        f = c.facts
        return {"title": render(c.rule.title, f), "why": render(c.rule.why_template, f),
                "steps": [render(s, f) for s in c.rule.steps]}

    def _refresh(self, ctx: Ctx, c: Candidate, last) -> dict:
        return {**self._text(c), "score": prioritize.score(ctx, c, last), "inputs_snapshot": self._snapshot(ctx, c)}

    def _new_task(self, ctx: Ctx, account_id: str, c: Candidate, last) -> m.Task:
        r = c.rule
        prov = ("SIMULATED" if "SIMULATED" in c.hit.provenance else "LIVE" if "LIVE" in c.hit.provenance
                else "HISTORIC" if c.hit.provenance == {"HISTORIC"} else "SYNTHETIC")
        policy_codes = ({x.code for x in ctx.policy.coverages} | {e.code for e in ctx.policy.endorsements}
                        | {x.code for x in ctx.policy.exclusions_plain})
        hours = c.hit.hours or 0
        return m.Task(
            id=f"task-{uuid.uuid4().hex[:10]}", rule_id=r.id, account_id=account_id, policy_id=ctx.policy.id,
            location_id=ctx.loc.id, asset_id=c.asset.id if c.asset else None, source="rule",
            priority=r.priority, est_minutes=r.est_minutes, est_cost_usd=r.est_cost_usd, peril=r.peril,
            coverage_note_key=r.coverage_note_key, coverage_codes=[x for x in r.coverage_codes if x in policy_codes],
            proof_default_level=r.proof.default_level, proof_accepted=r.proof.accepted, opened_at=ctx.now,
            due_at=ctx.now + timedelta(hours=r.expires_after_hours), expires_after_hours=r.expires_after_hours,
            cooldown_days=r.cooldown_days, relevant_date=(ctx.now + timedelta(hours=hours)).date(),
            provenance=prov, **self._refresh(ctx, c, last))

    # ---- bucketing ----------------------------------------------------------------------------
    def rebucket(self, account_id: str) -> None:
        cap = self.config.scoring["do_now_cap"]
        open_ = [t for t in self.store.list("tasks", account_id=account_id) if t["status"] == "open"]
        rule_tasks = sorted((t for t in open_ if t["source"] == "rule"), key=lambda t: -t["score"])
        ids = {t["id"] for t in rule_tasks[:cap]}
        for t in open_:
            bucket = "do_now" if (t["source"] != "rule" or t["id"] in ids) else "coming_up"
            if t.get("bucket") != bucket:
                t["bucket"] = bucket
                self.store.put("tasks", t["id"], t)

    # ---- alerts -------------------------------------------------------------------------------
    def _weather_alerts(self, ctx: Ctx, account_id: str, summary: dict) -> None:
        names = {n for g in ALERT_GROUPS for n in ctx.thresholds["nws_groups"][g]}
        acct = self.store.get("accounts", account_id)
        for a in ctx.alerts:
            if a.event not in names:
                continue
            sev = SEVERITY.get(a.severity or "", "watch")
            self._raise(account_id, acct, ctx.now, kind="weather", severity=sev, title=f"{a.event} — {ctx.loc.city}",
                        body=a.headline, deep_link="/alerts", dedupe=f"wx:{a.id}:{ctx.loc.id}",
                        provenance=a.provenance, summary=summary)
        for tid in summary["created"]:
            t = self.store.get("tasks", tid)
            if t and t["account_id"] == account_id and t["priority"] == "high":
                self._raise(account_id, acct, ctx.now, kind="task", severity="warning",
                            title=f"New task: {t['title']}", body=t["why"][:240], deep_link=f"/tasks/{tid}",
                            dedupe=f"task:{tid}", provenance=t["provenance"], summary=summary)

    def _raise(self, account_id, acct, now, *, kind, severity, title, body, deep_link, dedupe, provenance, summary):
        aid = "alert-" + hashlib.sha1(f"{account_id}|{dedupe}".encode()).hexdigest()[:12]
        if self.store.get("alerts", aid):
            return
        alert = m.Alert(id=aid, account_id=account_id, kind=kind, severity=severity, title=title, body=body,
                        deep_link=deep_link, dedupe_key=dedupe, created_at=now, provenance=provenance)
        alert.sent_channels = self.notifier.send(alert, acct, now)
        self.store.put("alerts", aid, alert.model_dump(mode="json"))
        summary["alerts"].append(aid)

    # ---- task actions -------------------------------------------------------------------------
    def get_task(self, task_id: str) -> dict:
        t = self.store.get("tasks", task_id)
        if not t:
            raise KeyError(task_id)
        return t

    def complete(self, task_id: str, level: str = "E0", by_user: str = "demo-user", extra: dict | None = None,
                 now: datetime | None = None, blob: dict | None = None, storage=None) -> dict:
        """Close a task with proof. `blob` = {data, content_type, filename} for E1/E2; E0 is a signed attestation.
        The server clock is authoritative for captured_at; the device clock is recorded separately."""
        t = self.get_task(task_id)
        if t["status"] != "open":
            raise ValueError(f"task is {t['status']}, not open")
        if level not in t["proof_accepted"]:
            raise ValueError(f"proof level {level} not accepted for this task (accepted: {t['proof_accepted']})")
        if level in ("E1", "E2") and not blob:
            raise ValueError(f"proof level {level} needs a {'photo' if level == 'E1' else 'document'} file")
        if level == "E0" and blob:
            raise ValueError("E0 is a one-tap attestation and takes no file")
        extra = extra or {}
        now = now or self.now()
        pid = f"proof-{uuid.uuid4().hex[:10]}"
        uri = None
        if blob:
            digest = hashlib.sha256(blob["data"]).hexdigest()
            key = f"proofs/{t['account_id']}/{task_id}/{pid}"
            storage.save(key, blob["data"], blob["content_type"])
            uri = key
        else:
            body = {"task_id": task_id, "level": level, "at": now.isoformat(), "by": by_user,
                    **{k: v for k, v in extra.items() if k in ("lat", "lon")}}
            digest = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        has_loc = extra.get("lat") is not None and extra.get("lon") is not None
        proof = m.Proof(
            id=pid, level=level, type=("attest" if level == "E0" else "photo" if level == "E1" else "document"),
            captured_at=now, sha256=digest, uri=uri, by_user=by_user,
            lat=extra.get("lat") if has_loc else None, lon=extra.get("lon") if has_loc else None,
            client_captured_at=extra.get("client_captured_at"), filename=(blob or {}).get("filename"),
            content_type=(blob or {}).get("content_type"), size_bytes=len(blob["data"]) if blob else None,
            location_source="device" if has_loc else "none")
        doc = proof.model_dump(mode="json")
        t["proof"].append(doc)
        t.update(status="done", closed_at=now.isoformat())
        self.store.put("tasks", task_id, t)
        self.store.put("proofs", pid, {**doc, "task_id": task_id, "account_id": t["account_id"],
                                       "task_title": t["title"], "visibility": t["visibility"]})
        self.rebucket(t["account_id"])
        return self.get_task(task_id)

    def defer(self, task_id: str, hours: int = 24) -> dict:
        t = self.get_task(task_id)
        if t["status"] != "open":
            raise ValueError(f"task is {t['status']}, not open")
        t.update(status="deferred", defer_until=(self.now() + timedelta(hours=hours)).isoformat(), bucket="coming_up")
        self.store.put("tasks", task_id, t)
        self.rebucket(t["account_id"])
        return t

    def decline(self, task_id: str) -> dict:
        t = self.get_task(task_id)
        if t["status"] not in ("open", "deferred"):
            raise ValueError(f"task is {t['status']}")
        t.update(status="declined", closed_at=self.now().isoformat(), visibility="private")
        self.store.put("tasks", task_id, t)
        self.rebucket(t["account_id"])
        return t

    def tasks(self, account_id: str, status: str | None = None) -> list[dict]:
        rows = self.store.list("tasks", account_id=account_id)
        if status in ("do_now", "coming_up"):
            rows = [t for t in rows if t["status"] == "open" and t["bucket"] == status]
        elif status:
            rows = [t for t in rows if t["status"] == status]
        return sorted(rows, key=lambda t: (t["status"] != "open", -t["score"]))
