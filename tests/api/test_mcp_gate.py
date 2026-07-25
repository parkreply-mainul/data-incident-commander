import pytest

from data_incident_commander.api.app import create_app
from data_incident_commander.application.commands import CreateInvestigation
from data_incident_commander.application.errors import DependencyUnavailable
from data_incident_commander.application.services import InvestigationService
from data_incident_commander.config import Settings
from data_incident_commander.integrations.datahub.live import DataHubLiveEvidenceProvider
from tests.application.conftest import ReportProvider, build_report, build_service


def test_gms_url_alone_does_not_activate_investigation_evidence():
    app = create_app(
        settings=Settings(datahub_gms_url="http://datahub-gms:8080")
    )
    service = app.state.investigation_service

    assert not service.evidence_provider.readiness.supports_mcp
    assert isinstance(service.writeback_provider, DataHubLiveEvidenceProvider)


def test_direct_gms_cannot_bypass_mandatory_mcp_gate():
    app = create_app(
        settings=Settings(datahub_gms_url="http://datahub-gms:8080")
    )
    service = app.state.investigation_service
    draft = service.create_draft(
        CreateInvestigation(title="NYC Taxi stale", target_asset_id="urn:target")
    )

    with pytest.raises(
        DependencyUnavailable, match="verified and ready DataHub MCP"
    ):
        service.investigate(draft.incident_id)


def test_verified_ready_mcp_provider_allows_investigation():
    service, _ = build_service("verified-mcp")
    draft = service.create_draft(
        CreateInvestigation(title="NYC Taxi stale", target_asset_id="urn:target")
    )
    provider = ReportProvider(
        build_report(
            incident_id=draft.incident_id,
            target_asset_id=draft.target_asset_id,
            title=draft.title,
        )
    )
    service.evidence_provider = provider

    investigated = service.investigate(draft.incident_id)

    assert investigated.report is not None
    assert provider.calls == 1


def test_unready_mcp_fails_before_evidence_collection():
    class UnreadyMcp(ReportProvider):
        @property
        def readiness(self):
            return self._readiness.model_copy(update={"available": False})

        def investigate(self, record):
            raise AssertionError("unready MCP must not be called")

    ready = ReportProvider(None).readiness
    provider = UnreadyMcp(None)
    provider._readiness = ready
    service, _ = build_service("unready-mcp")
    service.evidence_provider = provider
    draft = service.create_draft(
        CreateInvestigation(title="NYC Taxi stale", target_asset_id="urn:target")
    )

    with pytest.raises(
        DependencyUnavailable, match="verified and ready DataHub MCP"
    ):
        service.investigate(draft.incident_id)
