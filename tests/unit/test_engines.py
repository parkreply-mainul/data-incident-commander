from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from data_incident_commander.domain.base import canonical_json
from data_incident_commander.domain.confidence import ConfidenceInputs, assess_confidence
from data_incident_commander.domain.models import (
    EvidenceType,
    Reliability,
    Severity,
    SeverityInputs,
    SeverityRuleSet,
)
from data_incident_commander.domain.severity import assess_severity

from .conftest import NOW


def _severity_inputs(**overrides):
    values = {
        "confirmed_failure": False,
        "affected_asset_count": 0,
        "critical_asset_count": 0,
        "affected_dashboard_model_count": 0,
        "missing_ownership": False,
        "incomplete_evidence": False,
        "blast_radius_truncated": False,
    }
    values.update(overrides)
    return SeverityInputs(**values)


@pytest.mark.parametrize(
    ("score_inputs", "expected_score", "expected_severity"),
    [
        ({}, 0, Severity.LOW),
        ({"confirmed_failure": True}, 2, Severity.MEDIUM),
        ({"confirmed_failure": True, "critical_asset_count": 1}, 4, Severity.HIGH),
        (
            {
                "confirmed_failure": True,
                "critical_asset_count": 1,
                "affected_asset_count": 10,
                "missing_ownership": True,
            },
            8,
            Severity.CRITICAL,
        ),
    ],
)
def test_severity_boundaries(score_inputs, expected_score, expected_severity):
    result = assess_severity(_severity_inputs(**score_inputs))
    assert result.score == expected_score
    assert result.severity is expected_severity


def test_severity_thresholds_are_configurable():
    rules = SeverityRuleSet(
        affected_asset_threshold=2,
        broad_impact_threshold=4,
        dashboard_model_threshold=1,
        medium_score=1,
        high_score=3,
        critical_score=5,
    )
    result = assess_severity(_severity_inputs(affected_asset_count=2), rules)
    assert result.severity is Severity.MEDIUM
    assert result.ruleset_version == "1"


def test_severity_records_every_rule_and_explanation():
    result = assess_severity(_severity_inputs(confirmed_failure=True, incomplete_evidence=True))
    assert len(result.applied_rules) == 8
    assert {rule.rule_id for rule in result.applied_rules if rule.applied} == {
        "confirmed_failure",
        "incomplete_evidence",
    }
    assert all("+" in line for line in result.explanation)


def test_confidence_full_fresh_consistent_verified_evidence(evidence_factory):
    evidence = (
        evidence_factory("asset", EvidenceType.ASSET_METADATA),
        evidence_factory("fresh", EvidenceType.FRESHNESS_SIGNAL),
    )
    result = assess_confidence(
        ConfidenceInputs(
            evidence=evidence,
            expected_evidence_types=(EvidenceType.ASSET_METADATA, EvidenceType.FRESHNESS_SIGNAL),
        )
    )
    assert result.confidence == 1.0
    assert result.penalties == ()


def test_missing_evidence_lowers_confidence(evidence_factory):
    complete = assess_confidence(
        ConfidenceInputs(
            evidence=(evidence_factory("asset"),),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    missing = assess_confidence(
        ConfidenceInputs(
            evidence=(evidence_factory("asset"),),
            expected_evidence_types=(EvidenceType.ASSET_METADATA, EvidenceType.OWNERSHIP),
        )
    )
    assert missing.confidence < complete.confidence
    assert "missing expected evidence lowers coverage" in missing.penalties


def test_stale_evidence_penalty(evidence_factory):
    fresh = evidence_factory("fresh", age_seconds=10, stale_after_seconds=60)
    stale = evidence_factory("stale", age_seconds=120, stale_after_seconds=60)
    expected = (EvidenceType.ASSET_METADATA,)
    assert assess_confidence(
        ConfidenceInputs(evidence=(stale,), expected_evidence_types=expected)
    ).confidence < assess_confidence(
        ConfidenceInputs(evidence=(fresh,), expected_evidence_types=expected)
    ).confidence


def test_valid_timestamp_consistent_old_evidence_lowers_freshness(evidence_factory):
    fresh = evidence_factory("fresh", age_seconds=0, stale_after_seconds=60)
    values = evidence_factory("old").model_dump()
    values.update(
        observed_at=NOW - timedelta(seconds=120),
        retrieved_at=NOW,
        age_seconds=120,
        stale_after_seconds=60,
    )
    old = type(fresh).model_validate(values)
    expected = (EvidenceType.ASSET_METADATA,)
    old_result = assess_confidence(
        ConfidenceInputs(evidence=(old,), expected_evidence_types=expected)
    )
    fresh_result = assess_confidence(
        ConfidenceInputs(evidence=(fresh,), expected_evidence_types=expected)
    )
    assert old_result.confidence < fresh_result.confidence


def test_contradictory_age_is_rejected_before_confidence_assessment(evidence_factory):
    values = evidence_factory("contradictory").model_dump()
    values.update(
        observed_at=NOW - timedelta(hours=1),
        retrieved_at=NOW,
        age_seconds=0,
    )
    with pytest.raises(ValidationError, match="timestamp-derived minimum"):
        type(evidence_factory("template")).model_validate(values)


def test_conflicting_evidence_penalty(evidence_factory):
    evidence = (evidence_factory("e1"), evidence_factory("e2"))
    consistent = assess_confidence(
        ConfidenceInputs(evidence=evidence, expected_evidence_types=(EvidenceType.ASSET_METADATA,))
    )
    conflicting = assess_confidence(
        ConfidenceInputs(
            evidence=evidence,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            conflicting_evidence_count=1,
        )
    )
    assert conflicting.confidence < consistent.confidence
    assert conflicting.unique_conflict_count == 1
    assert conflicting.conflict_sources == ("legacy_count",)


def test_no_conflicts_have_no_consistency_penalty(evidence_factory):
    result = assess_confidence(
        ConfidenceInputs(
            evidence=(evidence_factory("e1"),),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    assert result.unique_conflict_count == 0
    assert result.conflict_sources == ()
    assert result.conflict_penalty == 0.0


def test_confidence_rejects_duplicate_identical_evidence_ids(evidence_factory):
    evidence = evidence_factory("e1")
    with pytest.raises(ValidationError, match="unique evidence_id"):
        ConfidenceInputs(
            evidence=(evidence, evidence),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )


def test_confidence_rejects_duplicate_id_with_different_payload(evidence_factory):
    first = evidence_factory("e1")
    values = first.model_dump()
    values["factual_payload"] = {"status": "different"}
    second = type(first).model_validate(values)
    with pytest.raises(ValidationError, match="unique evidence_id"):
        ConfidenceInputs(
            evidence=(first, second),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )


def test_unique_evidence_is_accepted_and_reordering_is_deterministic(evidence_factory):
    evidence = (
        evidence_factory("e1", conflicts=("e2",)),
        evidence_factory("e2"),
    )
    forward = assess_confidence(
        ConfidenceInputs(
            evidence=evidence,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    reordered = assess_confidence(
        ConfidenceInputs(
            evidence=tuple(reversed(evidence)),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    assert forward == reordered
    assert canonical_json(forward) == canonical_json(reordered)
    assert forward.unique_conflict_count == 1
    assert forward.conflict_penalty == 0.5


def test_conflict_only_from_evidence_reference(evidence_factory):
    evidence = (
        evidence_factory("e1", conflicts=("e2",)),
        evidence_factory("e2"),
    )
    result = assess_confidence(
        ConfidenceInputs(
            evidence=evidence,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    assert result.unique_conflict_count == 1
    assert result.conflict_sources == ("evidence_record_references",)


def test_record_conflict_reference_to_absent_evidence_is_rejected(evidence_factory):
    with pytest.raises(ValidationError, match="absent from evidence: missing"):
        ConfidenceInputs(
            evidence=(evidence_factory("e1", conflicts=("missing",)),),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )


@pytest.mark.parametrize(
    ("identity", "unknown_ids"),
    (
        (("e1", "missing"), "missing"),
        (("missing-a", "missing-b"), "missing-a, missing-b"),
    ),
)
def test_explicit_conflict_with_absent_evidence_is_rejected(
    evidence_factory,
    identity,
    unknown_ids,
):
    with pytest.raises(ValidationError, match=f"absent from evidence: {unknown_ids}"):
        ConfidenceInputs(
            evidence=(evidence_factory("e1"),),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(identity,),
        )


def test_valid_and_dangling_explicit_conflicts_are_rejected_together(evidence_factory):
    with pytest.raises(ValidationError, match="absent from evidence: missing"):
        ConfidenceInputs(
            evidence=(evidence_factory("e1"), evidence_factory("e2")),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e1", "e2"), ("e1", "missing")),
        )


def test_all_present_reciprocal_conflicts_are_valid_and_deterministic(evidence_factory):
    evidence = (
        evidence_factory("e1", conflicts=("e2",)),
        evidence_factory("e2", conflicts=("e1",)),
    )
    forward = assess_confidence(
        ConfidenceInputs(
            evidence=evidence,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    reversed_result = assess_confidence(
        ConfidenceInputs(
            evidence=tuple(reversed(evidence)),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    assert forward == reversed_result
    assert forward.unique_conflict_count == 1


def test_conflict_only_from_explicit_identity(evidence_factory):
    result = assess_confidence(
        ConfidenceInputs(
            evidence=(evidence_factory("e1"), evidence_factory("e2")),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e1", "e2"),),
        )
    )
    assert result.unique_conflict_count == 1
    assert result.conflict_sources == ("explicit_conflicts",)


def test_valid_explicit_conflict_identity_is_trimmed_sorted_and_deterministic(evidence_factory):
    forward = ConfidenceInputs(
        evidence=(evidence_factory("e1"), evidence_factory("e2")),
        expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        explicit_conflict_identities=((" e2 ", "e1"),),
    )
    reordered = ConfidenceInputs(
        evidence=(evidence_factory("e1"), evidence_factory("e2")),
        expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        explicit_conflict_identities=(("e1", "e2"),),
    )
    assert forward.explicit_conflict_identities == (("e1", "e2"),)
    assert forward.explicit_conflict_identities == reordered.explicit_conflict_identities


@pytest.mark.parametrize(
    "identity",
    [
        (),
        ("e1",),
        ("", "e1"),
        ("   ", "e1"),
        ("e1", "e1"),
    ],
    ids=["empty", "single", "blank", "whitespace", "duplicate"],
)
def test_malformed_explicit_conflict_identities_are_rejected(evidence_factory, identity):
    with pytest.raises(ValidationError):
        ConfidenceInputs(
            evidence=(evidence_factory("e1"),),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(identity,),
        )


def test_same_conflict_in_both_sources_is_counted_once(evidence_factory):
    result = assess_confidence(
        ConfidenceInputs(
            evidence=(
                evidence_factory("e1", conflicts=("e2",)),
                evidence_factory("e2"),
            ),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e2", "e1"),),
        )
    )
    assert result.unique_conflict_count == 1
    assert result.conflict_sources == (
        "evidence_record_references",
        "explicit_conflicts",
    )
    assert result.conflict_penalty == 0.5


def test_distinct_conflicts_across_sources_are_counted_once_each(evidence_factory):
    result = assess_confidence(
        ConfidenceInputs(
            evidence=(
                evidence_factory("e1", conflicts=("e2",)),
                evidence_factory("e2"),
                evidence_factory("e3"),
            ),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e2", "e1"), ("e2", "e3")),
        )
    )
    assert result.unique_conflict_count == 2
    assert result.conflict_penalty == pytest.approx(2 / 3, abs=1e-6)


def test_reordered_conflict_inputs_produce_identical_confidence(evidence_factory):
    evidence = (
        evidence_factory("e1", conflicts=("e2",)),
        evidence_factory("e2", conflicts=("e1",)),
        evidence_factory("e3"),
    )
    forward = assess_confidence(
        ConfidenceInputs(
            evidence=evidence,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e2", "e3"), ("e1", "e2")),
        )
    )
    reversed_result = assess_confidence(
        ConfidenceInputs(
            evidence=tuple(reversed(evidence)),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e2", "e1"), ("e3", "e2")),
        )
    )
    assert forward == reversed_result


def test_duplicate_conflict_references_in_one_record_are_normalized(evidence_factory):
    evidence = evidence_factory("e1", conflicts=("e2", "e2"))
    assert evidence.conflict_references == ("e2",)
    result = assess_confidence(
        ConfidenceInputs(
            evidence=(evidence, evidence_factory("e2")),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    assert result.unique_conflict_count == 1


def test_normalized_record_references_do_not_inflate_conflicts(evidence_factory):
    normalized = (
        evidence_factory("e1", conflicts=(" e2 ", "e2", " e2")),
        evidence_factory("e2", conflicts=(" e1 ",)),
    )
    reordered = tuple(reversed(normalized))
    first = assess_confidence(
        ConfidenceInputs(
            evidence=normalized,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    second = assess_confidence(
        ConfidenceInputs(
            evidence=reordered,
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    assert first.unique_conflict_count == 1
    assert first.conflict_penalty == 0.5
    assert first == second


def test_confidence_explanation_reports_unique_conflict_count(evidence_factory):
    result = assess_confidence(
        ConfidenceInputs(
            evidence=(
                evidence_factory("e1", conflicts=("e2",)),
                evidence_factory("e2"),
            ),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
        )
    )
    consistency = next(factor for factor in result.factors if factor.factor_id == "consistency")
    assert "Unique conflicts: 1" in consistency.explanation
    assert "normalized penalty: 0.500000" in consistency.explanation


def test_legacy_conflict_count_cannot_mix_with_identifiable_conflicts(evidence_factory):
    with pytest.raises(ValidationError, match="cannot be combined"):
        ConfidenceInputs(
            evidence=(
                evidence_factory("e1", conflicts=("e2",)),
                evidence_factory("e2"),
            ),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            conflicting_evidence_count=1,
        )


def test_conflict_scoring_does_not_change_severity(evidence_factory):
    severity_inputs = _severity_inputs(confirmed_failure=True, critical_asset_count=1)
    before = assess_severity(severity_inputs)
    assess_confidence(
        ConfidenceInputs(
            evidence=(
                evidence_factory("e1", conflicts=("e2",)),
                evidence_factory("e2"),
            ),
            expected_evidence_types=(EvidenceType.ASSET_METADATA,),
            explicit_conflict_identities=(("e1", "e2"),),
        )
    )
    assert assess_severity(severity_inputs) == before


def test_graph_truncation_penalty(evidence_factory):
    inputs = {
        "evidence": (evidence_factory("e1"),),
        "expected_evidence_types": (EvidenceType.ASSET_METADATA,),
    }
    normal = assess_confidence(ConfidenceInputs(**inputs))
    truncated = assess_confidence(ConfidenceInputs(**inputs, graph_truncated=True))
    assert truncated.confidence == pytest.approx(normal.confidence - 0.1)


def test_low_provenance_lowers_confidence(evidence_factory):
    verified = evidence_factory("v", reliability=Reliability.VERIFIED)
    low = evidence_factory("l", reliability=Reliability.LOW)
    expected = (EvidenceType.ASSET_METADATA,)
    assert assess_confidence(
        ConfidenceInputs(evidence=(low,), expected_evidence_types=expected)
    ).confidence < assess_confidence(
        ConfidenceInputs(evidence=(verified,), expected_evidence_types=expected)
    ).confidence


def test_confidence_does_not_change_severity(evidence_factory):
    severity_inputs = _severity_inputs(confirmed_failure=True, critical_asset_count=1)
    before = assess_severity(severity_inputs)
    assess_confidence(
        ConfidenceInputs(evidence=(), expected_evidence_types=(EvidenceType.FRESHNESS_SIGNAL,))
    )
    after = assess_severity(severity_inputs)
    assert before == after
    assert before.severity is Severity.HIGH
