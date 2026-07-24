# Domain Contracts

## Scope

Sprint 5 implements normalized, framework-independent contracts under
`src/data_incident_commander/domain/`. They contain no DataHub field names, MCP
tool names, HTTP concerns, UI concerns, LLM behavior, or demo conclusions.
Future verified adapters must translate external payloads into these contracts.

The contracts use strict, frozen Pydantic models. Unknown fields and coercion
are rejected. Timestamps must be timezone-aware and are normalized to UTC.
Canonical JSON uses sorted keys, compact separators, explicit enum values, and
UTC `Z` timestamps.

Evidence factual payloads accept only recursively valid JSON values: null,
booleans, integers, finite floats, strings, sequences, and string-keyed
mappings. Sequences become tuples and mappings become immutable proxies.
Sets, bytes, custom objects, non-string keys, NaN, and infinities are rejected.
Traversal paths and depths are likewise immutable and serialize back to normal
JSON objects and arrays.

Optional ownership contact metadata uses the same canonical-value validation,
recursive freezing, and stable JSON serialization as evidence payloads.

When evidence supplies `age_seconds`, it must be at least the elapsed time from
`observed_at` to `retrieved_at`. Because age is an integer while timestamps may
carry microseconds, the validator permits at most 999,999 microseconds of
integer-second precision loss. The comparison uses `timedelta`, not
floating-point seconds. Missing age remains missing; the contract does not
invent an assessment-time age.

Evidence conflict references are normalized to unique deterministic order.
Confidence combines their normalized evidence-ID pairs with explicit
incident/report conflict identities, deduplicating the same conflict across
both representations.

Incident-memory threshold `0.0` means every prior incident with at least one
positive deterministic match reason may be returned. A zero-score record with
no matching identifier, category, evidence type, or affected asset is never a
match at any threshold.

## Contract map

- `AssetIdentity` uses a generic `external_id`, display metadata, lifecycle,
  criticality, and optional owners/tags.
- `Ownership` never fabricates an owner and requires an evidence reference.
- immutable `EvidenceRecord` captures type, source operation, observation and
  retrieval time, factual payload, age policy, reliability, conflicts, and
  provenance. Omitted provenance is a deeply immutable empty mapping; explicit
  provenance uses the same canonical JSON validation and recursive freezing as
  factual payloads, while serialization emits ordinary JSON objects and arrays.
  Conflict-reference IDs are trimmed, blank IDs are rejected, and duplicates
  are deduplicated into deterministic sorted order.
- `ConfirmedFinding`, `InferredFinding`, `UnknownFinding`, and
  `ConflictingEvidence` preserve known/unknown separation. Confirmed findings
  require evidence IDs.
- `LineageGraph` stores normalized upstream-to-downstream edges and rejects
  unknown endpoints. Its constructor deduplicates and sorts nodes/edges.
- `BlastRadiusResult` separates direct and transitive downstream impact,
  unique counts, critical assets, bounds, truncation, and evidence.
- `SeverityAssessment` and `ConfidenceAssessment` are separate contracts.
  Confidence inputs reject duplicate evidence IDs and conflict identities that
  reference absent evidence before any factor is scored.
- `RemediationAction` is evidence-linked and descriptive only. Destructive
  actions require approval; no action executor exists.
- `ApprovalStateMachine` returns a new immutable history after each transition.
  Failure retains its origin, reason, actor, and timestamp; explicit retry can
  return only to that origin and cannot skip a required workflow stage.
  Retries at or beyond approval require explicit valid-approval and
  unchanged-payload-binding confirmations.
- `IncidentReport` combines the complete result, rejects duplicate evidence
  IDs, and recursively requires every supported evidence-reference field in
  findings, root cause, blast radius, ownership, remediation, conflicts, and
  incident memory to resolve within its ledger.
- incident-memory contracts match stable identifiers and categories, never
  display-name similarity.

## Lineage semantics

An edge means `upstream_id -> downstream_id`. Traversal supports both
directions, breadth-first deterministic ordering, configurable depth/node
limits, cycle safety, duplicate-path suppression, and first deterministic
shortest-path reconstruction. Truncation is explicit.

Blast radius traverses downstream. The root is excluded by default and may be
included only through an explicit option, which records it separately as
`included_root_asset_id`. The root never enters affected counts. Direct assets
are depth exactly one; transitive assets are deeper than one. Counts operate on
unique affected identifiers.

## Validation boundaries

The core deliberately does not validate raw DataHub or MCP payloads. Adapters
must:

1. verify the actual operation and response schema;
2. map external identifiers without assuming a URN field;
3. preserve timestamps, provenance, errors, and missing values;
4. reject or quarantine malformed evidence; and
5. construct these normalized models.

Fixtures in Sprint 5 are generic synthetic evidence used only by unit tests.
