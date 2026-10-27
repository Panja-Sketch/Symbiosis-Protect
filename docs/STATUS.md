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

## Phase 4 — Proof (2026-10-25) ✅
- Task completion with E0 one-tap (signed attestation hash), E1 photo (camera on phones; time = server clock, device time recorded separately; geolocation only if permitted, otherwise recorded as "not shared"), E2 document/PDF. SHA-256 computed server-side, blob stored via `BlobStorage` (local disk now, GCS in Phase 9), magic-byte type check, 8 MB cap, coordinate validation.
- `GET /proofs/{id}/file` re-verifies the hash before serving (409 on mismatch); `GET /accounts/{id}/evidence`; Evidence tab in Tasks with hash, location, level mix, download.
- Verified: pytest 67 (hash, tamper, type sniffing, size, coordinates, E0/E1 rules); Playwright 42/42 incl. photo → Evidence hash equals the client-computed SHA-256 → re-download byte-identical, and no-location path.

## Phase 5 — AI assistant (2026-10-25) ✅
- `POST /assistant/ask`, `GET /assistant/starters`. Grounded on the account's policy summary + glossary + coverage notes + open tasks only (no web, no other accounts). Output schema `{answer_plain, cited_coverage_codes, confidence, needs_agent, suggested_actions}` (+ glossary citations).
- `TemplateExplainer` (deterministic retrieval over policy items with synonym expansion, coverage gating, title boost) is the always-on fallback; `GeminiExplainer` (google-genai, Vertex, service-account auth, JSON schema, 500 max tokens, temperature 0.2) is used only when `AI_ENABLED=true`; every model answer is validated by `guard.py` and replaced on failure.
- Per-account rate limit (`AI_ASKS_PER_HOUR`, 429), response cache by (policy, normalized question), `ai_logs` (prompt hash only, model, latency, fallback used and why).
- UI: starter chips per LOB, answer bubbles with provenance pill, cited-coverage chips that jump to the coverage card, agent hand-off (email/call), refusal path.
- Verified: pytest 103 (18 scripted Q&A across all 6 personas + refusals, claim/pricing/legal hand-off, cross-account leak check, guard rejection of 5 bad-answer classes, outage fallback, cache, rate limit, log contents, all starters pass the guard); Playwright 46/46.
- Not verified: a live Gemini call (no Vertex credentials on this machine). The Gemini path is covered with a fake client; verify live in Phase 9 with the service account.

## Phase 6 — Sense mode (2026-10-25) ✅
- `SimulatedWaterDevice` (5 s ticks, deterministic jitter, water / stockroom-temperature / cooler-temperature profiles, valve shutoff) behind the `DeviceAdapter` shape; all output labelled SIMULATED.
- Case state machine detected → alerted → acting → verifying → verified | not_improving | inconclusive → reopened, with timeline, critical device alert, sensor-linked task, `water_leak` event that makes the existing rule create "Leak in 3B — check unit 2B below", E4 sensor proof with manifest SHA-256 and stored evidence for the Phase 7 export.
- API: `/devices`, `/devices/connect`, `/devices/{id}/readings|command`, `/accounts/{id}/cases`, `/cases/{id}` (+`report-fix`, `shutoff`, `acting`), `/director/device`; scheduler polls connected devices every 10 s.
- UI: Sense console (connect, live tiles, sparkline, case timeline and actions, demo controls).
- Verified: pytest 115 (closed loop incl. recurrence reopen, failed fix = not_improving, stale data = inconclusive not verified, temp probes, no-valve device, determinism); Playwright 50/50 incl. a real-time leak → verified → reopened run on both viewports.

## Phase 7 — Roles (2026-10-25) ✅
- Agent book (6 clients: active alerts with provenance, high-risk forecast days, shared open high-priority tasks, shared completion %, proof mix, Sense status, rule-composed renewal talking points) and Underwriter portfolio (participation, task completion, proof-level mix, active alerts by county, Sense cases, accounts table) with account drill-down (shared tasks/history/proofs/cases, synthetic claims).
- Sharing rules enforced in the API: per-task share toggle, account default (Settings), declined = always private, insurer/agent-issued = always visible and uncapped; proof visibility follows its task.
- Insurer/agent-issued recommendations (`POST /tasks/issue`) with alert to the policyholder; evidence export `POST /evidence/{policy}/export` → ZIP with `manifest.json`, `manifest.sha256` and per-file SHA-256 (shared-only for underwriter/agent, everything for the owner), persisted as `EvidencePackage`.
- Settings screen is real now (channels, quiet hours, sharing default).
- Verified: pytest 128 (role gates, private hidden, toggle, declined, portfolio tiles, issue + cap bypass, export zip re-hash, scope, sense evidence, preferences); Playwright 72/72 incl. role switch + redirects, same SHA-256 across policyholder/underwriter views, privacy toggle, issue → policyholder labelled card, export download + hash, agent book alert flags, axe on role pages.

## Phase 8 — Scenario Director (2026-10-26) ✅
- `/director` page + floating Director button: Freeze (Flagstaff), Extreme Heat (Phoenix metro), Severe Thunderstorm + Flash Flood (Tempe/Mesa), Dust Storm (I-10), slow leak (Mesa Palms 3B), burst (Maya's laundry), cooler drift (Desert Bloom), stockroom cold (Ponderosa), Reset, time-travel presets (July 18, Dec 22), day slider, live demo-clock and active-injection display. Everything injected is labelled SIMULATED.
- `GET /director/state`; Reset now also clears readings, device state, cases, proofs and rate-limit counters and restores seed data.
- Fixed along the way: hydration mismatch in the Sense "updated Ns ago" label (found by the console-error check), UTF-8 read of scenarios.yaml, event-driven task priority.
- Verified: **full BUILD_SPEC section 15 demo script runs end to end in ~110 s (limit 8 min) with zero console/page errors**, laptop + a 390×844 phone context (heat → Coverage Lens → Ask → photo proof on phone → storm/flood → freeze + holiday closure → Sense leak verified + reopened → agent + underwriter + export). pytest 129, Playwright 75/75.

## Phase 9 — Deploy (2026-10-26/27) ✅ deployed
- **Live:** web https://symbiosis-web-5ymav3tr5q-uc.a.run.app · API https://symbiosis-api-5ymav3tr5q-uc.a.run.app (`/docs` for OpenAPI; health at `/api/v1/healthz` because Cloud Run reserves `/healthz`).
- **Project:** new dedicated project `symbiosis-protect-az-26` (us-central1) linked to billing account 016A9D-BC0A62-2370A3. The existing `symbiosis-ai-2026` project already runs another Symbiosis app with identically named services and a default Firestore database, so it was left untouched.
- Created: Cloud Run `symbiosis-web` (min 0, max 2, 512 MiB) and `symbiosis-api` (min 0, max 1, 1 GiB), Firestore native + TTL on `cache.expires_at`, bucket `symbiosis-protect-az-26-proofs` (30-day delete), Artifact Registry, three service accounts (API: datastore.user, aiplatform.user, bucket objectAdmin; web and scheduler: no project roles), Secret Manager session secret, Cloud Scheduler `symbiosis-evaluate` every 15 min with OIDC, **budget alerts at $25/$50/$100/$150**.
- Verified live: Firestore persistence across instances, photo proof to GCS and byte-identical download through the web proxy, Scheduler OIDC call returns 200, **live Gemini (`gemini-3.5-flash-lite`, global endpoint) answers pass the guard** (gemini-2.x returned 404 for this project), live NWS + Open-Meteo, Lighthouse mobile on the public URL: performance 94–96, accessibility 100, best-practices 100, CLS 0. Playwright against the public URL: full suite earlier 62/75 with the remaining 13 caused by my test harness (it signed cookies with a secret that lacked the stored trailing newline); after switching the harness to server-issued cookies, roles + Sense + full demo script = 27/27, demo script 127 s on phone+laptop contexts. Core specs 56 passed on the same run.
- Bugs found only by deploying and fixed: the cloud API used the in-memory store (now `STORE_BACKEND=firestore`); `.gitignore` pattern `coverage/` had kept `web/app/coverage` out of git and the build upload (now anchored, `.gcloudignore` added); pnpm 12 refused the install over an ignored build script; Link prefetch caused continuous dynamic SSR hits (`prefetch={false}`).
- Not verified: Docker images built locally (Cloud Build built them instead); a physical-phone test.
- Cost note: scale-to-zero everything; the Scheduler job runs every 15 min — run `python scripts/tasks.py scheduler-pause` when not demoing.
