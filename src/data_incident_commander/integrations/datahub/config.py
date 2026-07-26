"""Strict, side-effect-free DataHub MCP configuration."""

from __future__ import annotations

import ipaddress
import os
import re
from pathlib import PurePath
from typing import Literal, Mapping
from urllib.parse import ParseResult, urlparse

from pydantic import Field, field_validator, model_validator

from data_incident_commander.domain.base import StrictModel


_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?$")
_RFC1918_NETWORKS = tuple(
    ipaddress.ip_network(value)
    for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
_IPV6_ULA = ipaddress.ip_network("fc00::/7")
_LOCAL_GMS_HOSTNAMES = frozenset({"localhost", "datahub-gms", "datahub"})
VERIFIED_MCP_SERVER_VERSION = "0.6.0"
MCP_SERVER_PACKAGE = "mcp-server-datahub"


def _private_or_loopback(host: str) -> bool:
    if host.lower() in _LOCAL_GMS_HOSTNAMES:
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    if address.is_loopback:
        return True
    if isinstance(address, ipaddress.IPv4Address):
        return any(
            address in network
            and address not in {network.network_address, network.broadcast_address}
            for network in _RFC1918_NETWORKS
        )
    return address in _IPV6_ULA


def _loopback_endpoint_host(host: str) -> bool:
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _parse_and_validate_http_url(value: str, field_name: str) -> ParseResult:
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        raise ValueError(f"{field_name} contains invalid URL or port syntax") from None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{field_name} must be an absolute HTTP(S) URL")
    authority = parsed.netloc.rsplit("@", 1)[-1]
    if authority.endswith(":") and port is None:
        raise ValueError(f"{field_name} contains an empty explicit port")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError(f"{field_name} port must be between 1 and 65535")
    return parsed


class DataHubMcpConfig(StrictModel):
    model_config = {
        **StrictModel.model_config,
        "hide_input_in_errors": True,
    }

    gms_url: str
    token_env_var: str = "DATAHUB_GMS_TOKEN"
    mode: Literal["stdio", "endpoint"] = "stdio"
    mcp_command: tuple[str, ...] = ("uvx",)
    mcp_endpoint: str | None = None
    mcp_server_version: str
    request_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    maximum_lineage_depth: int = Field(default=3, ge=1, le=20)
    maximum_lineage_nodes: int = Field(default=100, ge=1, le=10_000)
    mutation_enabled: bool = False
    documents_enabled: bool = False
    user_tools_enabled: bool = False
    environment_name: str = Field(min_length=1, max_length=64)

    @field_validator("gms_url")
    @classmethod
    def validate_private_gms_url(cls, value: str) -> str:
        parsed = _parse_and_validate_http_url(value, "gms_url")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("gms_url must not contain credentials, query, or fragment")
        if not _private_or_loopback(parsed.hostname):
            raise ValueError(
                "gms_url must use loopback, an approved local hostname, "
                "RFC1918 IPv4, or IPv6 ULA"
            )
        return value.rstrip("/")

    @field_validator("token_env_var")
    @classmethod
    def validate_token_reference(cls, value: str) -> str:
        if not _ENV_NAME.fullmatch(value):
            raise ValueError("token_env_var must be an uppercase environment variable name")
        return value

    @field_validator("mcp_server_version")
    @classmethod
    def validate_exact_version(cls, value: str) -> str:
        if not _VERSION.fullmatch(value):
            raise ValueError("mcp_server_version must be an exact semantic version")
        return value

    @field_validator("mcp_command")
    @classmethod
    def validate_command(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) != 1 or not value[0].strip():
            raise ValueError("mcp_command must contain exactly one executable")
        if PurePath(value[0]).name != "uvx":
            raise ValueError("only the officially documented uvx executable is accepted")
        return value

    @model_validator(mode="after")
    def validate_mode_and_mutation(self) -> "DataHubMcpConfig":
        if self.mode == "stdio" and self.mcp_endpoint is not None:
            raise ValueError("mcp_endpoint is only valid in endpoint mode")
        if self.mode == "endpoint":
            if self.mcp_endpoint is None:
                raise ValueError("endpoint mode requires mcp_endpoint")
            parsed = _parse_and_validate_http_url(self.mcp_endpoint, "mcp_endpoint")
            if parsed.scheme != "https" and not _loopback_endpoint_host(
                parsed.hostname
            ):
                raise ValueError("remote MCP endpoints must use HTTPS")
            if parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise ValueError("mcp_endpoint must not contain credentials")
        if self.mutation_enabled:
            raise ValueError("mutation cannot be enabled by runtime configuration in Sprint 8A")
        return self

    def token_value(self, environment: Mapping[str, str] | None = None) -> str | None:
        """Resolve the referenced secret without storing it in the model."""

        source = os.environ if environment is None else environment
        return source.get(self.token_env_var)

    @property
    def stdio_command(self) -> tuple[str, ...]:
        """Return the exact, immutable server invocation without secret values."""

        return (
            self.mcp_command[0],
            f"{MCP_SERVER_PACKAGE}=={self.mcp_server_version}",
            "--transport",
            "stdio",
        )

    def public_configuration(self) -> dict[str, object]:
        return {
            "gms_host_class": "private",
            "token_reference": self.token_env_var,
            "mode": self.mode,
            "mcp_server_version": self.mcp_server_version,
            "request_timeout_seconds": self.request_timeout_seconds,
            "maximum_lineage_depth": self.maximum_lineage_depth,
            "maximum_lineage_nodes": self.maximum_lineage_nodes,
            "mutation_enabled": False,
            "documents_enabled": self.documents_enabled,
            "user_tools_enabled": self.user_tools_enabled,
            "environment_name": self.environment_name,
        }
