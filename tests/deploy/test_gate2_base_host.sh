#!/usr/bin/env bash
set -Eeuo pipefail

readonly TEST_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly REPO_DIR="$(cd -- "${TEST_DIR}/../.." && pwd -P)"
readonly PRODUCTION_CHECKER="${REPO_DIR}/deploy/scripts/check_gate2_base_host.sh"
readonly FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT
readonly CHECKER="${FIXTURE_DIR}/check_gate2_base_host.fixture.sh"
readonly FIXTURE_BIN="${FIXTURE_DIR}/bin"
readonly OS_RELEASE_FIXTURE="${FIXTURE_DIR}/os-release"
readonly MEMINFO_FIXTURE="${FIXTURE_DIR}/meminfo"

# Instrument a temporary copy only. The production validator contains no
# fixture switch and always reads the host.
python3 - "$PRODUCTION_CHECKER" "$CHECKER" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
source = source.replace("/etc/os-release", "${DIC_GATE2_FIXTURE_OS_RELEASE}")
source = source.replace("/proc/meminfo", "${DIC_GATE2_FIXTURE_MEMINFO}")
source = source.replace(
    '  local name="$1"\n  command -v "$name" >/dev/null 2>&1',
    '''  local name="$1"
  if [[ ",${DIC_GATE2_FIXTURE_MISSING_COMMANDS:-}," == *",${name},"* ]]; then
    return 1
  fi
  command -v "$name" >/dev/null 2>&1''',
)
Path(sys.argv[2]).write_text(source, encoding="utf-8")
PY
chmod +x "$CHECKER"

mkdir "$FIXTURE_BIN"
cat >"${FIXTURE_BIN}/gate2-command-double" <<'EOF'
#!/usr/bin/env bash
set -eu
case "$(basename "$0")" in
  uname) printf '%s\n' "${DIC_GATE2_FIXTURE_ARCH}" ;;
  getconf) printf '%s\n' "${DIC_GATE2_FIXTURE_CPU}" ;;
  df)
    printf 'Filesystem 1048576-blocks Used Available Capacity Mounted on\n'
    printf '/dev/sda1 %s 1 %s 1%% %s\n' \
      "${DIC_GATE2_FIXTURE_ROOT_CAPACITY_MIB}" \
      "$((DIC_GATE2_FIXTURE_ROOT_CAPACITY_MIB - 1))" \
      "${DIC_GATE2_FIXTURE_ROOT_MOUNT}"
    ;;
  hostname) printf '%s\n' "${DIC_GATE2_FIXTURE_HOSTNAME}" ;;
  date) printf '%s\n' "${DIC_GATE2_FIXTURE_CLOCK_EPOCH}" ;;
  ps) printf '%s\n' "${DIC_GATE2_FIXTURE_PROCESSES}" ;;
  timedatectl) printf '%s\n' "${DIC_GATE2_FIXTURE_NTP_SYNC}" ;;
  ss) cat "${DIC_GATE2_FIXTURE_LISTENER_FILE}" ;;
  ip) printf '%s\n' "${DIC_GATE2_FIXTURE_IP_OUTPUT}" ;;
  findmnt) printf '%s\n' "${DIC_GATE2_FIXTURE_ROOT_SOURCE}" ;;
  systemctl) exit 3 ;;
  *) exit 127 ;;
esac
EOF
chmod +x "${FIXTURE_BIN}/gate2-command-double"
for command_name in uname getconf df hostname date ps timedatectl ss ip findmnt systemctl; do
  ln -s gate2-command-double "${FIXTURE_BIN}/${command_name}"
done

valid_listeners="${FIXTURE_DIR}/valid-listeners"
unexpected_listeners="${FIXTURE_DIR}/unexpected-listeners"
printf '%s\n' \
  'LISTEN 0 4096 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=1,fd=1))' \
  'LISTEN 0 4096 127.0.0.53:53 0.0.0.0:* users:(("systemd-resolved",pid=2,fd=2))' \
  'LISTEN 0 4096 127.0.0.1:8000 0.0.0.0:* users:(("local-only",pid=3,fd=3))' \
  'LISTEN 0 4096 [::1]:53 [::]:* users:(("systemd-resolved",pid=2,fd=4))' \
  'LISTEN 0 4096 ::1:9000 [::]:* users:(("local-only",pid=3,fd=5))' \
  >"$valid_listeners"
printf '%s\n' \
  'LISTEN 0 4096 0.0.0.0:22 0.0.0.0:* users:(("sshd",pid=1,fd=1))' \
  'LISTEN 0 4096 0.0.0.0:8080 0.0.0.0:* users:(("unexpected-app",pid=2,fd=2))' \
  >"$unexpected_listeners"

run_fixture() {
  cat >"$OS_RELEASE_FIXTURE" <<EOF
ID=${TEST_OS_ID:-ubuntu}
VERSION_ID="${TEST_OS_VERSION:-24.04}"
PRETTY_NAME="${TEST_OS_PRETTY:-Ubuntu 24.04 LTS}"
EOF
  cat >"$MEMINFO_FIXTURE" <<EOF
MemTotal:       ${TEST_MEMORY_KIB:-16777216} kB
SwapTotal:      ${TEST_SWAP_KIB:-0} kB
EOF
  env \
    PATH="${FIXTURE_BIN}:${PATH}" \
    DIC_GATE2_FIXTURE_OS_RELEASE="$OS_RELEASE_FIXTURE" \
    DIC_GATE2_FIXTURE_MEMINFO="$MEMINFO_FIXTURE" \
    DIC_GATE2_FIXTURE_ARCH="${TEST_ARCH:-x86_64}" \
    DIC_GATE2_FIXTURE_CPU="${TEST_CPU:-4}" \
    DIC_GATE2_FIXTURE_ROOT_CAPACITY_MIB="${TEST_ROOT_CAPACITY_MIB:-102400}" \
    DIC_GATE2_FIXTURE_ROOT_MOUNT="${TEST_ROOT_MOUNT:-/}" \
    DIC_GATE2_FIXTURE_ROOT_SOURCE="${TEST_ROOT_SOURCE:-/dev/sda1}" \
    DIC_GATE2_FIXTURE_HOSTNAME="${TEST_HOSTNAME:-dic-runtime-01}" \
    DIC_GATE2_FIXTURE_CLOCK_EPOCH="${TEST_CLOCK_EPOCH:-1784851200}" \
    DIC_GATE2_FIXTURE_NTP_SYNC="${TEST_NTP_SYNC:-yes}" \
    DIC_GATE2_FIXTURE_LISTENER_FILE="${TEST_LISTENER_FILE:-$valid_listeners}" \
    DIC_GATE2_FIXTURE_PROCESSES="${TEST_PROCESSES:-systemd /sbin/init}" \
    DIC_GATE2_FIXTURE_MISSING_COMMANDS="${TEST_MISSING_COMMANDS:-docker}" \
    DIC_GATE2_FIXTURE_IP_OUTPUT="${TEST_IP_OUTPUT:-}" \
    bash "$CHECKER" --expected-hostname dic-runtime-01
}

expect_pass() {
  local name="$1"; shift
  if ! output="$("$@" 2>&1)"; then
    printf 'FAIL fixture expected pass: %s\n%s\n' "$name" "$output" >&2
    exit 1
  fi
}
expect_fail() {
  local name="$1"; shift
  if output="$("$@" 2>&1)"; then
    printf 'FAIL fixture expected failure: %s\n%s\n' "$name" "$output" >&2
    exit 1
  fi
}

if rg -n 'DIC_GATE2_(TEST|FIXTURE)' "$PRODUCTION_CHECKER"; then
  echo "FAIL: production validator contains a fixture or test-mode environment hook." >&2
  exit 1
fi
if production_output="$(
  env \
    DIC_GATE2_TEST_MODE=yes \
    DIC_GATE2_TEST_OS_ID=ubuntu \
    DIC_GATE2_TEST_OS_VERSION=24.04 \
    DIC_GATE2_TEST_ARCH=x86_64 \
    DIC_GATE2_TEST_CPU=99 \
    DIC_GATE2_TEST_MEMORY_KIB=99999999 \
    DIC_GATE2_TEST_HOSTNAME=gate2-env-override-must-not-win \
    bash "$PRODUCTION_CHECKER" \
      --expected-hostname gate2-env-override-must-not-win 2>&1
)"; then
  echo "FAIL: production validator accepted inherited test-mode variables." >&2
  exit 1
fi
if ! grep -q 'hostname mismatch' <<<"$production_output" ||
   grep -q 'hostname matches approved manifest: gate2-env-override-must-not-win' \
     <<<"$production_output"; then
  echo "FAIL: production validator did not prove real-host hostname inspection." >&2
  exit 1
fi

expect_pass "valid pristine host" run_fixture
TEST_OS_VERSION=22.04 expect_fail "wrong Ubuntu version" run_fixture
TEST_ARCH=aarch64 expect_fail "wrong architecture" run_fixture
TEST_CPU=2 expect_fail "insufficient CPU" run_fixture
TEST_MEMORY_KIB=8388608 expect_fail "insufficient memory" run_fixture
TEST_MEMORY_KIB=16000000 expect_pass "realistic 16 GiB guest MemTotal" run_fixture
TEST_MEMORY_KIB=15728640 expect_pass "maximum allowed guest reservation" run_fixture
TEST_MEMORY_KIB=15728639 expect_fail "memory below reservation tolerance" run_fixture
TEST_ROOT_CAPACITY_MIB=51200 expect_fail "insufficient disk" run_fixture
TEST_LISTENER_FILE="$valid_listeners" expect_pass "SSH and IPv4/IPv6 loopback listeners" run_fixture
TEST_LISTENER_FILE="$unexpected_listeners" expect_fail "unexpected listener" run_fixture
TEST_PROCESSES="mcp-server-datahub --transport stdio" expect_fail "unexpected process" run_fixture
TEST_SWAP_KIB=0 expect_pass "swap absent and deferred" run_fixture
TEST_MISSING_COMMANDS="docker,ip,hostname" expect_fail "base command absence handled" run_fixture
TEST_IP_OUTPUT="2: ens4 inet 10.42.0.2/32 scope global ens4" \
  expect_pass "RFC1918 10/8 address" run_fixture
TEST_IP_OUTPUT="2: ens4 inet 172.16.1.2/24 scope global ens4" \
  expect_pass "RFC1918 lower 172 boundary" run_fixture
TEST_IP_OUTPUT="2: ens4 inet 172.31.255.254/24 scope global ens4" \
  expect_pass "RFC1918 upper 172 boundary" run_fixture
TEST_IP_OUTPUT="2: ens4 inet 192.168.40.2/24 scope global ens4" \
  expect_pass "RFC1918 192.168/16 address" run_fixture
TEST_IP_OUTPUT="2: ens4 inet 34.155.10.20/32 scope global ens4" \
  expect_fail "public IPv4 address" run_fixture

fake_bin="${FIXTURE_DIR}/fake-bin"
mkdir "$fake_bin"
printf '#!/usr/bin/env bash\nexit 0\n' >"${fake_bin}/docker"
chmod +x "${fake_bin}/docker"
PATH="${fake_bin}:${PATH}" TEST_MISSING_COMMANDS=ip \
  expect_fail "Docker unexpectedly present" run_fixture

if rg -n -i '(apt-get|snap |dnf |yum |pip |npm |curl |wget |docker pull|docker run|systemctl (start|stop|enable|disable)|rm -rf)' "$CHECKER"; then
  echo "FAIL: checker contains mutation, installation, download, or runtime-control command." >&2
  exit 1
fi

echo "Gate 2 base-host validator regression checks passed."
