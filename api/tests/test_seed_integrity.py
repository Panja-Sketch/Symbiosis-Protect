import json

from app.seed import COLLECTIONS, load_derived, load_seed
from app.seed import SEED as SEED_DIR

SEED = load_seed()
LOC_IDS = {r["id"] for r in SEED["locations"]}
ACCT_IDS = {r["id"] for r in SEED["accounts"]}
POLICY_IDS = {r["id"] for r in SEED["policies"]}
ALL_CODES = (
    {c["code"] for p in SEED["policies"] for c in p["coverages"]}
    | {e["code"] for p in SEED["policies"] for e in p["endorsements"]}
    | {x["code"] for p in SEED["policies"] for x in p["exclusions_plain"]}
)


def test_six_personas_with_one_policy_each():
    assert len(SEED["accounts"]) == 6 and len(SEED["policies"]) == 6 and len(SEED["locations"]) == 6
    assert {p["account_id"] for p in SEED["policies"]} == ACCT_IDS


def test_personal_lines_are_flagged_as_preview():
    flags = {p["lob"]: p["preview_flag"] for p in SEED["policies"]}
    assert flags["homeowners"] and flags["dwelling_fire"]
    assert not flags["bop"] and not flags["agribusiness"] and not flags["commercial_real_estate"]


def test_foreign_keys():
    assert {a["location_id"] for a in SEED["assets"]} <= LOC_IDS
    assert {c["policy_id"] for c in SEED["claims"]} <= POLICY_IDS
    assert {t["account_id"] for t in SEED["task_history"]} <= ACCT_IDS
    assert {d["location_id"] for d in SEED["devices"]} <= LOC_IDS
    assert {a["agent_id"] for a in SEED["accounts"]} <= {a["id"] for a in SEED["agents"]}
    assert {p["location_id"] for p in SEED["property_profiles"]} == LOC_IDS


def test_unit_register_is_48_units_with_3b_above_2b():
    units = {a["unit_label"]: a for a in SEED["assets"] if a["type"] == "unit"}
    assert len(units) == 48 and units["3B"]["floor"] == 3 and units["2B"]["floor"] == 2


def test_notes_and_glossary_reference_real_codes():
    for n in SEED["coverage_notes"]:
        assert set(n["related_codes"]) <= ALL_CODES, n["key"]
    for t in SEED["glossary"]:
        assert set(t["related_codes"]) <= ALL_CODES, t["term"]


def test_every_coverage_has_plain_text_and_no_promises():
    banned = ("will be covered", "is guaranteed", "always covered")
    for p in SEED["policies"]:
        assert p["coverages"] and p["exclusions_plain"]
        blob = json.dumps(p).lower()
        assert not any(b in blob for b in banned)


def test_no_real_insurer_names_in_seed():
    blob = json.dumps(SEED).lower()
    for name in ("state farm", "progressive", "geico", "allstate", "liberty mutual", "travelers"):
        assert name not in blob


def test_derived_files_exist_and_are_labelled():
    d = load_derived()
    for loc in LOC_IDS:
        h = d[f"history_{loc}"]
        assert h["provenance"] == "HISTORIC" and len(h["years"]) == 5 and len(h["monthly_normals"]) == 12
    assert d["storm_events_az"]["provenance"] == "HISTORIC"
    assert set(d["storm_events_az"]["locations"]) == LOC_IDS
    assert set(d["nri_az"]["locations"]) == LOC_IDS


def test_climate_sanity_matches_arizona_geography():
    d = load_derived()

    def hot(loc):
        return d[f"history_{loc}"]["avg_per_year"]["days_ge_110f"]

    def cold(loc):
        return d[f"history_{loc}"]["avg_per_year"]["nights_le_28f"]

    assert hot("loc-p6") > hot("loc-p1") > hot("loc-p4") == 0
    assert cold("loc-p4") > 30 and cold("loc-p1") < 3


def test_every_collection_has_a_file():
    assert all((SEED_DIR / f).exists() for f, _, _ in COLLECTIONS.values())
