#!/bin/bash
# ==============================================
# SCP World — Artifact Registry Setup
# ==============================================
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-scp-world-portfolio}"
REGION="us-central1"
REPO_NAME="scp-world"

echo "📦 Creating Artifact Registry: $REPO_NAME"

gcloud artifacts repositories create "$REPO_NAME" \
  --project="$PROJECT_ID" \
  --repository-format=docker \
  --location="$REGION" \
  --description="SCP World Docker images"

echo "✅ Artifact Registry created!"
echo "📋 Configure Docker: gcloud auth configure-docker ${REGION}-docker.pkg.dev"
