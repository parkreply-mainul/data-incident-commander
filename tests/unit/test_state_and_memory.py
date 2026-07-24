from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from data_incident_commander.domain.memory import IncidentMemoryQuery, match_previous_incidents
from data_incident_commander.domain.models import (
    EvidenceType,
    IncidentState,
    PreviousIncidentRecord,
    StateTransition,
)
from data_incident_commander.domain.state_machine import (
    ApprovalStateMachine,
    InvalidStateTransition,
)

from .conftest import NOW


def test_complete_valid_human_approval_flow_records_actor_and_reason():
    machine = ApprovalStateMachine()
    flow = (
        IncidentState.INVESTIGATED,
        IncidentState.AWAITING_APPROVAL,
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
        IncidentState.RESOLVED,
    )
    for index, state in enumerate(flow):
        machine = machine.transition(
            state,
            actor="reviewer",
            occurred_at=NOW + timedelta(minutes=index),
            approval_reason="Evidence reviewed" if state is IncidentState.APPROVED else None,
        )
    assert machine.current_state is IncidentState.RESOLVED
    assert len(machine.history) == 6
    assert machine.history[2].approval_reason == "Evidence reviewed"


def test_invalid_transition_is_rejected():
    with pytest.raises(InvalidStateTransition):
        ApprovalStateMachine().transition(
            IncidentState.APPROVED,
            actor="reviewer",
            occurred_at=NOW,
            approval_reason="Skipped review",
        )


def test_approval_requires_reason():
    machine = ApprovalStateMachine()
    machine = machine.transition(
        IncidentState.INVESTIGATED,
        actor="engine",
        occurred_at=NOW,
    )
    machine = machine.transition(
        IncidentState.AWAITING_APPROVAL,
        actor="engine",
        occurred_at=NOW + timedelta(minutes=1),
    )
    with pytest.raises(InvalidStateTransition, match="approval_reason"):
        machine.transition(
            IncidentState.APPROVED,
            actor="reviewer",
            occurred_at=NOW + timedelta(minutes=2),
        )


def test_draft_failure_requires_reason_and_retries_only_to_draft():
    failed = ApprovalStateMachine().transition(
        IncidentState.FAILED,
        actor="engine",
        occurred_at=NOW,
        failure_reason="Evidence dependency unavailable",
    )
    retried = failed.retry(
        actor="reviewer",
        occurred_at=NOW + timedelta(minutes=1),
    )
    assert retried.current_state is IncidentState.DRAFT
    assert failed.history[0].failure_reason == "Evidence dependency unavailable"
    assert failed.failed_from_state is IncidentState.DRAFT
    assert failed.failure_reason == "Evidence dependency unavailable"
    assert failed.failed_at == NOW
    assert failed.failure_actor == "engine"


def test_draft_failure_cannot_reach_approval():
    failed = ApprovalStateMachine().transition(
        IncidentState.FAILED,
        actor="engine",
        occurred_at=NOW,
        failure_reason="Investigation unavailable",
    )
    with pytest.raises(InvalidStateTransition):
        failed.transition(
            IncidentState.AWAITING_APPROVAL,
            actor="reviewer",
            occurred_at=NOW + timedelta(minutes=1),
        )


@pytest.mark.parametrize(
    ("origin", "invalid_destination"),
    (
        (IncidentState.INVESTIGATED, IncidentState.APPROVED),
        (IncidentState.AWAITING_APPROVAL, IncidentState.WRITEBACK_PENDING),
    ),
)
def test_failure_retry_preserves_origin(origin, invalid_destination):
    machine = ApprovalStateMachine().transition(
        IncidentState.INVESTIGATED,
        actor="engine",
        occurred_at=NOW,
    )
    if origin is IncidentState.AWAITING_APPROVAL:
        machine = machine.transition(
            IncidentState.AWAITING_APPROVAL,
            actor="engine",
            occurred_at=NOW + timedelta(minutes=1),
        )
    failed = machine.transition(
        IncidentState.FAILED,
        actor="engine",
        occurred_at=NOW + timedelta(minutes=2),
        failure_reason="Stage operation failed",
    )
    with pytest.raises(InvalidStateTransition):
        failed.transition(
            invalid_destination,
            actor="operator",
            occurred_at=NOW + timedelta(minutes=3),
            approval_reason="invalid skip"
            if invalid_destination is IncidentState.APPROVED
            else None,
        )
    retried = failed.retry(
        actor="operator",
        occurred_at=NOW + timedelta(minutes=3),
    )
    assert retried.current_state is origin


def test_restored_failed_history_requires_valid_origin_and_retry_destination():
    invalid_history = (
        StateTransition(
            from_state=IncidentState.DRAFT,
            to_state=IncidentState.FAILED,
            actor="engine",
            occurred_at=NOW,
            failure_reason="failed",
        ),
        StateTransition(
            from_state=IncidentState.FAILED,
            to_state=IncidentState.AWAITING_APPROVAL,
            actor="operator",
            occurred_at=NOW + timedelta(minutes=1),
            retry_action=True,
        ),
    )
    with pytest.raises(ValidationError, match="invalid step"):
        ApprovalStateMachine(
            current_state=IncidentState.AWAITING_APPROVAL,
            history=invalid_history,
        )


def test_failure_reason_is_required_and_retry_history_is_immutable():
    with pytest.raises(InvalidStateTransition, match="failure_reason"):
        ApprovalStateMachine().transition(
            IncidentState.FAILED,
            actor="engine",
            occurred_at=NOW,
        )
    failed = ApprovalStateMachine().transition(
        IncidentState.FAILED,
        actor="engine",
        occurred_at=NOW,
        failure_reason="failed",
    )
    retried = failed.retry(
        actor="operator",
        occurred_at=NOW + timedelta(minutes=1),
    )
    assert failed.current_state is IncidentState.FAILED
    assert len(failed.history) == 1
    assert len(retried.history) == 2
    with pytest.raises(ValidationError):
        retried.history = ()


def test_approved_failure_retry_requires_preserved_approval_and_payload_binding():
    machine = ApprovalStateMachine()
    for index, state in enumerate(
        (
            IncidentState.INVESTIGATED,
            IncidentState.AWAITING_APPROVAL,
            IncidentState.APPROVED,
        )
    ):
        machine = machine.transition(
            state,
            actor="reviewer",
            occurred_at=NOW + timedelta(minutes=index),
            approval_reason="approved" if state is IncidentState.APPROVED else None,
        )
    failed = machine.transition(
        IncidentState.FAILED,
        actor="writer",
        occurred_at=NOW + timedelta(minutes=3),
        failure_reason="write preparation failed",
    )
    with pytest.raises(InvalidStateTransition, match="unchanged payload binding"):
        failed.retry(
            actor="operator",
            occurred_at=NOW + timedelta(minutes=4),
        )
    retried = failed.retry(
        actor="operator",
        occurred_at=NOW + timedelta(minutes=4),
        approval_remains_valid=True,
        payload_binding_unchanged=True,
    )
    assert retried.current_state is IncidentState.APPROVED
    assert retried.history[-1].retry_action is True
    assert retried.history[-1].approval_remains_valid is True
    assert retried.history[-1].payload_binding_unchanged is True


def _failed_machine_from(origin: IncidentState) -> ApprovalStateMachine:
    machine = ApprovalStateMachine()
    path = (
        IncidentState.INVESTIGATED,
        IncidentState.AWAITING_APPROVAL,
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
    )
    for index, state in enumerate(path):
        if origin is IncidentState.DRAFT:
            break
        machine = machine.transition(
            state,
            actor="operator",
            occurred_at=NOW + timedelta(minutes=index),
            approval_reason="approved" if state is IncidentState.APPROVED else None,
        )
        if state is origin:
            break
    return machine.transition(
        IncidentState.FAILED,
        actor="engine",
        occurred_at=NOW + timedelta(minutes=10),
        failure_reason="stage failed",
    )


@pytest.mark.parametrize(
    "origin",
    (
        IncidentState.DRAFT,
        IncidentState.INVESTIGATED,
        IncidentState.AWAITING_APPROVAL,
    ),
)
@pytest.mark.parametrize(
    "confirmations",
    (
        {"approval_remains_valid": True},
        {"payload_binding_unchanged": True},
    ),
)
def test_preapproval_retry_rejects_postapproval_confirmations_with_domain_error(
    origin,
    confirmations,
):
    failed = _failed_machine_from(origin)
    with pytest.raises(
        InvalidStateTransition,
        match="valid only for post-approval retry",
    ):
        failed.retry(
            actor="operator",
            occurred_at=NOW + timedelta(minutes=11),
            **confirmations,
        )


def test_nonapproved_retry_accepts_omitted_approval_validity():
    failed = _failed_machine_from(IncidentState.INVESTIGATED)
    retried = failed.retry(
        actor="operator",
        occurred_at=NOW + timedelta(minutes=11),
    )
    assert retried.current_state is IncidentState.INVESTIGATED
    assert retried.history[-1].approval_remains_valid is False
    assert retried.history[-1].payload_binding_unchanged is False


@pytest.mark.parametrize(
    "origin",
    (
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
    ),
)
@pytest.mark.parametrize(
    "confirmations",
    (
        {},
        {"approval_remains_valid": True},
        {"payload_binding_unchanged": True},
    ),
)
def test_postapproval_retry_requires_both_confirmations(origin, confirmations):
    failed = _failed_machine_from(origin)
    with pytest.raises(
        InvalidStateTransition,
        match="valid approval and unchanged payload binding",
    ):
        failed.retry(
            actor="operator",
            occurred_at=NOW + timedelta(minutes=11),
            **confirmations,
        )


@pytest.mark.parametrize(
    "origin",
    (
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
    ),
)
def test_postapproval_retry_accepts_both_confirmations(origin):
    failed = _failed_machine_from(origin)
    retried = failed.retry(
        actor="operator",
        occurred_at=NOW + timedelta(minutes=11),
        approval_remains_valid=True,
        payload_binding_unchanged=True,
    )
    assert retried.current_state is origin
    assert retried.history[-1].approval_remains_valid is True
    assert retried.history[-1].payload_binding_unchanged is True


@pytest.mark.parametrize(
    "origin",
    (
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
    ),
)
def test_restored_postapproval_retry_requires_both_confirmations(origin):
    failed = _failed_machine_from(origin)
    forged_retry = StateTransition(
        from_state=IncidentState.FAILED,
        to_state=origin,
        actor="operator",
        occurred_at=NOW + timedelta(minutes=11),
        retry_action=True,
        approval_remains_valid=True,
        payload_binding_unchanged=False,
    )
    with pytest.raises(ValidationError):
        ApprovalStateMachine(
            current_state=origin,
            history=failed.history + (forged_retry,),
        )


def test_restored_retry_requires_explicit_retry_action():
    history = (
        StateTransition(
            from_state=IncidentState.DRAFT,
            to_state=IncidentState.FAILED,
            actor="engine",
            occurred_at=NOW,
            failure_reason="failed",
        ),
        StateTransition(
            from_state=IncidentState.FAILED,
            to_state=IncidentState.DRAFT,
            actor="operator",
            occurred_at=NOW + timedelta(minutes=1),
        ),
    )
    with pytest.raises(ValidationError, match="invalid step"):
        ApprovalStateMachine(current_state=IncidentState.DRAFT, history=history)


def test_transition_history_is_immutable():
    original = ApprovalStateMachine()
    transitioned = original.transition(
        IncidentState.INVESTIGATED,
        actor="engine",
        occurred_at=NOW,
    )
    assert original.current_state is IncidentState.DRAFT
    assert original.history == ()
    with pytest.raises(ValidationError):
        transitioned.history = ()


def test_direct_non_draft_construction_without_history_is_rejected():
    with pytest.raises(ValidationError, match="does not agree"):
        ApprovalStateMachine(current_state=IncidentState.APPROVED)


def test_restored_state_must_match_history_tail():
    history = (
        StateTransition(
            from_state=IncidentState.DRAFT,
            to_state=IncidentState.INVESTIGATED,
            actor="engine",
            occurred_at=NOW,
        ),
    )
    with pytest.raises(ValidationError, match="does not agree"):
        ApprovalStateMachine(
            current_state=IncidentState.AWAITING_APPROVAL,
            history=history,
        )


def test_restored_history_must_be_contiguous_from_draft():
    history = (
        StateTransition(
            from_state=IncidentState.INVESTIGATED,
            to_state=IncidentState.AWAITING_APPROVAL,
            actor="engine",
            occurred_at=NOW,
        ),
    )
    with pytest.raises(ValidationError, match="contiguous from DRAFT"):
        ApprovalStateMachine(
            current_state=IncidentState.AWAITING_APPROVAL,
            history=history,
        )


def test_valid_existing_machine_can_be_restored_from_complete_history():
    original = ApprovalStateMachine().transition(
        IncidentState.INVESTIGATED,
        actor="engine",
        occurred_at=NOW,
    )
    restored = ApprovalStateMachine.model_validate(original.model_dump())
    assert restored == original


def _record(
    incident_id: str,
    *,
    target: str = "asset:target",
    root: str | None = "asset:root",
    title: str = "Prior incident",
):
    return PreviousIncidentRecord(
        incident_id=incident_id,
        target_asset_id=target,
        root_cause_asset_id=root,
        issue_category="freshness",
        evidence_types=(EvidenceType.FRESHNESS_SIGNAL,),
        affected_asset_ids=("asset:dashboard",),
        title=title,
        resolved_at=NOW,
    )


def test_incident_memory_matching_is_explainable_and_deterministic():
    query = IncidentMemoryQuery(
        target_asset_id="asset:target",
        root_cause_asset_id="asset:root",
        issue_category="freshness",
        evidence_types=(EvidenceType.FRESHNESS_SIGNAL,),
        affected_asset_ids=("asset:dashboard",),
        threshold=0.5,
    )
    result = match_previous_incidents(query, (_record("z"), _record("a")))
    assert tuple(match.incident_id for match in result.matches) == ("a", "z")
    assert result.matches[0].similarity_score == 1.0
    assert result.matches[0].match_reasons == (
        "same root-cause asset",
        "same target asset",
        "same issue category",
        "overlapping evidence type",
        "overlapping affected asset",
    )


def test_display_name_similarity_alone_never_matches():
    query = IncidentMemoryQuery(
        target_asset_id="different:target",
        root_cause_asset_id="different:root",
        issue_category="quality",
        evidence_types=(EvidenceType.QUALITY_ASSERTION,),
        affected_asset_ids=("different:asset",),
        threshold=0.1,
    )
    record = _record(
        "prior",
        target="old:target",
        root="old:root",
        title="different target",
    )
    assert match_previous_incidents(query, (record,)).matches == ()


def test_zero_threshold_never_returns_an_unrelated_incident():
    query = IncidentMemoryQuery(
        target_asset_id="different:target",
        root_cause_asset_id="different:root",
        issue_category="quality",
        evidence_types=(EvidenceType.QUALITY_ASSERTION,),
        affected_asset_ids=("different:asset",),
        threshold=0.0,
    )
    assert match_previous_incidents(query, (_record("unrelated"),)).matches == ()


def test_zero_threshold_returns_incident_with_one_positive_reason():
    query = IncidentMemoryQuery(
        target_asset_id="asset:target",
        root_cause_asset_id="different:root",
        issue_category="quality",
        evidence_types=(EvidenceType.QUALITY_ASSERTION,),
        affected_asset_ids=("different:asset",),
        threshold=0.0,
    )
    result = match_previous_incidents(query, (_record("target-match"),))
    assert len(result.matches) == 1
    assert result.matches[0].similarity_score == 0.25
    assert result.matches[0].match_reasons == ("same target asset",)


def test_memory_threshold_boundary_is_configurable():
    query = IncidentMemoryQuery(
        target_asset_id="asset:target",
        issue_category="other",
        evidence_types=(),
        affected_asset_ids=(),
        threshold=0.25,
    )
    assert len(match_previous_incidents(query, (_record("prior"),)).matches) == 1
    stricter = query.model_copy(update={"threshold": 0.26})
    assert match_previous_incidents(stricter, (_record("prior"),)).matches == ()
