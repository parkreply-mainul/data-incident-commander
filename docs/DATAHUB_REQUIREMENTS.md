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

The Homebrew formula manages an isolated Python environment. No installation
method has yet been selected for DataIncident Commander.

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

- Apple Silicon compatibility for the selected DataHub release and every
  quickstart image.
- Compatibility with macOS 26.5.2.
- Whether the current 8 GB host can allocate the documented 8 GB Docker
  baseline while keeping macOS stable.
- Exact usable Docker Desktop and Docker Engine versions.
- Exact usable Docker Compose v2 version.
- Whether swap behavior in Docker Desktop satisfies the documented baseline.
- Required free disk beyond the documented 13 GB quickstart baseline after
  images, volumes, sample data, logs, and project services are included.
- The DataHub CLI version that should be pinned.
- The DataHub OSS release that should be pinned.
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

No installation or startup should occur until:

1. the version matrix has candidate pins;
2. Docker licensing and resource allocation are accepted by the user;
3. rollback steps are reviewed;
4. the prerequisite checker passes required checks; and
5. runtime validation is authorized as a separate sprint action.
