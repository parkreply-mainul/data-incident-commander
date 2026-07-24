#!/usr/bin/env bash
set -Eeuo pipefail

readonly DIC_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly DIC_DEPLOY_DIR="$(cd -- "${DIC_SCRIPT_DIR}/.." && pwd -P)"
declare -a DIC_DOCKER_COMMAND=(docker)

log() { printf '[DataIncident Commander] %s\n' "$*"; }
warn() { printf '[DataIncident Commander] WARN: %s\n' "$*" >&2; }
die() { printf '[DataIncident Commander] ERROR: %s\n' "$*" >&2; exit 1; }

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command is unavailable: $1"
}

docker_installer_preflight() {
  local command
  for command in uname sudo curl apt-get dpkg dpkg-query install chmod tee systemctl; do
    require_command "$command"
  done
}

check_conflicting_docker_packages() {
  local query_command="${1:-dpkg-query}"
  local package query_output query_status
  local -a installed=()
  local -a residual=()
  local -a packages=(
    docker.io
    docker-compose
    docker-compose-v2
    podman-docker
    containerd
    runc
  )

  require_command "$query_command"
  for package in "${packages[@]}"; do
    query_status=0
    query_output="$("$query_command" -W -f='${db:Status-Abbrev}' "$package" 2>/dev/null)" ||
      query_status=$?
    case "$query_status" in
      0)
        case "$query_output" in
          ii*) installed+=("$package") ;;
          rc*) residual+=("$package") ;;
          *) ;; # Known to dpkg, but neither installed nor residual config.
        esac
        ;;
      1) ;; # Package is absent from the local dpkg database.
      *) die "Could not query package state for ${package}; dpkg-query exited ${query_status}." ;;
    esac
  done

  if ((${#residual[@]})); then
    warn "Residual package configuration detected (not installed): ${residual[*]}."
  fi
  if ((${#installed[@]})); then
    die "Conflicting installed Docker packages detected: ${installed[*]}. Remove them manually according to Docker's official Ubuntu guidance, then rerun this script."
  fi
}

select_docker_command() {
  require_command docker
  if docker info >/dev/null 2>&1; then
    DIC_DOCKER_COMMAND=(docker)
  elif command -v sudo >/dev/null 2>&1 && sudo -n docker info >/dev/null 2>&1; then
    DIC_DOCKER_COMMAND=(sudo -n docker)
  else
    return 1
  fi
}

docker_safe() {
  "${DIC_DOCKER_COMMAND[@]}" "$@"
}

require_variable() {
  local name="$1"
  [[ -n "${!name:-}" ]] || die "Required environment variable is unset: ${name}"
}

load_environment() {
  local file="${1:-${DIC_ENV_FILE:-}}"
  [[ -n "$file" ]] || die "Use --env FILE or set DIC_ENV_FILE."
  [[ -f "$file" ]] || die "Environment file does not exist: ${file}"
  # shellcheck disable=SC1090
  set -a
  source "$file"
  set +a
}

require_project_name() {
  require_variable DIC_PROJECT_NAME
  [[ "$DIC_PROJECT_NAME" =~ ^[a-z0-9][a-z0-9-]{2,62}$ ]] ||
    die "DIC_PROJECT_NAME must be a lowercase project-scoped name."
}

require_ubuntu_2404() {
  require_command uname
  [[ "$(uname -s)" == "Linux" ]] || die "This script supports Ubuntu Linux only."
  [[ -r /etc/os-release ]] || die "/etc/os-release is unavailable."
  # shellcheck disable=SC1091
  source /etc/os-release
  [[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "24.04" ]] ||
    die "Only verified Ubuntu 24.04 LTS is supported by this package."
}

require_non_root() {
  [[ "${EUID}" -ne 0 ]] || die "Run as a named sudo-capable administrator, not root."
}

require_execution_approval() {
  [[ "${DIC_REMOTE_APPROVED:-no}" == "yes" ]] ||
    die "Remote provisioning/use has not been explicitly approved."
  [[ "${DIC_REMOTE_EXECUTION_APPROVED:-no}" == "yes" ]] ||
    die "Remote execution approval is absent."
}

confirm_exact() {
  local expected="$1"
  local prompt="$2"
  local answer
  [[ -t 0 ]] || die "Interactive confirmation is required."
  read -r -p "${prompt} Type '${expected}': " answer
  [[ "$answer" == "$expected" ]] || die "Confirmation did not match."
}

usage_common() {
  printf 'Options:\n  --help       Show help\n  --env FILE   Load a project environment file\n  --plan       Print intended actions without changing state\n'
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  case "${1:-}" in
    --help|"") echo "Shared deployment-script helpers."; usage_common ;;
    *) die "common.sh is a library and accepts only --help." ;;
  esac
fi
