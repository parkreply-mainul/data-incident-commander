"""Thread-safe one-process incident repository."""

from __future__ import annotations

from threading import RLock

from data_incident_commander.application.errors import (
    ConcurrentUpdateConflict,
    IncidentConflict,
    IncidentNotFound,
)
from data_incident_commander.application.records import InvestigationPage, InvestigationRecord


class InMemoryIncidentRepository:
    def __init__(self) -> None:
        self._records: dict[str, InvestigationRecord] = {}
        self._lock = RLock()

    @property
    def ready(self) -> bool:
        return True

    def create(self, record: InvestigationRecord) -> InvestigationRecord:
        with self._lock:
            if record.incident_id in self._records:
                raise IncidentConflict("An incident with this identifier already exists.")
            self._records[record.incident_id] = record
            return record

    def get(self, incident_id: str) -> InvestigationRecord | None:
        with self._lock:
            return self._records.get(incident_id)

    def list(self, *, offset: int, limit: int) -> tuple[InvestigationRecord, ...]:
        with self._lock:
            ordered = sorted(
                self._records.values(),
                key=lambda record: (record.created_at, record.incident_id),
            )
            return tuple(ordered[offset : offset + limit])

    def page(self, *, offset: int, limit: int) -> InvestigationPage:
        with self._lock:
            ordered = tuple(
                sorted(
                    self._records.values(),
                    key=lambda record: (record.created_at, record.incident_id),
                )
            )
            return InvestigationPage(
                items=ordered[offset : offset + limit],
                total=len(ordered),
                offset=offset,
                limit=limit,
            )

    def save(
        self,
        record: InvestigationRecord,
        *,
        expected_revision: int,
    ) -> InvestigationRecord:
        with self._lock:
            current = self._records.get(record.incident_id)
            if current is None:
                raise IncidentNotFound("The requested incident does not exist.")
            if current.revision != expected_revision:
                raise ConcurrentUpdateConflict(
                    "The incident changed after it was read."
                )
            persisted = record.model_copy(
                update={"revision": expected_revision + 1}
            )
            self._records[record.incident_id] = persisted
            return persisted

    def exists(self, incident_id: str) -> bool:
        with self._lock:
            return incident_id in self._records

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def reset_for_tests(self) -> None:
        with self._lock:
            self._records.clear()
