# macOS Environment Validation

## Scope

This document records the Sprint 2 read-only inspection and the separately
authorized Sprint 4A Docker Desktop installation and runtime validation on the
macOS host planned for future DataHub OSS, DataHub MCP Server, FastAPI,
React/Vite, and one-command demo work. Sprint 4A installed and started Docker
Desktop only. It did not install or start DataHub or any project dependency,
and Docker presence alone does not establish DataHub compatibility.

Inspection date: **2026-07-24**

Repository command: `make check`

## Current findings

| Area | Observed result | Assessment |
| --- | --- | --- |
| Operating system | macOS 26.5.2, build 25F84 | Detected; exact support remains unverified |
| CPU | Apple M1, arm64, 8 cores | Detected; architecture compatibility remains unverified |
| Physical memory | 8 GB | Warning: potentially constrained for a local multi-service stack |
| Repository volume | 228 GiB total; approximately 102 GiB available by the checker's integer calculation (`df -h` displayed 103 GiB); 51% used | No immediate storage warning |
| Docker CLI | `/usr/local/bin/docker`, 29.6.2, native `darwin/arm64` | Installed from the Docker Desktop bundle and executable |
| Docker Desktop | `/Applications/Docker.app`, 4.83.0 (build 234302) | Installed through the official Homebrew cask; observed running during Sprint 4A |
| Docker daemon | Docker Engine 29.6.2, `linux/arm64` (`aarch64` reported by `docker info`) | Observed reachable through the `desktop-linux` context during Sprint 4A |
| Docker Compose | Docker Compose v5.3.1 | Installed and executable |
| System Python | `/usr/bin/python3`, Python 3.9.6 | Present and unchanged; not used for the DataHub CLI |
| Isolated CLI Python | `/opt/homebrew/opt/python@3.11/bin/python3.11`, Python 3.11.15 | Installed in Sprint 4B; `.venv` uses it |
| `python` alias | Not found | Optional; use `python3` unless verified tooling requires otherwise |
| pip | `/usr/bin/pip3`, pip 21.2.4 for Python 3.9 | Present; project compatibility unverified |
| `pip` alias | Not found | Optional; use `pip3` unless verified tooling requires otherwise |
| pipx | Not found | Optional until the verified MCP installation approach requires it |
| Node.js | `/opt/homebrew/bin/node`, v25.9.0 | Present; project compatibility unverified |
| npm | `/opt/homebrew/bin/npm`, 11.12.1 | Present; project compatibility unverified |
| Git | `/usr/bin/git`, 2.50.1 (Apple Git-155) | Present |
| Make | `/usr/bin/make`, GNU Make 3.81 | Present |
| curl | `/usr/bin/curl`, 8.7.1 | Present |
| Java | macOS launcher exists, but no Java runtime is installed | Optional pending official tooling verification |
| Homebrew | `/opt/homebrew/bin/brew`, 6.0.12 | Present; used for the authorized Docker Desktop cask installation |

These findings describe the current host only. They do not select supported
versions for the project.

## Generic likely port observations

The following TCP ports had no visible listening process during the inspection:

```text
3000
3306
5173
8000
8080
9002
9092
9200
```

These are generic candidates commonly encountered across local web, data, and
development stacks. They are **not** asserted as required DataHub, MCP,
backend, or frontend ports. The checker does not stop any listener. If a
candidate port is occupied, it emits a warning so later setup can select or
configure a non-conflicting port.

## Sprint 4A Docker Desktop validation

Installation command:

```bash
brew install --cask docker
```

Homebrew installed its official `docker-desktop` cask. The first invocation
updated Homebrew metadata and its portable Ruby before installing Docker
Desktop 4.83.0 (build 234302). Homebrew requested macOS administrator
authentication to create command-line links. The unattended prompt was
cancelled without supplying credentials; Docker Desktop's normal first-run flow
subsequently created the links after the user completed its interactive setup.
No password or credential was handled by the project.

Observed runtime state during the Sprint 4A validation session:

- Docker Desktop status: `running`;
- Docker client: 29.6.2, `darwin/arm64`;
- Docker Engine: 29.6.2, `linux/arm64`;
- Docker Compose: v5.3.1;
- active context: `desktop-linux`;
- daemon architecture: `aarch64`;
- daemon allocation reported by `docker info`: 8 CPUs and 4,108,632,064 bytes
  (approximately 3.83 GiB) memory;
- storage driver: `overlayfs`;
- containers, images, volumes, and build cache: none;
- networks: only Docker's expected `bridge`, `host`, and `none` defaults;
- Kubernetes: disabled and stopped;
- Docker disk usage: 0 B for images, containers, volumes, and build cache; and
- no new TCP listeners were observed compared with the pre-install inspection.

Docker Desktop's settings store contained no explicit CPU, memory, disk-size,
swap, VMM, or Rosetta override keys. Therefore the 8-CPU and approximately
3.83-GiB values above are runtime observations, while the disk limit, VMM,
Rosetta integration, and other implicit defaults remain unverified.

A follow-up read-only inspection found `EnableDockerAI=true` in Docker
Desktop's settings store and a bundled `docker-agent serve api` background
process. The flag is therefore not documented as merely inert: Docker's
AI-assistant infrastructure is enabled at the Desktop level. This does not
mean an AI workload or MCP integration was configured or used. The same
inspection found:

- Docker Model Runner stopped;
- no Docker containers or local models;
- Docker MCP Toolkit CLI present as part of the Desktop distribution, but no
  MCP profiles;
- detected MCP clients disconnected or unconfigured; and
- Kubernetes disabled and stopped.

The user independently confirmed that they did not enable Docker AI, Docker MCP
Toolkit, Kubernetes, or another optional feature during setup. The observed
Desktop-level AI flag and background service therefore appear to be installation
defaults rather than user opt-in. Docker's public documentation describes
Gordon (`docker ai`), Model Runner, and MCP Toolkit as separate capabilities,
but the reviewed documentation does not define the internal
`EnableDockerAI` settings-store key. Sprint 4A did not invoke an AI assistant,
start Model Runner or an MCP gateway, connect an MCP client, or change any
Docker setting.

No Docker workload was started, and no image was pulled. This validates a
working Apple Silicon Docker runtime only; it does **not** establish that the
host resources or installed versions are compatible with DataHub.

## Blockers

There is no Docker or isolated CLI installation blocker. DataHub startup is
currently blocked because Docker exposes approximately 3.83 GiB while official
quickstart documentation records a tested 8 GB Docker allocation. This 8 GB
physical-memory host cannot provide the full baseline without leaving
effectively no memory for macOS.

## Warnings

- The host has 8 GB of physical memory. A multi-service local stack may be
  constrained; official DataHub resource requirements and a practical startup
  measurement are still required.
- During the Sprint 4A validation session, the daemon received approximately
  3.83 GiB of the host's 8 GB memory. Whether this is sufficient for DataHub is
  not established.
- Docker Desktop's internal `EnableDockerAI=true` default starts bundled
  AI-assistant infrastructure even though the user did not opt in. No AI model,
  MCP profile, connected MCP client, or AI/MCP container is active. Treat the
  distinction as a transparency warning; no setting was changed.
- Python 3.9.6 is present, but backend and DataHub tooling compatibility is
  unverified.
- Node.js 25.9.0 and npm 11.12.1 are present, but Vite/frontend compatibility
  is unverified.
- pipx is absent; whether it is useful or required depends on the verified MCP
  distribution and installation method.
- No Java runtime is installed; whether host Java is relevant depends on the
  selected official DataHub workflow.

## Read-only checker behavior

`scripts/check_prerequisites.sh`:

- is scoped to macOS for Sprint 2;
- uses only discovery and status commands;
- never installs or modifies software;
- never starts or stops processes, containers, or services;
- never prints environment variables or credentials;
- labels each result `PASS`, `WARN`, or `FAIL`;
- identifies required versus optional checks;
- tolerates absent optional commands;
- treats generic port occupancy as a warning;
- returns non-zero only when blocking required checks fail; and
- states that exact compatibility and port requirements remain unverified.

Run it directly or through Make:

```bash
scripts/check_prerequisites.sh
make check
```

Environment validation must precede installation. A successful check means
only that the documented prerequisites are present; it does not prove DataHub
compatibility or startup success.

## Resource recommendations for this 8 GB M1 host

These are conservative project recommendations, **not verified DataHub
requirements**:

- retain the observed approximately 4 GiB Docker memory allocation for
  non-DataHub validation rather than consuming nearly all host memory;
- do not increase Docker's allocation or start DataHub until the selected
  DataHub release's requirements are reconciled with an 8 GB host;
- retain the current CPU allocation for now because no workload has been
  benchmark-tested, and change it only if the DataHub spike justifies it;
- keep Kubernetes disabled;
- keep disk, networking, Rosetta, and VMM settings unchanged until the selected
  images and official workflow are known; and
- prefer a higher-memory host if the verified DataHub baseline cannot leave
  adequate memory for macOS.

## Items requiring official or runtime verification

Before any installation or startup:

- minimum and recommended CPU, memory, and disk resources;
- compatibility of Docker Desktop 4.83.0, Engine 29.6.2, and Compose v5.3.1
  with the selected DataHub release;
- supported Python and pip versions;
- supported Node.js and npm versions for the selected Vite toolchain;
- DataHub MCP Server distribution, runtime, and installation method;
- whether host Java is required by any selected tooling;
- exact DataHub service and exposed ports;
- MCP bind address and port;
- FastAPI backend bind address and port;
- Vite development and preview ports; and
- port override and collision behavior for the one-command demo.

## Readiness assessment

Readiness has three separate meanings:

- **Installation readiness:** Docker Desktop installation and the isolated
  Python 3.11/DataHub CLI setup are valid. Stopping Docker Desktop does not
  invalidate their installed versions or the historical arm64 evidence.
- **Generic prerequisite readiness:** `make check` verifies command
  availability, generic host prerequisites, candidate port availability, and
  time-bound Docker daemon reachability. It does not evaluate or override
  DataHub-specific resource feasibility.
- **DataHub startup feasibility:** Local DataHub startup on this host is
  **NOT CURRENTLY FEASIBLE** under the documented tested 8 GB Docker
  allocation. Docker exposes approximately 3.83 GiB on a host with only 8 GB
  physical memory.

A fresh successful `make check` remains necessary immediately before any
container work, but it is not sufficient authorization or evidence to start
DataHub. Startup remains blocked until a different runtime strategy or newly
verified resource evidence resolves the memory issue and separate startup
authorization is granted.

## Sprint 4B pre-start observation

During the Sprint 4B session, with Docker Desktop running, a fresh
`make check` completed with 23 PASS, 5 WARN, and 0 FAIL. This confirms
time-bound daemon reachability and prerequisite presence only.

Homebrew Python 3.11.15 and an ignored `.venv` were added for the isolated
DataHub CLI. The virtual environment reports pip 26.1.2 and DataHub CLI 1.6.0.
Neither system Python nor the Homebrew Python global site-packages contains
`acryl-datahub`.

The passing result preserves the generic prerequisite observation; it does not
change the **NOT CURRENTLY FEASIBLE** DataHub startup verdict above. No DataHub
image was pulled and no DataHub service was started.

## Rollback guidance

Use Docker's official Docker Desktop uninstall workflow only with separate
explicit approval. Docker documents the application uninstaller at
`/Applications/Docker.app/Contents/MacOS/uninstall`; uninstalling removes local
Docker containers, images, volumes, and other Docker data. Inspect and preserve
any unrelated Docker state before a future uninstall. Homebrew cask removal
must likewise be separately approved. Sprint 4A did not uninstall, delete,
prune, or reset anything.
