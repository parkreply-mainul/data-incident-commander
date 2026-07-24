# DataHub MCP Adapter Architecture

## Status

Sprint 8A implements a library-neutral application boundary, not a live
integration. No MCP package is installed, no MCP session has run, and no
DataHub response schema is assumed.

```text
InvestigationService
  → EvidenceProvider protocol
  → DataHubMcpEvidenceProvider
  → McpClientProtocol (future concrete client)
  → runtime-observed tool inventory
  → verified adapter DTOs
  → strict normalizers
  → framework-independent domain contracts
```

The default application provider remains `UnconfiguredEvidenceProvider`.
`DataHubMcpEvidenceProvider` is injectable in tests and future composition but
is not selected by production defaults.

## Configuration boundary

`DataHubMcpConfig` stores a token environment-variable *name*, never a token.
The canonical public configuration is
`DATAHUB_GMS_TOKEN_ENV=DATAHUB_GMS_TOKEN` with a blank
`DATAHUB_GMS_TOKEN=` placeholder; the older ambiguous `DATAHUB_TOKEN` name is
not used.
It accepts only loopback, the documented local names `localhost`,
`datahub-gms`, and `datahub`, RFC1918 IPv4 addresses excluding the enclosing
network/broadcast boundaries, and IPv6 ULA addresses. Link-local, metadata,
carrier-grade NAT, multicast, unspecified, reserved/documentation, public IP,
and public DNS hosts are rejected. Exact semantic MCP version pins, bounded
timeouts and lineage limits, and stdio or HTTPS endpoint mode remain required.
Configuration errors hide input values, and loading performs no network or
process action.

Self-hosted stdio execution is documented. Endpoint mode is an adapter
assumption reserved for future verification; it does not assert that the
selected self-hosted release exposes HTTP transport or a port.

Mutation is always false in Sprint 8A and cannot be enabled through model input.
Document and user tool flags represent configuration intent only; they do not
prove runtime capability.

MCP endpoint mode permits plain HTTP only for true loopback hosts:
`localhost`, any IPv4 address in `127.0.0.0/8`, and IPv6 `::1` (including
bracketed URL form). Every non-loopback endpoint requires HTTPS. This endpoint
transport rule is separate from the stricter GMS destination allowlist.
Both GMS and MCP URLs fail configuration validation on nonnumeric, signed,
whitespace, empty, zero, out-of-range, or malformed IPv6 ports. An omitted port
or an explicit port from 1 through 65535 is accepted.

## Client boundary

`McpClientProtocol` defines initialize, list-tools, invoke, readiness, and close
operations without selecting an MCP Python library. `McpToolDescriptor` and
`VerifiedToolResult` are adapter-level contracts; they do not claim the real
server returns those shapes. A future concrete client must translate the
observed library/runtime schema into them.

## Fail-closed investigation

The provider distinguishes configuration presence, client/session
availability, required-tool observation, verified adapter-level normalization,
implemented investigation orchestration, and operational availability.
Observed required capabilities are reported as
`capabilities_verified_but_investigation_unimplemented`; they do not make the
provider operational. Sprint 8A therefore always reports `available=false`.
It generates no fixture report, and investigation fails safely because verified
orchestration and raw-result adapters do not exist.

Integration errors that represent dependency availability subclass the
existing application dependency boundary. Authentication, tokens, commands,
raw payloads, and stack traces remain internal.
