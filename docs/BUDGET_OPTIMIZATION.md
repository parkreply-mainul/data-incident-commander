# Budget Optimization

> Historical Sprint 4D paid-route analysis. Sprint 8C Gate 1A supersedes the
> provider order: Google Cloud Free Trial is the primary free route, OVHcloud
> Public Cloud trial is the free fallback, paid OVHcloud B3-16 is the last
> resort, and AWS is not recommended for the preferred runtime.

## Decision basis

All calculations were prepared on **2026-07-24**. They are estimates before
tax and currency conversion. Promotional credit is excluded from the minimum
budget because eligibility, account approval, expiry, service coverage, and
capacity are not guaranteed.

The primary model uses OVHcloud B3-16 at the published **$0.1208/hour** rate.
It assumes:

- 80 active development hours;
- a clean final environment available from 2026-08-07 through 2026-09-09,
  approximately 792 hours;
- the full continuous project interval from 2026-07-24 through 2026-09-09,
  approximately 1,128 hours;
- $10–$20 contingency for snapshot/storage, public IPv4, DNS, egress, and
  pricing variance; and
- tax and foreign-exchange charges remain additional and unknown.

These are planning durations, not infrastructure authorization.

## Lifecycle totals

| Model | Compute assumption | Raw compute | Estimated total before tax | Reliability/cost result |
| --- | ---: | ---: | ---: | --- |
| **A. Continuous development through judging** | 1,128 hours | $136.26 | **$146–$160** | Simplest continuity, but pays for idle development time and carries development drift into judging. |
| **B. Develop, destroy, recreate for submission** | 80 + 792 = 872 hours | $105.34 | **$118–$135** | Cost-efficient; requires proven infrastructure/config restoration and careful snapshot/secret handling. |
| **C. Short development VM plus separate final judging VM** | 80 + 792 = 872 hours | $105.34 | **$115–$130** | Same approximate compute as B, but deliberately validates a clean final rebuild and avoids relying on a mutable development disk. **Selected.** |

The difference between B and C is procedural: B may restore a development
snapshot; C creates the final environment from reviewed scripts and persisted
public configuration, then loads approved secret/state material separately.
Model C is preferred because clean reproducibility is part of the submission
quality bar.

## Credit scenarios

- **OVHcloud:** an eligible first Public Cloud project may receive $200/€200
  for one month. The final 33-day retention window exceeds one month, so some
  spend may remain even if the credit applies.
- **Google Cloud:** an eligible new customer may receive $300 for 90 days.
- **AWS:** a new customer may receive $100 at signup and earn up to another
  $100 within a six-month plan.
- **Azure:** an eligible new account advertises $200 for 30 days.
- **Oracle:** a 30-day $300 trial exists, but the ongoing Always Free allowance
  is only 2 OCPU/12 GB and therefore below this project's baseline.
- **DigitalOcean, Hetzner, Scaleway:** no universal credit was accepted as a
  dependable planning input in this review.

Credits can reduce the invoice, never the required budget authorization or
teardown discipline. A credit-expiry alert must be set before use.

## Minimum budget and guardrail

- **Minimum realistic funded budget:** **$130 before tax**. This covers selected
  Model C near its upper estimate without assuming credit.
- **Maximum guardrail:** **$175 before tax** through verified teardown.
- Stop and request approval before creation if the provider calculator,
  taxes, currency conversion, or required ancillary resources forecast more
  than $175.
- If a verified credit applies, retain the same guardrail and report the final
  net invoice separately.

The previous $250 guardrail remains safe but is no longer cost-optimized. This
sprint recommends replacing it with $175 only after the user approves the
provider quote and lifecycle.

## Cost controls

- create one VM at a time;
- use on-demand/hourly billing, not reservations or long commitments;
- apply project labels and a provider budget alert before compute;
- keep DataHub and application dependencies on the included VM disk where
  operationally safe;
- avoid load balancers, managed databases, Kubernetes, duplicate final
  environments, and paid monitoring for the MVP;
- destroy the development VM after reproducible rebuild and recovery tests;
- do not count power-off as teardown unless the provider explicitly stops
  compute billing;
- inventory disks, snapshots, IPs, backups, DNS, and object storage after VM
  deletion; and
- delete final resources after the approved 2026-09-09 buffer and rotate
  credentials.

## Sensitivity and uncertainty

- Every additional final-runtime day costs about **$2.90** at $0.1208/hour,
  before ancillary charges and tax.
- Every additional 40 development hours costs about **$4.83**.
- A resize above 4 vCPU/16 GB can materially change all totals.
- Snapshot size, public IPv4, tax, and bandwidth remain quote-time checks.
- Judging may not require continuous availability through 2026-09-09; the
  buffer is a project reliability assumption.
