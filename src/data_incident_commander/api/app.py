"""FastAPI application factory with no network work during import."""

from __future__ import annotations

from collections.abc import Callable
import os
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from data_incident_commander.application.services import (
    InvestigationService,
    UnconfiguredEvidenceProvider,
)
from data_incident_commander.config import Settings
from data_incident_commander.integrations.datahub.adapter import (
    DataHubMcpEvidenceProvider,
)
from data_incident_commander.integrations.datahub.config import (
    DataHubMcpConfig,
    VERIFIED_MCP_SERVER_VERSION,
)
from data_incident_commander.integrations.datahub.live import DataHubLiveEvidenceProvider
from data_incident_commander.integrations.datahub.stdio_client import (
    DataHubMcpStdioClient,
)
from data_incident_commander.repositories.memory import InMemoryIncidentRepository

from .errors import install_error_handlers
from .routes import health, investigations


def create_app(
    *,
    service: InvestigationService | None = None,
    settings: Settings | None = None,
    request_id_provider: Callable[[], str] | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_environment()
    provider = UnconfiguredEvidenceProvider()
    if (
        resolved_settings.datahub_gms_url
        and resolved_settings.datahub_mcp_mode
        and resolved_settings.datahub_mcp_server_version
    ):
        try:
            mcp_config = DataHubMcpConfig(
                gms_url=resolved_settings.datahub_gms_url,
                token_env_var=resolved_settings.datahub_token_env,
                mode=resolved_settings.datahub_mcp_mode,
                mcp_server_version=resolved_settings.datahub_mcp_server_version,
                request_timeout_seconds=resolved_settings.datahub_mcp_timeout_seconds,
                mutation_enabled=False,
                documents_enabled=resolved_settings.datahub_mcp_documents_enabled,
                user_tools_enabled=resolved_settings.datahub_mcp_user_tools_enabled,
                environment_name=resolved_settings.environment,
            )
            if (
                mcp_config.mcp_server_version == VERIFIED_MCP_SERVER_VERSION
                and not mcp_config.documents_enabled
                and not mcp_config.user_tools_enabled
            ):
                provider = DataHubMcpEvidenceProvider(
                    mcp_config,
                    client=DataHubMcpStdioClient(mcp_config),
                )
        except (TypeError, ValueError):
            pass
    writeback_provider = None
    if resolved_settings.datahub_gms_url:
        writeback_provider = DataHubLiveEvidenceProvider(
            gms_url=resolved_settings.datahub_gms_url,
            token=os.getenv(resolved_settings.datahub_token_env),
            mutation_enabled=resolved_settings.datahub_mutation_enabled,
            writeback_tag_urn=resolved_settings.datahub_writeback_tag_urn,
        )
    resolved_service = service or InvestigationService(
        InMemoryIncidentRepository(),
        provider,
        writeback_provider=writeback_provider,
    )
    next_request_id = request_id_provider or (lambda: str(uuid4()))

    application = FastAPI(
        title=resolved_settings.service_name,
        version=resolved_settings.service_version,
        debug=False,
    )
    application.state.investigation_service = resolved_service
    application.state.settings = resolved_settings

    @application.middleware("http")
    async def correlation_id(request: Request, call_next) -> Response:
        supplied = request.headers.get("X-Request-ID", "").strip()
        request.state.request_id = supplied[:200] if supplied else next_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    install_error_handlers(application)
    application.include_router(health.router)
    application.include_router(investigations.router)
    return application


app = create_app()
