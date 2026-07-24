#!/usr/bin/env bash
set -Eeuo pipefail

readonly TEST_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$TEST_ROOT"

example="deploy/env/remote.env.example"
real_environment="deploy/env/remote.env"

[[ -f "$example" ]]
if git check-ignore --quiet "$example"; then
  echo "The public remote environment example must not be ignored." >&2
  exit 1
fi
git check-ignore --quiet "$real_environment"
git status --short --untracked-files=all -- "$example" | grep -q 'remote.env.example'

echo "Deployment environment ignore-policy regression checks passed."
