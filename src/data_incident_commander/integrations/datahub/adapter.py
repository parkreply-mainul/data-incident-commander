"""Evidence-provider boundary for a future verified DataHub MCP client."""

from __future__ import annotations

from data_incident_commander.application.protocols import EvidenceProviderReadiness
from data_incident_commander.application.records import InvestigationRecord

from .capabilities import CapabilityInventory
from .client_protocol import McpClientProtocol
from .config import DataHubMcpConfig
from .errors import McpUnavailable, MutationDisabled, ToolInventoryUnavailable


class DataHubMcpEvidenceProvider:
    """Fail-closed boundary for verified capabilities and future orchestration."""

    normalization_verified = True
    investigation_orchestration_implemented = False

    def __init__(
        self,
        config: DataHubMcpConfig,
        *,
        client: McpClientProtocol | None = None,
        inventory: CapabilityInventory | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.inventory = inventory

    @property
    def readiness(self) -> EvidenceProviderReadiness:
        client_ready = self.client is not None and self.client.ready
        capabilities_verified = (
            self.inventory is not None
            and self.inventory.observed_at is not None
            and self.inventory.required_reads_verified
        )
        if self.client is None:
            status = "client_absent"
        elif not client_ready:
            status = "client_unavailable"
        elif not capabilities_verified:
            status = "tool_inventory_unverified"
        else:
            status = "capabilities_verified_but_investigation_unimplemented"
        return EvidenceProviderReadiness(
            dependency_name=f"DataHub MCP evidence provider ({status})",
            status=status,
            configured=True,
            available=False,
            supports_datahub=True,
            supports_mcp=True,
            supports_writeback=False,
        )

    def investigate(self, record: InvestigationRecord):
        readiness = self.readiness
        if self.client is None or not self.client.ready:
            raise McpUnavailable("The verified DataHub MCP client is unavailable.")
        if (
            self.inventory is None
            or self.inventory.observed_at is None
            or not self.inventory.required_reads_verified
        ):
            raise ToolInventoryUnavailable(
                "The required DataHub MCP tool inventory has not been runtime verified."
            )
        raise McpUnavailable(
            "Runtime investigation orchestration is not implemented in Sprint 8A."
        )

    def require_mutation(self) -> None:
        raise MutationDisabled("DataHub MCP mutation is disabled.")
