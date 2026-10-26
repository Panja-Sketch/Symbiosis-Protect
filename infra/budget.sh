#!/usr/bin/env bash
# Budget alerts at $25 / $50 / $100 / $150 of the $200 credit.
#   BILLING_ACCOUNT=XXXXXX-XXXXXX-XXXXXX DRY_RUN=1 PROJECT_ID=... NWS_USER_AGENT=x bash infra/budget.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source infra/common.sh
require_owner_approval
: "${BILLING_ACCOUNT:?Set BILLING_ACCOUNT (gcloud billing accounts list)}"
run gcloud services enable billingbudgets.googleapis.com --project "$PROJECT_ID"
run gcloud billing budgets create --billing-account "$BILLING_ACCOUNT" --display-name "symbiosis-demo-200usd" \
  --budget-amount 200USD --filter-projects "projects/${PROJECT_ID}" \
  --threshold-rule percent=0.125 --threshold-rule percent=0.25 --threshold-rule percent=0.5 --threshold-rule percent=0.75
echo "Alerts at \$25, \$50, \$100, \$150 (12.5%, 25%, 50%, 75% of \$200). Email goes to billing account admins."
