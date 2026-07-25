from __future__ import annotations

import pytest

from data_incident_commander.application.commands import (
    ActorCommand,
    ApprovalCommand,
    CreateInvestigation,
    RetryCommand,
)
from data_incident_commander.application.errors import (
    DependencyUnavailable,
    IncidentConflict,
    IncidentNotFound,
    InvalidWorkflowTransition,
    ProviderOutputMismatch,
)
from data_incident_commander.application.protocols import EvidenceProviderReadiness
from data_incident_commander.application.services import InvestigationService
from data_incident_commander.domain.models import IncidentState

from .conftest import ReportProvider, build_report, build_service


class CountingUnavailableProvider:
    def __init__(self) -> None:
        self.calls = 0

    @property
    def readiness(self):
        return EvidenceProviderReadiness(
            dependency_name="counting provider",
            status="unavailable",
            configured=True,
            available=False,
            supports_datahub=True,
            supports_mcp=True,
            supports_writeback=False,
        )

    def investigate(self, record):
        self.calls += 1
        raise DependencyUnavailable("unavailable")


def test_draft_creation_uses_injected_id_and_time_without_evidence():
    service, _ = build_service("incident-fixed")
    record = service.create_draft(
        CreateInvestigation(title="Draft", target_asset_id="asset:target")
    )
    assert record.incident_id == "incident-fixed"
    assert record.revision == 1
    assert record.workflow.current_state is IncidentState.DRAFT
    assert record.report is None
    assert record.created_at == record.updated_at


def test_duplicate_generated_id_is_a_conflict():
    service, _ = build_service("duplicate", "duplicate")
    command = CreateInvestigation(title="Draft", target_asset_id="asset:target")
    service.create_draft(command)
    with pytest.raises(IncidentConflict):
        service.create_draft(command)


def test_missing_incident_is_not_found():
    service, _ = build_service()
    with pytest.raises(IncidentNotFound):
        service.get("missing")


def test_unconfigured_investigation_fails_without_mutating_draft():
    service, repository = build_service("incident")
    record = service.create_draft(CreateInvestigation(title="Draft", target_asset_id="asset"))
    with pytest.raises(DependencyUnavailable):
        service.investigate(record.incident_id)
    stored = repository.get(record.incident_id)
    assert stored.workflow.current_state is IncidentState.DRAFT
    assert stored.report is None


def test_unready_mcp_is_rejected_before_provider_collection():
    service, repository = build_service("incident")
    provider = CountingUnavailableProvider()
    service.evidence_provider = provider
    record = service.create_draft(CreateInvestigation(title="Draft", target_asset_id="asset"))
    with pytest.raises(DependencyUnavailable):
        service.investigate(record.incident_id)
    assert provider.calls == 0
    assert repository.get(record.incident_id) == record


def test_nondraft_rejects_before_provider_or_persistence():
    service, repository = build_service("incident")
    provider = CountingUnavailableProvider()
    service.evidence_provider = provider
    draft = service.create_draft(CreateInvestigation(title="Draft", target_asset_id="asset"))
    investigated = draft.model_copy(
        update={
            "workflow": draft.workflow.transition(
                IncidentState.INVESTIGATED,
                actor="prepared",
                occurred_at=service.clock.now(),
            )
        }
    )
    stored = repository.save(investigated, expected_revision=draft.revision)
    with pytest.raises(InvalidWorkflowTransition):
        service.investigate(draft.incident_id)
    assert provider.calls == 0
    assert repository.get(draft.incident_id) == stored
    assert repository.get(draft.incident_id).workflow.history == stored.workflow.history


def test_matching_provider_report_transitions_and_persists():
    service, repository = build_service("incident")
    draft = service.create_draft(
        CreateInvestigation(title="Draft title", target_asset_id="asset:target")
    )
    report = build_report(
        incident_id=draft.incident_id,
        target_asset_id=draft.target_asset_id,
        title=draft.title,
    )
    provider = ReportProvider(report)
    service.evidence_provider = provider
    investigated = service.investigate(draft.incident_id)
    assert provider.calls == 1
    assert investigated.workflow.current_state is IncidentState.INVESTIGATED
    assert investigated.report == report
    assert investigated.revision == draft.revision + 1
    assert repository.get(draft.incident_id) == investigated


@pytest.mark.parametrize(
    ("incident_id", "target_asset_id", "title", "status"),
    (
        ("wrong-incident", "asset:target", "Draft title", IncidentState.INVESTIGATED),
        ("incident", "asset:wrong", "Draft title", IncidentState.INVESTIGATED),
        ("wrong-incident", "asset:wrong", "Draft title", IncidentState.INVESTIGATED),
        ("incident", "asset:target", "Draft title", IncidentState.DRAFT),
        ("incident", "asset:target", "Provider replacement title", IncidentState.INVESTIGATED),
    ),
    ids=("wrong-incident", "wrong-target", "both-wrong", "wrong-status", "wrong-title"),
)
def test_mismatched_provider_report_preserves_original_draft(
    incident_id,
    target_asset_id,
    title,
    status,
):
    service, repository = build_service("incident")
    draft = service.create_draft(
        CreateInvestigation(title="Draft title", target_asset_id="asset:target")
    )
    service.evidence_provider = ReportProvider(
        build_report(
            incident_id=incident_id,
            target_asset_id=target_asset_id,
            title=title,
            status=status,
        )
    )
    with pytest.raises(ProviderOutputMismatch):
        service.investigate(draft.incident_id)
    stored = repository.get(draft.incident_id)
    assert stored == draft
    assert stored.revision == 1
    assert stored.workflow.history == ()
    assert stored.report is None


@pytest.mark.parametrize(
    "operation",
    (
        lambda service, incident_id: service.submit_for_approval(
            incident_id, ActorCommand(actor="actor")
        ),
        lambda service, incident_id: service.approve(
            incident_id,
            ApprovalCommand(actor="actor", reason="reviewed", payload_binding_id="sha256:x"),
        ),
        lambda service, incident_id: service.resolve(
            incident_id, ActorCommand(actor="actor")
        ),
        lambda service, incident_id: service.retry(
            incident_id, RetryCommand(actor="actor", reason="retry")
        ),
    ),
)
def test_invalid_application_transition_maps_domain_error(operation):
    service, _ = build_service("incident")
    record = service.create_draft(CreateInvestigation(title="Draft", target_asset_id="asset"))
    with pytest.raises(InvalidWorkflowTransition):
        operation(service, record.incident_id)


def test_valid_prepared_transitions_preserve_audit_history():
    service, repository = build_service("incident")
    record = service.create_draft(CreateInvestigation(title="Draft", target_asset_id="asset"))
    investigated = record.model_copy(
        update={
            "workflow": record.workflow.transition(
                IncidentState.INVESTIGATED,
                actor="test-provider",
                occurred_at=service.clock.now(),
            )
        }
    )
    repository.save(investigated, expected_revision=record.revision)
    awaiting = service.submit_for_approval(
        record.incident_id, ActorCommand(actor="review-coordinator")
    )
    approved = service.approve(
        record.incident_id,
        ApprovalCommand(
            actor="reviewer",
            reason="Evidence accepted",
            payload_binding_id="sha256:approved",
        ),
    )
    assert awaiting.workflow.current_state is IncidentState.AWAITING_APPROVAL
    assert approved.workflow.current_state is IncidentState.APPROVED
    assert len(approved.workflow.history) == 3
    assert approved.payload_binding_id == "sha256:approved"
