# CLAUDE.md — standing rules for this repo

Project: **Symbiosis Protect — Arizona demo**. Full spec: `BUILD_SPEC.md` (read it first; it is the source of truth).

## Working rules
- Build in the phase order in `BUILD_SPEC.md` §13. Finish each phase's Definition of Done before moving on.
- After each phase: run `make lint test`, commit `phase-N: <summary>`, update `docs/STATUS.md`.
- Record any deviation or judgment call in `docs/DECISIONS.md` (date, decision, reason).
- Local first. Do not run any `gcloud` deploy command until Phase 9 and until the owner says "deploy".

## Truthfulness rules (non-negotiable)
- Every data element in the UI carries a provenance label: LIVE · HISTORIC · SYNTHETIC · SIMULATED · AI.
- Never present simulated or synthetic data as live or real. Never invent statistics in UI copy; facts go in `docs/SOURCES.md` with a link.
- The AI never decides tasks, priorities, verification, or coverage. Rules decide; AI only phrases text and answers from provided policy data with citations. Always keep a deterministic fallback.
- AI answers must not promise a loss will be covered; route coverage decisions to the agent.
- Do not copy ISO or any insurer's policy wording; write original plain-language summaries.
- No real insurer logos or real people's addresses. Carrier name comes from `CARRIER_NAME`.

## Engineering rules
- Stack: Next.js 14 App Router + TS + Tailwind + shadcn/ui (web); FastAPI + Pydantic v2, Python 3.12 (api); Firestore (emulator locally); Vertex AI Gemini via `google-genai` with service-account auth.
- All thresholds and recommendations live in YAML playbooks under `api/app/playbooks/`. No magic numbers in code.
- Every external dependency goes through an adapter interface (`BUILD_SPEC.md` §7.3).
- NWS requests must send the `User-Agent` from `NWS_USER_AGENT`. Cache per §7.1.
- Secrets never committed; `.env.example` lists variable names only.
- Mobile-first: test every screen at 390×844 and 1440×900. Accessibility: WCAG 2.2 AA, axe clean.
- Keep costs inside the $200 GCP credit: scale-to-zero, no BigQuery/Pub/Sub in v1, budget alerts.

## Definition of "demo-ready"
The 7-minute script in `BUILD_SPEC.md` §15 runs end-to-end on phone and laptop, with the Scenario Director, without errors.
