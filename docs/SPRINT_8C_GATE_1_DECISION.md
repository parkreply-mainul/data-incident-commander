# Sprint 8C Gate 1 Closure

## Gate definitions

- **Gate 1A — current checkpoint:** read-only public-offer research and manual
  inspection of an already accessible console. It authorizes no account
  creation, trial activation, billing-account creation, payment or identity
  verification, provider terms acceptance, or resource creation.
- **Gate 1B — separately approval-gated:** create or use a provider account and
  complete trial-eligibility verification, including any approved identity or
  payment-method verification, trial activation, and provider terms.
- **Gate 2 — separately approval-gated:** create the exact approved cloud
  infrastructure. Gate 1B never implies Gate 2 approval.

## Decision

**Gate 1A and Gate 1B are complete. Gate 2 remains unapproved and no cloud
resource may be created.**

The user manually verified the following Google Cloud account state on
2026-07-24:

- Free Trial is active;
- €256.52 of trial credit remains;
- the **Activate** control for paid conversion remains present;
- Compute Engine API is enabled;
- a project with the display name `DataIncidentCommander` exists;
- `e2-standard-4` is available with 4 vCPU and 16 GB RAM;
- Ubuntu 24.04 LTS is available;
- 100 GB Balanced Persistent Disk is available;
- the observed estimate remains within the trial credit;
- no VM or infrastructure resource was created;
- no resource was started; and
- no billing change or paid conversion was accepted.

This record contains no project ID, billing-account ID, credential, payment
detail, or identity detail. The project display name is not an authorization
target; the exact project identity must be confirmed outside Git immediately
before any later approved action.

The recommended free-credit order is:

1. **Primary free route: Google Cloud Free Trial**
2. **Fallback free route: OVHcloud Public Cloud free trial**
3. **Paid last resort: OVHcloud `b3-16` under the existing $175-before-tax
   project guardrail**

AWS Free Plan is not selected because its published eligible x86
general-purpose maximum is `m7i-flex.large` at 2 vCPU/8 GiB, which meets only
the absolute floor and lacks the margin expected for reliable judging.

Gate 1B establishes free-credit eligibility and identifies a technically
suitable candidate. It does not establish the exact Gate 2 region, zone,
quota, public-access design, firewall rules, resource names, or itemized
pre-creation quote.

## Why Google Cloud is primary

- the account has an active Free Trial with €256.52 remaining;
- paid conversion remains unaccepted;
- the account exposes the preferred 4-vCPU/16-GB `e2-standard-4` shape;
- Ubuntu 24.04 LTS and 100 GB Balanced Persistent Disk are available; and
- the observed estimate remains within trial credit.

Remaining Gate 2 uncertainties:

- exact project ID confirmation outside Git;
- region, zone, quota, and zonal capacity;
- IAP and OS Login availability and private operator IAM eligibility;
- effective organization, folder, project, network, ingress, and egress
  firewall-policy evidence;
- itemized regional pricing, egress, logging, and tax; and
- credit expiration, budget threshold, and teardown date.

Classification: **FEASIBLE FOR GATE 2 PLANNING; RESOURCE CREATION UNAPPROVED**.

## Why OVHcloud is fallback

- Public `b3-16` matches 4 vCore/16 GB/100 GB and is publicly priced below the
  one-month credit.
- Existing OVHcloud customers may qualify if they have never created a Public
  Cloud project.
- A non-Local-Zone instance normally includes IPv4.

Risks:

- a saved valid payment method is mandatory;
- billing automatically begins after credit exhaustion;
- the credit lasts only one month;
- activating too early may not cover the complete judging period;
- eligibility, architecture, Ubuntu image, capacity, tax, traffic, and exact
  regional pricing require account evidence.

Classification: **ACCOUNT VERIFICATION REQUIRED**.

## Paid last resort

If both free routes fail, retain the previously reviewed OVHcloud `b3-16`
paid option in Gravelines, subject to:

- a fresh all-in quote;
- user acceptance of payment terms and automatic billing;
- the $175-before-tax maximum through teardown;
- quota/capacity and Ubuntu/x86 verification;
- budget alerts; and
- separately approved creation and deletion.

This checkpoint does not authorize the paid route.

## Gate 1 closure criteria

Gate 1B produces a **GO to prepare and request Gate 2 approval**, not a GO to
create resources. The following are confirmed:

- promotional credit is active or contractually guaranteed for this account;
- a 4-vCPU/16-GB candidate VM and Ubuntu 24.04 image are available;
- 100 GB Balanced Persistent Disk is available;
- the observed estimate remains within the available credit;
- no automatic paid conversion has been accepted unintentionally;
- no infrastructure exists; and
- exact resource creation still requires separate user approval.

## Gate 2 blockers

Remain **NO-GO for resource creation** until the Gate 2 approval request names
and verifies:

- exact project identity outside Git;
- region and zone;
- regional CPU, instance, and disk quota;
- exact `e2-standard-4` configuration and Ubuntu image;
- 100 GB Balanced Persistent Disk lifecycle behavior;
- IAP-only SSH and OS Login design with no external VM IP;
- least-privilege operator IAM and 2-Step Verification;
- exact effective firewall-policy evidence and VM-scoped deny-all egress;
- resource naming and labels;
- itemized compute, disk, IAP, network, logging, and tax estimate;
- trial expiration, budget threshold, and teardown date;
- rollback targets; and
- the user's explicit approval of that exact resource set.

## Next user action

Review
[SPRINT_8C_GATE_2_IMPLEMENTATION_PLAN.md](SPRINT_8C_GATE_2_IMPLEMENTATION_PLAN.md)
and supply the still-missing, non-secret region, zone, quota, access, cost, and
teardown fields. A later message must explicitly approve the exact Gate 2
resource set before creation.

## External-action status

- Gate 1A public research: complete
- Gate 1B account and trial-eligibility verification: complete
- Google Cloud Free Trial: active
- Paid conversion: not accepted
- VM/network/IP/firewall creation: not authorized without Gate 2
- Cloud CLI login/configuration: not authorized
- Docker/DataHub/MCP installation or startup: not authorized
- Mutation: not authorized
