# Version Matrix

## Status

This matrix separates versions stated by official DataHub documentation from
versions that still require selection and runtime validation. Sprint 4B
selected the DataHub OSS and CLI pins and installed only the CLI in an ignored
repository-local virtual environment. DataHub OSS has not been pulled or run.

Reviewed on **2026-07-24** against:

- [DataHub Quickstart Guide](https://docs.datahub.com/docs/quickstart)
- [DataHub MCP Server guide](https://docs.datahub.com/docs/features/feature-guides/mcp)
- [Official DataHub releases](https://github.com/datahub-project/datahub/releases)

“Verified” means the value is present in official documentation, not that it
has run successfully on this host.

| Component | Minimum | Recommended | Verified? | Notes |
| --- | --- | --- | --- | --- |
| Python | 3.10 | 3.11 for the isolated CLI | Official docs and local runtime | Current quickstart requires Python 3.10+. Homebrew Python 3.11.15 is installed for `.venv`; macOS `/usr/bin/python3` remains 3.9.6 and unchanged. |
| Node.js | Requires verification | Requires verification | No | Project frontend and self-hosted MCP version requirements must be selected. Official self-hosted MCP instructions use `uvx`, not Node.js. |
| npm | Requires verification | Requires verification | No | Must match the selected Node.js and Vite toolchain. |
| Docker | Requires verification | Requires verification | Runtime only | Docker Desktop 4.83.0 (build 234302), CLI 29.6.2, and Engine 29.6.2 were observed working on arm64 during validation sessions. DataHub compatibility remains unverified because the quickstart does not state an exact engine/Desktop version. |
| Docker Compose | v2 | Requires verification | Official docs and runtime | Quickstart explicitly requires Compose v2; installed Compose is v5.3.1. Compatibility with the selected DataHub release remains unverified. |
| DataHub OSS | v1.6.0 selected | v1.6.0 selected | Official release metadata | GitHub reports v1.6.0 as the latest stable release. It is selected but has not been pulled or run. |
| DataHub CLI | 1.6.0 selected | 1.6.0 selected | PyPI and local runtime | Exact stable `acryl-datahub==1.6.0` exists, requires Python 3.10+, matches the OSS release train, and reports CLI 1.6.0 from `.venv`. Runtime server compatibility remains unproven until startup. |
| MCP Server | Requires verification | Requires verification | Partial | Official docs state mutation tools require self-hosted server v0.5.0+, but this does not establish the minimum for read-only project needs. |
| FastAPI | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| React | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| TypeScript | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| Vite | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |

## Runtime host selection

Sprint 4C selected a future remote Linux VM baseline of at least 4 vCPU,
16 GB RAM, and 50 GB SSD for evaluation. This is a project safety margin, not
an official DataHub minimum or a provisioned resource. Linux distribution,
architecture, provider, Docker Engine/Compose pins, and actual full-stack
capacity remain unverified. DataHub OSS and CLI pins remain `v1.6.0` and
`1.6.0`; no version changed in Sprint 4C.

## Host observations by sprint

### Sprint 2 host inspection

- Python 3.9.6: below the official quickstart requirement of Python 3.10+;
- Node.js 25.9.0 and npm 11.12.1: present, compatibility unknown;
- Docker CLI, Docker Desktop, and Docker Compose: absent; and
- macOS on Apple M1: detected, but Docker architecture could not yet be
  runtime-verified.

### Sprint 4A runtime validation

During the Sprint 4A validation session, with Docker Desktop running:

- Docker Desktop 4.83.0 (build 234302), Docker CLI/Engine 29.6.2, and Compose
  v5.3.1 were installed and observed;
- Docker client and server architecture were observed as arm64; and
- the Docker daemon was reachable through the `desktop-linux` context.

These are installed-version and time-bound runtime observations, not a claim
that the daemon is permanently running. Compatibility with the selected
DataHub release and its images remains unverified.

See [ENVIRONMENT_VALIDATION.md](ENVIRONMENT_VALIDATION.md).

### Sprint 4B selection and isolated CLI validation

- selected DataHub OSS `v1.6.0`, the latest stable GitHub release observed on
  2026-07-24;
- selected exact stable `acryl-datahub==1.6.0` because PyPI publishes that
  release-train match and declares Python 3.10+;
- installed Homebrew Python 3.11.15 without replacing system Python;
- created ignored repository-local `.venv`;
- verified pip 26.1.2 and DataHub CLI 1.6.0 from `.venv`; and
- confirmed the CLI was not installed into system Python or the Homebrew
  interpreter's global site-packages.

The exact pin is defensible but actual CLI/server interoperability is still a
runtime question. Newer `1.6.0.x` CLI patch releases exist, but Sprint 4B did
not silently substitute one for the exact OSS release-train pin.

## Pinning rule

Before installation, record an explicit candidate version for every installed
component, its official source, architecture support evidence, license, and
compatibility relationship. Do not use `latest` in reproducible automation
after the capability spike.
