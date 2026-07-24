# Frontend Architecture

## Implemented boundary

Sprint 7 adds a desktop-first React 19, TypeScript 7, and Vite 8 client under
`frontend/`. It consumes only the committed FastAPI contract. The UI has no
DataHub, MCP, LLM, persistence, write-back, graph, or router dependency.

The installation host reported Node.js 25.9.0 and npm 11.12.1. The selected
Vite 8.1.5 engine range accepts Node 20.19+ or 22.12+, so the observed runtime
satisfies it. Direct versions are exact in `package.json`; `package-lock.json`
pins the complete installation graph for `npm ci`.

The source is divided into:

- `api/`: typed fetch boundary and normalized public-safe errors;
- `types/`: manual mirrors of the current transport contract;
- `pages/`: dashboard, investigations, draft creation, detail, status, and
  not-found views;
- `components/`: reusable shell, tables, readiness, feedback, and unavailable
  capability surfaces;
- `hooks/`: route and async lifecycle behavior;
- `utils/`: deterministic display formatting;
- `styles/`: tokens and responsive presentation; and
- `test/`: component, client, contract-fixture, error, and accessibility tests.

The small route set uses the browser History API. This avoids a routing
dependency while preserving real anchors, back/forward navigation, deep links
through Vite fallback, and deterministic page selection.

## Data flow

```text
React page
  → typed API client
  → Vite local proxy (/health and /api)
  → FastAPI transport boundary
  → application services
  → in-memory repository
```

No network call occurs during module import. Pages own loading, empty, error,
and retry state. Successful draft creation navigates to the stored detail
view. Investigate calls the real endpoint; the current 503 response is shown
without changing the displayed draft or inventing evidence.

## Pages

| Route | Current capability |
| --- | --- |
| `/` | Actual readiness summary, draft count, recent investigations |
| `/investigations` | Bounded deterministic pagination and retry |
| `/investigations/new` | Strictly supported draft fields and inline validation |
| `/investigations/:id` | Stored draft, revision, timestamps, audit, real investigate action |
| `/status` | Component-level readiness with manual refresh |

## State and truth boundaries

Future result areas are visible as disabled, explanatory panels so the product
information architecture can be assessed without implying functionality.
There are no fabricated lineage edges, evidence, severity, confidence, owners,
remediation, memory, or write receipts. Readiness data is cleared while a
refresh is pending and on failure so stale data is never labeled live.

Manual frontend types must be kept aligned with FastAPI until a later,
deliberately selected OpenAPI generation workflow replaces them.

## Responsive scope

The primary grid targets 1440, 1280, and 1024 pixel desktop/laptop widths. At
narrow widths, navigation becomes a horizontal scrollable region and detail
grids collapse without page-level horizontal overflow. A phone-optimized
application is outside Sprint 7.
