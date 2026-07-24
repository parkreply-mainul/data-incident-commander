#!/usr/bin/env bash
set -Eeuo pipefail

readonly MIN_CPU=4
readonly APPROVED_MEMORY_MIB=16384
# Linux MemTotal excludes a small amount reserved by the virtual platform and
# kernel. Permit at most 1 GiB of that reservation on the approved 16 GiB VM.
readonly MIN_GUEST_MEMORY_MIB=15360
readonly MIN_ROOT_MIB=81920
readonly MIN_CLOCK_EPOCH=1704067200
failures=0
warnings=0

log() { printf '[DataIncident Commander Gate 2] %s\n' "$*"; }
pass() { log "PASS: $*"; }
warn() { printf '[DataIncident Commander Gate 2] WARN: %s\n' "$*" >&2; warnings=$((warnings + 1)); }
fail() { printf '[DataIncident Commander Gate 2] FAIL: %s\n' "$*" >&2; failures=$((failures + 1)); }

usage() {
  cat <<'EOF'
Usage: check_gate2_base_host.sh --expected-hostname NAME

Read-only validation for a pristine Ubuntu 24.04 Gate 2 host. No package
installation, network download, Docker, curl, jq, git, openssl, Python package,
cloud SDK, or repository checkout is required.
EOF
}

expected_hostname=""
while (($#)); do
  case "$1" in
    --help) usage; exit 0 ;;
    --expected-hostname) expected_hostname="${2:-}"; shift 2 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ -n "$expected_hostname" ]] || { printf 'Missing --expected-hostname NAME.\n' >&2; exit 2; }
[[ "$expected_hostname" =~ ^[a-z0-9][a-z0-9-]{0,62}$ ]] ||
  { printf 'Expected hostname must be a lowercase DNS label.\n' >&2; exit 2; }

has_command() {
  local name="$1"
  command -v "$name" >/dev/null 2>&1
}

for name in uname getconf awk df hostname date ps; do
  if has_command "$name"; then pass "base command available: ${name}"
  else fail "base image command unavailable: ${name}"; fi
done
if ((failures)); then
  printf '[DataIncident Commander Gate 2] ERROR: base command preflight failed; no further probes ran.\n' >&2
  exit 1
fi

if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  source /etc/os-release
  os_id="${ID:-}"
  os_version="${VERSION_ID:-}"
  os_pretty="${PRETTY_NAME:-}"
else
  os_id=""; os_version=""; os_pretty=""
  fail "/etc/os-release is absent or unreadable."
fi
if [[ "$os_id" == ubuntu && "$os_version" == 24.04 && "$os_pretty" == *LTS* ]]; then
  pass "operating system is Ubuntu 24.04 LTS."
else
  fail "operating system must be Ubuntu 24.04 LTS; observed ID=${os_id:-unknown}, VERSION_ID=${os_version:-unknown}."
fi

architecture="$(uname -m 2>/dev/null || true)"
if [[ "$architecture" == x86_64 || "$architecture" == amd64 ]]; then
  pass "architecture is ${architecture}."
else
  fail "architecture must be x86_64/amd64; observed ${architecture:-unknown}."
fi

cpu_count="$(getconf _NPROCESSORS_ONLN 2>/dev/null || true)"
if [[ "$cpu_count" =~ ^[0-9]+$ ]] && ((cpu_count >= MIN_CPU)); then
  pass "online CPU count is ${cpu_count}."
else
  fail "online CPU count must be at least ${MIN_CPU}; observed ${cpu_count:-unknown}."
fi

memory_kib="$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || true)"
if [[ "$memory_kib" =~ ^[0-9]+$ ]] &&
   ((memory_kib / 1024 >= MIN_GUEST_MEMORY_MIB)); then
  pass "guest-visible memory is $((memory_kib / 1024)) MiB, consistent with the approved ${APPROVED_MEMORY_MIB} MiB machine after reservations."
else
  fail "approved memory is ${APPROVED_MEMORY_MIB} MiB and guest-visible memory must be at least ${MIN_GUEST_MEMORY_MIB} MiB; observed ${memory_kib:-unknown} KiB."
fi

read -r root_capacity_mib root_mount < <(df -Pm / 2>/dev/null | awk 'NR == 2 {print $2, $6}') || true
if [[ "$root_capacity_mib" =~ ^[0-9]+$ && "$root_mount" == / &&
      "$root_capacity_mib" -ge "$MIN_ROOT_MIB" ]]; then
  pass "root filesystem capacity is ${root_capacity_mib} MiB."
else
  fail "root filesystem must be / with at least ${MIN_ROOT_MIB} MiB capacity; observed ${root_capacity_mib:-unknown} MiB at ${root_mount:-unknown}."
fi

if has_command findmnt; then
  root_source="$(findmnt -n -o SOURCE / 2>/dev/null || true)"
else
  root_source="$(awk '$2 == "/" {print $1; exit}' /proc/mounts 2>/dev/null || true)"
fi
case "$root_source" in
  ""|none|tmpfs|overlay) fail "persistent boot/root disk not detected." ;;
  *) pass "persistent boot/root source is present: ${root_source}" ;;
esac

observed_hostname="$(hostname 2>/dev/null || true)"
if [[ "$observed_hostname" == "$expected_hostname" ]]; then
  pass "hostname matches approved manifest: ${observed_hostname}"
else
  fail "hostname mismatch; expected ${expected_hostname}, observed ${observed_hostname:-unknown}."
fi

clock_epoch="$(date +%s 2>/dev/null || true)"
if [[ "$clock_epoch" =~ ^[0-9]+$ ]] && ((clock_epoch >= MIN_CLOCK_EPOCH)); then
  pass "system clock passes TLS/SSH sanity threshold."
else
  fail "system clock is invalid for TLS/SSH; observed epoch ${clock_epoch:-unknown}."
fi
if has_command timedatectl; then
  ntp_sync="$(timedatectl show -p NTPSynchronized --value 2>/dev/null || true)"
  case "$ntp_sync" in
    yes) pass "time synchronization reports active." ;;
    no) fail "time synchronization reports inactive." ;;
    *) warn "time synchronization status unavailable; console evidence is required." ;;
  esac
else
  warn "timedatectl unavailable; console-side synchronization evidence is required."
fi

unexpected_listener=""
find_unexpected_listener() {
  awk '
    {
      endpoint = $4
      allowed_ssh = (endpoint ~ /:22$/)
      allowed_ipv4_loopback = (endpoint ~ /^127\.[0-9]+\.[0-9]+\.[0-9]+:[0-9]+$/)
      allowed_ipv6_loopback = (endpoint ~ /^\[::1\]:[0-9]+$/ ||
                               endpoint ~ /^::1:[0-9]+$/)
      if (!allowed_ssh && !allowed_ipv4_loopback && !allowed_ipv6_loopback) {
        print
        exit
      }
    }
  '
}
if has_command ss; then
  unexpected_listener="$(ss -H -ltnp 2>/dev/null | find_unexpected_listener)"
else
  warn "ss unavailable; kernel TCP tables are checked without process names."
  unexpected_listener="$(awk '
    function hexdec(value, result, i, digit) {
      result = 0
      for (i = 1; i <= length(value); i++) {
        digit = index("0123456789ABCDEF", toupper(substr(value, i, 1))) - 1
        if (digit < 0) return -1
        result = result * 16 + digit
      }
      return result
    }
    NR > 1 && $4 == "0A" {
      split($2, endpoint, ":")
      address = endpoint[1]
      port = hexdec(endpoint[2])
      loopback4 = (address == "0100007F")
      loopback6 = (length(address) == 32 && substr(address, 25, 8) == "01000000")
      allowed_local_dns = (port == 53 && (loopback4 || loopback6))
      if (port != 22 && !allowed_local_dns) { print; exit }
    }' /proc/net/tcp /proc/net/tcp6 2>/dev/null)"
fi
if [[ -n "$unexpected_listener" ]]; then
  fail "unexpected TCP listener: ${unexpected_listener}"
else
  pass "no unexpected TCP listener detected."
fi

process_snapshot="$(ps -eo comm=,args= 2>/dev/null || true)"
unexpected_process="$(printf '%s\n' "$process_snapshot" |
  awk '{
    line = tolower($0)
    if (line ~ /datahub|mcp[-_ ]?server|data_incident_commander|fastapi|uvicorn|vite|mysql|mariadb|kafka|opensearch|elasticsearch|dockerd|containerd/) {
      print
      exit
    }
  }')"
if [[ -n "$unexpected_process" ]]; then
  fail "unexpected application/runtime process: ${unexpected_process}"
else
  pass "no DataHub, MCP, application, database, Kafka, search, or Docker daemon process detected."
fi

if has_command docker || has_command dockerd || has_command containerd; then
  fail "Docker/container runtime executable unexpectedly installed before Gate 3."
else
  pass "Docker CLI, daemon, and container runtime executables are absent as required."
fi
if has_command systemctl && systemctl is-active --quiet docker 2>/dev/null; then
  fail "Docker daemon unexpectedly active before Gate 3."
else
  pass "Docker daemon is not detected as active."
fi

swap_kib="$(awk '/^SwapTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || true)"
if [[ "$swap_kib" =~ ^[0-9]+$ && "$swap_kib" -gt 0 ]]; then
  log "INFO: swap present (${swap_kib} KiB); Gate 3 must verify at least 2 GB."
else
  log "INFO: swap absent and accepted as deferred; Gate 3 must create and verify at least 2 GB before DataHub startup."
fi

if has_command ip; then
  interface_ipv4_output="$(ip -4 -o addr show scope global 2>/dev/null || true)"
else
  interface_ipv4_output=""
fi
if has_command ip; then
  public_guest_ipv4="$(printf '%s\n' "$interface_ipv4_output" |
    awk '
      NF {
        address = $4
        sub(/\/.*/, "", address)
        count = split(address, octet, ".")
        valid = (count == 4)
        for (i = 1; i <= count; i++) {
          if (octet[i] !~ /^[0-9]+$/ || octet[i] < 0 || octet[i] > 255) {
            valid = 0
          }
        }
        private = (valid &&
                   (octet[1] == 10 ||
                    (octet[1] == 172 && octet[2] >= 16 && octet[2] <= 31) ||
                    (octet[1] == 192 && octet[2] == 168)))
        if (!private) {
          print address
          exit
        }
      }
    ')"
  if [[ -n "$public_guest_ipv4" ]]; then
    fail "guest interface exposes a non-RFC1918 global IPv4 address."
  else
    pass "guest interfaces expose no detected public IPv4 address."
  fi
else
  warn "ip unavailable; guest-interface IPv4 evidence could not be collected."
fi
log "INFO: guest evidence cannot prove provider NAT/external-IP absence; console verification remains mandatory."
log "INFO: OS Login, IAP, IAM, and cloud firewall policy are console-side gates and are not inferred from the guest."

if ((failures)); then
  printf '[DataIncident Commander Gate 2] ERROR: %d blocking check(s) failed; %d warning(s).\n' "$failures" "$warnings" >&2
  exit 1
fi
log "PASS: Gate 2 base-host checks passed with ${warnings} warning(s)."
