"""Deterministic incident-memory matching without embeddings."""

from __future__ import annotations

from pydantic import Field

from .base import StrictModel
from .models import EvidenceType, IncidentMatch, IncidentMemoryResult, PreviousIncidentRecord


class IncidentMemoryQuery(StrictModel):
    target_asset_id: str
    root_cause_asset_id: str | None = None
    issue_category: str
    evidence_types: tuple[EvidenceType, ...]
    affected_asset_ids: tuple[str, ...]
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)


def match_previous_incidents(
    query: IncidentMemoryQuery,
    records: tuple[PreviousIncidentRecord, ...],
) -> IncidentMemoryResult:
    matches: list[IncidentMatch] = []
    query_evidence = set(query.evidence_types)
    query_affected = set(query.affected_asset_ids)
    for record in records:
        score = 0.0
        reasons: list[str] = []
        if query.root_cause_asset_id and query.root_cause_asset_id == record.root_cause_asset_id:
            score += 0.35
            reasons.append("same root-cause asset")
        if query.target_asset_id == record.target_asset_id:
            score += 0.25
            reasons.append("same target asset")
        if query.issue_category == record.issue_category:
            score += 0.20
            reasons.append("same issue category")
        if query_evidence & set(record.evidence_types):
            score += 0.10
            reasons.append("overlapping evidence type")
        if query_affected & set(record.affected_asset_ids):
            score += 0.10
            reasons.append("overlapping affected asset")
        score = round(score, 6)
        if reasons and score >= query.threshold:
            matches.append(
                IncidentMatch(
                    incident_id=record.incident_id,
                    similarity_score=score,
                    match_reasons=tuple(reasons),
                    evidence_ids=(),
                )
            )
    matches.sort(key=lambda item: (-item.similarity_score, item.incident_id))
    return IncidentMemoryResult(threshold=query.threshold, matches=tuple(matches))
