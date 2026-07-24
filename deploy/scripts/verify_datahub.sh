#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

readonly DIC_HEALTH_PENDING=10
readonly DIC_HEALTH_FAILED=20

usage() { echo "Usage: $0 [--help] [--env FILE]"; usage_common; }

expected_services() {
  local raw="${DIC_EXPECTED_SERVICES:-}"
  local service
  local seen="|"
  [[ -n "$raw" && "$raw" != "REQUIRES_RUNTIME_VERIFICATION" ]] ||
    die "DIC_EXPECTED_SERVICES must contain the runtime-verified Compose service inventory."
  IFS=',' read -r -a DIC_EXPECTED_SERVICE_LIST <<<"$raw"
  ((${#DIC_EXPECTED_SERVICE_LIST[@]} > 0)) ||
    die "At least one expected Compose service is required."
  for service in "${DIC_EXPECTED_SERVICE_LIST[@]}"; do
    [[ "$service" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] ||
      die "DIC_EXPECTED_SERVICES contains an invalid service name."
    [[ "$seen" != *"|${service}|"* ]] ||
      die "DIC_EXPECTED_SERVICES must contain each service exactly once."
    seen="${seen}${service}|"
  done
}

project_container_diagnostics() {
  warn "Project-scoped container states:"
  docker_safe ps -a \
    --filter "label=com.docker.compose.project=${DIC_PROJECT_NAME}" \
    --format '{{.Names}} {{.Status}}' |
    LC_ALL=C sort >&2 || warn "Project diagnostics query failed."
}

check_project_container_health_once() {
  local record id service state health name expected_sorted actual_sorted
  local inventory_output pending=no
  local -a actual_ids=()
  local -a actual_services=()
  DIC_ACTUAL_SERVICE_DIAGNOSTIC=""

  inventory_output="$(docker_safe ps -a \
    --filter "label=com.docker.compose.project=${DIC_PROJECT_NAME}" \
    --format '{{.ID}}|{{.Label "com.docker.compose.service"}}')" ||
    { warn "Could not read the project container inventory."; return "$DIC_HEALTH_FAILED"; }
  while IFS= read -r record; do
    [[ -n "$record" ]] || continue
    IFS='|' read -r id service <<<"$record"
    if [[ -z "$id" ]]; then
      warn "A project inventory record lacks a container identifier."
      actual_services+=("<missing-container-id>")
      continue
    fi
    actual_ids+=("$id")
    if [[ -z "$service" ]]; then
      warn "A project-scoped container lacks a recognized Compose service label."
      actual_services+=("<unlabelled>")
      continue
    fi
    if [[ ! "$service" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]]; then
      warn "A project-scoped container has an invalid Compose service label."
      actual_services+=("<invalid-label>")
      continue
    fi
    actual_services+=("$service")
  done <<<"$inventory_output"

  expected_sorted="$(printf '%s\n' "${DIC_EXPECTED_SERVICE_LIST[@]}" | LC_ALL=C sort)"
  actual_sorted="$(
    if ((${#actual_services[@]})); then
      printf '%s\n' "${actual_services[@]}" | LC_ALL=C sort
    fi
  )"
  if [[ "$actual_sorted" != "$expected_sorted" ]]; then
    DIC_ACTUAL_SERVICE_DIAGNOSTIC="$actual_sorted"
    print_inventory_mismatch
    return "$DIC_HEALTH_FAILED"
  fi

  for id in "${actual_ids[@]}"; do
    IFS='|' read -r state health name < <(
      docker_safe inspect \
        --format '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}|{{.Name}}' \
        "$id"
    )
    service="${name#/}"
    case "${state}:${health}" in
      running:healthy) ;;
      running:starting)
        warn "Project container health check is still starting: ${service}."
        pending=yes
        ;;
      running:none)
        warn "Project container ${service} has no Docker health check; a verified service-level probe is required."
        return "$DIC_HEALTH_FAILED"
        ;;
      running:unhealthy)
        warn "Project container is unhealthy: ${service}."
        return "$DIC_HEALTH_FAILED"
        ;;
      paused:*|restarting:*|exited:*|dead:*|created:*|removing:*)
        warn "Project container is in a terminal/non-ready state: ${service} (${state})."
        return "$DIC_HEALTH_FAILED"
        ;;
      *)
        warn "Project container returned an unrecognized state: ${service}."
        return "$DIC_HEALTH_FAILED"
        ;;
    esac
  done
  [[ "$pending" == no ]] || return "$DIC_HEALTH_PENDING"
}

print_inventory_mismatch() {
  local expected_sorted actual_sorted
  expected_sorted="$(printf '%s\n' "${DIC_EXPECTED_SERVICE_LIST[@]}" | LC_ALL=C sort)"
  actual_sorted="${DIC_ACTUAL_SERVICE_DIAGNOSTIC:-<unlabelled-or-invalid>}"
  warn "Expected project services (sorted):"
  printf '%s\n' "$expected_sorted" >&2
  warn "Actual project services (sorted):"
  printf '%s\n' "$actual_sorted" >&2
  project_container_diagnostics
}

wait_for_project_container_health() {
  local timeout="${DIC_STARTUP_TIMEOUT_SECONDS:-600}"
  local interval="${DIC_HEALTH_POLL_INTERVAL_SECONDS:-5}"
  local deadline result
  [[ "$timeout" =~ ^[0-9]+$ && "$timeout" -ge 1 && "$timeout" -le 1800 ]] ||
    die "DIC_STARTUP_TIMEOUT_SECONDS must be between 1 and 1800."
  [[ "$interval" =~ ^[0-9]+$ && "$interval" -ge 1 && "$interval" -le 60 ]] ||
    die "DIC_HEALTH_POLL_INTERVAL_SECONDS must be between 1 and 60."

  deadline=$((SECONDS + timeout))
  while :; do
    result=0
    check_project_container_health_once || result=$?
    case "$result" in
      0) return 0 ;;
      "$DIC_HEALTH_PENDING")
        if ((SECONDS >= deadline)); then
          warn "Timed out waiting for the complete project service inventory to become healthy."
          project_container_diagnostics
          return 1
        fi
        sleep "$interval"
        ;;
      *)
        project_container_diagnostics
        return 1
        ;;
    esac
  done
}

verify_documented_health_urls() {
  local raw="${DIC_VERIFIED_HEALTH_URLS:-}"
  local approved_hosts="${DIC_APPROVED_HEALTH_HOSTS:-}"
  local url index=0 validation_input validated_output
  local -a urls=()
  [[ -n "$raw" && "$raw" != "REQUIRES_RUNTIME_VERIFICATION" ]] ||
    die "DIC_VERIFIED_HEALTH_URLS is unresolved; container health alone cannot prove DataHub readiness."
  [[ "$approved_hosts" != "REQUIRES_RUNTIME_VERIFICATION" ]] ||
    die "DIC_APPROVED_HEALTH_HOSTS remains unresolved."
  require_command python3
  require_command curl

  validation_input="${raw}"$'\n'"${approved_hosts}"$'\n'
  validated_output="$(
    printf '%s' "$validation_input" |
      python3 "${DIC_SCRIPT_DIR}/validate_health_urls.py"
  )" || die "Health URL validation failed before any probe was sent."
  while IFS= read -r url; do
    [[ -n "$url" ]] && urls+=("$url")
  done <<<"$validated_output"
  ((${#urls[@]} > 0)) || die "At least one runtime-verified health URL is required."
  require_command env

  for url in "${urls[@]}"; do
    index=$((index + 1))
    env \
      -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u NO_PROXY \
      -u http_proxy -u https_proxy -u all_proxy -u no_proxy \
      curl --noproxy '*' \
      --fail --silent --show-error --max-time 10 "$url" >/dev/null ||
      die "Runtime-verified service health probe ${index} failed."
  done
}

main() {
  local env_file=""
  while (($#)); do
    case "$1" in
      --help) usage; exit 0 ;;
      --env) env_file="${2:-}"; shift 2 ;;
      *) die "Unknown argument: $1" ;;
    esac
  done
  load_environment "$env_file"
  require_project_name
  require_execution_approval
  select_docker_command ||
    die "Docker daemon is unavailable with current approved permissions."
  expected_services
  wait_for_project_container_health
  verify_documented_health_urls
  log "Observed project container image identifiers:"
  docker_safe ps \
    --filter "label=com.docker.compose.project=${DIC_PROJECT_NAME}" \
    --format '{{.ID}}' |
    while IFS= read -r container_id; do
      [[ -n "$container_id" ]] &&
        docker_safe inspect --format '{{.Name}} {{.Image}}' "$container_id"
    done
  log "PASS: expected project containers are healthy and configured service-level probes succeeded."
  log "This verifies configured checks only; it is not a claim of complete DataHub readiness."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
