"""Normalization from verified adapter DTOs, never guessed raw MCP payloads."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator

from data_incident_commander.domain.base import StrictModel, utc_datetime
from data_incident_commander.domain.models import (
    AssetIdentity,
    EvidenceRecord,
    EvidenceType,
    LineageEdge,
    LineageGraph,
    LineageNode,
    OwnerKind,
    Ownership,
    Reliability,
)

from .errors import NormalizationFailure


class VerifiedOwnerDto(StrictModel):
    owner_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    owner_type: str = Field(min_length=1)
    kind: OwnerKind
    evidence_id: str = Field(min_length=1)


class VerifiedAssetDto(StrictModel):
    external_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    asset_type: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    domain: str | None = None
    owners: tuple[VerifiedOwnerDto, ...] = ()
    tags: tuple[str, ...] = ()


class VerifiedLineageEdgeDto(StrictModel):
    upstream_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)


class VerifiedSignalKind(str, Enum):
    FRESHNESS = "freshness"
    QUALITY = "quality"


class VerifiedSignalDto(StrictModel):
    evidence_id: str = Field(min_length=1)
    kind: VerifiedSignalKind
    source_operation: str = Field(min_length=1)
    asset_id: str = Field(min_length=1)
    observed_at: datetime
    retrieved_at: datetime
    status: str = Field(min_length=1)

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)


def normalize_asset(value: VerifiedAssetDto) -> AssetIdentity:
    owners = tuple(
        Ownership(
            owner_id=owner.owner_id,
            display_name=owner.display_name,
            owner_type=owner.owner_type,
            kind=owner.kind,
            evidence_id=owner.evidence_id,
        )
        for owner in value.owners
    )
    try:
        return AssetIdentity(
            external_id=value.external_id,
            display_name=value.display_name,
            asset_type=value.asset_type,
            platform=value.platform,
            domain=value.domain,
            owners=owners or None,
            tags=value.tags or None,
        )
    except ValueError as error:
        raise NormalizationFailure("Verified asset DTO could not be normalized.") from error


def normalize_lineage(
    assets: tuple[VerifiedAssetDto, ...],
    edges: tuple[VerifiedLineageEdgeDto, ...],
    *,
    maximum_nodes: int,
) -> LineageGraph:
    if len(assets) > maximum_nodes:
        raise NormalizationFailure("Verified lineage exceeds the configured node limit.")
    try:
        return LineageGraph.create(
            tuple(LineageNode(asset=normalize_asset(asset)) for asset in assets),
            tuple(
                LineageEdge(
                    upstream_id=edge.upstream_id,
                    downstream_id=edge.downstream_id,
                    evidence_id=edge.evidence_id,
                )
                for edge in edges
            ),
        )
    except ValueError as error:
        raise NormalizationFailure("Verified lineage DTOs are inconsistent.") from error


def normalize_signal(value: VerifiedSignalDto) -> EvidenceRecord:
    evidence_type = (
        EvidenceType.FRESHNESS_SIGNAL
        if value.kind is VerifiedSignalKind.FRESHNESS
        else EvidenceType.QUALITY_ASSERTION
    )
    try:
        return EvidenceRecord(
            evidence_id=value.evidence_id,
            evidence_type=evidence_type,
            source_system="datahub-mcp",
            source_operation=value.source_operation,
            observed_at=value.observed_at,
            retrieved_at=value.retrieved_at,
            asset_id=value.asset_id,
            factual_payload={"status": value.status},
            reliability=Reliability.HIGH,
            provenance={
                "classification": "runtime-observed adapter DTO",
                "raw_payload_retained": False,
            },
        )
    except ValueError as error:
        raise NormalizationFailure("Verified signal DTO could not be normalized.") from error
