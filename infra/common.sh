#!/usr/bin/env bash
# Shared settings + guards for the infra scripts. Source this file; do not run it.
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID to the GCP project (e.g. export PROJECT_ID=symbiosis-protect-demo)}"
REGION="${REGION:-us-central1}"
REPO="${REPO:-symbiosis}"
BUCKET="${BUCKET:-${PROJECT_ID}-proofs}"
API_SERVICE="${API_SERVICE:-symbiosis-api}"
WEB_SERVICE="${WEB_SERVICE:-symbiosis-web}"
API_SA="symbiosis-api@${PROJECT_ID}.iam.gserviceaccount.com"
WEB_SA="symbiosis-web@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="symbiosis-sched@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_JOB="${SCHED_JOB:-symbiosis-evaluate}"
IMAGE_BASE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
GEMINI_MODEL="${GEMINI_MODEL:-gemini-3.5-flash-lite}"
# gemini-2.x models were not available to this project; the 3.5 flash-lite model is served from the global endpoint.
AI_LOCATION="${AI_LOCATION:-global}"
NWS_USER_AGENT="${NWS_USER_AGENT:?Set NWS_USER_AGENT, e.g. 'SymbiosisProtectDemo/0.1 (you@example.com)'}"
DRY_RUN="${DRY_RUN:-0}"

# CLAUDE.md: no gcloud deploy until Phase 9 AND the owner says "deploy". The owner confirms by exporting this variable.
require_owner_approval() {
  if [[ "$DRY_RUN" == "1" ]]; then return 0; fi
  if [[ "${OWNER_SAID_DEPLOY:-}" != "yes" ]]; then
    echo "Refusing to run: the owner has not approved deployment. Review with DRY_RUN=1, then export OWNER_SAID_DEPLOY=yes." >&2
    exit 2
  fi
}

# run <cmd...>: print the command; execute unless DRY_RUN=1.
run() {
  echo "+ $*"
  if [[ "$DRY_RUN" != "1" ]]; then "$@"; fi
}

# capture <cmd...>: like command substitution but prints a placeholder in dry runs.
capture() {
  if [[ "$DRY_RUN" == "1" ]]; then echo "<$1-output>"; else "$@"; fi
}
