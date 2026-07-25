"""Strict HTTP request and response contracts, separate from domain models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from data_incident_commander.domain.base import utc_datetime


class TransportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class HealthResponse(TransportModel):
    status: str
    service: str
    version: str
    timestamp: datetime


class ComponentReadiness(TransportModel):
    status: str
    detail: str


class ReadinessResponse(TransportModel):
    status: str
    service: str
    timestamp: datetime
    components: dict[str, ComponentReadiness]


class CreateInvestigationRequest(TransportModel):
    title: str = Field(min_length=1, max_length=200)
    target_asset_id: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    issue_category: str | None = Field(default=None, max_length=100)
    requester: dict[str, Any] | None = None


class ActorRequest(TransportModel):
    actor: str = Field(min_length=1, max_length=200)


class ApprovalRequest(ActorRequest):
    reason: str = Field(min_length=1, max_length=2000)
    payload_binding_id: str = Field(min_length=1, max_length=500)


class RetryRequest(ActorRequest):
    reason: str = Field(min_length=1, max_length=2000)
    approval_remains_valid: bool = False
    payload_binding_unchanged: bool = False


class TransitionResponse(TransportModel):
    from_state: str
    to_state: str
    actor: str
    occurred_at: datetime
    approval_reason: str | None
    failure_reason: str | None
    retry_action: bool
    approval_remains_valid: bool
    payload_binding_unchanged: bool


class InvestigationResponse(TransportModel):
    incident_id: str
    revision: int
    title: str
    target_asset_id: str
    description: str | None
    issue_category: str | None
    requester: dict[str, Any] | None
    state: str
    history: tuple[TransitionResponse, ...]
    payload_binding_id: str | None
    expected_payload_binding_id: str | None
    last_action_reason: str | None
    report: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)


class InvestigationListResponse(TransportModel):
    items: tuple[InvestigationResponse, ...]
    offset: int
    limit: int
    total: int


class ErrorBody(TransportModel):
    code: str
    message: str
    retryable: bool
    request_id: str
    details: dict[str, Any]


class ErrorEnvelope(TransportModel):
    error: ErrorBody
