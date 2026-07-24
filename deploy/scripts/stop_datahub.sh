#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
usage() { echo "Usage: $0 [--help] [--env FILE]"; usage_common; }
env_file=""; while (($#)); do case "$1" in --help) usage; exit 0 ;;
  --env) env_file="${2:-}"; shift 2 ;; *) die "Unknown argument: $1" ;; esac; done
load_environment "$env_file"; require_project_name; require_execution_approval
[[ "${DIC_QUICKSTART_PROJECT_SCOPE_VERIFIED:-no}" == yes ]] ||
  die "Project-scoped stop behavior is unverified; refusing to affect Docker state."
die "Stop command remains gated until the remote quickstart ownership inventory is recorded."
