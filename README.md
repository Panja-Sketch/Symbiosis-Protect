# Symbiosis Protect — Arizona demo
Spec: `BUILD_SPEC.md` · Rules: `CLAUDE.md` · Status: `docs/STATUS.md`

```
python scripts/tasks.py dev    # (or: make dev) emulator + api :8000 + web :3000
python scripts/tasks.py lint
python scripts/tasks.py test      # pytest + vitest
python scripts/tasks.py e2e       # Playwright at 390x844 and 1440x900 + axe + the full demo script
python scripts/tasks.py data      # rebuild datasets and seed JSON (downloads cached in data/raw)
```

Demo: open http://localhost:3100, use the identity switcher (persona + role), and the Director button for scenarios.
Deploy: see `docs/DEPLOY.md` (prepared, not run). Integration contracts: `docs/INTEGRATION.md`. Decisions: `docs/DECISIONS.md`.
