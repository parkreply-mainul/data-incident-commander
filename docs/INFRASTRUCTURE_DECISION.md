# Infrastructure Decision

> Historical Sprint 4D paid-route decision. Sprint 8C Gate 1A now evaluates
> Google Cloud Free Trial first, OVHcloud Public Cloud trial second, and this
> paid OVHcloud B3-16 configuration only as the last resort. AWS is not
> recommended for the preferred runtime.

## Selected plan

| Decision | Selection |
| --- | --- |
| Provider | **OVHcloud Public Cloud** |
| Region | **Gravelines, France (`GRA`)**, subject to exact SKU availability and quote |
| VM | **B3-16: 4 vCore, 16 GB RAM, 100 GB NVMe** |
| Architecture | Linux x86_64, subject to image verification |
| Expected compute price | **$0.1208/hour**, observed 2026-07-24; region, tax, IP, and invoice currency require confirmation |
| Primary lifecycle | **Model C:** short development VM, destroy it, then create a separate clean final judging VM |
| Expected project cost | **$115–$130 before tax**, excluding model/API usage |
| Funded minimum | **$130 before tax** without assuming promotional credit |
| Maximum guardrail | **$175 before tax** through teardown |
| Backup | **Hetzner CCX23 in Nuremberg (`nbg1`)**: 4 dedicated vCPU, 16 GB, 160 GB; €0.1378/hour or €85.99/month cap plus IPv4 and VAT |

The region is selected for proximity to the Europe/Paris operator and a
European judging endpoint. It is provisional until the provider shows B3-16
capacity, the Ubuntu LTS image, x86_64 architecture, public IPv4 terms, and an
all-in quote for that exact region.

## Why this is the smallest reliable choice

OVHcloud B3-16 meets the project's 4-vCPU/16-GB/50-GB planning baseline without
using unsupported reduced memory. Its published 100 GB local NVMe exceeds the
disk baseline, and its hourly rate is lower than the verified DigitalOcean and
current Hetzner dedicated reference rates. Model C preserves judging
reliability by proving that the public configuration can build a clean final
environment.

Cheaper candidates are not selected merely on price:

- local Docker has only 3.83 GiB and remains blocked;
- Oracle Always Free provides only 2 OCPU/12 GB under current documentation;
- Scaleway's attractive compute rate excludes storage and IPv4, and the exact
  all-in configuration and lifecycle behavior remain unresolved;
- Spot/preemptible capacity is unsuitable for judging;
- managed DataHub alone has unresolved OSS-rule compatibility; and
- Kubernetes or multi-VM designs add cost and operational failure modes.

## Hackathon compliance

The selected topology is still a self-hosted DataHub OSS `v1.6.0` plan:

```text
public HTTPS application
        |
React + FastAPI + MCP on one remote VM
        |
private local connection
        |
DataHub OSS v1.6.0 on the same VM
```

The official rules require open-source DataHub plus an approved agent
technology and an easy-to-access project URL. They do not explicitly name or
ban OVHcloud. They also do not explicitly state whether judges may be issued
test credentials. Credential acceptability must be confirmed with organizers;
the UI must not expose DataHub, MCP, databases, or mutation administration
directly.

## Go/no-go criteria

**GO for a future provisioning checkpoint requires all of:**

- explicit user approval of provider, region, VM, lifecycle, and maximum
  budget;
- current provider quote at or below the $175 guardrail;
- account eligibility, quota, and B3-16 capacity confirmed without relying on
  promotional credit;
- Ubuntu LTS x86_64 image, SSH keys, public IPv4, cloud firewall, snapshots,
  hourly billing, and deletion behavior verified;
- hackathon organizer clarification on judge credentials or an approved
  anonymous read-only demo design;
- infrastructure scripts/configuration reviewed without secrets;
- billing alert, resource labels, teardown owner, and 2026-09-09 deletion date;
- an application exposure plan that publishes only HTTPS; and
- separate approval before image pulls or DataHub startup.

Any missing item is **NO-GO**. Provider signup, payment entry, resource
creation, and startup remain blocked.

## Approval boundaries

The user must explicitly approve each of these material actions in a later
sprint:

1. creating or using a provider account and accepting provider terms;
2. entering or authorizing a payment method;
3. accepting the exact quote, tax treatment, and $175 guardrail;
4. creating firewall, IP, VM, disk, snapshot, DNS, or monitoring resources;
5. storing cloud or deployment credentials in an approved secret system;
6. pulling images and starting DataHub;
7. creating the final judging environment and issuing judge credentials; and
8. deleting billable resources and rotating credentials.

**No infrastructure has been provisioned, purchased, reserved, or started.**
