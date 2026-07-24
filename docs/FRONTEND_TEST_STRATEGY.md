# Frontend Test Strategy

## Automated Sprint 7 coverage

Vitest, jsdom, and Testing Library exercise behavior from the user's
perspective. Tests cover:

- shell navigation, active route, anchors, and keyboard activation;
- readiness with default, mixed, configured/unavailable, disabled, loading,
  refresh, and API failure states;
- draft form labels, required/format validation, focus, successful creation,
  returned ID/revision path, backend validation/conflict, request IDs, and
  absence of fabricated evidence;
- investigation list loading, empty, populated, deterministic server order,
  pagination, error, and retry;
- detail data, state/revision/timestamps, audit history, disabled result
  surfaces, dependency-unavailable investigation, retained draft state, and
  not found;
- plain and percent-encoded detail routes, malformed escape rejection without
  a render crash or API call;
- conflict/invalid-state refresh, refreshed revision/state display, neutral
  refresh-failure messaging, request-ID retention, and recovered controls;
- overlapping route loads in both completion orders, superseded rejection,
  current-request network failure, unmount cancellation, and manual-refresh
  ownership of data, error, loading, and live-status output;
- network, validation, dependency, conflict, and internal client errors;
- backend error-envelope and request-ID parsing;
- representative backend contract fixtures, UTC display, and unknown status;
  and
- semantic labels, focus, live status, table headings, and status text beyond
  color.

`make frontend-test` installs exactly the lockfile graph with `npm ci` and runs
the suite once, without watch mode. `make frontend-build` runs TypeScript
project checking followed by a production Vite build.

## Integration smoke

The bounded local smoke starts FastAPI and Vite on loopback, requests the
dashboard asset, verifies not-ready readiness through the Vite proxy, creates a
draft, retrieves it, invokes Investigate, confirms
`DEPENDENCY_UNAVAILABLE`, re-reads `DRAFT`, and stops both processes. It proves
the current honest boundary, not DataHub/MCP connectivity.

## Deferred coverage

Browser-driven visual regression, multiple desktop viewport screenshots,
automated accessibility scanning, and real graph interaction belong to later
phases. Full E2E investigation tests remain blocked until verified DataHub and
MCP adapters exist. Those tests must not replace live evidence with fixtures.
