<#
.SYNOPSIS
Deploys the vLLM server (Qwen2.5-7B-Instruct) to Cloud Run.
#>

$ErrorActionPreference = "Stop"

$ServiceName = "vllm-server-v3"
$Region = "asia-southeast1"

Write-Host "======================================================"
Write-Host "🚀 SCP World: Deploying vLLM to Cloud Run (Qwen2.5-7B)"
Write-Host "======================================================"

Write-Host "`n[Step 1/2] Removing existing '$ServiceName' service to free up L4 GPU quota..."
try {
    gcloud run services delete $ServiceName --region=$Region --quiet
    Write-Host "Service deleted successfully."
} catch {
    Write-Host "Service not present. Proceeding..."
}

Write-Host "`n[Step 2/2] Waiting 120 seconds for deletion to propagate (avoids GPU quota race)..."
for ($i = 120; $i -gt 0; $i--) {
    Write-Host -NoNewline "`rWaiting... $i seconds remaining "
    Start-Sleep -Seconds 1
}
Write-Host "`nWait complete."

$DeployArgs = @(
    "run", "deploy", $ServiceName,
    "--image=vllm/vllm-openai:latest",
    "--args=--model=Qwen/Qwen2.5-7B-Instruct,--trust-remote-code,--max-model-len=8192,--dtype=bfloat16,--enforce-eager,--gpu-memory-utilization=0.8,--port=8080,--served-model-name=qwen2.5-7b",
    "--cpu=8", "--memory=32Gi",
    "--gpu=1", "--gpu-type=nvidia-l4",
    "--no-gpu-zonal-redundancy",
    "--no-cpu-throttling",
    "--region=$Region",
    "--no-allow-unauthenticated",
    "--timeout=3600"
)

& gcloud @DeployArgs

Write-Host "`n✅ Deployment initiated. Update backend VLLM_LLM_URL if the service URL changed."
