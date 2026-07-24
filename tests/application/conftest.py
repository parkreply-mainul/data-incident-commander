from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data_incident_commander.application.services import (
    InvestigationService,
    UnconfiguredEvidenceProvider,
)
from data_incident_commander.application.protocols import EvidenceProviderReadiness
from data_incident_commander.domain.models import (
    AssetIdentity,
    BlastRadiusResult,
    ConfidenceAssessment,
    IncidentReport,
    IncidentState,
    Severity,
    SeverityAssessment,
)
from data_incident_commander.repositories.memory import InMemoryIncidentRepository


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


class FixedIds:
    def __init__(self, *values: str) -> None:
        self.values = iter(values)

    def new_id(self) -> str:
        return next(self.values)


class SteppingClock:
    def __init__(self) -> None:
        self.index = 0

    def now(self) -> datetime:
        value = NOW + timedelta(seconds=self.index)
        self.index += 1
        return value


class ReportProvider:
    def __init__(self, report) -> None:
        self.report = report
        self.calls = 0

    @property
    def readiness(self):
        return EvidenceProviderReadiness(
            dependency_name="report provider",
            status="ready",
            configured=True,
            available=True,
            supports_datahub=True,
            supports_mcp=True,
            supports_writeback=False,
        )

    def investigate(self, record):
        self.calls += 1
        return self.report


def build_service(*ids: str):
    repository = InMemoryIncidentRepository()
    service = InvestigationService(
        repository,
        UnconfiguredEvidenceProvider(),
        id_provider=FixedIds(*ids),
        clock=SteppingClock(),
    )
    return service, repository


def build_report(
    *,
    incident_id: str,
    target_asset_id: str,
    title: str,
    status: IncidentState = IncidentState.INVESTIGATED,
) -> IncidentReport:
    return IncidentReport(
        incident_id=incident_id,
        title=title,
        target_asset=AssetIdentity(
            external_id=target_asset_id,
            display_name=target_asset_id,
            asset_type="dataset",
            platform="synthetic-test",
        ),
        status=status,
        root_cause=None,
        blast_radius=BlastRadiusResult(
            root_asset_id=target_asset_id,
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
        confirmed_findings=(),
        inferred_findings=(),
        unknowns=(),
        conflicting_evidence=(),
        owners=(),
        remediation_actions=(),
        evidence_ledger=(),
        related_previous_incidents=(),
        created_at=NOW,
        updated_at=NOW,
        engine_version="test-1",
    )
