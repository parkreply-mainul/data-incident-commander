# Architecture

## Status and verification boundary

Sprint 5 implements the normalized deterministic domain core. Sprint 6 adds
the FastAPI transport boundary, application service ports, and a one-process
in-memory repository. DataHub/MCP adapters, durable persistence, write-back,
and frontend remain planned. No DataHub API name, MCP tool,
mutation capability, asset name, metadata field, or dataset graph shape is
confirmed here. DataHub behavior must be verified against official
documentation and the actual running DataHub OSS and MCP tool inventory before
adapter implementation.

## Architectural objectives

DataIncident Commander must:

- perform real runtime investigation through DataHub OSS and verified DataHub
  MCP Server operations;
- preserve evidence provenance from tool response to UI claim;
- separate deterministic calculations from generative recommendations;
- expose confidence, knowns, unknowns, conflicts, and partial results;
- place a human approval gate before mutation;
- verify persisted data through read-back comparison;
- retrieve previous incident memory; and
- provide a professional desktop UI without masking dependency failures.

## System context

```text
Human responder
      |
      v
React + TypeScript + Vite desktop UI
      |
      v
FastAPI + Pydantic backend
      |
      +--> Investigation engine and deterministic decision services
      |
      +--> Verified DataHub integration boundary
                    |
                    v
            DataHub MCP Server
                    |
                    v
               DataHub OSS
```

## Selected runtime topology

Sprint 4C evaluated, rather than assumed, the proposed remote direction. The
selected primary judging topology is one remote Linux VM:

```text
Judge browser
      |
  HTTPS application boundary
      |
React frontend
      |
FastAPI backend
      |
DataHub MCP Server
      |
DataHub OSS v1.6.0
```

Frontend, backend, MCP, and DataHub are co-located on private host/container
networks; only the application HTTPS boundary is intended to be public. The
backup development topology keeps DataHub OSS and MCP remote while running the
backend/frontend locally.

This is a selected architecture direction, not a deployed or runtime-verified
system. MCP transport, authentication, ports, mutation capability, reverse
proxy, and application deployment remain subject to their verification gates.
Local DataHub startup on the 8 GB Mac remains blocked. See
[RUNTIME_STRATEGY.md](RUNTIME_STRATEGY.md) and
[REMOTE_RUNTIME_SECURITY.md](REMOTE_RUNTIME_SECURITY.md).

The read and investigation path must use the required approved DataHub
technology. DataHub OSS is authoritative for retrieved catalog and operational
metadata. The application is authoritative only for its versioned
calculations, recorded investigation, and clearly labeled recommendations.

## Real-work runtime boundary

Golden-demo evidence must originate from a running DataHub OSS instance through
verified MCP operations. Every runtime evidence item must carry enough
provenance to demonstrate that origin. The application must report a
disconnected or unavailable state if DataHub or MCP cannot be reached.

Fixtures and fake adapters may support isolated automated tests only. A fixture,
chatbot response, hard-coded answer, precomputed output, or screenshot cannot
be used as the live demo path. The application must never simulate successful
DataHub reads, mutations, or read-back verification.

## Primary golden scenario

The **NYC Taxi planted freshness incident** provides the primary vertical slice.
A synthetic metadata scenario will plant a stale or failed upstream dataset
condition in DataHub OSS. The application will discover the relevant asset,
trace upstream and downstream lineage, retrieve freshness or quality and
ownership evidence, identify affected dashboards or other derived assets,
calculate blast radius and deterministic severity, calculate separate
confidence, retrieve relevant previous incidents, propose evidence-linked
remediation, and enter the human-controlled persistence flow.

Expected asset names, metadata fields, owners, graph shape, and the incident
record representation remain subject to validation during the DataHub dataset
and MCP capability spikes.

## Backend components

### Implemented normalized domain core

`src/data_incident_commander/domain/` now provides strict Pydantic contracts
and pure deterministic services for evidence, findings, lineage traversal,
blast radius, severity rubric v1, confidence, remediation descriptions, human
approval transitions, incident reports, and identifier-based incident-memory
matching.

The core depends only on normalized internal values. It does not import
FastAPI, DataHub, MCP, frontend code, or an LLM. Future verified adapters own
all translation from actual external payloads. See
[DOMAIN_CONTRACTS.md](DOMAIN_CONTRACTS.md).

### FastAPI application boundary

Sprint 6 exposes typed local HTTP endpoints for application health, explicit
readiness, draft creation/retrieval/listing, investigation orchestration, and
guarded workflow transitions. Transport contracts are separate from domain
models. The application service depends on repository, evidence-provider, ID,
and clock protocols rather than FastAPI or concrete integrations.

The default evidence provider is unconfigured and returns dependency
unavailable without changing the draft. Durable persistence, streaming,
read-back, recent incidents, and incident-memory endpoints remain planned.
The service performs a DRAFT-only state preflight before provider invocation.
In-memory persistence uses lock-protected optimistic revisions so concurrent
state changes cannot overwrite audit history. Injected providers describe
DataHub, MCP, and write-back capabilities without readiness network calls.

### Incident intake and asset resolver

Intake validates the incident signal, optional asset hints, observation time,
and traversal budgets. Asset resolution queries live DataHub metadata, ranks
candidates transparently, and requires disambiguation when confidence in the
identity is insufficient.

### Investigation orchestrator

The orchestrator runs a bounded evidence-gathering sequence and records its
timeline. It enforces lineage depth, node, tool-call, and elapsed-time limits,
preserves partial evidence, and reports tool failures.

### Verified DataHub integration boundary

A narrow adapter will be designed only after verified MCP capability discovery.
Required read behaviors include:

- asset discovery and lookup;
- upstream lineage retrieval;
- downstream lineage retrieval;
- ownership and domain retrieval;
- freshness or quality evidence retrieval; and
- previous incident retrieval.

These are required behaviors, not claims about current MCP tool names or
schemas. The adapter must preserve source identifiers, timestamps, tool
provenance, and errors.

### Evidence Ledger

Each planned evidence item contains:

- stable evidence identifier;
- evidence type and subject asset identifier;
- observed value and classification;
- DataHub/MCP provenance;
- source and retrieval timestamps when available;
- freshness or validity status;
- safe raw-response reference where appropriate;
- known, derived, hypothesis, or unknown classification;
- conflicts, gaps, and warnings; and
- references to lineage paths or calculations that use it.

Confirmed findings require evidence references. Derived findings require input
evidence and a calculation rule. Hypotheses and unknowns cannot be rendered as
observed facts.

### Lineage and blast-radius service

The service maintains separate upstream and downstream traversals, handles
cycles, and records truncation. Blast radius is a deterministic result derived
from retrieved downstream paths within configured bounds. Its contract will
include affected asset identifiers, affected dashboards or derived assets,
path evidence, counts by asset class when verified metadata permits, traversal
limits, excluded or unknown scope, and calculation version.

The UI must never imply that a bounded graph is complete when traversal was
truncated or evidence is missing.

### Severity engine

Severity is a deterministic, versioned measure of impact and urgency. Candidate
inputs, subject to the dataset spike, include verified blast radius, asset
criticality, freshness breach magnitude or duration, quality failures, and
production context. The output contains input evidence references, factor
contributions, final score, band, and rule version.

### Confidence engine

Confidence is separate from severity. It ranges from **0.0 to 1.0** and
represents evidence coverage and consistency—not model certainty. Missing,
stale, or conflicting evidence lowers confidence. Low confidence must block
overconfident root-cause language and promote unresolved questions. The output
contains the score, coverage factors, conflicts, unknowns, and calculation
version.

### Remediation generator

The generator receives only the incident signal, Evidence Ledger, lineage and
blast-radius result, severity, confidence, and relevant incident memory.
Factual premises require evidence references. Advice requiring verification is
labeled as a hypothesis or next diagnostic action. It cannot execute
remediation.

### Previous incident memory service

The memory service retrieves relevant persisted incidents through a verified
DataHub read path, preserves their provenance, and explains why they are
relevant. Previous recommendations are historical evidence, not automatically
correct instructions. Unverified or unavailable memory is reported as unknown.

### Human approval and incident recorder

The backend owns an explicit state machine:

```text
Draft investigation
  → human review
  → explicit approval
  → write-back
  → read-back
  → payload verification
  → recorded incident memory
```

Only a human-approved, validated payload may progress to write-back. Approval
records the reviewed payload identity and approval time. Any material payload
change invalidates prior approval.

### Planned write path

Write-back is planned, not confirmed, and is subject to verification of
supported DataHub MCP mutation capabilities against official documentation and
the actual running tool inventory.

1. Prefer a verified MCP mutation tool.
2. If MCP exposes no appropriate mutation, document and use an officially
   supported DataHub write API or SDK only if hackathon rules permit.
3. Keep the required approved DataHub technology on the read/investigation path.
4. Never simulate a successful mutation.
5. Disclose the actual verified write path in the final architecture.

Following persistence, the application must retrieve the record through a
verified read path and compare normalized material fields with the exact
human-approved payload. Only an equivalent result may transition to recorded
incident memory. Mismatch, partial write, or unavailable read-back is a visible
failure state.

## Frontend architecture

The React, TypeScript, and Vite frontend is a professional desktop-oriented
investigation workspace. Planned views and components are:

- investigation input;
- live investigation timeline;
- severity and root-cause summary;
- visual upstream/downstream lineage graph;
- blast-radius view;
- Evidence Ledger;
- confidence and known/unknown panel;
- owners and domains;
- remediation plan;
- human approval controls;
- write-back/read-back status;
- previous incident memory;
- recent incidents; and
- empty, loading, partial, error, disconnected, success, and resolved states.

The frontend consumes typed backend contracts. It does not call DataHub
directly and does not infer success from client state. Lineage visualization
must identify direction, selected asset, affected assets, evidence gaps,
truncation, and unavailable details. Approval controls must show the payload and
disable approval when required evidence or write capability is unavailable.

Real functionality comes before visual polish. A dedicated professional UI
phase remains required, including responsive desktop layout, accessible
interaction, readable evidence density, consistent operational states, and
submission-quality visual design.

## End-to-end investigation flow

1. Accept and validate the incident signal.
2. Resolve the target asset through live DataHub/MCP evidence.
3. Traverse bounded upstream lineage.
4. Traverse bounded downstream lineage.
5. Retrieve freshness or quality, ownership, and domain evidence.
6. Calculate blast radius from retrieved downstream paths.
7. Assemble the Evidence Ledger and separate knowns from unknowns.
8. Calculate deterministic severity.
9. Calculate separate confidence and evidence coverage.
10. Retrieve relevant previous incident memory.
11. Generate evidence-backed remediation.
12. Render the draft and live timeline in the desktop UI.
13. Obtain human review and explicit approval.
14. Invoke the verified, permitted write path.
15. Read the persisted representation back.
16. Compare it with the approved payload.
17. Record the verified result as incident memory.

## Security, trust, and privacy boundaries

- Treat incident text, catalog metadata, and previous incident text as
  untrusted input.
- Prevent metadata from redefining instructions or permissions.
- Allowlist verified MCP operations.
- Enforce traversal, time, and tool-call budgets.
- Keep mutation disabled unless verified, configured, and human-approved.
- Validate all API and persistence contracts.
- Use stable keys for idempotency and partial-write recovery.
- Do not retrieve underlying data rows when metadata is sufficient.
- Redact credentials and sensitive values from logs and UI errors.
- Use synthetic public-safe demo metadata only.

## One-command operational architecture

The future Makefile will delegate to modular, auditable scripts:

```text
scripts/check_prerequisites.sh
scripts/setup_environment.sh
scripts/start_datahub.sh
scripts/load_sample_data.sh
scripts/start_mcp.sh
scripts/start_backend.sh
scripts/start_frontend.sh
scripts/run_smoke_test.sh
scripts/demo_check.sh
scripts/submission_check.sh
scripts/stop_all.sh
```

Eventually, `make demo` must prepare the full environment, validate health, load
the planted NYC Taxi scenario, start the verified MCP path, backend, and
frontend, run smoke validation, and print URLs. These scripts remain
unimplemented in Sprint 1B; current Makefile targets print placeholders only.

## Decisions still requiring verification

- supported DataHub OSS and MCP Server versions;
- NYC Taxi asset names, metadata representation, and exact lineage graph;
- official dataset loading approach;
- actual MCP tools, schemas, authentication, and error behavior;
- whether an appropriate MCP mutation exists;
- hackathon permission for a fallback official DataHub API or SDK;
- incident record representation and previous-memory query;
- deterministic severity rubric and asset criticality source;
- normalized equivalence rules for read-back;
- model provider and structured-output strategy;
- API transport for the live timeline;
- graph visualization library;
- default traversal, timeout, retry, and retention limits; and
- exact dependency versions and licenses.
