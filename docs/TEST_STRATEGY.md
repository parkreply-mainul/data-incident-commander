# Test Strategy

## Purpose and current status

Tests must prove that DataIncident Commander performs useful work against a
running DataHub OSS instance through verified DataHub MCP Server operations,
preserves evidence provenance, makes reproducible calculations, and never
simulates success. Sprint 5 implements isolated deterministic core tests.
Sprint 6 adds isolated application, repository, and FastAPI contract tests with
the live integration deliberately unconfigured. Sprint 7 adds isolated
frontend client/component/accessibility contract tests and a bounded local
FastAPI/Vite smoke path. Real DataHub/MCP and full browser E2E tests remain
future work.

## Acceptance rules

- The golden demo cannot pass with fixtures, fake adapters, hard-coded answers,
  precomputed output, chatbot prose, screenshots, or simulated persistence.
- Runtime evidence must carry verifiable DataHub/MCP provenance.
- DataHub or MCP unavailability must produce a visible failed or disconnected
  result.
- Fixtures are allowed only in isolated automated tests.
- Confirmed findings require valid evidence references.
- Severity is deterministic and distinct from confidence.
- Confidence ranges from 0.0 to 1.0 and represents evidence coverage and
  consistency, not model certainty.
- Mutation tests must use only the actual verified and permitted write path.
- A write is not successful until read-back matches the approved payload.

## Test environments

- **Isolated:** deterministic unit, contract, component, and safety tests with
  synthetic fixtures.
- **Real integration:** supported DataHub OSS plus the DataHub MCP Server,
  loaded with the synthetic NYC Taxi metadata scenario.
- **Browser E2E:** real backend, frontend, DataHub, and MCP path.
- **Clean demo:** documented prerequisites and no pre-existing project state.
- **Optional live model:** separately configured grounding evaluation; never a
  substitute for deterministic tests.

Exact versions, verified operations, asset identifiers, metadata fields, and
graph shape will be recorded only after the environment, dataset, and MCP
capability spikes.

## Unit tests

Unit tests will cover input validation, candidate ranking, evidence
normalization, known/derived/hypothesis/unknown classification, cycle
detection, traversal limits, freshness calculations, blast-radius
calculations, severity factors, confidence coverage, stable persistence keys,
payload normalization, equivalence comparison, and redaction.

Sprint 5 currently covers strict contract validation, UTC timestamps, stable
serialization, evidence-ledger uniqueness, confirmed evidence requirements,
cycle/depth/node-safe lineage and paths, direct/transitive blast radius,
severity rubric boundaries and explanations, confidence penalties and
severity independence, remediation approval classification, immutable approval
transitions and retry, and deterministic identifier-based memory matching.
It also covers canonical evidence payload acceptance/rejection, deep
immutability of traversal mappings, and stable JSON serialization. The
repository-local Makefile bootstrap is validated against a temporary absent
virtual environment and by an idempotent second setup run.
Candidate ranking, adapters, idempotency, payload comparison, and timeout
policies remain pending.

## API contract tests

Sprint 6 FastAPI/Pydantic contract tests cover valid and invalid requests,
structured investigation results, timeline events, approval transitions,
persistence and read-back status, recent incidents, memory results, pagination
where currently implemented, application/readiness status, deterministic
serialization, and typed error responses. Persistence/read-back, recent
incidents, and memory API coverage remain future work.

## Real DataHub integration tests

Tests against running DataHub OSS will discover the validated NYC Taxi assets,
retrieve their metadata, verify expected observed relationships and evidence,
and prove that unavailable DataHub produces a visible failure. These tests
cannot use isolated fixtures as replacements.

## MCP tool tests

After capability discovery, tests will exercise the actual verified MCP tool
inventory, request and response schemas, authentication failures, unavailable
tools, malformed or partial responses, timeouts, rate or resource limits, and
provenance preservation. No tool name or mutation capability is assumed in
Sprint 1B.

## NYC Taxi golden-scenario tests

The golden scenario will plant a stale or failed upstream dataset condition and
verify asset resolution, upstream and downstream lineage, freshness or quality
evidence, ownership, affected dashboards or derived assets, blast radius,
severity, confidence, remediation, human approval, the verified write path,
read-back comparison, and previous incident memory.

Expected asset names, owners, metadata fields, and graph shape must come from
the validated DataHub dataset; tests must not invent them.

## Runtime provenance tests

These tests prove that runtime evidence came from the running DataHub/MCP path
by checking tool-call records, source identifiers, retrieval timestamps,
investigation identifiers, and evidence references. They will also verify that
disconnecting DataHub or MCP prevents a successful demo and that fixture
provenance is rejected in live-demo mode.

## Lineage integrity tests

Lineage tests will verify upstream/downstream direction, expected paths,
selected-asset identity, cycles, duplicates, missing nodes, branching,
pagination where applicable, depth and node limits, truncation flags, and
partial graph behavior.

## Blast-radius tests

Blast-radius tests will verify affected-asset membership, affected dashboards
or derived assets, path evidence, counts, de-duplication, bounded traversal,
unknown scope, truncation disclosure, and calculation version. A truncated
graph must not be presented as a complete blast radius.

## Deterministic severity boundary tests

Tests will cover every factor, weight, threshold, band boundary, rounding rule,
missing input rule, calculation version, and worked example. Identical evidence
must produce identical severity independent of generated prose.

## Confidence contract tests

Tests will verify the 0.0–1.0 range, evidence coverage, consistency penalties,
missing and conflicting evidence, calculation version, and separation from
severity. Low confidence must suppress definitive root-cause wording and cause
unknowns to remain visible.

## Evidence-grounding tests

An expected-evidence matrix will validate that asset identity, lineage impact,
ownership, freshness, quality, blast radius, severity, confidence, memory, and
remediation claims link to appropriate evidence. Tests will report missing,
invalid, or circular references and unsupported material claims.

## Hallucination and unsupported-claim tests

Tests will attempt to induce invented owners, assets, lineage, timestamps,
failure causes, write success, and remediation facts. Any material unsupported
claim rendered as confirmed is a failure. Fluent but ungrounded output does not
pass.

## Conflicting and stale evidence tests

Tests will provide conflicting observations, out-of-order timestamps, stale
assertions, and mixed freshness/quality signals. The Evidence Ledger must retain
the conflict, confidence must decrease, and the result must not silently choose
a preferred observation.

## Prompt-injection tests

Instruction-like content in incident text, asset descriptions, ownership
fields, previous incidents, and other metadata must not change system
instructions, tool allowlists, traversal budgets, approval state, or mutation
permissions.

## Missing-owner and unknown-data tests

Missing owners, domains, freshness signals, quality results, lineage nodes, and
criticality metadata must remain explicit unknowns. The application must not
invent replacements, and confidence must reflect reduced coverage.

## Human-approval tests

Tests will enforce:

```text
Draft investigation
  → human review
  → explicit approval
  → write-back
  → read-back
  → payload verification
  → recorded incident memory
```

Mutation must be rejected before approval, after approval revocation, or after
any material change to the approved payload. UI tests must verify that the
reviewed payload, write capability, warnings, and approval consequence are
visible.

Core state-machine tests also cover stage-aware failure context and retry:
failure from each stage may return only to that stage, generic transitions out
of `FAILED` are rejected, every retry at or beyond approval requires separate
valid-approval and unchanged-payload-binding confirmations, persisted histories
must retain both confirmation markers, and the happy path remains unchanged.
Confidence tests reject duplicate evidence IDs and prove reordered unique
evidence produces identical factors and canonical output. They also reject
dangling record and explicit conflict references before penalty calculation,
while preserving anonymous legacy-count behavior. Contract tests verify that
omitted and explicit evidence provenance are canonical, deeply immutable, and
stable under nested report serialization.

## Write-back/read-back payload-equivalence tests

These tests will use only the verified, permitted write path. After persistence,
the record must be retrieved through a verified read path and normalized
material fields compared with the exact approved payload. Mismatch, unavailable
read-back, or partial data is failure, not success. Successful write-back must
never be simulated.

## Idempotency and partial-write recovery tests

Tests will retry the same approved incident, inject permitted failure points,
and verify stable identity, no duplicate memory, safe recovery, clear partial
status, and eventual read-back equivalence.

## Previous-incident memory tests

Tests will verify retrieval relevance, provenance, ordering, isolation between
incidents, behavior with no history, avoidance of duplicate records, and the
rule that historical remediation is evidence rather than automatically correct
instruction.

## Backend API tests

Sprint 6 backend tests cover lifecycle health, dependency status, investigation
creation, timeline progression, partial results, approval authorization,
concurrent or repeated requests, persistence status, read-back verification,
recent incidents, memory retrieval, redaction, and error handling.

Current implemented coverage includes application-only health, explicit
unavailable dependencies, draft creation/retrieval/listing, fail-closed
investigation, transition enforcement, stable safe errors, deterministic
injected IDs/time, repository locking, app import, and OpenAPI generation.
Concurrency tests synchronize competing approvals and prove only one revision
and audit transition persists. Provider preflight tests prove invalid states
perform no external call or save. Readiness tests cover default, configured,
unavailable, DataHub-only, and MCP-backed capability descriptions without
network activity. Atomic pagination tests pause a lock-held snapshot while a
concurrent create waits, proving page items and total describe the same record
set without timing-based assertions.

Provider-output tests use complete schema-valid reports and independently vary
incident ID, target identifier, status, and protected title. They verify that
mismatches occur before transition/save, preserve the original revision and
empty audit/report state, emit a safe stable API error, and never echo provider
payload content. A matching report proves the valid investigated transition.

Correlation tests cover successful, validation, known application, not-found,
and unexpected-error responses. They verify caller IDs are preserved, absent
IDs are generated exactly once, the body and `X-Request-ID` header match, only
one header value is emitted, and internal failures remain safely redacted.

## Frontend component tests

Sprint 7 React tests cover navigation, readiness, investigation input,
draft listing/detail, audit history, pagination, request IDs, client errors,
focus and labels, and unavailable future-result surfaces. The detailed matrix
is in `docs/FRONTEND_TEST_STRATEGY.md`. Functional timeline, severity,
lineage, blast radius, Evidence Ledger, confidence, ownership, remediation,
approval, write/read, and memory tests remain gated on real API capabilities.

## Browser E2E tests

Browser tests will drive the complete desktop workflow against real backend,
DataHub, and MCP services: submit the NYC Taxi incident, inspect live evidence,
review lineage and blast radius, approve the exact payload, observe write and
read-back equivalence, and view the resulting incident memory.

## Lineage-visualization tests

Visualization tests will verify graph direction, selected asset, upstream and
downstream distinction, affected assets, keyboard access, readable labels,
cycles, truncation, unknown nodes, selection details, and consistency with the
backend graph contract.

## Accessibility tests

Automated and manual checks will cover keyboard-only operation, focus order and
visibility, semantic headings and landmarks, accessible names, status
announcements, dialog behavior, error association, color contrast, zoom and
reflow, non-color indicators, and accessible graph alternatives.

## Security and secrets tests

Tests and checks will cover secret scanning, committed-file inspection, log and
error redaction, configuration validation, authorization boundaries, CORS and
browser security settings, untrusted metadata handling, injection resistance,
dependency/license review, and absence of private or proprietary data.

## Performance and timeout tests

Tests will enforce tool-call, lineage depth, node, and elapsed-time budgets;
exercise large and cyclic graphs; verify cancellation and timeout behavior; and
ensure partial evidence remains usable without misrepresenting completeness.

## Clean-install tests

A clean public checkout will follow only documented prerequisites and commands.
The test will verify configuration templates, version checks, reproducible
setup, health validation, sample loading, no hidden local state, and clear
failure messages. No real credential may be required for public-safe setup
unless explicitly documented as an optional external service.

## One-command demo tests

Eventually, `make demo` must invoke modular scripts to check prerequisites,
prepare the environment, validate health, load the planted NYC Taxi scenario,
start MCP, backend, and frontend, run smoke validation, and print URLs. Tests
will prove repeatability, nonzero failure on unavailable dependencies, safe
cleanup, and rejection of fixture-only live mode.

The planned scripts are:

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

They are not implemented in Sprint 1B.

## Submission-compliance tests

Checks will verify required files and Makefile targets, Apache 2.0 licensing,
public-safe content, no secrets or private/proprietary artifacts, documented
versions and actual write path, working documentation links, clean-install and
demo results, required stack and DataHub technologies, test evidence,
accessibility results, limitations, and hackathon submission requirements.

## Data policy

All committed fixtures and seed definitions must be synthetic, minimal,
deterministic, appropriately licensed, and safe for a public repository. No
production metadata, credentials, private incident descriptions, or material
from ParkReply, SafeRelay, or PIC may be used. Fixture timestamps should be
controlled and fixture identity must be distinguishable from live runtime
evidence.

## Final quality gate

The project passes only when the clean one-command golden scenario performs
real DataHub-backed investigation, the professional desktop UI exposes evidence
and uncertainty, human approval gates the actual verified write path, read-back
matches the approved payload, the result becomes retrievable memory, and every
required compliance check passes.
