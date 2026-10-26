# STATUS

## Phase 0 — Scaffold (2026-10-25) ✅
- Works: monorepo (`web/` Next 14 + Tailwind, `api/` FastAPI + Pydantic v2, `data/`, `scripts/`, `infra/`, `docs/`); `dev` starts Firestore emulator + API :8000 + web :3100 and reports health; `lint` and `test` pass; `.env.example` has names only.
- Run on Windows: `python scripts/tasks.py <dev|seed|lint|test>` (`make` forwards to this).
- Stubbed: `seed` (Phase 1), `deploy` (gated to Phase 9 + owner saying "deploy").
- Gaps: shadcn/ui, Vitest, Playwright arrive in Phase 3.

## Phase 1 — Data (2026-10-25) ✅
- Derived (committed in `data/derived/`): `history_loc-p1..p6.json` (5-yr stats 2021–2025 + 1991–2020 monthly normals + records), `storm_events_az.json` (NCEI 2016–2025, per persona county/zone, 10-yr), `nri_az.json` (FEMA NRI v1.20 county + tract incl. AZ-tract percentiles).
- Seed (`data/seed/`): 6 locations (real NWS zone, tract, elevation), 6 accounts, 4 synthetic agents, 6 policies with original plain-language coverages/endorsements/exclusions, 75 assets (incl. 48-unit register for Mesa Palms), property profiles, 7 claims, 14 closed tasks, 7 simulated devices, 30-term glossary, 10 coverage notes.
- `python scripts/tasks.py data` rebuilds everything (raw downloads cached in git-ignored `data/raw/`); `python scripts/tasks.py seed` loads the Firestore emulator (refuses to run without `FIRESTORE_EMULATOR_HOST`).
- Tests: 19 pass (parsers, seed integrity/foreign keys, no-promise copy, climate sanity).
- Gaps: playbook YAML + rule engine (Phase 2); NRI values are county/tract level, not parcel level.
