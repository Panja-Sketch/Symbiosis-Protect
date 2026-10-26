# DECISIONS

| Date | Decision | Reason |
|---|---|---|
| 2026-10-25 | `Makefile` delegates to `scripts/tasks.py`; on Windows run `python scripts/tasks.py <task>` | `make` is not installed on the owner's Windows machine; Python runner works everywhere |
| 2026-10-25 | Firestore emulator via `npx firebase-tools emulators:start --only firestore` (Java 21 present) | No global firebase CLI needed |
| 2026-10-25 | Python deps via `uv` (api/pyproject.toml); web via `pnpm` | Spec §3 |
| 2026-10-25 | Local `.env` (git-ignored) created with demo values; `.env.example` has names only | CLAUDE.md secrets rule |
| 2026-10-25 | Open-Meteo free tier is non-commercial; fine for demo, production needs commercial plan or NOAA/NCEI | Spec §7.2 |
| 2026-10-25 | Web dev server on port 3100 (not 3000) | Port 3000 was occupied by an unrelated process on the owner's machine |
| 2026-10-25 | NRI hazard prefix IFLD (Inland Flooding) used where spec says riverine flood (RFLD) | NRI v1.20 (Dec 2025) has no RFLD columns |
| 2026-10-25 | NRI tract file via fema.gov v120 URL; downloads use curl | fema.gov returns Access Denied to python HTTP clients |
| 2026-10-25 | NCEI events matched by county FIPS (CZ_TYPE C) plus the location's own NWS forecast zone number (CZ_TYPE Z) | Heat/freeze products are issued by zone, so county-only matching misses them |
| 2026-10-25 | Open-Meteo archive 1991-2025 per location; recent-5-yr = 2021-2025, climate normals = 1991-2020 | Extra dataset beyond spec: monthly normals give 'vs normal' context. ERA5 grid values run slightly cooler than station records at the urban core; labelled HISTORIC reanalysis |
| 2026-10-25 | 26 playbook rules (spec minimum ≈24): extra `az.bop.water_heater_age`, `az.bop.sprinkler_annual_inspection`, `az.bop.snow_load_roof` (BOP) | Spec asks for ≥3 tasks per persona on any day; BOP personas had only 1 always-on rule |
| 2026-10-25 | Rules are asset-scoped when they need per-asset tasks (`scope: asset`); one task per matching asset | Lets cooler 2 be flagged while cooler 1 (serviced Aug 2026) is not |
| 2026-10-25 | Cooldown uses completed/declined history (live + seeded), ignoring entries dated after the Director's time-travel clock | Keeps July-18 time travel from seeing "future" completions |
| 2026-10-25 | Proof policy config lives at `api/app/playbooks/proof_policy.yaml` (spec §16 said `config/proof_policy.yaml`) | Keeps all YAML config in one folder the API packages |
| 2026-10-25 | Time-travel mode builds the forecast from 1991–2020 monthly normals, labelled SIMULATED | A live October forecast cannot represent July; never pass simulated weather off as live |
| 2026-10-25 | Task `provenance` = provenance of the inputs that triggered it (SIMULATED if any simulated input, else LIVE, else SYNTHETIC/HISTORIC); `wording_provenance` is `AI` only when AI phrased text | Rule text is deterministic templates, so it is not labelled AI |
| 2026-10-25 | Task/seed score bounds: exposure capped at 2.0 (scoring.yaml) | Prevents one claim-heavy persona from dominating all rankings |
| 2026-10-25 | Photo proof uses an <input type=file capture=environment> (native camera on phones, file picker on laptops) rather than a getUserMedia live stream | Simpler, works on every browser, still timestamps (server clock authoritative; device clock stored separately) and hashes server-side |
| 2026-10-25 | File type is sniffed from magic bytes; E1 accepts PNG/JPEG/WebP, E2 also PDF; 8 MB cap (MAX_PROOF_BYTES) | Do not trust client content-type |
| 2026-10-25 | Proof download re-hashes the stored blob and returns 409 if it no longer matches its recorded SHA-256 | Tamper evidence for the evidence package |
| 2026-10-25 | Assistant works without Gemini: `AI_ENABLED=false` by default, so locally every answer is the deterministic TemplateExplainer and is labelled SYNTHETIC (not AI). Gemini is used only when `AI_ENABLED=true` and Vertex credentials exist | No credentials on the dev machine; the truthfulness rule says never label rule-composed text as AI |
| 2026-10-25 | Claim-decision, pricing and legal questions never reach the model; they get a deterministic hand-off answer | Spec section 8 rule 3; removes the risk of a model promising coverage |
| 2026-10-25 | Every model answer must pass `ai/guard.py` (known codes, no promise phrases, hedge present, dollar figures present in cited items, citation-or-handoff) or the template answer replaces it, with the reason logged in `ai_logs` | Spec section 8 rule 4 enforced in code |
| 2026-10-25 | Readings are stored one document per 5 s tick with all metrics (flow_lpm, leak, temp_f, humidity), not one doc per metric | Fewer writes; the Reading contract is otherwise unchanged |
| 2026-10-25 | Sense device state changes are serialized with an in-process RLock; with more than one Cloud Run instance this would need a Firestore transaction | Sync FastAPI routes run in a thread pool; concurrent polls caused a lost-update. Demo runs one API instance |
| 2026-10-25 | Verification: 6 consecutive clean readings after the fix report; 8 consecutive bad readings = not_improving; stale (30 s) or missing data, or no verdict in 5 min = inconclusive; recurrence within 24 h reopens | Spec section 10; all values in playbooks/sense.yaml |
| 2026-10-25 | Sense tasks are closed only by sensor evidence (E4, SHA-256 of the readings manifest), never by a one-tap attestation | A sensor-verified fix must not be self-attested |
| 2026-10-25 | Role is passed to the API as X-Demo-Role from the signed demo-identity cookie; the privacy filter (shared + insurer/agent-issued only, never declined) is enforced in the API (app/roles.py), not just the UI | Demo-grade auth; swap for Firebase Auth when AUTH_MODE=firebase |
| 2026-10-25 | Agent and underwriter see the same shared-only slice of a client; the agent additionally sees policy gaps and claims for renewal talking points | Spec section 9.4/9.5 plus section 16 default (underwriter never sees declined items) |
| 2026-10-25 | Seeded Luis (P2) has share_default=false and private history so the privacy rule is demonstrable; the other five share by default | Shows participation 5/6 and hidden private items |
| 2026-10-25 | Renewal talking points are rule-composed (labelled SYNTHETIC), not AI-phrased; AI polishing is not wired | Truthfulness rule: do not label rule text as AI; AI phrasing can be added later with the numbers-preserved guard already in roles.py |
| 2026-10-25 | Insurer/agent-issued tasks are shared, always do_now and exempt from the cap, and cannot be made private by the policyholder | Spec section 5.3 |
