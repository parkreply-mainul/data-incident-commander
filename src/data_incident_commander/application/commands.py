"""Strict application commands independent of HTTP."""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import Field, field_serializer, field_validator

from data_incident_commander.domain.base import StrictModel, freeze_mapping, thaw_mapping


class CreateInvestigation(StrictModel):
    title: str = Field(min_length=1, max_length=200)
    target_asset_id: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=4000)
    issue_category: str | None = Field(default=None, max_length=100)
    requester: Mapping[str, Any] | None = None

    @field_validator("requester")
    @classmethod
    def freeze_requester(cls, value: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
        return None if value is None else freeze_mapping(value)

    @field_serializer("requester")
    def serialize_requester(self, value: Mapping[str, Any] | None) -> dict[str, Any] | None:
        return None if value is None else thaw_mapping(value)


class ApprovalCommand(StrictModel):
    actor: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    payload_binding_id: str = Field(min_length=1, max_length=500)


class RetryCommand(StrictModel):
    actor: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)
    approval_remains_valid: bool = False
    payload_binding_unchanged: bool = False


class ActorCommand(StrictModel):
    actor: str = Field(min_length=1, max_length=200)
