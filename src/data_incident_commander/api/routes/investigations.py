"""Incident investigation HTTP routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from data_incident_commander.application.commands import (
    ActorCommand,
    ApprovalCommand,
    CreateInvestigation,
    RetryCommand,
)
from data_incident_commander.application.services import InvestigationService

from ..dependencies import get_investigation_service
from ..mapping import investigation_response
from ..schemas import (
    ActorRequest,
    ApprovalRequest,
    CreateInvestigationRequest,
    InvestigationListResponse,
    InvestigationResponse,
    RetryRequest,
)

router = APIRouter(prefix="/api/v1/investigations", tags=["investigations"])
Service = Annotated[InvestigationService, Depends(get_investigation_service)]


@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
def create_investigation(body: CreateInvestigationRequest, service: Service):
    return investigation_response(
        service.create_draft(CreateInvestigation.model_validate(body.model_dump()))
    )


@router.get("", response_model=InvestigationListResponse)
def list_investigations(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> InvestigationListResponse:
    page = service.list(offset=offset, limit=limit)
    return InvestigationListResponse(
        items=tuple(investigation_response(record) for record in page.items),
        offset=page.offset,
        limit=page.limit,
        total=page.total,
    )


@router.get("/{incident_id}", response_model=InvestigationResponse)
def get_investigation(incident_id: str, service: Service):
    return investigation_response(service.get(incident_id))


@router.post("/{incident_id}/investigate", response_model=InvestigationResponse)
def investigate(incident_id: str, service: Service):
    return investigation_response(service.investigate(incident_id))


@router.post("/{incident_id}/submit-for-approval", response_model=InvestigationResponse)
def submit_for_approval(incident_id: str, body: ActorRequest, service: Service):
    return investigation_response(
        service.submit_for_approval(
            incident_id, ActorCommand.model_validate(body.model_dump())
        )
    )


@router.post("/{incident_id}/approve", response_model=InvestigationResponse)
def approve(incident_id: str, body: ApprovalRequest, service: Service):
    return investigation_response(
        service.approve(incident_id, ApprovalCommand.model_validate(body.model_dump()))
    )


@router.post("/{incident_id}/retry", response_model=InvestigationResponse)
def retry(incident_id: str, body: RetryRequest, service: Service):
    return investigation_response(
        service.retry(incident_id, RetryCommand.model_validate(body.model_dump()))
    )


@router.post("/{incident_id}/resolve", response_model=InvestigationResponse)
def resolve(incident_id: str, body: ActorRequest, service: Service):
    return investigation_response(
        service.resolve(incident_id, ActorCommand.model_validate(body.model_dump()))
    )
