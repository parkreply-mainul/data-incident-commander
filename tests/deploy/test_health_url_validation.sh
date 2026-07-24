#!/usr/bin/env bash
set -Eeuo pipefail

readonly TEST_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
readonly VALIDATOR="${TEST_ROOT}/deploy/scripts/validate_health_urls.py"
readonly VERIFIER="${TEST_ROOT}/deploy/scripts/verify_datahub.sh"
readonly TEST_TMP="$(mktemp -d)"
trap 'rm -rf -- "$TEST_TMP"' EXIT

validate() {
  local urls="$1" approved="${2:-}"
  printf '%s\n%s\n' "$urls" "$approved" | python3 "$VALIDATOR"
}

validate "http://localhost:8000/health"
validate "http://127.0.0.1:8000/health"
validate "http://[::1]:8000/health"
validate "http://10.0.0.10:8080/health" "10.0.0.10"
validate "https://[fc00::10]:8080/health" "fc00::10"
validate "http://localhost/health,http://127.0.0.1/health"

for rejected in \
  " http://localhost/health" \
  "http://localhost/health " \
  "http://localhost/health, http://127.0.0.1/health" \
  $'\thttp://localhost/health' \
  $'http://localhost/health\t' \
  $'\nhttp://localhost/health' \
  $'http://localhost/health\n' \
  "http://localhost/health,,http://127.0.0.1/health" \
  "http://10.0.0.11:8080/health" \
  "http://169.254.169.254/latest/meta-data" \
  "http://[fe80::1]/health" \
  "https://8.8.8.8/health" \
  "https://public.example.com/health" \
  "http://user:secret@localhost/health" \
  "http://localhost/health#fragment" \
  "ftp://localhost/health" \
  "http://[::1"; do
  if validate "$rejected" "10.0.0.10,fc00::10" >/dev/null 2>&1; then
    echo "Unsafe health URL unexpectedly passed: ${rejected}" >&2
    exit 1
  fi
done

fake_bin="${TEST_TMP}/bin"
curl_log="${TEST_TMP}/curl.log"
mkdir -p "$fake_bin"
cat >"${fake_bin}/curl" <<SCRIPT
#!/usr/bin/env bash
if env | grep -Eq '^(HTTP_PROXY|HTTPS_PROXY|ALL_PROXY|NO_PROXY|http_proxy|https_proxy|all_proxy|no_proxy)='; then
  echo "proxy variable reached curl" >&2
  exit 91
fi
no_proxy_argument=no
previous=""
for argument in "\$@"; do
  if [[ "\$previous" == "--noproxy" && "\$argument" == "*" ]]; then
    no_proxy_argument=yes
  fi
  previous="\$argument"
done
[[ "\$no_proxy_argument" == yes ]] || {
  echo "curl did not receive explicit --noproxy '*'" >&2
  exit 92
}
printf '%s\n' "\${@: -1}" >>"${curl_log}"
SCRIPT
chmod +x "${fake_bin}/curl"

run_probe_set() {
  local urls="$1" approved="$2"
  HTTP_PROXY=http://external-proxy.invalid:8080 \
  HTTPS_PROXY=http://external-proxy.invalid:8080 \
  ALL_PROXY=socks5://external-proxy.invalid:1080 \
  NO_PROXY=incorrect.invalid \
  http_proxy=http://external-proxy.invalid:8080 \
  https_proxy=http://external-proxy.invalid:8080 \
  all_proxy=socks5://external-proxy.invalid:1080 \
  no_proxy=incorrect.invalid \
  PATH="${fake_bin}:${PATH}" bash -c '
    source "$1"
    DIC_VERIFIED_HEALTH_URLS="$2"
    DIC_APPROVED_HEALTH_HOSTS="$3"
    verify_documented_health_urls
  ' test "$VERIFIER" "$urls" "$approved"
}

rm -f "$curl_log"
if run_probe_set \
  "http://localhost/health,https://public.example.com/health" \
  "" >/dev/null 2>&1; then
  echo "Mixed valid/invalid probe list unexpectedly passed." >&2
  exit 1
fi
[[ ! -e "$curl_log" ]]

if run_probe_set \
  "http://localhost/health, http://127.0.0.1/health" \
  "" >/dev/null 2>&1; then
  echo "Whitespace-padded probe list unexpectedly passed." >&2
  exit 1
fi
[[ ! -e "$curl_log" ]]

valid_urls="http://localhost/health,http://127.0.0.1/health,http://[::1]/health,http://10.0.0.10/health,https://[fc00::10]/health"
run_probe_set "$valid_urls" "10.0.0.10,fc00::10"
[[ "$(wc -l <"$curl_log" | tr -d ' ')" -eq 5 ]]
[[ "$(cat "$curl_log")" == "$(printf '%s' "$valid_urls" | tr ',' '\n')" ]]

echo "Private health URL validation regression checks passed."
