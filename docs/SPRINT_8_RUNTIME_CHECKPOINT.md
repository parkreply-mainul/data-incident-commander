# Sprint 8 Runtime Checkpoint

## Official source recheck

Reviewed **2026-07-24**:

- [DataHub v1.6.0 release](https://github.com/datahub-project/datahub/releases/tag/v1.6.0)
- [DataHub quickstart](https://docs.datahub.com/docs/quickstart), documenting
  `datahub docker quickstart --version v1.6.0` and a tested 2-CPU, 8-GB RAM,
  2-GB swap, 13-GB disk profile
- [DataHub MCP guide](https://docs.datahub.com/docs/features/feature-guides/mcp)
- [official MCP repository](https://github.com/acryldata/mcp-server-datahub)
- [Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/),
  documenting Ubuntu 24.04 LTS support and the official apt repository

Documentation facts are not runtime observations.

## Current NO-GO state

- No infrastructure has been provisioned or purchased.
- Google Cloud Gate 1 account and trial verification is complete, but no
  resource creation is authorized.
- No DataHub runtime has been started or images pulled.
- No MCP server has been installed or started.
- No MCP tool inventory has been observed.
- MCP capability verification and operational investigation readiness are
  separate gates; Sprint 8A implements no operational investigation path.
- The exact Compose service inventory and application/GMS/frontend health URLs
  remain runtime gates. Verification fails closed until they are recorded.
- Private non-loopback probe addresses additionally require exact canonical
  membership in the protected `DIC_APPROVED_HEALTH_HOSTS` allowlist. No URL is
  requested until the complete list validates.
- No mutation is enabled.
- No credentials, certificates, DNS records, or tokens exist in the repository.

Sprint 8B audited the official starter and did not change this NO-GO. The
starter uses Agent Context Kit directly rather than standalone MCP. The
selected primary remains the existing standalone-MCP path; Agent Context Kit is
only a conditional, separately approved write-back fallback. See
[RUNTIME_ARCHITECTURE_DECISION.md](RUNTIME_ARCHITECTURE_DECISION.md) and
[SPRINT_8C_LIVE_RUNTIME_PLAN.md](SPRINT_8C_LIVE_RUNTIME_PLAN.md).

Sprint 8C Gate 1 is complete. The active Google Cloud Free Trial has €256.52
remaining, paid conversion remains unaccepted, and the account exposes an
`e2-standard-4`, Ubuntu 24.04 LTS, and 100 GB Balanced Persistent Disk
candidate. No VM or infrastructure resource exists. OVHcloud Public Cloud
trial remains the free fallback, paid OVHcloud B3-16 remains the last resort,
and AWS is not recommended for the preferred runtime.

## Exact approval still required

Gate 1B is complete. Gate 2 separately requires approval of the current
itemized quote and tax, project identity, region/zone/SKU, quota, immutable
image, IAP/OS Login features, least-privilege IAM, effective firewall-policy
evidence, VM-scoped deny-all egress, disk, budget-monitoring owner, resource
names, teardown owner/schedule, rollback targets, and resource creation.
Later, separate approval is required before swap, Docker installation, image
pulls/DataHub startup, MCP installation, judge credentials, mutation
evaluation, and destructive teardown.

The prepared Gate 3 package, swap, transfer, Docker, and temporary outbound
network sequence is recorded in
`docs/SPRINT_8C_GATE_3_INSTALLATION_MANIFEST.md`. Its temporary ephemeral
external IPv4 permits no public ingress and does not authorize execution.

## Commands after approval

Only after a VM and private environment file exist:

```bash
make remote-check
make remote-plan REMOTE_ENV=/approved/path/remote.env
make remote-deploy REMOTE_ENV=/approved/path/remote.env
make remote-verify REMOTE_ENV=/approved/path/remote.env
```

`remote-deploy` still refuses startup until:

- Ubuntu 24.04 and 4-vCPU/16-GiB/50-GiB gates pass;
- Docker Engine/Compose and all required utilities are healthy;
- the v1.6.0 quickstart configuration is resolved and inspected;
- Compose project ownership, ports, volumes, tags, and architecture are
  verified;
- `DIC_REMOTE_APPROVED`, `DIC_REMOTE_EXECUTION_APPROVED`,
  `DIC_DATAHUB_START_APPROVED`, and
  `DIC_QUICKSTART_PROJECT_SCOPE_VERIFIED` are explicitly set in the protected
  runtime environment; and
- rollback and health timeout are confirmed.

## Rollback boundary

Automation may stop or inspect only resources proven to carry the unique
project label. Cleanup remains unimplemented until a real inventory exists and
requires separate exact confirmation. Provider deletion, Docker prune,
DataHub nuke, broad file deletion, and token rotation are never implicit.
