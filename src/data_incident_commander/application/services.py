"""Deterministic use cases around the framework-independent domain."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
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
    WritebackVerificationFailure,
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
    MUTATION_IN_PROGRESS = "DataHub mutation is in progress."
    VERIFICATION_PENDING = (
        "DataHub mutation was attempted; read-back verification is pending."
    )

    def __init__(
        self,
        repository: IncidentRepository,
        evidence_provider: EvidenceProvider,
        *,
        writeback_provider: object | None = None,
        id_provider: IncidentIdProvider | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.repository = repository
        self.evidence_provider = evidence_provider
        self.writeback_provider = writeback_provider
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
        readiness = self.evidence_provider.readiness
        if not (
            readiness.configured
            and readiness.available
            and readiness.supports_datahub
            and readiness.supports_mcp
        ):
            raise DependencyUnavailable(
                "A verified and ready DataHub MCP evidence provider is required."
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
        expected_binding = self.payload_binding(record)
        if expected_binding is not None and command.payload_binding_id != expected_binding:
            raise InvalidWorkflowTransition(
                "Approval payload binding does not match the investigated report."
            )
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

    @staticmethod
    def payload_binding(record: InvestigationRecord) -> str | None:
        if record.report is None:
            return None
        payload = record.report.model_dump_json(exclude={"updated_at"})
        return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

    def writeback(self, incident_id: str, command: ActorCommand) -> InvestigationRecord:
        record = self.get(incident_id)
        if record.workflow.current_state not in {
            IncidentState.APPROVED,
            IncidentState.WRITEBACK_PENDING,
        }:
            raise InvalidWorkflowTransition(
                f"{record.workflow.current_state.value} -> WRITEBACK_PENDING is invalid"
            )
        if record.payload_binding_id != self.payload_binding(record):
            raise InvalidWorkflowTransition("Approved payload binding is no longer valid.")
        provider = self.writeback_provider or self.evidence_provider
        verifier = getattr(provider, "verify_writeback", None)
        if verifier is None:
            raise DependencyUnavailable(
                "The evidence provider does not support write-back verification."
            )
        if record.workflow.current_state is IncidentState.WRITEBACK_PENDING:
            if record.last_action_reason != self.VERIFICATION_PENDING:
                raise InvalidWorkflowTransition(
                    "DataHub mutation is still in progress; verification cannot start yet."
                )
            return self._verify_writeback(record, verifier)
        readiness = provider.readiness
        if not (
            readiness.configured
            and readiness.available
            and readiness.supports_datahub
            and readiness.supports_writeback
        ):
            raise DependencyUnavailable(
                "Approval-gated DataHub write-back is disabled or unavailable."
            )
        mutator = getattr(provider, "mutate_writeback", None)
        if mutator is None:
            raise DependencyUnavailable(
                "The evidence provider does not support controlled write-back."
            )
        now = self.clock.now()
        pending = record.workflow.transition(
            IncidentState.WRITEBACK_PENDING, actor=command.actor, occurred_at=now
        )
        pending_record = self.repository.save(
            record.model_copy(
                update={
                    "workflow": pending,
                    "last_action_reason": self.MUTATION_IN_PROGRESS,
                    "updated_at": now,
                }
            ),
            expected_revision=record.revision,
        )
        try:
            mutator(pending_record)
        except Exception as error:
            failed_at = self.clock.now()
            if isinstance(error, WritebackVerificationFailure):
                self.repository.save(
                    pending_record.model_copy(
                        update={
                            "last_action_reason": self.VERIFICATION_PENDING,
                            "updated_at": failed_at,
                        }
                    ),
                    expected_revision=pending_record.revision,
                )
                raise
            failed = pending_record.workflow.transition(
                IncidentState.FAILED,
                actor="datahub-writeback",
                occurred_at=failed_at,
                failure_reason="DataHub write-back or read-back verification failed.",
            )
            self.repository.save(
                pending_record.model_copy(
                    update={
                        "workflow": failed,
                        "last_action_reason": (
                            "DataHub write-back or read-back verification failed."
                        ),
                        "updated_at": failed_at,
                    }
                ),
                expected_revision=pending_record.revision,
            )
            raise
        verification_at = self.clock.now()
        verification_record = self.repository.save(
            pending_record.model_copy(
                update={
                    "last_action_reason": self.VERIFICATION_PENDING,
                    "updated_at": verification_at,
                }
            ),
            expected_revision=pending_record.revision,
        )
        return self._verify_writeback(verification_record, verifier)

    def _verify_writeback(self, pending_record, verifier):
        receipt = verifier(pending_record)
        report = pending_record.report.model_copy(
            update={
                "evidence_ledger": pending_record.report.evidence_ledger + (receipt,),
                "updated_at": self.clock.now(),
            }
        )
        recorded_at = self.clock.now()
        recorded = pending_record.workflow.transition(
            IncidentState.RECORDED, actor="datahub-readback-verifier", occurred_at=recorded_at
        )
        return self.repository.save(
            pending_record.model_copy(
                update={"workflow": recorded, "report": report, "updated_at": recorded_at}
            ),
            expected_revision=pending_record.revision,
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
