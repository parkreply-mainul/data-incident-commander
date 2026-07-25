"""Minimal live DataHub GMS provider for the NYC Taxi demo."""

from __future__ import annotations

from collections.abc import Mapping
import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from data_incident_commander.application.protocols import EvidenceProviderReadiness
from data_incident_commander.application.records import InvestigationRecord
from data_incident_commander.domain.blast_radius import calculate_blast_radius
from data_incident_commander.domain.confidence import ConfidenceInputs, assess_confidence
from data_incident_commander.domain.models import (
    ActionClassification,
    AssetCriticality,
    AssetIdentity,
    ConfirmedFinding,
    EvidenceRecord,
    EvidenceType,
    IncidentReport,
    IncidentState,
    LineageEdge,
    LineageGraph,
    LineageNode,
    OwnerKind,
    Ownership,
    Reliability,
    RemediationAction,
    RemediationPriority,
    RootCause,
    SeverityInputs,
    UnknownFinding,
)
from data_incident_commander.domain.severity import assess_severity

from .errors import (
    McpUnavailable,
    MutationDisabled,
    NormalizationFailure,
    WritebackVerificationFailure,
)
from .config import _parse_and_validate_http_url, _private_or_loopback


SEARCH_QUERY = """
query dicSearch($input: SearchInput!) {
  search(input: $input) { searchResults { entity { urn type } } }
}
"""
ADD_TAG_MUTATION = """
mutation dicAddTag($input: TagAssociationInput!) {
  addTag(input: $input)
}
"""
DOWNSTREAM_LINEAGE_QUERY = """
query dicDownstreamLineage($input: ScrollAcrossLineageInput!) {
  scrollAcrossLineage(input: $input) {
    searchResults { degree entity { urn type } }
  }
}
"""
DATASET_URN_PATTERN = re.compile(
    r"^urn:li:dataset:\(urn:li:dataPlatform:[^,()]+,[^,()]+,[^,()]+\)$"
)


class _GraphqlOperationRejected(McpUnavailable):
    """DataHub explicitly rejected an operation without accepting it."""


def _id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"


class DataHubLiveEvidenceProvider:
    """Bounded live reads and a single, explicitly gated tag mutation."""

    def __init__(
        self,
        *,
        gms_url: str,
        token: str | None,
        mutation_enabled: bool = False,
        timeout_seconds: float = 20.0,
        readiness_timeout_seconds: float = 2.0,
        maximum_lineage_depth: int = 3,
        maximum_lineage_nodes: int = 100,
        writeback_tag_urn: str = "urn:li:tag:dic-incident-recorded",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        parsed = _parse_and_validate_http_url(gms_url, "gms_url")
        if (
            not _private_or_loopback(parsed.hostname or "")
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("gms_url must be a credential-free private DataHub URL")
        self.gms_url = gms_url.rstrip("/")
        self.mutation_enabled = mutation_enabled
        self.maximum_lineage_depth = maximum_lineage_depth
        self.maximum_lineage_nodes = maximum_lineage_nodes
        self.writeback_tag_urn = writeback_tag_urn
        self.readiness_timeout_seconds = readiness_timeout_seconds
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(
            base_url=self.gms_url,
            headers=headers,
            timeout=timeout_seconds,
            transport=transport,
        )

    @property
    def readiness(self) -> EvidenceProviderReadiness:
        available = False
        try:
            response = self.client.get(
                "/health", timeout=self.readiness_timeout_seconds
            )
            response.raise_for_status()
            available = response.text.strip() == "UP"
        except (httpx.HTTPError, ValueError):
            available = False
        return EvidenceProviderReadiness(
            dependency_name="DataHub v1.6.0 GMS live evidence provider",
            status="ready" if available else "unavailable",
            configured=True,
            available=available,
            supports_datahub=True,
            supports_mcp=False,
            supports_writeback=self.mutation_enabled,
        )

    def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self.client.post(
                "/api/graphql", json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise McpUnavailable("DataHub GMS did not return a usable response.") from error
        if not isinstance(body, Mapping):
            raise McpUnavailable("DataHub GMS did not return a usable response.")
        if body.get("errors"):
            raise _GraphqlOperationRejected(
                "DataHub rejected the requested metadata operation."
            )
        data = body.get("data")
        if not isinstance(data, Mapping):
            raise McpUnavailable("DataHub GMS did not return a usable response.")
        return dict(data)

    def _aspects(self, urn: str) -> dict[str, Any]:
        path = f"/entitiesV2/{quote(urn, safe='')}?aspects=datasetProperties&aspects=ownership&aspects=upstreamLineage&aspects=globalTags&aspects=domains"
        try:
            response = self.client.get(path)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise McpUnavailable("DataHub entity metadata could not be read.") from error
        if not isinstance(body, Mapping):
            raise McpUnavailable("DataHub entity metadata could not be read.")
        aspects = body.get("aspects")
        if not isinstance(aspects, Mapping):
            raise McpUnavailable("DataHub entity metadata could not be read.")
        for aspect in aspects.values():
            if not isinstance(aspect, Mapping):
                raise McpUnavailable("DataHub entity metadata could not be read.")
            if "value" in aspect and not isinstance(aspect["value"], Mapping):
                raise McpUnavailable("DataHub entity metadata could not be read.")
        return dict(aspects)

    def _direct_downstream(self, urn: str, *, count: int) -> tuple[str, ...]:
        data = self._graphql(
            DOWNSTREAM_LINEAGE_QUERY,
            {
                "input": {
                    "query": "*",
                    "urn": urn,
                    "count": count,
                    "direction": "DOWNSTREAM",
                    "orFilters": [
                        {
                            "and": [
                                {
                                    "condition": "EQUAL",
                                    "negated": False,
                                    "field": "degree",
                                    "values": ["1"],
                                }
                            ]
                        }
                    ],
                }
            },
        )
        result = data.get("scrollAcrossLineage")
        if not isinstance(result, dict) or not isinstance(
            result.get("searchResults"), list
        ):
            raise McpUnavailable(
                "DataHub downstream lineage response was missing required fields."
            )
        urns: list[str] = []
        for item in result["searchResults"]:
            entity = item.get("entity") if isinstance(item, dict) else None
            downstream = entity.get("urn") if isinstance(entity, dict) else None
            if not isinstance(downstream, str) or not downstream:
                raise McpUnavailable(
                    "DataHub downstream lineage contained an invalid entity."
                )
            if downstream != urn:
                urns.append(downstream)
        return tuple(sorted(set(urns)))

    def _discover_downstream(
        self, target_urn: str
    ) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...], bool]:
        """Breadth-first degree-1 traversal with strict depth and node bounds."""

        discovered = {target_urn}
        frontier = (target_urn,)
        edges: set[tuple[str, str]] = set()
        exhausted_depth = True
        for _depth in range(self.maximum_lineage_depth):
            next_frontier: set[str] = set()
            for upstream in frontier:
                remaining = self.maximum_lineage_nodes - len(discovered)
                downstreams = self._direct_downstream(
                    upstream, count=max(1, remaining + 1)
                )
                new_nodes = tuple(node for node in downstreams if node not in discovered)
                if len(new_nodes) > remaining:
                    raise NormalizationFailure(
                        "DataHub downstream lineage exceeds the configured node limit."
                    )
                for downstream in downstreams:
                    edges.add((upstream, downstream))
                    if downstream not in discovered:
                        discovered.add(downstream)
                        next_frontier.add(downstream)
            if not next_frontier:
                exhausted_depth = False
                break
            frontier = tuple(sorted(next_frontier))
        truncated = False
        if exhausted_depth and frontier:
            truncated = any(
                any(
                    node not in discovered
                    for node in self._direct_downstream(
                        urn, count=max(1, self.maximum_lineage_nodes + 1)
                    )
                )
                for urn in frontier
            )
        return tuple(sorted(discovered)), tuple(sorted(edges)), truncated

    @staticmethod
    def _value(aspects: dict[str, Any], name: str) -> dict[str, Any]:
        aspect = aspects.get(name) or {}
        value = aspect.get("value", aspect)
        return value if isinstance(value, dict) else {}

    def investigate(self, record: InvestigationRecord) -> IncidentReport:
        now = datetime.now(timezone.utc)
        data = self._graphql(
            SEARCH_QUERY,
            {"input": {"type": "DATASET", "query": record.target_asset_id, "start": 0, "count": 50}},
        )
        results = data.get("search", {}).get("searchResults", [])
        urns = sorted(
            {
                item.get("entity", {}).get("urn")
                for item in results
                if item.get("entity", {}).get("urn")
            }
        )
        exact = record.target_asset_id if record.target_asset_id in urns else None
        if exact is None and len(urns) == 1:
            exact = urns[0]
        if exact is None:
            raise NormalizationFailure(
                "DataHub asset search was ambiguous or returned no exact NYC Taxi asset."
            )

        related_urns, discovered_edges, lineage_truncated = self._discover_downstream(exact)
        metadata = {urn: self._aspects(urn) for urn in related_urns}
        evidence: list[EvidenceRecord] = []
        assets: dict[str, AssetIdentity] = {}
        for urn, aspects in metadata.items():
            props = self._value(aspects, "datasetProperties")
            custom = props.get("customProperties") or {}
            if isinstance(custom, list):
                custom = {item["key"]: item["value"] for item in custom}
            owner_items = self._value(aspects, "ownership").get("owners") or []
            owners = tuple(
                Ownership(
                    owner_id=item.get("owner", "unknown"),
                    display_name=item.get("owner", "unknown").rsplit(":", 1)[-1],
                    owner_type=item.get("type", "TECHNICAL_OWNER"),
                    kind=OwnerKind.TEAM,
                    evidence_id=_id("ownership", urn, item.get("owner", "unknown")),
                )
                for item in owner_items
            )
            platform = urn.split(",")[0].rsplit(":", 1)[-1] if "," in urn else "datahub"
            criticality = AssetCriticality(custom.get("dic_criticality", "unknown"))
            assets[urn] = AssetIdentity(
                external_id=urn,
                display_name=props.get("name") or urn.rsplit(",", 2)[-2],
                asset_type=custom.get("dic_asset_type", "dataset"),
                platform=platform,
                criticality=criticality,
                owners=owners or None,
            )
            metadata_id = _id("metadata", urn)
            evidence.append(
                EvidenceRecord(
                    evidence_id=metadata_id,
                    evidence_type=EvidenceType.ASSET_METADATA,
                    source_system="datahub-gms",
                    source_operation="entitiesV2",
                    observed_at=now,
                    retrieved_at=now,
                    asset_id=urn,
                    factual_payload={"name": assets[urn].display_name, "custom_properties": custom},
                    reliability=Reliability.VERIFIED,
                )
            )
            for owner in owners:
                evidence.append(
                    EvidenceRecord(
                        evidence_id=owner.evidence_id,
                        evidence_type=EvidenceType.OWNERSHIP,
                        source_system="datahub-gms",
                        source_operation="entitiesV2:ownership",
                        observed_at=now,
                        retrieved_at=now,
                        asset_id=urn,
                        factual_payload={"owner": owner.owner_id, "type": owner.owner_type},
                        reliability=Reliability.VERIFIED,
                    )
                )
            for kind, key, evidence_type in (
                ("freshness", "dic_freshness_status", EvidenceType.FRESHNESS_SIGNAL),
                ("quality", "dic_quality_status", EvidenceType.QUALITY_ASSERTION),
            ):
                if key in custom:
                    observed_text = custom.get(f"dic_{kind}_observed_at")
                    try:
                        observed = datetime.fromisoformat(observed_text.replace("Z", "+00:00"))
                    except (AttributeError, ValueError):
                        observed = now
                    evidence.append(
                        EvidenceRecord(
                            evidence_id=_id(kind, urn),
                            evidence_type=evidence_type,
                            source_system="datahub-gms",
                            source_operation=f"entitiesV2:datasetProperties.{key}",
                            observed_at=observed,
                            retrieved_at=now,
                            asset_id=urn,
                            factual_payload={"status": custom[key]},
                            reliability=Reliability.VERIFIED,
                        )
                    )

        edges: list[LineageEdge] = []
        for upstream, downstream in discovered_edges:
            if upstream not in assets or downstream not in assets:
                raise NormalizationFailure(
                    "DataHub lineage referenced an entity outside the bounded traversal."
                )
            eid = _id("lineage", upstream, downstream)
            edges.append(
                LineageEdge(
                    upstream_id=upstream,
                    downstream_id=downstream,
                    evidence_id=eid,
                )
            )
            evidence.append(
                EvidenceRecord(
                    evidence_id=eid,
                    evidence_type=EvidenceType.LINEAGE_EDGE,
                    source_system="datahub-gms",
                    source_operation="scrollAcrossLineage:DOWNSTREAM:degree=1",
                    observed_at=now,
                    retrieved_at=now,
                    asset_id=downstream,
                    factual_payload={"upstream": upstream, "downstream": downstream},
                    reliability=Reliability.VERIFIED,
                )
            )
        graph = LineageGraph.create(
            tuple(LineageNode(asset=value) for value in assets.values()), tuple(edges)
        )
        blast = calculate_blast_radius(
            graph,
            exact,
            max_depth=self.maximum_lineage_depth,
            max_nodes=self.maximum_lineage_nodes,
            include_root=True,
        )
        if lineage_truncated:
            summary = dict(blast.impact_summary_inputs)
            summary["truncated"] = True
            blast = blast.model_copy(
                update={"truncated": True, "impact_summary_inputs": summary}
            )
            evidence.append(
                EvidenceRecord(
                    evidence_id=_id(
                        "lineage-truncated",
                        exact,
                        str(self.maximum_lineage_depth),
                    ),
                    evidence_type=EvidenceType.ASSET_METADATA,
                    source_system="datahub-gms",
                    source_operation="scrollAcrossLineage:bounded-truncation",
                    observed_at=now,
                    retrieved_at=now,
                    asset_id=exact,
                    factual_payload={
                        "lineage_truncated": True,
                        "maximum_depth": self.maximum_lineage_depth,
                    },
                    reliability=Reliability.VERIFIED,
                )
            )
        failed = tuple(
            item
            for item in evidence
            if item.evidence_type in {EvidenceType.FRESHNESS_SIGNAL, EvidenceType.QUALITY_ASSERTION}
            and str(item.factual_payload.get("status", "")).lower() in {"failed", "stale", "failing"}
        )
        required = (
            EvidenceType.ASSET_METADATA,
            EvidenceType.LINEAGE_EDGE,
            EvidenceType.FRESHNESS_SIGNAL,
            EvidenceType.QUALITY_ASSERTION,
            EvidenceType.OWNERSHIP,
        )
        missing = {kind for kind in required if kind not in {item.evidence_type for item in evidence}}
        severity = assess_severity(
            SeverityInputs(
                confirmed_failure=bool(failed),
                affected_asset_count=blast.total_affected,
                critical_asset_count=len(blast.critical_assets_affected),
                affected_dashboard_model_count=int(blast.impact_summary_inputs["dashboard_model_count"]),
                missing_ownership=not assets[exact].owners,
                incomplete_evidence=bool(missing),
                blast_radius_truncated=blast.truncated,
            )
        )
        confidence = assess_confidence(
            ConfidenceInputs(
                evidence=tuple(evidence),
                expected_evidence_types=required,
                graph_truncated=blast.truncated,
            )
        )
        evidence_priority = {
            EvidenceType.FRESHNESS_SIGNAL: 0,
            EvidenceType.QUALITY_ASSERTION: 1,
        }
        root_candidates = tuple(
            sorted(
                failed,
                key=lambda item: (
                    item.asset_id != exact,
                    evidence_priority[item.evidence_type],
                    item.asset_id,
                    item.evidence_id,
                ),
            )
        )
        root_evidence = root_candidates[0] if root_candidates else None
        if root_evidence is not None:
            root_asset_name = assets[root_evidence.asset_id].display_name
            if root_evidence.evidence_type is EvidenceType.FRESHNESS_SIGNAL:
                issue = "freshness"
                root_description = (
                    f"DataHub reports stale freshness evidence for {root_asset_name} "
                    f"({root_evidence.asset_id})."
                )
                finding_id = "freshness-failure"
                finding_statement = (
                    f"Stale freshness evidence is present for {root_asset_name} "
                    f"({root_evidence.asset_id})."
                )
            else:
                issue = "quality"
                root_description = (
                    f"DataHub reports a failed quality assertion for {root_asset_name} "
                    f"({root_evidence.asset_id})."
                )
                finding_id = "quality-failure"
                finding_statement = (
                    f"A failed quality assertion is present for {root_asset_name} "
                    f"({root_evidence.asset_id})."
                )
        root = (
            RootCause(
                asset_id=root_evidence.asset_id,
                issue_category=issue,
                description=root_description,
                confirmed=True,
                evidence_ids=(root_evidence.evidence_id,),
            )
            if root_evidence
            else None
        )
        remediation_refs = (root_evidence.evidence_id,) if root_evidence else (evidence[0].evidence_id,)
        return IncidentReport(
            incident_id=record.incident_id,
            title=record.title,
            target_asset=assets[exact],
            status=IncidentState.INVESTIGATED,
            root_cause=root,
            blast_radius=blast,
            severity=severity,
            confidence=confidence,
            confirmed_findings=(
                ConfirmedFinding(
                    finding_id=finding_id,
                    statement=finding_statement,
                    evidence_ids=(root_evidence.evidence_id,),
                ),
            ) if root_evidence else (),
            inferred_findings=(),
            unknowns=tuple(
                UnknownFinding(
                    finding_id=f"missing-{kind.value}",
                    question=f"Where is {kind.value} evidence?",
                    reason="The live DataHub entity did not provide this evidence type.",
                )
                for kind in sorted(missing, key=lambda value: value.value)
            ),
            conflicting_evidence=(),
            owners=assets[exact].owners or (),
            remediation_actions=(
                RemediationAction(
                    action_id="rerun-nyc-taxi-ingestion",
                    title="Rerun the NYC Taxi ingestion job",
                    description="Restore the delayed upstream feed, rerun ingestion, then recheck freshness.",
                    priority=RemediationPriority.URGENT if root_evidence else RemediationPriority.MEDIUM,
                    rationale="The recommendation follows directly from the live freshness evidence.",
                    evidence_references=remediation_refs,
                    requires_human_approval=True,
                    classification=ActionClassification.NON_DESTRUCTIVE,
                    expected_verification_step="Confirm DataHub freshness is healthy and downstream assets update.",
                ),
            ),
            evidence_ledger=tuple(evidence),
            related_previous_incidents=(),
            created_at=now,
            updated_at=now,
            engine_version="dic-live-1",
        )

    def mutate_writeback(self, record: InvestigationRecord) -> None:
        if not self.mutation_enabled:
            raise MutationDisabled("DataHub mutation is disabled by default.")
        resolved_urn = (
            record.report.target_asset.external_id
            if record.report is not None
            else None
        )
        if (
            not isinstance(resolved_urn, str)
            or DATASET_URN_PATTERN.fullmatch(resolved_urn) is None
        ):
            raise NormalizationFailure(
                "Write-back requires a resolved DataHub dataset URN."
            )
        try:
            self._graphql(
                ADD_TAG_MUTATION,
                {
                    "input": {
                        "tagUrn": self.writeback_tag_urn,
                        "resourceUrn": resolved_urn,
                    }
                },
            )
        except _GraphqlOperationRejected:
            raise
        except McpUnavailable as error:
            raise WritebackVerificationFailure(
                "DataHub write-back acceptance could not be verified."
            ) from error

    def verify_writeback(self, record: InvestigationRecord) -> EvidenceRecord:
        resolved_urn = (
            record.report.target_asset.external_id
            if record.report is not None
            else None
        )
        if (
            not isinstance(resolved_urn, str)
            or DATASET_URN_PATTERN.fullmatch(resolved_urn) is None
        ):
            raise NormalizationFailure(
                "Write-back requires a resolved DataHub dataset URN."
            )
        try:
            aspects = self._aspects(resolved_urn)
        except McpUnavailable as error:
            raise WritebackVerificationFailure(
                "DataHub write-back read-back verification was unavailable."
            ) from error
        tags = self._value(aspects, "globalTags").get("tags") or []
        observed = {item.get("tag") for item in tags}
        if self.writeback_tag_urn not in observed:
            raise WritebackVerificationFailure(
                "DataHub write-back read-back verification failed."
            )
        now = datetime.now(timezone.utc)
        return EvidenceRecord(
            evidence_id=_id("writeback", record.incident_id, self.writeback_tag_urn),
            evidence_type=EvidenceType.WRITEBACK_RECEIPT,
            source_system="datahub-gms",
            source_operation="addTag + entitiesV2:globalTags",
            observed_at=now,
            retrieved_at=now,
            asset_id=resolved_urn,
            factual_payload={"tag_urn": self.writeback_tag_urn, "verified": True},
            reliability=Reliability.VERIFIED,
        )

    def writeback(self, record: InvestigationRecord) -> EvidenceRecord:
        """Compatibility helper; application orchestration uses the split operations."""

        self.mutate_writeback(record)
        return self.verify_writeback(record)
