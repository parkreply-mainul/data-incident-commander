from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import subprocess
import threading
import time
from types import SimpleNamespace

import pytest

from data_incident_commander.application.commands import CreateInvestigation
from data_incident_commander.application.errors import DependencyUnavailable
from data_incident_commander.domain.models import Severity
from data_incident_commander.integrations.datahub.adapter import DataHubMcpEvidenceProvider
from data_incident_commander.integrations.datahub.capabilities import CapabilityInventory
from data_incident_commander.integrations.datahub.client_protocol import VerifiedToolResult
from data_incident_commander.integrations.datahub.errors import (
    McpUnavailable,
    ToolInventoryUnavailable,
)
from data_incident_commander.integrations.datahub.stdio_client import (
    _CHILD_ENVIRONMENT_ALLOWLIST,
    _SDK_INHERITED_OPERATIONAL_ENVIRONMENT,
    DataHubMcpStdioClient,
    VERIFIED_TOOL_NAMES,
)
from mcp.client.stdio import DEFAULT_INHERITED_ENV_VARS, get_default_environment
from tests.application.conftest import build_service

from .test_config_and_capabilities import config, observed_inventory


NOW = datetime(2026, 7, 24, 12, tzinfo=timezone.utc)


def verified_inventory() -> CapabilityInventory:
    baseline = observed_inventory()
    return CapabilityInventory(
        server_version="0.6.0",
        observed_at=baseline.observed_at,
        capabilities=tuple(
            item.model_copy(update={"version": "0.6.0"})
            for item in baseline.capabilities
        ),
    )


def schemas():
    values = {
        name: {"type": "object", "properties": {}, "required": []}
        for name in VERIFIED_TOOL_NAMES
    }
    values["search"] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "num_results": {"type": "integer"},
            "offset": {"type": "integer"},
        },
        "required": [],
    }
    values["get_entities"] = {
        "type": "object",
        "properties": {
            "urns": {
                "anyOf": [
                    {"type": "array", "items": {"type": "string"}},
                    {"type": "string"},
                ]
            }
        },
        "required": ["urns"],
    }
    values["get_lineage"] = {
        "type": "object",
        "properties": {
            "urn": {"type": "string"},
            "upstream": {"type": "boolean"},
            "max_hops": {"type": "integer"},
            "max_results": {"type": "integer"},
            "offset": {"type": "integer"},
        },
        "required": ["urn"],
    }
    values["get_lineage_paths_between"] = {
        "type": "object",
        "properties": {
            "source_urn": {"type": "string"},
            "target_urn": {"type": "string"},
            "source_column": {
                "anyOf": [{"type": "string"}, {"type": "null"}]
            },
            "target_column": {
                "anyOf": [{"type": "string"}, {"type": "null"}]
            },
            "direction": {
                "anyOf": [{"type": "string"}, {"type": "null"}]
            },
        },
        "required": ["source_urn", "target_urn"],
    }
    return values


def sdk_fakes(*, tool_schemas=None, call_result=None, failure=None, delay=0):
    state = {
        "parameters": [],
        "errlogs": [],
        "transport_closed": 0,
        "session_closed": 0,
    }
    selected = tool_schemas or schemas()

    @asynccontextmanager
    async def transport(parameters, *, errlog):
        state["parameters"].append(parameters)
        state["errlogs"].append(errlog)
        try:
            yield ("read", "write")
        finally:
            state["transport_closed"] += 1

    class Session:
        async def initialize(self):
            if delay:
                await asyncio.sleep(delay)
            if failure:
                raise failure

        async def list_tools(self):
            return SimpleNamespace(
                tools=[
                    {"name": name, "inputSchema": schema}
                    for name, schema in selected.items()
                ]
            )

        async def call_tool(self, name, arguments):
            return SimpleNamespace(
                structuredContent=call_result or {"ok": True},
                content=[],
                isError=False,
            )

    @asynccontextmanager
    async def session(*streams):
        try:
            yield Session()
        finally:
            state["session_closed"] += 1

    return state, transport, session


def test_stdio_client_initializes_validates_and_closes_exact_pinned_command():
    state, transport, session = sdk_fakes()
    environment = {
        "PATH": "/controlled",
        "DIC_TEST_TOKEN": "token-that-must-not-leak",
    }
    client = DataHubMcpStdioClient(
        config(
            mcp_server_version="0.6.0",
            token_env_var="DIC_TEST_TOKEN",
        ),
        environment=environment,
        transport_factory=transport,
        session_factory=session,
    )

    client.initialize()
    result = client.invoke(
        "search", {"query": "taxi", "num_results": 1, "offset": 0}
    )

    assert client.ready
    assert {tool.name for tool in client.list_tools()} == VERIFIED_TOOL_NAMES
    assert result.payload == {"ok": True}
    assert state["parameters"][0]["command"] == "uvx"
    assert state["parameters"][0]["args"] == (
        "mcp-server-datahub==0.6.0",
        "--transport",
        "stdio",
    )
    assert state["parameters"][0]["env"]["DATAHUB_GMS_URL"] == "http://datahub-gms:8080"
    assert state["parameters"][0]["env"]["DIC_TEST_TOKEN"] == "token-that-must-not-leak"
    assert set(state["parameters"][0]["env"]) == {
        "PATH",
        "DATAHUB_GMS_URL",
        "DIC_TEST_TOKEN",
    }
    assert state["errlogs"] == [subprocess.DEVNULL, subprocess.DEVNULL]
    assert "token-that-must-not-leak" not in repr(client)
    assert state["transport_closed"] == 2
    assert state["session_closed"] == 2


@pytest.mark.parametrize(
    "bad_schemas",
    [
        lambda values: {name: schema for name, schema in values.items() if name != "search"},
        lambda values: {
            **values,
            "get_lineage": {"type": "object", "properties": {"urn": {}}},
        },
        lambda values: {
            **values,
            "search": {
                **values["search"],
                "properties": {
                    **values["search"]["properties"],
                    "query": {"type": "integer"},
                },
            },
        },
        lambda values: {
            **values,
            "get_entities": {
                **values["get_entities"],
                "required": [],
            },
        },
        lambda values: {
            **values,
            "get_entities": {
                **values["get_entities"],
                "properties": {
                    "urns": {
                        "anyOf": [
                            {
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                            {"type": "string"},
                        ]
                    }
                },
            },
        },
        lambda values: {
            **values,
            "get_lineage_paths_between": {
                **values["get_lineage_paths_between"],
                "properties": {
                    **values["get_lineage_paths_between"]["properties"],
                    "source_urn": {"type": "integer"},
                },
            },
        },
        lambda values: {
            **values,
            "get_lineage_paths_between": {
                **values["get_lineage_paths_between"],
                "required": ["source_urn"],
            },
        },
        lambda values: {
            **values,
            "get_lineage_paths_between": {
                **values["get_lineage_paths_between"],
                "properties": {
                    **values["get_lineage_paths_between"]["properties"],
                    "unexpected": {"type": "string"},
                },
            },
        },
    ],
)
def test_missing_or_incompatible_inventory_fails_closed_and_cleans_up(bad_schemas):
    state, transport, session = sdk_fakes(tool_schemas=bad_schemas(schemas()))
    client = DataHubMcpStdioClient(
        config(mcp_server_version="0.6.0"),
        environment={},
        transport_factory=transport,
        session_factory=session,
    )

    with pytest.raises(ToolInventoryUnavailable):
        client.initialize()

    assert not client.ready
    assert state["transport_closed"] == 1
    assert state["session_closed"] == 1


def test_session_failure_is_safe_and_cleanup_occurs():
    state, transport, session = sdk_fakes(failure=RuntimeError("secret raw log"))
    client = DataHubMcpStdioClient(
        config(mcp_server_version="0.6.0"),
        environment={"DATAHUB_GMS_TOKEN": "hidden-token"},
        transport_factory=transport,
        session_factory=session,
    )

    with pytest.raises(McpUnavailable) as error:
        client.initialize()

    assert "hidden-token" not in str(error.value)
    assert "secret raw log" not in str(error.value)
    assert state["transport_closed"] == 1
    assert state["session_closed"] == 1


def test_effective_sdk_environment_is_explicitly_approved(monkeypatch):
    for name in _SDK_INHERITED_OPERATIONAL_ENVIRONMENT:
        monkeypatch.setenv(name, f"controlled-{name.lower()}")
    monkeypatch.setenv("DATAHUB_GMS_TOKEN", "controlled-token")
    monkeypatch.setenv("UNRELATED_SECRET", "must-not-reach-child")
    state, transport, session = sdk_fakes()
    client = DataHubMcpStdioClient(
        config(mcp_server_version="0.6.0"),
        transport_factory=transport,
        session_factory=session,
    )

    client.initialize()

    configured = state["parameters"][0]["env"]
    effective = {**get_default_environment(), **configured}
    assert set(DEFAULT_INHERITED_ENV_VARS) == _SDK_INHERITED_OPERATIONAL_ENVIRONMENT
    assert set(effective).issubset(
        _CHILD_ENVIRONMENT_ALLOWLIST
        | {"DATAHUB_GMS_URL", "DATAHUB_GMS_TOKEN"}
    )
    assert "UNRELATED_SECRET" not in effective
    assert effective["DATAHUB_GMS_TOKEN"] == "controlled-token"


def test_invocation_arguments_must_match_verified_schema():
    _, transport, session = sdk_fakes()
    client = DataHubMcpStdioClient(
        config(mcp_server_version="0.6.0"),
        environment={},
        transport_factory=transport,
        session_factory=session,
    )
    client.initialize()

    with pytest.raises(ToolInventoryUnavailable):
        client.invoke("search", {"query": 7, "num_results": 1, "offset": 0})


def test_timeout_is_safe_and_cleans_up_session_and_transport():
    state, transport, session = sdk_fakes(delay=0.05)
    client = DataHubMcpStdioClient(
        config(mcp_server_version="0.6.0", request_timeout_seconds=0.001),
        environment={},
        transport_factory=transport,
        session_factory=session,
    )

    with pytest.raises(McpUnavailable, match="timed out"):
        client.initialize()

    assert state["transport_closed"] == 1
    assert state["session_closed"] == 1


RAW = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_trips_raw,PROD)"
METRICS = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_daily_metrics,PROD)"
DASHBOARD = "urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_dashboard,PROD)"


class FixtureClient:
    def __init__(self):
        self._ready = True
        self.calls = []
        self.closed = False

    @property
    def ready(self):
        return self._ready

    def initialize(self):
        self._ready = True

    def list_tools(self):
        raise AssertionError("preverified inventory should be reused")

    def invoke(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "search":
            payload = {"entities": [{"urn": RAW}]}
        elif name == "get_lineage" and arguments["upstream"]:
            payload = {"upstreams": {"searchResults": [], "hasMore": False}}
        elif name == "get_lineage" and arguments["urn"] == RAW:
            payload = {
                "downstreams": {
                    "searchResults": [{"entity": {"urn": METRICS}}],
                    "hasMore": False,
                }
            }
        elif name == "get_lineage" and arguments["urn"] == METRICS:
            payload = {
                "downstreams": {
                    "searchResults": [{"entity": {"urn": DASHBOARD}}],
                    "hasMore": False,
                }
            }
        elif name == "get_lineage" and arguments["urn"] == DASHBOARD:
            payload = {"downstreams": {"searchResults": [], "hasMore": False}}
        elif name == "get_entities":
            payload = {
                "entities": [
                    {
                        "urn": RAW,
                        "name": "NYC Taxi Trips Raw",
                        "properties": {
                            "customProperties": {
                                "dic_freshness_status": "stale",
                                "dic_freshness_observed_at": "2026-07-24T09:00:00Z",
                                "dic_quality_status": "passing",
                                "dic_asset_type": "dataset",
                                "dic_criticality": "high",
                            }
                        },
                        "owners": [
                            {
                                "owner": "urn:li:corpGroup:data-platform",
                                "type": "TECHNICAL_OWNER",
                            }
                        ],
                    },
                    {
                        "urn": METRICS,
                        "name": "NYC Taxi Daily Metrics",
                        "properties": {
                            "customProperties": {
                                "dic_asset_type": "model",
                                "dic_criticality": "high",
                            }
                        },
                    },
                    {
                        "urn": DASHBOARD,
                        "name": "NYC Taxi Operations Dashboard",
                        "properties": {
                            "customProperties": {
                                "dic_asset_type": "dashboard",
                                "dic_criticality": "critical",
                            }
                        },
                    },
                ]
            }
        else:
            raise AssertionError(f"unexpected MCP call: {name}")
        return VerifiedToolResult(tool_name=name, observed_at=NOW, payload=payload)

    def close(self):
        self.closed = True
        self._ready = False


def test_nyc_taxi_investigation_uses_only_required_mcp_reads_and_normalizes():
    client = FixtureClient()
    provider = DataHubMcpEvidenceProvider(
        config(mcp_server_version="0.6.0"),
        client=client,
        inventory=verified_inventory(),
    )
    service, _ = build_service("mcp-nyc")
    service.evidence_provider = provider
    draft = service.create_draft(
        CreateInvestigation(title="NYC Taxi stale", target_asset_id=RAW)
    )

    investigated = service.investigate(draft.incident_id)
    report = investigated.report

    assert report is not None
    assert report.target_asset.display_name == "NYC Taxi Trips Raw"
    assert report.target_asset.owners[0].display_name == "data-platform"
    assert report.root_cause.issue_category == "freshness"
    assert report.blast_radius.directly_affected_assets == (METRICS,)
    assert report.blast_radius.transitively_affected_assets == (DASHBOARD,)
    assert report.severity.severity is Severity.HIGH
    assert report.confidence.confidence > 0
    assert report.remediation_actions
    assert [name for name, _ in client.calls] == [
        "search",
        "get_lineage",
        "get_lineage",
        "get_lineage",
        "get_lineage",
        "get_entities",
    ]
    assert client.closed
    assert all(item.source_system == "datahub-mcp" for item in report.evidence_ledger)
    upstream_call = next(
        arguments
        for name, arguments in client.calls
        if name == "get_lineage" and arguments["upstream"]
    )
    assert upstream_call["max_hops"] == 1


def test_lineage_node_limit_is_exact_and_marks_truncation():
    client = FixtureClient()
    provider = DataHubMcpEvidenceProvider(
        config(mcp_server_version="0.6.0", maximum_lineage_nodes=2),
        client=client,
        inventory=verified_inventory(),
    )
    service, _ = build_service("mcp-bounded")
    service.evidence_provider = provider
    draft = service.create_draft(
        CreateInvestigation(title="bounded", target_asset_id=RAW)
    )

    report = service.investigate(draft.incident_id).report

    assert report is not None
    assert report.blast_radius.overall_asset_count == 2
    assert report.blast_radius.truncated
    assert report.blast_radius.directly_affected_assets == (METRICS,)
    assert report.blast_radius.transitively_affected_assets == ()


def test_provider_serializes_investigation_lifecycle():
    provider = DataHubMcpEvidenceProvider(config(mcp_server_version="0.6.0"))
    active = 0
    maximum_active = 0
    guard = threading.Lock()

    def controlled(_record):
        nonlocal active, maximum_active
        with guard:
            active += 1
            maximum_active = max(maximum_active, active)
        time.sleep(0.01)
        with guard:
            active -= 1
        return "done"

    provider._investigate_locked = controlled
    threads = [
        threading.Thread(target=provider.investigate, args=(object(),))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert maximum_active == 1


def test_initialization_failure_is_cached_for_retry_interval():
    class FailingClient:
        ready = False

        def __init__(self):
            self.calls = 0

        def initialize(self):
            self.calls += 1
            raise RuntimeError("unavailable")

        def list_tools(self):
            return ()

        def close(self):
            pass

    client = FailingClient()
    provider = DataHubMcpEvidenceProvider(
        config(mcp_server_version="0.6.0"), client=client
    )

    assert not provider.readiness.available
    assert not provider.readiness.available
    assert client.calls == 1


class InvalidEntityClient(FixtureClient):
    def invoke(self, name, arguments):
        result = super().invoke(name, arguments)
        if name != "get_entities":
            return result
        payload = result.payload
        entities = [dict(item) for item in payload["entities"]]
        entities[0]["owners"] = (
            {
                "owner": "urn:li:corpGroup:data-platform",
                "type": "TECHNICAL_OWNER",
            },
            {
                "owner": "urn:li:corpGroup:data-platform",
                "type": "TECHNICAL_OWNER",
            },
        )
        return VerifiedToolResult(
            tool_name=name,
            observed_at=NOW,
            payload={"entities": entities},
        )


def test_unexpected_normalization_validation_uses_safe_dependency_error():
    provider = DataHubMcpEvidenceProvider(
        config(mcp_server_version="0.6.0"),
        client=InvalidEntityClient(),
        inventory=verified_inventory(),
    )
    service, _ = build_service("mcp-invalid-entity")
    service.evidence_provider = provider
    draft = service.create_draft(
        CreateInvestigation(title="invalid entity", target_asset_id=RAW)
    )

    with pytest.raises(DependencyUnavailable):
        service.investigate(draft.incident_id)


class MalformedClient(FixtureClient):
    def invoke(self, name, arguments):
        return VerifiedToolResult(tool_name=name, observed_at=NOW, payload={"bad": True})


def test_malformed_mcp_response_is_a_safe_dependency_error():
    provider = DataHubMcpEvidenceProvider(
        config(mcp_server_version="0.6.0"),
        client=MalformedClient(),
        inventory=verified_inventory(),
    )
    service, _ = build_service("mcp-malformed")
    service.evidence_provider = provider
    draft = service.create_draft(
        CreateInvestigation(title="bad MCP", target_asset_id=RAW)
    )

    with pytest.raises(DependencyUnavailable):
        service.investigate(draft.incident_id)
