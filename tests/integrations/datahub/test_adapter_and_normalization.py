from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from data_incident_commander.domain.models import EvidenceType, OwnerKind
from data_incident_commander.api.app import create_app
from data_incident_commander.application.commands import CreateInvestigation
from data_incident_commander.application.errors import DependencyUnavailable
from data_incident_commander.config import Settings
from data_incident_commander.integrations.datahub.adapter import DataHubMcpEvidenceProvider
from data_incident_commander.integrations.datahub.capabilities import (
    CapabilityInventory,
    CapabilityName,
)
from data_incident_commander.integrations.datahub.client_protocol import (
    McpToolDescriptor,
    VerifiedToolResult,
)
from data_incident_commander.integrations.datahub.errors import (
    McpUnavailable,
    MutationDisabled,
    NormalizationFailure,
    ToolInventoryUnavailable,
)
from data_incident_commander.integrations.datahub.normalization import (
    VerifiedAssetDto,
    VerifiedLineageEdgeDto,
    VerifiedOwnerDto,
    VerifiedSignalDto,
    VerifiedSignalKind,
    normalize_asset,
    normalize_lineage,
    normalize_signal,
)
from data_incident_commander.integrations.datahub.readiness import readiness_summary

from .test_config_and_capabilities import config, observed_inventory
from tests.api.conftest import SyncASGIClient
from tests.application.conftest import build_service


NOW = datetime(2026, 7, 24, 12, tzinfo=timezone.utc)


class ControlledClient:
    def __init__(self, ready: bool = True) -> None:
        self._ready = ready
        self.closed = False

    @property
    def ready(self) -> bool:
        return self._ready

    def initialize(self) -> None:
        self._ready = True

    def list_tools(self) -> tuple[McpToolDescriptor, ...]:
        return (
            McpToolDescriptor(
                name="search",
                schema_fingerprint="controlled-test-only",
                read_only=True,
            ),
        )

    def invoke(self, tool_name, arguments):
        return VerifiedToolResult(tool_name=tool_name, observed_at=NOW, payload={"ok": True})

    def close(self) -> None:
        self.closed = True


def test_configured_provider_without_client_is_honestly_unavailable():
    provider = DataHubMcpEvidenceProvider(config())
    assert provider.readiness.configured
    assert not provider.readiness.available
    assert provider.readiness.status == "client_absent"
    assert provider.readiness.supports_datahub
    assert provider.readiness.supports_mcp
    assert not provider.readiness.supports_writeback
    with pytest.raises(McpUnavailable):
        provider.investigate(object())


def test_unavailable_client_and_unverified_inventory_have_distinct_statuses():
    unavailable = DataHubMcpEvidenceProvider(config(), client=ControlledClient(False))
    assert unavailable.readiness.status == "client_unavailable"
    unverified = DataHubMcpEvidenceProvider(config(), client=ControlledClient())
    assert unverified.readiness.status == "tool_inventory_unverified"
    with pytest.raises(ToolInventoryUnavailable):
        unverified.investigate(object())


def test_mutating_required_capability_keeps_provider_unverified_and_unavailable():
    baseline = observed_inventory()
    inventory = CapabilityInventory(
        server_version=baseline.server_version,
        observed_at=baseline.observed_at,
        capabilities=tuple(
            item.model_copy(update={"read_only": False})
            if item.name is CapabilityName.LINEAGE_PATHS
            else item
            for item in baseline.capabilities
        ),
    )
    provider = DataHubMcpEvidenceProvider(
        config(), client=ControlledClient(), inventory=inventory
    )
    assert provider.readiness.status == "tool_inventory_unverified"
    assert not provider.readiness.available
    with pytest.raises(ToolInventoryUnavailable):
        provider.investigate(object())


def test_observed_inventory_verifies_capabilities_but_not_operational_readiness():
    provider = DataHubMcpEvidenceProvider(
        config(), client=ControlledClient(), inventory=observed_inventory()
    )
    assert not provider.readiness.available
    assert (
        provider.readiness.status
        == "capabilities_verified_but_investigation_unimplemented"
    )
    summary = readiness_summary(provider)
    assert summary["client_available"] is True
    assert summary["required_tools_observed"] is True
    assert summary["capabilities_verified"] is True
    assert summary["adapter_normalization_verified"] is True
    assert summary["investigation_orchestration_implemented"] is False
    with pytest.raises(McpUnavailable, match="not implemented"):
        provider.investigate(object())


def test_readiness_summary_is_safe_and_mutation_stays_disabled():
    provider = DataHubMcpEvidenceProvider(config())
    summary = readiness_summary(provider)
    assert summary["configured"] is True
    assert summary["available"] is False
    assert summary["mutation_enabled"] is False
    with pytest.raises(MutationDisabled):
        provider.require_mutation()


def test_api_readiness_exposes_configured_but_unverified_adapter_honestly():
    service, _ = build_service()
    service.evidence_provider = DataHubMcpEvidenceProvider(config())
    client = SyncASGIClient(create_app(service=service, settings=Settings(service_version="test")))
    body = client.get("/health/readiness").json()
    assert body["status"] == "not_ready"
    assert body["components"]["evidence_provider"]["status"] == "unavailable"
    assert "client_absent" in body["components"]["evidence_provider"]["detail"]
    assert body["components"]["datahub"]["status"] == "unavailable"
    assert body["components"]["mcp"]["status"] == "unavailable"
    assert body["components"]["writeback"]["status"] == "disabled"


def test_api_never_reports_full_readiness_for_unimplemented_orchestration():
    service, _ = build_service()
    service.evidence_provider = DataHubMcpEvidenceProvider(
        config(), client=ControlledClient(), inventory=observed_inventory()
    )
    client = SyncASGIClient(
        create_app(service=service, settings=Settings(service_version="test"))
    )
    body = client.get("/health/readiness").json()
    assert body["status"] == "not_ready"
    assert body["components"]["evidence_provider"]["status"] == "unavailable"
    assert (
        "capabilities_verified_but_investigation_unimplemented"
        in body["components"]["evidence_provider"]["detail"]
    )
    assert body["components"]["datahub"]["status"] == "unavailable"
    assert body["components"]["mcp"]["status"] == "unavailable"
    assert body["components"]["writeback"]["status"] == "disabled"


def test_unimplemented_orchestration_produces_no_report_or_state_change():
    service, repository = build_service("incident-mcp-boundary")
    service.evidence_provider = DataHubMcpEvidenceProvider(
        config(), client=ControlledClient(), inventory=observed_inventory()
    )
    draft = service.create_draft(
        CreateInvestigation(
            title="Controlled integration boundary",
            target_asset_id="asset:controlled",
        )
    )

    with pytest.raises(
        DependencyUnavailable, match="verified and ready DataHub MCP"
    ):
        service.investigate(draft.incident_id)

    stored = repository.get(draft.incident_id)
    assert stored == draft
    assert stored is not None
    assert stored.report is None


def test_controlled_client_contract_is_library_neutral():
    client = ControlledClient()
    assert client.list_tools()[0].name == "search"
    assert client.invoke("search", {}).payload["ok"] is True
    client.close()
    assert client.closed


def asset(identifier: str, *, owner: bool = False) -> VerifiedAssetDto:
    owners = (
        VerifiedOwnerDto(
            owner_id="owner:analytics",
            display_name="Analytics",
            owner_type="technical",
            kind=OwnerKind.TEAM,
            evidence_id="evidence:owner",
        ),
    ) if owner else ()
    return VerifiedAssetDto(
        external_id=identifier,
        display_name=identifier,
        asset_type="dataset",
        platform="verified-test",
        owners=owners,
    )


def test_verified_asset_and_owner_normalize_without_invention():
    normalized = normalize_asset(asset("asset:a", owner=True))
    assert normalized.external_id == "asset:a"
    assert normalized.owners is not None
    assert normalized.owners[0].evidence_id == "evidence:owner"
    assert normalized.domain is None


def test_lineage_normalization_rejects_dangling_edges_and_node_limit():
    dangling = VerifiedLineageEdgeDto(
        upstream_id="asset:a", downstream_id="asset:missing", evidence_id="edge:1"
    )
    with pytest.raises(NormalizationFailure):
        normalize_lineage((asset("asset:a"),), (dangling,), maximum_nodes=10)
    with pytest.raises(NormalizationFailure, match="node limit"):
        normalize_lineage(
            (asset("asset:a"), asset("asset:b")), (), maximum_nodes=1
        )


def test_lineage_normalization_rejects_conflicting_duplicate_identities():
    with pytest.raises(NormalizationFailure):
        normalize_lineage(
            (
                asset("asset:a"),
                VerifiedAssetDto(
                    external_id="asset:a",
                    display_name="different",
                    asset_type="dataset",
                    platform="verified-test",
                ),
            ),
            (),
            maximum_nodes=10,
        )


def test_lineage_normalization_is_deterministic():
    edge = VerifiedLineageEdgeDto(
        upstream_id="asset:a", downstream_id="asset:b", evidence_id="edge:1"
    )
    first = normalize_lineage((asset("asset:b"), asset("asset:a")), (edge,), maximum_nodes=10)
    second = normalize_lineage((asset("asset:a"), asset("asset:b")), (edge,), maximum_nodes=10)
    assert first == second


def test_signal_requires_aware_timestamps_and_preserves_provenance():
    with pytest.raises(ValidationError):
        VerifiedSignalDto(
            evidence_id="evidence:1",
            kind=VerifiedSignalKind.FRESHNESS,
            source_operation="verified-operation",
            asset_id="asset:a",
            observed_at=datetime(2026, 7, 24, 11),
            retrieved_at=NOW,
            status="late",
        )
    signal = VerifiedSignalDto(
        evidence_id="evidence:1",
        kind=VerifiedSignalKind.FRESHNESS,
        source_operation="verified-operation",
        asset_id="asset:a",
        observed_at=NOW,
        retrieved_at=NOW,
        status="late",
    )
    normalized = normalize_signal(signal)
    assert normalized.evidence_type is EvidenceType.FRESHNESS_SIGNAL
    assert normalized.source_operation == "verified-operation"
    assert normalized.factual_payload["status"] == "late"


def test_verified_tool_result_rejects_noncanonical_payload():
    with pytest.raises(ValidationError):
        VerifiedToolResult(tool_name="search", observed_at=NOW, payload={"bad": {1, 2}})
