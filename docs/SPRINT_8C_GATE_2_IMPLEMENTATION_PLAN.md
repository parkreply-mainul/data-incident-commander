# Sprint 8C Gate 2 Implementation Plan

## Status and authority boundary

**Planning only. Gate 2 is not approved.**

Gate 1A and Gate 1B are complete. The user manually verified:

- an active Google Cloud Free Trial with €256.52 remaining;
- paid conversion remains unaccepted;
- Compute Engine API is enabled;
- a project with display name `DataIncidentCommander` exists;
- `e2-standard-4` is available with 4 vCPU and 16 GB RAM;
- Ubuntu 24.04 LTS is available;
- 100 GB Balanced Persistent Disk is available; and
- the observed estimate remains within trial credit.

No VM, disk, network, firewall, external IP, or other infrastructure resource
has been created or started. This plan does not authorize account changes,
paid conversion, cloud CLI authentication, resource creation, Docker
installation, image pulls, DataHub, MCP, application deployment, or mutation.

## Gate 2 objective

Create only the smallest approved, empty Ubuntu host and its minimum secure
network boundary. Gate 2 ends after the host passes read-only prerequisite and
security validation. Docker installation is Gate 3 and remains separately
approval-gated.

## Proposed resource envelope

The exact values marked **unresolved** must be supplied and approved before
execution.

| Field | Proposed value | Gate status |
|---|---|---|
| Provider | Google Cloud Free Trial | Verified |
| Project | Display name `DataIncidentCommander`; exact project ID retained outside Git | Identity confirmation required |
| Machine | `e2-standard-4`, 4 vCPU, 16 GB RAM | Account-observed |
| Architecture | x86_64 | Must be confirmed in the final image/machine selection |
| Image | Ubuntu 24.04 LTS | Account-observed; exact image identity unresolved |
| Boot disk | 100 GB Balanced Persistent Disk | Account-observed; deletion policy unresolved |
| Region and zone | Not selected | **Unresolved** |
| External access | Ephemeral public IPv4 or another reviewed route | **Unresolved** |
| SSH | Key authentication, restricted to the operator's current approved source | **Unresolved** |
| Cloud firewall | Default deny; only approved administrative access during Gate 2 | Rule names and source ranges unresolved |
| Labels | Project-specific, non-secret ownership and lifecycle labels | Exact values unresolved |
| Budget | Must remain within €256.52 trial credit with contingency | Itemized current estimate unresolved |
| Teardown date | Before trial expiry and after judging, subject to the verified expiry date | **Unresolved** |

Do not put project IDs, billing IDs, IP addresses, SSH keys, account emails, or
credentials in this repository.

## Required evidence before approval

The Gate 2 approval request must present, in one bounded resource manifest:

1. exact provider project identity, reviewed outside Git;
2. selected region and zone;
3. account quota for E2 CPU, one instance, 100 GB disk, and one external IPv4
   if used;
4. current zonal availability for `e2-standard-4`;
5. exact Ubuntu 24.04 LTS image identity and x86_64 architecture;
6. disk type, size, encryption default, and delete-with-instance policy;
7. public access route and why it is required;
8. firewall rule names, directions, protocols, ports, priorities, target
   selectors, and source ranges;
9. SSH-key source and storage boundary, without sharing the private key;
10. deterministic resource names and non-secret labels;
11. itemized compute, disk, IPv4, network, snapshot, logging, and tax estimate;
12. trial expiration, budget threshold, monitoring approach, and teardown date;
13. exact creation sequence;
14. exact validation sequence; and
15. exact rollback targets and deletion-cost checks.

If any field is unclear, Gate 2 remains NO-GO.

## Proposed creation sequence after explicit approval

No step below may run before the user approves the complete resource manifest.

1. Reconfirm Free Trial state, remaining credit, and unaccepted paid
   conversion.
2. Reconfirm project, region, zone, quota, capacity, image, and itemized cost.
3. Record a pre-creation inventory showing no project VM, disk, reserved IP, or
   project firewall resource in the approved scope.
4. Create project-specific network controls with default-deny behavior.
5. Create only the approved SSH access rule, restricted to the approved source.
6. Create one `e2-standard-4` VM with Ubuntu 24.04 LTS and one 100 GB Balanced
   Persistent Disk.
7. Attach only the approved ephemeral IPv4 or alternative access path.
8. Apply the approved non-secret labels.
9. Verify the provider reports the exact approved machine, disk, image,
   network, firewall, and IP inventory.
10. Establish SSH host-key trust through a separately observed fingerprint.
11. Run only the repository's read-only remote prerequisite checker.
12. Record CPU, memory, disk, architecture, swap, time synchronization,
    listeners, firewall state, and current cost estimate.
13. Stop. Request Gate 3 approval before installing Docker.

No broad firewall source, password SSH, root login, startup script, package
installation, Docker action, repository credential, or application secret is
allowed in Gate 2.

## Acceptance criteria

Gate 2 succeeds only if:

- the created inventory exactly equals the approved manifest;
- the VM reports at least 4 vCPU, 16 GB RAM, and 50 GB usable disk;
- Ubuntu 24.04 LTS and x86_64 are confirmed;
- administrative access works through the approved restricted path;
- no internal DataHub, MCP, database, Kafka, search, Docker, backend, or
  frontend port is public;
- no unapproved resource exists;
- the current estimate remains inside the approved credit guardrail;
- no paid conversion or billing change occurred;
- the remote prerequisite checker passes its Gate 2 host checks; and
- no package or application has been installed.

Failure of any criterion is a Gate 2 failure, not a partial success.

## Failure and rollback boundary

- Stop immediately on a manifest mismatch, quota failure, unexpected charge,
  broad firewall exposure, architecture mismatch, or insufficient resources.
- Do not resize, add disks, reserve another IP, change regions, or broaden
  firewall rules without a new approval.
- Capture only redacted, project-scoped diagnostics.
- Do not delete or alter unrelated provider resources.
- Cleanup may target only the exact Gate 2 resources, and destructive cleanup
  requires explicit confirmation of those resolved resource identifiers.
- After approved cleanup, verify that VM, disk, IP, firewall, snapshot, and
  logging charges have stopped or identify any retained billable item.

## Gate 2 approval request template

```text
Provider: Google Cloud Free Trial
Paid conversion still unaccepted:
Remaining credit and expiry:
Project verified outside Git:
Region:
Zone:
Machine: e2-standard-4
Architecture:
Image:
Disk type/size/delete policy:
External access route:
Firewall rules and source ranges:
SSH key boundary:
Resource names and labels:
Quota evidence:
Itemized hourly/daily/30-day estimate:
Budget threshold:
Teardown date:
Rollback targets:
No existing resource conflict:
Explicit approval to create exactly this manifest: yes / no
```

An affirmative answer is valid only when every preceding field is complete.
Approval of Gate 2 does not approve Gate 3 Docker installation.
