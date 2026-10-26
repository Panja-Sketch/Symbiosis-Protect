# DECISIONS

| Date | Decision | Reason |
|---|---|---|
| 2026-10-25 | `Makefile` delegates to `scripts/tasks.py`; on Windows run `python scripts/tasks.py <task>` | `make` is not installed on the owner's Windows machine; Python runner works everywhere |
| 2026-10-25 | Firestore emulator via `npx firebase-tools emulators:start --only firestore` (Java 21 present) | No global firebase CLI needed |
| 2026-10-25 | Python deps via `uv` (api/pyproject.toml); web via `pnpm` | Spec §3 |
| 2026-10-25 | Local `.env` (git-ignored) created with demo values; `.env.example` has names only | CLAUDE.md secrets rule |
| 2026-10-25 | Open-Meteo free tier is non-commercial; fine for demo, production needs commercial plan or NOAA/NCEI | Spec §7.2 |
| 2026-10-25 | Web dev server on port 3100 (not 3000) | Port 3000 was occupied by an unrelated process on the owner's machine |
