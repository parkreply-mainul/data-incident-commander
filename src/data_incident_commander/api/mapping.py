"""Explicit mapping from immutable application records to HTTP contracts."""

from __future__ import annotations

from data_incident_commander.application.records import InvestigationRecord
from data_incident_commander.domain.base import thaw_mapping

from .schemas import InvestigationResponse, TransitionResponse
from data_incident_commander.application.services import InvestigationService


def investigation_response(record: InvestigationRecord) -> InvestigationResponse:
    history = tuple(
        TransitionResponse(
            from_state=transition.from_state.value,
            to_state=transition.to_state.value,
            actor=transition.actor,
            occurred_at=transition.occurred_at,
            approval_reason=transition.approval_reason,
            failure_reason=transition.failure_reason,
            retry_action=transition.retry_action,
            approval_remains_valid=transition.approval_remains_valid,
            payload_binding_unchanged=transition.payload_binding_unchanged,
        )
        for transition in record.workflow.history
    )
    return InvestigationResponse(
        incident_id=record.incident_id,
        revision=record.revision,
        title=record.title,
        target_asset_id=record.target_asset_id,
        description=record.description,
        issue_category=record.issue_category,
        requester=None if record.requester is None else thaw_mapping(record.requester),
        state=record.workflow.current_state.value,
        history=history,
        payload_binding_id=record.payload_binding_id,
        expected_payload_binding_id=InvestigationService.payload_binding(record),
        last_action_reason=record.last_action_reason,
        report=None if record.report is None else record.report.model_dump(mode="json"),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
