"""Verified DataHub MCP evidence provider and bounded investigation orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import threading
import time
from typing import Any

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

from .capabilities import (
    CapabilityInventory,
    CapabilityName,
    DocumentationStatus,
    McpCapability,
    RuntimeStatus,
)
from .client_protocol import McpClientProtocol
from .config import DataHubMcpConfig
from .errors import McpUnavailable, MutationDisabled, NormalizationFailure, ToolInventoryUnavailable


def _id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _items(payload: Mapping[str, Any], *keys: str) -> list[Mapping[str, Any]]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (list, tuple)) and all(
            isinstance(item, Mapping) for item in value
        ):
            return list(value)
    wrapped = payload.get("result")
    if isinstance(wrapped, (list, tuple)) and all(
        isinstance(item, Mapping) for item in wrapped
    ):
        return list(wrapped)
    return []


def _urn(value: Mapping[str, Any]) -> str | None:
    direct = value.get("urn") or value.get("entityUrn") or value.get("entity_urn")
    if isinstance(direct, str) and direct:
        return direct
    entity = value.get("entity")
    return _urn(entity) if isinstance(entity, Mapping) else None


class DataHubMcpEvidenceProvider:
    normalization_verified = True
    investigation_orchestration_implemented = True
    INITIALIZATION_RETRY_SECONDS = 5.0

    def __init__(
        self,
        config: DataHubMcpConfig,
        *,
        client: McpClientProtocol | None = None,
        inventory: CapabilityInventory | None = None,
    ) -> None:
        self.config = config
        self.client = client
        self.inventory = inventory
        self._initialization_error: Exception | None = None
        self._initialization_failed_at: float | None = None
        self._runtime_lock = threading.RLock()

    def _initialize_runtime(self) -> None:
        with self._runtime_lock:
            if self.client is None or (
                self.client.ready and self.inventory is not None
            ):
                return
            if (
                self._initialization_failed_at is not None
                and time.monotonic() - self._initialization_failed_at
                < self.INITIALIZATION_RETRY_SECONDS
            ):
                return
            try:
                self.client.initialize()
                names = {tool.name for tool in self.client.list_tools()}
                mapping = {
                    CapabilityName.ASSET_SEARCH: "search",
                    CapabilityName.ENTITY_INSPECTION: "get_entities",
                    CapabilityName.UPSTREAM_LINEAGE: "get_lineage",
                    CapabilityName.DOWNSTREAM_LINEAGE: "get_lineage",
                    CapabilityName.LINEAGE_PATHS: "get_lineage_paths_between",
                    CapabilityName.OWNERSHIP_CONTEXT: "get_entities",
                }
                now = datetime.now(timezone.utc)
                self.inventory = CapabilityInventory(
                    server_version=self.config.mcp_server_version,
                    observed_at=now,
                    capabilities=tuple(
                        McpCapability(
                            name=name,
                            documentation_status=DocumentationStatus.DOCUMENTED,
                            runtime_status=(
                                RuntimeStatus.OBSERVED
                                if mapping.get(name) in names
                                else RuntimeStatus.UNOBSERVED
                            ),
                            enabled=mapping.get(name) in names,
                            read_only=True,
                            source="runtime MCP list_tools schema validation",
                            version=self.config.mcp_server_version,
                            verified_at=now if mapping.get(name) in names else None,
                            notes="Enabled only after exact tool and input-schema verification.",
                        )
                        for name in CapabilityName
                    )
                )
                self._initialization_error = None
                self._initialization_failed_at = None
            except Exception as error:
                self._initialization_error = error
                self._initialization_failed_at = time.monotonic()
                self.inventory = None

    @property
    def readiness(self) -> EvidenceProviderReadiness:
        with self._runtime_lock:
            self._initialize_runtime()
            client_ready = self.client is not None and self.client.ready
            capabilities_verified = (
                self.inventory is not None
                and self.inventory.observed_at is not None
                and self.inventory.required_reads_verified
            )
            if self.client is None:
                status = "client_absent"
            elif not client_ready:
                status = "client_unavailable"
            elif not capabilities_verified:
                status = "tool_inventory_unverified"
            else:
                status = "ready"
            return EvidenceProviderReadiness(
                dependency_name=f"DataHub MCP evidence provider ({status})",
                status=status,
                configured=True,
                available=client_ready and capabilities_verified,
                supports_datahub=True,
                supports_mcp=True,
                supports_writeback=False,
            )

    @staticmethod
    def _entity(value: Mapping[str, Any], now: datetime) -> tuple[AssetIdentity, list[EvidenceRecord]]:
        urn = _urn(value)
        if urn is None:
            raise NormalizationFailure("A DataHub MCP entity has no supported URN.")
        props = value.get("properties") or value.get("datasetProperties") or {}
        if not isinstance(props, Mapping):
            props = {}
        custom = props.get("customProperties") or value.get("customProperties") or {}
        if isinstance(custom, list):
            custom = {
                item.get("key"): item.get("value")
                for item in custom
                if isinstance(item, Mapping) and isinstance(item.get("key"), str)
            }
        if not isinstance(custom, Mapping):
            custom = {}
        owner_values = value.get("owners") or value.get("ownership") or ()
        if isinstance(owner_values, Mapping):
            owner_values = owner_values.get("owners") or ()
        owners = tuple(
            Ownership(
                owner_id=str(item.get("owner") or item.get("urn")),
                display_name=str(
                    item.get("displayName")
                    or item.get("name")
                    or str(item.get("owner") or item.get("urn")).rsplit(":", 1)[-1]
                ),
                owner_type=str(item.get("type") or "TECHNICAL_OWNER"),
                kind=OwnerKind.TEAM,
                evidence_id=_id("ownership", urn, str(item.get("owner") or item.get("urn"))),
            )
            for item in owner_values
            if isinstance(item, Mapping) and (item.get("owner") or item.get("urn"))
        )
        criticality_text = str(custom.get("dic_criticality", "unknown")).lower()
        try:
            criticality = AssetCriticality(criticality_text)
        except ValueError:
            criticality = AssetCriticality.UNKNOWN
        platform = urn.split(",")[0].rsplit(":", 1)[-1] if "," in urn else "datahub"
        asset = AssetIdentity(
            external_id=urn,
            display_name=str(value.get("name") or props.get("name") or urn),
            asset_type=str(custom.get("dic_asset_type") or value.get("type") or "dataset").lower(),
            platform=platform,
            criticality=criticality,
            owners=owners or None,
        )
        evidence = [
            EvidenceRecord(
                evidence_id=_id("metadata", urn),
                evidence_type=EvidenceType.ASSET_METADATA,
                source_system="datahub-mcp",
                source_operation="get_entities",
                observed_at=now,
                retrieved_at=now,
                asset_id=urn,
                factual_payload={"name": asset.display_name, "custom_properties": dict(custom)},
                reliability=Reliability.VERIFIED,
            )
        ]
        evidence.extend(
            EvidenceRecord(
                evidence_id=owner.evidence_id,
                evidence_type=EvidenceType.OWNERSHIP,
                source_system="datahub-mcp",
                source_operation="get_entities",
                observed_at=now,
                retrieved_at=now,
                asset_id=urn,
                factual_payload={"owner": owner.owner_id, "type": owner.owner_type},
                reliability=Reliability.VERIFIED,
            )
            for owner in owners
        )
        for kind, key, evidence_type in (
            ("freshness", "dic_freshness_status", EvidenceType.FRESHNESS_SIGNAL),
            ("quality", "dic_quality_status", EvidenceType.QUALITY_ASSERTION),
        ):
            if key not in custom:
                continue
            observed = now
            timestamp = custom.get(f"dic_{kind}_observed_at")
            if isinstance(timestamp, str):
                try:
                    observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except ValueError:
                    pass
            evidence.append(
                EvidenceRecord(
                    evidence_id=_id(kind, urn),
                    evidence_type=evidence_type,
                    source_system="datahub-mcp",
                    source_operation=f"get_entities:{key}",
                    observed_at=observed,
                    retrieved_at=now,
                    asset_id=urn,
                    factual_payload={"status": str(custom[key])},
                    reliability=Reliability.VERIFIED,
                )
            )
        return asset, evidence

    def investigate(self, record: InvestigationRecord) -> IncidentReport:
        with self._runtime_lock:
            return self._investigate_locked(record)

    def _investigate_locked(self, record: InvestigationRecord) -> IncidentReport:
        readiness = self.readiness
        if self.client is not None and self.client.ready and not readiness.available:
            raise ToolInventoryUnavailable(
                "The required DataHub MCP tool inventory has not been runtime verified."
            )
        if not readiness.available or self.client is None:
            raise McpUnavailable("The verified DataHub MCP client is unavailable.")
        now = datetime.now(timezone.utc)
        try:
            search = self.client.invoke(
                "search",
                {"query": record.target_asset_id, "num_results": 10, "offset": 0},
            ).payload
            search_items = _items(search, "entities", "results", "searchResults")
            urns = sorted({value for item in search_items if (value := _urn(item))})
            target = record.target_asset_id if record.target_asset_id in urns else None
            if target is None and len(urns) == 1:
                target = urns[0]
            if target is None:
                raise NormalizationFailure(
                    "DataHub MCP search did not resolve one exact target dataset."
                )

            lineage_urns = {target}
            pairs: set[tuple[str, str]] = set()
            truncated = False

            def related_entities(
                payload: Mapping[str, Any], upstream: bool
            ) -> tuple[list[Mapping[str, Any]], bool]:
                direction = payload.get("upstreams" if upstream else "downstreams")
                if isinstance(direction, Mapping):
                    return (
                        _items(direction, "searchResults", "entities", "results"),
                        bool(
                            direction.get("hasMore")
                            or direction.get("truncatedDueToTokenBudget")
                        ),
                    )
                return (
                    _items(
                        payload,
                        "relationships",
                        "edges",
                        "lineage",
                        "entities",
                        "results",
                    ),
                    bool(payload.get("truncated") or payload.get("hasMore")),
                )

            upstream_limit = (
                self.config.maximum_lineage_nodes - len(lineage_urns)
            )
            upstream_payload = (
                self.client.invoke(
                    "get_lineage",
                    {
                        "urn": target,
                        "upstream": True,
                        "max_hops": 1,
                        "max_results": upstream_limit,
                        "offset": 0,
                    },
                ).payload
                if upstream_limit > 0
                else {"upstreams": {"searchResults": [], "hasMore": True}}
            )
            upstream_items, upstream_truncated = related_entities(
                upstream_payload, True
            )
            truncated = truncated or upstream_truncated
            upstream_remaining = (
                self.config.maximum_lineage_nodes - len(lineage_urns)
            )
            if len(upstream_items) > upstream_remaining:
                upstream_items = upstream_items[:upstream_remaining]
                truncated = True
            for item in upstream_items:
                if related := _urn(item):
                    pairs.add((related, target))
                    lineage_urns.add(related)

            queue: list[tuple[str, int]] = [(target, 0)]
            visited = {target}
            while queue:
                current, depth = queue.pop(0)
                if depth >= self.config.maximum_lineage_depth:
                    continue
                remaining = self.config.maximum_lineage_nodes - len(lineage_urns)
                if remaining <= 0:
                    truncated = True
                    break
                payload = self.client.invoke(
                    "get_lineage",
                    {
                        "urn": current,
                        "upstream": False,
                        "max_hops": 1,
                        "max_results": remaining,
                        "offset": 0,
                    },
                ).payload
                relations, page_truncated = related_entities(payload, False)
                truncated = truncated or page_truncated
                for relation in relations:
                    source = relation.get("source") or relation.get("upstream")
                    destination = relation.get("target") or relation.get("downstream")
                    if isinstance(source, Mapping):
                        source = _urn(source)
                    if isinstance(destination, Mapping):
                        destination = _urn(destination)
                    related = _urn(relation)
                    if not isinstance(source, str) or not isinstance(destination, str):
                        if related:
                            source, destination = current, related
                        else:
                            continue
                    new_nodes = {source, destination} - lineage_urns
                    if len(lineage_urns) + len(new_nodes) > (
                        self.config.maximum_lineage_nodes
                    ):
                        truncated = True
                        break
                    pairs.add((source, destination))
                    lineage_urns.update((source, destination))
                    if destination not in visited:
                        visited.add(destination)
                        queue.append((destination, depth + 1))

            entities_payload = self.client.invoke(
                "get_entities", {"urns": sorted(lineage_urns)}
            ).payload
            entity_items = [
                item
                for item in _items(entities_payload, "entities", "results")
                if _urn(item) in lineage_urns
            ]
            assets: dict[str, AssetIdentity] = {}
            evidence: list[EvidenceRecord] = []
            for item in entity_items:
                asset, records = self._entity(item, now)
                assets[asset.external_id] = asset
                evidence.extend(records)
            if target not in assets or any(
                endpoint not in assets for pair in pairs for endpoint in pair
            ):
                raise NormalizationFailure(
                    "DataHub MCP entity metadata was incomplete for bounded lineage."
                )

            edges = []
            for source, destination in sorted(pairs):
                evidence_id = _id("lineage", source, destination)
                edges.append(
                    LineageEdge(
                        upstream_id=source,
                        downstream_id=destination,
                        evidence_id=evidence_id,
                    )
                )
                evidence.append(
                    EvidenceRecord(
                        evidence_id=evidence_id,
                        evidence_type=EvidenceType.LINEAGE_EDGE,
                        source_system="datahub-mcp",
                        source_operation="get_lineage",
                        observed_at=now,
                        retrieved_at=now,
                        asset_id=destination,
                        factual_payload={"upstream": source, "downstream": destination},
                        reliability=Reliability.VERIFIED,
                    )
                )
            graph = LineageGraph.create(
                tuple(LineageNode(asset=asset) for asset in assets.values()),
                tuple(edges),
            )
            blast = calculate_blast_radius(
                graph,
                target,
                max_depth=self.config.maximum_lineage_depth,
                max_nodes=self.config.maximum_lineage_nodes,
                include_root=True,
            )
            if truncated:
                summary = dict(blast.impact_summary_inputs)
                summary["truncated"] = True
                blast = blast.model_copy(
                    update={"truncated": True, "impact_summary_inputs": summary}
                )
            failed = tuple(
                item
                for item in evidence
                if item.asset_id == target
                and item.evidence_type
                in {EvidenceType.FRESHNESS_SIGNAL, EvidenceType.QUALITY_ASSERTION}
                and str(item.factual_payload.get("status", "")).lower()
                in {"failed", "stale", "failing"}
            )
            required = (
                EvidenceType.ASSET_METADATA,
                EvidenceType.LINEAGE_EDGE,
                EvidenceType.FRESHNESS_SIGNAL,
                EvidenceType.QUALITY_ASSERTION,
                EvidenceType.OWNERSHIP,
            )
            present = {item.evidence_type for item in evidence}
            missing = set(required) - present
            severity = assess_severity(
                SeverityInputs(
                    confirmed_failure=bool(failed),
                    affected_asset_count=blast.total_affected,
                    critical_asset_count=len(blast.critical_assets_affected),
                    affected_dashboard_model_count=int(
                        blast.impact_summary_inputs["dashboard_model_count"]
                    ),
                    missing_ownership=not assets[target].owners,
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
            root_evidence = sorted(
                failed,
                key=lambda item: (
                    item.evidence_type is not EvidenceType.FRESHNESS_SIGNAL,
                    item.evidence_id,
                ),
            )[0] if failed else None
            root = None
            findings = ()
            if root_evidence is not None:
                issue = (
                    "freshness"
                    if root_evidence.evidence_type is EvidenceType.FRESHNESS_SIGNAL
                    else "quality"
                )
                root = RootCause(
                    asset_id=target,
                    issue_category=issue,
                    description=(
                        f"DataHub MCP reports {issue} failure evidence for "
                        f"{assets[target].display_name} ({target})."
                    ),
                    confirmed=True,
                    evidence_ids=(root_evidence.evidence_id,),
                )
                findings = (
                    ConfirmedFinding(
                        finding_id=f"{issue}-failure",
                        statement=f"Confirmed {issue} failure evidence is present for the target.",
                        evidence_ids=(root_evidence.evidence_id,),
                    ),
                )
            remediation_ref = (
                root_evidence.evidence_id
                if root_evidence is not None
                else _id("metadata", target)
            )
            return IncidentReport(
                incident_id=record.incident_id,
                title=record.title,
                target_asset=assets[target],
                status=IncidentState.INVESTIGATED,
                root_cause=root,
                blast_radius=blast,
                severity=severity,
                confidence=confidence,
                confirmed_findings=findings,
                inferred_findings=(),
                unknowns=tuple(
                    UnknownFinding(
                        finding_id=f"missing-{kind.value}",
                        question=f"Where is {kind.value} evidence?",
                        reason="The verified MCP responses did not provide this signal.",
                    )
                    for kind in sorted(missing, key=lambda value: value.value)
                ),
                conflicting_evidence=(),
                owners=assets[target].owners or (),
                remediation_actions=(
                    RemediationAction(
                        action_id="restore-and-rerun-upstream",
                        title="Restore and rerun the affected upstream pipeline",
                        description="Restore the delayed feed, rerun processing, and recheck freshness.",
                        priority=(
                            RemediationPriority.URGENT
                            if root_evidence
                            else RemediationPriority.MEDIUM
                        ),
                        rationale="The recommendation follows from verified target evidence.",
                        evidence_references=(remediation_ref,),
                        requires_human_approval=True,
                        classification=ActionClassification.NON_DESTRUCTIVE,
                        expected_verification_step="Confirm freshness is healthy and downstream assets update.",
                    ),
                ),
                evidence_ledger=tuple(evidence),
                related_previous_incidents=(),
                created_at=now,
                updated_at=now,
                engine_version="dic-mcp-1",
            )
        except (McpUnavailable, ToolInventoryUnavailable):
            raise
        except NormalizationFailure as error:
            raise McpUnavailable(
                "The verified DataHub MCP response could not be safely normalized."
            ) from error
        except Exception as error:
            raise McpUnavailable(
                "The verified DataHub MCP response could not be safely normalized."
            ) from error
        finally:
            self.client.close()

    def require_mutation(self) -> None:
        raise MutationDisabled("DataHub MCP mutation is disabled.")
