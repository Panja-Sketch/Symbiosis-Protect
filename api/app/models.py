"""Canonical data contracts (BUILD_SPEC §6). Seed data is validated against these."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

Provenance = Literal["LIVE", "HISTORIC", "SYNTHETIC", "SIMULATED", "AI"]
LOB = Literal["homeowners", "dwelling_fire", "bop", "commercial_real_estate", "agribusiness"]
AssetType = Literal[
    "water_heater", "washer_hoses", "ice_maker_line", "dishwasher_line", "hvac_condensate", "roof",
    "sprinkler_system", "refrigeration", "unit", "roof_drains", "main_shutoff", "backflow_preventer",
    "backup_power", "wash_down_system", "rooftop_unit",
]


class Contact(BaseModel):
    email: str
    phone: str | None = None


class Preferences(BaseModel):
    channels: list[Literal["in_app", "email"]] = ["in_app", "email"]
    quiet_hours: tuple[str, str] | None = ("21:00", "07:00")


class Agent(BaseModel):
    id: str
    agency_name: str
    name: str
    email: str
    phone: str | None = None
    provenance: Provenance = "SYNTHETIC"


class Account(BaseModel):
    id: str
    persona_id: str
    display_name: str
    type: Literal["person", "business"]
    headline: str
    agent_id: str
    contact: Contact
    preferences: Preferences = Preferences()
    program_label: str | None = None
    provenance: Provenance = "SYNTHETIC"


class Location(BaseModel):
    id: str
    account_id: str
    label: str
    city: str
    county: str
    state: str = "AZ"
    lat: float
    lon: float
    nws_zone: str
    nws_county: str
    nws_office: str
    nws_grid_x: int
    nws_grid_y: int
    time_zone: str
    county_fips: str
    fema_tract_id: str
    elevation_ft: int
    hard_water_zone: bool
    provenance: Provenance = "SYNTHETIC"


class Coverage(BaseModel):
    code: str
    name_plain: str
    limit_usd: int | None = None
    limit_note: str | None = None
    deductible_usd: int | None = None
    deductible_note: str | None = None
    what_it_covers_plain: str
    what_it_does_not_plain: str
    examples: list[str] = Field(default_factory=list)


class Endorsement(BaseModel):
    code: str
    name_plain: str
    present: bool
    why_it_matters_plain: str


class ExclusionNote(BaseModel):
    code: str
    title: str
    plain: str


class Policy(BaseModel):
    id: str
    account_id: str
    lob: LOB
    product_label: str
    term_start: date
    term_end: date
    status: Literal["active", "pending", "expired"] = "active"
    coverages: list[Coverage]
    endorsements: list[Endorsement]
    exclusions_plain: list[ExclusionNote]
    deductibles: dict[str, int | str]
    preview_flag: bool = False
    summary_disclaimer: str = (
        "This is a plain-language summary written for this demo, not your policy contract. "
        "Your policy documents and your agent confirm final coverage decisions."
    )
    provenance: Provenance = "SYNTHETIC"


class Asset(BaseModel):
    id: str
    location_id: str
    type: AssetType
    label: str
    install_year: int | None = None
    last_service_date: date | None = None
    material: str | None = None
    unit_label: str | None = None
    floor: int | None = None
    notes: str = ""
    attributes: dict = Field(default_factory=dict)
    provenance: Provenance = "SYNTHETIC"


class PropertyProfile(BaseModel):
    """Per-location facts the rule engine reads (kept out of Location so it can be edited in 'My place')."""

    location_id: str
    year_built: int
    sqft: int
    construction: str
    roof_type: str
    stories: int
    has_central_ac: bool
    occupancy: Literal["owner_occupied", "tenant_occupied", "vacant_between_tenants", "commercial_open",
                       "multi_unit_residential", "agricultural_facility"]
    heated_year_round: bool = True
    freeze_exposed_plumbing: bool = False
    sprinkler_type: Literal["none", "wet", "dry"] = "none"
    unit_count: int | None = None
    scheduled_closures: list[dict] = Field(default_factory=list)  # [{label, start, end}]
    notes: str = ""
    provenance: Provenance = "SYNTHETIC"


class CoverageNote(BaseModel):
    key: str
    title: str
    plain: str
    related_codes: list[str] = Field(default_factory=list)


class Claim(BaseModel):
    id: str
    policy_id: str
    date: date
    peril: str
    cause: str
    paid_usd: int
    provenance: Provenance = "SYNTHETIC"


class Proof(BaseModel):
    id: str
    level: Literal["E0", "E1", "E2", "E3", "E4"]
    type: Literal["attest", "photo", "document", "review", "sensor"]
    captured_at: datetime
    lat: float | None = None
    lon: float | None = None
    sha256: str
    uri: str | None = None
    by_user: str


class HistoricTask(BaseModel):
    """Seeded task history (closed items) so readiness rings and agent/underwriter views have depth."""

    id: str
    account_id: str
    rule_id: str
    title: str
    status: Literal["done", "declined", "expired"]
    opened_at: datetime
    closed_at: datetime
    asset_id: str | None = None
    proof_level: Literal["E0", "E1", "E2", "E3", "E4"] | None = None
    visibility: Literal["private", "shared"] = "private"
    provenance: Provenance = "SYNTHETIC"


class Device(BaseModel):
    id: str
    location_id: str
    vendor: Literal["simulated", "flo", "phyn", "leakbot", "generic"] = "simulated"
    model: str
    label: str
    unit_label: str | None = None
    status: Literal["available", "connected", "offline"] = "available"
    supports_shutoff: bool = True
    provenance: Provenance = "SIMULATED"


class GlossaryTerm(BaseModel):
    term: str
    plain: str
    related_codes: list[str] = Field(default_factory=list)


class WeatherAlert(BaseModel):
    id: str
    event: str
    severity: str | None = None
    urgency: str | None = None
    headline: str
    description: str = ""
    onset: datetime | None = None
    ends: datetime | None = None
    expires: datetime | None = None
    area_desc: str = ""
    source: Literal["NWS", "SCENARIO"] = "NWS"
    provenance: Provenance = "LIVE"


class DailyForecast(BaseModel):
    date: date
    max_f: float | None = None
    min_f: float | None = None
    precip_in: float | None = None
    precip_prob: int | None = None
    short: str | None = None
    source: str = "NWS"


class HourlyForecast(BaseModel):
    start: datetime
    temp_f: float
    precip_prob: int | None = None
    short: str | None = None


class Forecast(BaseModel):
    location_id: str
    fetched_at: datetime
    daily: list[DailyForecast]
    hourly: list[HourlyForecast] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    provenance: Provenance = "LIVE"


class Task(BaseModel):
    id: str
    rule_id: str
    account_id: str
    policy_id: str
    location_id: str
    asset_id: str | None = None
    source: Literal["rule", "insurer", "agent"] = "rule"
    title: str
    why: str
    steps: list[str]
    priority: Literal["high", "medium", "low"]
    score: float = 0.0
    est_minutes: int | None = None
    est_cost_usd: tuple[int, int] | None = None
    peril: str = "water"
    coverage_note_key: str | None = None
    coverage_codes: list[str] = Field(default_factory=list)
    proof_default_level: Literal["E0", "E1", "E2", "E3", "E4"] = "E1"
    proof_accepted: list[str] = Field(default_factory=lambda: ["E0", "E1"])
    status: Literal["open", "done", "deferred", "declined", "expired"] = "open"
    defer_until: datetime | None = None
    expires_after_hours: int = 168
    cooldown_days: int = 30
    bucket: Literal["do_now", "coming_up"] = "coming_up"
    relevant_date: date | None = None
    due_at: datetime | None = None
    opened_at: datetime
    closed_at: datetime | None = None
    inputs_snapshot: dict = Field(default_factory=dict)
    proof: list[Proof] = Field(default_factory=list)
    visibility: Literal["private", "shared"] = "private"
    provenance: Provenance = "SYNTHETIC"
    wording_provenance: Literal["AI"] | None = None  # set only when AI phrased the text


class Alert(BaseModel):
    id: str
    account_id: str
    kind: Literal["weather", "task", "device", "agent"]
    severity: Literal["info", "watch", "warning", "critical"]
    title: str
    body: str
    deep_link: str | None = None
    dedupe_key: str
    created_at: datetime
    sent_channels: list[str] = Field(default_factory=list)
    read_at: datetime | None = None
    provenance: Provenance = "LIVE"
