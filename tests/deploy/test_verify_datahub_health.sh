#!/usr/bin/env bash
set -Eeuo pipefail

readonly TEST_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
readonly VERIFIER="${TEST_ROOT}/deploy/scripts/verify_datahub.sh"
readonly TEST_TMP="$(mktemp -d)"
trap 'rm -rf -- "$TEST_TMP"' EXIT

make_docker_double() {
  local scenario="$1"
  local path="${TEST_TMP}/docker-${scenario}"
  sed "s/__SCENARIO__/${scenario}/g; s|__STATE_FILE__|${TEST_TMP}/transition-state|g" \
    >"$path" <<'SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail
scenario="__SCENARIO__"
arguments=" $* "

if [[ "${1:-}" == "ps" ]]; then
  [[ "$arguments" == *" label=com.docker.compose.project=dic-test "* ]] ||
    { echo "unscoped Docker query" >&2; exit 99; }
  if [[ "$arguments" == *" {{.ID}}|{{.Label "* ]]; then
    case "$scenario" in
      none) ;;
      partial) printf 'id-alpha|alpha\n' ;;
      unexpected|unexpected_unhealthy)
        printf 'id-alpha|alpha\nid-beta|beta\nid-gamma|gamma\n'
        ;;
      multiple_unexpected)
        printf 'id-alpha|alpha\nid-beta|beta\nid-gamma|gamma\nid-delta|delta\n'
        ;;
      duplicate) printf 'id-alpha|alpha\nid-beta|beta\nid-beta-2|beta\n' ;;
      orphan) printf 'id-alpha|alpha\nid-beta|beta\nid-orphan|\n' ;;
      *) printf 'id-alpha|alpha\nid-beta|beta\n' ;;
    esac
  elif [[ "$arguments" == *" {{.Names}} {{.Status}} "* ]]; then
    printf 'dic-test-beta scoped-state\n'
    printf 'dic-test-alpha scoped-state\n'
    case "$scenario" in
      unexpected|unexpected_unhealthy) printf 'dic-test-gamma scoped-state\n' ;;
      multiple_unexpected)
        printf 'dic-test-gamma scoped-state\ndic-test-delta scoped-state\n'
        ;;
      duplicate) printf 'dic-test-beta-2 scoped-state\n' ;;
      orphan) printf 'dic-test-orphan scoped-state\n' ;;
    esac
  fi
  exit 0
fi

if [[ "${1:-}" == "inspect" ]]; then
  id="${@: -1}"
  [[ "$id" == id-alpha || "$id" == id-beta || "$id" == id-gamma ]] ||
    { echo "inspect attempted for an unscoped container ID" >&2; exit 99; }
  service="${id#id-}"
  case "$scenario:$service" in
    starting:*) printf 'running|starting|/dic-test-%s\n' "$service" ;;
    unhealthy:*|unexpected_unhealthy:gamma)
      printf 'running|unhealthy|/dic-test-%s\n' "$service"
      ;;
    exited:*) printf 'exited|none|/dic-test-%s\n' "$service" ;;
    nohealth:*) printf 'running|none|/dic-test-%s\n' "$service" ;;
    transition:*)
      count=0
      [[ -f "__STATE_FILE__" ]] && read -r count <"__STATE_FILE__"
      count=$((count + 1))
      printf '%s\n' "$count" >"__STATE_FILE__"
      if [[ "$count" -le 2 ]]; then
        printf 'running|starting|/dic-test-%s\n' "$service"
      else
        printf 'running|healthy|/dic-test-%s\n' "$service"
      fi
      ;;
    *) printf 'running|healthy|/dic-test-%s\n' "$service" ;;
  esac
  exit 0
fi

echo "unexpected Docker-double invocation" >&2
exit 98
SCRIPT
  chmod +x "$path"
  printf '%s' "$path"
}

run_once() {
  local scenario="$1"
  bash -c '
    source "$1"
    DIC_PROJECT_NAME=dic-test
    DIC_EXPECTED_SERVICES=alpha,beta
    DIC_DOCKER_COMMAND=("$2")
    expected_services
    check_project_container_health_once
  ' test "$VERIFIER" "$(make_docker_double "$scenario")"
}

expect_status() {
  local expected="$1" scenario="$2" result=0
  run_once "$scenario" >/dev/null 2>&1 || result=$?
  [[ "$result" -eq "$expected" ]] || {
    echo "Scenario ${scenario}: expected ${expected}, observed ${result}." >&2
    exit 1
  }
}

expect_status 0 healthy
expect_status 20 none
expect_status 20 partial
expect_status 10 starting
expect_status 20 unhealthy
expect_status 20 exited
expect_status 20 nohealth
expect_status 20 unexpected
expect_status 20 multiple_unexpected
expect_status 20 duplicate
expect_status 20 orphan
expect_status 20 unexpected_unhealthy
expect_status 0 external_ignored

diagnostic_result=0
diagnostic_output="$(run_once multiple_unexpected 2>&1)" || diagnostic_result=$?
[[ "$diagnostic_result" -eq 20 ]]
[[ "$diagnostic_output" == *$'Actual project services (sorted):\nalpha\nbeta\ndelta\ngamma'* ]]
[[ "$diagnostic_output" != *"external-container"* ]]

bash -c '
  source "$1"
  DIC_PROJECT_NAME=dic-test
  DIC_EXPECTED_SERVICES=alpha,beta
  DIC_STARTUP_TIMEOUT_SECONDS=3
  DIC_HEALTH_POLL_INTERVAL_SECONDS=1
  DIC_DOCKER_COMMAND=("$2")
  expected_services
  wait_for_project_container_health
' test "$VERIFIER" "$(make_docker_double transition)" >/dev/null 2>&1

timeout_result=0
timeout_output="$(
  bash -c '
    source "$1"
    DIC_PROJECT_NAME=dic-test
    DIC_EXPECTED_SERVICES=alpha,beta
    DIC_STARTUP_TIMEOUT_SECONDS=1
    DIC_HEALTH_POLL_INTERVAL_SECONDS=1
    DIC_DOCKER_COMMAND=("$2")
    expected_services
    wait_for_project_container_health
  ' test "$VERIFIER" "$(make_docker_double starting)" 2>&1
)" || timeout_result=$?
[[ "$timeout_result" -ne 0 ]]
[[ "$timeout_output" == *"Timed out"* ]]
[[ "$timeout_output" == *"dic-test-alpha"* ]]
[[ "$timeout_output" != *"external"* ]]

gate_result=0
gate_output="$(
  bash -c '
    source "$1"
    DIC_VERIFIED_HEALTH_URLS=REQUIRES_RUNTIME_VERIFICATION
    DIC_APPROVED_HEALTH_HOSTS=REQUIRES_RUNTIME_VERIFICATION
    verify_documented_health_urls
  ' test "$VERIFIER" 2>&1
)" || gate_result=$?
[[ "$gate_result" -ne 0 ]]
[[ "$gate_output" == *"container health alone cannot prove DataHub readiness"* ]]

echo "DataHub project health-verification regression checks passed."
