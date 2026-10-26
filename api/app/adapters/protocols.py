"""Adapter interfaces (BUILD_SPEC §7.3). Every external dependency sits behind one of these."""

from datetime import datetime
from typing import Literal, Protocol

from app.models import Alert, Forecast, Location, Policy, WeatherAlert


class PolicySource(Protocol):  # demo: JSON seed -> later: carrier policy admin API
    def get_policy(self, policy_id: str) -> Policy: ...
    def list_policies(self, account_id: str) -> list[Policy]: ...


class WeatherProvider(Protocol):  # NWS + Open-Meteo, ScenarioProvider (demo injection)
    def forecast(self, loc: Location) -> Forecast: ...
    def active_alerts(self, loc: Location) -> list[WeatherAlert]: ...


class HistoryProvider(Protocol):  # derived JSON now -> BigQuery later
    def stats(self, loc: Location) -> dict: ...


class DeliveryResult(Protocol):
    ok: bool
    channel: str


class Notifier(Protocol):  # in-app, console e-mail (dev); SMTP / Twilio later
    def send(self, alert: Alert) -> list[str]: ...


class DeviceAdapter(Protocol):  # simulated now -> Flo / Phyn / LeakBot / webhook later
    def readings(self, device_id: str, since: datetime) -> list[dict]: ...
    def command(self, device_id: str, action: Literal["shutoff", "open"]) -> dict: ...


class Cache(Protocol):
    def get(self, key: str) -> dict | list | None: ...
    def set(self, key: str, value: dict | list, ttl_seconds: int) -> None: ...
