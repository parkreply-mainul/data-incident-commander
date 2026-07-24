# macOS Environment Validation

## Scope

This document records a read-only Sprint 2 inspection of the macOS host planned
for future DataHub OSS, DataHub MCP Server, FastAPI, React/Vite, and one-command
demo work. No packages were installed, no container or application service was
started or stopped, and no compatibility claim is made from tool presence
alone.

Inspection date: **2026-07-24**

Repository command: `make check`

## Current findings

| Area | Observed result | Assessment |
| --- | --- | --- |
| Operating system | macOS 26.5.2, build 25F84 | Detected; exact support remains unverified |
| CPU | Apple M1, arm64, 8 cores | Detected; architecture compatibility remains unverified |
| Physical memory | 8 GB | Warning: potentially constrained for a local multi-service stack |
| Repository volume | 228 GiB total; approximately 102 GiB available by the checker's integer calculation (`df -h` displayed 103 GiB); 51% used | No immediate storage warning |
| Docker CLI | Not found | Blocking for the planned container-based setup spike |
| Docker Desktop | Application bundle not found in standard system or user application locations | Warning; a compatible alternative runtime may be acceptable |
| Docker daemon | Could not be checked because the Docker CLI is absent | Blocking |
| Docker Compose | Not found | Blocking for the planned container-based setup spike |
| Python | `/usr/bin/python3`, Python 3.9.6 | Present; project compatibility unverified |
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
| Homebrew | `/opt/homebrew/bin/brew`, 6.0.11 | Present; not used by this sprint |

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

## Blockers

The planned local container-based DataHub OSS setup spike cannot proceed on
this host until a compatible container environment is selected and made
available:

- Docker CLI is absent.
- Docker daemon reachability cannot be established.
- Docker Compose is absent.

This document does not authorize installation. Compatible products and versions
must first be checked against official DataHub requirements and project
licensing or hackathon constraints.

## Warnings

- The host has 8 GB of physical memory. A multi-service local stack may be
  constrained; official DataHub resource requirements and a practical startup
  measurement are still required.
- Docker Desktop is absent. A compatible alternative container runtime may be
  acceptable, but no Docker CLI or reachable daemon is currently available.
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

## Items requiring official verification

Before any installation or startup:

- supported macOS and Apple Silicon status;
- minimum and recommended CPU, memory, and disk resources;
- supported Docker Desktop or alternative container runtime versions;
- required Docker Compose form and version;
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

The machine is **not yet ready** for the next container-based DataHub OSS setup
spike because the Docker CLI, daemon access, and Compose are unavailable.
The machine otherwise has the basic source-development commands and substantial
free disk space. Readiness should be reassessed with `make check` after official
requirements are reviewed and the user separately authorizes any necessary
installation.
