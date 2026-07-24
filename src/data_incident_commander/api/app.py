"""FastAPI application factory with no network work during import."""

from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from data_incident_commander.application.services import (
    InvestigationService,
    UnconfiguredEvidenceProvider,
)
from data_incident_commander.config import Settings
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
    resolved_service = service or InvestigationService(
        InMemoryIncidentRepository(),
        UnconfiguredEvidenceProvider(),
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
