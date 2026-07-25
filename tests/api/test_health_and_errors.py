from __future__ import annotations

from data_incident_commander.api.app import create_app
from data_incident_commander.application.protocols import EvidenceProviderReadiness
from data_incident_commander.config import Settings
from tests.api.conftest import SyncASGIClient
from tests.application.conftest import build_service


class ReadinessProvider:
    def __init__(
        self,
        *,
        configured=True,
        available=True,
        supports_datahub=True,
        supports_mcp=True,
        supports_writeback=False,
        status="ready",
    ):
        self.calls = 0
        self._readiness = EvidenceProviderReadiness(
            dependency_name="injected provider",
            status=status,
            configured=configured,
            available=available,
            supports_datahub=supports_datahub,
            supports_mcp=supports_mcp,
            supports_writeback=supports_writeback,
        )

    @property
    def readiness(self):
        return self._readiness

    def investigate(self, record):
        self.calls += 1
        raise AssertionError("readiness must not call investigate")


def test_health_is_application_only(api_context):
    client, _, _ = api_context
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.json()["version"] == "test"
    assert "datahub" not in response.json()
    assert response.headers["X-Request-ID"] == "request-fixed"


def test_caller_supplied_request_id_is_preserved_on_success(api_context):
    client, _, _ = api_context
    response = client.get("/health", headers={"X-Request-ID": "caller-id"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "caller-id"


def test_readiness_does_not_claim_demo_readiness(api_context):
    client, _, _ = api_context
    response = client.get("/health/readiness")
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "not_ready"
    assert body["components"]["datahub"]["status"] == "not_configured"
    assert body["components"]["mcp"]["status"] == "not_configured"
    assert body["components"]["writeback"]["status"] == "not_configured"
    assert body["components"]["evidence_provider"]["status"] == "not_configured"


def test_configured_provider_readiness_is_derived_without_network_call(api_context):
    client, service, _ = api_context
    provider = ReadinessProvider()
    service.evidence_provider = provider
    first = client.get("/health/readiness").json()
    second = client.get("/health/readiness").json()
    assert first["components"]["evidence_provider"]["status"] == "ready"
    assert first["components"]["datahub"]["status"] == "ready"
    assert first["components"]["mcp"]["status"] == "ready"
    assert first["components"]["writeback"]["status"] == "disabled"
    assert first["status"] == "not_ready"
    assert provider.calls == 0
    first.pop("timestamp")
    second.pop("timestamp")
    assert first == second


def test_configured_but_unavailable_provider_is_reported(api_context):
    client, service, _ = api_context
    service.evidence_provider = ReadinessProvider(
        available=False,
        status="unavailable",
    )
    components = client.get("/health/readiness").json()["components"]
    assert components["evidence_provider"]["status"] == "unavailable"
    assert components["datahub"]["status"] == "unavailable"
    assert components["mcp"]["status"] == "unavailable"


def test_datahub_only_and_mcp_capabilities_are_distinct(api_context):
    client, service, _ = api_context
    service.evidence_provider = ReadinessProvider(supports_mcp=False)
    datahub_only = client.get("/health/readiness").json()["components"]
    assert datahub_only["datahub"]["status"] == "ready"
    assert datahub_only["mcp"]["status"] == "unsupported"

    service.evidence_provider = ReadinessProvider(
        supports_datahub=True,
        supports_mcp=True,
    )
    mcp_backed = client.get("/health/readiness").json()["components"]
    assert mcp_backed["datahub"]["status"] == "ready"
    assert mcp_backed["mcp"]["status"] == "ready"


def test_gms_writeback_readiness_is_separate_from_unavailable_mcp(api_context):
    client, service, _ = api_context
    service.writeback_provider = ReadinessProvider(supports_writeback=True)

    components = client.get("/health/readiness").json()["components"]

    assert components["mcp"]["status"] == "not_configured"
    assert components["evidence_provider"]["status"] == "not_configured"
    assert components["writeback"]["status"] == "ready"


def test_writeback_readiness_reports_disabled_mutation(api_context):
    client, service, _ = api_context
    service.writeback_provider = ReadinessProvider(supports_writeback=False)

    assert (
        client.get("/health/readiness").json()["components"]["writeback"]["status"]
        == "disabled"
    )


def test_writeback_readiness_reports_unavailable_provider(api_context):
    client, service, _ = api_context
    service.writeback_provider = ReadinessProvider(
        available=False,
        supports_writeback=True,
        status="unavailable",
    )

    assert (
        client.get("/health/readiness").json()["components"]["writeback"]["status"]
        == "unavailable"
    )


def test_writeback_readiness_reports_enabled_available_provider(api_context):
    client, service, _ = api_context
    service.writeback_provider = ReadinessProvider(supports_writeback=True)

    body = client.get("/health/readiness").json()
    assert body["components"]["writeback"]["status"] == "ready"
    assert body["status"] == "not_ready"


def test_validation_error_is_stable_and_public_safe(api_context):
    client, _, _ = api_context
    response = client.post(
        "/api/v1/investigations",
        json={"title": "", "target_asset_id": "asset", "unknown": True},
        headers={"X-Request-ID": "request-user"},
    )
    body = response.json()
    assert response.status_code == 422
    assert body == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "The request is invalid.",
            "retryable": False,
            "request_id": "request-user",
            "details": {},
        }
    }
    assert response.headers["X-Request-ID"] == body["error"]["request_id"]
    assert "Traceback" not in response.text
    assert "/Users/" not in response.text


def test_unexpected_error_is_safely_normalized(api_context):
    client, service, _ = api_context

    def explode(*args, **kwargs):
        raise RuntimeError("/private/path secret=value")

    service.list = explode
    response = client.get("/api/v1/investigations")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]
    assert response.headers.get_list("X-Request-ID") == ["request-fixed"]
    assert "/private/path" not in response.text
    assert "secret=value" not in response.text


def test_generated_request_id_is_created_once_and_shared_by_body_and_header():
    service, _ = build_service()
    generated = []

    def next_request_id():
        generated.append("generated-id")
        return "generated-id"

    app = create_app(
        service=service,
        settings=Settings(service_version="test"),
        request_id_provider=next_request_id,
    )
    client = SyncASGIClient(app)
    response = client.get("/api/v1/investigations/missing")
    assert generated == ["generated-id"]
    assert response.status_code == 404
    assert response.headers.get_list("X-Request-ID") == ["generated-id"]
    assert response.json()["error"]["request_id"] == "generated-id"


def test_app_import_and_openapi_require_no_external_services():
    app = create_app()
    schema = app.openapi()
    assert "/health" in schema["paths"]
    assert "/api/v1/investigations" in schema["paths"]
