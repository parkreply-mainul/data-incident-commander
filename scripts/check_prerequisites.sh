#!/usr/bin/env bash

# Read-only macOS prerequisite inspection for DataIncident Commander.
# This script does not install software, start or stop services, modify
# configuration, inspect environment variables, or print credentials.

set -u
set -o pipefail

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'PASS [%s] %s\n' "$1" "$2"
}

warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  printf 'WARN [%s] %s\n' "$1" "$2"
}

fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  printf 'FAIL [%s] %s\n' "$1" "$2"
}

command_path() {
  command -v "$1" 2>/dev/null || true
}

# Sets PROBE_PATH and PROBE_OUTPUT only when an executable resolves, its version
# command succeeds, and the command returns at least one non-empty output line.
# Returns 1 when the executable is absent and 2 when it is present but unusable.
version_probe() {
  local command_name=$1
  local raw_output

  shift
  PROBE_PATH=$(command_path "$command_name")
  PROBE_OUTPUT=

  if [ -z "$PROBE_PATH" ]; then
    return 1
  fi

  if ! raw_output=$("$@" 2>&1); then
    return 2
  fi

  PROBE_OUTPUT=$(printf '%s\n' "$raw_output" | awk 'NF {print; exit}')
  if [ -z "$PROBE_OUTPUT" ]; then
    return 2
  fi

  return 0
}

printf '%s\n' 'DataIncident Commander — macOS prerequisite check'
printf '%s\n' 'Read-only: no installation, service startup, or configuration changes.'
printf '\n'

if command -v sw_vers >/dev/null 2>&1; then
  PRODUCT_NAME=$(sw_vers -productName 2>/dev/null || true)
  PRODUCT_VERSION=$(sw_vers -productVersion 2>/dev/null || true)
  BUILD_VERSION=$(sw_vers -buildVersion 2>/dev/null || true)
  if [ "$PRODUCT_NAME" = "macOS" ] && [ -n "$PRODUCT_VERSION" ]; then
    pass "required" "macOS detected: $PRODUCT_VERSION (build $BUILD_VERSION)."
  else
    fail "required" "This Sprint 2 checker supports macOS only. Run it on macOS."
  fi
else
  fail "required" "sw_vers is unavailable; this checker cannot verify macOS."
fi

ARCHITECTURE=$(uname -m 2>/dev/null || true)
if [ -n "$ARCHITECTURE" ]; then
  pass "required" "CPU architecture detected: $ARCHITECTURE."
else
  fail "required" "CPU architecture could not be detected with uname."
fi

DISK_LINE=$(df -Pk . 2>/dev/null | awk 'NR == 2 {print $2 " " $3 " " $4 " " $5 " " $6}')
if [ -n "$DISK_LINE" ]; then
  DISK_AVAILABLE_KB=$(printf '%s\n' "$DISK_LINE" | awk '{print $3}')
  DISK_AVAILABLE_GIB=$((DISK_AVAILABLE_KB / 1024 / 1024))
  if [ "$DISK_AVAILABLE_GIB" -ge 40 ]; then
    pass "required" "Repository volume has approximately ${DISK_AVAILABLE_GIB} GiB free."
  else
    warn "required" "Repository volume has approximately ${DISK_AVAILABLE_GIB} GiB free. Exact DataHub storage needs remain unverified; review official requirements before setup."
  fi
else
  fail "required" "Available disk space could not be read with df."
fi

MEMORY_BYTES=$(sysctl -n hw.memsize 2>/dev/null || true)
if [ -n "$MEMORY_BYTES" ] && [ "$MEMORY_BYTES" -gt 0 ] 2>/dev/null; then
  MEMORY_GIB=$((MEMORY_BYTES / 1024 / 1024 / 1024))
else
  MEMORY_GIB=$(system_profiler SPHardwareDataType 2>/dev/null |
    awk -F: '/^[[:space:]]*Memory:/ {gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2; exit}' |
    awk '{print $1}')
fi

if [ -n "${MEMORY_GIB:-}" ] && [ "$MEMORY_GIB" -gt 0 ] 2>/dev/null; then
  if [ "$MEMORY_GIB" -le 8 ]; then
    warn "required" "Physical memory detected: ${MEMORY_GIB} GB. This may be constrained for a local multi-service stack; verify official DataHub requirements before setup."
  else
    pass "required" "Physical memory detected: ${MEMORY_GIB} GB. Exact DataHub requirements remain unverified."
  fi
else
  warn "required" "Physical memory could not be determined. Verify it manually before setup."
fi

DOCKER_PATH=$(command_path docker)
if [ -n "$DOCKER_PATH" ]; then
  if version_probe docker docker --version; then
    DOCKER_PATH=$PROBE_PATH
    DOCKER_VERSION=$PROBE_OUTPUT
    pass "required" "Docker CLI detected at $DOCKER_PATH: $DOCKER_VERSION"
  else
    fail "required" "Docker resolves to $DOCKER_PATH, but its version probe failed or returned no output. Repair the Docker CLI before setup."
  fi

  if DOCKER_SERVER_VERSION=$(docker info --format '{{.ServerVersion}}' 2>/dev/null) &&
    [ -n "$DOCKER_SERVER_VERSION" ]; then
    pass "required" "Docker daemon is reachable (server $DOCKER_SERVER_VERSION)."
  else
    fail "required" "Docker daemon is not reachable. Start Docker Desktop manually before the future setup spike; this checker will not start it."
  fi

  if version_probe docker docker compose version; then
    COMPOSE_VERSION=$PROBE_OUTPUT
    pass "required" "Docker Compose detected: $COMPOSE_VERSION"
  else
    COMPOSE_PLUGIN_STATUS=$?
    if version_probe docker-compose docker-compose --version; then
      COMPOSE_VERSION=$PROBE_OUTPUT
      warn "required" "Legacy Docker Compose detected: $COMPOSE_VERSION. Verify whether the selected DataHub setup supports it."
    else
      COMPOSE_STANDALONE_STATUS=$?
      if [ "$COMPOSE_PLUGIN_STATUS" -eq 2 ] || [ "$COMPOSE_STANDALONE_STATUS" -eq 2 ]; then
        fail "required" "Docker Compose resolves, but its version probe failed or returned no output. Repair Compose before setup."
      else
        fail "required" "Docker Compose is unavailable. Install a compatible Docker Compose only after official requirements are verified."
      fi
    fi
  fi
else
  fail "required" "Docker CLI is unavailable. Install a compatible Docker Desktop/CLI only after official DataHub requirements are verified."
  fail "required" "Docker daemon availability cannot be checked without the Docker CLI."
  if version_probe docker-compose docker-compose --version; then
    COMPOSE_VERSION=$PROBE_OUTPUT
    warn "required" "Legacy standalone Docker Compose detected without the Docker CLI: $COMPOSE_VERSION. This is insufficient for the planned spike; verify the selected setup."
  else
    COMPOSE_STANDALONE_STATUS=$?
    if [ "$COMPOSE_STANDALONE_STATUS" -eq 2 ]; then
      fail "required" "Standalone docker-compose resolves, but its version probe failed or returned no output."
    else
      fail "required" "Neither the Docker Compose plugin nor standalone docker-compose is available."
    fi
  fi
fi

if [ -d /Applications/Docker.app ] || [ -d "$HOME/Applications/Docker.app" ]; then
  pass "optional" "Docker Desktop application bundle is present. Daemon reachability is checked separately."
else
  warn "optional" "Docker Desktop application bundle was not found in standard macOS application locations. A compatible alternative may be acceptable; verify official requirements before selecting a runtime."
fi

if version_probe python3 python3 --version; then
  PYTHON_PATH=$PROBE_PATH
  PYTHON_VERSION=$PROBE_OUTPUT
  pass "required" "Python detected at $PYTHON_PATH: $PYTHON_VERSION. Compatibility is not yet verified."
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    fail "required" "python3 is unavailable. Install a compatible Python only after the project version is selected."
  else
    fail "required" "python3 resolves to $PROBE_PATH, but its version probe failed or returned no output. Repair the Python executable before setup."
  fi
fi

if version_probe python python --version; then
  PYTHON_ALIAS_PATH=$PROBE_PATH
  PYTHON_ALIAS_VERSION=$PROBE_OUTPUT
  pass "optional" "python alias detected at $PYTHON_ALIAS_PATH: $PYTHON_ALIAS_VERSION"
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    warn "optional" "python alias is unavailable; use python3 unless the selected tooling documents another command."
  else
    warn "optional" "python alias resolves to $PROBE_PATH, but its version probe failed or returned no output. Use the verified python3 executable."
  fi
fi

if version_probe pip3 pip3 --version; then
  PIP_PATH=$PROBE_PATH
  PIP_VERSION=$PROBE_OUTPUT
  pass "required" "pip detected at $PIP_PATH: $PIP_VERSION"
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    fail "required" "pip3 is unavailable. Select a compatible Python toolchain before installation."
  else
    fail "required" "pip3 resolves to $PROBE_PATH, but its version probe failed or returned no output. Repair pip before setup."
  fi
fi

if version_probe pip pip --version; then
  PIP_ALIAS_PATH=$PROBE_PATH
  PIP_ALIAS_VERSION=$PROBE_OUTPUT
  pass "optional" "pip alias detected at $PIP_ALIAS_PATH: $PIP_ALIAS_VERSION"
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    warn "optional" "pip alias is unavailable; use pip3 unless the selected tooling documents another command."
  else
    warn "optional" "pip alias resolves to $PROBE_PATH, but its version probe failed or returned no output. Use the verified pip3 executable."
  fi
fi

if version_probe pipx pipx --version; then
  PIPX_PATH=$PROBE_PATH
  PIPX_VERSION=$PROBE_OUTPUT
  pass "optional" "pipx detected at $PIPX_PATH: $PIPX_VERSION"
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    warn "optional" "pipx is unavailable. It is not currently required; revisit after the MCP installation method is officially verified."
  else
    warn "optional" "pipx resolves to $PROBE_PATH, but its version probe failed or returned no output. Treat pipx as unusable."
  fi
fi

if version_probe node node --version; then
  NODE_PATH=$PROBE_PATH
  NODE_VERSION=$PROBE_OUTPUT
  pass "required" "Node.js detected at $NODE_PATH: $NODE_VERSION. Compatibility is not yet verified."
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    fail "required" "Node.js is unavailable. Install a compatible version only after the frontend version is selected."
  else
    fail "required" "Node.js resolves to $PROBE_PATH, but its version probe failed or returned no output. Repair Node.js before setup."
  fi
fi

if version_probe npm npm --version; then
  NPM_PATH=$PROBE_PATH
  NPM_VERSION=$PROBE_OUTPUT
  pass "required" "npm detected at $NPM_PATH: $NPM_VERSION. Compatibility is not yet verified."
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    fail "required" "npm is unavailable. Install it with the selected compatible Node.js toolchain."
  else
    fail "required" "npm resolves to $PROBE_PATH, but its version probe failed or returned no output. Repair npm before setup."
  fi
fi

for TOOL in git make curl; do
  if version_probe "$TOOL" "$TOOL" --version; then
    TOOL_PATH=$PROBE_PATH
    TOOL_VERSION=$PROBE_OUTPUT
    pass "required" "$TOOL detected at $TOOL_PATH: $TOOL_VERSION"
  else
    PROBE_STATUS=$?
    if [ "$PROBE_STATUS" -eq 1 ]; then
      fail "required" "$TOOL is unavailable. Provide it before running future project automation."
    else
      fail "required" "$TOOL resolves to $PROBE_PATH, but its version probe failed or returned no output. Repair it before running future project automation."
    fi
  fi
done

if version_probe java java -version; then
  JAVA_PATH=$PROBE_PATH
  JAVA_VERSION=$PROBE_OUTPUT
  pass "optional" "Java runtime detected at $JAVA_PATH: $JAVA_VERSION"
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    warn "optional" "Java runtime is not installed. Direct host Java requirements, if any, must be verified against official DataHub tooling documentation."
  else
    warn "optional" "Java resolves to $PROBE_PATH, but its version probe failed or returned no output. Treat the runtime as unusable until verified."
  fi
fi

if version_probe brew brew --version; then
  BREW_PATH=$PROBE_PATH
  BREW_VERSION=$PROBE_OUTPUT
  pass "optional" "Homebrew detected at $BREW_PATH: $BREW_VERSION"
else
  PROBE_STATUS=$?
  if [ "$PROBE_STATUS" -eq 1 ]; then
    warn "optional" "Homebrew is not installed. It is not required by this checker; future setup guidance must document any actual dependency."
  else
    warn "optional" "Homebrew resolves to $PROBE_PATH, but its version probe failed or returned no output. Treat Homebrew as unusable."
  fi
fi

printf '\n%s\n' 'Generic likely port checks (not confirmed DataHub requirements):'
if command -v lsof >/dev/null 2>&1; then
  for PORT in 3000 3306 5173 8000 8080 9002 9092 9200; do
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null | sed -n '2p' | grep -q .; then
      warn "optional" "TCP port $PORT is occupied. Do not stop its process; choose or configure ports after official requirements are verified."
    else
      pass "optional" "TCP port $PORT has no visible listener."
    fi
  done
else
  warn "optional" "lsof is unavailable, so generic candidate ports were not checked."
fi

printf '\n'
printf 'Summary: %s PASS, %s WARN, %s FAIL\n' "$PASS_COUNT" "$WARN_COUNT" "$FAIL_COUNT"
printf '%s\n' 'Exact DataHub, MCP, backend, and frontend versions and ports remain subject to official verification.'

if [ "$FAIL_COUNT" -gt 0 ]; then
  exit 1
fi

exit 0
