import json
import os
from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.adapters.cache import MemoryCache
from app.adapters.history import DerivedHistoryProvider
from app.adapters.scenario import ScenarioProvider, inject, reset, time_travel
from app.adapters.weather import CompositeWeatherProvider, NWSProvider, OpenMeteoProvider
from app.models import Location
from app.seed import load_derived
from app.store import MemoryStore

UA = "SymbiosisProtectTest/0.1 (test@example.com)"
LOC = Location(id="loc-p1", account_id="acct-p1", label="x", city="Chandler", county="Maricopa County", lat=33.3062, lon=-111.8413,
               nws_zone="AZZ548", nws_county="AZC013", nws_office="PSR", nws_grid_x=1, nws_grid_y=2,
               time_zone="America/Phoenix", county_fips="04013", fema_tract_id="04013523002", elevation_ft=1220,
               hard_water_zone=True)

POINT = {"properties": {"forecastHourly": "https://api.weather.gov/gridpoints/PSR/1,2/forecast/hourly"}}


def hourly_payload():
    periods = [{"startTime": f"2026-10-25T{h:02d}:00:00-07:00", "temperature": 60 + h, "temperatureUnit": "F",
                "probabilityOfPrecipitation": {"value": 10}, "shortForecast": "Sunny"} for h in range(0, 24)]
    return {"properties": {"periods": periods}}


ALERTS = {"features": [{"properties": {
    "id": "urn:oid:1", "event": "Extreme Heat Warning", "severity": "Severe", "urgency": "Expected",
    "headline": "Extreme Heat Warning issued", "description": "Hot.", "onset": "2026-10-25T10:00:00-07:00",
    "ends": "2026-10-26T20:00:00-07:00", "expires": "2026-10-26T20:00:00-07:00", "areaDesc": "Phoenix Metro"}}]}


@respx.mock
def test_nws_sends_user_agent_and_caches():
    p = respx.get("https://api.weather.gov/points/33.3062,-111.8413").mock(return_value=httpx.Response(200, json=POINT))
    h = respx.get("https://api.weather.gov/gridpoints/PSR/1,2/forecast/hourly").mock(
        return_value=httpx.Response(200, json=hourly_payload()))
    a = respx.get("https://api.weather.gov/alerts/active?point=33.3062,-111.8413").mock(
        return_value=httpx.Response(200, json=ALERTS))
    nws = NWSProvider(UA, MemoryCache())
    f = nws.forecast(LOC)
    al = nws.active_alerts(LOC)
    nws.forecast(LOC)
    nws.active_alerts(LOC)
    assert f.daily[0].max_f == 83 and f.daily[0].min_f == 60 and f.provenance == "LIVE"
    assert al[0].event == "Extreme Heat Warning" and al[0].source == "NWS" and al[0].provenance == "LIVE"
    for route in (p, h, a):
        assert route.call_count == 1, "second call must be served from cache"
        assert route.calls[0].request.headers["user-agent"] == UA


@respx.mock
def test_composite_falls_back_to_open_meteo_when_nws_down():
    respx.get(url__regex=r"https://api\.weather\.gov/.*").mock(return_value=httpx.Response(503))
    respx.get("https://api.open-meteo.com/v1/forecast").mock(return_value=httpx.Response(200, json={"daily": {
        "time": ["2026-10-25", "2026-10-26"], "temperature_2m_max": [88.0, 90.0], "temperature_2m_min": [60.0, 61.0],
        "precipitation_sum": [0.0, 0.3], "precipitation_probability_max": [0, 40]}}))
    cache = MemoryCache()
    comp = CompositeWeatherProvider(NWSProvider(UA, cache), OpenMeteoProvider(cache))
    f = comp.forecast(LOC)
    assert [d.max_f for d in f.daily] == [88.0, 90.0] and f.daily[1].precip_in == 0.3
    assert f.sources == ["Open-Meteo forecast"]


@respx.mock
def test_composite_merges_nws_temps_with_open_meteo_precip():
    respx.get("https://api.weather.gov/points/33.3062,-111.8413").mock(return_value=httpx.Response(200, json=POINT))
    respx.get("https://api.weather.gov/gridpoints/PSR/1,2/forecast/hourly").mock(
        return_value=httpx.Response(200, json=hourly_payload()))
    respx.get("https://api.open-meteo.com/v1/forecast").mock(return_value=httpx.Response(200, json={"daily": {
        "time": ["2026-10-25", "2026-10-26"], "temperature_2m_max": [1.0, 2.0], "temperature_2m_min": [1.0, 2.0],
        "precipitation_sum": [0.7, 0.0], "precipitation_probability_max": [80, 0]}}))
    cache = MemoryCache()
    f = CompositeWeatherProvider(NWSProvider(UA, cache), OpenMeteoProvider(cache)).forecast(LOC)
    day = next(d for d in f.daily if d.date.isoformat() == "2026-10-25")
    assert day.max_f == 83 and day.precip_in == 0.7 and day.source == "NWS+Open-Meteo"


def test_composite_raises_only_when_all_sources_fail():
    class Boom:
        def forecast(self, loc):
            raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        CompositeWeatherProvider(Boom(), Boom()).forecast(LOC)


def test_memory_cache_ttl():
    t = [1000.0]
    c = MemoryCache(clock=lambda: t[0])
    c.set("k", {"a": 1}, 60)
    assert c.get("k") == {"a": 1}
    t[0] += 61
    assert c.get("k") is None


class BaseOK:
    def forecast(self, loc):
        from conftest import FakeWeather

        return FakeWeather().forecast(loc)

    def active_alerts(self, loc):
        raise RuntimeError("NWS down")


def test_scenario_provider_labels_everything_simulated_and_survives_nws_outage():
    store, hist = MemoryStore(), DerivedHistoryProvider(load_derived())
    sp = ScenarioProvider(BaseOK(), store, hist)
    assert sp.forecast(LOC).provenance == "LIVE"
    inject(store, "heat_phoenix", datetime.now(UTC))
    f, alerts = sp.forecast(LOC), sp.active_alerts(LOC)
    assert f.provenance == "SIMULATED" and max(d.max_f for d in f.daily) == 114
    assert alerts[0].provenance == "SIMULATED" and alerts[0].source == "SCENARIO" and alerts[0].id.startswith("sim:")
    other = LOC.model_copy(update={"id": "loc-p4", "city": "Flagstaff"})
    assert sp.active_alerts(other) == [], "heat scenario must not leak to Flagstaff"
    reset(store)
    assert sp.forecast(LOC).provenance == "LIVE"


def test_scenario_time_travel_builds_forecast_from_normals():
    store = MemoryStore()
    sp = ScenarioProvider(BaseOK(), store, DerivedHistoryProvider(load_derived()))
    time_travel(store, datetime(2026, 7, 18, 12, tzinfo=UTC))
    f = sp.forecast(LOC)
    assert f.provenance == "SIMULATED" and f.daily[0].date.isoformat() == "2026-07-18" and f.daily[0].max_f > 100


@pytest.mark.skipif(not os.environ.get("RUN_LIVE"), reason="live network test; set RUN_LIVE=1")
def test_live_nws_and_open_meteo_for_all_personas():
    ua = os.environ.get("NWS_USER_AGENT", UA)
    cache = MemoryCache()
    comp = CompositeWeatherProvider(NWSProvider(ua, cache), OpenMeteoProvider(cache))
    locs = json.loads(open("../data/seed/locations.json").read())
    for raw in locs:
        loc = Location(**raw)
        f = comp.forecast(loc)
        assert len(f.daily) >= 5 and f.provenance == "LIVE"
        assert any("NWS" in s for s in f.sources), f"NWS missing for {loc.city}"
        comp.active_alerts(loc)  # must not raise
