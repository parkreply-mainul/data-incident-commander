# Version Matrix

## Status

This matrix separates versions stated by official DataHub documentation from
versions that still require selection and runtime validation. Sprint 4A
installed Docker Desktop only; no DataHub or application package has been
installed.

Reviewed on **2026-07-24** against:

- [DataHub Quickstart Guide](https://docs.datahub.com/docs/quickstart)
- [DataHub MCP Server guide](https://docs.datahub.com/docs/features/feature-guides/mcp)
- [Official DataHub releases](https://github.com/datahub-project/datahub/releases)

“Verified” means the value is present in official documentation, not that it
has run successfully on this host.

| Component | Minimum | Recommended | Verified? | Notes |
| --- | --- | --- | --- | --- |
| Python | 3.10 | Requires verification | Official docs | Current quickstart requires Python 3.10+. Host Python 3.9.6 does not meet that documented requirement. |
| Node.js | Requires verification | Requires verification | No | Project frontend and self-hosted MCP version requirements must be selected. Official self-hosted MCP instructions use `uvx`, not Node.js. |
| npm | Requires verification | Requires verification | No | Must match the selected Node.js and Vite toolchain. |
| Docker | Requires verification | Requires verification | Runtime only | Docker Desktop 4.83.0 (build 234302), CLI 29.6.2, and Engine 29.6.2 are installed and working on arm64. DataHub compatibility remains unverified because the quickstart does not state an exact engine/Desktop version. |
| Docker Compose | v2 | Requires verification | Official docs and runtime | Quickstart explicitly requires Compose v2; installed Compose is v5.3.1. Compatibility with the selected DataHub release remains unverified. |
| DataHub OSS | Requires verification | Requires verification | Current docs are 1.6.0 | The current documentation site is versioned 1.6.0 and quickstart shows `v1.6.0` as a pinning example. The project has not selected or run it. |
| DataHub CLI | Requires verification | Requires verification | Install method only | Official methods are Homebrew and the `acryl-datahub` pip package. Pin must be chosen with the OSS release. |
| MCP Server | Requires verification | Requires verification | Partial | Official docs state mutation tools require self-hosted server v0.5.0+, but this does not establish the minimum for read-only project needs. |
| FastAPI | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| React | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| TypeScript | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| Vite | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |

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

## Pinning rule

Before installation, record an explicit candidate version for every installed
component, its official source, architecture support evidence, license, and
compatibility relationship. Do not use `latest` in reproducible automation
after the capability spike.
