from datetime import UTC, date, datetime, timedelta

import pytest

from app.adapters.notifier import ConsoleEmailNotifier, InAppNotifier, NotifierChain
from app.engine.engine import Engine
from app.engine.playbooks import load_config, load_rules
from app.models import DailyForecast, Forecast, WeatherAlert
from app.seed import seed_store
from app.store import MemoryStore

NOW = datetime(2026, 10, 25, 15, 0, tzinfo=UTC)  # 08:00 in Arizona
TODAY = date(2026, 10, 25)


def calm_days(n=8, hi=84.0, lo=58.0):
    return [DailyForecast(date=TODAY + timedelta(days=i), max_f=hi, min_f=lo, precip_in=0.0, precip_prob=5,
                          source="FIXTURE") for i in range(n)]


class FakeWeather:
    """Fixture weather: per-location forecast overrides and alerts. Never touches the network."""

    def __init__(self):
        self.days = {}
        self.alerts = {}
        self.fail = False

    def set_days(self, loc_id, **kw):
        self.days[loc_id] = calm_days(**kw)

    def forecast(self, loc):
        if self.fail:
            raise RuntimeError("down")
        return Forecast(location_id=loc.id, fetched_at=NOW, daily=self.days.get(loc.id, calm_days()),
                        sources=["fixture"], provenance="LIVE")

    def active_alerts(self, loc):
        if self.fail:
            raise RuntimeError("down")
        return self.alerts.get(loc.id, [])


def alert(event, loc_id="x", sev="Severe", sim=False, hours=12):
    return WeatherAlert(id=f"urn:test:{event}:{loc_id}", event=event, severity=sev, urgency="Expected",
                        headline=f"{event} headline", onset=NOW, ends=NOW + timedelta(hours=hours),
                        expires=NOW + timedelta(hours=hours), source="SCENARIO" if sim else "NWS",
                        provenance="SIMULATED" if sim else "LIVE")


@pytest.fixture
def env():
    store = MemoryStore()
    seed_store(store)
    store.put("scenario_state", "active", {"injections": [], "fake_now": NOW.isoformat()})
    weather = FakeWeather()
    outbox = ConsoleEmailNotifier()
    engine = Engine(store, weather, None, NotifierChain(InAppNotifier(store), outbox), load_rules(), load_config())
    engine.outbox = outbox
    return engine, store, weather


def rule_ids(engine, account_id, status="open"):
    return sorted(t["rule_id"].removeprefix("az.").removesuffix(".v1") for t in engine.tasks(account_id, status))
