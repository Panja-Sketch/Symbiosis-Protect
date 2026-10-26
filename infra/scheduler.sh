#!/usr/bin/env bash
# Pause or resume the 15-minute evaluation job (pause it whenever you are not demoing).
#   bash infra/scheduler.sh pause|resume
set -euo pipefail
cd "$(dirname "$0")/.."
source infra/common.sh
require_owner_approval
case "${1:-}" in
  pause)  run gcloud scheduler jobs pause "$SCHED_JOB" --location "$REGION" --project "$PROJECT_ID" ;;
  resume) run gcloud scheduler jobs resume "$SCHED_JOB" --location "$REGION" --project "$PROJECT_ID" ;;
  *) echo "usage: scheduler.sh pause|resume" >&2; exit 1 ;;
esac
