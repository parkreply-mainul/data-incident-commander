from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from data_incident_commander.domain.base import canonical_json
from data_incident_commander.domain.models import (
    ActionClassification,
    AssetIdentity,
    BlastRadiusResult,
    ConfidenceAssessment,
    ConflictingEvidence,
    ConfirmedFinding,
    EvidenceType,
    IncidentMatch,
    IncidentReport,
    IncidentState,
    InferredFinding,
    OwnerKind,
    Ownership,
    Reliability,
    RemediationAction,
    RemediationPriority,
    RootCause,
    Severity,
    SeverityAssessment,
)

from .conftest import NOW


def test_contracts_are_strict_and_forbid_extra_fields():
    with pytest.raises(ValidationError):
        AssetIdentity(
            external_id="asset:1",
            display_name="Asset",
            asset_type="dataset",
            platform="synthetic",
            unexpected=True,
        )
    with pytest.raises(ValidationError):
        ConfidenceAssessment(confidence="0.8", factors=(), penalties=())


def test_timezone_aware_timestamps_are_required_and_normalized(evidence_factory):
    values = evidence_factory("e1").model_dump()
    values["retrieved_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError):
        type(evidence_factory("e1")).model_validate(values)

    offset = timezone(timedelta(hours=2))
    values = evidence_factory("e2").model_dump()
    values.update(
        observed_at=datetime(2026, 7, 24, 14, 0, tzinfo=offset),
        retrieved_at=datetime(2026, 7, 24, 14, 0, tzinfo=offset),
    )
    reparsed = type(evidence_factory("e2")).model_validate(values)
    assert reparsed.observed_at == NOW
    assert reparsed.observed_at.tzinfo == timezone.utc


def _evidence_with_age(evidence_factory, *, elapsed: timedelta, age_seconds):
    evidence_type = type(evidence_factory("age-template"))
    values = evidence_factory("age-check").model_dump()
    values.update(
        observed_at=NOW,
        retrieved_at=NOW + elapsed,
        age_seconds=age_seconds,
    )
    return evidence_type.model_validate(values)


def test_age_exactly_equal_to_timestamp_delta_is_valid(evidence_factory):
    evidence = _evidence_with_age(
        evidence_factory,
        elapsed=timedelta(seconds=10),
        age_seconds=10,
    )
    assert evidence.age_seconds == 10


def test_age_greater_than_timestamp_delta_is_valid(evidence_factory):
    evidence = _evidence_with_age(
        evidence_factory,
        elapsed=timedelta(seconds=10),
        age_seconds=11,
    )
    assert evidence.age_seconds == 11


def test_subsecond_integer_precision_tolerance_is_valid(evidence_factory):
    evidence = _evidence_with_age(
        evidence_factory,
        elapsed=timedelta(seconds=10, microseconds=999_999),
        age_seconds=10,
    )
    assert evidence.age_seconds == 10


def test_age_materially_below_timestamp_delta_is_rejected(evidence_factory):
    with pytest.raises(ValidationError, match="timestamp-derived minimum"):
        _evidence_with_age(
            evidence_factory,
            elapsed=timedelta(seconds=12),
            age_seconds=10,
        )


def test_negative_age_is_rejected(evidence_factory):
    with pytest.raises(ValidationError):
        _evidence_with_age(
            evidence_factory,
            elapsed=timedelta(0),
            age_seconds=-1,
        )


def test_zero_age_is_valid_when_timestamps_are_equal(evidence_factory):
    assert _evidence_with_age(
        evidence_factory,
        elapsed=timedelta(0),
        age_seconds=0,
    ).age_seconds == 0


def test_zero_age_is_rejected_when_retrieval_is_later(evidence_factory):
    with pytest.raises(ValidationError, match="timestamp-derived minimum"):
        _evidence_with_age(
            evidence_factory,
            elapsed=timedelta(seconds=1),
            age_seconds=0,
        )


def test_missing_age_remains_missing(evidence_factory):
    evidence = _evidence_with_age(
        evidence_factory,
        elapsed=timedelta(hours=1),
        age_seconds=None,
    )
    assert evidence.age_seconds is None


def test_evidence_record_is_immutable(evidence_factory):
    evidence = evidence_factory("e1")
    with pytest.raises(ValidationError):
        evidence.evidence_id = "changed"
    with pytest.raises(TypeError):
        evidence.factual_payload["status"] = "changed"


def test_evidence_conflict_reference_is_trimmed_deduplicated_and_sorted(evidence_factory):
    evidence = evidence_factory(
        "e1",
        conflicts=(" e3 ", "e2", " e2 ", "e3"),
    )
    assert evidence.conflict_references == ("e2", "e3")
    with pytest.raises(ValidationError):
        evidence.conflict_references = ()


@pytest.mark.parametrize("reference", ["", "   "], ids=["empty", "whitespace"])
def test_evidence_conflict_reference_rejects_blank_values(evidence_factory, reference):
    with pytest.raises(ValidationError, match="must be non-empty"):
        evidence_factory("e1", conflicts=(reference,))


def test_reordered_evidence_conflict_references_have_identical_json(evidence_factory):
    first = evidence_factory("e1", conflicts=(" e3 ", "e2", "e2"))
    second = evidence_factory("e1", conflicts=("e2", "e3"))
    assert canonical_json(first) == canonical_json(second)


def test_omitted_evidence_provenance_is_frozen_and_serializes_as_object(evidence_factory):
    values = evidence_factory("e1").model_dump()
    values.pop("provenance")
    evidence = type(evidence_factory("e1")).model_validate(values)
    assert dict(evidence.provenance) == {}
    with pytest.raises(TypeError):
        evidence.provenance["adapter"] = "changed"
    assert json.loads(canonical_json(evidence))["provenance"] == {}


def test_explicit_evidence_provenance_is_deeply_frozen(evidence_factory):
    values = evidence_factory("e1").model_dump()
    values["provenance"] = {"adapter": {"steps": ["read", {"verified": True}]}}
    evidence = type(evidence_factory("e1")).model_validate(values)
    assert evidence.provenance["adapter"]["steps"] == ("read", {"verified": True})
    with pytest.raises(TypeError):
        evidence.provenance["adapter"]["steps"][1]["verified"] = False
    assert json.loads(canonical_json(evidence))["provenance"] == {
        "adapter": {"steps": ["read", {"verified": True}]}
    }


@pytest.mark.parametrize("invalid_value", [{1}, b"bytes", object(), {1: "bad"}])
def test_evidence_provenance_rejects_noncanonical_values(evidence_factory, invalid_value):
    values = evidence_factory("e1").model_dump()
    values["provenance"] = {"invalid": invalid_value}
    with pytest.raises(ValidationError):
        type(evidence_factory("e1")).model_validate(values)


def test_evidence_provenance_stays_frozen_inside_incident_report(evidence_factory):
    evidence = evidence_factory("e1")
    values = evidence.model_dump()
    values["provenance"] = {"adapter": {"verified": True}}
    nested = type(evidence).model_validate(values)
    report = _report(evidence_factory, (nested,), ())
    with pytest.raises(TypeError):
        report.evidence_ledger[0].provenance["adapter"]["verified"] = False


def test_evidence_payload_accepts_and_freezes_every_canonical_json_category(evidence_factory):
    evidence = evidence_factory("e1")
    values = evidence.model_dump()
    values["factual_payload"] = {
        "null": None,
        "boolean": True,
        "integer": 7,
        "float": 1.25,
        "string": "value",
        "list": [1, {"nested": False}],
        "tuple": ("a", 2),
        "mapping": {"child": "value"},
    }
    normalized = type(evidence).model_validate(values)
    assert normalized.factual_payload["list"] == (1, {"nested": False})
    assert normalized.factual_payload["tuple"] == ("a", 2)
    with pytest.raises(TypeError):
        normalized.factual_payload["mapping"]["child"] = "changed"
    assert json.loads(canonical_json(normalized))["factual_payload"] == {
        "boolean": True,
        "float": 1.25,
        "integer": 7,
        "list": [1, {"nested": False}],
        "mapping": {"child": "value"},
        "null": None,
        "string": "value",
        "tuple": ["a", 2],
    }


@pytest.mark.parametrize(
    "invalid_value",
    [
        {1, 2},
        b"bytes",
        object(),
        {1: "non-string key"},
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
    ids=["set", "bytes", "custom-object", "non-string-key", "nan", "positive-inf", "negative-inf"],
)
def test_evidence_payload_rejects_noncanonical_json_values(evidence_factory, invalid_value):
    values = evidence_factory("e1").model_dump()
    values["factual_payload"] = {"invalid": invalid_value}
    with pytest.raises(ValidationError):
        type(evidence_factory("e1")).model_validate(values)


def _owner_with_contact(contact):
    return Ownership(
        owner_id="owner:1",
        display_name="Synthetic Owner",
        owner_type="custodian",
        kind=OwnerKind.TEAM,
        contact=contact,
        evidence_id="e1",
    )


def test_ownership_contact_accepts_freezes_and_serializes_nested_metadata():
    owner = _owner_with_contact(
        {
            "email": "owner@example.invalid",
            "active": True,
            "priority": 2,
            "weight": 1.5,
            "optional": None,
            "channels": ["email", {"kind": "chat"}],
        }
    )
    assert owner.contact["channels"] == ("email", {"kind": "chat"})
    serialized = json.loads(canonical_json(owner))
    assert serialized["contact"] == {
        "active": True,
        "channels": ["email", {"kind": "chat"}],
        "email": "owner@example.invalid",
        "optional": None,
        "priority": 2,
        "weight": 1.5,
    }


def test_ownership_contact_rejects_direct_and_nested_mutation():
    owner = _owner_with_contact({"email": "old", "nested": {"channel": "chat"}, "order": [1, 2]})
    with pytest.raises(TypeError):
        owner.contact["email"] = "new"
    with pytest.raises(TypeError):
        owner.contact["nested"]["channel"] = "changed"
    with pytest.raises(TypeError):
        owner.contact["order"][0] = 99


def test_ownership_contact_remains_immutable_through_asset_identity():
    owner = _owner_with_contact({"nested": {"email": "owner@example.invalid"}})
    asset = AssetIdentity(
        external_id="asset:1",
        display_name="Asset",
        asset_type="dataset",
        platform="synthetic",
        owners=(owner,),
    )
    with pytest.raises(TypeError):
        asset.owners[0].contact["nested"]["email"] = "changed"


def test_ownership_contact_remains_immutable_through_incident_report(evidence_factory):
    owner = _owner_with_contact({"nested": {"email": "owner@example.invalid"}})
    report = _report(evidence_factory, (evidence_factory("e1"),), ())
    values = report.model_dump()
    values["owners"] = (owner,)
    report_with_owner = IncidentReport.model_validate(values)
    with pytest.raises(TypeError):
        report_with_owner.owners[0].contact["nested"]["email"] = "changed"


@pytest.mark.parametrize(
    "invalid_value",
    [
        {1, 2},
        b"bytes",
        object(),
        {1: "non-string key"},
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
    ids=["set", "bytes", "custom-object", "non-string-key", "nan", "positive-inf", "negative-inf"],
)
def test_ownership_contact_rejects_noncanonical_values(invalid_value):
    with pytest.raises(ValidationError):
        _owner_with_contact({"invalid": invalid_value})


def test_confirmed_finding_requires_evidence():
    with pytest.raises(ValidationError):
        ConfirmedFinding(finding_id="f1", statement="Observed failure", evidence_ids=())


def _report(evidence_factory, evidence_ledger, findings):
    return IncidentReport(
        incident_id="incident:1",
        title="Synthetic incident",
        target_asset=AssetIdentity(
            external_id="asset:root",
            display_name="Root",
            asset_type="dataset",
            platform="synthetic",
        ),
        status=IncidentState.INVESTIGATED,
        root_cause=None,
        blast_radius=BlastRadiusResult(
            root_asset_id="asset:root",
            directly_affected_assets=(),
            transitively_affected_assets=(),
            affected_counts_by_type={},
            critical_assets_affected=(),
            traversal_depth_reached=0,
            truncated=False,
            evidence_references=(),
            impact_summary_inputs={
                "direct_count": 0,
                "transitive_count": 0,
                "total_count": 0,
                "critical_count": 0,
                "dashboard_model_count": 0,
                "truncated": False,
            },
        ),
        severity=SeverityAssessment(
            severity=Severity.LOW,
            score=0,
            ruleset_version="1",
            applied_rules=(),
            explanation=("No rules applied.",),
        ),
        confidence=ConfidenceAssessment(confidence=0.0, factors=(), penalties=()),
        confirmed_findings=findings,
        inferred_findings=(),
        unknowns=(),
        conflicting_evidence=(),
        owners=(),
        remediation_actions=(),
        evidence_ledger=evidence_ledger,
        related_previous_incidents=(),
        created_at=NOW,
        updated_at=NOW,
        engine_version="core-1",
    )


def test_incident_report_rejects_duplicate_evidence_ids(evidence_factory):
    evidence = evidence_factory("e1")
    with pytest.raises(ValidationError, match="duplicate evidence"):
        _report(evidence_factory, (evidence, evidence), ())


def test_incident_report_rejects_unresolved_confirmed_evidence_reference(evidence_factory):
    finding = ConfirmedFinding(finding_id="f1", statement="Observed", evidence_ids=("missing",))
    with pytest.raises(ValidationError, match="report references evidence absent"):
        _report(evidence_factory, (evidence_factory("e1"),), (finding,))


@pytest.mark.parametrize(
    "changes",
    [
        {
            "inferred_findings": (
                InferredFinding(
                    finding_id="i1",
                    statement="Derived",
                    evidence_ids=("missing",),
                    rationale="Synthetic inference",
                ),
            )
        },
        {
            "root_cause": RootCause(
                asset_id="asset:root",
                issue_category="freshness",
                description="Synthetic root cause",
                confirmed=True,
                evidence_ids=("missing",),
            )
        },
        {
            "blast_radius": BlastRadiusResult(
                root_asset_id="asset:root",
                directly_affected_assets=(),
                transitively_affected_assets=(),
                affected_counts_by_type={},
                critical_assets_affected=(),
                traversal_depth_reached=0,
                truncated=False,
                evidence_references=("missing",),
                impact_summary_inputs={},
            )
        },
        {
            "owners": (
                Ownership(
                    owner_id="owner:1",
                    display_name="Owner",
                    owner_type="custodian",
                    kind=OwnerKind.TEAM,
                    evidence_id="missing",
                ),
            )
        },
        {
            "remediation_actions": (
                RemediationAction(
                    action_id="a1",
                    title="Inspect",
                    description="Inspect synthetic state",
                    priority=RemediationPriority.MEDIUM,
                    rationale="Evidence-based diagnostic",
                    evidence_references=("missing",),
                    requires_human_approval=True,
                    classification=ActionClassification.NON_DESTRUCTIVE,
                    expected_verification_step="Verify observed state",
                ),
            )
        },
        {
            "conflicting_evidence": (
                ConflictingEvidence(
                    conflict_id="c1",
                    description="Synthetic conflict",
                    evidence_ids=("e1", "missing"),
                ),
            )
        },
        {
            "related_previous_incidents": (
                IncidentMatch(
                    incident_id="prior",
                    similarity_score=0.8,
                    match_reasons=("same target asset",),
                    evidence_ids=("missing",),
                ),
            )
        },
    ],
    ids=[
        "inferred-finding",
        "root-cause",
        "blast-radius",
        "report-owner",
        "remediation",
        "conflict",
        "previous-incident",
    ],
)
def test_report_rejects_unsupported_evidence_from_every_evidence_bearing_field(
    evidence_factory,
    changes,
):
    report = _report(evidence_factory, (evidence_factory("e1"),), ())
    values = report.model_dump()
    values.update(changes)
    with pytest.raises(ValidationError, match="missing"):
        IncidentReport.model_validate(values)


def test_report_rejects_unsupported_target_asset_owner_evidence(evidence_factory):
    report = _report(evidence_factory, (evidence_factory("e1"),), ())
    owner = Ownership(
        owner_id="owner:1",
        display_name="Owner",
        owner_type="custodian",
        kind=OwnerKind.TEAM,
        evidence_id="missing",
    )
    target = report.target_asset.model_copy(update={"owners": (owner,)})
    values = report.model_dump()
    values["target_asset"] = target
    with pytest.raises(ValidationError, match="missing"):
        IncidentReport.model_validate(values)


def test_report_rejects_unsupported_evidence_record_conflict_reference(evidence_factory):
    with pytest.raises(ValidationError, match="missing"):
        _report(
            evidence_factory,
            (evidence_factory("e1", conflicts=("missing",)),),
            (),
        )


def test_report_accepts_references_closed_over_the_evidence_ledger(evidence_factory):
    evidence = evidence_factory("e1")
    finding = ConfirmedFinding(finding_id="f1", statement="Observed", evidence_ids=("e1",))
    report = _report(evidence_factory, (evidence,), (finding,))
    assert report.confirmed_findings == (finding,)


def test_confidence_range_is_validated():
    for value in (-0.01, 1.01):
        with pytest.raises(ValidationError):
            ConfidenceAssessment(confidence=value, factors=(), penalties=())


def test_remediation_destructive_actions_require_approval():
    with pytest.raises(ValidationError, match="requires human approval"):
        RemediationAction(
            action_id="a1",
            title="Change state",
            description="A synthetic external change",
            priority=RemediationPriority.HIGH,
            rationale="Evidence supports a controlled action",
            evidence_references=("e1",),
            requires_human_approval=False,
            classification=ActionClassification.DESTRUCTIVE,
            expected_verification_step="Read back persisted state",
        )


def test_canonical_json_is_stable_and_enums_are_predictable(evidence_factory):
    report = _report(evidence_factory, (evidence_factory("e1"),), ())
    first = canonical_json(report)
    second = canonical_json(report)
    assert first == second
    parsed = json.loads(first)
    assert parsed["status"] == "INVESTIGATED"
    assert parsed["created_at"].endswith("Z")
    assert first == canonical_json(IncidentReport.model_validate(report.model_dump()))
