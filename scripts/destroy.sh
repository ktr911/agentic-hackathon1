#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_ID="${PROJECT_ID:-zenn-hack5-i-icc}"
REGION="${REGION:-asia-northeast1}"
WEB_SERVICE="${WEB_SERVICE:-fieldnote-client}"
AGENT_SA_NAME="${AGENT_SA_NAME:-fieldnote-agent-runtime}"
WEB_SA_NAME="${WEB_SA_NAME:-fieldnote-web}"
ARTIFACT_BUCKET="${ARTIFACT_BUCKET:-${PROJECT_ID}-fieldnote-artifacts}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="${ROOT_DIR}/.deploy"
RESOURCE_FILE="${STATE_DIR}/agent-engine-resource.txt"

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

if [[ "${CONFIRM_DESTROY:-}" != "${PROJECT_ID}" ]]; then
  fail "削除するには CONFIRM_DESTROY=${PROJECT_ID} を指定してください。"
fi

command -v gcloud >/dev/null || fail "gcloud CLI が必要です。"
ACTIVE_ACCOUNT="$(gcloud auth list --filter='status:ACTIVE' --format='value(account)' | head -n 1)"
[[ -n "${ACTIVE_ACCOUNT}" ]] || fail "Google Cloud に未ログインです。"

echo "Cloud Run を削除します: ${WEB_SERVICE}"
if gcloud run services describe "${WEB_SERVICE}" \
  --project="${PROJECT_ID}" --region="${REGION}" >/dev/null 2>&1; then
  gcloud run services delete "${WEB_SERVICE}" \
    --project="${PROJECT_ID}" --region="${REGION}" --quiet
fi

if [[ -s "${RESOURCE_FILE}" ]]; then
  AGENT_ENGINE_RESOURCE="$(tr -d '[:space:]' < "${RESOURCE_FILE}")"
  if [[ ! "${AGENT_ENGINE_RESOURCE}" =~ ^projects/[0-9]+/locations/${REGION}/reasoningEngines/[0-9]+$ ]]; then
    fail "不正な Agent Runtime リソース名です: ${AGENT_ENGINE_RESOURCE}"
  fi

  echo "Agent Runtime を削除します: ${AGENT_ENGINE_RESOURCE}"
  DELETE_RESPONSE="$(curl --fail --silent --show-error \
    --request DELETE \
    --header "Authorization: Bearer $(gcloud auth print-access-token)" \
    "https://${REGION}-aiplatform.googleapis.com/v1/${AGENT_ENGINE_RESOURCE}?force=true")"
  OPERATION_NAME="$(python3 -c 'import json, sys; print(json.load(sys.stdin).get("name", ""))' <<<"${DELETE_RESPONSE}")"

  if [[ -n "${OPERATION_NAME}" ]]; then
    echo "Agent Runtime の削除完了を待ちます"
    for _ in {1..120}; do
      OPERATION_RESPONSE="$(curl --fail --silent --show-error \
        --header "Authorization: Bearer $(gcloud auth print-access-token)" \
        "https://${REGION}-aiplatform.googleapis.com/v1/${OPERATION_NAME}")"
      set +e
      python3 -c '
import json
import sys

operation = json.load(sys.stdin)
if operation.get("error"):
    print(operation["error"], file=sys.stderr)
    raise SystemExit(2)
raise SystemExit(0 if operation.get("done") else 1)
' <<<"${OPERATION_RESPONSE}"
      OPERATION_STATUS=$?
      set -e
      if [[ ${OPERATION_STATUS} -eq 0 ]]; then
        break
      elif [[ ${OPERATION_STATUS} -eq 2 ]]; then
        fail "Agent Runtime の削除に失敗しました。"
      fi
      sleep 5
    done
    [[ ${OPERATION_STATUS} -eq 0 ]] || fail "Agent Runtime の削除が10分以内に完了しませんでした。"
  fi
fi

echo "生成画像バケットを削除します: gs://${ARTIFACT_BUCKET}"
if gcloud storage buckets describe "gs://${ARTIFACT_BUCKET}" \
  --project="${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud storage rm --recursive "gs://${ARTIFACT_BUCKET}/**" >/dev/null 2>&1 || true
  gcloud storage buckets delete "gs://${ARTIFACT_BUCKET}" --quiet
fi

for service_account_name in "${AGENT_SA_NAME}" "${WEB_SA_NAME}"; do
  service_account="${service_account_name}@${PROJECT_ID}.iam.gserviceaccount.com"
  if gcloud iam service-accounts describe "${service_account}" \
    --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "サービスアカウントを削除します: ${service_account}"
    gcloud iam service-accounts delete "${service_account}" \
      --project="${PROJECT_ID}" --quiet
  fi
done

rm -f \
  "${STATE_DIR}/agent-engine-resource.txt" \
  "${STATE_DIR}/agent-engine-config.json" \
  "${STATE_DIR}/agent-engine-deploy.log" \
  "${STATE_DIR}/smoke-test.sse"

echo "Fieldnote の専用リソースを削除しました。共有 API と Artifact Registry は残しています。"
