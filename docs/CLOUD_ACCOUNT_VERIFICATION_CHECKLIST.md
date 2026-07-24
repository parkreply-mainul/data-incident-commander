# Cloud Account Verification Checklist

## Safety boundary

**Status: Gate 1A and Gate 1B completed on 2026-07-24.** The user manually
confirmed an active Google Cloud Free Trial, €256.52 remaining credit, an
unaccepted paid-conversion **Activate** control, Compute Engine API enabled,
the `e2-standard-4` and Ubuntu 24.04 LTS options, and 100 GB Balanced
Persistent Disk. No VM or infrastructure was created or started, and no
billing change was accepted.

This checklist is retained as the audit procedure. It does not authorize Gate
2 resource creation.

This checklist supports **Gate 1A**, the read-only public-offer research and
manual inspection of an already accessible console. Gate 1A does not authorize
account creation, trial activation, terms acceptance, payment entry or
verification, a billing account or project, resource creation, or paid
conversion.

**Gate 1B** is the separately approved use or creation of a provider account
and completion of trial-eligibility verification. It covers any required
identity or payment-method verification, trial activation, and provider terms.
It must be explicitly approved before those actions. Gate 1B never authorizes
a VM or any other cloud resource; resource creation always requires separate
**Gate 2** approval.

Never send:

- a card or bank-account number;
- identity documents;
- password or recovery codes;
- API keys or access tokens;
- a full billing address;
- tax identifiers; or
- screenshots containing those values.

Redact name, email, customer/account/project IDs, addresses, payment details,
and support case numbers. Send only the requested status text or tightly
cropped, redacted screenshots.

## Primary route: Google Cloud Free Trial

### A. Public offer and prior-use check

1. Open the official
   [Google Cloud Free Program page](https://docs.cloud.google.com/free/docs/free-cloud-features)
   in a private browser window.
2. Confirm it still says:
   - $300 Welcome credit;
   - 90 days;
   - no automatic charges; and
   - manual activation is required to become a paid billing account.
3. Determine privately whether either disqualifier applies:
   - previously a paying Google Cloud, Google Maps Platform, or Firebase user;
   - previously enrolled in the Google Cloud Free Trial.
4. Do not send account identifiers. Return only `prior paid use: yes/no/unsure`
   and `prior trial: yes/no/unsure`.

### B. Stop before activation

The enrollment flow can request a payment method, create a payments profile,
verify identity, create a Free Trial billing account, and create an initial
project. Those actions require explicit Gate 1B approval and are not authorized
by this Gate 1A checklist.

Before entering payment data or clicking a final button such as **Start free**,
**Agree and continue**, **Activate**, or an equivalent:

1. record the exact credit amount, currency, and duration shown;
2. record whether the page calls the resulting account “Free Trial” or “Paid”;
3. record the wording about automatic charging and manual paid activation;
4. record whether a card, bank verification, or identity verification is
   requested; and
5. stop.

Do not click the paid-account **Activate** action under Gate 1A or Gate 1B.
Paid conversion would require a separately documented approval and is not part
of the free-route eligibility check.

### C. If an eligible Free Trial is already active

Only perform this section if the user already has an active trial that was not
created for this sprint.

1. In **Billing > Overview**, verify:
   - account type is **Free trial account**, not paid;
   - remaining credit;
   - credit currency;
   - expiration date/days;
   - an **Activate** button is visible, proving paid conversion has not
     occurred.
2. Do not click **Activate**.
3. In **IAM & Admin > Quotas & System Limits**, inspect without requesting
   changes:
   - regional N2 CPU quota is at least 4;
   - persistent-disk quota supports 100 GiB;
   - in-use external IPv4 quota supports one address;
   - instance quota supports one VM.
4. Inspect candidate regions, starting with `us-central1`, without opening a
   final create action:
   - `n2-standard-4` is listed;
   - Ubuntu 24.04 LTS x86 is listed;
   - the console does not show a quota or policy block.
5. Open the official Pricing Calculator or the read-only estimate shown before
   creation and configure:
   - one `n2-standard-4`;
   - Ubuntu 24.04 LTS;
   - 100 GiB standard Persistent Disk;
   - one public IPv4;
   - expected outbound traffic;
   - 720 hours.
6. Do not save a billing project, reserve an IP, create a network/firewall, or
   click **Create**.

### D. Evidence to return

Return text or redacted screenshots showing:

- `eligibility offer shown: yes/no`;
- credit amount, currency, and expiry;
- exact account label: `Free trial` or `Paid`;
- whether the paid **Activate** control is still present;
- regional N2 CPU quota value and usage;
- disk and in-use external IP quota values;
- candidate region and whether `n2-standard-4` is selectable;
- whether Ubuntu 24.04 LTS x86 is selectable;
- the full pre-creation estimate broken into compute, disk, IPv4, and network;
- any warning, restriction, deposit, or identity-verification message; and
- confirmation: `no resource was created`.

Do not include account, project, billing-account, or payment identifiers.

## Free fallback: OVHcloud

Use only if Google is ineligible, quota-blocked, or unavailable.

Before activating a first Public Cloud project:

1. Open the official account-local Public Cloud free-trial offer.
2. Confirm the account says it is eligible for the first-project €200/US$200
   one-month credit.
3. Check whether a past or current Public Cloud project makes the account
   ineligible.
4. Record the payment-method, identity-check, deposit, and automatic-billing
   wording without entering or accepting anything.
5. Inspect the catalog for a non-Local-Zone `b3-16`:
   - 4 vCore;
   - 16 GB RAM;
   - 100 GB NVMe;
   - x86_64;
   - Ubuntu 24.04 LTS;
   - included public IPv4;
   - suitable region, preferably Gravelines.
6. Record quota/capacity and the complete hourly estimate, including traffic,
   IP, tax, and extras.
7. Stop before **Activate project**, voucher activation, terms acceptance, or
   payment entry.

Return only redacted eligibility, timing, catalog, quota, capacity, and price
evidence. Because OVHcloud documents automatic billing after credit
exhaustion, it cannot receive a GO without explicit acceptance of that risk and
a teardown date comfortably before expiration.

## Paid last resort: OVHcloud `b3-16`

Do not inspect or accept paid ordering terms under Gate 1A. If both free routes
fail, the same `b3-16` configuration may be reviewed under a separately
approved Gate 1B, with a fresh quote and the $175-before-tax guardrail. VM
creation would still require Gate 2 approval.

## AWS — not recommended

AWS is not the preferred free route. If checked manually:

- verify the account is genuinely new;
- select **Free Plan**, not Paid Plan;
- confirm $100 immediate credit and which additional credits are already
  earned;
- confirm `m7i-flex.large` is the largest eligible general-purpose option shown;
- verify whether Ubuntu 24.04 can be used without a paid-only Marketplace
  action;
- inspect EBS and IPv4 coverage and quotas; and
- stop before account creation, payment verification, resource launch, or paid
  upgrade.

Do not treat a Paid Plan's $200 credit as a no-paid-commitment route.

## Review response template

```text
Provider:
Prior paid use: yes / no / unsure
Prior trial: yes / no / unsure
Offer shown:
Account state: no account / inactive / free trial / paid / unsure
Credit and expiration:
Payment or identity request:
Automatic-charge wording:
Candidate VM and region:
CPU quota:
Disk quota:
IPv4 quota:
Ubuntu 24.04 x86 available:
Pre-creation estimate:
Warnings or exclusions:
No resource created: yes / no
```

If any field is unclear, stop and report `unsure`; do not resolve it by
accepting terms or advancing the enrollment flow.
