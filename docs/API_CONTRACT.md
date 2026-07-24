# API Contract

Sprint 6 exposes a local development API at `http://127.0.0.1:8000` by default.
It is an application boundary, not a claim that DataHub-backed investigation is
available.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Application process health only |
| GET | `/health/readiness` | Explicit component readiness |
| POST | `/api/v1/investigations` | Create an empty `DRAFT` request |
| GET | `/api/v1/investigations` | Deterministic bounded listing |
| GET | `/api/v1/investigations/{incident_id}` | Retrieve stored state |
| POST | `/api/v1/investigations/{incident_id}/investigate` | Invoke the evidence-provider boundary |
| POST | `/api/v1/investigations/{incident_id}/submit-for-approval` | Enforce investigated-state review |
| POST | `/api/v1/investigations/{incident_id}/approve` | Record explicit approval and payload binding |
| POST | `/api/v1/investigations/{incident_id}/retry` | Invoke stage-aware domain retry |
| POST | `/api/v1/investigations/{incident_id}/resolve` | Resolve only from `RECORDED` |

The default evidence provider is unconfigured. Investigation returns
`DEPENDENCY_UNAVAILABLE`, leaves the incident in `DRAFT`, and stores no invented
evidence or conclusions.

List pagination uses `offset >= 0` and `1 <= limit <= 100`, with a default limit
of 20. Items and total come from one atomic repository snapshot, so concurrent
draft creation cannot produce internally inconsistent pagination metadata.
Responses serialize enums as stable strings and timestamps as UTC. Unknown
request fields are rejected.

Every response includes `X-Request-ID`. A valid caller-supplied identifier is
preserved; otherwise one identifier is generated for the request. Error
envelopes use exactly the same value as the response header, including
validation, known application, not-found, and unexpected internal errors.

Investigation is accepted only from `DRAFT`; this state is checked before the
evidence provider is invoked. Investigation responses include a repository
revision. State-changing requests use that revision internally for atomic
compare-and-swap persistence, and stale updates return retryable
`INCIDENT_CONFLICT`.

A provider report is persisted only after semantic ownership validation.
Mismatched incident ID, target identifier, investigated status, protected
title, or applicable issue category returns `PROVIDER_OUTPUT_MISMATCH`. The
draft, audit history, report field, and revision remain unchanged.

Readiness reports application, repository, evidence-provider, DataHub, MCP, and
write-back states separately. Provider readiness is injected capability data
and is inspected without network calls. Full readiness remains false while
Sprint 6 write-back is disabled, even if a test provider reports available
DataHub and MCP reads.

## Operational boundary

Request bodies are expected to remain small: titles are limited to 200
characters, target identifiers to 500, descriptions to 4,000, and other
command strings are bounded. Infrastructure-level maximum request-body limits
remain a deployment concern for a later hardened runtime phase.

No CORS policy is enabled, authentication is not implemented or claimed, debug
mode is disabled, and the development command binds only to `127.0.0.1` by
default.
