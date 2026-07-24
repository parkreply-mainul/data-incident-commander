# Version Matrix

## Status

This matrix separates versions stated by official DataHub documentation from
versions that still require selection and runtime validation. No package or
service version has been installed for this project.

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
| Docker | Requires verification | Requires verification | Requirement only | Docker is required by quickstart, but no exact engine/Desktop version is stated in the reviewed quickstart. |
| Docker Compose | v2 | Requires verification | Official docs | Quickstart explicitly requires Compose v2; an exact minor version is not stated. |
| DataHub OSS | Requires verification | Requires verification | Current docs are 1.6.0 | The current documentation site is versioned 1.6.0 and quickstart shows `v1.6.0` as a pinning example. The project has not selected or run it. |
| DataHub CLI | Requires verification | Requires verification | Install method only | Official methods are Homebrew and the `acryl-datahub` pip package. Pin must be chosen with the OSS release. |
| MCP Server | Requires verification | Requires verification | Partial | Official docs state mutation tools require self-hosted server v0.5.0+, but this does not establish the minimum for read-only project needs. |
| FastAPI | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| React | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| TypeScript | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |
| Vite | Requires verification | Requires verification | No | Project dependency; not constrained by reviewed DataHub docs. |

## Host comparison

The Sprint 2 host inspection found:

- Python 3.9.6: below the official quickstart requirement of Python 3.10+;
- Node.js 25.9.0 and npm 11.12.1: present, compatibility unknown;
- Docker and Docker Compose: absent; and
- macOS on Apple M1: architecture compatibility requires runtime verification.

See [ENVIRONMENT_VALIDATION.md](ENVIRONMENT_VALIDATION.md).

## Pinning rule

Before installation, record an explicit candidate version for every installed
component, its official source, architecture support evidence, license, and
compatibility relationship. Do not use `latest` in reproducible automation
after the capability spike.
