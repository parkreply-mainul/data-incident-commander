# Data Incident Commander

Data Incident Commander (DIC) is an evidence-grounded incident-response agent
for the DataHub Agent Hackathon, **Agents That Do Real Work** category.

> Runtime truth: the deterministic application, UI, approval workflow, test
> fixtures, and controlled direct-GMS write/read-back candidate are implemented.
> The golden demo remains fail-closed until the approved DataHub v1.6.0 VM
> supplies a runtime-verified standalone MCP version, inventory, and schemas.

## The 20-second problem

When a data product goes stale, responders manually jump between catalog
search, lineage, quality, ownership, and downstream consumers. The work is
slow, conclusions are hard to audit, and a rushed automation can mutate
metadata before a human understands what it will write.

## The 20-second solution

DIC turns one incident report into a traceable response record. It retrieves
live DataHub evidence through mandatory MCP operations, calculates bounded
blast radius, deterministic severity, and evidence confidence, recommends a
remediation, pauses for explicit human approval, performs one controlled
DataHub write-back, reads it back as proof, and records verified incident
memory.

## Golden demo: NYC Taxi freshness incident

```text
Report stale NYC Taxi raw trips
  → resolve the asset through DataHub MCP
  → collect metadata, ownership, freshness, quality, and lineage
  → calculate downstream blast radius
  → calculate deterministic severity and evidence confidence
  → recommend rerunning the delayed ingestion
  → submit the exact report for human review
  → approve its SHA-256 payload binding
  → write the incident tag through an approved DataHub operation
  → read globalTags back and verify the tag
  → transition to RECORDED and retain in-process incident memory
```

The small fixture contains three assets:

```text
NYC Taxi Trips Raw
  → NYC Taxi Daily Metrics
    → NYC Taxi Operations Dashboard
```

The raw asset carries a planted stale freshness signal. The derived model and
dashboard make impact visible without turning the demo into a data-loading
project.

## Why DataHub is essential

DataHub is the live system of record for asset identity, ownership, lineage,
freshness/quality context, and the final metadata tag. Without DataHub, DIC has
no evidence and refuses to invent a successful investigation. The demo is not
a chatbot over fixtures: its acceptance contract requires runtime evidence
from the pinned **DataHub OSS v1.6.0** instance.

## Why MCP is mandatory

The read/investigation path must use a runtime-verified standalone DataHub MCP
Server. The existing `DataHubMcpEvidenceProvider` and typed normalization
boundary fail closed until the actual server version, tool inventory, schemas,
and read-only capabilities are observed. Tool names or response fields are
never guessed.

Direct GMS is secondary. It is currently a minimal candidate for fixture
ingestion and the controlled tag write/read-back path; it does not replace MCP
as the evidence origin.

## Safety model

- **Fail closed:** missing, ambiguous, malformed, unavailable, or unverified
  evidence never becomes a successful investigation.
- **Deterministic decisions:** versioned rules calculate lineage traversal,
  blast radius, severity, and confidence independently of an LLM.
- **Evidence ledger:** every confirmed finding and recommendation refers to
  typed evidence with source operation and timestamps.
- **Human-controlled mutation:** write-back is disabled by default and cannot
  run before `INVESTIGATED → AWAITING_APPROVAL → APPROVED`.
- **Approval binding:** the reviewer approves the SHA-256 binding of the exact
  normalized report.
- **Read-back proof:** `RECORDED` is reached only after DataHub returns the
  expected tag; mismatch leaves the incident `APPROVED`.
- **No source-data remediation:** DIC recommends operational action but does
  not alter NYC Taxi data, run pipelines, or contact owners.

## Concise architecture

```text
React/Vite UI
  → FastAPI application service
    → typed incident state machine + in-memory repository
    → deterministic lineage / blast radius / severity / confidence engines
    → DataHubMcpEvidenceProvider (mandatory read evidence)
      → runtime-verified DataHub MCP Server
        → DataHub OSS v1.6.0
    → approval-gated DataHub mutation
      → independent read-back verification
```

The backend owns calculations and workflow state. DataHub owns catalog
evidence and persisted metadata. MCP is the mandatory read boundary. See
[Architecture](docs/ARCHITECTURE.md) and
[MCP adapter architecture](docs/MCP_ADAPTER_ARCHITECTURE.md).

## Local development and validation

Prerequisites: Python 3.11+, Node/npm, and repository-local dependencies.

```bash
make check
make setup
make test
make integration-test
make frontend-test
make frontend-build
make remote-check
```

Run the fail-closed local application in two terminals:

```bash
# Terminal 1
make api API_HOST=127.0.0.1 API_PORT=8000

# Terminal 2
make frontend FRONTEND_PORT=5173
```

Open `http://127.0.0.1:5173`. Draft intake works locally. Investigation remains
unavailable unless the required DataHub and verified MCP provider are connected.

## Approved-VM demo commands

These commands are documentation only. Do not run them until the VM, token,
MCP release, and mutation checkpoint have been separately approved.

```bash
cd /opt/data-incident-commander

export DIC_GMS_URL=http://127.0.0.1:8080
export DIC_GMS_TOKEN_ENV=DATAHUB_GMS_TOKEN
export DATAHUB_GMS_TOKEN='<runtime-secret>'

# Load only the small public demo metadata after approval.
datahub ingest -c demo/nyc_taxi_recipe.yml

# Verify the pinned DataHub runtime and deployment artifacts.
make remote-verify REMOTE_ENV=/secure/path/dic-remote.env
make integration-test

# Terminal 1: start the API after the verified MCP provider is configured.
make api API_HOST=127.0.0.1 API_PORT=8000

# Terminal 2: start the UI.
make frontend FRONTEND_PORT=5173
```

For the separately approved mutation rehearsal, stop the API process, enable
the narrow mutation configuration in the same shell, and restart it:

```bash
export DIC_DATAHUB_MUTATION_ENABLED=true
export DIC_DATAHUB_WRITEBACK_TAG_URN=urn:li:tag:dic-incident-recorded
make api API_HOST=127.0.0.1 API_PORT=8000
```

Expected effect: only the approved incident tag is associated with the target
demo dataset. Rollback: remove `dic-incident-recorded` from that dataset and
restart the API without `DIC_DATAHUB_MUTATION_ENABLED=true`.

## Judge walkthrough checklist

- [ ] DataHub reports v1.6.0 and the MCP inventory is visibly verified.
- [ ] Submit the NYC Taxi raw-dataset freshness incident.
- [ ] Show live asset, ownership, freshness, quality, and lineage evidence.
- [ ] Explain direct and transitive blast radius.
- [ ] Show deterministic severity separately from evidence confidence.
- [ ] Read the evidence-backed remediation.
- [ ] Demonstrate that write-back is unavailable before human approval.
- [ ] Submit and approve the exact payload binding.
- [ ] Perform the single controlled tag write.
- [ ] Show the read-back receipt and `RECORDED` state.
- [ ] Show the verified in-process incident-memory ending.
- [ ] Demonstrate fail-closed behavior if DataHub or MCP is unavailable.

## Submission material

- [Hackathon submission](docs/HACKATHON_SUBMISSION.md)
- [3–4 minute demo script](docs/DEMO_SCRIPT.md)
- [Screenshot plan](docs/SCREENSHOT_PLAN.md)
- [Project charter](PROJECT_CHARTER.md)
- [Test strategy](docs/TEST_STRATEGY.md)

## Scope and independence

DIC does not execute remediation, mutate source data, add a database, introduce
a general agent platform, or silently choose ambiguous assets. This repository
is standalone: it does not copy, import, adapt, reference, or use another
project as a hidden dependency, implementation source, fixture, or demo-data
source.

## License

Licensed under the [Apache License 2.0](LICENSE). Secrets, private operational
metadata, and generated runtime state must not be committed.
