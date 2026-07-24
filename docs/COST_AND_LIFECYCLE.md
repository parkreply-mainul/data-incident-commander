# Cost and Lifecycle

## Scope and source date

This is a planning estimate, not a purchase authorization or provider
commitment. Prices and limits were accessed on **2026-07-24** and may change by
region, tax status, account, currency, capacity, or provider policy.

Primary price reference:
[DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets).

Billing and storage references:

- [Droplet billing](https://docs.digitalocean.com/products/droplets/details/pricing/)
- [Snapshot pricing](https://docs.digitalocean.com/products/snapshots/details/)

## Reference runtime

A DigitalOcean General Purpose Droplet matching the project planning baseline
was listed at:

| Resource | Published specification | Published price |
| --- | --- | ---: |
| General Purpose Droplet | 4 vCPU, 16 GiB RAM, 50 GiB SSD, 5,000 GiB transfer | $0.1875/hour or $126/month |
| Droplet snapshot | Charged by stored size | $0.06/GB-month |
| Cloud firewall | No additional charge | $0 |

This plan is used because it exactly matches 4 vCPU, 16 GiB, and 50 GiB.
DigitalOcean also lists cheaper shared-CPU or differently balanced plans, but
their reliability/performance tradeoffs have not been runtime-tested for
DataHub.

## Development and judging assumptions

- Development planning starts 2026-07-24.
- Submission deadline is 2026-08-10.
- Official judging period is 2026-08-17 through 2026-08-31.
- Winners are expected around 2026-09-08.
- The primary demo should remain available through an approved buffer after
  the winner announcement, tentatively 2026-09-09.
- Active development compute is estimated at 80–160 hours before judging.
- Judging/retention availability is estimated at 24 continuous days
  (576 hours) from 2026-08-17 through 2026-09-09.

These dates come from the hackathon rules; actual provisioning dates and judge
access expectations remain assumptions.

## Estimated cost

At $0.1875/hour:

- 80–160 development hours: **$15–$30**;
- 576 judging/retention hours: **$108**;
- compute subtotal with destroy/recreate lifecycle: approximately
  **$123–$138**;
- optional snapshot, conservatively assuming all 50 GB are billable for one
  month: up to **$3**; and
- expected project range: approximately **$125–$145**, before tax, DNS,
  unexpected egress, backups, or provider changes.

Keeping the same VM continuously for roughly 47 days would produce a raw hourly
estimate near **$211.50** before provider monthly caps. A conservative
continuous-retention planning range is therefore **$190–$215**, plus ancillary
charges.

The project maximum budget guardrail is **$250 total** through teardown. This
is a proposed guardrail, not approval to spend. Stop and request direction if
forecasted cost could exceed it.

## Storage and network considerations

- The reference VM includes 50 GiB SSD and 5,000 GiB transfer.
- DigitalOcean states inbound transfer is free and outbound over the team
  allowance is $0.01/GiB.
- Public image pulls, package downloads, browser traffic, backups, and
  monitoring may count differently; verify actual billing dashboards.
- Snapshots cost $0.06/GB-month and continue billing independently of a deleted
  VM until removed.
- Reserved IPs, DNS, load balancers, external volumes, backups, or object
  storage are excluded unless separately selected and priced.

## Shutdown versus deletion

DigitalOcean bills a Droplet from creation until destruction, including while
powered off. Shutdown is an operational action, not a cost-control action.

- **Shutdown:** use for brief maintenance, safe snapshots, resize workflows, or
  restart testing. It does not stop compute charges.
- **Deletion:** use after an approved backup when compute is no longer needed.
  It stops Droplet billing but is destructive.
- **Snapshot then delete:** possible development-gap strategy, but restoration
  reliability, snapshot size, IP/DNS changes, and credential rotation must be
  tested before relying on it.

## Lifecycle policy

### Development

- provision only after explicit approval;
- tag every billable resource to this project;
- enable budget alerts before compute creation;
- destroy idle development VMs when a tested reproducible rebuild exists;
- review cost daily while resources exist; and
- avoid unmanaged duplicate environments.

### Pre-judging freeze

- create and verify an approved backup;
- freeze versions and infrastructure;
- run end-to-end and recovery checks;
- confirm judge URL, TLS, credentials, and availability window; and
- approve the continuous-retention estimate.

### Judging retention

- keep one primary environment, not parallel idle copies;
- do not resize, upgrade, or rotate non-expiring credentials without cause;
- monitor health and cost;
- preserve a minimal recovery backup; and
- keep availability through the approved post-judging buffer.

### Teardown

After winner announcement and the approved buffer:

- obtain deletion approval;
- preserve only required public-safe evidence and approved encrypted backup;
- destroy VM, volumes, snapshots, reserved addresses, load balancers, and
  project DNS records;
- revoke cloud, Git, model-provider, DataHub, and MCP credentials;
- verify the provider billing inventory is empty; and
- record the final cost and deletion date.

**Reminder: powering off is not teardown. Delete all approved project
resources after judging to stop charges.**

## Uncertainty

- Provider prices and capacity may change.
- Taxes, currency conversion, DNS, TLS services, monitoring, and model API
  usage are excluded.
- A 16 GB VM may require resizing after actual DataHub/MCP/application load
  measurement.
- Public IPv4, firewall, backup, and snapshot behavior must be rechecked for
  the selected provider and region.
- Hackathon judge traffic and retention requirements are not precisely stated.
