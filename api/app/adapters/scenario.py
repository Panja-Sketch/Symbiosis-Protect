"""ScenarioProvider: wraps a real provider and applies Scenario Director injections (always SIMULATED)."""

from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import yaml

from app.models import DailyForecast, Forecast, Location, WeatherAlert

SCENARIOS = yaml.safe_load((Path(__file__).resolve().parent.parent / "playbooks" / "scenarios.yaml").read_text(encoding="utf-8"))
STATE_COL, STATE_ID = "scenario_state", "active"


def get_state(store) -> dict:
    return store.get(STATE_COL, STATE_ID) or {"injections": [], "fake_now": None}


def clock(store, real_now: datetime | None = None) -> datetime:
    """Current time for the engine, honouring Director time-travel."""
    state = get_state(store)
    return datetime.fromisoformat(state["fake_now"]) if state.get("fake_now") else (real_now or datetime.now(UTC))


def inject(store, kind: str, now: datetime) -> dict:
    if kind not in SCENARIOS:
        raise KeyError(kind)
    state = get_state(store)
    state["injections"] = [i for i in state["injections"] if i["kind"] != kind]
    state["injections"].append({"kind": kind, "created_at": now.isoformat()})
    store.put(STATE_COL, STATE_ID, state)
    return state


def time_travel(store, to: datetime | None) -> dict:
    state = get_state(store)
    state["fake_now"] = to.isoformat() if to else None
    store.put(STATE_COL, STATE_ID, state)
    return state


def reset(store) -> None:
    store.put(STATE_COL, STATE_ID, {"injections": [], "fake_now": None})


class ScenarioProvider:
    def __init__(self, base, store, history_provider):
        self.base, self.store, self.history = base, store, history_provider

    def _active(self, loc: Location, now: datetime):
        for inj in get_state(self.store)["injections"]:
            spec = SCENARIOS[inj["kind"]]
            if loc.city not in spec["cities"]:
                continue
            created = datetime.fromisoformat(inj["created_at"])
            yield inj, spec, created

    def _synth_from_normals(self, loc: Location, now: datetime) -> Forecast:
        """Time-travel mode: build a plausible week from 1991-2020 monthly normals, labelled SIMULATED."""
        norm = {m["month"]: m for m in self.history.stats(loc)["monthly_normals"]}
        days = []
        for i in range(10):
            d = (now + timedelta(days=i)).date()
            n = norm[d.month]
            days.append(DailyForecast(date=d, max_f=n["mean_max_f"], min_f=n["mean_min_f"], precip_in=0.0,
                                      precip_prob=10, source="SIMULATED (monthly normals)"))
        return Forecast(location_id=loc.id, fetched_at=now, daily=days,
                        sources=["Scenario Director time-travel (1991-2020 normals)"], provenance="SIMULATED")

    def forecast(self, loc: Location) -> Forecast:
        state = get_state(self.store)
        now = clock(self.store)
        if state.get("fake_now"):
            f = self._synth_from_normals(loc, now)
        else:
            f = self.base.forecast(loc)
        applied = False
        for _, spec, _created in self._active(loc, now):
            ov = spec["forecast"]
            start = now.date() if state.get("fake_now") else date.today()
            by_date = {d.date: d for d in f.daily}
            for i in range(ov["days"]):
                d = start + timedelta(days=i)
                by_date[d] = DailyForecast(date=d, max_f=ov["max_f"], min_f=ov["min_f"], precip_in=ov["precip_in"],
                                           precip_prob=ov["precip_prob"], source="SIMULATED (Scenario Director)")
            f = f.model_copy(update={"daily": [by_date[k] for k in sorted(by_date)], "hourly": []})
            applied = True
        if applied:
            f = f.model_copy(update={"provenance": "SIMULATED", "sources": f.sources + ["Scenario Director"]})
        return f

    def active_alerts(self, loc: Location) -> list[WeatherAlert]:
        state = get_state(self.store)
        now = clock(self.store)
        try:
            alerts = [] if state.get("fake_now") else self.base.active_alerts(loc)
        except Exception:  # noqa: BLE001 - real feed outage must not hide injected alerts
            alerts = []
        for inj, spec, created in self._active(loc, now):
            for n, a in enumerate(spec["alerts"]):
                start = created if not state.get("fake_now") else now
                alerts.append(WeatherAlert(
                    id=f"sim:{inj['kind']}:{n}:{loc.id}", event=a["event"], severity=a["severity"],
                    urgency=a["urgency"], headline=a["headline"], description="Injected by the Scenario Director.",
                    onset=start, ends=start + timedelta(hours=a["duration_hours"]),
                    expires=start + timedelta(hours=a["duration_hours"]), area_desc=loc.city,
                    source="SCENARIO", provenance="SIMULATED"))
        return alerts
