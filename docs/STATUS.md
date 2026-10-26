# STATUS

## Phase 0 — Scaffold (2026-10-25) ✅
- Works: monorepo (`web/` Next 14 + Tailwind, `api/` FastAPI + Pydantic v2, `data/`, `scripts/`, `infra/`, `docs/`); `dev` starts Firestore emulator + API :8000 + web :3100 and reports health; `lint` and `test` pass; `.env.example` has names only.
- Run on Windows: `python scripts/tasks.py <dev|seed|lint|test>` (`make` forwards to this).
- Stubbed: `seed` (Phase 1), `deploy` (gated to Phase 9 + owner saying "deploy").
- Gaps: shadcn/ui, Vitest, Playwright arrive in Phase 3.
