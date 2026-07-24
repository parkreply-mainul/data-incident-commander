#!/usr/bin/env bash
set -Eeuo pipefail

readonly TEST_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
readonly COMMON="${TEST_ROOT}/deploy/scripts/common.sh"
readonly INSTALLER="${TEST_ROOT}/deploy/scripts/install_docker_ubuntu.sh"
readonly TEST_TMP="$(mktemp -d)"
trap 'rm -rf -- "$TEST_TMP"' EXIT
readonly REQUIRED=(uname sudo curl apt-get dpkg dpkg-query install chmod tee systemctl)

make_command_directory() {
  local missing="${1:-}" directory="${TEST_TMP}/commands-${1:-all}" command
  mkdir -p "$directory"
  for command in "${REQUIRED[@]}"; do
    [[ "$command" == "$missing" ]] && continue
    printf '#!/bin/sh\nexit 97\n' >"${directory}/${command}"
    chmod +x "${directory}/${command}"
  done
  printf '%s' "$directory"
}

run_preflight() {
  local path="$1"
  bash -c 'source "$1"; PATH="$2"; docker_installer_preflight' \
    test "$COMMON" "$path"
}

for missing in curl sudo apt-get; do
  marker="${TEST_TMP}/mutation-${missing}"
  result=0
  output="$(run_preflight "$(make_command_directory "$missing")" 2>&1)" || result=$?
  [[ "$result" -ne 0 ]]
  [[ "$output" == *"Required command is unavailable: ${missing}"* ]]
  [[ ! -e "$marker" ]]
done

all_commands="$(make_command_directory)"
run_preflight "$all_commands"
run_preflight "$all_commands"

ubuntu_line="$(grep -n '^require_ubuntu_2404$' "$INSTALLER" | cut -d: -f1)"
preflight_line="$(grep -n '^docker_installer_preflight$' "$INSTALLER" | cut -d: -f1)"
conflict_line="$(grep -n '^check_conflicting_docker_packages dpkg-query$' "$INSTALLER" | cut -d: -f1)"
mutation_line="$(grep -n '^sudo install -m 0755 -d /etc/apt/keyrings$' "$INSTALLER" | cut -d: -f1)"
[[ "$ubuntu_line" -lt "$preflight_line" ]]
[[ "$preflight_line" -lt "$conflict_line" ]]
[[ "$conflict_line" -lt "$mutation_line" ]]

echo "Docker installer preflight regression checks passed."
