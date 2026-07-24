"""Typed normalized contracts independent of DataHub and MCP payload shapes."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Literal, Mapping

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from .base import StrictModel, freeze_mapping, thaw_mapping, utc_datetime


class AssetCriticality(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LifecycleStatus(str, Enum):
    UNKNOWN = "unknown"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


class OwnerKind(str, Enum):
    TEAM = "team"
    INDIVIDUAL = "individual"


class Ownership(StrictModel):
    owner_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    owner_type: str = Field(min_length=1)
    kind: OwnerKind
    contact: Mapping[str, Any] | None = None
    evidence_id: str = Field(min_length=1)

    @field_validator("contact")
    @classmethod
    def contact_is_canonical_and_immutable(
        cls,
        value: Mapping[str, Any] | None,
    ) -> Mapping[str, Any] | None:
        return None if value is None else freeze_mapping(value)

    @field_serializer("contact")
    def serialize_contact(
        self,
        value: Mapping[str, Any] | None,
    ) -> dict[str, Any] | None:
        return None if value is None else thaw_mapping(value)


class AssetIdentity(StrictModel):
    external_id: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    asset_type: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    domain: str | None = None
    lifecycle_status: LifecycleStatus = LifecycleStatus.UNKNOWN
    criticality: AssetCriticality = AssetCriticality.UNKNOWN
    owners: tuple[Ownership, ...] | None = None
    tags: tuple[str, ...] | None = None

    @field_validator("owners")
    @classmethod
    def owners_are_unique(cls, value: tuple[Ownership, ...] | None) -> tuple[Ownership, ...] | None:
        if value is not None and len({owner.owner_id for owner in value}) != len(value):
            raise ValueError("owners must have unique owner_id values")
        return value


class EvidenceType(str, Enum):
    ASSET_METADATA = "asset_metadata"
    LINEAGE_EDGE = "lineage_edge"
    FRESHNESS_SIGNAL = "freshness_signal"
    QUALITY_ASSERTION = "quality_assertion"
    OWNERSHIP = "ownership"
    PREVIOUS_INCIDENT = "previous_incident"
    WRITEBACK_RECEIPT = "write_back_receipt"


class Reliability(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


AGE_PRECISION_TOLERANCE = timedelta(microseconds=999_999)


class EvidenceRecord(StrictModel):
    evidence_id: str = Field(min_length=1)
    evidence_type: EvidenceType
    source_system: str = Field(min_length=1)
    source_operation: str = Field(min_length=1)
    observed_at: datetime
    retrieved_at: datetime
    asset_id: str = Field(min_length=1)
    factual_payload: Mapping[str, Any]
    age_seconds: int | None = Field(default=None, ge=0)
    stale_after_seconds: int | None = Field(default=None, gt=0)
    reliability: Reliability
    conflict_references: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = Field(default_factory=dict, validate_default=True)

    @field_validator("observed_at", "retrieved_at")
    @classmethod
    def timestamps_are_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)

    @field_validator("factual_payload", "provenance")
    @classmethod
    def mappings_are_immutable(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_mapping(value)

    @field_serializer("factual_payload", "provenance")
    def serialize_mappings(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_mapping(value)

    @model_validator(mode="after")
    def validate_times_and_conflicts(self) -> "EvidenceRecord":
        if self.observed_at > self.retrieved_at:
            raise ValueError("observed_at cannot be after retrieved_at")
        if self.age_seconds is not None:
            minimum_age = self.retrieved_at - self.observed_at
            declared_age = timedelta(seconds=self.age_seconds)
            if declared_age + AGE_PRECISION_TOLERANCE < minimum_age:
                raise ValueError(
                    "age_seconds is smaller than the timestamp-derived minimum age"
                )
        if self.evidence_id in self.conflict_references:
            raise ValueError("evidence cannot conflict with itself")
        return self

    @field_validator("conflict_references")
    @classmethod
    def normalize_conflict_references(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(reference.strip() for reference in value)
        if any(not reference for reference in normalized):
            raise ValueError("conflict reference evidence IDs must be non-empty")
        return tuple(sorted(set(normalized)))


_EVIDENCE_REFERENCE_FIELDS = frozenset(
    {"evidence_id", "evidence_ids", "evidence_references", "conflict_references"}
)


def _collect_evidence_references(value: Any, *, field_name: str | None = None) -> set[str]:
    """Collect reference fields recursively so new nested contracts stay ledger-closed."""

    if field_name in _EVIDENCE_REFERENCE_FIELDS:
        if isinstance(value, str):
            return {value}
        return {item for item in value if isinstance(item, str)}
    if isinstance(value, BaseModel):
        references: set[str] = set()
        for name in value.__class__.model_fields:
            references.update(
                _collect_evidence_references(getattr(value, name), field_name=name)
            )
        return references
    if isinstance(value, Mapping):
        references = set()
        for item in value.values():
            references.update(_collect_evidence_references(item))
        return references
    if isinstance(value, tuple | list):
        references = set()
        for item in value:
            references.update(_collect_evidence_references(item))
        return references
    return set()


class Finding(StrictModel):
    finding_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = ()


class ConfirmedFinding(Finding):
    @model_validator(mode="after")
    def requires_evidence(self) -> "ConfirmedFinding":
        if not self.evidence_ids:
            raise ValueError("confirmed findings require at least one evidence_id")
        return self


class InferredFinding(Finding):
    rationale: str = Field(min_length=1)


class UnknownFinding(StrictModel):
    finding_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class ConflictingEvidence(StrictModel):
    conflict_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    evidence_ids: tuple[str, ...] = Field(min_length=2)

    @field_validator("evidence_ids")
    @classmethod
    def evidence_is_unique(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("conflicting evidence IDs must be unique")
        return value


class LineageNode(StrictModel):
    asset: AssetIdentity

    @property
    def node_id(self) -> str:
        return self.asset.external_id


class LineageEdge(StrictModel):
    upstream_id: str = Field(min_length=1)
    downstream_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def rejects_self_edge(self) -> "LineageEdge":
        if self.upstream_id == self.downstream_id:
            raise ValueError("lineage self-edges are not allowed")
        return self

    @property
    def identity(self) -> tuple[str, str]:
        return (self.upstream_id, self.downstream_id)


class LineageGraph(StrictModel):
    nodes: tuple[LineageNode, ...]
    edges: tuple[LineageEdge, ...]

    @classmethod
    def create(
        cls,
        nodes: list[LineageNode] | tuple[LineageNode, ...],
        edges: list[LineageEdge] | tuple[LineageEdge, ...],
    ) -> "LineageGraph":
        unique_nodes: dict[str, LineageNode] = {}
        for node in nodes:
            existing = unique_nodes.get(node.node_id)
            if existing is not None and existing != node:
                raise ValueError(
                    f"conflicting duplicate lineage node for identifier {node.node_id!r}"
                )
            unique_nodes[node.node_id] = node
        unique_edges: dict[tuple[str, str], LineageEdge] = {}
        for edge in edges:
            existing = unique_edges.get(edge.identity)
            if existing is not None and existing != edge:
                raise ValueError(
                    "conflicting duplicate lineage edge for endpoints "
                    f"{edge.upstream_id!r} -> {edge.downstream_id!r}"
                )
            unique_edges[edge.identity] = edge
        return cls(
            nodes=tuple(unique_nodes[key] for key in sorted(unique_nodes)),
            edges=tuple(unique_edges[key] for key in sorted(unique_edges)),
        )

    @model_validator(mode="after")
    def validates_graph(self) -> "LineageGraph":
        node_ids = [node.node_id for node in self.nodes]
        if node_ids != sorted(node_ids) or len(node_ids) != len(set(node_ids)):
            raise ValueError("nodes must be unique and deterministically ordered")
        identities = [edge.identity for edge in self.edges]
        if identities != sorted(identities) or len(identities) != len(set(identities)):
            raise ValueError("edges must be unique and deterministically ordered")
        unknown = {
            endpoint
            for edge in self.edges
            for endpoint in edge.identity
            if endpoint not in set(node_ids)
        }
        if unknown:
            raise ValueError(f"edges reference unknown nodes: {sorted(unknown)}")
        return self


class BlastRadiusResult(StrictModel):
    root_asset_id: str
    included_root_asset_id: str | None = None
    directly_affected_assets: tuple[str, ...]
    transitively_affected_assets: tuple[str, ...]
    affected_counts_by_type: Mapping[str, int]
    critical_assets_affected: tuple[str, ...]
    traversal_depth_reached: int = Field(ge=0)
    truncated: bool
    evidence_references: tuple[str, ...]
    impact_summary_inputs: Mapping[str, int | bool]

    @field_validator("affected_counts_by_type", "impact_summary_inputs")
    @classmethod
    def mappings_are_immutable(cls, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return freeze_mapping(value)

    @field_serializer("affected_counts_by_type", "impact_summary_inputs")
    def serialize_mappings(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return thaw_mapping(value)

    @property
    def total_affected(self) -> int:
        return len(self.directly_affected_assets) + len(self.transitively_affected_assets)

    @property
    def overall_asset_ids(self) -> tuple[str, ...]:
        affected = self.directly_affected_assets + self.transitively_affected_assets
        if self.included_root_asset_id is None:
            return affected
        return (self.included_root_asset_id,) + affected

    @property
    def overall_asset_count(self) -> int:
        return len(self.overall_asset_ids)


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AppliedRule(StrictModel):
    rule_id: str
    description: str
    points: int
    applied: bool


class SeverityRuleSet(StrictModel):
    version: str = "1"
    affected_asset_threshold: int = Field(default=3, ge=1)
    broad_impact_threshold: int = Field(default=10, ge=1)
    dashboard_model_threshold: int = Field(default=2, ge=1)
    medium_score: int = Field(default=2, ge=0)
    high_score: int = Field(default=4, ge=0)
    critical_score: int = Field(default=7, ge=0)

    @model_validator(mode="after")
    def ordered_thresholds(self) -> "SeverityRuleSet":
        if not self.medium_score < self.high_score < self.critical_score:
            raise ValueError("severity score thresholds must be strictly increasing")
        if self.affected_asset_threshold > self.broad_impact_threshold:
            raise ValueError("affected thresholds must be ordered")
        return self


class SeverityInputs(StrictModel):
    confirmed_failure: bool
    affected_asset_count: int = Field(ge=0)
    critical_asset_count: int = Field(ge=0)
    affected_dashboard_model_count: int = Field(ge=0)
    missing_ownership: bool
    incomplete_evidence: bool
    blast_radius_truncated: bool


class SeverityAssessment(StrictModel):
    severity: Severity
    score: int = Field(ge=0)
    ruleset_version: str
    applied_rules: tuple[AppliedRule, ...]
    explanation: tuple[str, ...]


class ConfidenceFactor(StrictModel):
    factor_id: str
    weight: float = Field(ge=0.0, le=1.0)
    value: float = Field(ge=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)
    explanation: str


class ConfidenceAssessment(StrictModel):
    confidence: float = Field(ge=0.0, le=1.0)
    factors: tuple[ConfidenceFactor, ...]
    penalties: tuple[str, ...]
    unique_conflict_count: int = Field(default=0, ge=0)
    conflict_sources: tuple[str, ...] = ()
    conflict_penalty: float = Field(default=0.0, ge=0.0, le=1.0)


class RemediationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ActionClassification(str, Enum):
    NON_DESTRUCTIVE = "non_destructive"
    DESTRUCTIVE = "destructive"


class RemediationAction(StrictModel):
    action_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: RemediationPriority
    rationale: str = Field(min_length=1)
    evidence_references: tuple[str, ...]
    requires_human_approval: bool
    classification: ActionClassification
    expected_verification_step: str = Field(min_length=1)
    rollback_guidance: str | None = None

    @model_validator(mode="after")
    def destructive_requires_approval(self) -> "RemediationAction":
        if self.classification is ActionClassification.DESTRUCTIVE and not self.requires_human_approval:
            raise ValueError("destructive remediation requires human approval")
        if not self.evidence_references:
            raise ValueError("remediation requires evidence references")
        return self


class IncidentState(str, Enum):
    DRAFT = "DRAFT"
    INVESTIGATED = "INVESTIGATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    WRITEBACK_PENDING = "WRITEBACK_PENDING"
    RECORDED = "RECORDED"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class StateTransition(StrictModel):
    from_state: IncidentState
    to_state: IncidentState
    actor: str = Field(min_length=1)
    occurred_at: datetime
    approval_reason: str | None = None
    failure_reason: str | None = None
    retry_action: bool = False
    approval_remains_valid: bool = False
    payload_binding_unchanged: bool = False

    @field_validator("occurred_at")
    @classmethod
    def timestamp_is_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)


class RootCause(StrictModel):
    asset_id: str
    issue_category: str
    description: str
    confirmed: bool
    evidence_ids: tuple[str, ...]

    @model_validator(mode="after")
    def confirmed_requires_evidence(self) -> "RootCause":
        if self.confirmed and not self.evidence_ids:
            raise ValueError("confirmed root cause requires evidence")
        return self


class PreviousIncidentRecord(StrictModel):
    incident_id: str
    target_asset_id: str
    root_cause_asset_id: str | None = None
    issue_category: str
    evidence_types: tuple[EvidenceType, ...]
    affected_asset_ids: tuple[str, ...]
    title: str
    resolved_at: datetime

    @field_validator("resolved_at")
    @classmethod
    def resolved_is_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)


class IncidentMatch(StrictModel):
    incident_id: str
    similarity_score: float = Field(ge=0.0, le=1.0)
    match_reasons: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()


class IncidentMemoryResult(StrictModel):
    threshold: float = Field(ge=0.0, le=1.0)
    matches: tuple[IncidentMatch, ...]


class IncidentReport(StrictModel):
    incident_id: str
    title: str
    target_asset: AssetIdentity
    status: IncidentState
    root_cause: RootCause | None
    blast_radius: BlastRadiusResult
    severity: SeverityAssessment
    confidence: ConfidenceAssessment
    confirmed_findings: tuple[ConfirmedFinding, ...]
    inferred_findings: tuple[InferredFinding, ...]
    unknowns: tuple[UnknownFinding, ...]
    conflicting_evidence: tuple[ConflictingEvidence, ...]
    owners: tuple[Ownership, ...]
    remediation_actions: tuple[RemediationAction, ...]
    evidence_ledger: tuple[EvidenceRecord, ...]
    related_previous_incidents: tuple[IncidentMatch, ...]
    created_at: datetime
    updated_at: datetime
    schema_version: Literal["1"] = "1"
    engine_version: str

    @field_validator("created_at", "updated_at")
    @classmethod
    def report_timestamps_are_utc(cls, value: datetime) -> datetime:
        return utc_datetime(value)

    @model_validator(mode="after")
    def validate_ledger(self) -> "IncidentReport":
        evidence_ids = [record.evidence_id for record in self.evidence_ledger]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence ledger contains duplicate evidence IDs")
        available = set(evidence_ids)
        referenced: set[str] = set()
        for field_name in self.__class__.model_fields:
            if field_name == "evidence_ledger":
                continue
            referenced.update(
                _collect_evidence_references(getattr(self, field_name), field_name=field_name)
            )
        referenced.update(
            evidence_id
            for record in self.evidence_ledger
            for evidence_id in record.conflict_references
        )
        if not referenced.issubset(available):
            missing = sorted(referenced - available)
            raise ValueError(f"report references evidence absent from the ledger: {missing}")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be before created_at")
        return self
