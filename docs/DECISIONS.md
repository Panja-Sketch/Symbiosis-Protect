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
