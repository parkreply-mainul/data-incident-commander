#!/usr/bin/env bash
set -Eeuo pipefail

readonly FIXTURE_DIR="$(mktemp -d)"
trap 'rm -rf "$FIXTURE_DIR"' EXIT

readonly INPUT="${FIXTURE_DIR}/fstab"
readonly FIRST_PASS="${FIXTURE_DIR}/fstab.first"
readonly SECOND_PASS="${FIXTURE_DIR}/fstab.second"
readonly DELETE_EXPRESSION='\|^/swapfile[[:space:]][[:space:]]*none[[:space:]][[:space:]]*swap[[:space:]]|d'

printf '%s\n' \
  'UUID=root / ext4 defaults 0 1' \
  '/swapfile none swap sw 0 0' \
  '/swapfile     none    swap    sw 0 0' \
  $'/swapfile\tnone\tswap\tsw 0 0' \
  '/other-swap none swap sw 0 0' \
  '/dev/sdb2 none swap sw 0 0' \
  >"$INPUT"

sed "$DELETE_EXPRESSION" "$INPUT" >"$FIRST_PASS"
sed "$DELETE_EXPRESSION" "$FIRST_PASS" >"$SECOND_PASS"

if grep -Eq '^/swapfile[[:space:]]+none[[:space:]]+swap[[:space:]]' "$FIRST_PASS"; then
  echo "FAIL: an intended /swapfile entry remains." >&2
  exit 1
fi
grep -Fxq '/other-swap none swap sw 0 0' "$FIRST_PASS"
grep -Fxq '/dev/sdb2 none swap sw 0 0' "$FIRST_PASS"
cmp -s "$FIRST_PASS" "$SECOND_PASS"

echo "Gate 3 swap rollback regex regression checks passed."
