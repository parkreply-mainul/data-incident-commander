# Sprint 8C Gate 2 Deployment Manifest

## Status and authority boundary

**NO-GO. Planning only; Gate 2 is not approved.**

Gate 1A and Gate 1B are complete. The user manually verified an active Google
Cloud Free Trial with €256.52 remaining, unaccepted paid conversion, Compute
Engine API enabled, `e2-standard-4`, Ubuntu 24.04 LTS, and 100 GB Balanced
Persistent Disk availability.

No VM, disk, VPC, subnet, firewall rule, external IP, IAM binding, budget,
logging configuration, or other infrastructure resource has been created or
changed by this plan. It authorizes no cloud CLI authentication, API
enablement, billing change, resource creation, installation, image pull,
DataHub or MCP startup, application deployment, or mutation.

Gate 2 creates only an empty host and its minimum secure network and access
boundary. Docker, swap, package installation, repository access, and all
workload activity belong to Gate 3 or later.

## Executable manifest

Every **PRIVATE UNRESOLVED** or **UNRESOLVED** value must be supplied,
console-verified, and explicitly approved before execution. Private values
remain outside Git.

### Project and location

| Field | Required value | Status |
|---|---|---|
| Provider | Google Cloud Free Trial | Verified |
| Project display name | `DataIncidentCommander` | Account-observed |
| Exact project ID | Private console value; do not commit | **PRIVATE UNRESOLVED** |
| Region | `europe-west9` | Recommended; quota verification required |
| Zone | `europe-west9-a` | Recommended; capacity verification required |
| Fallback zone | None automatic | Zone changes require a revised manifest and approval |

The operator must verify that the privately selected project ID maps to the
observed display name immediately before every approved action. No project ID,
billing-account ID, user identity, or payment detail belongs in this
repository.

### VM and immutable image

| Field | Required value | Status |
|---|---|---|
| VM name | `dic-runtime-01` | Proposed |
| Machine | `e2-standard-4`, standard provisioning | Account-observed |
| CPU and RAM | 4 vCPU, 16 GB | Account-observed |
| Architecture | x86_64 | Verify against exact image and created VM |
| OS | Ubuntu 24.04 LTS amd64 | Intended |
| Image project | `ubuntu-os-cloud` | Console verification required |
| Exact image name | Immutable image name, not a family | **UNRESOLVED** |
| Exact image self-link | Immutable self-link | **PRIVATE UNRESOLVED** |
| Image creation date | Exact console value | **UNRESOLVED** |
| Image deprecation state | Active; not deprecated or obsolete | **UNRESOLVED** |
| Provisioning | On-demand; not Spot or preemptible | Proposed |
| Automatic restart | Enabled | Proposed |
| Host maintenance | Migrate | Proposed |
| Startup script | None | Fixed |
| Attached service account | None | Fixed |
| Deletion protection | Disabled for bounded teardown | Proposed |

An Ubuntu image family may locate a candidate during inspection, but it must
not appear in the approved command or executable resource payload. Approval
binds the exact immutable image name and self-link.

Enable Shielded VM Secure Boot, vTPM, and integrity monitoring after confirming
the exact image supports them. A compatibility failure stops Gate 2 and does
not authorize silently disabling a protection.

### Disk

| Field | Required value | Status |
|---|---|---|
| Name | `dic-runtime-01-boot` | Proposed |
| Type | `pd-balanced` | Account-observed |
| Size | 100 GB | Account-observed |
| Scope | Zonal, same zone as VM | Proposed |
| Encryption | Google-managed encryption | Proposed |
| Auto-delete with VM | Enabled | Proposed |
| Snapshots | None in Gate 2 | Fixed |
| Additional disks | None | Fixed |

### Labels and target selector

Apply only these non-secret labels:

| Key | Value |
|---|---|
| `application` | `data-incident-commander` |
| `environment` | `development` |
| `managed-by` | `gate2-manual` |
| `sprint` | `8c` |
| `lifecycle` | `temporary` |
| `data-classification` | `synthetic-only` |

Apply the dedicated network tag `dic-gate2-host` only to `dic-runtime-01`.
IAM permissions to edit metadata, labels, or network tags must not be granted
through broad permanent project roles.

## Network and firewall manifest

### Network

| Field | Required value |
|---|---|
| VPC | `dic-vpc` |
| Routing | Regional |
| Auto-created subnets | Disabled |
| Subnet | `dic-europe-west9-subnet` |
| Subnet CIDR | `10.42.0.0/24` |
| Region | `europe-west9` |
| External IPv4 | None |
| External IPv6 | None |
| Static IP | None |
| Cloud NAT | None |
| Load balancer | None |
| Public DNS | None |
| VPC Flow Logs | Disabled |

Gate 2 exposes no public application or administrative endpoint.

### IAP-only SSH ingress

Create exactly one Gate 2 ingress allow:

| Field | Value |
|---|---|
| Rule name | `dic-g2-allow-iap-ssh` |
| Direction | Ingress |
| Priority | `1000` |
| Action | Allow |
| Protocol and port | TCP 22 |
| Source | `35.235.240.0/20` |
| Target tag | `dic-gate2-host` |
| Firewall logging | Disabled |

No rule may allow TCP 22 from the public internet, an operator IP, a broad
private range, or another source. No ingress rule for HTTP, HTTPS, DataHub,
MCP, backend, frontend, database, Kafka, search, or Docker is allowed.

### Fail-closed egress

Create this VPC rule, scoped only to the dedicated Gate 2 tag:

| Field | Value |
|---|---|
| Rule name | `dic-g2-deny-all-egress` |
| Direction | Egress |
| Priority | `1000` |
| Action | Deny |
| Destination | `0.0.0.0/0` |
| Protocols and ports | All |
| Target tag | `dic-gate2-host` |
| Firewall logging | Disabled |

No egress allow rule is approved in Gate 2. Do not rely on the implied
allow-all egress rule. DNS, NTP, Ubuntu repositories, Docker registries,
GitHub, DataHub image registries, package indexes, and every public
destination remain Gate 3 approval items.

The rules affect only `dic-runtime-01` through `dic-gate2-host` and must not
alter unrelated resources.

### Effective firewall-policy audit

Before approval, capture redacted console evidence for:

- organization policies and hierarchical firewall policies;
- folder policies and inherited firewall policies, even if no folder is
  expected;
- project-level firewall policies;
- global network firewall policies;
- all `dic-vpc` VPC firewall rules and implied rules;
- target tags and service identities;
- effective ingress and egress rules for the proposed VM; and
- any policy that can override, bypass, or precede the proposed rules.

Do not assume the absence of an organization, folder, or existing VPC removes
the need to inspect its effective policy context.

Approval requires proof that only IAP's `35.235.240.0/20` can reach TCP 22, no
other ingress can reach the VM, all VM egress is denied, no inherited rule
exposes the VM, and no unrelated resource is targeted.

## IAP, OS Login, and IAM manifest

### Operator workflow

After Gate 2 approval and creation:

1. Use the Google Cloud console or a separately approved authenticated client
   to initiate IAP TCP forwarding to `dic-runtime-01`.
2. IAP authenticates and authorizes the private operator identity.
3. The tunnel reaches TCP 22 only from `35.235.240.0/20`.
4. OS Login authorizes the operator; project metadata SSH keys remain blocked.
5. Verify the SSH host key through an independently observed console source
   before accepting it.
6. Run only read-only host validation.
7. End the session and confirm no metadata SSH key was persisted outside OS
   Login.

No workflow step is executed by this document.

### SSH controls

- OS Login enabled at the instance;
- OS Login 2-Step Verification required;
- operator Google account 2-Step Verification required;
- project-wide SSH keys blocked;
- password authentication disabled;
- routine root login disabled;
- metadata-based SSH keys prohibited;
- host-key verification mandatory;
- no private key stored in Git, VM metadata, documentation, or logs; and
- no public VM IP or public TCP 22 path.

### Least-privilege IAM

These private account values and exact bindings require separate approval:

| Field | Requirement | Status |
|---|---|---|
| Operator Google identity | Kept outside Git | **PRIVATE UNRESOLVED** |
| IAP role | IAP-secured Tunnel User / `roles/iap.tunnelResourceAccessor`, target-scoped where supported | **UNRESOLVED** |
| OS Login role | Least privilege for validation; temporary admin only if required | **UNRESOLVED** |
| Instance viewing | Minimal permission to resolve and view the target VM | **UNRESOLVED** |
| Service usage | Minimal permission to use approved IAP/OS Login services | **UNRESOLVED** |
| Temporary administrator | Private identity, purpose, start, expiry, and revocation evidence | **PRIVATE UNRESOLVED** |
| Policy administrators | Private identities allowed to edit IAM, firewall, tags, labels, and metadata | **PRIVATE UNRESOLVED** |

Rules:

- no permanent Owner or Editor;
- no permanent broad Compute Admin as the operating model;
- privileged access is resource-scoped or just-in-time where supported;
- every binding has an owner, purpose, scope, and removal time;
- the operator cannot attach or impersonate a service account;
- the VM has no attached service account;
- IAM, API, metadata, label, tag, firewall, and policy changes require explicit
  approval; and
- no user email, subject ID, or account identifier is committed.

Before approval, confirm required IAP TCP forwarding and OS Login features/APIs
are available or identify exact separately approved enablement actions. This
plan does not enable them.

## Logging policy

Gate 2 uses the lowest-cost configuration:

- VPC Flow Logs disabled;
- firewall rule logging disabled;
- Ops Agent not installed;
- premium logging not enabled;
- no custom log sink, Pub/Sub topic, or exported destination; and
- no new retention configuration.

Required provider audit logs that already exist remain provider-managed, but
this plan does not change them. Gate 3 may propose bounded logging only after
sampling, aggregation interval, metadata inclusion, retention, exclusions, and
cost are reviewed.

## Approval-grade cost and budget fields

The earlier €140–€180 range is historical planning context only, not an
approval estimate. The account console must supply:

| Cost field for `europe-west9` | Required account-console value |
|---|---|
| `e2-standard-4` compute | **UNRESOLVED** |
| 100 GB `pd-balanced` | **UNRESOLVED** |
| IAP TCP forwarding | **UNRESOLVED; confirm whether any charge applies** |
| Logging | Expected zero optional Gate 2 logging; verify |
| External IPv4 | Expected zero because none is assigned; verify |
| Network transfer | **UNRESOLVED** |
| Tax/currency treatment | **UNRESOLVED** |
| Expected daily cost | **UNRESOLVED** |
| Expected seven-day cost | **UNRESOLVED** |
| Cost through teardown | **UNRESOLVED** |
| Remaining credit after projected use | **UNRESOLVED** |
| Exact Free Trial expiration | **PRIVATE UNRESOLVED** |
| Paid conversion remains unaccepted | Reconfirm immediately before creation |

Do not infer or silently convert missing prices. Reconfirm the estimate,
credit, expiration, and non-paid account state immediately before approval and
again before creation.

### Human budget monitoring

| Control | Required value |
|---|---|
| Monitoring owner | Private named person outside Git — **UNRESOLVED** |
| Review frequency | At least twice daily while any Gate 2 resource exists |
| Planning ceiling | Exact approved cost-through-teardown — **UNRESOLVED** |
| Alert thresholds | 50%, 75%, 90%, and 100% of approved project budget |
| Forecast alert | 100% of approved budget |
| Manual shutdown trigger | Forecast or actual spend reaches 90%, unexpected charge appears, or trial state changes |
| Mandatory teardown trigger | Forecast/actual reaches 100%, paid conversion is requested, expiry safety date arrives, or judging access ends |
| Billing anomaly review | Every twice-daily review |
| Unexpected-resource review | Every twice-daily review |

Budgets are alerts, not hard caps. Gate 2 adds no automated billing
disablement, Pub/Sub automation, or automatic destructive action. Creating or
changing a project budget requires explicit approval in the final Gate 2
action list.

## Runtime and teardown schedule

| Field | Required private/account value |
|---|---|
| Planned runtime start | **UNRESOLVED** |
| Judging availability requirement | **UNRESOLVED** |
| Exact Free Trial expiration | **PRIVATE UNRESOLVED** |
| Teardown date | **UNRESOLVED** |
| Named teardown owner | **PRIVATE UNRESOLVED** |
| Teardown verification time and timezone | **UNRESOLVED** |

Teardown must occur no later than seven days before Free Trial expiration
unless a separately reviewed and approved paid plan exists. The date must also
satisfy verified judging availability.

Teardown is a separate destructive action. Resolve and confirm exact IDs for
only the VM, boot disk, two Gate 2 firewall rules, subnet, VPC, Gate 2 IAM
bindings, and any approved Gate 2 project budget. Never delete the project,
billing account, or unrelated resource.

After approved teardown, verify that the exact VM and disk are absent, no
external IP was ever assigned, firewall rules/subnet/VPC are absent, Gate 2 IAM
bindings are removed, no snapshot or optional logging resource exists, and no
Gate 2 resource continues to accrue cost. Remove a budget only with separate
authorization.

## Swap ownership

Gate 2 validates the empty host's CPU, memory, disk, architecture, operating
system, access, and effective firewall policy. Gate 2 does not create swap.

Gate 3 must create and verify at least 2 GB swap before DataHub startup. The
DataHub startup gate fails closed if swap is absent, smaller than 2 GB, or
unusable.

## Creation and validation sequence

Only after every blocker is resolved and the exact manifest is approved:

1. reconfirm trial state, credit, expiry, paid-conversion state, project,
   estimate, quota, capacity, and immutable image;
2. capture a redacted pre-creation inventory and effective policy audit;
3. apply only approved least-privilege IAM bindings;
4. create the VPC, subnet, IAP ingress rule, and deny-all egress rule;
5. create the VM and disk using the immutable image, without a service account
   or external IP;
6. apply only approved labels and `dic-gate2-host`;
7. verify inventory and effective policy exactly match the manifest;
8. connect through IAP and OS Login and verify the host key;
9. stream and run only
   `deploy/scripts/check_gate2_base_host.sh --expected-hostname
   dic-runtime-01`, without persisting a repository checkout;
10. record base host properties and current console cost;
11. end access and stop; and
12. request Gate 3 approval before swap, Docker, packages, repositories,
    images, DataHub, or MCP.

Do not silently change zones, attach an external IP or service account,
broaden IAM/firewall access, disable Shielded VM, allow egress, or create an
extra resource.

## Acceptance criteria

Gate 2 succeeds only if:

- actual inventory exactly matches the approved manifest;
- `check_gate2_base_host.sh` passes its pristine-host checks;
- the VM reports 4 vCPU, 16 GB RAM, Ubuntu 24.04 LTS amd64, the approved image,
  and at least 50 GB usable disk;
- no external IPv4 or IPv6 is attached;
- IAP plus OS Login is the only administrative path;
- operator 2-Step Verification and least-privilege IAM are verified;
- only IAP can reach TCP 22 and all VM egress is denied;
- effective policy evidence shows no unintended inherited allow;
- no service account, startup script, package, swap, Docker component,
  repository, workload, or secret is present;
- optional logging remains disabled;
- actual cost remains within the approved estimate;
- trial and paid-conversion state are unchanged; and
- no unrelated resource was created or modified.

Failure of any criterion is a Gate 2 failure, not partial success.

## Remaining NO-GO blockers

Gate 2 remains NO-GO until supplied and approved privately:

1. exact project ID;
2. operator identity, 2-Step Verification status, and IAM eligibility;
3. `europe-west9-a` quota and current `e2-standard-4` capacity;
4. immutable Ubuntu image name, self-link, creation date, architecture, and
   deprecation status;
5. effective organization, folder, project, global-network, VPC, inherited,
   ingress, and egress firewall-policy evidence;
6. exact itemized console estimate and tax/currency treatment;
7. exact Free Trial expiration and reconfirmed unaccepted paid conversion;
8. planned runtime start and judging availability requirement;
9. named private budget-monitoring owner;
10. named private teardown owner, teardown date, and verification time;
11. confirmation that IAP TCP forwarding and OS Login features/APIs are
    available; and
12. explicit approval of every IAM, budget, network, firewall, VM, and disk
    action.

Approval of Gate 2 never approves Gate 3 or paid conversion.
