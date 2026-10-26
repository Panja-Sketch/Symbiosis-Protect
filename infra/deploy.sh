#!/usr/bin/env bash
# Deploy web + api to Cloud Run (scale to zero), Firestore native, one GCS bucket, one Cloud Scheduler job.
#   DRY_RUN=1 PROJECT_ID=... NWS_USER_AGENT=... bash infra/deploy.sh      # prints every command, runs nothing
#   OWNER_SAID_DEPLOY=yes PROJECT_ID=... NWS_USER_AGENT=... bash infra/deploy.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source infra/common.sh
require_owner_approval

echo "== 1. APIs"
run gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com \
  storage.googleapis.com aiplatform.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com iam.googleapis.com \
  --project "$PROJECT_ID"

echo "== 2. Artifact Registry"
run gcloud artifacts repositories create "$REPO" --repository-format=docker --location="$REGION" --project "$PROJECT_ID" || true

echo "== 3. Firestore (native mode) + TTL for the cache collection"
run gcloud firestore databases create --location="$REGION" --type=firestore-native --project "$PROJECT_ID" || true
run gcloud firestore fields ttls update expires_at --collection-group=cache --enable-ttl --project "$PROJECT_ID" || true

echo "== 4. Proof bucket (objects deleted after 30 days)"
run gcloud storage buckets create "gs://${BUCKET}" --location="$REGION" --uniform-bucket-level-access --project "$PROJECT_ID" || true
run gcloud storage buckets update "gs://${BUCKET}" --lifecycle-file=infra/bucket-lifecycle.json

echo "== 5. Service accounts (least privilege)"
for name in symbiosis-api symbiosis-web symbiosis-sched; do
  run gcloud iam service-accounts create "$name" --project "$PROJECT_ID" || true
done
run gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:${API_SA}" --role roles/datastore.user --condition=None
run gcloud projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:${API_SA}" --role roles/aiplatform.user --condition=None
run gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" --member "serviceAccount:${API_SA}" --role roles/storage.objectAdmin
# The web service reads no GCP resources; it gets no project roles. The scheduler SA only mints an OIDC token (no roles).

echo "== 6. Session secret (Secret Manager)"
if [[ "$DRY_RUN" == "1" ]]; then
  echo "+ openssl rand -base64 32 | gcloud secrets create symbiosis-session-secret --data-file=- (skipped if it exists)"
else
  gcloud secrets describe symbiosis-session-secret --project "$PROJECT_ID" >/dev/null 2>&1 \
    || openssl rand -base64 32 | gcloud secrets create symbiosis-session-secret --data-file=- --project "$PROJECT_ID"
fi
for sa in "$API_SA" "$WEB_SA"; do
  run gcloud secrets add-iam-policy-binding symbiosis-session-secret --member "serviceAccount:${sa}" --role roles/secretmanager.secretAccessor --project "$PROJECT_ID"
done

echo "== 7. Build images with Cloud Build"
run gcloud builds submit --config infra/cloudbuild-api.yaml --substitutions "_IMAGE=${IMAGE_BASE}/api:latest" --project "$PROJECT_ID" .
run gcloud builds submit --config infra/cloudbuild-web.yaml --substitutions "_IMAGE=${IMAGE_BASE}/web:latest" --project "$PROJECT_ID" .

echo "== 8. Deploy API (min 0 / max 1 instance: Sense device state is serialized in-process, see docs/DECISIONS.md)"
run gcloud run deploy "$API_SERVICE" --image "${IMAGE_BASE}/api:latest" --region "$REGION" --project "$PROJECT_ID" \
  --service-account "$API_SA" --allow-unauthenticated --min-instances 0 --max-instances 1 --memory 1Gi --cpu 1 --timeout 60 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},STORAGE_BACKEND=gcs,GCS_BUCKET=${BUCKET},DEMO_MODE=true,SCHEDULER_ENABLED=false,AI_ENABLED=true,GEMINI_MODEL=${GEMINI_MODEL},AUTH_MODE=demo,INTERNAL_AUTH=oidc,SCHEDULER_SERVICE_ACCOUNT=${SCHED_SA},NWS_USER_AGENT=${NWS_USER_AGENT}" \
  --set-secrets "SESSION_SECRET=symbiosis-session-secret:latest"
API_URL="$(capture gcloud run services describe "$API_SERVICE" --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')"
# The Scheduler's ID token is minted for this audience; the API verifies it.
run gcloud run services update "$API_SERVICE" --region "$REGION" --project "$PROJECT_ID" --update-env-vars "SCHEDULER_AUDIENCE=${API_URL}"

echo "== 9. Deploy web"
run gcloud run deploy "$WEB_SERVICE" --image "${IMAGE_BASE}/web:latest" --region "$REGION" --project "$PROJECT_ID" \
  --service-account "$WEB_SA" --allow-unauthenticated --min-instances 0 --max-instances 2 --memory 512Mi --cpu 1 \
  --set-env-vars "API_BASE_URL=${API_URL},DEMO_MODE=true,CARRIER_NAME=Symbiosis Protect" \
  --set-secrets "SESSION_SECRET=symbiosis-session-secret:latest"

echo "== 10. Cloud Scheduler: evaluate every 15 minutes (OIDC)"
run gcloud scheduler jobs create http "$SCHED_JOB" --location "$REGION" --project "$PROJECT_ID" --schedule "*/15 * * * *" \
  --uri "${API_URL}/api/v1/internal/evaluate" --http-method POST \
  --oidc-service-account-email "$SCHED_SA" --oidc-token-audience "$API_URL" --attempt-deadline 60s \
  || run gcloud scheduler jobs update http "$SCHED_JOB" --location "$REGION" --project "$PROJECT_ID" --schedule "*/15 * * * *" \
       --uri "${API_URL}/api/v1/internal/evaluate" --oidc-service-account-email "$SCHED_SA" --oidc-token-audience "$API_URL"

echo "== 11. Smoke test"
WEB_URL="$(capture gcloud run services describe "$WEB_SERVICE" --region "$REGION" --project "$PROJECT_ID" --format 'value(status.url)')"
if [[ "$DRY_RUN" != "1" ]]; then
  curl -fsS "${API_URL}/healthz" && echo
  curl -fsS "${WEB_URL}/api/healthz" && echo
fi
echo "Web: ${WEB_URL}"
echo "API: ${API_URL}  (docs: ${API_URL}/docs)"
echo "Remember: run infra/budget.sh once, and 'python scripts/tasks.py scheduler-pause' when you are not demoing."
