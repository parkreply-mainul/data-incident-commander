# Remote Deployment Plan

## Status

This is a future execution plan for the selected fully remote single-VM
strategy. Sprint 8A adds provider-neutral dry-run and fail-closed artifacts
under `deploy/`. No infrastructure, DNS, certificate, firewall, repository
checkout, Docker installation, image pull, or service startup has occurred.

Commands appear only where current official documentation verifies their
meaning. Provider resource IDs, regions, image slugs, DNS names, usernames,
package versions, and secrets remain placeholders until a provisioning sprint
verifies them.

## 1. Approval and provider selection

**Status: Blocked.**

- treat OVHcloud B3-16 in Gravelines as the provisional primary and Hetzner
  CCX23 in Nuremberg as the backup;
- obtain explicit account, payment, provisioning, and budget approval;
- recheck hackathon rules, provider price, region capacity, and account limits;
- select Linux architecture and a supported distribution;
- select at least 4 vCPU, 16 GB RAM, and 50 GB SSD;
- record every billable resource and deletion owner; and
- define judging and teardown dates.

No provider command is documented yet. The planning selections are not verified
account/region resource identifiers, and no credential path or all-in quote has
been approved.

## 2. Network boundary before compute

- create a default-deny cloud firewall;
- restrict SSH to approved administrator sources or a verified console path;
- reserve public HTTPS only for the future application;
- do not expose DataHub, MCP, database, Kafka, or Docker ports;
- document outbound requirements; and
- verify recovery access before disabling password authentication.

Provider firewall behavior and the interaction with Docker-published ports must
be tested before DataHub startup.

## 3. Provision the VM

- use a current provider-supported Linux image;
- attach only the dedicated SSH public key;
- enable provider monitoring without application-secret capture;
- apply the firewall by immutable resource ID or verified tag;
- record VM, disk, firewall, IP, and region identifiers; and
- verify CPU, RAM, disk, architecture, clock, and package-source state.

## 4. Harden administrative access

- verify the host key;
- create a named administrator;
- confirm `sudo` and recovery-console access;
- disable password and routine root SSH only after recovery is proven;
- apply security updates with a documented reboot decision; and
- retain no cloud API token on the VM unless required.

## 5. Install Docker Engine and Compose

Use Docker's official distribution-specific repository instructions:
[Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

The official package set is:

```text
docker-ce
docker-ce-cli
containerd.io
docker-buildx-plugin
docker-compose-plugin
```

Before installation, list available versions and pin the selected compatible
Docker Engine/CLI packages. Verify:

```bash
sudo systemctl status docker
sudo docker version
sudo docker info
sudo docker compose version
```

The official guide proposes `docker run hello-world`, which pulls an image.
Whether to perform that probe must be explicitly approved in the provisioning
sprint. Docker group membership is optional and root-equivalent; do not grant
it casually.

## 6. Repository access

Because this repository is public, use an HTTPS read-only clone after verifying
the final repository URL and commit hash. Do not place a GitHub token on the
host. Check out the exact reviewed commit in detached or deployment-controlled
state and verify:

```bash
git status --short
git rev-parse HEAD
```

If the repository later becomes private, use a dedicated read-only deploy key
only after approval and plan its revocation.

## 7. Install the isolated DataHub CLI

- install an official Python 3.10+ package without replacing system tooling;
- create a deployment-local virtual environment;
- install exact `acryl-datahub==1.6.0`;
- verify Python, pip, CLI path, and `datahub version`;
- disable telemetry for project commands where supported; and
- confirm no global Python installation.

Exact Linux Python commands depend on the selected distribution and are
deferred until its official package versions are verified.

## 8. Pre-start inspection

- download the exact official `v1.6.0` quickstart profile;
- verify its checksum against the reviewed source;
- resolve it with `docker compose config` without pulling;
- verify all image tags and architecture manifests;
- confirm at least 8 GB remains available to the Docker workload;
- check disk and swap;
- verify ports 3306, 4319, 8080, 9002, 9092, and 9200 are not publicly
  exposed;
- record pre-start processes, listeners, Docker objects, and memory; and
- review stop, backup, and cleanup boundaries.

## 9. DataHub startup

**Requires a separate explicit checkpoint.**

The official pinned quickstart form is:

```bash
DATAHUB_TELEMETRY_ENABLED=false .venv/bin/datahub docker quickstart \
  --version v1.6.0
```

Do not run it until resource, binding, secret, rollback, and authorization gates
pass. Apply a bounded startup timeout and stop on memory pressure, unexpected
public listeners, architecture failure, or unhealthy prerequisites.

## 10. Health verification

- record the exact runtime-observed Compose service inventory before
  verification;
- compare the complete sorted project service-label inventory exactly and fail
  on missing, unexpected, duplicate, orphaned, or unlabelled containers;
- require each expected project-labelled container to exist and run;
- wait while a Docker health check is `starting`, require `healthy`, and fail
  on unhealthy or non-running states;
- fail closed for containers without Docker health checks until a verified
  service-level probe is configured;
- verify runtime-observed application/GMS/frontend health URLs through intended
  private paths without credentials in URLs;
- validate every URL before any request: loopback is implicit, while RFC1918
  and IPv6 ULA literals require exact membership in the protected approved-host
  allowlist; reject public, link-local/metadata, special, malformed, or
  unapproved destinations;
- do not treat container health alone as complete DataHub readiness;
- record actual versions, listeners, memory, disk, and restart behavior;
- verify no unrelated Docker object exists or was altered; and
- retain redacted diagnostics.

## 11. Secure connectivity

- place MCP and backend on the same private host/network as DataHub where
  supported;
- keep GMS and MCP private;
- terminate public TLS at a verified reverse proxy;
- expose only the application URL on 443;
- enforce application authentication and bounded requests;
- verify browser-to-backend and backend-to-MCP failure behavior; and
- do not enable mutation until the separate MCP capability/approval sprint.

Exact MCP transport and port remain unknown until the tool inventory is
verified.

## 12. Application deployment

- install pinned backend/frontend dependencies only in their project scopes;
- bind internal services privately;
- validate health and disconnected states;
- load only the approved synthetic NYC Taxi scenario;
- run read-only smoke tests first; and
- enable a mutation path only after human approval and read-back controls pass.

## 13. Shutdown and restart

Official DataHub quickstart stop command:

```bash
.venv/bin/datahub docker quickstart --stop
```

Stopping containers is not deletion. Before a judging restart, record state,
start through the pinned workflow, and rerun full health and smoke checks.
Provider power-off does not necessarily stop billing.

## 14. Backup

Official quickstart backup form:

```bash
.venv/bin/datahub docker quickstart --backup --backup-file <approved-path>
```

DataHub documents that this backup covers MySQL metadata but not timeseries
data. Store backups encrypted with restricted access, test restoration in a
separate approved exercise, and never commit them.

## 15. Judging-period availability

- freeze versions and configuration before judging;
- retain the primary runtime continuously for the confirmed judging window;
- run scheduled external health checks without secrets;
- keep a redacted runbook and backup strategy;
- avoid upgrades and discretionary changes;
- maintain a tested recovery path; and
- retain until the winner-announcement buffer date approved in the lifecycle
  plan.

The current planning window is 2026-08-07 through 2026-09-09. See
[JUDGING_AVAILABILITY_PLAN.md](JUDGING_AVAILABILITY_PLAN.md). Whether judges may
receive test credentials still requires organizer clarification.

## 16. Cleanup and rollback

Normal rollback order:

1. block new judge sessions;
2. stop application mutation;
3. take an approved backup;
4. stop project services;
5. capture redacted diagnostics;
6. revoke runtime tokens;
7. destroy the VM and every separately billed project resource after explicit
   approval; and
8. verify billing and DNS cleanup.

Never run Docker prune, DataHub `nuke`, recursive deletion, or broad provider
deletion as an implicit rollback. Destructive cleanup requires resolved
resource identifiers and separate approval.

## Sprint 8A automation boundary

`make remote-check` performs local shell syntax, help-contract, proxy-template,
and secret-placeholder checks. `make remote-plan` prints host, Docker, and
DataHub actions without changing state. Execution targets require a
noncommitted environment, approval variables, Ubuntu 24.04, and project gates.

DataHub startup stops at an implementation gate until an approved remote host
can resolve the official v1.6.0 configuration and prove Compose project
ownership. Stop, restart, and cleanup remain blocked rather than guessing
unsafe commands.
