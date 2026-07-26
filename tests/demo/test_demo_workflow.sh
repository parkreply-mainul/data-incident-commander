#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MAC="${ROOT}/scripts/demo-mac.sh"
VM="${ROOT}/scripts/demo-vm.sh"
MAKEFILE="${ROOT}/Makefile"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
assert_has() { grep -Fq -- "$2" "$1" || fail "$1 is missing: $2"; }
assert_lacks() { ! grep -Eiq -- "$2" "$1" || fail "$1 contains forbidden pattern: $2"; }
assert_before() {
  local file="$1" first="$2" second="$3" first_line second_line
  first_line="$(grep -nF -- "${first}" "${file}" | head -n 1 | cut -d: -f1)"
  second_line="$(grep -nF -- "${second}" "${file}" | head -n 1 | cut -d: -f1)"
  [[ -n "${first_line}" && -n "${second_line}" && "${first_line}" -lt "${second_line}" ]] ||
    fail "$file must place '$first' before '$second'"
}

bash -n "${MAC}" "${VM}" "${BASH_SOURCE[0]}"

assert_has "${MAC}" 'VM_INSTANCE="instance-20260724-222331"'
assert_has "${MAC}" 'GCP_PROJECT="dataincidentcommander"'
assert_has "${MAC}" 'GCP_ZONE="europe-west9-a"'
assert_has "${MAC}" '-L 127.0.0.1:8000:127.0.0.1:8000'
assert_has "${MAC}" 'trap cleanup EXIT INT TERM'
assert_has "${MAC}" 'kill "${FRONTEND_PID}"'
assert_has "${MAC}" 'kill "${TUNNEL_PID}"'
assert_has "${MAC}" 'lsof -nP -iTCP:5173 -sTCP:LISTEN'
assert_has "${MAC}" '--port 5173 --strictPort'
assert_has "${MAC}" 'until curl --fail --silent --max-time 2 "${FRONTEND_URL}"'
assert_has "${MAC}" 'kill -0 "${FRONTEND_PID}"'
assert_has "${MAC}" 'printf '\''READY: open %s'
assert_before "${MAC}" 'lsof -nP -iTCP:5173 -sTCP:LISTEN' 'gcloud compute instances describe'
assert_before "${MAC}" 'until curl --fail --silent --max-time 2 "${FRONTEND_URL}"' 'printf '\''READY: open %s'

assert_has "${VM}" 'COMPOSE_FILE="/home/mainulis599/.datahub/quickstart/docker-compose.yml"'
assert_has "${VM}" 'SECRETS_FILE="/home/mainulis599/.datahub/quickstart/.local-secrets.env"'
assert_has "${VM}" 'sudo test -f "${COMPOSE_FILE}"'
assert_has "${VM}" 'sudo test -f "${SECRETS_FILE}"'
assert_has "${VM}" 'sudo env DATAHUB_VERSION=v1.6.0 UI_INGESTION_DEFAULT_CLI_VERSION=v1.6.0'
assert_has "${VM}" 'docker compose --profile quickstart --env-file "${SECRETS_FILE}"'
assert_has "${VM}" '-f "${COMPOSE_FILE}" ps --status running --quiet'
assert_has "${VM}" '-f "${COMPOSE_FILE}" up -d'
assert_has "${VM}" 'http://127.0.0.1:8080/health'
assert_has "${VM}" 'http://127.0.0.1:9002'
assert_has "${VM}" '--host 127.0.0.1 --port 8000'
assert_has "${VM}" 'backend_pid_is_owned'
assert_has "${VM}" 'already running'
assert_has "${VM}" 'Removing stale backend PID file.'
assert_has "${VM}" 'refusing to terminate it'
assert_has "${VM}" 'DataHub and its metadata volumes were left running.'
assert_has "${VM}" 'if [[ -f "${ENV_FILE}" ]]'
assert_lacks "${VM}" 'ACTION.*!=.*stop'
assert_has "${VM}" 'RUNTIME_DIR="${DIC_DEMO_RUNTIME_DIR:-${PROJECT_DIR}/deploy/runtime/demo}"'
assert_before "${VM}" 'source "${ENV_FILE}"' 'RUNTIME_DIR="${DIC_DEMO_RUNTIME_DIR:-${PROJECT_DIR}/deploy/runtime/demo}"'

assert_lacks "${MAC}" 'firewall|0\.0\.0\.0|8080:|9002:'
assert_lacks "${VM}" 'firewall|0\.0\.0\.0|docker[[:space:]]+(compose[[:space:]]+)?down|volume[[:space:]]+(rm|prune)'
assert_lacks "${MAC}" 'DATAHUB_GMS_TOKEN|token'
assert_lacks "${VM}" 'echo.*token|printf.*token|set[[:space:]]+-x'

assert_has "${MAKEFILE}" 'demo-start:'
assert_has "${MAKEFILE}" 'demo-status:'
assert_has "${MAKEFILE}" 'demo-stop:'

printf 'Demo workflow static and shell syntax tests passed.\n'
