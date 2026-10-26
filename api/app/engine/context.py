"""Everything a rule may look at, gathered once per (location, now)."""

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.models import Asset, Claim, Forecast, Location, Policy, PropertyProfile, WeatherAlert


@dataclass
class Ctx:
    now: datetime  # timezone-aware, in the location's zone
    loc: Location
    profile: PropertyProfile
    assets: list[Asset]
    policy: Policy
    forecast: Forecast | None
    alerts: list[WeatherAlert]
    history: dict
    nri: dict
    claims: list[Claim]
    events: list[dict]
    config: object  # engine.playbooks.Config
    weather_error: str | None = None
    extras: dict = field(default_factory=dict)

    @property
    def today(self):
        return self.now.date()

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.loc.time_zone)

    @property
    def thresholds(self) -> dict:
        return self.config.thresholds

    def assets_of(self, types) -> list[Asset]:
        types = [types] if isinstance(types, str) else list(types)
        return [a for a in self.assets if a.type in types]

    @property
    def simulated(self) -> bool:
        return bool(self.forecast and self.forecast.provenance == "SIMULATED") or any(
            a.provenance == "SIMULATED" for a in self.alerts)
