"""Sense mode: detection -> alert -> action -> sensor-verified fix -> closed -> reopen on recurrence.

Verification is deterministic and conservative: missing or stale data is `inconclusive`, never `verified`."""

import hashlib
import json
import uuid
from datetime import datetime, timedelta

from app import models as m
from app.sense import sim

ACTIVE = ("detected", "alerted", "acting", "verifying", "not_improving", "inconclusive", "reopened")
KIND_FOR_DEVICE = {"water": "leak", "stockroom": "freeze_risk", "cooler": "cooler_temp"}
RULE_FOR_KIND = {"leak": "az.sense.leak.v1", "freeze_risk": "az.sense.freeze_risk.v1", "cooler_temp": "az.sense.cooler_temp.v1"}
NOTE_FOR_KIND = {"leak": "water_sudden_vs_gradual", "freeze_risk": "freeze_heat_condition", "cooler_temp": "spoilage_cooling_failure"}
CODES_FOR_KIND = {"leak": ["HO_WATER_SUDDEN", "DF_WATER_SUDDEN", "BOP_WATER_SUDDEN", "CRE_WATER_ESCAPE"],
                  "freeze_risk": ["BOP_FREEZE_CONDITION", "END_HEAT_MAINTAIN"],
                  "cooler_temp": ["AG_SPOILAGE", "AG_UTILITY", "END_EQUIP_BREAKDOWN"]}


class SenseError(ValueError):
    pass


class SenseService:
    def __init__(self, store, engine):
        self.store, self.engine, self.cfg = store, engine, sim.CFG

    # ---- helpers ----------------------------------------------------------------------------------------------
    def device(self, device_id: str) -> dict:
        d = self.store.get("devices", device_id)
        if not d:
            raise KeyError(device_id)
        return d

    def anomalous(self, device: dict, r: dict) -> bool:
        t = self.cfg["thresholds"]
        if device["kind"] == "water":
            return r["leak"] == t["leak_wet"] or (r["flow_lpm"] or 0) > t["idle_flow_lpm"]
        if device["kind"] == "stockroom":
            return r["temp_f"] <= t["stockroom_alert_f"]
        return r["temp_f"] >= t["cooler_alert_f"]

    def clean(self, device: dict, r: dict) -> bool:
        t = self.cfg["thresholds"]
        if device["kind"] == "water":
            return r["leak"] == 0 and (r["flow_lpm"] or 0) <= t["idle_flow_lpm"]
        if device["kind"] == "stockroom":
            return r["temp_f"] >= t["stockroom_clear_f"]
        return r["temp_f"] <= t["cooler_clear_f"]

    @staticmethod
    def _tail(rows: list[dict], pred) -> int:
        n = 0
        for r in reversed(rows):
            if not pred(r):
                break
            n += 1
        return n

    def _need(self, device: dict) -> int:
        return self.cfg["detect_consecutive"] if device["kind"] == "water" else self.cfg["thresholds"]["detect_consecutive_temp"]

    @sim.locked
    def connect(self, device_id: str, now: datetime) -> dict:
        d = self.device(device_id)
        d.update(status="connected")
        self.store.put("devices", device_id, d)
        if not sim.get_state(self.store, device_id):
            sim.init_state(self.store, d, now)
        sim.materialize(self.store, d, now)
        return d

    def _case(self, device_id: str) -> dict | None:
        cases = sorted(self.store.list("cases", device_id=device_id), key=lambda c: c["opened_at"], reverse=True)
        return cases[0] if cases else None

    def _log(self, case: dict, state: str, note: str, now: datetime, source: str = "system") -> None:
        case["state"] = state
        case["timeline"].append({"ts": now.isoformat(), "state": state, "note": note, "source": source})
        self.store.put("cases", case["id"], case)

    # ---- poll / state machine ---------------------------------------------------------------------------------
    @sim.locked
    def poll(self, device_id: str, now: datetime) -> dict:
        d = self.device(device_id)
        if d["status"] != "connected":
            return {"device": d, "case": None, "new_readings": 0}
        made = sim.materialize(self.store, d, now)
        rows = sim.readings(self.store, device_id, now - timedelta(minutes=10))
        case = self._case(device_id)
        need = self._need(d)
        tail_bad = self._tail(rows, lambda r: self.anomalous(d, r))
        if case is None or (case["state"] == "verified" and not self._in_watch(case, now)):
            if tail_bad >= need and (case is None or datetime.fromisoformat(rows[-1]["ts"]) > datetime.fromisoformat(case["verified_at"])):
                case = self._open(d, rows[-1], now)
        elif case["state"] == "verified":
            if tail_bad >= need and datetime.fromisoformat(rows[-1]["ts"]) > datetime.fromisoformat(case["verified_at"]):
                self._reopen(case, d, rows[-1], now)
        elif case["state"] == "verifying":
            self._verify(case, d, rows, now)
        return {"device": d, "case": self._case(device_id), "new_readings": len(made)}

    def _in_watch(self, case: dict, now: datetime) -> bool:
        return bool(case.get("verified_at")) and now - datetime.fromisoformat(case["verified_at"]) <= timedelta(hours=self.cfg["reopen_watch_hours"])

    def _where(self, d: dict) -> tuple[str, str]:
        if d.get("unit_label"):
            return f" in Unit {d['unit_label']}", f" in Unit {d['unit_label']}"
        return "", f" ({d['label']})"

    def _reading_text(self, d: dict, r: dict) -> str:
        if d["kind"] == "water":
            return f"{r['flow_lpm']} L/min flow with the leak sensor {'wet' if r['leak'] else 'dry'}"
        return f"{r['temp_f']}°F"

    def _open(self, d: dict, r: dict, now: datetime) -> dict:
        acct = self.store.get("locations", d["location_id"])["account_id"]
        kind = KIND_FOR_DEVICE[d["kind"]]
        case = m.Case(id=f"case-{uuid.uuid4().hex[:8]}", device_id=d["id"], location_id=d["location_id"], account_id=acct, kind=kind,
                      state="detected", unit_label=d.get("unit_label"), opened_at=now).model_dump(mode="json")
        self._log(case, "detected", f"Sensor reading outside normal: {self._reading_text(d, r)}.", now, "sensor")
        self._alert_and_task(case, d, r, now, reopened=False)
        return case

    def _reopen(self, case: dict, d: dict, r: dict, now: datetime) -> None:
        case["reopen_count"] += 1
        case.update(fix_reported_at=None, verified_at=None)
        self._log(case, "reopened", f"Problem returned after verification: {self._reading_text(d, r)}.", now, "sensor")
        self._alert_and_task(case, d, r, now, reopened=True)

    def _alert_and_task(self, case: dict, d: dict, r: dict, now: datetime, reopened: bool) -> None:
        text = self.cfg["case_text"][case["kind"]]
        where, where_sensor = self._where(d)
        limit = self.cfg["thresholds"]["stockroom_alert_f" if case["kind"] == "freeze_risk" else "cooler_alert_f"]
        fmt = {"where": where, "where_sensor": where_sensor, "reading": self._reading_text(d, r), "limit": limit}
        loc = m.Location(**self.store.get("locations", d["location_id"]))
        policy = self.store.list("policies", account_id=case["account_id"])[0]
        codes = {x["code"] for k in ("coverages", "endorsements", "exclusions_plain") for x in policy[k]}
        title = text["title"].format(**fmt)
        task = m.Task(
            id=f"task-sense-{uuid.uuid4().hex[:8]}", rule_id=RULE_FOR_KIND[case["kind"]], account_id=case["account_id"],
            policy_id=policy["id"], location_id=loc.id, source="rule", title=("Leak returned: " if reopened else "") + title,
            why=text["why"].format(**fmt), steps=text["steps"], priority="high", score=5.0, est_minutes=30,
            peril="freeze" if case["kind"] == "freeze_risk" else "spoilage" if case["kind"] == "cooler_temp" else "water",
            coverage_note_key=NOTE_FOR_KIND[case["kind"]], coverage_codes=[c for c in CODES_FOR_KIND[case["kind"]] if c in codes],
            proof_default_level="E4", proof_accepted=["E4"], bucket="do_now", opened_at=now, due_at=now + timedelta(hours=24),
            expires_after_hours=720, cooldown_days=0, relevant_date=now.date(), provenance="SIMULATED",
            inputs_snapshot={"reasons": [f"Sensor {d['label']}: {self._reading_text(d, r)} (SIMULATED device)."], "alert_ids": [],
                             "asset_ids": [], "asset_facts": {}, "input_provenance": ["SIMULATED"], "evaluated_at": now.isoformat(),
                             "weather": {"provenance": None, "sources": []}, "coverage_keys": [NOTE_FOR_KIND[case["kind"]]],
                             "case_id": case["id"]})
        self.store.put("tasks", task.id, task.model_dump(mode="json"))
        case["task_ids"].append(task.id)
        note = f"Alert sent and task created: {task.title}"
        if reopened:  # stay in `reopened` until the user acts again
            case["timeline"].append({"ts": now.isoformat(), "state": "reopened", "note": note, "source": "system"})
            self.store.put("cases", case["id"], case)
        else:
            self._log(case, "alerted", note, now)
        acct = self.store.get("accounts", case["account_id"])
        self.engine._raise(case["account_id"], acct, now, kind="device", severity="critical", title=task.title,
                           body=task.why, deep_link="/sense", dedupe=f"case:{case['id']}:{case['reopen_count']}",
                           provenance="SIMULATED", summary={"alerts": []})
        if case["kind"] == "leak":
            self.store.put("events", f"evt-{uuid.uuid4().hex[:8]}", {
                "id": f"evt-{uuid.uuid4().hex[:8]}", "location_id": loc.id, "kind": "water_leak", "unit_label": d.get("unit_label"),
                "at": now.isoformat(), "source": f"sensor {d['id']}", "simulated": True, "case_id": case["id"]})
        self.engine.evaluate_account(case["account_id"])  # e.g. creates "check the unit below" for apartments
        self.engine.rebucket(case["account_id"])

    # ---- user actions -----------------------------------------------------------------------------------------
    @sim.locked
    def shutoff(self, case_id: str, now: datetime) -> dict:
        case = self._get(case_id)
        d = self.device(case["device_id"])
        res = sim.command(self.store, d, "shutoff", now)
        if not res["ok"]:
            raise SenseError(res["reason"])
        note = "Water shut off with the device valve (simulated command)."
        if case["state"] in ("alerted", "reopened", "not_improving", "inconclusive"):
            self._log(case, "acting", note, now, "user")
        else:
            case["timeline"].append({"ts": now.isoformat(), "state": case["state"], "note": note, "source": "user"})
            self.store.put("cases", case_id, case)
        return self._get(case_id)

    @sim.locked
    def acting(self, case_id: str, now: datetime) -> dict:
        case = self._get(case_id)
        if case["state"] not in ("alerted", "reopened", "not_improving", "inconclusive"):
            raise SenseError(f"case is {case['state']}")
        self._log(case, "acting", "Resident or manager is working on the fix.", now, "user")
        return case

    @sim.locked
    def report_fix(self, case_id: str, now: datetime) -> dict:
        case = self._get(case_id)
        if case["state"] not in ("alerted", "acting", "not_improving", "inconclusive", "reopened"):
            raise SenseError(f"cannot report a fix while the case is {case['state']}")
        d = self.device(case["device_id"])
        state = sim.get_state(self.store, d["id"])
        sim.materialize(self.store, d, now)
        state = sim.get_state(self.store, d["id"])
        state["valve"] = "open"
        self.store.put(sim.STATE_COL, d["id"], state)
        if state.get("fix_works", True):
            sim.set_scenario(self.store, d, "recovery", now)
        case["fix_reported_at"] = now.isoformat()
        self._log(case, "verifying", "Fix reported. Waiting for the sensor to confirm normal readings.", now, "user")
        return case

    # ---- verification -----------------------------------------------------------------------------------------
    def _verify(self, case: dict, d: dict, rows: list[dict], now: datetime) -> None:
        v = self.cfg["verify"]
        fix = datetime.fromisoformat(case["fix_reported_at"])
        post = [r for r in rows if datetime.fromisoformat(r["ts"]) > fix]
        newest = datetime.fromisoformat(rows[-1]["ts"]) if rows else None
        if newest is None or (now - newest).total_seconds() > v["stale_after_seconds"]:
            return self._log(case, "inconclusive", "Sensor data is missing or stale, so the fix cannot be verified.", now)
        clean_n = self._tail(post, lambda r: self.clean(d, r))
        bad_n = self._tail(post, lambda r: self.anomalous(d, r))
        if clean_n >= v["clean_consecutive"]:
            return self._verified(case, d, post, now)
        if bad_n >= v["bad_consecutive"]:
            return self._log(case, "not_improving", f"Sensor still reads {self._reading_text(d, post[-1])} after the fix.", now, "sensor")
        if (now - fix).total_seconds() > v["window_seconds"]:
            self._log(case, "inconclusive", "Not enough clean readings within the verification window.", now)

    def _verified(self, case: dict, d: dict, post: list[dict], now: datetime) -> None:
        window = post[-self.cfg["verify"]["clean_consecutive"]:]
        manifest = {"case_id": case["id"], "device_id": d["id"], "kind": case["kind"], "fix_reported_at": case["fix_reported_at"],
                    "verified_at": now.isoformat(), "readings": window, "timeline": case["timeline"], "simulated": True}
        digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, default=str).encode()).hexdigest()
        case.update(verified_at=now.isoformat(), manifest_sha256=digest)
        self.store.put("case_evidence", case["id"], {"id": case["id"], "manifest": manifest, "manifest_sha256": digest})
        self._log(case, "verified", f"Sensor confirmed {len(window)} consecutive normal readings. Evidence hash {digest[:12]}…", now, "sensor")
        for tid in case["task_ids"]:
            t = self.store.get("tasks", tid)
            if t and t["status"] == "open":
                proof = m.Proof(id=f"proof-{uuid.uuid4().hex[:10]}", level="E4", type="sensor", captured_at=now, sha256=digest,
                                by_user="sensor", location_source="none").model_dump(mode="json")
                t["proof"].append(proof)
                t.update(status="done", closed_at=now.isoformat())
                self.store.put("tasks", tid, t)
                self.store.put("proofs", proof["id"], {**proof, "task_id": tid, "account_id": t["account_id"], "task_title": t["title"],
                                                      "visibility": t["visibility"]})
        self.engine.rebucket(case["account_id"])
        acct = self.store.get("accounts", case["account_id"])
        self.engine._raise(case["account_id"], acct, now, kind="device", severity="info", title="Fix verified by sensor",
                           body="Readings are back to normal. The case is closed and the sensor keeps watching.", deep_link="/sense",
                           dedupe=f"case:{case['id']}:verified:{case['reopen_count']}", provenance="SIMULATED", summary={"alerts": []})

    def _get(self, case_id: str) -> dict:
        c = self.store.get("cases", case_id)
        if not c:
            raise KeyError(case_id)
        return c

    # ---- views ------------------------------------------------------------------------------------------------
    def poll_account(self, account_id: str, now: datetime) -> list[dict]:
        out = []
        for loc in self.store.list("locations", account_id=account_id):
            for d in self.store.list("devices", location_id=loc["id"]):
                if d["status"] == "connected":
                    out.append(self.poll(d["id"], now))
        return out

    def poll_all(self, now: datetime) -> None:
        for d in self.store.list("devices"):
            if d["status"] == "connected":
                self.poll(d["id"], now)
