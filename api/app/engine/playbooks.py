"""Load + validate YAML playbooks. All thresholds live in YAML, never in Python."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator

PLAYBOOK_DIR = Path(__file__).resolve().parent.parent / "playbooks"
RULE_FILES = ("homeowners.yaml", "bop.yaml", "cre.yaml", "agribusiness.yaml")

CONDITION_KEYS = {
    "always", "nws_group", "nws_event", "forecast_max_temp_f", "forecast_min_temp_f", "forecast_precip_in",
    "season", "asset_age_years", "asset_last_service_months", "asset_attr", "closure_within_days",
    "recent_event", "register_incomplete", "units_match",
}
APPLIES_KEYS = {
    "has_central_ac", "occupancy", "sprinkler_type", "freeze_exposed_plumbing", "asset_exists",
    "elevation_gte_high_country",
}


class ProofSpec(BaseModel):
    default_level: str = "E1"
    accepted: list[str] = Field(default_factory=lambda: ["E0", "E1"])


class Rule(BaseModel):
    id: str
    lob: list[str]
    peril: str
    title: str
    why_template: str
    applies_if: dict = Field(default_factory=dict)
    scope: str = "location"  # location | asset
    asset_type: str | list[str] | None = None
    when: dict
    steps: list[str]
    est_minutes: int | None = None
    est_cost_usd: tuple[int, int] | None = None
    proof: ProofSpec = ProofSpec()
    coverage_note_key: str | None = None
    coverage_codes: list[str] = Field(default_factory=list)
    priority: str = "medium"
    expires_after_hours: int = 168
    cooldown_days: int = 30
    sources: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self):
        bad = set(self.applies_if) - APPLIES_KEYS
        if bad:
            raise ValueError(f"{self.id}: unknown applies_if keys {bad}")
        if set(self.when) - {"any", "all", "and"}:
            raise ValueError(f"{self.id}: when must use any/all")
        for key in ("any", "all", "and"):
            for cond in self.when.get(key, []):
                if len(cond) != 1 or next(iter(cond)) not in CONDITION_KEYS:
                    raise ValueError(f"{self.id}: bad condition {cond}")
        if self.scope == "asset" and not self.asset_type:
            raise ValueError(f"{self.id}: asset-scoped rule needs asset_type")
        return self

    @property
    def asset_types(self) -> list[str]:
        t = self.asset_type
        return [] if t is None else [t] if isinstance(t, str) else list(t)


def load_yaml(name: str) -> dict:
    return yaml.safe_load((PLAYBOOK_DIR / name).read_text(encoding="utf-8"))


def load_rules() -> list[Rule]:
    rules = [Rule(**r) for f in RULE_FILES for r in load_yaml(f)]
    ids = [r.id for r in rules]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate rule ids")
    return rules


class Config(BaseModel):
    thresholds: dict
    scoring: dict
    proof_policy: dict


def load_config() -> Config:
    return Config(thresholds=load_yaml("thresholds.yaml"), scoring=load_yaml("scoring.yaml"),
                  proof_policy=load_yaml("proof_policy.yaml"))
