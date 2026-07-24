#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() { echo "Usage: $0 [--help] [--env FILE]"; usage_common; }
env_file=""
while (($#)); do
  case "$1" in
    --help) usage; exit 0 ;;
    --env) env_file="${2:-}"; shift 2 ;;
    *) die "Unknown argument: $1" ;;
  esac
done
load_environment "$env_file"
require_project_name
require_ubuntu_2404
require_non_root

failures=0
check_minimum() {
  local label="$1" actual="$2" minimum="$3"
  if ((actual >= minimum)); then log "PASS: ${label}: ${actual}"; else
    warn "FAIL: ${label}: ${actual}; required project gate: ${minimum}"
    failures=$((failures + 1))
  fi
}

arch="$(uname -m)"
[[ "$arch" == "x86_64" || "$arch" == "aarch64" ]] ||
  { warn "FAIL: unsupported architecture ${arch}"; failures=$((failures + 1)); }
check_minimum "CPU threads" "$(getconf _NPROCESSORS_ONLN)" 4
memory_kib="$(awk '/MemTotal/ {print $2}' /proc/meminfo)"
check_minimum "physical memory MiB" "$((memory_kib / 1024))" 16384
disk_mib="$(df -Pm "$DIC_DEPLOY_DIR" | awk 'NR==2 {print $4}')"
check_minimum "available disk MiB" "$disk_mib" 51200

for command in docker curl jq git openssl; do
  version_argument="--version"
  [[ "$command" == openssl ]] && version_argument="version"
  if command -v "$command" >/dev/null 2>&1 && "$command" "$version_argument" >/dev/null 2>&1; then
    log "PASS: ${command} executable is usable."
  else
    warn "FAIL: ${command} is missing or unusable."
    failures=$((failures + 1))
  fi
done
select_docker_command ||
  { warn "FAIL: Docker daemon is unavailable to the current user."; failures=$((failures + 1)); }
docker_safe compose version >/dev/null 2>&1 ||
  { warn "FAIL: Docker Compose v2 is unavailable."; failures=$((failures + 1)); }

log "INFO: swap visible: $(awk '/SwapTotal/ {print $2 \" KiB\"}' /proc/meminfo)"
if command -v timedatectl >/dev/null 2>&1; then
  timedatectl show -p NTPSynchronized --value 2>/dev/null |
    sed 's/^/[DataIncident Commander] INFO: NTP synchronized: /'
else
  warn "WARN: timedatectl unavailable; time synchronization needs manual verification."
fi

IFS=',' read -r -a ports <<<"${DIC_EXCLUSIVE_PORTS:-}"
for port in "${ports[@]}"; do
  [[ "$port" =~ ^[0-9]+$ ]] || die "Invalid port in DIC_EXCLUSIVE_PORTS."
  if command -v ss >/dev/null 2>&1 && ss -H -ltn "sport = :${port}" | grep -q .; then
    warn "FAIL: planned exclusive port ${port} already has a listener."
    failures=$((failures + 1))
  else
    log "PASS: planned exclusive port ${port} has no detected TCP listener."
  fi
done

if id -nG | tr ' ' '\n' | grep -qx docker; then
  warn "WARN: current user belongs to root-equivalent docker group."
else
  log "INFO: current user is not in the docker group; sudo Docker access may be required."
fi

((failures == 0)) || die "${failures} blocking prerequisite check(s) failed."
log "PASS: remote project deployment gates passed."
