# Data Incident Commander

## Category

**DataHub Agent Hackathon — Agents That Do Real Work**

## Problem

A freshness incident rarely stops at one table. Responders must correlate
catalog identity, ownership, freshness and quality signals, upstream causes,
downstream consumers, and previous incidents. Manual correlation is slow and
difficult to audit, while unconstrained automation can write misleading
metadata before a responder reviews its evidence.

## Solution

Data Incident Commander (DIC) converts one incident report into a bounded,
evidence-grounded response record. It retrieves live DataHub evidence through
mandatory MCP operations, calculates blast radius, deterministic severity, and
evidence confidence, recommends remediation, requires explicit approval, then
performs and independently verifies one controlled DataHub write-back.

## Technical architecture

```text
React/Vite judge UI
  → FastAPI API and application service
    → strict Pydantic contracts
    → deterministic state, lineage, blast-radius, severity, and confidence
    → in-process incident repository
    → DataHubMcpEvidenceProvider
      → verified standalone DataHub MCP Server
        → DataHub OSS v1.6.0
    → approval-gated write adapter
      → DataHub read-back verification
```

DataHub is authoritative for metadata evidence. DIC is authoritative for its
versioned calculations, approval history, recommendations, and incident state.
An LLM is not required for scoring or mutation authority.

## DataHub usage

DIC uses DataHub for:

- canonical asset resolution;
- dataset properties and identifiers;
- technical ownership;
- freshness and quality context;
- upstream/downstream lineage;
- downstream impact evidence;
- the controlled incident tag; and
- read-back proof from the persisted `globalTags` aspect.

The live runtime is pinned to DataHub OSS v1.6.0. The small NYC Taxi fixture
exists only to make the judge scenario reproducible.

## MCP usage

MCP is mandatory for the read and investigation path. The repository contains
a typed, library-neutral `DataHubMcpEvidenceProvider`, an observed-capability
inventory, a client protocol, strict verified DTOs, and normalizers. The
provider remains unavailable until the running MCP release, tool inventory,
schemas, and required read-only operations have been observed.

Direct GMS is secondary and cannot claim MCP-origin evidence. It is retained as
a minimal fixture and controlled write/read-back candidate if the verified MCP
mutation is unavailable or unsuitable and the fallback is approved.

## Human approval and safety

- All dependencies fail closed.
- Ambiguous asset search is rejected.
- Lineage traversal has depth and node limits.
- Severity and confidence are deterministic and separate.
- Confirmed findings require evidence references.
- Mutation is disabled by default.
- Approval binds the exact report using SHA-256.
- Only the approved workflow state can invoke write-back.
- A successful mutation is not enough: DataHub must return the expected tag.
- A mismatch does not reach `RECORDED`.
- DIC never changes source data or executes the recommended remediation.

## NYC Taxi freshness scenario

The planted incident starts at:

`urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_trips_raw,PROD)`

Its lineage is:

```text
NYC Taxi Trips Raw — stale
  → NYC Taxi Daily Metrics
    → NYC Taxi Operations Dashboard
```

DIC confirms the freshness signal, identifies technical ownership, finds the
affected model and critical dashboard, calculates severity and confidence,
and recommends restoring and rerunning the delayed NYC Taxi ingestion. The
operator then submits the exact report for review, a human approves its
binding, and DIC writes and reads back `dic-incident-recorded`.

## What is implemented

- Strict incident, evidence, lineage, remediation, memory, and transport models.
- Cycle-safe bounded lineage and blast-radius calculation.
- Versioned deterministic severity and evidence-confidence models.
- Approval-state machine and optimistic in-memory repository.
- FastAPI intake, investigation, approval, write-back, retry, and readiness APIs.
- React UI for intake, evidence, impact, scoring, approval, and proof.
- Environment-backed secret references and mutation-off defaults.
- Minimal NYC Taxi metadata fixture.
- Direct-GMS integration candidate with tag read-back verification.
- Focused unit, application, API, DataHub integration, frontend, and deployment tests.

The final live MCP tool schemas and compatibility are intentionally not claimed
until observed on the approved VM.

## Intentionally out of scope

- Source-data mutation or pipeline execution.
- Automatic remediation.
- Owner notification.
- A general-purpose agent platform.
- A new database or connector framework.
- Unbounded lineage traversal.
- Silent resolution of ambiguous assets.
- Unconstrained LLM tool selection.
- Cloud provisioning or deployment from this repository review.

## Reproducibility

Local validation:

```bash
make check
make setup
make test
make integration-test
make frontend-test
make frontend-build
make remote-check
```

Local fail-closed UI:

```bash
# Terminal 1
make api API_HOST=127.0.0.1 API_PORT=8000

# Terminal 2
make frontend FRONTEND_PORT=5173
```

Approved VM, after credentials and MCP version/inventory are verified:

```bash
cd /opt/data-incident-commander
export DIC_GMS_URL=http://127.0.0.1:8080
export DIC_GMS_TOKEN_ENV=DATAHUB_GMS_TOKEN
export DATAHUB_GMS_TOKEN='<runtime-secret>'
datahub ingest -c demo/nyc_taxi_recipe.yml
make remote-verify REMOTE_ENV=/secure/path/dic-remote.env
make integration-test

# Terminal 1
make api API_HOST=127.0.0.1 API_PORT=8000

# Terminal 2
make frontend FRONTEND_PORT=5173
```

The separate mutation checkpoint stops the API, sets
`DIC_DATAHUB_MUTATION_ENABLED=true` only for the approved rehearsal, and then
restarts the API.

## Expected judge walkthrough

1. Verify DataHub v1.6.0, MCP, and application readiness.
2. Report the stale NYC Taxi raw dataset.
3. Inspect the evidence ledger and owner.
4. Explain lineage and downstream blast radius.
5. Compare deterministic severity with evidence confidence.
6. Read the remediation and its verification step.
7. Show that mutation is unavailable before approval.
8. Submit and approve the SHA-256-bound report.
9. Write the tag and show independent DataHub read-back.
10. End on `RECORDED` and verified in-process incident memory.

## Repository and license

This standalone repository contains only Data Incident Commander code,
fixtures, deployment checks, and documentation. It is licensed under Apache
License 2.0. Runtime credentials, private host details, and generated state are
excluded from source control.
