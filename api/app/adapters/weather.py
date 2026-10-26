"""Weather adapters: NWS (hourly + official alerts), Open-Meteo (daily + precip), composite, scenario."""

from collections import defaultdict
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import httpx

from app.models import DailyForecast, Forecast, HourlyForecast, Location, WeatherAlert

NWS_BASE = "https://api.weather.gov"
OM_FORECAST = "https://api.open-meteo.com/v1/forecast"
TTL_POINTS, TTL_FORECAST, TTL_ALERTS = 7 * 86400, 30 * 60, 5 * 60  # BUILD_SPEC §7.1


def _dt(s: str | None) -> datetime | None:
    return datetime.fromisoformat(s) if s else None


class NWSProvider:
    """api.weather.gov. Sends the configured User-Agent on every request; caches per §7.1."""

    def __init__(self, user_agent: str, cache, client: httpx.Client | None = None):
        self._ua, self._cache = user_agent, cache
        self._http = client or httpx.Client(timeout=20)

    def _get(self, url: str) -> dict:
        r = self._http.get(url, headers={"User-Agent": self._ua, "Accept": "application/geo+json"})
        r.raise_for_status()
        return r.json()

    def _cached(self, key: str, ttl: int, fn):
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        val = fn()
        self._cache.set(key, val, ttl)
        return val

    def point(self, loc: Location) -> dict:
        return self._cached(f"nws:points:{loc.lat},{loc.lon}", TTL_POINTS,
                            lambda: self._get(f"{NWS_BASE}/points/{loc.lat},{loc.lon}")["properties"])

    def hourly(self, loc: Location) -> list[HourlyForecast]:
        url = self.point(loc)["forecastHourly"]
        props = self._cached(f"nws:hourly:{loc.id}", TTL_FORECAST, lambda: self._get(url)["properties"])
        out = []
        for p in props["periods"]:
            t = p["temperature"] if p.get("temperatureUnit", "F") == "F" else p["temperature"] * 9 / 5 + 32
            out.append(HourlyForecast(start=_dt(p["startTime"]), temp_f=float(t),
                                      precip_prob=(p.get("probabilityOfPrecipitation") or {}).get("value"),
                                      short=p.get("shortForecast")))
        return out

    def active_alerts(self, loc: Location) -> list[WeatherAlert]:
        data = self._cached(f"nws:alerts:{loc.lat},{loc.lon}", TTL_ALERTS,
                            lambda: self._get(f"{NWS_BASE}/alerts/active?point={loc.lat},{loc.lon}"))
        out = []
        for f in data.get("features", []):
            p = f["properties"]
            out.append(WeatherAlert(
                id=p["id"], event=p["event"], severity=p.get("severity"), urgency=p.get("urgency"),
                headline=p.get("headline") or p["event"], description=(p.get("description") or "")[:1500],
                onset=_dt(p.get("onset") or p.get("effective")), ends=_dt(p.get("ends")),
                expires=_dt(p.get("expires")), area_desc=p.get("areaDesc", ""), source="NWS", provenance="LIVE"))
        return out

    def forecast(self, loc: Location) -> Forecast:
        tz = ZoneInfo(loc.time_zone)
        hourly = self.hourly(loc)
        by_day = defaultdict(list)
        for h in hourly:
            by_day[h.start.astimezone(tz).date()].append(h)
        daily = [DailyForecast(date=d, max_f=max(h.temp_f for h in hs), min_f=min(h.temp_f for h in hs),
                               precip_prob=max((h.precip_prob or 0) for h in hs), source="NWS")
                 for d, hs in sorted(by_day.items())]
        return Forecast(location_id=loc.id, fetched_at=datetime.now(UTC), daily=daily, hourly=hourly,
                        sources=["NWS hourly forecast"], provenance="LIVE")


class OpenMeteoProvider:
    def __init__(self, cache, client: httpx.Client | None = None):
        self._cache = cache
        self._http = client or httpx.Client(timeout=20)

    def forecast(self, loc: Location) -> Forecast:
        key = f"om:forecast:{loc.id}"
        data = self._cache.get(key)
        if data is None:
            r = self._http.get(OM_FORECAST, params={
                "latitude": loc.lat, "longitude": loc.lon, "timezone": loc.time_zone, "forecast_days": 10,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
                "temperature_unit": "fahrenheit", "precipitation_unit": "inch"})
            r.raise_for_status()
            data = r.json()["daily"]
            self._cache.set(key, data, TTL_FORECAST)
        daily = [DailyForecast(date=date.fromisoformat(t), max_f=mx, min_f=mn, precip_in=p, precip_prob=pp,
                               source="Open-Meteo")
                 for t, mx, mn, p, pp in zip(data["time"], data["temperature_2m_max"], data["temperature_2m_min"],
                                             data["precipitation_sum"], data["precipitation_probability_max"],
                                             strict=True)]
        return Forecast(location_id=loc.id, fetched_at=datetime.now(UTC), daily=daily,
                        sources=["Open-Meteo forecast"], provenance="LIVE")

    def active_alerts(self, loc: Location) -> list[WeatherAlert]:
        return []  # Open-Meteo has no official alerts; NWS is the only alert source.


class CompositeWeatherProvider:
    """NWS first (official), Open-Meteo fills missing days and supplies precip amounts. Either may fail."""

    def __init__(self, nws, om):
        self.nws, self.om = nws, om

    def forecast(self, loc: Location) -> Forecast:
        nws = om = None
        errors = []
        for name in ("nws", "om"):
            try:
                f = getattr(self, name).forecast(loc)
                nws, om = (f, om) if name == "nws" else (nws, f)
            except Exception as e:  # noqa: BLE001 - provider outage must not break the engine
                errors.append(f"{name}: {e.__class__.__name__}")
        if nws is None and om is None:
            raise RuntimeError("no weather source available: " + "; ".join(errors))
        base = {d.date: d for d in (om.daily if om else [])}
        for d in (nws.daily if nws else []):
            o = base.get(d.date)
            # Keep NWS temperatures, but take precipitation amount from Open-Meteo when present.
            base[d.date] = d.model_copy(update={"precip_in": o.precip_in if o else None,
                                                "source": "NWS+Open-Meteo" if o else "NWS"})
        sources = (nws.sources if nws else []) + (om.sources if om else [])
        return Forecast(location_id=loc.id, fetched_at=datetime.now(UTC),
                        daily=[base[k] for k in sorted(base)], hourly=nws.hourly if nws else [],
                        sources=sources, provenance="LIVE")

    def active_alerts(self, loc: Location) -> list[WeatherAlert]:
        return self.nws.active_alerts(loc)
