# Human Approval State Machine

## Normal flow

```text
DRAFT
  → INVESTIGATED
  → AWAITING_APPROVAL
  → APPROVED
  → WRITEBACK_PENDING
  → RECORDED
  → RESOLVED
```

Each transition records the prior and next state, actor, and timezone-aware UTC
timestamp. Entering `APPROVED` requires an approval reason. Entering `FAILED`
requires a failure reason. Timestamps must be monotonic.

The state machine and its transition tuple are immutable. Calling
`transition()` returns a new state-machine value and leaves the prior value
unchanged. Invalid skips and transitions after `RESOLVED` are rejected.
Direct creation is limited to `DRAFT` with empty history. Restoring any later
state requires a contiguous, valid, monotonic history beginning at `DRAFT`,
including required approval and failure reasons, whose final state equals
`current_state`.

## Failure and retry

`FAILED` is reachable from every non-terminal normal state when a reason is
recorded. The immutable transition into failure retains the failed stage,
failure reason, actor, and failure timestamp. These values are exposed as the
machine's current failure context.

```text
FAILED → the exact stage recorded as failed_from_state
```

Retry is available only through the explicit `retry()` operation; generic
transitions out of `FAILED` are rejected. A draft failure therefore returns
only to `DRAFT`, an investigation failure only to `INVESTIGATED`, and an
approval-review failure only to `AWAITING_APPROVAL`. Failures from `APPROVED`,
`WRITEBACK_PENDING`, or `RECORDED` can return to their exact origin only when
the caller explicitly supplies both `approval_remains_valid=true` and
`payload_binding_unchanged=true`. If either confirmation is false or absent,
retry is rejected before a transition is constructed. Before `APPROVED`, both
confirmations must remain false; supplying either as true is likewise rejected
with the state machine's domain transition error. No retry may advance beyond
the failed stage.

Restoration validates the complete path from `DRAFT`, failure origin, explicit
retry marker, retry destination, both post-approval confirmation markers where
applicable, required reasons and actors, monotonic UTC timestamps, and final
current state.
Persistence, idempotency, mutation, and read-back remain future work subject to
verified DataHub capabilities.
