<#
.SYNOPSIS
Deploys the SCP World FastAPI backend to Cloud Run.
Builds from backend/ source (uses backend/Dockerfile via buildpacks).
#>

$ErrorActionPreference = "Stop"

$ProjectId   = "scpworld"
$ServiceName = "scp-backend"
$Region      = "asia-southeast1"
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$SourceDir   = Join-Path $ScriptDir "..\backend"

# Public OAuth client ID — safe to embed (verified against this aud at token check).
$GoogleClientId = "1087559947666-uuelrdfelo0c76nm837e4v9epv5er3sa.apps.googleusercontent.com"

$EnvVars = @(
    "FIRESTORE_PROJECT_ID=scpworld",
    "FIRESTORE_DATABASE_ID=(default)",
    "FIRESTORE_COLLECTION=scp_documents",
    "FIRESTORE_SESSION_COLLECTION=sessions",
    "VLLM_LLM_URL=https://vllm-server-v3-hduoqgwvoq-as.a.run.app/v1",
    "VLLM_LLM_MODEL=qwen2.5-7b",
    "EMBED_MODEL_NAME=BAAI/bge-m3",
    "MAX_CONVERSATION_TURNS=10",
    "GOOGLE_CLIENT_ID=$GoogleClientId"
) -join ","

Write-Host "======================================================"
Write-Host "🚀 SCP World: Deploying backend to Cloud Run"
Write-Host "    project: $ProjectId"
Write-Host "    service: $ServiceName"
Write-Host "    region : $Region"
Write-Host "    source : $SourceDir"
Write-Host "======================================================"

$DeployArgs = @(
    "run", "deploy", $ServiceName,
    "--project=$ProjectId",
    "--source=$SourceDir",
    "--region=$Region",
    "--platform=managed",
    "--allow-unauthenticated",
    "--port=8080",
    "--cpu=2",
    "--memory=4Gi",
    "--min-instances=0",
    "--max-instances=3",
    "--timeout=600",
    "--concurrency=20",
    "--set-env-vars=$EnvVars"
)

& gcloud @DeployArgs

$Url = & gcloud run services describe $ServiceName --region=$Region --project=$ProjectId --format='value(status.url)'
Write-Host "`n✅ Deployment complete."
Write-Host "    URL: $Url"
Write-Host "`nSmoke test:"
Write-Host "    curl -s $Url/health"
