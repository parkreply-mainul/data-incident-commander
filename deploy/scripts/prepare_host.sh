#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"
usage() { echo "Usage: $0 [--help] [--env FILE] --plan"; usage_common; }
env_file=""; plan=no
while (($#)); do case "$1" in
  --help) usage; exit 0 ;; --env) env_file="${2:-}"; shift 2 ;;
  --plan) plan=yes; shift ;; *) die "Unknown argument: $1" ;; esac; done
load_environment "$env_file"; require_project_name
[[ "$plan" == yes ]] || die "Host preparation execution is blocked pending remote provisioning approval."
log "PLAN: validate 4 vCPU, 16 GiB RAM, 50 GiB free disk, Ubuntu 24.04, clock, swap, ports."
log "PLAN: install pinned Docker from official apt repository only after separate approval."
log "PLAN: create project-owned directories with least privilege; store secrets outside Git."
log "PLAN: apply cloud and host default-deny firewalls before public application exposure."
