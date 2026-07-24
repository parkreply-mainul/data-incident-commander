"""Helpers for side-effect-free adapter readiness inspection."""

from .adapter import DataHubMcpEvidenceProvider


def readiness_summary(provider: DataHubMcpEvidenceProvider) -> dict[str, object]:
    state = provider.readiness
    client_available = provider.client is not None and provider.client.ready
    required_tools_observed = (
        provider.inventory is not None
        and provider.inventory.observed_at is not None
        and provider.inventory.required_reads_verified
    )
    return {
        "configured": state.configured,
        "client_available": client_available,
        "required_tools_observed": required_tools_observed,
        "capabilities_verified": client_available and required_tools_observed,
        "adapter_normalization_verified": provider.normalization_verified,
        "investigation_orchestration_implemented": (
            provider.investigation_orchestration_implemented
        ),
        "available": state.available,
        "status": state.status,
        "supports_datahub": state.supports_datahub,
        "supports_mcp": state.supports_mcp,
        "supports_writeback": state.supports_writeback,
        "mutation_enabled": False,
    }
