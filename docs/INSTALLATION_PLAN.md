# Future Installation Plan

## Status and safety rules

This is a staged checklist, not an installation script.

**Completed preparation:**

- Docker Desktop installation and basic runtime validation;
- isolated Homebrew Python 3.11 environment;
- repository-local ignored `.venv`;
- pinned `acryl-datahub==1.6.0` CLI installation and version validation; and
- pre-start Compose, image-manifest, and port inspection.

**Still pending:**

- DataHub image pulls;
- first DataHub startup;
- runtime health verification;
- NYC Taxi ingestion;
- MCP installation and capability inspection;
- backend and frontend setup; and
- smoke tests.

The Docker step remains partially complete because its DataHub memory
feasibility gate is unresolved. Completed preparation does not verify
CLI/server compatibility and must not be interpreted as authorization to pull
or start DataHub. All pending work requires its applicable gates and separate
authorization.

Sprint 4C selected a fully remote single Linux VM as the primary future demo
runtime and a hybrid remote-DataHub/MCP topology as backup. No infrastructure
has been provisioned. The local DataHub startup remains blocked, and the remote
plan begins with separate budget and provisioning approval. See
[RUNTIME_STRATEGY.md](RUNTIME_STRATEGY.md) and
[REMOTE_DEPLOYMENT_PLAN.md](REMOTE_DEPLOYMENT_PLAN.md).

For every step:

- record the pre-change state;
- use only official installation sources;
- pin versions after validation;
- do not print or commit secrets;
- stop on failed verification;
- avoid deleting data not created by this project; and
- review rollback before making the change.

## 1. Docker

**Status: Partially complete.** Installation, basic runtime validation, pinned
configuration inspection, and registry-manifest architecture checks completed.
The memory feasibility gate remains unresolved. This step is not complete and
does not authorize DataHub startup.

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

**Completed in Sprint 4A (2026-07-24):**

- installed the official Homebrew `docker-desktop` cask with
  `brew install --cask docker`;
- made the Docker CLI available;
- observed Docker Engine responsive during the validation session;
- made Docker Compose available;
- observed native arm64 client and server architecture during the validation
  session;
- recorded Docker Desktop 4.83.0 (build 234302), CLI/Engine 29.6.2, and Compose
  v5.3.1;
- observed 8 CPUs and approximately 3.83 GiB daemon memory;
- verified no containers, images, or volumes were created and Kubernetes is
  disabled;
- did not change Docker CPU, memory, disk, networking, Rosetta, or VMM settings.

**Still pending before DataHub startup:**

- prove runtime compatibility with pinned DataHub `v1.6.0`;
- run all required images on Apple Silicon; registry manifests advertise arm64
  variants, but this is not runtime proof;
- reconcile the host's approximately 3.83 GiB Docker memory allocation with
  DataHub's documented tested 8 GiB allocation;
- determine whether this 8 GB host is viable; and
- perform a fresh successful `make check`.

Until every pending gate is satisfied and startup is separately authorized,
later phases must not interpret Sprint 4A installation evidence as permission
or readiness to start DataHub.

Follow-up read-only verification established that the internal
`EnableDockerAI=true` value is not merely an inert stored flag: Docker Desktop
runs its bundled `docker-agent serve api` background process. It remains an
installation default rather than a recorded user opt-in. Model Runner is
stopped, no MCP profiles or connected MCP clients exist, no AI/MCP container is
running, and Kubernetes is disabled. Sprint 4A did not invoke, configure, or
alter any AI or MCP feature. The reviewed public Docker documentation does not
define the internal settings-store key, so documentation should describe the
observed states rather than equate that key with a configured AI workload.

**Rollback clarification:** Docker's official application uninstaller is
`/Applications/Docker.app/Contents/MacOS/uninstall`. Its use is destructive to
local Docker data and therefore requires separate approval after inspecting
and preserving unrelated state. A Homebrew cask uninstall likewise requires
separate approval.

## 2. Python environment

**Status: Completed.** The isolated CLI Python environment was completed in
Sprint 4B. This does not select
the future backend interpreter or dependencies.

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

**Sprint 4B result:** Installed Homebrew Python 3.11.15, created ignored
repository-local `.venv`, and verified pip 26.1.2. `/usr/bin/python3` remains
3.9.6. Homebrew installed `mpdecimal` and refreshed the Python formula's
required `ca-certificates`, `openssl@3`, and `sqlite` dependencies.

## 3. DataHub CLI

**Status: Completed.** Isolated CLI installation and version validation are
complete. CLI/server compatibility remains unverified until an authorized
runtime test.

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

**Sprint 4B result:** Installed exact `acryl-datahub==1.6.0` only inside
`.venv`. It reports DataHub CLI 1.6.0 on Python 3.11.15. System Python and the
Homebrew Python global site-packages do not contain `acryl-datahub`. The pin
matches the selected OSS `v1.6.0` release train; actual interoperability
remains unverified.

## 4. DataHub OSS

**Status: Blocked.** DataHub OSS is selected and inspected, but not installed
or started. Local startup is blocked by the **NOT CURRENTLY FEASIBLE** memory
verdict. The selected remote strategy is blocked on budget, provider,
provisioning, security, and separate startup approvals.

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

**Sprint 4B pre-start result:** Selected `v1.6.0`. The pinned CLI exposes no
documented dry-run/config-only quickstart option, so `quickstart` was not
invoked. The exact official Compose file selected by the CLI was instead
downloaded to temporary storage and resolved with `docker compose config`.
Expected inventory: 7 services, 7 images, 3 named volumes, 4 health checks, and
6 distinct published host ports. All seven image manifests advertise arm64;
no image layer was pulled.

Planned startup command, only after every gate and separate approval:

```bash
DATAHUB_TELEMETRY_ENABLED=false .venv/bin/datahub docker quickstart \
  --version v1.6.0 --arch arm64
```

Planned first rollback is the CLI's official stop workflow. The exact stop
command and generated Compose path must be captured during startup. Removing
project-created volumes, networks, images, or local quickstart state is a
separate destructive action requiring explicit approval; never use prune or
an unrestricted cleanup command.

## 5. Health verification

**Status: Pending.** Requires an authorized, successful DataHub startup.

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

**Status: Pending.** Requires successful DataHub runtime health verification.

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

**Status: Pending.** No MCP package or capability has been installed or
runtime-inspected.

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

**Status: Pending.** No backend environment or application dependency has been
installed.

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

**Status: Pending.** No frontend environment or application dependency has
been installed.

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

**Status: Pending.** Requires the verified DataHub, MCP, backend, and frontend
runtime path.

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
- Docker has the documented tested 8 GB allocation, or an evidence-based
  exception is explicitly accepted without misrepresenting official guidance;
- viability of this 8 GB physical-memory host is resolved;
- ports reviewed;
- rollback approved;
- secrets strategy defined; and
- `make check` has no blocking failures.
