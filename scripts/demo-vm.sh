#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${DIC_VM_PROJECT_DIR:-/home/mainulislam/data-incident-commander}"
ENV_FILE="${DIC_DEMO_ENV_FILE:-${PROJECT_DIR}/.env}"
ACTION="${1:-}"
if [[ -f "${ENV_FILE}" ]]; then
  # Load the private runtime configuration without displaying it. This also
  # permits the verified compose path to live in the ignored VM .env file.
  # shellcheck disable=SC1090
  set -a
  source "${ENV_FILE}"
  set +a
fi
COMPOSE_FILE="${DIC_DATAHUB_COMPOSE_FILE:-${HOME}/.datahub/quickstart/docker-compose.quickstart.yml}"
RUNTIME_DIR="${DIC_DEMO_RUNTIME_DIR:-${PROJECT_DIR}/deploy/runtime/demo}"
PID_FILE="${RUNTIME_DIR}/backend.pid"
LOG_FILE="${RUNTIME_DIR}/backend.log"
GMS_HEALTH_URL="http://127.0.0.1:8080/health"
DATAHUB_FRONTEND_URL="http://127.0.0.1:9002"
BACKEND_HEALTH_URL="http://127.0.0.1:8000/health"
WAIT_SECONDS="${DIC_DEMO_WAIT_SECONDS:-300}"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command '$1' was not found."
}

backend_pid() {
  [[ -f "${PID_FILE}" ]] || return 1
  local pid
  read -r pid <"${PID_FILE}"
  [[ "${pid}" =~ ^[1-9][0-9]*$ ]] || return 1
  printf '%s\n' "${pid}"
}

backend_pid_is_owned() {
  local pid="$1" command_line process_dir
  [[ -r "/proc/${pid}/cmdline" && -e "/proc/${pid}/cwd" ]] || return 1
  command_line="$(tr '\0' ' ' <"/proc/${pid}/cmdline")"
  process_dir="$(readlink -f "/proc/${pid}/cwd")"
  [[ "${command_line}" == *"uvicorn data_incident_commander.api.app:app"* ]]
  [[ "${process_dir}" == "$(readlink -f "${PROJECT_DIR}")" ]]
}

backend_is_running() {
  local pid
  pid="$(backend_pid)" || return 1
  kill -0 "${pid}" 2>/dev/null && backend_pid_is_owned "${pid}"
}

wait_for_url() {
  local name="$1" url="$2" deadline
  deadline=$((SECONDS + WAIT_SECONDS))
  until curl --fail --silent --show-error --max-time 5 "${url}" >/dev/null 2>&1; do
    (( SECONDS < deadline )) || fail "${name} did not become ready at ${url} within ${WAIT_SECONDS}s."
    sleep 2
  done
}

load_backend_environment() {
  [[ -f "${ENV_FILE}" ]] || fail "Missing ${ENV_FILE}. Create it on the VM with the verified MCP environment and chmod 600 it."
  # shellcheck disable=SC1090
  set -a
  source "${ENV_FILE}"
  set +a
  case "${DIC_GMS_URL:-}" in
    http://127.0.0.1:8080 | http://localhost:8080) ;;
    *) fail "DIC_GMS_URL must use VM loopback port 8080 in ${ENV_FILE}." ;;
  esac
  [[ "${DIC_MCP_MODE:-}" == "stdio" ]] || fail "DIC_MCP_MODE must be stdio in ${ENV_FILE}."
  [[ -n "${DIC_MCP_SERVER_VERSION:-}" ]] || fail "DIC_MCP_SERVER_VERSION is missing from ${ENV_FILE}."
  local token_name="${DIC_GMS_TOKEN_ENV:-DATAHUB_GMS_TOKEN}"
  [[ "${token_name}" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || fail "DIC_GMS_TOKEN_ENV is invalid."
  [[ -n "${!token_name:-}" ]] || fail "The token variable named by DIC_GMS_TOKEN_ENV is unset or empty."
}

datahub_status() {
  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    printf 'DataHub: unavailable (compose file missing: %s)\n' "${COMPOSE_FILE}"
    return 1
  fi
  if docker compose -f "${COMPOSE_FILE}" --profile quickstart ps --status running --quiet 2>/dev/null |
      grep -q . &&
    curl --fail --silent --max-time 3 "${GMS_HEALTH_URL}" >/dev/null 2>&1 &&
    curl --fail --silent --max-time 3 "${DATAHUB_FRONTEND_URL}" >/dev/null 2>&1; then
    printf 'DataHub: ready (GMS and frontend healthy on VM loopback)\n'
    return 0
  fi
  printf 'DataHub: not ready\n'
  return 1
}

start() {
  require_command docker
  require_command curl
  [[ -d "${PROJECT_DIR}" ]] || fail "VM project directory not found: ${PROJECT_DIR}"
  [[ -f "${COMPOSE_FILE}" ]] || fail "Verified DataHub compose file not found: ${COMPOSE_FILE}"
  [[ -x "${PROJECT_DIR}/.venv/bin/python" ]] ||
    fail "Backend virtual environment missing. Run 'cd ${PROJECT_DIR} && make setup' once."
  load_backend_environment
  mkdir -p "${RUNTIME_DIR}"
  chmod 700 "${RUNTIME_DIR}"

  printf 'Starting DataHub v1.6.0 quickstart...\n'
  docker compose -f "${COMPOSE_FILE}" --profile quickstart up -d
  printf 'Waiting for private GMS and DataHub frontend health...\n'
  wait_for_url "DataHub GMS" "${GMS_HEALTH_URL}"
  wait_for_url "DataHub frontend" "${DATAHUB_FRONTEND_URL}"

  if backend_is_running; then
    printf 'DIC backend: already running (PID %s)\n' "$(backend_pid)"
  else
    if [[ -f "${PID_FILE}" ]]; then
      printf 'Removing stale backend PID file.\n'
      rm -f "${PID_FILE}"
    fi
    if curl --fail --silent --max-time 2 "${BACKEND_HEALTH_URL}" >/dev/null 2>&1; then
      fail "Port 8000 is already serving without an owned DIC backend PID. Stop that process manually."
    fi
    printf 'Starting DIC backend on VM loopback...\n'
    (
      cd "${PROJECT_DIR}"
      umask 077
      nohup .venv/bin/python -m uvicorn data_incident_commander.api.app:app \
        --app-dir src --host 127.0.0.1 --port 8000 >>"${LOG_FILE}" 2>&1 &
      printf '%s\n' "$!" >"${PID_FILE}"
    )
  fi

  wait_for_url "DIC backend" "${BACKEND_HEALTH_URL}"
  printf 'READY: DataHub and DIC backend are healthy; backend is private at 127.0.0.1:8000.\n'
  printf 'Backend log: %s\n' "${LOG_FILE}"
}

status() {
  local result=0
  require_command docker
  require_command curl
  datahub_status || result=1
  if backend_is_running &&
    curl --fail --silent --max-time 3 "${BACKEND_HEALTH_URL}" >/dev/null 2>&1; then
    printf 'DIC backend: ready (PID %s, VM loopback only)\n' "$(backend_pid)"
  elif backend_is_running; then
    printf 'DIC backend: process running but health check failed (see %s)\n' "${LOG_FILE}"
    result=1
  else
    printf 'DIC backend: stopped\n'
    result=1
  fi
  return "${result}"
}

stop() {
  local pid deadline
  if ! pid="$(backend_pid)"; then
    printf 'DIC backend: already stopped\n'
    return
  fi
  if ! kill -0 "${pid}" 2>/dev/null; then
    rm -f "${PID_FILE}"
    printf 'DIC backend: removed stale PID file; process was not running\n'
    return
  fi
  backend_pid_is_owned "${pid}" ||
    fail "PID ${pid} is not the owned DIC backend; refusing to terminate it. Remove ${PID_FILE} after inspection."
  kill -TERM "${pid}"
  deadline=$((SECONDS + 15))
  while kill -0 "${pid}" 2>/dev/null && (( SECONDS < deadline )); do sleep 1; done
  kill -0 "${pid}" 2>/dev/null &&
    fail "Backend PID ${pid} did not stop after SIGTERM; inspect it manually."
  rm -f "${PID_FILE}"
  printf 'DIC backend: stopped. DataHub and its metadata volumes were left running.\n'
}

case "${ACTION}" in
  start) start ;;
  status) status ;;
  stop) stop ;;
  *) fail "Usage: $0 {start|status|stop}" ;;
esac
