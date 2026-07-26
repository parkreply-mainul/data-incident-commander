#!/usr/bin/env bash
set -euo pipefail

VM_INSTANCE="instance-20260724-222331"
GCP_PROJECT="dataincidentcommander"
GCP_ZONE="europe-west9-a"
VM_PROJECT_DIR="/opt/data-incident-commander"
FRONTEND_URL="http://127.0.0.1:5173"
TUNNEL_PID=""
FRONTEND_PID=""

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

cleanup() {
  trap - EXIT INT TERM
  [[ -z "${FRONTEND_PID}" ]] || kill "${FRONTEND_PID}" 2>/dev/null || true
  [[ -z "${TUNNEL_PID}" ]] || kill "${TUNNEL_PID}" 2>/dev/null || true
  [[ -z "${FRONTEND_PID}" ]] || wait "${FRONTEND_PID}" 2>/dev/null || true
  [[ -z "${TUNNEL_PID}" ]] || wait "${TUNNEL_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

command -v gcloud >/dev/null 2>&1 || fail "gcloud CLI is required and must be authenticated."
command -v npm >/dev/null 2>&1 || fail "npm is required."
command -v curl >/dev/null 2>&1 || fail "curl is required."
command -v lsof >/dev/null 2>&1 || fail "lsof is required to verify local demo ports."
[[ -f frontend/package.json ]] || fail "Run this command from the Data Incident Commander repository root."
if lsof -nP -iTCP:5173 -sTCP:LISTEN >/dev/null 2>&1; then
  fail "Local port 5173 is already in use. Stop that process, then rerun make demo-start."
fi

state="$(gcloud compute instances describe "${VM_INSTANCE}" \
  --project "${GCP_PROJECT}" --zone "${GCP_ZONE}" --format='value(status)')" ||
  fail "Could not inspect the VM. Check gcloud authentication and project access."
if [[ "${state}" != "RUNNING" ]]; then
  printf 'Starting VM %s...\n' "${VM_INSTANCE}"
  gcloud compute instances start "${VM_INSTANCE}" --project "${GCP_PROJECT}" --zone "${GCP_ZONE}"
fi

printf 'Starting/checking DataHub and the DIC backend on the VM...\n'
gcloud compute ssh "${VM_INSTANCE}" --project "${GCP_PROJECT}" --zone "${GCP_ZONE}" \
  --command "cd ${VM_PROJECT_DIR} && ./scripts/demo-vm.sh start"

if curl --silent --max-time 1 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  fail "Local port 8000 is already in use. Stop that process, then rerun make demo-start."
fi

printf 'Opening private SSH tunnel for the backend...\n'
gcloud compute ssh "${VM_INSTANCE}" --project "${GCP_PROJECT}" --zone "${GCP_ZONE}" \
  -- -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:8000:127.0.0.1:8000 &
TUNNEL_PID=$!

deadline=$((SECONDS + 30))
until curl --fail --silent --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; do
  kill -0 "${TUNNEL_PID}" 2>/dev/null || fail "SSH tunnel exited before the backend became reachable."
  (( SECONDS < deadline )) || fail "SSH tunnel opened, but the backend was not reachable within 30s."
  sleep 1
done

printf 'Starting local frontend on 127.0.0.1:5173...\n'
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5173 --strictPort &
FRONTEND_PID=$!

deadline=$((SECONDS + 30))
until curl --fail --silent --max-time 2 "${FRONTEND_URL}" >/dev/null 2>&1; do
  kill -0 "${FRONTEND_PID}" 2>/dev/null ||
    fail "Frontend exited before it became reachable on port 5173. Check the Vite output above."
  (( SECONDS < deadline )) || fail "Frontend did not become reachable on port 5173 within 30s."
  sleep 1
done

printf 'READY: open %s (Ctrl+C cleans up the frontend and tunnel).\n' "${FRONTEND_URL}"
wait "${FRONTEND_PID}"
