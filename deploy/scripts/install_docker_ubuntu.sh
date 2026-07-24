#!/usr/bin/env bash
set -Eeuo pipefail
source "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)/common.sh"

usage() { echo "Usage: $0 [--help] [--env FILE] [--plan]"; usage_common; }
env_file=""; plan=no
while (($#)); do
  case "$1" in
    --help) usage; exit 0 ;;
    --env) env_file="${2:-}"; shift 2 ;;
    --plan) plan=yes; shift ;;
    *) die "Unknown argument: $1" ;;
  esac
done
load_environment "$env_file"
require_project_name
if [[ "$plan" == yes ]]; then
  log "PLAN: require Ubuntu 24.04 LTS and a named sudo-capable administrator."
  log "PLAN: configure Docker's official apt repository and signing key."
  log "PLAN: list versions; require DIC_DOCKER_VERSION before pinned installation."
  log "PLAN: install docker-ce, CLI, containerd, buildx, and Compose v2."
  log "PLAN: verify daemon locally; do not expose TCP or change docker-group membership."
  exit 0
fi
require_ubuntu_2404
require_non_root
require_execution_approval
require_variable DIC_DOCKER_VERSION
docker_installer_preflight
log "Refusing automated package removal: conflicting Docker packages must be reviewed manually."
check_conflicting_docker_packages dpkg-query
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
codename="$(. /etc/os-release && printf '%s' "${UBUNTU_CODENAME:-$VERSION_CODENAME}")"
architecture="$(dpkg --print-architecture)"
printf '%s\n' \
  'Types: deb' \
  'URIs: https://download.docker.com/linux/ubuntu' \
  "Suites: ${codename}" \
  'Components: stable' \
  "Architectures: ${architecture}" \
  'Signed-By: /etc/apt/keyrings/docker.asc' |
  sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null
sudo apt-get update
sudo apt-get install --yes \
  "docker-ce=${DIC_DOCKER_VERSION}" \
  "docker-ce-cli=${DIC_DOCKER_VERSION}" \
  containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl is-active --quiet docker || die "Docker daemon is not active."
sudo docker version >/dev/null
sudo docker compose version >/dev/null
log "PASS: Docker Engine and Compose verified. No docker-group membership was changed."
