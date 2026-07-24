"""Immutable application records persisted through repository protocols."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from pydantic import Field, field_serializer, field_validator

from data_incident_commander.domain.base import StrictModel, freeze_mapping, thaw_mapping, utc_datetime
from data_incident_commander.domain.models import IncidentReport
from data_incident_commander.domain.state_machine import ApprovalStateMachine


class InvestigationRecord(StrictModel):
    incident_id: str = Field(min_length=1)
    revision: int = Field(default=1, ge=1)
    title: str
    target_asset_id: str
    description: str | None = None
    issue_category: str | None = None
    requester: Mapping[str, Any] | None = None
    workflow: ApprovalStateMachine
    report: IncidentReport | None = None
    payload_binding_id: str | None = None
    last_action_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)

    @field_validator("requester")
    @classmethod
    def requester_is_immutable(
        cls, value: Mapping[str, Any] | None
    ) -> Mapping[str, Any] | None:
        return None if value is None else freeze_mapping(value)

    @field_serializer("requester")
    def serialize_requester(self, value: Mapping[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else thaw_mapping(value)


class InvestigationPage(StrictModel):
    items: tuple[InvestigationRecord, ...]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)
