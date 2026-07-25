# Screenshot Plan

Capture only these six judge-facing images at a consistent desktop viewport.
Use the NYC Taxi incident and hide browser chrome, tokens, hostnames, request
IDs, and unrelated records.

## 1. Incident report

**Frame:** Investigation header, `INVESTIGATED` state, NYC Taxi target URN, and
timeline.

**Why it matters:** Establishes the concrete incident and shows that DIC
maintains a controlled, auditable workflow rather than producing a chat answer.

## 2. Evidence ledger

**Frame:** Records for asset metadata, ownership, stale freshness, quality, and
lineage with their DataHub source operations.

**Why it matters:** This is the strongest proof that conclusions are grounded
in typed DataHub evidence.

## 3. Lineage and blast radius

**Frame:** Raw trips → daily metrics → operations dashboard, with direct and
transitive affected counts.

**Why it matters:** Makes the operational impact of one freshness failure
immediately understandable.

## 4. Severity, confidence, and remediation

**Frame:** Deterministic severity score, confidence percentage, and the
recommended ingestion rerun plus its verification step.

**Why it matters:** Demonstrates that impact, evidence quality, and action are
separate, explainable outputs.

## 5. Human approval

**Frame:** `AWAITING_APPROVAL` state, **Approve bound report** action, and the
timeline immediately before mutation.

**Why it matters:** Shows the deliberate human-control moment and makes clear
that investigation does not imply mutation authority.

## 6. DataHub write-back and read-back proof

**Frame:** Side-by-side or paired capture of DIC in `RECORDED` with the verified
write-back receipt and DataHub showing `dic-incident-recorded` on the NYC Taxi
raw dataset.

**Why it matters:** Proves real work occurred in DataHub and was independently
read back before in-process incident memory was recorded.
