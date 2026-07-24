# Confidence Model

## Contract

Confidence ranges from **0.0 to 1.0** and represents evidence coverage,
freshness, consistency, and provenance quality. It is not model certainty,
probability that a root cause is true, or severity.

Default weighted factors:

| Factor | Weight | Meaning |
| --- | ---: | --- |
| Coverage | 0.35 | Fraction of expected evidence types present |
| Freshness | 0.25 | Evidence age relative to its explicit stale threshold |
| Consistency | 0.25 | Absence of evidence conflicts |
| Provenance | 0.15 | Average normalized reliability classification |

Reliability values are normalized as low `0.25`, medium `0.50`, high `0.80`,
and verified `1.00`. Evidence without age policy receives a conservative
freshness value of `0.50`. Missing evidence reduces coverage; no evidence
produces zero freshness and provenance. Graph truncation applies a separate
`0.10` penalty. The final score is clamped to the valid range and rounded to
six decimal places.

An explicit evidence age is accepted only after the evidence contract verifies
that it is consistent with the observation-to-retrieval timestamp interval,
allowing less than one second for integer precision. Contradictory ages are
rejected before confidence calculation.

Every factor records weight, value, contribution, and explanation. Penalties
identify missing, stale, conflicting, or truncated evidence. A confirmed
finding still requires evidence regardless of the confidence score.

## Conflict normalization

Confidence uses one authoritative set of conflict identities. Each identity is
a sorted tuple of at least two distinct, trimmed, non-empty evidence IDs.
Malformed empty, one-element, blank, whitespace-only, or internally duplicated
identities are rejected before normalization. Identities derived from
`EvidenceRecord.conflict_references` use trimmed, non-empty, deduplicated,
deterministically sorted IDs. They are unioned with explicit incident/report
identities and deduplicated before scoring. Reciprocal references, repeated
references, whitespace variants, reordered inputs, and the same conflict in
both sources therefore produce one penalty.

`ConfidenceInputs.evidence` requires unique `evidence_id` values and rejects
duplicates rather than silently selecting or averaging them. Coverage,
freshness, provenance, and the conflict-penalty denominator therefore use only
a valid unique evidence set. Reordering that set does not change the assessment
or its canonical serialized result.

Every identifiable conflict ID—whether supplied through an evidence record or
an explicit identity—must resolve to that unique evidence set. A dangling ID
rejects the complete confidence input before scoring; it is never discarded,
partially retained, or counted as a phantom conflict.

`conflicting_evidence_count` remains as a backward-compatible input only when
no identifiable record or explicit conflicts are present. It means the total
number of unique anonymous conflicts. Combining the legacy count with
identifiable conflicts is rejected as ambiguous.

The assessment records the unique conflict count, contributing sources, and
normalized conflict penalty. The consistency factor explanation repeats those
values.

This version is deterministic and configurable only through explicit code and
future versioning. It contains no learned weights or semantic judgment.
