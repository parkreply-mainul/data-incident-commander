# Sprint 8C Live Runtime Plan

## Purpose and current state

Sprint 8C will establish the first real DataHub-backed vertical slice. Gate 1
is complete, but Gate 2 and every later external action remain unapproved. As
of 2026-07-24:

- Google Cloud Free Trial is active with €256.52 remaining;
- a project with display name `DataIncidentCommander` exists;
- paid conversion has not been accepted;
- no VM or infrastructure resource has been created or started;
- no remote Docker installation has occurred;
- DataHub has not been started;
- MCP and Agent Context Kit have not been installed;
- no LLM credential has been supplied; and
- mutation remains disabled.

Every gate below requires its own explicit approval where it changes external
state, incurs cost, handles a credential, or enables mutation.

## Runtime target

Primary topology remains a remote single VM. Gate 1B selected the available
Google Cloud `e2-standard-4` candidate with Ubuntu 24.04 LTS and 100 GB
Balanced Persistent Disk. OVHcloud's Public Cloud trial remains the free
fallback, and paid OVHcloud B3-16 remains the last resort. AWS is not
recommended for the preferred runtime. No candidate is provisioned, and this
is not a claimed formal production minimum. See
[SPRINT_8C_GATE_1_DECISION.md](SPRINT_8C_GATE_1_DECISION.md).

The free route is investigated first, but not assumed:

1. verify official provider trial/credit terms, eligibility, region, required
   payment method, expiry, billable IPv4/storage/egress, and quota;
2. confirm the offer supports the full minimum VM for the required period;
3. reject any “free” option that weakens memory, availability, public access,
   deletion control, or judging reliability;
4. request approval before account creation; and
5. request separate approval before resource creation even when credits cover
   the quoted price.

If no reliable free-credit route exists, return to the already documented
OVHcloud/Hetzner paid decision and its $175-before-tax maximum guardrail.

## Approval gates

| Gate | Action | Evidence required before approval |
|---|---|---|
| 1A | Read official offers and manually inspect any already accessible console without creating an account or activating a trial | Dated URLs, eligible SKU/region, quota, expiry, all residual costs |
| 1B | Create or use a provider account and complete trial-eligibility verification | Explicit user approval of the provider, account use or creation, identity/payment verification, trial activation, and terms |
| 2 | Provision infrastructure | Exact region, SKU, disk, IP, firewall, hourly estimate, maximum budget |
| 3 | Install Docker on the VM | Supported Ubuntu release, prerequisite pass, official-repository plan |
| 4 | Pull/start DataHub v1.6.0 | Resolved configuration, ports, images/digests, rollback, fresh capacity pass |
| 5 | Load the NYC Taxi scenario | Licensed source, ingestion plan, exact synthetic metadata to plant |
| 6 | Install/start MCP read-only | Exact package/version, transport, private binding, token scope |
| 7 | Supply an LLM credential | Provider, model, purpose, spend cap, retention terms; optional for deterministic path |
| 8 | Enable mutation | Exact tool, scope, test asset, approved payload, rollback/read-back plan |
| 9 | Expose judge application | HTTPS, authentication/access instructions, firewall, availability window |
| 10 | Teardown | Exact resources, backup decision, credential rotation, billing verification |

Approval of one gate does not imply approval of the next.

Gate 1A never authorizes account creation, trial activation, billing-account
creation, payment acceptance, provider terms acceptance, or resource creation.
Each of those account or eligibility actions requires explicit Gate 1B
approval. Gate 1B does not authorize a VM, disk, IP, firewall, or other cloud
resource; those always require separate Gate 2 approval.

## Checkpoint sequence

### 1. Free-account and cost verification — complete

- Recheck provider offers from official sources on the execution date.
- Prefer credits that cover the required VM without a weaker SKU.
- Record tax, IPv4, storage, snapshot, egress, and powered-off billing.
- Do not request credentials or payment data in the repository.

**Exit achieved:** Google Cloud Free Trial and a suitable candidate are
verified. No infrastructure exists. See the Gate 1 closure record.

### 2. Infrastructure creation

- Follow
  [SPRINT_8C_GATE_2_IMPLEMENTATION_PLAN.md](SPRINT_8C_GATE_2_IMPLEMENTATION_PLAN.md).
- Provision only the approved Ubuntu LTS VM, disk, IPv4, SSH key, and
  default-deny cloud firewall.
- Record provider resource identifiers outside Git.
- Run the read-only remote prerequisite checker.
- Abort if CPU, memory, disk, architecture, time sync, listeners, or access
  controls fail.

**Exit:** the empty host passes 4-vCPU/16-GB/50-GB gates.

### 3. Docker installation

- Use only the reviewed repository-local
  `deploy/scripts/install_docker_ubuntu.sh` installer. It implements Docker's
  official Ubuntu apt-repository procedure with project-specific safety checks
  and pinning. Do not replace it with `get.docker.com` or another convenience
  installer.
- Do not expose the daemon or grant docker-group access implicitly.
- Record Engine and Compose versions.
- Rerun prerequisites and inspect listeners.

**Exit:** Docker is healthy; no DataHub image has been pulled.

### 4. DataHub startup

- Resolve and review the pinned DataHub v1.6.0 deployment.
- Capture service inventory, images, tags, digests, ports, volumes, and health
  checks.
- Pull only after approval and start only the project-scoped stack.
- Wait for exact inventory and verified service health.
- Keep GMS, databases, Kafka, search, and Docker private.

**Exit:** DataHub UI and GMS health are verified through approved paths and
resource use is within bounds.

### 5. NYC Taxi sample metadata

- Select a license-compatible NYC Taxi data source.
- Define the smallest metadata-only graph needed for the golden scenario.
- Ingest assets, lineage, ownership, dashboard/derived impact, quality or
  freshness evidence, and one prior incident representation.
- Plant the stale/failed upstream condition explicitly.
- Record the actual URNs and graph from DataHub after ingestion; do not derive
  acceptance names from this planning document.

**Exit:** a human can inspect the planted condition and graph in DataHub.

### 6. MCP installation and inventory

- Select and pin the official self-hosted MCP release compatible with the
  observed environment.
- Bind it privately and authenticate with a least-privilege token.
- Start with mutation disabled.
- Record server version, transport, health, complete tool inventory, schemas,
  read-only/destructive hints, and errors.
- Compare runtime tools with the documented capability model.

**Exit:** required read tools are observed and version-consistent; mutation is
still off.

### 7. First read-only investigation

Run each step separately before end-to-end orchestration:

1. asset search and unambiguous identifier resolution;
2. upstream lineage;
3. downstream lineage and exact paths;
4. freshness or quality evidence;
5. ownership/domain context;
6. deterministic blast radius;
7. deterministic severity and separate confidence;
8. Evidence Ledger receipt capture; and
9. application/UI investigation with dependency disconnect testing.

For every operation retain the operation name, sanitized request identity,
retrieval time, runtime version, evidence identifiers, and normalized result.
Do not retain tokens or unsafe raw payloads.

**Exit:** the application investigates the planted incident through MCP, and
fails visibly when MCP is disconnected.

### 8. Human-approved write and read-back

This is a separate mutation checkpoint:

- select one non-destructive, idempotent incident-memory representation;
- capture the exact tool and input schema;
- enable only the required mutation under explicit approval;
- present the normalized payload, actor, reason, and binding digest;
- execute once;
- capture the mutation receipt;
- retrieve the persisted value through a verified read path;
- compare normalized persisted and approved payloads;
- record previous-incident memory only after equivalence succeeds; and
- disable mutation again after the test if operationally supported.

Never use the starter's pattern of handing every mutation tool directly to an
LLM. Failed or partial writes remain failures.

### 9. Judging availability

- Deploy the reviewed backend/frontend build behind HTTPS.
- Expose only the application boundary.
- Provide free judge access for the official judging period.
- Run scheduled health and golden-scenario checks.
- Freeze versions and avoid upgrades.
- Keep a redacted recovery runbook and budget alerts.

The official rules currently state a submission deadline of August 10, 2026 at
5:00 pm Eastern, judging from August 17 through August 31, and free project
access through judging. Recheck immediately before deployment.

### 10. Cleanup and cost control

- Stop mutation first.
- Preserve only approved, secret-free evidence receipts.
- Rotate/revoke DataHub, MCP, LLM, SSH, and provider credentials.
- Delete exact project resources only with explicit teardown approval.
- Verify snapshots, disks, IPs, DNS, and other separately billed items are gone.
- Confirm the final provider invoice/balance.

No Docker prune, broad deletion, or implicit account removal is permitted.

## LLM decision

An LLM is required by the starter's LangGraph loop, not by DataIncident
Commander's deterministic investigation path. Sprint 8C should reach the first
read-only MCP investigation without an LLM. Any model credential is a separate
optional gate for evidence-backed remediation wording and must not control
severity, approval, or mutation.

## Go/no-go outcome

Sprint 8C is a **GO** only when the user separately approves the relevant
external actions and each preceding exit criterion passes. It is a **NO-GO**
if resource, cost, security, tool, normalization, approval, or read-back
evidence is insufficient. Planning completion alone never authorizes startup.
