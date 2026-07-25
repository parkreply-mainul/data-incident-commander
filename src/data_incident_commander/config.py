"""Minimal environment-backed API settings."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str = "Data Incident Commander"
    service_version: str = "0.2.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    datahub_gms_url: str | None = None
    datahub_token_env: str = "DATAHUB_GMS_TOKEN"
    datahub_mutation_enabled: bool = False
    datahub_writeback_tag_urn: str = "urn:li:tag:dic-incident-recorded"

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            service_name=os.getenv("DIC_SERVICE_NAME", cls.service_name),
            service_version=os.getenv("DIC_SERVICE_VERSION", cls.service_version),
            environment=os.getenv("DIC_ENVIRONMENT", cls.environment),
            host=os.getenv("DIC_HOST", cls.host),
            port=int(os.getenv("DIC_PORT", str(cls.port))),
            log_level=os.getenv("DIC_LOG_LEVEL", cls.log_level),
            datahub_gms_url=os.getenv("DIC_GMS_URL") or None,
            datahub_token_env=os.getenv("DIC_GMS_TOKEN_ENV", cls.datahub_token_env),
            datahub_mutation_enabled=os.getenv("DIC_DATAHUB_MUTATION_ENABLED", "false").lower()
            == "true",
            datahub_writeback_tag_urn=os.getenv(
                "DIC_DATAHUB_WRITEBACK_TAG_URN", cls.datahub_writeback_tag_urn
            ),
        )
