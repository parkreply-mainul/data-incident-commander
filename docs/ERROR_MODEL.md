# API Error Model

All handled errors use one envelope:

```json
{
  "error": {
    "code": "INCIDENT_NOT_FOUND",
    "message": "The requested incident does not exist.",
    "retryable": false,
    "request_id": "correlation-id",
    "details": {}
  }
}
```

Supported categories are `VALIDATION_ERROR`, `INCIDENT_NOT_FOUND`,
`INVALID_STATE_TRANSITION`, `DEPENDENCY_UNAVAILABLE`, `CONFLICT`,
`INCIDENT_CONFLICT`, `PROVIDER_OUTPUT_MISMATCH`, and `INTERNAL_ERROR`.
`INCIDENT_CONFLICT` represents an optimistic-concurrency failure, is retryable,
and instructs the caller to re-read before deciding whether to resubmit.
`PROVIDER_OUTPUT_MISMATCH` is non-retryable and reports only that normalized
provider output did not belong to the request; it does not echo the provider
payload or mismatch values. Neither error exposes repository, adapter, or lock
implementation details.

Validation responses do not expose raw Pydantic diagnostics. Unexpected
exceptions become a generic internal error without stack traces, filesystem
paths, environment values, credentials, or raw exception text. A caller may
supply `X-Request-ID`; otherwise the application generates one. The identifier
is stored once in request context and returned in the envelope and response
header. The shared error-response builder assigns the header directly, so even
an unexpected exception outside the middleware's normal return path preserves
the same correlation ID.
