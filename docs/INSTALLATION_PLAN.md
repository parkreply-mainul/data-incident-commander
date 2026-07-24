# Future Installation Plan

## Status and safety rules

This is a future checklist, not an installation script. No step has been
executed. Installation requires separate user authorization after official
version selection.

For every step:

- record the pre-change state;
- use only official installation sources;
- pin versions after validation;
- do not print or commit secrets;
- stop on failed verification;
- avoid deleting data not created by this project; and
- review rollback before making the change.

## 1. Docker

**Purpose:** Provide the container engine required by the official local
DataHub quickstart.

**Verification:**

- confirm supported macOS and Apple Silicon status from official sources;
- record Docker Desktop/Engine and Compose versions;
- verify the daemon is reachable without starting DataHub;
- allocate resources against the official tested baseline; and
- rerun `make check`.

**Rollback:** Use the selected runtime’s official macOS uninstall procedure
only with explicit approval. Preserve unrelated images, containers, volumes,
and settings.

**Failure handling:** Stop. Capture the non-secret error and architecture or
resource mismatch. Do not try alternative runtimes or privileged workarounds
without a documented decision.

## 2. Python environment

**Purpose:** Provide an isolated supported Python for project tooling and the
DataHub CLI path if pip is selected.

**Verification:**

- select Python 3.10+ based on DataHub quickstart requirements;
- verify executable path and version;
- verify environment isolation;
- verify pip belongs to that interpreter; and
- confirm the system Python remains untouched.

**Rollback:** Remove only the project-created environment after confirming its
exact path. Do not remove or modify macOS system Python.

**Failure handling:** Stop on interpreter, architecture, certificate, or pip
mismatch. Do not install into system Python as a fallback.

## 3. DataHub CLI

**Purpose:** Provide the official CLI used to run and manage local quickstart.

**Verification:**

- select Homebrew or pip from the official quickstart methods;
- pin and record the candidate CLI version;
- run the official version command;
- confirm command path and architecture; and
- confirm compatibility with the candidate DataHub release.

**Rollback:** Use the chosen package manager’s official removal method for only
the selected CLI installation. Preserve unrelated packages and environments.

**Failure handling:** Stop on dependency or version conflict. Do not mix
Homebrew and pip installations to bypass the failure.

## 4. DataHub OSS

**Purpose:** Start the pinned local DataHub quickstart stack for development and
verification.

**Verification:**

- inspect the pinned release’s Compose file before startup;
- record images, volumes, networks, and host port mappings;
- run the official quickstart only after approval;
- verify every reported service health state; and
- record actual versions and architecture.

**Rollback:** Use the official quickstart stop workflow first. Remove only
project-created containers, networks, or volumes with separate explicit
approval. Back up any state that must survive.

**Failure handling:** Stop and preserve diagnostic logs without secrets. Do not
run destructive reset or nuke commands. Classify image, architecture, port,
memory, disk, or health failure before retrying.

## 5. Health verification

**Purpose:** Prove that the actual DataHub services are reachable before sample
data or MCP work.

**Verification:**

- confirm the UI at the documented quickstart address;
- confirm the actual GMS endpoint;
- inspect container health without changing state;
- verify authentication with a test identity; and
- compare actual listeners with `PORT_MATRIX.md`.

**Rollback:** Health checks are read-only. If health is bad, use only the
approved official stop workflow; do not delete state.

**Failure handling:** Mark the environment unavailable and stop downstream
steps. Never substitute a fixture, screenshot, or mock response.

## 6. NYC Taxi dataset

**Purpose:** Load a synthetic, public-safe metadata graph for the planted
freshness incident.

**Verification:**

- validate source licensing and synthetic transformations;
- verify the official supported ingestion mechanism;
- observe actual asset URNs and metadata fields;
- verify upstream/downstream lineage, owners, derived assets, and quality or
  freshness representation; and
- record the graph without inventing identifiers.

**Rollback:** Remove only records created by the dedicated seed process through
a verified supported method. Prefer resetting an isolated disposable
quickstart instance rather than deleting individual unknown entities.

**Failure handling:** Stop if the ingestion mechanism, freshness evidence, or
lineage representation is unsupported. Revise the scenario documentation from
observed capability; do not hard-code expected success.

## 7. MCP Server

**Purpose:** Expose verified DataHub metadata operations to the future agent.

**Verification:**

- install the pinned self-hosted package through the official `uv`/`uvx` path;
- configure the verified GMS URL and a least-privilege test token;
- list the actual MCP tools and schemas;
- exercise read-only search, entity, lineage, ownership, and quality behavior;
- confirm failure behavior; and
- keep mutation tools disabled.

**Rollback:** Stop the MCP process, remove only its project-created isolated
environment or client configuration, and revoke the test token.

**Failure handling:** Mark unavailable tools accurately. Do not invent tools,
enable mutations, or substitute direct APIs during the read capability spike.

## 8. Backend

**Purpose:** Provide the future FastAPI/Pydantic application boundary after the
DataHub/MCP contracts are verified.

**Verification:**

- install only pinned project dependencies in an isolated environment;
- validate API contracts and configuration;
- verify disconnected behavior when DataHub/MCP is unavailable; and
- run backend tests without exposing secrets.

**Rollback:** Remove only the project environment and generated local state.
No DataHub state should be modified by backend setup.

**Failure handling:** Stop on dependency, contract, or health failure. Do not
fake MCP responses in the live runtime path.

## 9. Frontend

**Purpose:** Provide the future React/TypeScript/Vite desktop interface.

**Verification:**

- install only pinned dependencies after Node/npm selection;
- verify the selected project port is configurable and free;
- verify connection to the real backend;
- verify disconnected and partial states; and
- run accessibility and component checks.

**Rollback:** Remove only project-generated dependency and build artifacts
after confirming their repository-local paths.

**Failure handling:** Stop on lockfile, runtime, port, or backend-contract
failure. Do not replace live backend behavior with a screenshot-only demo.

## 10. Smoke tests

**Purpose:** Prove the complete environment performs real DataHub-backed work.

**Verification:**

- confirm all required health checks;
- resolve a known seeded asset through MCP;
- retrieve live upstream/downstream lineage and evidence;
- verify runtime provenance;
- confirm the UI shows actual backend state; and
- fail deliberately when DataHub or MCP is unavailable.

**Rollback:** Smoke tests are read-only until a separately approved write-back
phase. Stop project-managed services through the approved workflow.

**Failure handling:** Return non-zero, identify the failed dependency, preserve
safe diagnostics, and block the demo. Never report simulated success.

## Installation readiness gate

Installation is not authorized until the following are complete:

- official requirements and licenses reviewed;
- candidate versions recorded;
- Apple Silicon feasibility resolved;
- resource allocation accepted;
- ports reviewed;
- rollback approved;
- secrets strategy defined; and
- `make check` has no blocking failures.
