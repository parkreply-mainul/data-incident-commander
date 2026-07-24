from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest

from data_incident_commander.application.commands import CreateInvestigation
from data_incident_commander.application.commands import ApprovalCommand
from data_incident_commander.application.errors import (
    ConcurrentUpdateConflict,
    IncidentConflict,
)
from data_incident_commander.application.services import (
    InvestigationService,
    UnconfiguredEvidenceProvider,
)
from data_incident_commander.domain.models import IncidentState
from data_incident_commander.repositories.memory import InMemoryIncidentRepository

from .conftest import FixedIds, SteppingClock, build_service


def test_repository_create_get_save_exists_and_list():
    service, repository = build_service("b", "a")
    first = service.create_draft(CreateInvestigation(title="First", target_asset_id="asset:1"))
    second = service.create_draft(CreateInvestigation(title="Second", target_asset_id="asset:2"))
    assert repository.exists("b")
    assert repository.get("b") == first
    updated = first.model_copy(update={"title": "Updated"})
    persisted = repository.save(updated, expected_revision=first.revision)
    assert persisted.revision == 2
    assert repository.get("b").title == "Updated"
    assert repository.list(offset=0, limit=10) == (persisted, second)


def test_repository_rejects_duplicates_and_bounds_list():
    service, repository = build_service("same")
    record = service.create_draft(CreateInvestigation(title="One", target_asset_id="asset:1"))
    with pytest.raises(IncidentConflict):
        repository.create(record)
    assert repository.list(offset=1, limit=10) == ()


def test_atomic_page_empty_single_and_multiple_pages():
    service, repository = build_service("a", "b", "c")
    assert repository.page(offset=0, limit=10).model_dump() == {
        "items": (),
        "total": 0,
        "offset": 0,
        "limit": 10,
    }
    first = service.create_draft(
        CreateInvestigation(title="First", target_asset_id="asset:1")
    )
    single = repository.page(offset=0, limit=10)
    assert single.items == (first,)
    assert single.total == 1

    second = service.create_draft(
        CreateInvestigation(title="Second", target_asset_id="asset:2")
    )
    third = service.create_draft(
        CreateInvestigation(title="Third", target_asset_id="asset:3")
    )
    assert repository.page(offset=0, limit=2).items == (first, second)
    assert repository.page(offset=0, limit=2).total == 3
    assert repository.page(offset=2, limit=2).items == (third,)
    assert repository.page(offset=3, limit=2).items == ()


def test_page_records_are_immutable_and_deterministically_ordered():
    service, repository = build_service("z", "a")
    first = service.create_draft(
        CreateInvestigation(title="First", target_asset_id="asset:1")
    )
    second = service.create_draft(
        CreateInvestigation(title="Second", target_asset_id="asset:2")
    )
    page = repository.page(offset=0, limit=10)
    assert page.items == (first, second)
    with pytest.raises(Exception):
        page.items[0].title = "Changed"


class PausedPageRepository(InMemoryIncidentRepository):
    def __init__(self) -> None:
        super().__init__()
        self.snapshot_started = Event()
        self.release_snapshot = Event()

    def page(self, *, offset, limit):
        with self._lock:
            self.snapshot_started.set()
            assert self.release_snapshot.wait(timeout=2)
            return super().page(offset=offset, limit=limit)


def test_concurrent_create_cannot_split_page_items_from_total():
    repository = PausedPageRepository()
    service = InvestigationService(
        repository,
        UnconfiguredEvidenceProvider(),
        id_provider=FixedIds("first", "second"),
        clock=SteppingClock(),
    )
    first = service.create_draft(
        CreateInvestigation(title="First", target_asset_id="asset:1")
    )
    create_attempted = Event()

    def create_second():
        create_attempted.set()
        return service.create_draft(
            CreateInvestigation(title="Second", target_asset_id="asset:2")
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        page_future = pool.submit(service.list, offset=0, limit=10)
        assert repository.snapshot_started.wait(timeout=2)
        create_future = pool.submit(create_second)
        assert create_attempted.wait(timeout=2)
        repository.release_snapshot.set()
        page = page_future.result(timeout=2)
        second = create_future.result(timeout=2)

    assert page.items == (first,)
    assert page.total == 1
    assert repository.page(offset=0, limit=10).items == (first, second)
    assert repository.count() == 2


def test_application_service_uses_atomic_page_operation():
    class PageOnlyRepository(InMemoryIncidentRepository):
        page_called = False

        def page(self, *, offset, limit):
            self.page_called = True
            return super().page(offset=offset, limit=limit)

        def list(self, *, offset, limit):
            raise AssertionError("service must not call list")

        def count(self):
            raise AssertionError("service must not call count")

    repository = PageOnlyRepository()
    service = InvestigationService(
        repository,
        UnconfiguredEvidenceProvider(),
        id_provider=FixedIds(),
        clock=SteppingClock(),
    )
    page = service.list(offset=0, limit=20)
    assert repository.page_called is True
    assert page.total == 0


def test_repository_returns_immutable_records():
    service, repository = build_service("one")
    record = service.create_draft(CreateInvestigation(title="One", target_asset_id="asset:1"))
    with pytest.raises(Exception):
        repository.get(record.incident_id).title = "Changed"


def test_repository_basic_concurrent_creation():
    service, repository = build_service(*(f"id-{index}" for index in range(20)))
    commands = tuple(
        CreateInvestigation(title=f"Incident {index}", target_asset_id=f"asset:{index}")
        for index in range(20)
    )
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = tuple(pool.map(service.create_draft, commands))
    assert len(records) == 20
    assert repository.count() == 20
    assert len({record.incident_id for record in records}) == 20


def test_reset_is_explicit_and_test_scoped():
    service, repository = build_service("one")
    service.create_draft(CreateInvestigation(title="One", target_asset_id="asset:1"))
    repository.reset_for_tests()
    assert repository.count() == 0


def test_stale_save_is_rejected_without_changing_record():
    service, repository = build_service("one")
    original = service.create_draft(
        CreateInvestigation(title="One", target_asset_id="asset:1")
    )
    first = repository.save(
        original.model_copy(update={"title": "First update"}),
        expected_revision=original.revision,
    )
    with pytest.raises(ConcurrentUpdateConflict):
        repository.save(
            original.model_copy(update={"title": "Stale update"}),
            expected_revision=original.revision,
        )
    assert repository.get(original.incident_id) == first
    assert first.revision == original.revision + 1


class BarrierGetRepository(InMemoryIncidentRepository):
    def __init__(self) -> None:
        super().__init__()
        self.barrier = Barrier(2)
        self.synchronize_get = False

    def get(self, incident_id):
        record = super().get(incident_id)
        if self.synchronize_get:
            self.barrier.wait(timeout=2)
        return record


def test_two_concurrent_approvals_cannot_both_persist():
    repository = BarrierGetRepository()
    service = InvestigationService(
        repository,
        UnconfiguredEvidenceProvider(),
        id_provider=FixedIds("incident"),
        clock=SteppingClock(),
    )
    draft = service.create_draft(
        CreateInvestigation(title="One", target_asset_id="asset:1")
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
    repository.synchronize_get = True

    def approve(actor):
        return service.approve(
            draft.incident_id,
            ApprovalCommand(
                actor=actor,
                reason=f"approved by {actor}",
                payload_binding_id="sha256:same",
            ),
        )

    successes = []
    conflicts = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = (pool.submit(approve, "actor-a"), pool.submit(approve, "actor-b"))
        for future in futures:
            try:
                successes.append(future.result())
            except ConcurrentUpdateConflict as error:
                conflicts.append(error)

    assert len(successes) == 1
    assert len(conflicts) == 1
    repository.synchronize_get = False
    current = repository.get(draft.incident_id)
    assert current.revision == awaiting.revision + 1
    assert len(current.workflow.history) == len(awaiting.workflow.history) + 1
    assert current.workflow.history[-1].actor in {"actor-a", "actor-b"}
