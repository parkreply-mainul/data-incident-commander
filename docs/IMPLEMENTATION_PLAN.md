# Implementation Plan

## Delivery principles

Implementation proceeds in evidence-backed vertical slices. Real functionality
comes before visual polish, but professional UI quality is a required dedicated
phase and submission criterion. Runtime integration must never be replaced by
fixtures, hard-coded responses, precomputed results, or screenshots.

Write-back remains planned and unconfirmed until official documentation and the
actual MCP tool inventory are verified. No phase may simulate integration
success.

## Phase 0: repository foundation

**Goal:** Establish the public Apache 2.0 repository, scope, architecture,
quality strategy, safe configuration template, placeholder command contract,
and empty future directories.

**Exit criteria:** Documentation agrees on the NYC Taxi scenario, live-evidence
acceptance gate, full stack, workflow, UI commitment, testing obligations, and
unverified write path. No application code, automation scripts, or dependencies
exist.

## Phase 1: environment validation

**Goal:** Validate prerequisites and select compatible, appropriately licensed
versions without assuming capabilities.

Environment validation precedes installation. The macOS-only `make check`
command performs read-only discovery and generic candidate-port checks. Its
results do not establish DataHub compatibility; official requirements and an
actual successful startup must still be verified.

**Work:**

- verify supported Python, Node.js, DataHub OSS, and MCP Server versions;
- verify local resource and platform prerequisites;
- review hackathon rules for required technologies and permitted write paths;
- document authentication and secret handling;
- record dependency and license decisions; and
- define health signals and unavailable-dependency behavior.

**Exit criteria:** A documented environment matrix exists, dependency failures
are detectable, and no capability is claimed solely from an assumption.

## Phase 2: DataHub OSS and NYC Taxi dataset

**Goal:** Establish the real synthetic metadata scenario in a running DataHub
OSS instance.

**Work:**

- validate the available NYC Taxi source and licensing;
- define a synthetic planted stale or failed upstream dataset condition;
- load and verify upstream/downstream lineage;
- include affected dashboards or derived assets;
- include ownership and domain metadata;
- include freshness or quality evidence;
- define expected blast-radius paths without hard-coding runtime output;
- seed relevant previous incident memory; and
- document actual verified asset identifiers and graph shape after loading.

**Exit criteria:** The scenario is queryable in DataHub OSS, its expected
metadata is documented from observation, and no invented asset names remain in
acceptance tests.

## Phase 3: verified MCP capability spike

**Goal:** Verify actual DataHub MCP operations against official documentation
and the running tool inventory.

**Work:**

- inventory tool names, schemas, authentication, errors, and limits;
- verify asset discovery and lookup;
- verify upstream and downstream lineage retrieval;
- verify ownership, domain, freshness, and quality evidence retrieval;
- verify previous incident retrieval options;
- determine whether a suitable MCP mutation exists;
- determine the permitted official DataHub API/SDK fallback if needed; and
- document the actual read and planned write paths.

**Exit criteria:** Required read operations work against the NYC Taxi scenario.
Mutation capability is labeled verified or unavailable. No fake integration or
invented tool name is accepted.

## Phase 4: typed contracts and investigation engine

**Goal:** Implement the read-only, evidence-grounded investigation core.

**Sprint 5 status:** Partially complete. Normalized contracts and deterministic
lineage, blast-radius, severity, confidence, remediation, approval-state, and
incident-memory logic are implemented with isolated synthetic unit tests. The
verified MCP adapter, runtime orchestration, asset resolution, Evidence Ledger
assembly from live operations, and NYC Taxi integration remain pending.

**Work:**

- define Pydantic contracts for incident input, evidence, lineage, blast radius,
  severity, confidence, remediation, memory, timeline, and failures;
- implement the narrow verified MCP adapter;
- implement asset ambiguity handling;
- implement bounded upstream and downstream traversal;
- implement deterministic blast-radius calculation;
- assemble the Evidence Ledger;
- separate known, derived, hypothesized, and unknown findings;
- implement deterministic, versioned severity;
- implement 0.0–1.0 evidence coverage and consistency confidence;
- retrieve relevant previous incidents; and
- produce evidence-backed remediation without executing it.

**Exit criteria:** A read-only NYC Taxi investigation proves runtime DataHub/MCP
provenance, reports dependency failure honestly, and returns reproducible
structured results.

## Phase 5: write-back and memory

**Goal:** Implement the human-controlled persistence lifecycle through a
verified and permitted write path.

**Work:**

- finalize the incident representation from verified capabilities;
- implement draft review and explicit human approval state;
- bind approval to an immutable payload identity;
- prefer a verified MCP mutation tool;
- use an official supported DataHub write API or SDK only if MCP lacks an
  appropriate mutation and hackathon rules permit the fallback;
- never simulate successful write-back;
- implement stable identity, idempotency, retries, and partial-write recovery;
- read the persisted representation back;
- compare normalized material fields with the approved payload; and
- expose only verified records as future incident memory.

**Exit criteria:** The state flow is enforced:

```text
Draft investigation
  → human review
  → explicit approval
  → write-back
  → read-back
  → payload verification
  → recorded incident memory
```

The actual write path is disclosed, mismatch is a failure, and retry does not
duplicate incident memory.

## Phase 6: FastAPI backend

**Goal:** Expose investigation capabilities through a typed application API.

**Work:**

- create FastAPI lifecycle, health, investigation, timeline, approval,
  persistence, recent-incident, and memory interfaces;
- validate requests and responses with Pydantic;
- preserve provenance and error semantics through API boundaries;
- expose empty, loading, partial, error, disconnected, success, and resolved
  states;
- enforce authorization and approval transitions; and
- add API contract, security, timeout, and recovery tests.

**Exit criteria:** The backend exposes the verified engine without bypassing
evidence, permission, or dependency gates.

## Phase 7: React desktop UI

**Goal:** Deliver a professional React, TypeScript, and Vite desktop
investigation workspace.

**Views and components:**

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

**Work:** Implement accessible keyboard behavior, focus management, readable
evidence density, responsive desktop layout, graph semantics, consistent
operational states, and submission-quality visual polish after the real
backend path works.

**Exit criteria:** A responder can conduct and verify the full human-controlled
workflow without hiding partial evidence or dependency failures. Accessibility
and professional visual-quality acceptance checks pass.

## Phase 8: one-command automation

**Goal:** Provide modular, inspectable orchestration behind the Makefile.

**Planned scripts:**

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

`make demo` must eventually check prerequisites, prepare the complete demo
environment, validate service health, load the planted NYC Taxi scenario, start
MCP, backend, and frontend, run smoke validation, and print URLs. Modular
scripts must fail clearly and clean up safely.

**Exit criteria:** The one-command path succeeds from a documented clean
environment and visibly fails when required dependencies are unavailable.

## Phase 9: comprehensive tests

**Goal:** Complete the test matrix in `docs/TEST_STRATEGY.md`.

**Work:** Cover deterministic logic, API contracts, actual DataHub/MCP
integration, runtime provenance, NYC Taxi expectations, lineage, blast radius,
severity boundaries, grounding and hallucination safety, conflicting evidence,
prompt injection, approval, persistence equivalence, memory, frontend, browser
E2E, accessibility, security, performance, clean installation, one-command
demo, and submission compliance.

**Exit criteria:** Every required test category has automated coverage or a
documented, reproducible manual verification where automation is genuinely
infeasible. The golden demo cannot pass using isolated fixtures.

## Phase 10: demo and submission

**Goal:** Deliver a truthful, judge-verifiable submission.

**Work:**

- rehearse the NYC Taxi planted freshness incident from a clean environment;
- visibly demonstrate live DataHub/MCP provenance;
- demonstrate lineage, blast radius, Evidence Ledger, severity, confidence,
  unknowns, ownership, remediation, and memory;
- demonstrate human approval, actual write path, read-back, and equivalence;
- show honest disconnected and partial states;
- complete professional visual polish and accessibility review;
- disclose verified versions, tools, write path, fallbacks, and limitations; and
- run submission compliance and secret scans.

**Exit criteria:** The demo performs real DataHub-backed work, the documentation
matches reality, no success is simulated, and all submission criteria pass.

## Planned Makefile mapping

The `check` target runs read-only prerequisite validation. `setup` now creates
an ignored repository-local Python 3.11+ `.venv` and installs the Sprint 5
pins; `test` invokes that idempotent bootstrap and runs the unit suite. Other
unfinished targets remain safe print-only placeholders. Their future
responsibilities are:

| Target | Planned responsibility |
| --- | --- |
| `check` | Run the implemented read-only macOS prerequisite validation |
| `setup` | Implemented repository-local Sprint 5 Python/test bootstrap; broader environment preparation remains future work |
| `start` | Start required services through modular scripts |
| `seed` | Load and verify the NYC Taxi planted scenario |
| `test` | Run the comprehensive automated suite |
| `smoke` | Verify health and a live read-only DataHub/MCP probe |
| `demo` | Prepare and run the complete one-command demo |
| `demo-check` | Verify golden-scenario prerequisites and expected evidence |
| `submission-check` | Verify repository, security, tests, docs, and compliance |
| `stop` | Stop project-managed services safely |

## Definition of done

A feature is done only when its contract, provenance, normal and failure paths,
security constraints, tests, and documentation agree. Mutation features also
require verified capability, human approval, read-back equivalence,
idempotency, recovery, and disclosure of the actual write path.
