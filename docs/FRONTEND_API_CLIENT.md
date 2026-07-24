# Frontend API Client

## Configuration

The browser client uses `fetch`. `VITE_API_BASE_URL` optionally supplies an API
base URL and defaults to same-origin. During development, Vite proxies `/api`
and `/health` to `VITE_API_PROXY_TARGET`, defaulting to
`http://127.0.0.1:8000`. These values are endpoints, not secrets.

`VITE_API_TIMEOUT_MS` controls the bounded request timeout and defaults to
10,000 milliseconds. The client does not hard-code a production host.

Read operations accept an `AbortSignal`. The shared asynchronous hook aborts
the prior request on dependency changes, manual refresh, and unmount. A
monotonically increasing request generation additionally guards every data,
error, and loading update, so a client that completes after cancellation still
cannot replace newer route state. Intentional cancellation is distinct from a
real timeout or network failure and is never rendered as an error.

## Error contract

`ApiClientError` normalizes:

- `NETWORK_ERROR`;
- backend `VALIDATION_ERROR`;
- `INCIDENT_NOT_FOUND`;
- `DEPENDENCY_UNAVAILABLE`;
- `INCIDENT_CONFLICT`; and
- `INTERNAL_ERROR`.

JSON is checked defensively. HTML, malformed JSON, and unrecognized error bodies
become public-safe failures rather than raw responses. Stack traces and
internal exception values are not rendered.

The client preserves correlation in this order: backend error-envelope
`request_id`, then `X-Request-ID`. Callers receive the normalized ID for
support display. Request IDs are never treated as authorization credentials.

After `INCIDENT_CONFLICT` or `INVALID_STATE_TRANSITION`, the detail page
performs one guarded record refresh before describing state or revision. The
original action error and request ID remain visible. If the refresh fails, the
UI reports that current state is unconfirmed and offers a separate refresh;
only `DEPENDENCY_UNAVAILABLE` on a loaded `DRAFT` carries the backend-guaranteed
unchanged-draft message.

## Contract ownership

`frontend/src/types/api.ts` manually mirrors only current FastAPI models:
health/readiness, draft request, stored incident, page, and stable error
envelope. Unknown component status values remain displayable as neutral
`unknown` states. OpenAPI generation is intentionally deferred; any backend
contract change must update types, fixtures, and client tests together.

## Safety behavior

The client sends only supported draft fields, uses JSON serialization, applies
no arbitrary object deserialization, and makes no request on import. It never
converts a backend failure into a successful result. An investigate failure is
returned to the detail page with its request ID while the page retains the
last real stored `DRAFT` record.

Incident path segments are decoded inside a non-throwing route boundary.
Malformed percent encoding renders the standard not-found view within the
application shell and causes no API request.
