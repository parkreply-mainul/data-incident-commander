from __future__ import annotations

import json
import httpx
import pytest
from threading import Event, Thread
from urllib.parse import unquote

from data_incident_commander.application.errors import ConcurrentUpdateConflict
from data_incident_commander.application.errors import DependencyUnavailable
from data_incident_commander.application.errors import InvalidWorkflowTransition
from data_incident_commander.application.commands import (
    ActorCommand,
    ApprovalCommand,
    CreateInvestigation,
)
from data_incident_commander.application.records import InvestigationRecord
from data_incident_commander.application.protocols import EvidenceProviderReadiness
from data_incident_commander.application.services import InvestigationService
from data_incident_commander.domain.models import EvidenceType, IncidentState, Reliability
from data_incident_commander.domain.state_machine import ApprovalStateMachine
from data_incident_commander.integrations.datahub.errors import (
    McpUnavailable,
    MutationDisabled,
    NormalizationFailure,
    WritebackVerificationFailure,
)
from data_incident_commander.integrations.datahub.live import DataHubLiveEvidenceProvider
from tests.application.conftest import NOW
from tests.application.conftest import ReportProvider, build_report, build_service


RAW = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_trips_raw,PROD)"
MODEL = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_daily_metrics,PROD)"
DASHBOARD = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_ops_dashboard,PROD)"
UNRELATED = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.unrelated,PROD)"
BRANCH = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_branch,PROD)"
OUT_OF_BOUND = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.out_of_bound,PROD)"


def live_handler(
    *,
    readback_matches: bool = True,
    cycle: bool = False,
    malformed_lineage: bool = False,
    terminal_model: bool = False,
    downstream_override: dict[str, tuple[str, ...]] | None = None,
    target_freshness_status: str | None = "stale",
    target_quality_status: str | None = "passing",
    downstream_quality_status: str | None = "passing",
):
    aspects = {
        RAW: {
            "datasetProperties": {"value": {"name": "NYC Taxi Trips Raw", "customProperties": {
                "dic_freshness_status": "stale",
                "dic_freshness_observed_at": "2026-07-24T09:00:00Z",
                "dic_quality_status": "passing",
                "dic_asset_type": "dataset",
                "dic_criticality": "high",
            }}},
            "ownership": {"value": {"owners": [{
                "owner": "urn:li:corpGroup:data-platform",
                "type": "TECHNICAL_OWNER",
            }]}},
            "upstreamLineage": {"value": {"upstreams": []}},
            "globalTags": {"value": {"tags": (
                [{"tag": "urn:li:tag:dic-incident-recorded"}]
                if readback_matches else [{"tag": "urn:li:tag:other"}]
            )}},
        },
        MODEL: {
            "datasetProperties": {"value": {"name": "NYC Taxi Daily Metrics", "customProperties": {
                "dic_quality_status": "passing", "dic_asset_type": "model",
                "dic_criticality": "high",
            }}},
            "upstreamLineage": {"value": {"upstreams": [{"dataset": RAW}]}},
        },
        DASHBOARD: {
            "datasetProperties": {"value": {"name": "NYC Taxi Operations Dashboard", "customProperties": {
                "dic_quality_status": "passing", "dic_asset_type": "dashboard",
                "dic_criticality": "critical",
            }}},
            "upstreamLineage": {"value": {"upstreams": [{"dataset": MODEL}]}},
        },
        UNRELATED: {
            "datasetProperties": {"value": {"name": "Unrelated", "customProperties": {
                "dic_asset_type": "dataset", "dic_criticality": "low",
            }}},
            "upstreamLineage": {"value": {"upstreams": []}},
        },
        BRANCH: {
            "datasetProperties": {"value": {"name": "NYC Taxi Branch", "customProperties": {
                "dic_quality_status": "passing", "dic_asset_type": "model",
                "dic_criticality": "low",
            }}},
            "upstreamLineage": {"value": {"upstreams": [{"dataset": RAW}]}},
        },
    }
    downstream = {
        RAW: (MODEL,),
        MODEL: () if terminal_model else (DASHBOARD,),
        DASHBOARD: (RAW,) if cycle else (),
        UNRELATED: (),
    }
    if downstream_override is not None:
        downstream.update(downstream_override)
    raw_custom = aspects[RAW]["datasetProperties"]["value"]["customProperties"]
    model_custom = aspects[MODEL]["datasetProperties"]["value"]["customProperties"]
    if target_freshness_status is None:
        raw_custom.pop("dic_freshness_status", None)
    else:
        raw_custom["dic_freshness_status"] = target_freshness_status
    if target_quality_status is None:
        raw_custom.pop("dic_quality_status", None)
    else:
        raw_custom["dic_quality_status"] = target_quality_status
    if downstream_quality_status is None:
        model_custom.pop("dic_quality_status", None)
    else:
        model_custom["dic_quality_status"] = downstream_quality_status

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, text="UP")
        if request.url.path == "/api/graphql":
            body = json.loads(request.read())
            query = body["query"]
            if "dicAddTag" in query:
                return httpx.Response(200, json={"data": {"addTag": True}})
            if "dicDownstreamLineage" in query:
                if malformed_lineage:
                    return httpx.Response(200, json={"data": {}})
                urn = body["variables"]["input"]["urn"]
                return httpx.Response(
                    200,
                    json={"data": {"scrollAcrossLineage": {"searchResults": [
                        {"degree": 1, "entity": {"urn": item, "type": "DATASET"}}
                        for item in downstream[urn]
                    ]}}},
                )
            return httpx.Response(
                200,
                json={"data": {"search": {"searchResults": [
                    {"entity": {"urn": RAW, "type": "DATASET"}}
                ]}}},
            )
        urn = unquote(request.url.path.removeprefix("/entitiesV2/"))
        return httpx.Response(200, json={"aspects": aspects[urn]})

    return handler


def record(target: str) -> InvestigationRecord:
    return InvestigationRecord(
        incident_id="inc-live",
        title="NYC Taxi stale",
        target_asset_id=target,
        issue_category="freshness",
        workflow=ApprovalStateMachine(),
        created_at=NOW,
        updated_at=NOW,
    )


def resolved_record(query: str, resolved_urn: str = RAW) -> InvestigationRecord:
    value = record(query)
    return value.model_copy(
        update={
            "report": build_report(
                incident_id=value.incident_id,
                target_asset_id=resolved_urn,
                title=value.title,
            )
        }
    )


def approved_service(incident_id: str, provider: ReportProvider):
    service, repository = build_service(incident_id)
    draft = service.create_draft(
        CreateInvestigation(title="NYC Taxi stale", target_asset_id=RAW)
    )
    provider.report = build_report(
        incident_id=draft.incident_id,
        target_asset_id=RAW,
        title=draft.title,
    )
    service.evidence_provider = ReportProvider(provider.report)
    service.investigate(draft.incident_id)
    service.submit_for_approval(draft.incident_id, ActorCommand(actor="operator"))
    awaiting = service.get(draft.incident_id)
    service.approve(
        draft.incident_id,
        ApprovalCommand(
            actor="reviewer",
            reason="reviewed",
            payload_binding_id=service.payload_binding(awaiting),
        ),
    )
    service.writeback_provider = provider
    return service, repository, draft.incident_id


class ReadyWritebackProvider(ReportProvider):
    @property
    def readiness(self):
        return EvidenceProviderReadiness(
            dependency_name="ready writeback provider",
            status="ready",
            configured=True,
            available=True,
            supports_datahub=True,
            supports_mcp=False,
            supports_writeback=True,
        )


def test_live_search_fails_closed_when_ambiguous():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/graphql"
        return httpx.Response(
            200,
            json={"data": {"search": {"searchResults": [
                {"entity": {"urn": "urn:one", "type": "DATASET"}},
                {"entity": {"urn": "urn:two", "type": "DATASET"}},
            ]}}},
        )

    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(handler),
    )
    with pytest.raises(NormalizationFailure, match="ambiguous"):
        provider.investigate(record("nyc taxi"))


@pytest.mark.parametrize(
    "envelope",
    (
        [],
        "unexpected",
        {},
        {"data": None},
        {"data": "unexpected"},
        {"data": []},
    ),
    ids=(
        "top-level-array",
        "top-level-string",
        "missing-data",
        "null-data",
        "string-data",
        "array-data",
    ),
)
def test_graphql_rejects_malformed_envelopes_safely(envelope):
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token="private-test-token",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=envelope)
        ),
    )

    with pytest.raises(
        McpUnavailable, match="DataHub GMS did not return a usable response"
    ) as raised:
        provider._graphql("query test { test }", {})

    assert "private-test-token" not in str(raised.value)
    assert str(envelope) not in str(raised.value)


def test_graphql_accepts_valid_data_mapping():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"data": {"ok": True}})
        ),
    )

    assert provider._graphql("query test { test }", {}) == {"ok": True}


def test_graphql_explicit_errors_use_existing_rejection_path():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "errors": [{"message": "internal response detail"}],
                    "data": None,
                },
            )
        ),
    )

    with pytest.raises(
        McpUnavailable, match="DataHub rejected the requested metadata operation"
    ) as raised:
        provider._graphql("query test { test }", {})

    assert "internal response detail" not in str(raised.value)


def test_writeback_is_disabled_without_explicit_configuration():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(lambda request: httpx.Response(500)),
    )
    with pytest.raises(MutationDisabled):
        provider.writeback(record("urn:li:dataset:test"))


def test_readiness_requires_verified_datahub_health_response():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text="UP")
        ),
    )

    assert provider.readiness.available
    assert provider.readiness.status == "ready"


@pytest.mark.parametrize(
    ("handler", "expected_status"),
    [
        (
            lambda request: (_ for _ in ()).throw(httpx.ConnectError("offline")),
            "unavailable",
        ),
        (lambda request: httpx.Response(401), "unavailable"),
        (lambda request: httpx.Response(200, json={"status": "ok"}), "unavailable"),
        (
            lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("timed out")),
            "unavailable",
        ),
    ],
    ids=("connection-failure", "authentication-failure", "non-datahub", "timeout"),
)
def test_readiness_fails_closed_without_healthy_datahub(handler, expected_status):
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token="not-exposed",
        readiness_timeout_seconds=0.1,
        transport=httpx.MockTransport(handler),
    )

    readiness = provider.readiness
    assert not readiness.available
    assert readiness.status == expected_status
    assert "not-exposed" not in readiness.model_dump_json()


def test_successful_live_evidence_normalizes_all_required_metadata():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(live_handler()),
    )
    report = provider.investigate(record(RAW))

    types = {item.evidence_type for item in report.evidence_ledger}
    assert {
        EvidenceType.ASSET_METADATA,
        EvidenceType.OWNERSHIP,
        EvidenceType.LINEAGE_EDGE,
        EvidenceType.FRESHNESS_SIGNAL,
        EvidenceType.QUALITY_ASSERTION,
    }.issubset(types)
    assert report.target_asset.owners is not None
    assert report.target_asset.owners[0].owner_id == "urn:li:corpGroup:data-platform"
    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert report.blast_radius.transitively_affected_assets == (DASHBOARD,)
    assert report.root_cause is not None and report.root_cause.confirmed


def test_target_stale_freshness_produces_freshness_root_cause():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(live_handler()),
    )

    report = provider.investigate(record(RAW))

    assert report.root_cause is not None
    assert report.root_cause.asset_id == RAW
    assert report.root_cause.issue_category == "freshness"
    assert "stale freshness evidence" in report.root_cause.description
    assert RAW in report.root_cause.description
    assert report.confirmed_findings[0].finding_id == "freshness-failure"


def test_target_failed_quality_produces_quality_root_cause():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            live_handler(
                target_freshness_status="healthy",
                target_quality_status="failed",
            )
        ),
    )

    report = provider.investigate(record(RAW))

    assert report.root_cause is not None
    assert report.root_cause.asset_id == RAW
    assert report.root_cause.issue_category == "quality"
    assert "failed quality assertion" in report.root_cause.description
    assert RAW in report.root_cause.description
    assert report.confirmed_findings[0].finding_id == "quality-failure"


def test_downstream_quality_failure_is_not_described_as_target_freshness():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            live_handler(
                target_freshness_status="healthy",
                target_quality_status="passing",
                downstream_quality_status="failed",
            )
        ),
    )

    report = provider.investigate(record(RAW))

    assert report.root_cause is not None
    assert report.root_cause.asset_id == MODEL
    assert report.root_cause.issue_category == "quality"
    assert "failed quality assertion" in report.root_cause.description
    assert MODEL in report.root_cause.description
    assert "stale freshness" not in report.root_cause.description


def test_target_failure_is_preferred_over_downstream_failure():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            live_handler(
                target_freshness_status="healthy",
                target_quality_status="failed",
                downstream_quality_status="failed",
            )
        ),
    )

    report = provider.investigate(record(RAW))

    assert report.root_cause is not None
    assert report.root_cause.asset_id == RAW
    assert report.root_cause.issue_category == "quality"


def test_no_failed_evidence_has_no_confirmed_root_cause():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            live_handler(
                target_freshness_status="healthy",
                target_quality_status="passing",
                downstream_quality_status="passing",
            )
        ),
    )

    report = provider.investigate(record(RAW))

    assert report.root_cause is None
    assert report.confirmed_findings == ()


def test_exact_target_search_discovers_bounded_transitive_downstream_only():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=2,
        transport=httpx.MockTransport(live_handler()),
    )
    report = provider.investigate(record(RAW))

    assert report.target_asset.external_id == RAW
    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert report.blast_radius.transitively_affected_assets == (DASHBOARD,)
    assert all(item.asset_id != UNRELATED for item in report.evidence_ledger)


def test_downstream_traversal_stops_at_depth_bound():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=1,
        transport=httpx.MockTransport(live_handler()),
    )
    report = provider.investigate(record(RAW))

    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert report.blast_radius.transitively_affected_assets == ()
    assert report.blast_radius.truncated
    assert report.blast_radius.impact_summary_inputs["truncated"] is True
    assert any(
        item.source_operation == "scrollAcrossLineage:bounded-truncation"
        and item.factual_payload["lineage_truncated"] is True
        for item in report.evidence_ledger
    )
    assert "truncated lineage graph applies a 0.10 penalty" in report.confidence.penalties
    assert any(
        rule.rule_id == "truncated_blast_radius" and rule.applied
        for rule in report.severity.applied_rules
    )
    assert DASHBOARD not in report.blast_radius.overall_asset_ids


def test_lineage_ending_at_depth_bound_is_not_truncated():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=1,
        transport=httpx.MockTransport(live_handler(terminal_model=True)),
    )

    report = provider.investigate(record(RAW))

    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert not report.blast_radius.truncated
    assert report.blast_radius.impact_summary_inputs["truncated"] is False
    assert not any(
        item.source_operation == "scrollAcrossLineage:bounded-truncation"
        for item in report.evidence_ledger
    )
    assert not any("truncated lineage" in item for item in report.confidence.penalties)


def test_cycle_only_lookahead_does_not_mark_truncation():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=1,
        transport=httpx.MockTransport(
            live_handler(
                downstream_override={
                    RAW: (MODEL,),
                    MODEL: (RAW,),
                }
            )
        ),
    )

    report = provider.investigate(record(RAW))

    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert not report.blast_radius.truncated


def test_converging_result_before_new_child_marks_truncation():
    requested_counts: list[int] = []
    delegate = live_handler(
        downstream_override={
            RAW: (MODEL,),
            MODEL: (RAW, OUT_OF_BOUND),
        }
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/graphql":
            body = json.loads(request.read())
            if "dicDownstreamLineage" in body["query"]:
                requested_counts.append(body["variables"]["input"]["count"])
        return delegate(request)

    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=1,
        maximum_lineage_nodes=10,
        transport=httpx.MockTransport(handler),
    )

    report = provider.investigate(record(RAW))

    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert OUT_OF_BOUND not in report.blast_radius.overall_asset_ids
    assert report.blast_radius.truncated
    assert requested_counts[-1] == 11
    assert "truncated lineage graph applies a 0.10 penalty" in report.confidence.penalties


def test_multiple_discovered_results_before_new_child_mark_truncation():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=1,
        maximum_lineage_nodes=10,
        transport=httpx.MockTransport(
            live_handler(
                downstream_override={
                    RAW: (MODEL, BRANCH),
                    MODEL: (RAW, BRANCH, OUT_OF_BOUND),
                    BRANCH: (RAW, MODEL),
                }
            )
        ),
    )

    report = provider.investigate(record(RAW))

    assert report.blast_radius.directly_affected_assets == tuple(
        sorted((MODEL, BRANCH))
    )
    assert OUT_OF_BOUND not in report.blast_radius.overall_asset_ids
    assert report.blast_radius.truncated
    assert report.blast_radius.impact_summary_inputs["truncated"] is True


def test_downstream_cycle_terminates_without_duplicate_or_unrelated_assets():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        maximum_lineage_depth=10,
        maximum_lineage_nodes=10,
        transport=httpx.MockTransport(live_handler(cycle=True)),
    )
    report = provider.investigate(record(RAW))

    assert report.blast_radius.directly_affected_assets == (MODEL,)
    assert report.blast_radius.transitively_affected_assets == (DASHBOARD,)
    asset_metadata = {
        item.asset_id
        for item in report.evidence_ledger
        if item.evidence_type is EvidenceType.ASSET_METADATA
    }
    assert asset_metadata == {RAW, MODEL, DASHBOARD}


def test_missing_lineage_response_fails_without_fabricated_evidence():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(live_handler(malformed_lineage=True)),
    )
    with pytest.raises(McpUnavailable, match="missing required fields"):
        provider.investigate(record(RAW))


@pytest.mark.parametrize(
    "envelope",
    ([], "unexpected", None, {}, {"aspects": []}),
    ids=(
        "top-level-array",
        "top-level-string",
        "top-level-null",
        "missing-aspects",
        "non-object-aspects",
    ),
)
def test_entities_v2_rejects_malformed_envelopes(envelope):
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token="private-test-token",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json=envelope)
        ),
    )

    with pytest.raises(McpUnavailable, match="metadata could not be read") as raised:
        provider._aspects(RAW)

    assert "private-test-token" not in str(raised.value)
    assert str(envelope) not in str(raised.value)


@pytest.mark.parametrize(
    "aspects",
    (
        {"datasetProperties": "invalid"},
        {"datasetProperties": {"value": []}},
    ),
    ids=("malformed-aspect-entry", "non-object-aspect-value"),
)
def test_entities_v2_rejects_malformed_aspect_payloads(aspects):
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"aspects": aspects})
        ),
    )

    with pytest.raises(McpUnavailable, match="metadata could not be read"):
        provider._aspects(RAW)


def test_entities_v2_accepts_valid_aspects_mapping():
    expected = {"datasetProperties": {"value": {"name": "NYC Taxi"}}}
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(200, json={"aspects": expected})
        ),
    )

    assert provider._aspects(RAW) == expected


def test_approved_add_tag_is_read_back_and_returns_verified_receipt():
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        mutation_enabled=True,
        transport=httpx.MockTransport(live_handler()),
    )
    receipt = provider.writeback(resolved_record(RAW))

    assert receipt.evidence_type is EvidenceType.WRITEBACK_RECEIPT
    assert receipt.reliability is Reliability.VERIFIED
    assert receipt.factual_payload["verified"] is True
    assert receipt.factual_payload["tag_urn"] == "urn:li:tag:dic-incident-recorded"


def test_name_based_writeback_and_readback_use_only_resolved_dataset_urn():
    observed_mutation_urns: list[str] = []
    observed_readback_urns: list[str] = []
    delegate = live_handler()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/graphql":
            body = json.loads(request.read())
            if "dicAddTag" in body["query"]:
                observed_mutation_urns.append(
                    body["variables"]["input"]["resourceUrn"]
                )
        elif request.url.path.startswith("/entitiesV2/"):
            observed_readback_urns.append(
                unquote(request.url.path.removeprefix("/entitiesV2/"))
            )
        return delegate(request)

    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        mutation_enabled=True,
        transport=httpx.MockTransport(handler),
    )

    receipt = provider.writeback(resolved_record("NYC Taxi raw"))

    assert observed_mutation_urns == [RAW]
    assert observed_readback_urns == [RAW]
    assert "NYC Taxi raw" not in observed_mutation_urns
    assert receipt.asset_id == RAW


@pytest.mark.parametrize(
    "resolved_urn",
    (None, "", "NYC Taxi raw", "urn:li:chart:1", "urn:li:dataset:()"),
)
def test_missing_or_malformed_resolved_dataset_urn_fails_before_mutation(
    resolved_urn,
):
    mutation_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal mutation_calls
        if request.url.path == "/api/graphql":
            mutation_calls += 1
        return httpx.Response(500)

    value = record("NYC Taxi raw")
    if resolved_urn is not None:
        value = resolved_record("NYC Taxi raw")
        value = value.model_copy(
            update={
                "report": value.report.model_copy(
                    update={
                        "target_asset": value.report.target_asset.model_copy(
                            update={"external_id": resolved_urn}
                        )
                    }
                )
            }
        )
    provider = DataHubLiveEvidenceProvider(
        gms_url="http://datahub-gms:8080",
        token=None,
        mutation_enabled=True,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(NormalizationFailure, match="resolved DataHub dataset URN"):
        provider.writeback(value)

    assert mutation_calls == 0


def test_successful_approval_gated_writeback_reaches_recorded_with_receipt():
    class SuccessfulWriter(ReadyWritebackProvider):
        @property
        def readiness(self):
            return EvidenceProviderReadiness(
                dependency_name="successful readback provider",
                status="ready",
                configured=True,
                available=True,
                supports_datahub=True,
                supports_mcp=True,
                supports_writeback=True,
            )

        def mutate_writeback(self, record):
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(live_handler()),
            )
            return provider.mutate_writeback(record)

        def verify_writeback(self, record):
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(live_handler()),
            )
            return provider.verify_writeback(record)

    service, _, incident_id = approved_service(
        "incident-success", SuccessfulWriter(None)
    )
    recorded = service.writeback(incident_id, ActorCommand(actor="operator"))

    assert recorded.workflow.current_state is IncidentState.RECORDED
    assert recorded.report is not None
    assert recorded.report.evidence_ledger[-1].evidence_type is EvidenceType.WRITEBACK_RECEIPT


@pytest.mark.parametrize(
    "mutation_handler",
    (
        lambda request: httpx.Response(
            200, content=b"{", headers={"Content-Type": "application/json"}
        ),
        lambda request: httpx.Response(200, json=[]),
        lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("timed out")),
        lambda request: (_ for _ in ()).throw(httpx.ConnectError("connection lost")),
        lambda request: httpx.Response(502, text="unexpected upstream response"),
    ),
    ids=(
        "malformed-json",
        "malformed-envelope",
        "timeout",
        "connection-loss",
        "unexpected-http-response",
    ),
)
def test_uncertain_mutation_outcome_preserves_approved_state(mutation_handler):
    class UncertainWriter(ReadyWritebackProvider):
        def mutate_writeback(self, record):
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(mutation_handler),
            )
            return provider.mutate_writeback(record)

        def verify_writeback(self, record):
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(live_handler()),
            )
            return provider.verify_writeback(record)

    service, repository, incident_id = approved_service(
        "incident-uncertain", UncertainWriter(None)
    )

    with pytest.raises(
        WritebackVerificationFailure, match="acceptance could not be verified"
    ):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.WRITEBACK_PENDING
    assert stored.last_action_reason == service.VERIFICATION_PENDING
    assert not any(
        transition.to_state is IncidentState.RECORDED
        for transition in stored.workflow.history
    )


def test_explicit_graphql_mutation_rejection_remains_failed():
    class RejectedWriter(ReadyWritebackProvider):
        def mutate_writeback(self, record):
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(
                        200,
                        json={
                            "errors": [{"message": "mutation rejected"}],
                            "data": None,
                        },
                    )
                ),
            )
            return provider.mutate_writeback(record)

        def verify_writeback(self, record):
            raise AssertionError("verification must not follow proven rejection")

    service, repository, incident_id = approved_service(
        "incident-rejected", RejectedWriter(None)
    )

    with pytest.raises(McpUnavailable, match="rejected"):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.FAILED


def test_malformed_entities_readback_preserves_approved_state():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/graphql":
            return httpx.Response(200, json={"data": {"addTag": True}})
        return httpx.Response(200, json=[])

    class MalformedReadbackWriter(ReadyWritebackProvider):
        def _provider(self):
            return DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(handler),
            )

        def mutate_writeback(self, record):
            return self._provider().mutate_writeback(record)

        def verify_writeback(self, record):
            return self._provider().verify_writeback(record)

    service, repository, incident_id = approved_service(
        "incident-malformed-readback", MalformedReadbackWriter(None)
    )

    with pytest.raises(
        WritebackVerificationFailure, match="verification was unavailable"
    ):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.WRITEBACK_PENDING


def test_mismatched_readback_preserves_approval_and_can_retry_to_recorded():
    class MismatchedWriter(ReportProvider):
        readback_matches = False
        mutation_calls = 0
        verification_calls = 0

        @property
        def readiness(self):
            return EvidenceProviderReadiness(
                dependency_name="mismatched readback provider",
                status="ready",
                configured=True,
                available=True,
                supports_datahub=True,
                supports_mcp=True,
                supports_writeback=True,
            )

        def _provider(self):
            return DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(
                    live_handler(readback_matches=self.readback_matches)
                ),
            )

        def mutate_writeback(self, record):
            self.mutation_calls += 1
            return self._provider().mutate_writeback(record)

        def verify_writeback(self, record):
            self.verification_calls += 1
            return self._provider().verify_writeback(record)

    writer = MismatchedWriter(None)
    service, repository, incident_id = approved_service("incident-writeback", writer)

    with pytest.raises(
        WritebackVerificationFailure, match="read-back verification failed"
    ):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.WRITEBACK_PENDING
    assert stored.payload_binding_id == service.payload_binding(stored)
    assert not any(
        transition.to_state is IncidentState.RECORDED
        for transition in stored.workflow.history
    )

    with pytest.raises(WritebackVerificationFailure):
        service.writeback(incident_id, ActorCommand(actor="operator"))
    assert writer.mutation_calls == 1
    assert writer.verification_calls == 2

    writer.readback_matches = True
    recorded = service.writeback(incident_id, ActorCommand(actor="operator"))
    assert recorded.workflow.current_state is IncidentState.RECORDED
    assert writer.mutation_calls == 1
    assert writer.verification_calls == 3


def test_definite_mutation_failure_is_persisted_truthfully():
    class FailedMutationWriter(ReadyWritebackProvider):
        def mutate_writeback(self, record):
            raise MutationDisabled("mutation rejected before acceptance")

        def verify_writeback(self, record):
            raise AssertionError("verification must not follow proven rejection")

    service, repository, incident_id = approved_service(
        "incident-mutation-failed", FailedMutationWriter(None)
    )

    with pytest.raises(MutationDisabled, match="rejected"):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.FAILED
    assert stored.workflow.failed_from_state is IncidentState.WRITEBACK_PENDING


@pytest.mark.parametrize(
    ("configured", "available", "supports_writeback"),
    (
        (True, True, False),
        (True, False, True),
        (False, False, False),
    ),
    ids=("mutation-disabled", "provider-unavailable", "provider-unsupported"),
)
def test_unready_writeback_provider_preserves_approved_without_mutation(
    configured,
    available,
    supports_writeback,
):
    class GuardedWriter(ReportProvider):
        mutation_calls = 0

        @property
        def readiness(self):
            return EvidenceProviderReadiness(
                dependency_name="guarded writeback provider",
                status="ready" if available else "unavailable",
                configured=configured,
                available=available,
                supports_datahub=True,
                supports_mcp=True,
                supports_writeback=supports_writeback,
            )

        def mutate_writeback(self, record):
            self.mutation_calls += 1
            raise AssertionError("unready provider must not mutate")

        def verify_writeback(self, record):
            raise AssertionError("unready provider must not verify")

    writer = GuardedWriter(None)
    service, repository, incident_id = approved_service(
        "incident-unready-writeback", writer
    )

    with pytest.raises(DependencyUnavailable, match="disabled or unavailable"):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.APPROVED
    assert writer.mutation_calls == 0


def test_concurrent_writeback_requests_call_external_writer_at_most_once():
    entered = Event()
    release = Event()

    class BlockingWriter(ReadyWritebackProvider):
        write_calls = 0

        def mutate_writeback(self, record):
            self.write_calls += 1
            entered.set()
            assert release.wait(timeout=2)
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(live_handler()),
            )
            return provider.mutate_writeback(record)

        def verify_writeback(self, record):
            provider = DataHubLiveEvidenceProvider(
                gms_url="http://datahub-gms:8080",
                token=None,
                mutation_enabled=True,
                transport=httpx.MockTransport(live_handler()),
            )
            return provider.verify_writeback(record)

    writer = BlockingWriter(None)
    service, repository, incident_id = approved_service("incident-race", writer)
    first_errors: list[Exception] = []

    def first_request():
        try:
            service.writeback(incident_id, ActorCommand(actor="operator-1"))
        except Exception as error:
            first_errors.append(error)

    thread = Thread(target=first_request)
    thread.start()
    assert entered.wait(timeout=2)
    with pytest.raises(InvalidWorkflowTransition, match="still in progress"):
        service.writeback(incident_id, ActorCommand(actor="operator-2"))
    release.set()
    thread.join(timeout=2)

    assert not first_errors
    assert writer.write_calls == 1
    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.RECORDED


def test_stale_pending_claim_fails_before_external_side_effect():
    class CountingWriter(ReadyWritebackProvider):
        write_calls = 0

        def mutate_writeback(self, record):
            self.write_calls += 1
            raise AssertionError("writer must not be called")

        def verify_writeback(self, record):
            raise AssertionError("verifier must not be called")

    class StaleClaimRepository:
        def __init__(self, delegate):
            self.delegate = delegate

        def __getattr__(self, name):
            return getattr(self.delegate, name)

        def save(self, record, *, expected_revision):
            if record.workflow.current_state is IncidentState.WRITEBACK_PENDING:
                raise ConcurrentUpdateConflict("The incident changed after it was read.")
            return self.delegate.save(record, expected_revision=expected_revision)

    writer = CountingWriter(None)
    service, repository, incident_id = approved_service("incident-stale", writer)
    service.repository = StaleClaimRepository(repository)

    with pytest.raises(ConcurrentUpdateConflict):
        service.writeback(incident_id, ActorCommand(actor="operator"))

    assert writer.write_calls == 0
    stored = repository.get(incident_id)
    assert stored is not None
    assert stored.workflow.current_state is IncidentState.APPROVED
