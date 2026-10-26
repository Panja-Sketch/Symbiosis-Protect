"""Generate + validate data/seed/*.json from scripts/seedgen (validated against api/app/models.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "api"))

from app import models as m  # noqa: E402
from seedgen import entities as e  # noqa: E402
from seedgen import glossary as g  # noqa: E402
from seedgen import policies as p  # noqa: E402

from lib import SEED, write_json  # noqa: E402


def dump(models):
    return [x.model_dump(mode="json") for x in models]


def main():
    write_json(SEED / "agents.json", dump(m.Agent(**a) for a in e.AGENTS))
    write_json(SEED / "accounts.json", dump(m.Account(**a) for a in e.ACCOUNTS))
    write_json(SEED / "policies.json", dump(m.Policy(**x) for x in p.policies()))
    write_json(SEED / "assets.json", dump(m.Asset(**a) for a in e.assets()))
    write_json(SEED / "property_profiles.json", dump(m.PropertyProfile(**x) for x in e.profiles()))
    write_json(SEED / "claims.json", dump(m.Claim(**c) for c in e.claims()))
    write_json(SEED / "task_history.json", dump(m.HistoricTask(**t) for t in e.task_history()))
    write_json(SEED / "devices.json", dump(m.Device(**d) for d in e.devices()))
    write_json(SEED / "glossary.json", dump(m.GlossaryTerm(term=t, plain=pl, related_codes=rc) for t, pl, rc in g.GLOSSARY))
    write_json(SEED / "coverage_notes.json", dump(
        m.CoverageNote(key=k, title=t, plain=pl, related_codes=rc) for k, t, pl, rc in g.COVERAGE_NOTES))
    print("seed written to", SEED)


if __name__ == "__main__":
    main()
