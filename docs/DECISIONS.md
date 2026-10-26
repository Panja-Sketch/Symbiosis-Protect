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
