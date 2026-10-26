#!/usr/bin/env bash
# Tear everything down. This deletes data (Firestore documents are NOT deleted by this script; delete the database
# in the console if you want them gone). Requires CONFIRM_DESTROY=yes in addition to owner approval.
set -euo pipefail
cd "$(dirname "$0")/.."
source infra/common.sh
require_owner_approval
if [[ "$DRY_RUN" != "1" && "${CONFIRM_DESTROY:-}" != "yes" ]]; then echo "Set CONFIRM_DESTROY=yes to proceed." >&2; exit 2; fi
run gcloud scheduler jobs delete "$SCHED_JOB" --location "$REGION" --project "$PROJECT_ID" --quiet || true
run gcloud run services delete "$WEB_SERVICE" --region "$REGION" --project "$PROJECT_ID" --quiet || true
run gcloud run services delete "$API_SERVICE" --region "$REGION" --project "$PROJECT_ID" --quiet || true
run gcloud artifacts repositories delete "$REPO" --location "$REGION" --project "$PROJECT_ID" --quiet || true
run gcloud storage rm -r "gs://${BUCKET}" --project "$PROJECT_ID" || true
run gcloud secrets delete symbiosis-session-secret --project "$PROJECT_ID" --quiet || true
for name in symbiosis-api symbiosis-web symbiosis-sched; do
  run gcloud iam service-accounts delete "${name}@${PROJECT_ID}.iam.gserviceaccount.com" --project "$PROJECT_ID" --quiet || true
done
echo "Done. To stop all billing for good, delete the project: gcloud projects delete ${PROJECT_ID}"
