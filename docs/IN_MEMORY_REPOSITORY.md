# In-Memory Repository

Sprint 6 uses a one-process `InMemoryIncidentRepository` behind the
`IncidentRepository` protocol.

Properties:

- lock-protected create, get, list, save, exists, and count operations;
- immutable stored `InvestigationRecord` values;
- deterministic revision `1` on creation;
- atomic compare-and-swap saves requiring the caller's expected revision;
- exactly one revision increment for each successful save;
- stale saves rejected without changing the stored record or silently retrying;
- duplicate identifiers rejected as conflicts;
- deterministic ordering by creation timestamp and incident identifier;
- immutable pagination results containing items, total, offset, and limit;
- one lock-held pagination snapshot that orders, counts, and slices the same
  record set, preventing concurrent creation from splitting items and total;
- no global dictionary exposed to callers;
- explicit `reset_for_tests()` utility only.

Data is intentionally lost when the process stops. This implementation is for
local development and deterministic tests, not multi-process or production
persistence. A future repository can replace it without changing domain
contracts or HTTP transport models.
