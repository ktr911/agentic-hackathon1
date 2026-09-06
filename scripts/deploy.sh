#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID="${PROJECT_ID:-agentic-ai-hackathon-test1}"
REGION="${REGION:-asia-northeast1}"
WEB_SERVICE="${WEB_SERVICE:-fieldnote-client}"
AGENT_DISPLAY_NAME="${AGENT_DISPLAY_NAME:-fieldnote-agent}"
AGENT_SA_NAME="${AGENT_SA_NAME:-fieldnote-agent-runtime}"
WEB_SA_NAME="${WEB_SA_NAME:-fieldnote-web}"
ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-${PROJECT_ID}-fieldnote-artifacts}"
ADK_VERSION="${ADK_VERSION:-2.8.0}"
SMOKE_TEST="${SMOKE_TEST:-true}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${ROOT_DIR}/.deploy"
RESOURCE_FILE="${STATE_DIR}/agent-engine-resource.txt"
CONFIG_FILE="${STATE_DIR}/agent-engine-config.json"
LOG_FILE="${STATE_DIR}/agent-engine-deploy.log"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

command -v gcloud >/dev/null || fail "gcloud CLI が必要です。"
command -v uvx >/dev/null || fail "uv/uvx が必要です。"

ACTIVE_ACCOUNT="$(gcloud auth list --filter='status:ACTIVE' --format='value(account)' | head -n 1)"
if [[ -z "${ACTIVE_ACCOUNT}" ]]; then
  fail "Google Cloud に未ログインです。先に 'gcloud auth login' と 'gcloud auth application-default login' を実行してください。"
fi
gcloud auth application-default print-access-token >/dev/null 2>&1 || \
  fail "Application Default Credentials がありません。'gcloud auth application-default login' を実行してください。"

gcloud projects describe "${PROJECT_ID}" --format='value(projectId)' >/dev/null
mkdir -p "${STATE_DIR}"

echo "[1/8] API を有効化します (${PROJECT_ID})"
gcloud services enable \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"

AGENT_SA="${AGENT_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
WEB_SA="${WEB_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

ensure_service_account() {
  local name="$1"
  local display_name="$2"
  local email="${name}@${PROJECT_ID}.iam.gserviceaccount.com"
  if ! gcloud iam service-accounts describe "${email}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${name}" \
      --display-name="${display_name}" \
      --project="${PROJECT_ID}"
  fi
}

grant_project_role() {
  local member="$1"
  local role="$2"
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="${member}" \
    --role="${role}" \
    --condition=None \
    --quiet >/dev/null
}

echo "[2/8] 実行用サービスアカウントと IAM を設定します"
ensure_service_account "${AGENT_SA_NAME}" "Fieldnote Agent Runtime"
ensure_service_account "${WEB_SA_NAME}" "Fieldnote Cloud Run web"
grant_project_role "serviceAccount:${AGENT_SA}" "roles/aiplatform.user"
grant_project_role "serviceAccount:${AGENT_SA}" "roles/logging.logWriter"
grant_project_role "serviceAccount:${AGENT_SA}" "roles/serviceusage.serviceUsageConsumer"
grant_project_role "serviceAccount:${WEB_SA}" "roles/aiplatform.user"
grant_project_role "serviceAccount:${WEB_SA}" "roles/logging.logWriter"

if [[ "${ACTIVE_ACCOUNT}" == *.gserviceaccount.com ]]; then
  DEPLOYER_MEMBER="serviceAccount:${ACTIVE_ACCOUNT}"
else
  DEPLOYER_MEMBER="user:${ACTIVE_ACCOUNT}"
fi
for service_account in "${AGENT_SA}" "${WEB_SA}"; do
  gcloud iam service-accounts add-iam-policy-binding "${service_account}" \
    --member="${DEPLOYER_MEMBER}" \
    --role="roles/iam.serviceAccountUser" \
    --project="${PROJECT_ID}" \
    --quiet >/dev/null
done

echo "[3/8] 生成画像用 GCS バケットを設定します"
if ! gcloud storage buckets describe "gs://${ARTIFACT_BUCKET}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${ARTIFACT_BUCKET}" \
    --project="${PROJECT_ID}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
fi
gcloud storage buckets add-iam-policy-binding "gs://${ARTIFACT_BUCKET}" \
  --member="serviceAccount:${AGENT_SA}" \
  --role="roles/storage.objectAdmin" >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${ARTIFACT_BUCKET}" \
  --member="serviceAccount:${WEB_SA}" \
  --role="roles/storage.objectViewer" >/dev/null

python3 - "${CONFIG_FILE}" "${AGENT_SA}" <<'PY'
import json
import sys

path, service_account = sys.argv[1:]
with open(path, "w", encoding="utf-8") as file:
    json.dump(
        {
            "service_account": service_account,
            "min_instances": 0,
            "max_instances": 3,
            "resource_limits": {"cpu": "2", "memory": "4Gi"},
            "container_concurrency": 5,
            "env_vars": {"GOOGLE_CLOUD_MODEL_LOCATION": "global"},
        },
        file,
        indent=2,
    )
PY

echo "[4/8] ADK エージェントを Agent Runtime にデプロイします"
AGENT_ENGINE_ARGS=()
if [[ -s "${RESOURCE_FILE}" ]]; then
  EXISTING_RESOURCE="$(tr -d '[:space:]' < "${RESOURCE_FILE}")"
  if [[ "${EXISTING_RESOURCE}" =~ /reasoningEngines/([0-9]+)$ ]]; then
    AGENT_ENGINE_ARGS+=(--agent_engine_id="${BASH_REMATCH[1]}")
    echo "既存リソースを更新します: ${EXISTING_RESOURCE}"
  fi
fi

DEPLOY_COMMAND=(
  uvx
  --from "google-adk==${ADK_VERSION}"
  --with "google-cloud-aiplatform[adk,agent_engines]==2.1.0"
  adk deploy agent_engine
  --project="${PROJECT_ID}"
  --region="${REGION}"
  --display_name="${AGENT_DISPLAY_NAME}"
  --description="地質情報と観光情報を統合する Fieldnote ADK agent"
  --agent_engine_config_file="${CONFIG_FILE}"
  --artifact_service_uri="gs://${ARTIFACT_BUCKET}"
  --adk_version="${ADK_VERSION}"
)
if [[ ${#AGENT_ENGINE_ARGS[@]} -gt 0 ]]; then
  DEPLOY_COMMAND+=("${AGENT_ENGINE_ARGS[@]}")
fi
DEPLOY_COMMAND+=("${ROOT_DIR}/src/agent")

set +e
"${DEPLOY_COMMAND[@]}" 2>&1 | tee "${LOG_FILE}"
DEPLOY_STATUS=${PIPESTATUS[0]}
set -e
[[ ${DEPLOY_STATUS} -eq 0 ]] || fail "Agent Runtime のデプロイに失敗しました。ログ: ${LOG_FILE}"

AGENT_ENGINE_RESOURCE="$(grep -Eo "projects/[A-Za-z0-9-]+/locations/${REGION}/reasoningEngines/[0-9]+" "${LOG_FILE}" | tail -n 1 || true)"
if [[ -z "${AGENT_ENGINE_RESOURCE}" && -n "${EXISTING_RESOURCE:-}" ]]; then
  AGENT_ENGINE_RESOURCE="${EXISTING_RESOURCE}"
fi
[[ -n "${AGENT_ENGINE_RESOURCE}" ]] || fail "デプロイ結果から Agent Runtime のリソース名を取得できませんでした。"
printf '%s\n' "${AGENT_ENGINE_RESOURCE}" > "${RESOURCE_FILE}"

echo "[5/8] Cloud Run に Web クライアント/BFF をデプロイします"
gcloud run deploy "${WEB_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --source="${ROOT_DIR}/src/web" \
  --service-account="${WEB_SA}" \
  --allow-unauthenticated \
  --timeout=900 \
  --max-instances=3 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},AGENT_ENGINE_RESOURCE=${AGENT_ENGINE_RESOURCE},ARTIFACT_BUCKET=${ARTIFACT_BUCKET}" \
  --quiet

echo "[6/8] Cloud Run URL を取得します"
WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT_ID}" \
  --region="${REGION}" \
  --format='value(status.url)')"

echo "[7/8] HTTP 疎通確認を行います"
curl --fail --silent --show-error "${WEB_URL}/api/healthz"
echo

echo "[8/8] エージェントの E2E 疎通確認を行います"
if [[ "${SMOKE_TEST}" == "true" ]]; then
  SMOKE_USER="deploy-smoke-$(date +%s)"
  SESSION_RESPONSE="$(curl --fail --silent --show-error \
    --request POST \
    --header 'Content-Type: application/json' \
    --data '{}' \
    "${WEB_URL}/apps/agent/users/${SMOKE_USER}/sessions")"
  SESSION_ID="$(python3 -c 'import json, sys; print(json.load(sys.stdin)["id"])' <<<"${SESSION_RESPONSE}")"
  SMOKE_PAYLOAD="$(python3 - "${SMOKE_USER}" "${SESSION_ID}" <<'PY'
import json
import sys

user_id, session_id = sys.argv[1:]
print(json.dumps({
    "appName": "agent",
    "userId": user_id,
    "sessionId": session_id,
    "newMessage": {
        "role": "user",
        "parts": [{"text": "箱根の地質と観光を短く調査して"}],
    },
    "streaming": False,
}))
PY
)"
  curl --fail --silent --show-error --no-buffer \
    --request POST \
    --header 'Content-Type: application/json' \
    --data "${SMOKE_PAYLOAD}" \
    "${WEB_URL}/run_sse" | tee "${STATE_DIR}/smoke-test.sse" >/dev/null
  grep -q 'root_agent' "${STATE_DIR}/smoke-test.sse" || \
    fail "E2E 応答に root_agent のイベントがありません。ログ: ${STATE_DIR}/smoke-test.sse"
  echo "E2E smoke test: OK"
else
  echo "SMOKE_TEST=${SMOKE_TEST} のためスキップしました"
fi

echo "Deployment complete"
echo "Web: ${WEB_URL}"
echo "Agent Runtime: ${AGENT_ENGINE_RESOURCE}"
echo "Artifacts: gs://${ARTIFACT_BUCKET}"
