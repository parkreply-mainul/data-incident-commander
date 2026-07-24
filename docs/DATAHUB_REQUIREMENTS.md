# DataHub Requirements Baseline

## Scope and evidence standard

This document records only facts supported by current official DataHub
documentation as reviewed on **2026-07-24**. It does not claim that this machine
has run DataHub or that a documented configuration is compatible with this
project until runtime validation succeeds.

Primary source: [DataHub Quickstart Guide](https://docs.datahub.com/docs/quickstart).

## Verified

### Supported quickstart operating-system families

The official quickstart prerequisite table provides installation guidance for:

- Windows, using Docker Desktop;
- macOS, using Docker Desktop; and
- Linux, using Docker for Linux and Docker Compose.

This verifies that macOS is an officially documented quickstart platform. It
does not, by itself, verify every macOS release or CPU architecture.

### Docker and Docker Compose

The official quickstart requires:

- Docker for the selected platform;
- Docker Compose v2; and
- a running Docker engine.

The `datahub docker quickstart` command deploys the local instance with a
downloaded Compose file.

### Python

The current quickstart requires Python **3.10 or newer** and states that the
DataHub CLI does not support Python 2.

### Tested resource configuration

The official quickstart identifies the following as a tested and confirmed
Docker allocation:

- 2 CPUs;
- 8 GB RAM;
- 2 GB swap; and
- 13 GB disk space.

The source does not label this configuration as a formal minimum or a
recommended production allocation. This project therefore records it only as
an official tested quickstart baseline.

### Official DataHub CLI installation methods

The quickstart documents two CLI installation methods:

- Homebrew: the `datahub-project/tap/datahub` formula; and
- pip: the `acryl-datahub` Python package.

The Homebrew formula manages an isolated Python environment. Sprint 4B instead
selected the documented pip method inside a repository-local virtual
environment and pinned `acryl-datahub==1.6.0`.

### Official quickstart workflow

The documented local quickstart sequence is:

1. install and launch Docker plus Docker Compose v2;
2. provide Python 3.10+;
3. install the DataHub CLI through Homebrew or pip;
4. verify the CLI with `datahub version`;
5. start the local stack with `datahub docker quickstart`;
6. verify the UI at `http://localhost:9002`; and
7. optionally initialize the CLI and load the experimental showcase data pack.

The quickstart documentation states that the local stack includes DataHub GMS,
the frontend, MySQL, OpenSearch, Kafka, and DataHub Actions. It also states that
quickstart is for local use and is not recommended as a production instance.

### Official deployment approaches

Official DataHub materials describe:

- DataHub Cloud as the managed deployment;
- Docker quickstart for local development and evaluation;
- Kubernetes with Helm for production self-hosted deployment; and
- running from source for contributors.

For this project, the documented target is the Docker quickstart local
deployment. Production deployment is outside the hackathon MVP.

## Needs runtime verification

- Successful execution of the selected DataHub release and every quickstart
  image on Apple Silicon. Sprint 4B registry-manifest inspection found arm64
  variants for all seven resolved images, but no image was pulled or run.
- Compatibility with macOS 26.5.2.
- Whether the current 8 GB host can allocate the documented 8 GB Docker
  baseline while keeping macOS stable.
- Exact usable Docker Desktop and Docker Engine versions.
- Exact usable Docker Compose v2 version.
- Whether swap behavior in Docker Desktop satisfies the documented baseline.
- Required free disk beyond the documented 13 GB quickstart baseline after
  images, volumes, sample data, logs, and project services are included.
- Successful image pulls and startup on arm64.
- Health of every quickstart service.
- UI accessibility at the documented local URL.
- GMS accessibility and authentication behavior.
- Compatibility of the NYC Taxi metadata loading approach.
- Shutdown, restart, backup, restore, and cleanup behavior for the selected
  release.

## Not established by official documentation reviewed

- A formal minimum-resource specification distinct from the tested baseline.
- A recommended-resource specification for this project’s combined DataHub,
  MCP, backend, and frontend stack.
- An explicit Apple Silicon support statement.
- Guaranteed support for this host’s exact macOS version.

## Safety gate

The isolated CLI installation is complete. DataHub startup must not occur
until:

1. the selected `v1.6.0` release and `acryl-datahub==1.6.0` pin remain
   acceptable;
2. the 8 GB tested Docker allocation is available or a separately documented,
   evidence-based exception is accepted;
3. the 8 GB physical-memory host is judged viable without weakening the
   official baseline;
4. rollback steps and project-only cleanup boundaries are reviewed;
5. a fresh `make check` passes required checks; and
6. first startup receives separate explicit authorization.
