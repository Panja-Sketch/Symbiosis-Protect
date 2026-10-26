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

## Phase 2 — Engine (2026-10-25) ✅
- Adapters: `NWSProvider` (User-Agent from `NWS_USER_AGENT`; cache points 7 d / forecast 30 min / alerts 5 min), `OpenMeteoProvider`, `CompositeWeatherProvider` (NWS temps + Open-Meteo precip, graceful fallback), `ScenarioProvider` (Director injections + time-travel, always SIMULATED), notifier chain (in-app + console e-mail with quiet hours), `MemoryCache`/`FirestoreCache`, `MemoryStore`/`FirestoreStore`.
- Engine: 26 YAML playbooks, 14 condition types, deterministic scoring (severity × priority × urgency × exposure × (1 − completion recency)), Do-now cap 3, task lifecycle (create/refresh/expire/defer/decline/complete with cooldowns), alert dedupe, APScheduler job (every `SCHEDULER_MINUTES`), `POST /api/v1/internal/evaluate`.
- API: personas, accounts, policies, weather, alerts, history, risk-ribbon, tasks (list/complete[E0]/defer/decline), alerts (list/read), director (inject/time-travel/reset), internal evaluate.
- Verified: 58 tests pass (golden rule tests per persona and scenario, adapters with mocked NWS incl. User-Agent assertion and cache hits, API flows). Live check (`RUN_LIVE=1`): NWS + Open-Meteo succeed for all 6 locations; with real Oct-25 forecast the Flagstaff sprinkler-freeze task fires with LIVE provenance.
- Not yet: photo proof (Phase 4), AI wording (Phase 5), devices/cases (Phase 6), roles (Phase 7), full Director UI (Phase 8). Multipart `complete` arrives in Phase 4 (JSON E0 now).

## Phase 3 — UI core (2026-10-25) ✅
- Web: Desert Instrument tokens (light + dark, contrast-checked text variants), Inter + Fraunces, phone tab bar / laptop sidebar, demo-identity switcher (HMAC-signed cookie, labelled "not a login"), provenance pills with tooltips on every data block.
- Screens: Home (Risk Ribbon with task pins, Do-now ≤3, weather + NWS alerts, readiness ring, history teaser), Tasks (Do now / Coming up / Done + seeded history), Coverage Lens sheet (what could happen · what your policy says with coverage chips · what to do · why now · proof actions), Coverage, My place (editable asset ages → tasks re-evaluate; Recharts history; FEMA NRI), Alerts (filters, mark read), More. Ask/Sense/Settings are honest "arrives in Phase N" pages.
- API additions: `GET /accounts/{id}/assets`, `PATCH /assets/{id}`; Director reset now restores seeded assets.
- Verified: Playwright 36/36 at 390×844 and 1440×900 including axe WCAG 2.2 AA on 11 pages, no horizontal scroll, heat-scenario → SIMULATED task → Coverage Lens → complete → readiness updates, persona switch, asset edit. Vitest 4, pytest 60.
- Gaps: Lighthouse score not yet measured; Agent/Underwriter roles listed in the switcher but views arrive in Phase 7; photo/doc proof in Phase 4.
