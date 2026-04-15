#!/bin/bash
# Deploy vLLM server (Qwen2.5-7B-Instruct) to Cloud Run.

set -e

SERVICE_NAME="vllm-server-v3"
REGION="asia-southeast1"

echo "======================================================"
echo "🚀 SCP World: Deploying vLLM to Cloud Run (Qwen2.5-7B)"
echo "======================================================"

echo ""
echo "[Step 1/2] Removing existing '${SERVICE_NAME}' service to free up L4 GPU quota..."
gcloud run services delete "${SERVICE_NAME}" --region="${REGION}" --quiet || echo "Service not present. Proceeding..."

echo ""
echo "[Step 2/2] Waiting 120s for deletion to propagate (avoids GPU quota race)..."
for i in {120..1}; do
    echo -ne "\rWaiting... $i seconds remaining "
    sleep 1
done
echo -e "\nWait complete."

gcloud run deploy "${SERVICE_NAME}" \
  --image=vllm/vllm-openai:latest \
  --args="--model=Qwen/Qwen2.5-7B-Instruct,--trust-remote-code,--max-model-len=8192,--dtype=bfloat16,--enforce-eager,--gpu-memory-utilization=0.8,--port=8080,--served-model-name=qwen2.5-7b" \
  --cpu=8 --memory=32Gi \
  --gpu=1 --gpu-type=nvidia-l4 \
  --no-gpu-zonal-redundancy \
  --no-cpu-throttling \
  --region="${REGION}" \
  --no-allow-unauthenticated \
  --timeout=3600

echo ""
echo "✅ Deployment initiated. Update backend VLLM_LLM_URL if the service URL changed."
