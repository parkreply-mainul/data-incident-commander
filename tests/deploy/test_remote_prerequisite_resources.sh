#!/usr/bin/env bash
set -Eeuo pipefail

readonly REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
readonly SOURCE_CHECKER="${REPO_DIR}/deploy/scripts/check_remote_prerequisites.sh"
readonly FIXTURE_DIR="$(mktemp -d)"
readonly SCRIPT_DIR="${FIXTURE_DIR}/deploy/scripts"
readonly CHECKER="${SCRIPT_DIR}/check_remote_prerequisites.sh"
readonly MEMINFO="${FIXTURE_DIR}/meminfo"
readonly ENV_FILE="${FIXTURE_DIR}/remote.env"
readonly FAKE_BIN="${FIXTURE_DIR}/bin"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

mkdir -p "$SCRIPT_DIR" "$FAKE_BIN"

# Instrument only the temporary regression copy. Production always reads the
# real /proc/meminfo and exposes no fixture environment hook.
python3 - "$SOURCE_CHECKER" "$CHECKER" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
source = source.replace("/proc/meminfo", "${DIC_TEST_MEMINFO}")
Path(sys.argv[2]).write_text(source, encoding="utf-8")
PY

cat >"${SCRIPT_DIR}/common.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
DIC_DEPLOY_DIR="${DIC_TEST_DEPLOY_DIR}"
log() { printf '[Data Incident Commander] %s\n' "$*"; }
warn() { printf '[Data Incident Commander] WARN: %s\n' "$*" >&2; }
die() { printf '[Data Incident Commander] ERROR: %s\n' "$*" >&2; exit 1; }
usage_common() { :; }
load_environment() { source "$1"; }
require_project_name() { :; }
require_ubuntu_2404() { :; }
require_non_root() { :; }
select_docker_command() { return 0; }
docker_safe() { return 0; }
EOF

cat >"${FAKE_BIN}/resource-command-double" <<'EOF'
#!/usr/bin/env bash
set -eu
case "$(basename "$0")" in
  uname) printf 'x86_64\n' ;;
  getconf) printf '4\n' ;;
  df)
    printf 'Filesystem 1048576-blocks Used Available Capacity Mounted on\n'
    printf '/dev/sda1 102400 1 93598 1%% /\n'
    ;;
  docker|curl|jq|git|openssl) exit 0 ;;
  timedatectl) printf 'yes\n' ;;
  ss) exit 0 ;;
  id) printf 'operator sudo\n' ;;
  *) exit 127 ;;
esac
EOF
chmod +x "${FAKE_BIN}/resource-command-double"
for name in uname getconf df docker curl jq git openssl timedatectl ss id; do
  ln -s resource-command-double "${FAKE_BIN}/${name}"
done

cat >"$ENV_FILE" <<'EOF'
DIC_PROJECT_NAME=data-incident-commander
DIC_EXCLUSIVE_PORTS=80,443
EOF

run_fixture() {
  local memory_mib="$1"
  local swap_value="$2"
  {
    printf 'MemTotal:       %s kB\n' "$((memory_mib * 1024))"
    if [[ "$swap_value" == missing ]]; then
      :
    elif [[ "$swap_value" == malformed ]]; then
      printf 'SwapTotal:      invalid kB\n'
    else
      printf 'SwapTotal:      %s kB\n' "$swap_value"
    fi
  } >"$MEMINFO"

  env \
    PATH="${FAKE_BIN}:${PATH}" \
    DIC_TEST_MEMINFO="$MEMINFO" \
    DIC_TEST_DEPLOY_DIR="$FIXTURE_DIR" \
    bash "$CHECKER" --env "$ENV_FILE"
}

expect_pass() {
  local name="$1" memory_mib="$2" swap_kib="$3"
  local output
  if ! output="$(run_fixture "$memory_mib" "$swap_kib" 2>&1)"; then
    printf 'FAIL fixture expected pass: %s\n%s\n' "$name" "$output" >&2
    exit 1
  fi
  printf '%s\n' "$output"
}

expect_fail() {
  local name="$1" memory_mib="$2" swap_kib="$3"
  local output
  if output="$(run_fixture "$memory_mib" "$swap_kib" 2>&1)"; then
    printf 'FAIL fixture expected failure: %s\n%s\n' "$name" "$output" >&2
    exit 1
  fi
  printf '%s\n' "$output"
}

expect_pass "live guest memory" 15987 2099196 >/dev/null
expect_pass "memory threshold" 15360 2099196 >/dev/null
expect_fail "one MiB below memory threshold" 15359 2099196 >/dev/null
expect_fail "obviously undersized memory" 8192 2099196 >/dev/null

above_output="$(expect_pass "swap above two GiB" 15987 2099196)"
grep -Fq 'INFO: SwapTotal: 2099196 KiB' <<<"$above_output"
expect_pass "swap exactly two GiB" 15987 2097152 >/dev/null
expect_fail "swap below two GiB" 15987 2097151 >/dev/null
expect_fail "zero swap" 15987 0 >/dev/null
expect_fail "malformed swap" 15987 malformed >/dev/null
expect_fail "missing swap" 15987 missing >/dev/null

if rg -n 'DIC_TEST_' "$SOURCE_CHECKER"; then
  echo "FAIL: production checker contains a test-fixture hook." >&2
  exit 1
fi

echo "Remote prerequisite resource regression checks passed."
