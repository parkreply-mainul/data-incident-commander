#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
usage() { echo "Usage: $0 [--help] [--env FILE]"; usage_common; }
env_file=""; while (($#)); do case "$1" in --help) usage; exit 0 ;;
  --env) env_file="${2:-}"; shift 2 ;; *) die "Unknown argument: $1" ;; esac; done
load_environment "$env_file"; require_project_name
select_docker_command || die "Docker daemon is unavailable with current approved permissions."
log "Host: $(uname -srm)"
log "Docker: $(docker_safe version --format '{{.Client.Version}}' 2>/dev/null || echo unavailable)"
log "Compose: $(docker_safe compose version --short 2>/dev/null || echo unavailable)"
log "Project containers (names and status only):"
docker_safe ps -a --filter "label=com.docker.compose.project=${DIC_PROJECT_NAME}" \
  --format '{{.Names}}\t{{.Status}}'
log "Diagnostics omit environment values, inspect payloads, and container logs."
