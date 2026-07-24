"""Ports required by application services."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import Field

from data_incident_commander.domain.base import StrictModel
from data_incident_commander.domain.models import IncidentReport

from .records import InvestigationPage, InvestigationRecord


class IncidentRepository(Protocol):
    @property
    def ready(self) -> bool: ...

    def create(self, record: InvestigationRecord) -> InvestigationRecord: ...
    def get(self, incident_id: str) -> InvestigationRecord | None: ...
    def list(self, *, offset: int, limit: int) -> tuple[InvestigationRecord, ...]: ...
    def page(self, *, offset: int, limit: int) -> InvestigationPage: ...
    def save(
        self, record: InvestigationRecord, *, expected_revision: int
    ) -> InvestigationRecord: ...
    def exists(self, incident_id: str) -> bool: ...
    def count(self) -> int: ...


class EvidenceProviderReadiness(StrictModel):
    dependency_name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    configured: bool
    available: bool
    supports_datahub: bool
    supports_mcp: bool
    supports_writeback: bool


class EvidenceProvider(Protocol):
    @property
    def readiness(self) -> EvidenceProviderReadiness: ...

    def investigate(self, record: InvestigationRecord) -> IncidentReport: ...


class IncidentIdProvider(Protocol):
    def new_id(self) -> str: ...


class Clock(Protocol):
    def now(self) -> datetime: ...
