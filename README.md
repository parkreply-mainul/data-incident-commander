# DataIncident Commander

DataIncident Commander is an evidence-grounded incident investigation
application planned exclusively for the DataHub Agent Hackathon in the
**Agents That Do Real Work** category. It must use a running **DataHub OSS**
instance and verified **DataHub MCP Server** operations to investigate real
metadata at runtime.

> **Status:** Sprint 1B is documentation and repository foundation only. The
> application, integrations, scripts, UI, and write-back are not implemented.

## Project vision

Turn a vague data incident signal into a traceable, actionable incident record.
Responders should be able to inspect the affected assets, lineage, owners,
freshness and quality signals, blast radius, severity calculation, confidence,
unknowns, proposed remediation, and history behind every conclusion.

## Problem statement

Incident responders often correlate catalog search, lineage, ownership,
freshness, quality, and previous incident knowledge manually. That work is slow
and difficult to audit. A conversational metadata summary is not enough:
DataIncident Commander must perform bounded DataHub-backed investigation,
expose its evidence, and support a human-controlled incident lifecycle.

## Real-work guarantee

Runtime evidence used by the product and golden demo must originate from a
running DataHub OSS instance through verified DataHub MCP operations. A
fixture-only, chatbot-only, hard-coded, precomputed, or screenshot-only demo
does not satisfy project acceptance criteria.

The demo must visibly fail or report unavailable dependencies when DataHub or
the MCP Server is unavailable. Fixtures are permitted only for isolated
automated tests; they cannot stand in for the live integration demonstration.
No successful DataHub read, write, or verification may be simulated.

## Primary golden scenario: NYC Taxi planted freshness incident

The golden demo will load a synthetic NYC Taxi metadata scenario into DataHub
OSS and plant a stale or failed upstream dataset freshness condition. The
application will:

1. resolve the reported asset against live DataHub metadata;
2. traverse and display its relevant upstream and downstream lineage;
3. retrieve freshness or quality evidence and ownership metadata;
4. identify affected dashboards or other derived assets;
5. calculate a bounded blast radius from retrieved lineage;
6. calculate deterministic severity separately from confidence;
7. distinguish confirmed findings, derived findings, hypotheses, and unknowns;
8. retrieve relevant previous incident memory;
9. propose evidence-backed remediation;
10. present the draft investigation for human review and explicit approval;
11. perform planned write-back only through a verified, permitted write path;
12. read the persisted record back and compare it with the approved payload; and
13. expose the verified record as incident memory for future investigations.

Exact DataHub asset names, metadata fields, incident representation, and graph
shape are intentionally not invented here. They are subject to validation
during the DataHub dataset and MCP capability spikes.

## MVP scope and workflow

The planned MVP includes:

- asset resolution with ambiguity handling;
- bounded upstream lineage traversal;
- bounded downstream lineage traversal;
- blast-radius calculation with supporting paths;
- freshness and quality evidence retrieval;
- ownership and domain retrieval;
- a provenance-preserving Evidence Ledger;
- deterministic, versioned severity;
- confidence and evidence-coverage calculation;
- explicit known-versus-unknown separation;
- evidence-backed remediation;
- previous incident retrieval and memory;
- professional desktop investigation UI;
- human review and explicit approval;
- planned DataHub write-back, subject to verification; and
- persisted-payload read-back and equivalence verification.

The human-controlled state flow is:

```text
Draft investigation
  → human review
  → explicit approval
  → write-back
  → read-back
  → payload verification
  → recorded incident memory
```

The MVP will not modify source data, execute remediation, contact owners, or
silently select ambiguous assets.

## Evidence, severity, and confidence

The Evidence Ledger will preserve evidence identifiers, asset identifiers,
sources, observation and retrieval times, raw-response references when safe,
and conflicts or warnings. Confirmed findings require evidence references.
Derived findings must identify their evidence and deterministic calculation.
Hypotheses and unknowns must remain visibly separate.

Severity measures incident impact and urgency through deterministic, versioned
rules. Confidence is a separate value from **0.0 to 1.0** representing evidence
coverage and consistency—not model certainty. Missing or conflicting evidence
lowers confidence. Low confidence must prevent overconfident root-cause claims,
even when deterministic severity is high. The UI must display confidence,
coverage, and unknowns.

## Architecture overview

The planned application has three major parts:

- a Python backend for investigation orchestration, typed contracts, evidence,
  severity, memory, and the HTTP API;
- a React desktop UI for investigation, lineage, blast radius, approval,
  persistence verification, and incident history; and
- a verified integration boundary to DataHub OSS through the DataHub MCP
  Server, with mutation handled only as described below.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for component and trust
boundaries.

## Intended technology stack

### Backend

- Python
- FastAPI
- Pydantic
- pytest

### Frontend

- React
- TypeScript
- Vite

### Integration

- DataHub OSS
- DataHub MCP Server

Dependencies and versions will be selected only after environment and
capability validation. None are installed or declared in Sprint 1B.

## Professional desktop UI

The dedicated desktop UI phase will provide:

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

Real investigation functionality comes before visual polish. Professional visual
quality, usable information hierarchy, accessibility, and complete operational
states are nevertheless required project phases and submission criteria.

## Planned DataHub write path

Write-back is planned, not confirmed. It is subject to verification of supported
DataHub MCP mutation capabilities against official documentation and the actual
running tool inventory.

The project will:

1. prefer a verified MCP mutation tool;
2. if MCP exposes no appropriate mutation, document and use an officially
   supported DataHub write API or SDK only if hackathon rules permit it;
3. continue to use the required approved DataHub technology for the read and
   investigation path;
4. never simulate successful write-back; and
5. disclose the actual verified write path in the final architecture.

## One-command experience

The eventual `make demo` command will orchestrate modular scripts to check
prerequisites, prepare the complete demo environment, validate health, load the
planted NYC Taxi scenario, start MCP, backend, and frontend services, run smoke
validation, and print usable URLs.

Planned scripts, not implemented in Sprint 1B:

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

The current Makefile targets are safe placeholders that print messages only.

## Repository structure

```text
.
├── PROJECT_CHARTER.md
├── README.md
├── docs/
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── TEST_STRATEGY.md
├── examples/                         # Future sample incident inputs
├── scripts/                          # Future modular automation scripts
├── src/
│   └── data_incident_commander/
│       ├── agent/                    # Future orchestration
│       ├── domain/                   # Future evidence and decision contracts
│       └── integrations/datahub/     # Future verified DataHub integration
└── tests/
    ├── fixtures/                     # Isolated-test fixtures only
    ├── integration/                  # Future real integration tests
    └── unit/                         # Future deterministic tests
```

Empty directories remain intentionally untracked; no `.gitkeep` files are
needed for Sprint 1B.

## Development principles

- Runtime evidence before conclusions.
- Provenance and timestamps by default.
- Deterministic severity, separate from evidence confidence.
- Visible knowns, unknowns, conflicts, and partial results.
- Bounded lineage traversal and allowlisted tool operations.
- Human approval before any incident mutation.
- Read-back equivalence verification after persistence.
- No simulated integration success.
- Synthetic, public-safe demo metadata only.
- Real functionality before visual polish, with professional UI quality still
  required for submission.

## Project independence

This repository is completely independent:

- Do not access ParkReply code.
- Do not access SafeRelay code.
- Do not access PIC code.
- Do not copy, import, adapt, reference, or use any of them as hidden
  dependencies, implementation sources, fixtures, or demo data.

Only material created for this repository or appropriately licensed public
dependencies may be used.

## Placeholder commands

```bash
make setup
make start
make seed
make test
make smoke
make demo
make demo-check
make submission-check
make stop
```

## Documentation

- [Project charter](PROJECT_CHARTER.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [Test strategy](docs/TEST_STRATEGY.md)

## License

DataIncident Commander is intended for public release under the
[Apache License 2.0](LICENSE). Credentials, private operational metadata, and
incompatibly licensed material must never be committed.
