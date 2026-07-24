from __future__ import annotations

import asyncio

import httpx
import pytest

from data_incident_commander.api.app import create_app
from data_incident_commander.config import Settings

from tests.application.conftest import build_service


class SyncASGIClient:
    """Small synchronous facade over HTTPX's in-process async ASGI transport."""

    def __init__(self, app) -> None:
        self.app = app

    def request(self, method: str, path: str, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=self.app, raise_app_exceptions=False)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)


@pytest.fixture
def api_context():
    service, repository = build_service(*(f"incident-{index}" for index in range(20)))
    app = create_app(
        service=service,
        settings=Settings(service_version="test"),
        request_id_provider=lambda: "request-fixed",
    )
    yield SyncASGIClient(app), service, repository
