from __future__ import annotations

from data_incident_commander.application.commands import CreateInvestigation
from data_incident_commander.application.errors import ConcurrentUpdateConflict
from data_incident_commander.application.services import (
    InvestigationService,
    UnconfiguredEvidenceProvider,
)
from data_incident_commander.api.app import create_app
from data_incident_commander.config import Settings
from data_incident_commander.domain.models import IncidentState
from data_incident_commander.repositories.memory import InMemoryIncidentRepository
from tests.api.conftest import SyncASGIClient
from tests.application.conftest import (
    FixedIds,
    ReportProvider,
    SteppingClock,
    build_report,
)


def _create(client, title="Draft", target="asset:target"):
    return client.post(
        "/api/v1/investigations",
        json={"title": title, "target_asset_id": target},
    )


def test_create_draft_has_deterministic_fields_and_no_invented_results(api_context):
    client, _, _ = api_context
    response = _create(client)
    body = response.json()
    assert response.status_code == 201
    assert body["incident_id"] == "incident-0"
    assert body["state"] == "DRAFT"
    assert body["history"] == []
    assert body["report"] is None
    assert body["payload_binding_id"] is None


def test_unknown_fields_and_invalid_input_are_rejected(api_context):
    client, _, _ = api_context
    assert _create(client, title="").status_code == 422
    assert client.post(
        "/api/v1/investigations",
        json={"title": "Draft", "target_asset_id": "asset", "extra": "no"},
    ).status_code == 422


def test_duplicate_generated_incident_id_returns_conflict(api_context):
    client, service, _ = api_context
    service.id_provider = FixedIds("duplicate", "duplicate")
    assert _create(client).status_code == 201
    response = _create(client)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


class ConflictOnSaveRepository(InMemoryIncidentRepository):
    force_conflict = False

    def save(self, record, *, expected_revision):
        if self.force_conflict:
            raise ConcurrentUpdateConflict("internal repository detail")
        return super().save(record, expected_revision=expected_revision)


def test_concurrent_update_api_error_is_stable_retryable_and_rereadable():
    repository = ConflictOnSaveRepository()
    service = InvestigationService(
        repository,
        UnconfiguredEvidenceProvider(),
        id_provider=FixedIds("incident"),
        clock=SteppingClock(),
    )
    draft = service.create_draft(
        CreateInvestigation(title="Draft", target_asset_id="asset")
    )
    workflow = draft.workflow
    for state in (IncidentState.INVESTIGATED, IncidentState.AWAITING_APPROVAL):
        workflow = workflow.transition(
            state,
            actor="prepared",
            occurred_at=service.clock.now(),
        )
    awaiting = repository.save(
        draft.model_copy(update={"workflow": workflow}),
        expected_revision=draft.revision,
    )
    repository.force_conflict = True
    client = SyncASGIClient(
        create_app(service=service, settings=Settings(service_version="test"))
    )
    response = client.post(
        "/api/v1/investigations/incident/approve",
        json={"actor": "reviewer", "reason": "reviewed", "payload_binding_id": "sha256:x"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INCIDENT_CONFLICT"
    assert response.json()["error"]["retryable"] is True
    assert "repository" not in response.text
    reread = client.get("/api/v1/investigations/incident")
    assert reread.status_code == 200
    assert reread.json()["revision"] == awaiting.revision
    assert reread.json()["state"] == "AWAITING_APPROVAL"


def test_get_missing_returns_structured_404_with_request_id(api_context):
    client, _, _ = api_context
    response = client.get(
        "/api/v1/investigations/missing",
        headers={"X-Request-ID": "lookup-id"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "INCIDENT_NOT_FOUND"
    assert response.json()["error"]["request_id"] == "lookup-id"
    assert response.headers["X-Request-ID"] == "lookup-id"


def test_get_and_list_are_deterministic_and_bounded(api_context):
    client, _, _ = api_context
    first = _create(client, "First", "asset:1").json()
    second = _create(client, "Second", "asset:2").json()
    assert client.get(f"/api/v1/investigations/{first['incident_id']}").json() == first
    page = client.get("/api/v1/investigations?limit=1&offset=1").json()
    assert page["total"] == 2
    assert page["items"][0]["incident_id"] == second["incident_id"]
    assert client.get("/api/v1/investigations?limit=101").status_code == 422
    assert client.get("/api/v1/investigations?offset=-1").status_code == 422


def test_investigate_fails_closed_and_preserves_draft(api_context):
    client, _, repository = api_context
    incident_id = _create(client).json()["incident_id"]
    response = client.post(f"/api/v1/investigations/{incident_id}/investigate")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DEPENDENCY_UNAVAILABLE"
    assert response.json()["error"]["request_id"] == "request-fixed"
    assert response.headers["X-Request-ID"] == response.json()["error"]["request_id"]
    stored = repository.get(incident_id)
    assert stored.workflow.current_state is IncidentState.DRAFT
    assert stored.report is None


def test_provider_output_mismatch_has_safe_stable_api_error(api_context):
    client, service, repository = api_context
    draft = service.create_draft(
        CreateInvestigation(title="Protected title", target_asset_id="asset:target")
    )
    service.evidence_provider = ReportProvider(
        build_report(
            incident_id="provider-secret-incident",
            target_asset_id="asset:provider-secret-target",
            title="provider-secret-title",
        )
    )
    response = client.post(
        f"/api/v1/investigations/{draft.incident_id}/investigate",
        headers={"X-Request-ID": "mismatch-request"},
    )
    assert response.status_code == 502
    assert response.json() == {
        "error": {
            "code": "PROVIDER_OUTPUT_MISMATCH",
            "message": (
                "The investigation provider returned a report that does not match the request."
            ),
            "retryable": False,
            "request_id": "mismatch-request",
            "details": {},
        }
    }
    assert "provider-secret" not in response.text
    assert repository.get(draft.incident_id) == draft


def test_public_transition_shortcuts_are_rejected(api_context):
    client, _, _ = api_context
    incident_id = _create(client).json()["incident_id"]
    calls = (
        (f"/api/v1/investigations/{incident_id}/submit-for-approval", {"actor": "a"}),
        (
            f"/api/v1/investigations/{incident_id}/approve",
            {"actor": "a", "reason": "r", "payload_binding_id": "digest"},
        ),
        (
            f"/api/v1/investigations/{incident_id}/retry",
            {
                "actor": "a",
                "reason": "r",
                "approval_remains_valid": False,
                "payload_binding_unchanged": False,
            },
        ),
        (f"/api/v1/investigations/{incident_id}/resolve", {"actor": "a"}),
    )
    for path, body in calls:
        response = client.post(path, json=body)
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_prepared_valid_application_states_are_exposed(api_context):
    client, service, repository = api_context
    record = service.create_draft(
        CreateInvestigation(title="Prepared", target_asset_id="asset")
    )
    investigated = record.model_copy(
        update={
            "workflow": record.workflow.transition(
                IncidentState.INVESTIGATED,
                actor="test-provider",
                occurred_at=service.clock.now(),
            )
        }
    )
    repository.save(investigated, expected_revision=record.revision)
    awaiting = client.post(
        f"/api/v1/investigations/{record.incident_id}/submit-for-approval",
        json={"actor": "coordinator"},
    )
    approved = client.post(
        f"/api/v1/investigations/{record.incident_id}/approve",
        json={"actor": "reviewer", "reason": "reviewed", "payload_binding_id": "sha256:x"},
    )
    assert awaiting.json()["state"] == "AWAITING_APPROVAL"
    assert approved.json()["state"] == "APPROVED"
    assert len(approved.json()["history"]) == 3


def test_resolve_succeeds_only_for_test_prepared_recorded_state(api_context):
    client, service, repository = api_context
    record = service.create_draft(
        CreateInvestigation(title="Prepared", target_asset_id="asset")
    )
    workflow = record.workflow
    for state in (
        IncidentState.INVESTIGATED,
        IncidentState.AWAITING_APPROVAL,
        IncidentState.APPROVED,
        IncidentState.WRITEBACK_PENDING,
        IncidentState.RECORDED,
    ):
        workflow = workflow.transition(
            state,
            actor="test",
            occurred_at=service.clock.now(),
            approval_reason="approved" if state is IncidentState.APPROVED else None,
        )
    repository.save(
        record.model_copy(update={"workflow": workflow}),
        expected_revision=record.revision,
    )
    response = client.post(
        f"/api/v1/investigations/{record.incident_id}/resolve",
        json={"actor": "resolver"},
    )
    assert response.status_code == 200
    assert response.json()["state"] == "RESOLVED"


def test_response_enum_and_utc_serialization_are_stable(api_context):
    client, _, _ = api_context
    first = _create(client).json()
    assert first["state"] == "DRAFT"
    assert first["created_at"].endswith("Z")
    retrieved = client.get(f"/api/v1/investigations/{first['incident_id']}").json()
    assert retrieved == first
