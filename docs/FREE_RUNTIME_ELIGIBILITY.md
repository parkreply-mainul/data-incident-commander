# Free Runtime Eligibility

## Decision scope

This Gate 1A research was performed on **2026-07-24** using only official
provider sources. No account was created or accessed, no trial was activated,
no billing project or resource was created, and no payment method was entered.
Gate 1B requires separate approval before account use or creation,
trial-eligibility actions, identity or payment verification, trial activation,
or provider terms acceptance. Gate 2 separately governs resource creation.

The required planning target is an x86_64 Ubuntu 24.04 LTS VM with 4 vCPU,
16 GB RAM, and 50–100 GB disk. The absolute floor of 2 CPU, 8 GB RAM, 2 GB
swap, and 20 GB usable disk is a feasibility floor, not the preferred judging
configuration.

Prices below are public list-price estimates in USD unless stated otherwise.
They exclude tax and variable outbound traffic. A 30-day estimate uses 720
hours. Provider console quotes, quotas, regional capacity, account currency,
tax, and promotional-credit coverage remain mandatory gates.

## Summary

| Order | Provider | Free offer | Preferred VM | Billing behavior | Gate 1A decision |
|---|---|---|---|---|---|
| 1 | Google Cloud Free Trial — primary free route | $300, 90 days | `n2-standard-4`: 4 vCPU, 16 GiB plus 50–100 GB disk | Payment verification required; no charges unless manually upgraded to paid billing | **POSSIBLY FEASIBLE — Gate 1B verification required** |
| 2 | OVHcloud Public Cloud trial — free fallback | €200 in France / US$200 worldwide, one month | Public `b3-16`: 4 vCore, 16 GB, 100 GB NVMe | Valid payment method required; automatic billing after credit exhaustion | **ACCOUNT VERIFICATION REQUIRED** |
| 3 | OVHcloud `b3-16` — paid last resort | No free-credit assumption | Public `b3-16`: 4 vCore, 16 GB, 100 GB NVMe | Paid usage subject to a fresh quote, explicit approval, and the $175-before-tax guardrail | **NOT AUTHORIZED** |
| 4 | AWS — not recommended | $100 immediately and up to $100 earned, Free Plan up to six months | Free Plan limits published eligible types to at most `m7i-flex.large`, 2 vCPU/8 GiB | Payment method required; Free Plan does not charge unless upgraded or a paid-only service is activated | **NOT FEASIBLE at preferred size** |

No additional provider was evaluated because Google Cloud and OVHcloud both
have official offers that can potentially fund the preferred target.

## 1. Google Cloud Free Trial — primary free route

### Confirmed from official sources

- The [Google Cloud Free Program](https://docs.cloud.google.com/free/docs/free-cloud-features)
  gives eligible new users **$300 for 90 days**.
- Eligibility requires never having been a paying Google Cloud, Google Maps
  Platform, or Firebase user and never having previously enrolled in the Free
  Trial.
- A valid credit card or other payment method is required. Google verifies
  identity and payment and may place a temporary $0–$1 authorization hold.
- The Free Trial creates a non-billable trial billing account. Google states
  there are no automatic charges; conversion to paid billing requires manual
  activation.
- When credit or 90 days expires without an upgrade, the trial billing account
  closes and resources stop. It enters a limited recovery period before
  deletion.
- Compute Engine is covered, but Free Trial accounts cannot request quota
  increases, use GPUs, Windows Server images, Marketplace, or certain other
  services.
- Quota does not guarantee zonal capacity. Both must be checked in the account.
- Google documents Ubuntu 24.04 LTS x86 as the GA image family
  `ubuntu-2404-lts-amd64`.
- The official general-purpose pricing page lists `n2-standard-4` at 4 vCPU,
  16 GiB, and **$0.194236/hour** in its displayed US pricing.
- Standard Persistent Disk is approximately $0.04/GiB-month in the displayed
  US pricing. An in-use standard VM external IPv4 is $0.005/hour. Regional
  pricing and currency can differ.

### Candidate and estimate

Candidate: `n2-standard-4`, Ubuntu 24.04 LTS x86, `us-central1`, one ephemeral
external IPv4, and 50–100 GiB standard Persistent Disk. The region is a pricing
reference, not a selection; account quota, capacity, latency, and judging
access must be reviewed.

| Period | 50 GiB disk estimate | 100 GiB disk estimate |
|---|---:|---:|
| Hour, blended | $0.2020 | $0.2048 |
| Day | $4.85 | $4.92 |
| 7 days | $33.94 | $34.41 |
| 30 days | $145.45 | $147.45 |

Calculation:

- compute: `$0.194236 × 720 = $139.84992`;
- disk: approximately `$2/month` for 50 GiB or `$4/month` for 100 GiB;
- IPv4: `$0.005 × 720 = $3.60`.

Outbound traffic, snapshots, logs, DNS, tax, and regional price differences are
excluded. Even the 100 GiB estimate leaves approximately $152.55 of the $300
credit, but only the account's billing estimate can confirm coverage.

### Account-specific unknowns

- whether the user is eligible or has prior paid/trial history;
- country-specific payment and bank verification;
- regional N2 CPU, disk, and in-use external IP quotas;
- `n2-standard-4` and Ubuntu image capacity in the selected zone;
- whether account abuse controls restrict the intended VM;
- exact regional price, currency, tax, and egress;
- whether one public IPv4 is available; and
- trial activation date and credit expiration visible in the console.

### Feasibility

**POSSIBLY FEASIBLE** and the recommended free route. It funds the preferred
shape for 30 days in the public estimate, covers the judging window if
activated at the appropriate time, and does not automatically convert to paid
billing. It remains **NO-GO** until eligibility, active credit, quota, capacity,
and the non-paid billing state are observed manually.

## 2. OVHcloud Public Cloud trial — free fallback

### Confirmed from official sources

- The [French offer](https://www.ovhcloud.com/fr/public-cloud/free-trial/)
  advertises **€200** for one month. The
  [worldwide offer](https://www.ovhcloud.com/en/public-cloud/free-trial/)
  advertises **US$200**; the account market determines currency.
- The offer is for the first Public Cloud project. An existing OVHcloud account
  may qualify only if the person has never created a Public Cloud project or
  used the credit.
- Credit activates when the first project is activated and expires after one
  month.
- A valid payment method must be saved.
- After credit is exhausted, subsequent Public Cloud use is billed
  automatically to the default payment method.
- The offer covers ordinary Public Cloud products at public rates in available
  regions, excluding free/beta offers and incompatible promotions.
- The [official price list](https://www.ovhcloud.com/en/public-cloud/prices/)
  lists `b3-16` at 4 vCore, 16 GB RAM, 100 GB NVMe, and $0.1208/hour. It says
  an IPv4 address is included by default except in Local Zones, where the
  order screen supplies the additional-IP price.
- Public Cloud instances are hourly billed and deletable. Exact account terms
  and resource deletion behavior must be reviewed before activation.

### Candidate and estimate

Candidate: non-Local-Zone `b3-16`, preferably Gravelines if the account shows
x86_64 and Ubuntu 24.04 LTS.

| Period | Compute + included local disk | IPv4 | Estimated total |
|---|---:|---:|---:|
| Hour | $0.1208 | Included outside Local Zones | $0.1208 |
| Day | $2.8992 | Included outside Local Zones | $2.90 |
| 7 days | $20.2944 | Included outside Local Zones | $20.29 |
| 30 days | $86.976 | Included outside Local Zones | $86.98 |

The public estimate is within €200/US$200, before tax and any separately
charged traffic, snapshot, backup, or additional IP. It does not prove the
account's regional price or promotional coverage.

### Account-specific unknowns

- whether this person or an existing account is eligible;
- payment-card authorization, identity checks, or any deposit;
- `b3-16` quota and capacity in a suitable non-Local-Zone region;
- x86_64 and Ubuntu 24.04 image availability in that region;
- exact tax, account-currency conversion, traffic coverage, and credit balance;
- whether project activation immediately accepts automatic post-credit billing;
  and
- whether activation can be timed to cover the entire August 17–31 judging
  period. Activating too early could exhaust the one-month duration before
  judging ends.

### Feasibility

**ACCOUNT VERIFICATION REQUIRED.** It meets the preferred technical shape and
the credit appears sufficient, but the automatic-billing and one-month timing
risks prevent a free-route GO without manual account evidence and explicit
acceptance.

## 3. OVHcloud `b3-16` — paid last resort

This is the same technical `b3-16` shape evaluated above, but without assuming
promotional credit. It remains subject to a fresh all-in quote, the existing
$175-before-tax guardrail, explicit payment and billing acceptance, and
separate Gate 1B and Gate 2 approvals. Gate 1A does not authorize this route.

## 4. AWS Free Plan — not recommended

### Confirmed from official sources

- The [AWS Free Tier](https://aws.amazon.com/free/) gives new customers $100
  immediately and up to another $100 through specified activities, for a Free
  Plan lasting up to six months or until credits are depleted.
- Existing or former AWS customers are ineligible for the new Free Plan and
  credits.
- A valid payment method and identity/phone verification are required.
- AWS states the Free Plan incurs no charges unless the user upgrades to a Paid
  Plan or activates a paid-only service.
- The initial additional credits are not guaranteed: they must be earned
  through console activities and can take time to appear.
- Free Plan access is limited to selected services and instance types.
- Current official EC2 documentation lists only `t3.micro`, `t3.small`,
  `t4g.micro`, `t4g.small`, `c7i-flex.large`, and `m7i-flex.large` as eligible
  for post-July-15-2025 accounts.
- `m7i-flex.large` is x86 with 2 vCPU and 8 GiB. It meets only the project's
  absolute CPU/RAM floor.
- `m7i-flex.xlarge` and `m6i.xlarge` provide the preferred 4 vCPU/16 GiB shape,
  but neither appears in the published Free Plan eligible list.
- AWS charges $0.005/hour for public IPv4. The EBS pricing example uses
  $0.08/GB-month for gp3 in a representative region.

### Candidate and estimate

Free Plan candidate: `m7i-flex.large`, Ubuntu 24.04 LTS x86 if available
without a Marketplace restriction, 50–100 GB gp3, and one public IPv4.

The current public pages do not expose a reliable all-in Free Plan console
estimate for this account, disk, and region. Exact compute, EBS, IPv4, credit
coverage, and quota are therefore an **account-console gate**, not guessed.
More importantly, the candidate is only 2 vCPU/8 GiB and leaves no memory
margin above DataHub's documented tested baseline.

Paid-plan reference only: `m6i.xlarge` in `us-east-1` is documented at
$0.192/hour. Adding 50–100 GB gp3 at the representative $0.08/GB-month and one
IPv4 produces these planning estimates:

| Period | 50 GB gp3 | 100 GB gp3 |
|---|---:|---:|
| Hour, blended | $0.2026 | $0.2081 |
| Day | $4.86 | $4.99 |
| 7 days | $34.03 | $34.96 |
| 30 days | $145.84 | $149.84 |

This preferred-size path requires verifying or selecting a Paid Plan and
therefore is not an approved free, no-paid-commitment route.

### Feasibility

**NOT FEASIBLE at the preferred target under the published Free Plan.** The
Free Plan is potentially usable at the absolute floor, but that is too risky
for reliable DataHub plus MCP, backend, frontend, and judging. AWS remains an
account-verification reference, not the selected free fallback.

## Coverage and billing risks

| Provider | Compute/disk/IP coverage | Principal risk |
|---|---|---|
| Google Cloud | Compute Engine and covered trial products use the $300 credit; disk/IP are billable components expected to draw from it | Quota cannot be raised during trial; exact coverage and capacity require console evidence |
| OVHcloud free trial | Ordinary Public Cloud services at public rates are covered; `b3-16` includes local disk and normally IPv4 outside Local Zones | Automatic post-credit billing and one-month expiry |
| OVHcloud paid `b3-16` | No promotional-credit coverage is assumed | Paid commitment, tax, traffic, and retained-resource billing |
| AWS | Credits apply to eligible services; EC2 is included, but Free Plan access is limited | Preferred VM size is not in the published Free Plan list; earned second $100 is conditional |

No provider should be treated as free merely because the estimated total is
below the headline credit. Tax, account currency, exclusions, egress, retained
disks/IPs/snapshots, and timing remain explicit gates.

## Sources and access date

All sources accessed 2026-07-24:

- [Google Cloud Free Program](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Google Compute Engine pricing](https://cloud.google.com/products/compute/pricing/general-purpose)
- [Google disk pricing](https://cloud.google.com/compute/disks-image-pricing)
- [Google external IPv4 pricing](https://cloud.google.com/vpc/pricing)
- [Google Compute Engine quotas](https://docs.cloud.google.com/compute/resource-usage)
- [Google operating-system images](https://docs.cloud.google.com/compute/docs/images/os-details)
- [OVHcloud Public Cloud free trial](https://www.ovhcloud.com/en/public-cloud/free-trial/)
- [OVHcloud France free trial](https://www.ovhcloud.com/fr/public-cloud/free-trial/)
- [OVHcloud Public Cloud prices](https://www.ovhcloud.com/en/public-cloud/prices/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [AWS Free Tier FAQs](https://aws.amazon.com/free/free-tier-faqs/)
- [AWS EC2 Free Plan instance guidance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/LaunchingAndUsingInstances.html)
- [AWS general-purpose instance specifications](https://aws.amazon.com/ec2/instance-types/general-purpose/)
- [AWS EBS pricing](https://aws.amazon.com/ebs/pricing/)
- [AWS VPC IPv4 pricing](https://aws.amazon.com/vpc/pricing/)
