#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# deploy_frontend.sh – Build the Vite/React frontend and sync to S3.
#
# Required env vars:
#   S3_BUCKET  – name of the target S3 bucket
#               (default: sat-prop-budget-frontend-557150842610)
#
# Optional env vars:
#   CLOUDFRONT_DIST_ID – if set, creates a /* invalidation after the sync
###############################################################################

FRONTEND_DIR="$(cd "$(dirname "$0")/../frontend" && pwd)"

echo "==> Installing dependencies …"
if [ -f "$FRONTEND_DIR/package-lock.json" ]; then
  npm ci --prefix "$FRONTEND_DIR"
else
  npm install --prefix "$FRONTEND_DIR"
fi

echo "==> Building frontend …"
npm run build --prefix "$FRONTEND_DIR"

S3_BUCKET="${S3_BUCKET:-sat-prop-budget-frontend-557150842610}"

echo "==> Syncing to s3://${S3_BUCKET} …"
aws s3 sync "$FRONTEND_DIR/dist" "s3://${S3_BUCKET}" --delete

if [ -n "${CLOUDFRONT_DIST_ID:-}" ]; then
  echo "==> Creating CloudFront invalidation for distribution ${CLOUDFRONT_DIST_ID} …"
  aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_DIST_ID" \
    --paths "/*"
  echo "==> Invalidation created."
else
  echo "==> CLOUDFRONT_DIST_ID not set – skipping invalidation."
fi

echo "==> Done."
