"""Application-only health and explicit dependency readiness."""

from fastapi import APIRouter, Depends, Request

from data_incident_commander.application.services import InvestigationService
from ..dependencies import get_investigation_service
from ..schemas import ComponentReadiness, HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(
    request: Request,
    service: InvestigationService = Depends(get_investigation_service),
) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        version=settings.service_version,
        timestamp=service.clock.now(),
    )


@router.get("/health/readiness", response_model=ReadinessResponse)
def readiness(
    request: Request,
    service: InvestigationService = Depends(get_investigation_service),
) -> ReadinessResponse:
    settings = request.app.state.settings
    provider = service.evidence_provider.readiness
    writeback_provider = (
        service.writeback_provider or service.evidence_provider
    ).readiness
    repository_ready = service.repository.ready
    writeback_ready = (
        writeback_provider.configured
        and writeback_provider.available
        and writeback_provider.supports_datahub
        and writeback_provider.supports_writeback
    )

    def dependency_component(supported: bool, label: str) -> ComponentReadiness:
        if not provider.configured:
            return ComponentReadiness(
                status="not_configured", detail=f"{label} is not configured."
            )
        if not supported:
            return ComponentReadiness(
                status="unsupported", detail=f"The provider does not support {label}."
            )
        if not provider.available:
            return ComponentReadiness(
                status="unavailable", detail=f"{label} is configured but unavailable."
            )
        return ComponentReadiness(status="ready", detail=f"{label} is available.")

    components = {
        "application": ComponentReadiness(status="ready", detail="API process is available."),
        "incident_repository": ComponentReadiness(
            status="ready" if repository_ready else "unavailable",
            detail=(
                "Incident repository is available."
                if repository_ready
                else "Incident repository is unavailable."
            ),
        ),
        "evidence_provider": ComponentReadiness(
            status=(
                "not_configured"
                if not provider.configured
                else "unavailable"
                if not provider.available
                else provider.status
            ),
            detail=provider.dependency_name,
        ),
        "datahub": dependency_component(provider.supports_datahub, "DataHub"),
        "mcp": dependency_component(provider.supports_mcp, "DataHub MCP"),
        "writeback": ComponentReadiness(
            status=(
                "not_configured"
                if not writeback_provider.configured
                else "disabled"
                if not writeback_provider.supports_writeback
                else "unavailable"
                if not writeback_provider.available
                else "ready"
                if writeback_ready
                else "unavailable"
            ),
            detail=(
                "Approval-gated DataHub tag write-back is enabled."
                if writeback_ready
                else "The configured write-back provider is unavailable."
                if writeback_provider.configured
                and writeback_provider.supports_writeback
                and not writeback_provider.available
                else "Write-back is not configured."
                if not writeback_provider.configured
                else "Write-back is disabled by default."
            ),
        ),
    }
    full_system_ready = (
        repository_ready
        and provider.configured
        and provider.available
        and provider.supports_datahub
        and provider.supports_mcp
        and writeback_ready
    )
    return ReadinessResponse(
        status="ready" if full_system_ready else "not_ready",
        service=settings.service_name,
        timestamp=service.clock.now(),
        components=components,
    )
