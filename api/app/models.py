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
