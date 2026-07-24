"""FastAPI dependency accessors."""

from fastapi import Request

from data_incident_commander.application.services import InvestigationService


def get_investigation_service(request: Request) -> InvestigationService:
    return request.app.state.investigation_service
