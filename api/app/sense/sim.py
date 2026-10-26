"""SimulatedWaterDevice (DeviceAdapter): deterministic readings every `tick_seconds`. Everything it emits is SIMULATED."""

import hashlib
import threading
from datetime import datetime, timedelta

import yaml

from app.engine.playbooks import PLAYBOOK_DIR

CFG = yaml.safe_load((PLAYBOOK_DIR / "sense.yaml").read_text(encoding="utf-8"))
STATE_COL, READ_COL = "device_state", "readings"
LOCK = threading.RLock()  # FastAPI runs sync routes in a thread pool; serialize device state read-modify-write

WATER_SCENARIOS = ("normal", "slow_leak", "burst", "recovery")
SCENARIOS = {"water": WATER_SCENARIOS, "stockroom": ("normal", "freeze_drop", "recovery"),
             "cooler": ("normal", "cooler_drift", "recovery")}


def _locked(fn):
    def wrapper(*a, **k):
        with LOCK:
            return fn(*a, **k)

    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def jitter(device_id: str, epoch: int, name: str) -> float:
    """Deterministic value in [-1, 1] so tests and demos are repeatable."""
    h = hashlib.sha256(f"{device_id}|{epoch}|{name}".encode()).digest()
    return int.from_bytes(h[:4], "big") / 2**31 - 1


def _tick(ts: datetime) -> int:
    return int(ts.timestamp()) // CFG["tick_seconds"]


def reading_at(device: dict, state: dict, ts: datetime) -> dict:
    kind, scen = device["kind"], state["scenario"]
    since = datetime.fromisoformat(state["scenario_since"])
    dt = max(0.0, (ts - since).total_seconds())
    ticks = dt / CFG["tick_seconds"]
    p = CFG["profiles"][kind][scen]
    j, ep = CFG["jitter"], _tick(ts)
    out = {"flow_lpm": None, "leak": None, "temp_f": None, "humidity": None}
    if kind == "water":
        flow = p["flow"]
        out["leak"] = 0
        hum = p.get("humidity", 40)
        if scen == "slow_leak":
            out["leak"] = 1 if dt >= p["leak_after_s"] else 0
            hum = min(p["humidity_cap"], 40 + p["humidity_per_tick"] * ticks)
        elif scen == "burst":
            out["leak"] = p["leak"]
            hum = min(p["humidity_cap"], 40 + p["humidity_per_tick"] * ticks)
        elif scen == "recovery":
            out["leak"] = 1 if dt < p["wet_for_s"] else 0
            hum = max(p["humidity_floor"], 60 + p["humidity_per_tick"] * ticks)
        if state.get("valve") == "closed":
            flow = 0.0
        out["flow_lpm"] = round(max(0.0, flow + jitter(device["id"], ep, "f") * j["flow"] * (1 if flow else 0)), 2)
        out["humidity"] = round(hum + jitter(device["id"], ep, "h") * j["humidity"], 1)
        out["temp_f"] = round(p["temp"] + jitter(device["id"], ep, "t") * j["temp"], 1)
    else:
        if scen == "normal":
            t = p["temp"]
        elif scen == "freeze_drop":
            t = max(p["floor"], p["start"] - p["drop_per_tick"] * ticks)
        elif scen == "cooler_drift":
            t = min(p["cap"], p["start"] + p["rise_per_tick"] * ticks)
        else:  # recovery
            t = (min(p["cap"], p["start"] + p["rise_per_tick"] * ticks) if kind == "stockroom"
                 else max(p["floor"], p["start"] - p["drop_per_tick"] * ticks))
        out["temp_f"] = round(t + jitter(device["id"], ep, "t") * j["temp"], 1)
    return out


def get_state(store, device_id: str) -> dict | None:
    return store.get(STATE_COL, device_id)


@_locked
def init_state(store, device: dict, now: datetime) -> dict:
    state = {"id": device["id"], "scenario": "normal", "scenario_since": now.isoformat(), "valve": "open", "fix_works": True,
             "last_tick": (now - timedelta(seconds=CFG["backfill_seconds"])).isoformat()}
    store.put(STATE_COL, device["id"], state)
    return state


@_locked
def set_scenario(store, device: dict, scenario: str, now: datetime, fix_works: bool | None = None) -> dict:
    if scenario not in SCENARIOS[device["kind"]]:
        raise ValueError(f"{scenario} is not a scenario for a {device['kind']} device")
    state = get_state(store, device["id"]) or init_state(store, device, now)
    materialize(store, device, now)  # settle history before the scenario changes
    state = get_state(store, device["id"])
    state.update(scenario=scenario, scenario_since=now.isoformat())
    if fix_works is not None:
        state["fix_works"] = fix_works
    store.put(STATE_COL, device["id"], state)
    return state


@_locked
def materialize(store, device: dict, now: datetime) -> list[dict]:
    """Generate and persist any ticks between last_tick and now. Idempotent."""
    state = get_state(store, device["id"])
    if state is None:
        return []
    step = timedelta(seconds=CFG["tick_seconds"])
    ts = datetime.fromisoformat(state["last_tick"]) + step
    made = []
    n = 0
    while ts <= now and n < CFG["max_ticks_per_poll"]:
        r = {"id": f"{device['id']}:{int(ts.timestamp())}", "device_id": device["id"], "ts": ts.isoformat(),
             **reading_at(device, state, ts), "quality": "good", "provenance": "SIMULATED"}
        store.put(READ_COL, r["id"], r)
        made.append(r)
        state["last_tick"] = ts.isoformat()
        ts += step
        n += 1
    if made:
        store.put(STATE_COL, device["id"], state)
    return made


def readings(store, device_id: str, since: datetime) -> list[dict]:
    rows = [r for r in store.list(READ_COL, device_id=device_id) if datetime.fromisoformat(r["ts"]) > since]
    return sorted(rows, key=lambda r: r["ts"])


@_locked
def command(store, device: dict, action: str, now: datetime) -> dict:
    if action not in ("shutoff", "open"):
        raise ValueError("action must be shutoff or open")
    if not device.get("supports_shutoff"):
        return {"ok": False, "reason": "this device cannot control a valve"}
    state = get_state(store, device["id"]) or init_state(store, device, now)
    materialize(store, device, now)
    state = get_state(store, device["id"])
    state["valve"] = "closed" if action == "shutoff" else "open"
    store.put(STATE_COL, device["id"], state)
    return {"ok": True, "valve": state["valve"], "at": now.isoformat(), "simulated": True}


locked = _locked


class SimulatedWaterDevice:
    """DeviceAdapter implementation bound to a Store."""

    def __init__(self, store, devices_by_id):
        self.store, self.devices = store, devices_by_id

    def readings(self, device_id: str, since: datetime) -> list[dict]:
        return readings(self.store, device_id, since)

    def command(self, device_id: str, action: str) -> dict:
        from datetime import UTC

        return command(self.store, self.devices[device_id], action, datetime.now(UTC))
