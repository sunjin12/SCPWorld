#!/bin/bash
# Deploy SCP World FastAPI backend to Cloud Run.
# Builds from backend/ source (uses backend/Dockerfile via buildpacks).

set -e

PROJECT_ID="scpworld"
SERVICE_NAME="scp-backend"
REGION="asia-southeast1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/../backend"

# Public OAuth client ID — safe to embed (verified against this aud at token check).
GOOGLE_CLIENT_ID="1087559947666-uuelrdfelo0c76nm837e4v9epv5er3sa.apps.googleusercontent.com"

ENV_VARS="FIRESTORE_PROJECT_ID=scpworld"
ENV_VARS="${ENV_VARS},FIRESTORE_DATABASE_ID=(default)"
ENV_VARS="${ENV_VARS},FIRESTORE_COLLECTION=scp_documents"
ENV_VARS="${ENV_VARS},FIRESTORE_SESSION_COLLECTION=sessions"
ENV_VARS="${ENV_VARS},VLLM_LLM_URL=https://vllm-server-v3-hduoqgwvoq-as.a.run.app/v1"
ENV_VARS="${ENV_VARS},VLLM_LLM_MODEL=qwen2.5-7b"
ENV_VARS="${ENV_VARS},EMBED_MODEL_NAME=BAAI/bge-m3"
ENV_VARS="${ENV_VARS},MAX_CONVERSATION_TURNS=10"
ENV_VARS="${ENV_VARS},GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}"

echo "======================================================"
echo "🚀 SCP World: Deploying backend to Cloud Run"
echo "    project: ${PROJECT_ID}"
echo "    service: ${SERVICE_NAME}"
echo "    region : ${REGION}"
echo "    source : ${SOURCE_DIR}"
echo "======================================================"

gcloud run deploy "${SERVICE_NAME}" \
  --project="${PROJECT_ID}" \
  --source="${SOURCE_DIR}" \
  --region="${REGION}" \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --cpu=2 \
  --memory=4Gi \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=600 \
  --concurrency=20 \
  --set-env-vars="${ENV_VARS}"

URL="$(gcloud run services describe "${SERVICE_NAME}" --region="${REGION}" --project="${PROJECT_ID}" --format='value(status.url)')"
echo ""
echo "✅ Deployment complete."
echo "    URL: ${URL}"
echo ""
echo "Smoke test:"
echo "    curl -s ${URL}/health"
