# Runtime Strategy

## Decision

**Primary strategy:** one remote Linux VM hosting the complete demo runtime:
DataHub OSS `v1.6.0`, DataHub MCP Server, FastAPI backend, and React frontend.

**Backup strategy:** hybrid development mode with DataHub OSS and MCP on the
remote VM while the backend and frontend run locally.

**Provider decision:** Sprint 4D selects OVHcloud B3-16 in Gravelines as the
provisional primary and Hetzner CCX23 in Nuremberg as provider backup. Region,
capacity, all-in quote, tax, and account approval remain go/no-go gates. See
[INFRASTRUCTURE_DECISION.md](INFRASTRUCTURE_DECISION.md).

Neither strategy is provisioned or authorized for execution. The primary
strategy is selected because it is the smallest topology that satisfies the
DataHub OSS requirement while giving judges one stable public application URL
without depending on the 8 GB Mac, a home network, or a live developer laptop.
The backup reduces remote application setup during development but is not the
preferred judging topology.

Research access date: **2026-07-24**

## Evidence standard

### Verified

- The hackathon requires a working application incorporating the open-source
  DataHub platform together with at least one approved agent technology,
  including MCP Server.
- The “Agents That Do Real Work” category expects the agent to read DataHub,
  take action, and contribute results back where appropriate.
- Judges require easy access through a project URL, hosted application, or
  clear repository setup instructions.
- DataHub quickstart requires Docker, Docker Compose v2, Python 3.10+, and a
  running Docker engine.
- DataHub documents a tested quickstart allocation of 2 CPUs, 8 GB RAM, 2 GB
  swap, and 13 GB disk.
- Quickstart is intended for development/evaluation, not production. Its
  defaults expose ports broadly and include development credentials.
- Official DataHub deployment alternatives include Docker quickstart,
  production Docker/Helm deployment, Kubernetes, running from source, and
  DataHub Cloud.

Sources:

- [Hackathon rules](https://datahub.devpost.com/rules)
- [Hackathon overview](https://datahub.devpost.com/)
- [DataHub quickstart](https://docs.datahub.com/docs/quickstart)
- [DataHub deployment overview](https://docs.datahub.com/)
- [DataHub AWS/EKS guide](https://docs.datahub.com/docs/deploy/aws)

### Estimates and assumptions

- The remote planning baseline of 4 vCPU, 16 GB RAM, and 50 GB SSD is a
  project safety margin, not an official DataHub minimum.
- A single adequately sized VM should be simpler and cheaper for this
  temporary demo than Kubernetes or separate managed data services.
- Actual resource consumption, startup time, MCP transport, and full-stack
  reliability remain runtime questions.
- Hackathon rules establish technology and accessibility requirements but do
  not explicitly approve a specific cloud provider or say that DataHub Cloud
  alone substitutes for DataHub OSS.

## Comparison matrix

| Strategy | Compliance | Reliability | Cost/setup | Connectivity | Decision |
| --- | --- | --- | --- | --- | --- |
| A. Remote Linux VM, DataHub OSS | Strong OSS fit; MCP still must be included | High if sized, secured, and monitored | Moderate; one VM | Requires secure app/MCP placement decision | Viable foundation |
| B. Local Mac with reduced resources | Uses OSS, but violates the current feasibility gate | Low; memory pressure and unsupported reduction | No cloud cost; high failure risk | Simple local path | Rejected |
| C. Remote DataHub OSS/MCP, local backend/frontend | Strong technology fit | Good for development; weaker for judging because the Mac and cross-network path must stay available | Moderate | Requires secure remote-to-local or local-to-remote connectivity | Selected backup |
| D. Fully remote DataHub OSS/MCP/backend/frontend | Strongest end-to-end OSS and MCP fit | Best judging reliability and public accessibility on one host | Moderate; most remote setup | Internal service network plus one public app boundary | Selected primary |
| E. Managed/cloud DataHub only | Compliance uncertain; must not be assumed to satisfy OSS | Potentially high | Price and access uncertain | Provider-dependent | Secondary contingency only |
| F1. Official remote quickstart on adequate Linux | Uses OSS; temporary development/demo use | Reasonable after hardening and runtime proof | Lowest official self-hosted complexity | Single-host internal path | Basis of primary |
| F2. Official Helm/Kubernetes deployment | Uses OSS | Potentially high after expert setup | High time, cost, and operational complexity | Strong service isolation possible | Rejected for MVP |
| F3. Run DataHub from source | Uses OSS | Adds build and contributor-tooling risk | High setup time | Single or multi-host | Rejected for MVP |

## Criteria assessment

### Primary: fully remote single VM

- **Hackathon/DataHub OSS:** preserves pinned DataHub OSS and required MCP path.
- **Reliability:** removes dependence on local Mac memory and availability.
- **Baseline:** evaluate Linux x86_64 or arm64, at least 4 vCPU, 16 GB RAM,
  50 GB SSD, Docker Engine, and Compose v2.
- **Apple Silicon:** no runtime dependence on the Mac; x86_64 is acceptable if
  every selected image manifest supports it.
- **Setup:** one host and one Docker network; no Kubernetes.
- **Public access:** only the application HTTPS boundary is intended to be
  public. Easy-access judging URL still requires rule and security validation.
- **Security:** DataHub stores, GMS, MCP, backend administration, and Docker
  socket stay private; SSH is restricted.
- **Connectivity:** co-location minimizes DataHub/MCP/backend latency. Frontend
  reaches only the application API boundary.
- **Reproducibility:** pinned versions, documented host baseline, modular
  scripts, backups, and health gates.
- **Rollback:** stop the project, preserve an approved backup, then delete the
  VM and rotate credentials after judging.
- **One-command potential:** strongest topology for a future remote
  `make demo`, once provisioning and secrets are separate from application
  startup.

### Backup: hybrid

Remote DataHub OSS and MCP remain authoritative. The local backend/frontend
connect to an authenticated private or tunneled MCP/application boundary.
This is suitable for development when public judging access is not required.
It is not the judging default because laptop sleep, IP changes, tunnels, and
home-network outages add failure modes.

## Operational and compliance risks

- Quickstart defaults are unsafe for direct internet exposure.
- A single VM is a single point of failure.
- Remote quickstart is still a development deployment, not production.
- Provider account limits, region capacity, IP behavior, and billing require
  verification before provisioning.
- MCP installation, transport, authentication, and mutation inventory remain
  unverified.
- Public demo authentication and judge access must balance ease of testing with
  protection of mutation capabilities.
- Managed DataHub cannot be represented as satisfying the OSS requirement
  without written rule confirmation.
- A live URL may be required throughout judging; the exact availability window
  and whether judges need credentials remain unresolved.

## Explicit rejection reasons

- **Reduced-resource local Mac:** rejected because 3.83 GiB is below the
  documented tested 8 GB Docker allocation and the host cannot safely provide
  the full baseline.
- **Kubernetes/EKS:** rejected for the MVP because official AWS guidance uses a
  multi-node cluster and adds Helm, IAM, ingress, certificate, load-balancer,
  and storage complexity.
- **Run from source:** rejected because it expands build/runtime scope without
  improving judging reliability.
- **Managed-only:** rejected as primary because DataHub OSS use cannot be
  inferred.
- **Hybrid for judging:** rejected as primary because it depends on local
  availability and additional secure connectivity.

## Go/no-go criteria

**GO for provisioning research to become an action** requires:

- explicit user approval and maximum budget acceptance;
- confirmation that the provider/region offers the selected size and public
  access behavior;
- a verified Linux distribution and architecture;
- a documented firewall and SSH recovery path;
- a credential, DNS/TLS, backup, and deletion plan;
- reconfirmation of current hackathon rules; and
- no need to expose Docker, GMS, databases, or MCP directly.

**GO for first remote DataHub startup** additionally requires:

- successful remote prerequisite checks;
- at least the selected 4 vCPU/16 GB/50 GB baseline;
- pinned Docker/Compose and DataHub versions;
- verified free ports and private bindings;
- reviewed startup timeout and rollback;
- captured baseline billing/resource identifiers; and
- separate explicit startup authorization.

Until then, the decision is **NO-GO for provisioning and startup**. Sprint 4D
research did not create an account, authorize payment, or provision anything.
