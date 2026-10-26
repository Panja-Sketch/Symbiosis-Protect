"""Load validated seed + derived data into Firestore (emulator locally). `python -m app.seed`."""

import json
from pathlib import Path

from app import models as m

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "data" / "seed"
DERIVED = ROOT / "data" / "derived"

# collection -> (file, model, id field)
COLLECTIONS = {
    "agents": ("agents.json", m.Agent, "id"),
    "accounts": ("accounts.json", m.Account, "id"),
    "locations": ("locations.json", m.Location, "id"),
    "policies": ("policies.json", m.Policy, "id"),
    "assets": ("assets.json", m.Asset, "id"),
    "property_profiles": ("property_profiles.json", m.PropertyProfile, "location_id"),
    "claims": ("claims.json", m.Claim, "id"),
    "task_history": ("task_history.json", m.HistoricTask, "id"),
    "devices": ("devices.json", m.Device, "id"),
    "glossary": ("glossary.json", m.GlossaryTerm, "term"),
    "coverage_notes": ("coverage_notes.json", m.CoverageNote, "key"),
}


def load_seed() -> dict[str, list[dict]]:
    """Read + validate every seed file. Raises pydantic.ValidationError on bad data."""
    out = {}
    for name, (fname, model, _) in COLLECTIONS.items():
        rows = json.loads((SEED / fname).read_text(encoding="utf-8"))
        out[name] = [model(**r).model_dump(mode="json") for r in rows]
    return out


def load_derived() -> dict[str, dict]:
    """Derived datasets keyed by doc id: history_<loc>, storm_events_az, nri_az."""
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(DERIVED.glob("*.json"))}


def _doc_id(value: str) -> str:
    return value.replace("/", "_")


def seed_store(store) -> dict[str, int]:
    """Write all validated seed + derived docs into any Store (memory or Firestore)."""
    counts = {}
    for name, rows in load_seed().items():
        id_field = COLLECTIONS[name][2]
        for row in rows:
            store.put(name, _doc_id(str(row[id_field])), row)
        counts[name] = len(rows)
    derived = load_derived()
    for doc_id, body in derived.items():
        store.put("derived", doc_id, body)
    counts["derived"] = len(derived)
    return counts


def seed_firestore(db=None) -> dict[str, int]:
    from app.db import get_db
    from app.store import FirestoreStore

    return seed_store(FirestoreStore(db or get_db()))


if __name__ == "__main__":
    from app.config import get_settings

    if not get_settings().firestore_emulator_host:
        raise SystemExit("Refusing to seed: FIRESTORE_EMULATOR_HOST is not set (local emulator only).")
    for k, v in seed_firestore().items():
        print(f"{k:18s} {v}")
