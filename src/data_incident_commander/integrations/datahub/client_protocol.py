"""Library-neutral MCP client contracts; no raw schema assumptions."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Protocol

from pydantic import Field, field_serializer, field_validator

from data_incident_commander.domain.base import (
    StrictModel,
    freeze_mapping,
    thaw_mapping,
    utc_datetime,
)


class McpToolDescriptor(StrictModel):
    name: str = Field(min_length=1)
    schema_fingerprint: str = Field(min_length=1)
    read_only: bool


class VerifiedToolResult(StrictModel):
    tool_name: str = Field(min_length=1)
    observed_at: datetime
    payload: Mapping[str, Any]

    @field_validator("observed_at")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)

    @field_validator("payload")
    @classmethod
    def payload_is_canonical(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_mapping(value)

    @field_serializer("payload")
    def serialize_payload(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_mapping(value)


class McpClientProtocol(Protocol):
    @property
    def ready(self) -> bool: ...

    def initialize(self) -> None: ...
    def list_tools(self) -> tuple[McpToolDescriptor, ...]: ...
    def invoke(self, tool_name: str, arguments: Mapping[str, Any]) -> VerifiedToolResult: ...
    def close(self) -> None: ...
