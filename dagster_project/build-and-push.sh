#!/bin/bash
set -e

# prd環境用Dockerイメージビルド・プッシュスクリプト
PROJECT_ID="olist-data-portal"
PREFIX="odp-"
REGION="asia-northeast1"

gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

docker buildx build \
  --platform linux/amd64 \
  --no-cache \
  --push \
  -f dagster_project/dagster_project/Dockerfile_dagster \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/odp-dagster/dagster:latest \
  .

docker buildx build \
  --platform linux/amd64 \
  --no-cache \
  --push \
  -f dagster_project/dagster_project/Dockerfile_user_code \
  -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/odp-dagster/dagster-user-code:latest \
  .

