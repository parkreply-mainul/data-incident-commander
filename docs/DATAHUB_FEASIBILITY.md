# DataHub OSS Feasibility

## Decision

**Verdict: NOT CURRENTLY FEASIBLE**

DataHub OSS `v1.6.0` and `acryl-datahub==1.6.0` are selected, the CLI is
isolated and working, and every resolved image manifest advertises arm64.
Nevertheless, first startup remains blocked: official quickstart documentation
records a tested Docker allocation of 8 GB RAM, while Docker currently exposes
approximately 3.83 GiB on a host with only 8 GB physical memory.

This sprint did not pull an image layer, create a container, or start DataHub.

## Evidence and official sources

Reviewed on **2026-07-24**:

- [DataHub Quickstart Guide](https://docs.datahub.com/docs/quickstart)
- [DataHub GitHub releases](https://github.com/datahub-project/datahub/releases)
- [DataHub v1.6.0 quickstart profile](https://github.com/datahub-project/datahub/blob/v1.6.0/docker/quickstart/docker-compose.quickstart-profile.yml)
- [acryl-datahub on PyPI](https://pypi.org/project/acryl-datahub/)

GitHub's latest-release API returned stable, non-prerelease `v1.6.0`, published
2026-05-21. PyPI provides exact stable `acryl-datahub==1.6.0` and declares
Python 3.10 or newer. Later `1.6.0.x` CLI patch builds exist; the exact 1.6.0
pin was chosen as a transparent release-train match, not as proof of runtime
interoperability.

## Host profile

| Item | Observed value |
| --- | --- |
| Host | Apple M1 MacBook Air, arm64, 8 CPU cores |
| macOS | 26.5.2, build 25F84 |
| Physical memory | 8 GB |
| Available repository-volume space | Approximately 99 GiB during Sprint 4B |
| Docker Desktop | 4.83.0, build 234302 |
| Docker CLI / Engine | 29.6.2 / 29.6.2 |
| Docker Compose | v5.3.1 |
| Docker memory | 4,108,632,064 bytes, approximately 3.83 GiB |
| System Python | 3.9.6, unchanged |
| Isolated Python | Homebrew Python 3.11.15 |
| Virtual environment | Repository-local ignored `.venv` |
| DataHub CLI | `acryl-datahub==1.6.0` |

During Sprint 4B, with Docker Desktop running, `make check` reported 23 PASS,
5 WARN, and 0 FAIL. This is time-bound evidence, not a permanent readiness
guarantee.

## Selected release and rationale

- **DataHub OSS:** `v1.6.0`, observed as the latest stable GitHub release.
- **DataHub CLI:** exact `acryl-datahub==1.6.0`, available from PyPI, requiring
  Python 3.10+, and aligned by release train with the selected OSS version.
- **Python:** 3.11.15, satisfying the documented Python 3.10+ requirement
  without modifying macOS system Python.

The CLI reports version 1.6.0. Its installed source resolves an explicit
`v1.6.0` request to the official file
`docker/quickstart/docker-compose.quickstart-profile.yml` and Docker tag
`v1.6.0`. Actual CLI/server compatibility remains unverified until startup.

## Official resource baseline versus host

The quickstart documents a tested and confirmed Docker allocation of 2 CPUs,
8 GB RAM, 2 GB swap, and 13 GB disk. It does not label this as a formal minimum.
The project will not weaken or silently reinterpret that evidence.

Docker currently exposes 8 CPUs and approximately 3.83 GiB RAM. The memory
allocation is less than half the documented tested baseline. Because the host
itself has only 8 GB, assigning the full baseline would leave effectively no
memory for macOS and is not considered safe without stronger evidence or a
higher-memory host.

The Compose profile also declares JVM heaps of 1 GiB for GMS, 512 MiB for the
frontend, 512 MiB for Kafka, and up to 1 GiB for OpenSearch, before MySQL,
Actions, upgrade work, container overhead, Docker, and macOS are counted. The
Compose file does not declare per-service platform values or general memory
limits.

## Service and image inventory

The exact v1.6.0 quickstart profile was downloaded to temporary storage and
resolved with `DATAHUB_VERSION=v1.6.0 docker compose ... config`. The CLI
itself was not asked to quickstart because it exposes no documented
config-only/dry-run mode.

| Service | Resolved image | Registry manifest architectures | Published host ports | Health check |
| --- | --- | --- | --- | --- |
| `kafka-broker` | `confluentinc/cp-kafka:8.0.0` | amd64, arm64 | 9092 | Yes |
| `mysql` | `mysql:8.2` | amd64, arm64/v8 | 3306 | Yes |
| `opensearch` | `opensearchproject/opensearch:2.19.3` | amd64, arm64 | 9200 | Yes |
| `system-update-quickstart` | `acryldata/datahub-upgrade:v1.6.0` | amd64, arm64 | None | No |
| `datahub-gms-quickstart` | `acryldata/datahub-gms:v1.6.0` | amd64, arm64 | 8080, 4319 | Yes |
| `datahub-actions-quickstart` | `acryldata/datahub-actions:v1.6.0-slim` | amd64, arm64 | None | No |
| `frontend-quickstart` | `acryldata/datahub-frontend-react:v1.6.0` | amd64, arm64 | 9002 | No |

No image appears amd64-only from manifest inspection. Registry metadata is not
proof that an image will start or remain healthy on this host.

The profile resolves:

- 7 services;
- 7 images;
- 3 named volumes: `broker`, `mysqldata`, and `osdata`;
- 4 health checks; and
- 6 distinct published host ports: 3306, 4319, 8080, 9002, 9092, and 9200.

## Unresolved risks

- Docker memory is approximately 3.83 GiB versus the documented tested 8 GB.
- An 8 GB physical-memory host may be intrinsically unsuitable for the tested
  local configuration.
- No image has been pulled or executed on arm64.
- Docker Desktop, Engine, and Compose compatibility with v1.6.0 remains
  unproven.
- The exact stable CLI/OSS pair is release-train aligned but not runtime-tested.
- Swap and disk allocation settings remain unverified.
- Port 4319 is not yet covered by `make check`; all published ports need a
  fresh collision check.
- Actual startup service count, health, memory pressure, and listener behavior
  are unknown.
- Quickstart creates local secrets and state under the user's DataHub
  directory during startup; their exact paths and lifecycle must be captured
  without exposing secret values.

## Exact pre-start checklist

1. Obtain explicit authorization for first DataHub startup.
2. Resolve the memory gate without weakening the official tested baseline,
   preferably by using a host that can safely allocate 8 GB to Docker.
3. Confirm Docker Desktop is running.
4. Run a fresh `make check` and require zero blocking failures.
5. Check all declared host ports, including 4319, for collisions.
6. Confirm Kubernetes, Model Runner, and Docker MCP Toolkit remain unused.
7. Confirm no unrelated Docker container, image, volume, or network will be
   altered.
8. Reconfirm the selected `v1.6.0` release and CLI pin.
9. Reinspect the official pinned Compose checksum and resolved image list.
10. Record baseline Docker state and host memory pressure.
11. Review startup, stop, and project-only cleanup commands.
12. Define bounded startup timeout and abort thresholds for memory pressure.

## Go/no-go criteria for first startup

**GO** requires all of the following:

- separate explicit startup authorization;
- a fresh passing `make check`;
- no published-port collision;
- a safe resolution of the 8 GB Docker allocation baseline;
- adequate host memory headroom;
- unchanged pinned release and image inventory;
- reviewed rollback commands and exact project-state boundaries; and
- no need to enable Kubernetes, MCP, mutation tools, or Docker AI features.

**NO-GO** applies if any criterion is missing. The current decision is NO-GO
because the Docker memory and host-viability criteria are unresolved.

## Planned startup and rollback

Planned startup, not authorized:

```bash
DATAHUB_TELEMETRY_ENABLED=false .venv/bin/datahub docker quickstart \
  --version v1.6.0 --arch arm64
```

The first rollback action will be the pinned CLI's official stop workflow,
using the exact generated Compose file recorded during startup. It must stop
only the `datahub` quickstart project.

Cleanup boundaries:

- never prune Docker;
- never remove unrelated containers, images, volumes, or networks;
- never delete DataHub state as part of ordinary stop;
- inspect generated state and identifiers before any cleanup;
- require separate explicit approval before removing project-created volumes,
  networks, images, secrets, or local quickstart files; and
- preserve diagnostics without credential or token values.
