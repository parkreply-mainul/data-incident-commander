"""Documented-versus-observed MCP capability inventory."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
import re

from pydantic import Field, field_validator, model_validator

from data_incident_commander.domain.base import StrictModel, utc_datetime

_EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")


class DocumentationStatus(str, Enum):
    DOCUMENTED = "documented"
    ADAPTER_ASSUMPTION = "adapter_assumption_pending_runtime_verification"
    UNSUPPORTED = "unsupported"


class RuntimeStatus(str, Enum):
    UNOBSERVED = "unobserved"
    OBSERVED = "observed"
    MISSING = "missing"


class CapabilityName(str, Enum):
    ASSET_SEARCH = "asset_search"
    ENTITY_INSPECTION = "entity_inspection"
    UPSTREAM_LINEAGE = "upstream_lineage"
    DOWNSTREAM_LINEAGE = "downstream_lineage"
    LINEAGE_PATHS = "lineage_paths"
    OWNERSHIP_CONTEXT = "ownership_context"
    DOCUMENTS = "documents"
    MUTATION = "mutation"
    WRITEBACK = "writeback"
    USER = "user"


class McpCapability(StrictModel):
    name: CapabilityName
    documentation_status: DocumentationStatus
    runtime_status: RuntimeStatus = RuntimeStatus.UNOBSERVED
    enabled: bool = False
    read_only: bool
    source: str = Field(min_length=1)
    version: str = Field(min_length=1)
    verified_at: datetime | None = None
    notes: str = Field(min_length=1)

    @field_validator("version")
    @classmethod
    def version_is_nonblank_and_unmodified(cls, value: str) -> str:
        if not value.strip() or value != value.strip():
            raise ValueError("capability version must be nonblank without whitespace padding")
        return value

    @field_validator("verified_at")
    @classmethod
    def timestamp_is_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else utc_datetime(value)

    @model_validator(mode="after")
    def validate_observation(self) -> "McpCapability":
        if self.runtime_status is RuntimeStatus.OBSERVED and self.verified_at is None:
            raise ValueError("observed capabilities require verified_at")
        if self.runtime_status is not RuntimeStatus.OBSERVED and self.verified_at is not None:
            raise ValueError("unobserved or missing capabilities cannot have verified_at")
        if self.enabled and self.runtime_status is not RuntimeStatus.OBSERVED:
            raise ValueError("only runtime-observed capabilities may be enabled")
        if self.documentation_status is DocumentationStatus.UNSUPPORTED and self.enabled:
            raise ValueError("unsupported capabilities cannot be enabled")
        return self


class CapabilityInventory(StrictModel):
    server_version: str = Field(min_length=1)
    observed_at: datetime | None = None
    capabilities: tuple[McpCapability, ...]

    @field_validator("server_version")
    @classmethod
    def server_version_is_exact(cls, value: str) -> str:
        if not _EXACT_VERSION.fullmatch(value):
            raise ValueError("server_version must be an exact semantic version")
        return value

    @field_validator("capabilities")
    @classmethod
    def capabilities_are_canonical(
        cls, value: tuple[McpCapability, ...]
    ) -> tuple[McpCapability, ...]:
        return tuple(sorted(value, key=lambda item: item.name.value))

    @field_validator("observed_at")
    @classmethod
    def observed_timestamp_is_utc(cls, value: datetime | None) -> datetime | None:
        return None if value is None else utc_datetime(value)

    @model_validator(mode="after")
    def validate_inventory(self) -> "CapabilityInventory":
        names = [capability.name for capability in self.capabilities]
        if len(names) != len(set(names)):
            raise ValueError("capability names must be unique")
        observed = any(
            capability.runtime_status is RuntimeStatus.OBSERVED
            for capability in self.capabilities
        )
        if observed and self.observed_at is None:
            raise ValueError("runtime-observed inventory requires observed_at")
        if not observed and self.observed_at is not None:
            raise ValueError("unobserved inventory cannot have observed_at")
        mismatched = tuple(
            capability.name.value
            for capability in self.capabilities
            if capability.runtime_status is RuntimeStatus.OBSERVED
            and capability.version != self.server_version
        )
        if mismatched:
            raise ValueError(
                "runtime-observed capability versions must match server_version"
            )
        return self

    def verified_read(self, name: CapabilityName) -> bool:
        return any(
            item.name is name
            and item.runtime_status is RuntimeStatus.OBSERVED
            and item.enabled
            and item.read_only
            and item.version == self.server_version
            for item in self.capabilities
        )

    @property
    def required_reads_verified(self) -> bool:
        required = {
            CapabilityName.ASSET_SEARCH,
            CapabilityName.ENTITY_INSPECTION,
            CapabilityName.UPSTREAM_LINEAGE,
            CapabilityName.DOWNSTREAM_LINEAGE,
            CapabilityName.LINEAGE_PATHS,
            CapabilityName.OWNERSHIP_CONTEXT,
        }
        return all(self.verified_read(name) for name in required)


def documented_inventory(server_version: str) -> CapabilityInventory:
    """Documentation-only inventory. Nothing is runtime observed or enabled."""

    documented = {
        CapabilityName.ASSET_SEARCH,
        CapabilityName.ENTITY_INSPECTION,
        CapabilityName.UPSTREAM_LINEAGE,
        CapabilityName.DOWNSTREAM_LINEAGE,
        CapabilityName.LINEAGE_PATHS,
        CapabilityName.OWNERSHIP_CONTEXT,
        CapabilityName.DOCUMENTS,
        CapabilityName.MUTATION,
        CapabilityName.USER,
    }
    capabilities = tuple(
        McpCapability(
            name=name,
            documentation_status=(
                DocumentationStatus.DOCUMENTED
                if name in documented
                else DocumentationStatus.ADAPTER_ASSUMPTION
            ),
            read_only=name not in {CapabilityName.MUTATION, CapabilityName.WRITEBACK},
            source="official DataHub MCP documentation",
            version=server_version,
            notes="Runtime availability and schema remain unverified.",
        )
        for name in CapabilityName
    )
    return CapabilityInventory(server_version=server_version, capabilities=capabilities)
