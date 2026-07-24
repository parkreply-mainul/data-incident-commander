#!/usr/bin/env bash
set -Eeuo pipefail

readonly TEST_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
readonly COMMON="${TEST_ROOT}/deploy/scripts/common.sh"
readonly INSTALLER="${TEST_ROOT}/deploy/scripts/install_docker_ubuntu.sh"
readonly TEST_TMP="$(mktemp -d)"
trap 'rm -rf -- "$TEST_TMP"' EXIT

make_query_double() {
  local scenario="$1"
  local path="${TEST_TMP}/dpkg-query-${scenario}"
  sed "s/__SCENARIO__/${scenario}/g" >"$path" <<'SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail
package="${@: -1}"
case "__SCENARIO__:${package}" in
  none:*) exit 1 ;;
  first:docker.io|middle:docker-compose-v2|last:runc) printf 'ii '; exit 0 ;;
  multiple:docker.io|multiple:runc) printf 'ii '; exit 0 ;;
  residual:containerd) printf 'rc '; exit 0 ;;
  query_error:docker-compose-v2) exit 2 ;;
  *) exit 1 ;;
esac
SCRIPT
  chmod +x "$path"
  printf '%s' "$path"
}

run_check() {
  local scenario="$1"
  bash -c 'source "$1"; check_conflicting_docker_packages "$2"' \
    test "$COMMON" "$(make_query_double "$scenario")"
}

run_check none
run_check residual

for scenario in first middle last multiple; do
  if output="$(run_check "$scenario" 2>&1)"; then
    echo "Expected conflict detection for scenario: ${scenario}" >&2
    exit 1
  fi
  [[ "$output" == *"Conflicting installed Docker packages detected"* ]]
done

if output="$(run_check query_error 2>&1)"; then
  echo "Expected query failure to stop validation." >&2
  exit 1
fi
[[ "$output" == *"Could not query package state"* ]]

check_line="$(grep -n 'check_conflicting_docker_packages dpkg-query' "$INSTALLER" | cut -d: -f1)"
mutation_line="$(grep -n 'sudo install -m 0755 -d /etc/apt/keyrings' "$INSTALLER" | cut -d: -f1)"
[[ -n "$check_line" && -n "$mutation_line" && "$check_line" -lt "$mutation_line" ]]

echo "Docker conflict detection regression checks passed."
