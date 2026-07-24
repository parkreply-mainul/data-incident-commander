"""Deterministic use cases around the framework-independent domain."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from data_incident_commander.domain.models import IncidentState
from data_incident_commander.domain.state_machine import InvalidStateTransition

from .commands import ActorCommand, ApprovalCommand, CreateInvestigation, RetryCommand
from .errors import (
    DependencyUnavailable,
    IncidentConflict,
    IncidentNotFound,
    InvalidWorkflowTransition,
    ProviderOutputMismatch,
)
from .protocols import (
    Clock,
    EvidenceProvider,
    EvidenceProviderReadiness,
    IncidentIdProvider,
    IncidentRepository,
)
from .records import InvestigationPage, InvestigationRecord


class UuidIncidentIdProvider:
    def new_id(self) -> str:
        return str(uuid4())


class UtcClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class UnconfiguredEvidenceProvider:
    @property
    def readiness(self) -> EvidenceProviderReadiness:
        return EvidenceProviderReadiness(
            dependency_name="DataHub MCP evidence provider",
            status="not_configured",
            configured=False,
            available=False,
            supports_datahub=False,
            supports_mcp=False,
            supports_writeback=False,
        )

    def investigate(self, record: InvestigationRecord):
        raise DependencyUnavailable(
            "A verified DataHub MCP evidence provider is not configured."
        )


class InvestigationService:
    def __init__(
        self,
        repository: IncidentRepository,
        evidence_provider: EvidenceProvider,
        *,
        id_provider: IncidentIdProvider | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.repository = repository
        self.evidence_provider = evidence_provider
        self.id_provider = id_provider or UuidIncidentIdProvider()
        self.clock = clock or UtcClock()

    def create_draft(self, command: CreateInvestigation) -> InvestigationRecord:
        incident_id = self.id_provider.new_id()
        now = self.clock.now()
        record = InvestigationRecord(
            incident_id=incident_id,
            title=command.title,
            target_asset_id=command.target_asset_id,
            description=command.description,
            issue_category=command.issue_category,
            requester=command.requester,
            workflow={"current_state": IncidentState.DRAFT, "history": ()},
            created_at=now,
            updated_at=now,
        )
        try:
            return self.repository.create(record)
        except IncidentConflict:
            raise

    def get(self, incident_id: str) -> InvestigationRecord:
        record = self.repository.get(incident_id)
        if record is None:
            raise IncidentNotFound("The requested incident does not exist.")
        return record

    def list(self, *, offset: int, limit: int) -> InvestigationPage:
        return self.repository.page(offset=offset, limit=limit)

    def investigate(self, incident_id: str) -> InvestigationRecord:
        record = self.get(incident_id)
        if record.workflow.current_state is not IncidentState.DRAFT:
            raise InvalidWorkflowTransition(
                f"{record.workflow.current_state.value} -> INVESTIGATED is invalid"
            )
        report = self.evidence_provider.investigate(record)
        mismatches: list[str] = []
        if report.incident_id != record.incident_id:
            mismatches.append("incident identifier")
        if report.target_asset.external_id != record.target_asset_id:
            mismatches.append("target asset identifier")
        if report.status is not IncidentState.INVESTIGATED:
            mismatches.append("report status")
        if report.title != record.title:
            mismatches.append("incident title")
        if (
            record.issue_category is not None
            and report.root_cause is not None
            and report.root_cause.issue_category != record.issue_category
        ):
            mismatches.append("issue category")
        if mismatches:
            raise ProviderOutputMismatch(
                "Provider report does not match the requested incident: "
                + ", ".join(mismatches)
            )
        now = self.clock.now()
        try:
            workflow = record.workflow.transition(
                IncidentState.INVESTIGATED,
                actor="evidence-provider",
                occurred_at=now,
            )
        except InvalidStateTransition as error:
            raise InvalidWorkflowTransition(str(error)) from None
        return self.repository.save(
            record.model_copy(update={"workflow": workflow, "report": report, "updated_at": now}),
            expected_revision=record.revision,
        )

    def submit_for_approval(self, incident_id: str, command: ActorCommand) -> InvestigationRecord:
        return self._transition(
            self.get(incident_id), IncidentState.AWAITING_APPROVAL, command.actor
        )

    def approve(self, incident_id: str, command: ApprovalCommand) -> InvestigationRecord:
        record = self.get(incident_id)
        now = self.clock.now()
        try:
            workflow = record.workflow.transition(
                IncidentState.APPROVED,
                actor=command.actor,
                occurred_at=now,
                approval_reason=command.reason,
            )
        except InvalidStateTransition as error:
            raise InvalidWorkflowTransition(str(error)) from None
        return self.repository.save(
            record.model_copy(
                update={
                    "workflow": workflow,
                    "payload_binding_id": command.payload_binding_id,
                    "last_action_reason": command.reason,
                    "updated_at": now,
                }
            ),
            expected_revision=record.revision,
        )

    def retry(self, incident_id: str, command: RetryCommand) -> InvestigationRecord:
        record = self.get(incident_id)
        now = self.clock.now()
        try:
            workflow = record.workflow.retry(
                actor=command.actor,
                occurred_at=now,
                approval_remains_valid=command.approval_remains_valid,
                payload_binding_unchanged=command.payload_binding_unchanged,
            )
        except InvalidStateTransition as error:
            raise InvalidWorkflowTransition(str(error)) from None
        return self.repository.save(
            record.model_copy(
                update={
                    "workflow": workflow,
                    "last_action_reason": command.reason,
                    "updated_at": now,
                }
            ),
            expected_revision=record.revision,
        )

    def resolve(self, incident_id: str, command: ActorCommand) -> InvestigationRecord:
        return self._transition(self.get(incident_id), IncidentState.RESOLVED, command.actor)

    def _transition(
        self,
        record: InvestigationRecord,
        state: IncidentState,
        actor: str,
    ) -> InvestigationRecord:
        now = self.clock.now()
        try:
            workflow = record.workflow.transition(state, actor=actor, occurred_at=now)
        except InvalidStateTransition as error:
            raise InvalidWorkflowTransition(str(error)) from None
        return self.repository.save(
            record.model_copy(update={"workflow": workflow, "updated_at": now}),
            expected_revision=record.revision,
        )
