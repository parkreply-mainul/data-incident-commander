from __future__ import annotations

from datetime import datetime, timezone

import pytest

from data_incident_commander.domain.models import (
    AssetCriticality,
    AssetIdentity,
    EvidenceRecord,
    EvidenceType,
    LineageNode,
    Reliability,
)


NOW = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def evidence_factory():
    def build(
        evidence_id: str,
        evidence_type: EvidenceType = EvidenceType.ASSET_METADATA,
        *,
        age_seconds: int | None = 10,
        stale_after_seconds: int | None = 60,
        reliability: Reliability = Reliability.VERIFIED,
        conflicts: tuple[str, ...] = (),
    ) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=evidence_id,
            evidence_type=evidence_type,
            source_system="synthetic-test-source",
            source_operation="normalized-read",
            observed_at=NOW,
            retrieved_at=NOW,
            asset_id="asset:root",
            factual_payload={"status": "observed"},
            age_seconds=age_seconds,
            stale_after_seconds=stale_after_seconds,
            reliability=reliability,
            conflict_references=conflicts,
            provenance={"adapter": "unit-test"},
        )

    return build


@pytest.fixture
def node_factory():
    def build(
        external_id: str,
        asset_type: str = "dataset",
        criticality: AssetCriticality = AssetCriticality.LOW,
        display_name: str | None = None,
    ) -> LineageNode:
        return LineageNode(
            asset=AssetIdentity(
                external_id=external_id,
                display_name=display_name or external_id,
                asset_type=asset_type,
                platform="synthetic",
                criticality=criticality,
            )
        )

    return build
