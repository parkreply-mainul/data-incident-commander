"""Evidence coverage and consistency confidence model."""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from .base import StrictModel
from .models import ConfidenceAssessment, ConfidenceFactor, EvidenceRecord, EvidenceType, Reliability


class ConfidenceInputs(StrictModel):
    evidence: tuple[EvidenceRecord, ...]
    expected_evidence_types: tuple[EvidenceType, ...]
    explicit_conflict_identities: tuple[tuple[str, ...], ...] = ()
    conflicting_evidence_count: int = Field(default=0, ge=0)
    graph_truncated: bool = False

    @field_validator("evidence")
    @classmethod
    def evidence_ids_are_unique(
        cls,
        value: tuple[EvidenceRecord, ...],
    ) -> tuple[EvidenceRecord, ...]:
        evidence_ids = tuple(record.evidence_id for record in value)
        if len(set(evidence_ids)) != len(evidence_ids):
            raise ValueError("confidence evidence must have unique evidence_id values")
        return value

    @field_validator("explicit_conflict_identities")
    @classmethod
    def normalize_explicit_conflicts(
        cls,
        value: tuple[tuple[str, ...], ...],
    ) -> tuple[tuple[str, ...], ...]:
        normalized: set[tuple[str, ...]] = set()
        for identity in value:
            if len(identity) < 2:
                raise ValueError("explicit conflicts require at least two evidence IDs")
            trimmed = tuple(evidence_id.strip() for evidence_id in identity)
            if any(not evidence_id for evidence_id in trimmed):
                raise ValueError("explicit conflict evidence IDs must be non-empty")
            if len(set(trimmed)) != len(trimmed):
                raise ValueError("explicit conflict identities cannot contain duplicate IDs")
            normalized.add(tuple(sorted(trimmed)))
        return tuple(sorted(normalized))

    @model_validator(mode="after")
    def validate_conflict_inputs(self) -> "ConfidenceInputs":
        evidence_ids = {record.evidence_id for record in self.evidence}
        referenced_ids = {
            reference
            for record in self.evidence
            for reference in record.conflict_references
        }
        referenced_ids.update(
            evidence_id
            for identity in self.explicit_conflict_identities
            for evidence_id in identity
        )
        unknown_ids = referenced_ids - evidence_ids
        if unknown_ids:
            raise ValueError(
                "conflict identities reference evidence IDs absent from evidence: "
                + ", ".join(sorted(unknown_ids))
            )
        has_record_conflicts = any(record.conflict_references for record in self.evidence)
        if self.conflicting_evidence_count and (
            has_record_conflicts or self.explicit_conflict_identities
        ):
            raise ValueError(
                "conflicting_evidence_count cannot be combined with identifiable conflicts"
            )
        return self


_RELIABILITY = {
    Reliability.LOW: 0.25,
    Reliability.MEDIUM: 0.5,
    Reliability.HIGH: 0.8,
    Reliability.VERIFIED: 1.0,
}


def assess_confidence(inputs: ConfidenceInputs) -> ConfidenceAssessment:
    evidence = inputs.evidence
    expected = set(inputs.expected_evidence_types)
    present = {record.evidence_type for record in evidence}
    coverage = len(expected & present) / len(expected) if expected else 1.0

    freshness_values = []
    for record in evidence:
        if record.age_seconds is None or record.stale_after_seconds is None:
            freshness_values.append(0.5)
        elif record.age_seconds <= record.stale_after_seconds:
            freshness_values.append(1.0)
        else:
            freshness_values.append(max(0.0, record.stale_after_seconds / record.age_seconds))
    freshness = sum(freshness_values) / len(freshness_values) if freshness_values else 0.0

    record_conflicts = {
        tuple(sorted((record.evidence_id, reference)))
        for record in evidence
        for reference in record.conflict_references
    }
    explicit_conflicts = set(inputs.explicit_conflict_identities)
    normalized_conflicts = record_conflicts | explicit_conflicts
    conflict_sources: list[str] = []
    if record_conflicts:
        conflict_sources.append("evidence_record_references")
    if explicit_conflicts:
        conflict_sources.append("explicit_conflicts")
    if inputs.conflicting_evidence_count:
        conflict_sources.append("legacy_count")
    unique_conflict_count = (
        len(normalized_conflicts)
        if normalized_conflicts
        else inputs.conflicting_evidence_count
    )
    conflict_penalty = min(1.0, unique_conflict_count / max(1, len(evidence)))
    consistency = 1.0 - conflict_penalty
    provenance = (
        sum(_RELIABILITY[record.reliability] for record in evidence) / len(evidence)
        if evidence
        else 0.0
    )

    raw_factors = (
        ("coverage", 0.35, coverage, "Coverage of expected evidence types"),
        ("freshness", 0.25, freshness, "Freshness relative to each evidence record's age limit"),
        (
            "consistency",
            0.25,
            consistency,
            f"Unique conflicts: {unique_conflict_count}; "
            f"sources: {', '.join(conflict_sources) if conflict_sources else 'none'}; "
            f"normalized penalty: {conflict_penalty:.6f}",
        ),
        ("provenance", 0.15, provenance, "Reliability classification of evidence provenance"),
    )
    factors = tuple(
        ConfidenceFactor(
            factor_id=factor_id,
            weight=weight,
            value=round(value, 6),
            contribution=round(weight * value, 6),
            explanation=description,
        )
        for factor_id, weight, value, description in raw_factors
    )
    score = sum(factor.contribution for factor in factors)
    penalties: list[str] = []
    if coverage < 1.0:
        penalties.append("missing expected evidence lowers coverage")
    if freshness < 1.0:
        penalties.append("stale or unaged evidence lowers freshness")
    if consistency < 1.0:
        penalties.append(
            f"{unique_conflict_count} unique conflict(s) lower consistency "
            f"by {conflict_penalty:.6f}"
        )
    if inputs.graph_truncated:
        score -= 0.1
        penalties.append("truncated lineage graph applies a 0.10 penalty")
    return ConfidenceAssessment(
        confidence=round(min(1.0, max(0.0, score)), 6),
        factors=factors,
        penalties=tuple(penalties),
        unique_conflict_count=unique_conflict_count,
        conflict_sources=tuple(conflict_sources),
        conflict_penalty=round(conflict_penalty, 6),
    )
