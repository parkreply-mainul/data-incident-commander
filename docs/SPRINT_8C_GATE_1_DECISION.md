# Sprint 8C Gate 1A Research Decision

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

**Gate 1A outcome: complete. Current outcome: NO-GO for Gate 1B and
infrastructure creation.**

The recommended free-credit order is:

1. **Primary free route: Google Cloud Free Trial**
2. **Fallback free route: OVHcloud Public Cloud free trial**
3. **Paid last resort: OVHcloud `b3-16` under the existing $175-before-tax
   project guardrail**

AWS Free Plan is not selected because its published eligible x86
general-purpose maximum is `m7i-flex.large` at 2 vCPU/8 GiB, which meets only
the absolute floor and lacks the margin expected for reliable judging.

No account-specific eligibility, active credit, quota, regional capacity, or
pre-creation quote was observed. Research alone cannot satisfy this gate.

## Why Google Cloud is primary

- $300 is larger than the approximately $145–$147 public 30-day estimate for
  `n2-standard-4`, 50–100 GiB standard disk, and one IPv4.
- Ninety days comfortably spans development, submission, and the August
  judging period if activated at the approved time.
- The official trial does not automatically charge. Paid billing requires a
  manual activation.
- Ubuntu 24.04 LTS x86 and the preferred 4-vCPU/16-GiB machine type are
  officially documented.

Risks:

- the user might be ineligible due to prior Google paid use or a prior trial;
- a payment method and identity verification are required;
- Free Trial quota cannot be increased;
- N2, disk, IP quota and zonal capacity are account-specific; and
- regional pricing, egress, tax, and the final billing estimate remain unknown.

Classification: **POSSIBLY FEASIBLE / ACCOUNT VERIFICATION REQUIRED**.

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

## Strict GO criteria

Gate 1B verification may produce a **GO for a Gate 2 resource-creation approval
request**, not for creation itself, only when all are evidenced:

- promotional credit is active or contractually guaranteed for this account;
- the candidate VM and Ubuntu 24.04 x86 image are available;
- CPU, disk, instance, and IPv4 quotas are sufficient;
- the complete estimate, including disk, IPv4, expected network, and tax,
  remains within credit with a safe margin;
- the credit lasts through the planned runtime and judging window;
- no automatic paid conversion has been accepted unintentionally;
- deletion, retained-resource billing, budget alerts, and credit-expiry
  behavior are understood;
- public judging access can be provided safely; and
- the user separately and explicitly approves exact resource creation.

## Strict NO-GO criteria

Remain or return **NO-GO** if:

- the account is ineligible or the credit is absent;
- preferred size or Ubuntu/x86 is excluded;
- quota/capacity cannot support the preferred VM;
- using only the technical floor would threaten judging reliability;
- billing, tax, traffic, IPv4, disk, or expiration is unclear;
- an unacceptable deposit or paid-plan conversion is required;
- automatic billing risk is not explicitly accepted;
- public judging access is unavailable;
- the conservative estimate can exceed the credit; or
- account verification cannot be completed without sharing sensitive data.

## Next user action

Under Gate 1A, follow
[CLOUD_ACCOUNT_VERIFICATION_CHECKLIST.md](CLOUD_ACCOUNT_VERIFICATION_CHECKLIST.md)
for Google Cloud only as far as public research or an already accessible
console permits. Stop before account creation, payment or identity
verification, terms acceptance, or trial activation. Return only the redacted
status fields requested by the checklist.

If Google is ineligible or cannot show sufficient quota, perform the OVHcloud
fallback inspection, again stopping before account/project creation or trial
activation. Request explicit Gate 1B approval if eligibility cannot be
confirmed without those actions.

## External-action status

- Gate 1A research and already accessible read-only inspection: authorized
- Gate 1B account use/creation and eligibility actions: not authorized
- Account creation: not authorized without Gate 1B
- Trial activation: not authorized without Gate 1B
- Billing account/project creation: not authorized without Gate 1B
- Payment or identity submission: not authorized without Gate 1B
- VM/network/IP creation: not authorized
- Cloud CLI login/configuration: not authorized
- Docker/DataHub/MCP installation or startup: not authorized
- Mutation: not authorized
