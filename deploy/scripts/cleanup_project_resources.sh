#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
usage() { echo "Usage: $0 [--help] [--env FILE]"; usage_common; }
env_file=""; while (($#)); do case "$1" in --help) usage; exit 0 ;;
  --env) env_file="${2:-}"; shift 2 ;; *) die "Unknown argument: $1" ;; esac; done
load_environment "$env_file"; require_project_name; require_execution_approval
[[ "${DIC_CLEANUP_CONFIRMATION:-no}" == "yes" ]] ||
  die "Set DIC_CLEANUP_CONFIRMATION=yes only after project resource IDs are reviewed."
confirm_exact "delete-${DIC_PROJECT_NAME}" "Delete only inventoried project-scoped resources."
die "Cleanup implementation remains blocked until the remote resource inventory is recorded."
