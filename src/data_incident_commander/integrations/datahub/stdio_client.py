"""Synchronous, bounded MCP stdio client backed by the official Python SDK."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Mapping
from contextlib import AsyncExitStack
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
from typing import Any

from .client_protocol import McpToolDescriptor, VerifiedToolResult
from .config import DataHubMcpConfig
from .errors import CapabilityDisabled, McpUnavailable, ToolInventoryUnavailable


VERIFIED_TOOL_NAMES = frozenset(
    {
        "search",
        "get_lineage",
        "get_dataset_queries",
        "get_entities",
        "list_schema_fields",
        "get_lineage_paths_between",
        "search_documents",
        "grep_documents",
    }
)
_REQUIRED_SCHEMA_PROPERTIES = {
    "search": frozenset({"query", "num_results", "offset"}),
    "get_entities": frozenset({"urns"}),
    "get_lineage": frozenset(
        {"urn", "upstream", "max_hops", "max_results", "offset"}
    ),
    "get_lineage_paths_between": frozenset(
        {
            "source_urn",
            "target_urn",
            "source_column",
            "target_column",
            "direction",
        }
    ),
}
_REQUIRED_SCHEMA_FIELDS = {
    "search": frozenset(),
    "get_entities": frozenset({"urns"}),
    "get_lineage": frozenset({"urn"}),
    "get_lineage_paths_between": frozenset({"source_urn", "target_urn"}),
}
_EXPECTED_SCHEMA_TYPES = {
    "search": {
        "query": frozenset({"string"}),
        "num_results": frozenset({"integer"}),
        "offset": frozenset({"integer"}),
    },
    "get_entities": {"urns": frozenset({"array", "string"})},
    "get_lineage": {
        "urn": frozenset({"string"}),
        "upstream": frozenset({"boolean"}),
        "max_hops": frozenset({"integer"}),
        "max_results": frozenset({"integer"}),
        "offset": frozenset({"integer"}),
    },
    "get_lineage_paths_between": {
        "source_urn": frozenset({"string"}),
        "target_urn": frozenset({"string"}),
        "source_column": frozenset({"string"}),
        "target_column": frozenset({"string"}),
        "direction": frozenset({"string"}),
    },
}
_EXACT_SCHEMA_PROPERTIES = {
    "get_lineage_paths_between": _REQUIRED_SCHEMA_PROPERTIES[
        "get_lineage_paths_between"
    ],
}
_ENABLED_INVESTIGATION_TOOLS = frozenset(
    {"search", "get_entities", "get_lineage", "get_lineage_paths_between"}
)
_SDK_INHERITED_OPERATIONAL_ENVIRONMENT = frozenset(
    {"HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER"}
)
_CHILD_ENVIRONMENT_ALLOWLIST = _SDK_INHERITED_OPERATIONAL_ENVIRONMENT | frozenset(
    {
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMROOT",
        "TMPDIR",
        "UV_CACHE_DIR",
        "UV_PYTHON",
        "http_proxy",
        "https_proxy",
        "no_proxy",
    }
)


class DataHubMcpStdioClient:
    """Open a fresh SDK session per bounded operation and always close it."""

    def __init__(
        self,
        config: DataHubMcpConfig,
        *,
        environment: Mapping[str, str] | None = None,
        transport_factory: Callable[..., Any] | None = None,
        session_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config
        self._environment = environment
        self._transport_factory = transport_factory
        self._session_factory = session_factory
        self._ready = False
        self._tools: tuple[McpToolDescriptor, ...] = ()
        self._schemas: dict[str, Mapping[str, Any]] = {}

    @property
    def ready(self) -> bool:
        return self._ready

    def _child_environment(self) -> dict[str, str]:
        source = os.environ if self._environment is None else self._environment
        child = {
            name: source[name]
            for name in _CHILD_ENVIRONMENT_ALLOWLIST
            if name in source
        }
        child["DATAHUB_GMS_URL"] = self.config.gms_url
        token = self.config.token_value(source)
        if token:
            child[self.config.token_env_var] = token
        return child

    async def _session(self, operation: Callable[[Any], Any]) -> Any:
        try:
            if self._transport_factory is None or self._session_factory is None:
                from mcp import ClientSession, StdioServerParameters
                from mcp.client.stdio import stdio_client

                transport_factory = stdio_client
                session_factory = ClientSession
                parameters = StdioServerParameters(
                    command=self.config.stdio_command[0],
                    args=list(self.config.stdio_command[1:]),
                    env=self._child_environment(),
                )
            else:
                transport_factory = self._transport_factory
                session_factory = self._session_factory
                parameters = {
                    "command": self.config.stdio_command[0],
                    "args": self.config.stdio_command[1:],
                    "env": self._child_environment(),
                }
            async with AsyncExitStack() as stack:
                transport = transport_factory(
                    parameters,
                    errlog=subprocess.DEVNULL,
                )
                streams = await stack.enter_async_context(transport)
                session = await stack.enter_async_context(session_factory(*streams))
                await session.initialize()
                return await operation(session)
        except (TimeoutError, asyncio.TimeoutError) as error:
            raise McpUnavailable("The DataHub MCP request timed out.") from error
        except (McpUnavailable, ToolInventoryUnavailable):
            raise
        except Exception as error:
            raise McpUnavailable("The DataHub MCP stdio session is unavailable.") from error

    def _run(self, operation: Callable[[Any], Any]) -> Any:
        try:
            return asyncio.run(
                asyncio.wait_for(
                    self._session(operation),
                    timeout=self.config.request_timeout_seconds,
                )
            )
        except (TimeoutError, asyncio.TimeoutError) as error:
            raise McpUnavailable("The DataHub MCP request timed out.") from error
        except RuntimeError as error:
            raise McpUnavailable("The DataHub MCP stdio session could not run.") from error

    @staticmethod
    def _schema(tool: Any) -> Mapping[str, Any]:
        schema = getattr(tool, "inputSchema", None)
        if schema is None and isinstance(tool, Mapping):
            schema = tool.get("inputSchema") or tool.get("input_schema")
        if not isinstance(schema, Mapping):
            raise ToolInventoryUnavailable("An MCP tool has no supported input schema.")
        return schema

    @staticmethod
    def _json_schema_types(value: Mapping[str, Any]) -> frozenset[str]:
        direct = value.get("type")
        if isinstance(direct, str):
            return frozenset({direct})
        if isinstance(direct, list):
            return frozenset(item for item in direct if isinstance(item, str))
        variants = value.get("anyOf") or value.get("oneOf")
        if isinstance(variants, list):
            return frozenset(
                schema_type
                for variant in variants
                if isinstance(variant, Mapping)
                for schema_type in DataHubMcpStdioClient._json_schema_types(variant)
            )
        return frozenset()

    def initialize(self) -> None:
        async def inspect(session: Any) -> tuple[McpToolDescriptor, ...]:
            response = await session.list_tools()
            tools = getattr(response, "tools", response)
            by_name = {
                getattr(tool, "name", None)
                if not isinstance(tool, Mapping)
                else tool.get("name"): tool
                for tool in tools
            }
            if set(by_name) != VERIFIED_TOOL_NAMES:
                raise ToolInventoryUnavailable(
                    "The DataHub MCP tool inventory does not match the verified version."
                )
            descriptors = []
            verified_schemas: dict[str, Mapping[str, Any]] = {}
            for name in sorted(by_name):
                schema = self._schema(by_name[name])
                if schema.get("type") != "object":
                    raise ToolInventoryUnavailable(
                        f"The verified schema for MCP tool {name!r} is incompatible."
                    )
                properties = schema.get("properties")
                if not isinstance(properties, Mapping):
                    raise ToolInventoryUnavailable(
                        f"The verified schema for MCP tool {name!r} is incompatible."
                    )
                required = _REQUIRED_SCHEMA_PROPERTIES.get(name, frozenset())
                if not required.issubset(properties):
                    raise ToolInventoryUnavailable(
                        f"The verified schema for MCP tool {name!r} is incompatible."
                    )
                exact_properties = _EXACT_SCHEMA_PROPERTIES.get(name)
                if (
                    exact_properties is not None
                    and set(properties) != exact_properties
                ):
                    raise ToolInventoryUnavailable(
                        f"The verified schema for MCP tool {name!r} is incompatible."
                    )
                required_fields = schema.get("required", [])
                if not isinstance(required_fields, list) or any(
                    not isinstance(field, str) for field in required_fields
                ):
                    raise ToolInventoryUnavailable(
                        f"The verified schema for MCP tool {name!r} is incompatible."
                    )
                expected_required = _REQUIRED_SCHEMA_FIELDS.get(name)
                if (
                    expected_required is not None
                    and set(required_fields) != expected_required
                ):
                    raise ToolInventoryUnavailable(
                        f"The verified schema for MCP tool {name!r} is incompatible."
                    )
                for field, expected_types in _EXPECTED_SCHEMA_TYPES.get(
                    name, {}
                ).items():
                    property_schema = properties[field]
                    actual_types = (
                        self._json_schema_types(property_schema) - {"null"}
                        if isinstance(property_schema, Mapping)
                        else frozenset()
                    )
                    if actual_types != expected_types:
                        raise ToolInventoryUnavailable(
                            f"The verified schema for MCP tool {name!r} is incompatible."
                        )
                if name == "get_entities":
                    urns_schema = properties["urns"]
                    variants = (
                        urns_schema.get("anyOf") or urns_schema.get("oneOf")
                        if isinstance(urns_schema, Mapping)
                        else None
                    )
                    candidates = (
                        variants
                        if isinstance(variants, list)
                        else [urns_schema]
                    )
                    array_schemas = [
                        candidate
                        for candidate in candidates
                        if isinstance(candidate, Mapping)
                        and candidate.get("type") == "array"
                    ]
                    if len(array_schemas) != 1 or not isinstance(
                        array_schemas[0].get("items"), Mapping
                    ) or array_schemas[0]["items"].get("type") != "string":
                        raise ToolInventoryUnavailable(
                            "The verified schema for MCP tool 'get_entities' is incompatible."
                        )
                canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
                verified_schemas[name] = schema
                descriptors.append(
                    McpToolDescriptor(
                        name=name,
                        schema_fingerprint=hashlib.sha256(
                            canonical.encode()
                        ).hexdigest(),
                        read_only=True,
                    )
                )
            self._schemas = verified_schemas
            return tuple(descriptors)

        self._tools = self._run(inspect)
        self._ready = True

    def list_tools(self) -> tuple[McpToolDescriptor, ...]:
        if not self._ready:
            self.initialize()
        return self._tools

    @staticmethod
    def _payload(result: Any) -> Mapping[str, Any]:
        structured = getattr(result, "structuredContent", None)
        if isinstance(structured, Mapping):
            return structured
        content = getattr(result, "content", None)
        if not isinstance(content, (list, tuple)):
            raise McpUnavailable("The DataHub MCP response was malformed.")
        texts = [
            getattr(item, "text", None)
            for item in content
            if isinstance(getattr(item, "text", None), str)
        ]
        if len(texts) != 1:
            raise McpUnavailable("The DataHub MCP response was malformed.")
        try:
            payload = json.loads(texts[0])
        except (TypeError, json.JSONDecodeError) as error:
            raise McpUnavailable("The DataHub MCP response was malformed.") from error
        if isinstance(payload, list):
            return {"result": payload}
        if not isinstance(payload, Mapping):
            raise McpUnavailable("The DataHub MCP response was malformed.")
        return payload

    def invoke(
        self, tool_name: str, arguments: Mapping[str, Any]
    ) -> VerifiedToolResult:
        if tool_name not in _ENABLED_INVESTIGATION_TOOLS:
            raise CapabilityDisabled(
                "The requested MCP capability is disabled for investigations."
            )
        if not self._ready or tool_name not in {tool.name for tool in self._tools}:
            raise ToolInventoryUnavailable(
                "The requested MCP tool has not been runtime verified."
            )
        expected = _EXPECTED_SCHEMA_TYPES.get(tool_name, {})
        required = _REQUIRED_SCHEMA_FIELDS.get(tool_name, frozenset())
        schema_properties = self._schemas.get(tool_name, {}).get("properties", {})
        if not isinstance(schema_properties, Mapping) or any(
            field not in schema_properties for field in arguments
        ):
            raise ToolInventoryUnavailable(
                "The requested MCP tool arguments do not match the verified schema."
            )
        if not required.issubset(arguments):
            raise ToolInventoryUnavailable(
                "The requested MCP tool arguments do not match the verified schema."
            )
        python_types = {
            "array": (list, tuple),
            "boolean": (bool,),
            "integer": (int,),
            "string": (str,),
        }
        for field, value in arguments.items():
            expected_types = expected.get(field)
            if expected_types is None:
                continue
            accepted = tuple(
                item
                for schema_type in expected_types
                for item in python_types[schema_type]
            )
            if not isinstance(value, accepted) or (
                "integer" in expected_types and isinstance(value, bool)
            ):
                raise ToolInventoryUnavailable(
                    "The requested MCP tool arguments do not match the verified schema."
                )

        async def call(session: Any) -> Mapping[str, Any]:
            result = await session.call_tool(tool_name, dict(arguments))
            if getattr(result, "isError", False):
                raise McpUnavailable("The DataHub MCP tool call failed.")
            return self._payload(result)

        return VerifiedToolResult(
            tool_name=tool_name,
            observed_at=datetime.now(timezone.utc),
            payload=self._run(call),
        )

    def close(self) -> None:
        self._ready = False
        self._tools = ()
        self._schemas = {}
