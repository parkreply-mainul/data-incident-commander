#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
usage() { echo "Usage: $0 [--help] [--env FILE] [--plan]"; usage_common; }
env_file=""; plan=no
while (($#)); do case "$1" in
  --help) usage; exit 0 ;; --env) env_file="${2:-}"; shift 2 ;;
  --plan) plan=yes; shift ;; *) die "Unknown argument: $1" ;; esac; done
load_environment "$env_file"; require_project_name
[[ "${DIC_DATAHUB_VERSION:-}" == "v1.6.0" ]] || die "DIC_DATAHUB_VERSION must be v1.6.0."
if [[ "$plan" == yes ]]; then
  log "PLAN: rerun remote prerequisites and verify project-scoped quickstart behavior."
  log "PLAN: inspect the resolved v1.6.0 Compose configuration before any pull."
  log "PLAN: run: datahub docker quickstart --version v1.6.0"
  log "PLAN: bounded health verification and image-digest recording follow startup."
  log "GATE: MCP and mutation remain disabled; internal services remain private."
  exit 0
fi
require_execution_approval; require_ubuntu_2404; require_non_root
[[ "${DIC_DATAHUB_START_APPROVED:-no}" == yes ]] || die "DataHub startup is not approved."
[[ "${DIC_QUICKSTART_PROJECT_SCOPE_VERIFIED:-no}" == yes ]] ||
  die "Quickstart Compose project scoping has not been runtime verified; startup blocked."
"${DIC_SCRIPT_DIR}/check_remote_prerequisites.sh" --env "$env_file"
require_command datahub
log "IMPLEMENTATION GATE: resolved Compose inspection and project-label behavior require the approved remote runtime."
die "Startup intentionally remains blocked until the runtime checkpoint records resolved configuration."
