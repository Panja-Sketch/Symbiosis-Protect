# DEPLOY (Phase 9) — deployed 2026-10-27

Deployed after the owner said "deploy". Project `symbiosis-protect-az-26`; web https://symbiosis-web-5ymav3tr5q-uc.a.run.app. The scripts are idempotent: re-run `infra/deploy.sh` to roll out a new version.

## What gets created (us-central1, scale to zero)
| Piece | Setting |
|---|---|
| Cloud Run `symbiosis-api` | min 0, **max 1** (see DECISIONS: Sense state is serialized in-process), 1 GiB, service account `symbiosis-api` |
| Cloud Run `symbiosis-web` | min 0, max 2, 512 MiB, service account `symbiosis-web` (no GCP roles) |
| Firestore | native mode; TTL on `cache.expires_at` |
| Cloud Storage | one bucket `${PROJECT_ID}-proofs`, objects deleted after 30 days |
| Cloud Scheduler | one job, every 15 min, `POST /api/v1/internal/evaluate` with an OIDC ID token; the API accepts only the scheduler service account |
| Secret Manager | `symbiosis-session-secret` (random) for the demo-identity cookie |
| Vertex AI | `roles/aiplatform.user` for the API service account; model `GEMINI_MODEL` (Flash-Lite class), ≤500 output tokens, 30 asks/hour/account, response cache |
| Not used | BigQuery, Pub/Sub, always-on instances |

## Steps (owner)
```bash
export PROJECT_ID=symbiosis-protect-demo            # an existing project with billing linked
export NWS_USER_AGENT='SymbiosisProtectDemo/0.1 (you@example.com)'
export BILLING_ACCOUNT=XXXXXX-XXXXXX-XXXXXX          # gcloud billing accounts list
gcloud auth login && gcloud config set project $PROJECT_ID

DRY_RUN=1 bash infra/deploy.sh        # review every command first
export OWNER_SAID_DEPLOY=yes
bash infra/budget.sh                  # alerts at $25 / $50 / $100 / $150
bash infra/deploy.sh                  # prints the public web URL when done
```
Windows without bash: `python scripts/tasks.py deploy|budget|scheduler-pause|scheduler-resume|destroy` (needs Git Bash). Pause the Scheduler when not demoing: `python scripts/tasks.py scheduler-pause`.

## Cost guardrails
- Cloud Run, Firestore, GCS, Scheduler (3 free jobs) and Secret Manager sit inside free tiers for demo traffic; the only metered item that can grow is Vertex AI (Flash-Lite, ≤500 tokens, rate-limited and cached) and Cloud Build minutes (two small builds per deploy).
- Budget alerts are email only; they do not stop spend. If an alert fires, run `scheduler-pause` and, if needed, `destroy` (or delete the project).
- `destroy.sh` removes the services, bucket, registry, secret and service accounts. It does **not** delete Firestore documents; delete the database in the console, or delete the project.

## Gotchas learned on the first deploy
- Do not reuse a project that already hosts another app: `symbiosis-ai-2026` has same-named services and a default Firestore DB. Use a fresh project.
- Cloud Run reserves `/healthz`; the API health check is `/api/v1/healthz`.
- The session secret in Secret Manager ends with a newline (created via `openssl | gcloud`); anything that signs cookies outside the server must include it. Prefer server-issued cookies (`POST /api/session`).
- Gemini 2.x model IDs returned 404; use `GEMINI_MODEL=gemini-3.5-flash-lite` with `GOOGLE_CLOUD_LOCATION=global`.
- `.gcloudignore` controls the Cloud Build upload (otherwise `.gitignore` patterns apply).

## Earlier local verification
- `next build` succeeds (and `NEXT_OUTPUT=standalone` is what the Docker image uses; Windows cannot create the symlinks it needs).
- Lighthouse (mobile, production build, local): Home performance 92–93, accessibility 100, CLS 0.
- OIDC verification, GCS adapter and bucket-lifecycle logic are unit tested with fakes.
- **Not verified:** the Docker images were not built (Docker Desktop engine would not start on the dev machine), and nothing has run on Cloud Run, Vertex AI or Firestore in the cloud. First deploy may need small fixes; keep `DRY_RUN=1` output and Cloud Build logs handy.

## Public-demo notes
- Demo mode is on in the cloud (Director + demo identity are public). All data is synthetic or simulated and labelled. For a stricter demo set `DEMO_MODE=false` on both services (hides `/director` and the director API) — but then the Scenario Director script cannot run.
- The API is public (the web app proxies to it). Nothing real is stored; proof photos are demo uploads and expire after 30 days.
