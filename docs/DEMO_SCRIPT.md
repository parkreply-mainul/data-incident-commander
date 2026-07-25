# Data Incident Commander: 3–4 Minute Judge Demo

## Before the clock

Have three tabs open:

1. DIC **System status** showing DataHub and verified MCP readiness.
2. DIC **New investigation**.
3. DataHub on the NYC Taxi raw dataset.

Confirm the write-back tag is absent before beginning. Keep credentials and
terminal environment values off screen.

## 0:00–0:25 — Frame the problem

**Narration**

> “A stale table is rarely an isolated incident. Responders normally jump
> between catalog search, ownership, freshness, quality, and lineage, then make
> an impact judgment that is difficult to audit. Data Incident Commander turns
> that work into one evidence-backed, human-controlled flow.”

**Action**

- Show **System status** briefly.
- Point to DataHub, MCP, repository, and write-back capability separately.

**Highlight**

- DataHub v1.6.0 is the metadata authority.
- MCP is the mandatory evidence path.
- If either dependency is unavailable, DIC fails visibly.

## 0:25–0:55 — Report the incident

**Action**

- Open **New investigation**.
- Enter:
  - Title: `NYC Taxi raw trips are stale`
  - Target asset:
    `urn:li:dataset:(urn:li:dataPlatform:bigquery,dic_demo.nyc_taxi_trips_raw,PROD)`
  - Description: `The operations dashboard has not refreshed on schedule.`
  - Category: `freshness`
  - Requester: `Demo responder`
  - Team: `Data Platform`
- Select **Create draft**.

**Narration**

> “The report starts as intake only. DIC has not invented evidence, severity,
> or a root cause.”

**Highlight**

- State is `DRAFT`.
- The evidence panels clearly show that verified collection is still pending.

## 0:55–1:35 — Investigate with DataHub evidence

**Action**

- Select **Collect verified DataHub evidence**.
- Wait for state `INVESTIGATED`.
- Scroll to **Evidence ledger**.

**Narration**

> “DIC resolves this exact asset through DataHub MCP and collects asset
> metadata, technical ownership, freshness, quality, and lineage. Every record
> carries its DataHub source operation and timestamp.”

**Highlight**

- `asset_metadata`
- `ownership`
- `freshness_signal` showing `stale`
- `quality_assertion`
- the two `lineage_edge` records
- No fixture or synthetic evidence is presented as a live result.

## 1:35–2:10 — Explain impact and decision logic

**Action**

- Show **Lineage and blast radius**.
- Show **Severity and confidence**.
- Show **Recommended response**.

**Narration**

> “The stale raw trips affect the daily metrics directly and the operations
> dashboard transitively. Severity is calculated from versioned impact rules.
> Confidence is separate: it measures evidence coverage and consistency, not
> model certainty.”

> “The recommendation is to restore and rerun the delayed ingestion, then
> verify freshness and downstream updates. DIC recommends the action; it does
> not execute it.”

**Highlight**

- Direct versus transitive impact.
- Critical dashboard impact.
- Applied severity score.
- Confidence percentage and any missing evidence.
- Evidence references behind the recommendation.

## 2:10–2:50 — Human approval moment

**Action**

- Point out that write-back is not yet available.
- Select **Send report for human review**.
- Show state `AWAITING_APPROVAL`.
- Select **Approve bound report**.
- Show state `APPROVED`.

**Narration**

> “Mutation is disabled by workflow until a human reviews the evidence. The
> approval is not a generic yes: it binds the exact normalized report with
> SHA-256. If that payload changes, the approval is invalid.”

**Highlight**

- Timeline transitions.
- Human reviewer actor and approval reason.
- Exact payload binding.
- No write occurred during investigation or submission.

## 2:50–3:25 — Write-back and read-back proof

**Action**

- Select **Write tag and verify in DataHub**.
- Wait for state `RECORDED`.
- Show **DataHub write-back proof**.
- Switch to DataHub and refresh the NYC Taxi raw dataset.
- Point to `dic-incident-recorded`.

**Narration**

> “DIC performs one allowlisted metadata operation. It does not trust the
> mutation response alone: it reads `globalTags` back from DataHub and compares
> the observed tag. Only that verified match permits the `RECORDED` state.”

**Highlight**

- `write_back_receipt`
- `verified: true`
- The expected tag URN.
- The tag visible independently in DataHub.

## 3:25–3:45 — End with incident memory

**Action**

- Return to DIC.
- Show **Incident memory** and the completed timeline.

**Narration**

> “The verified record is now available as incident memory in the current
> incident repository. The result is grounded in DataHub, deterministic,
> reviewable, approval-gated, and proven by read-back.”

## If a dependency fails

Do not switch to fabricated results. Show the visible **Verification pending**
state and say:

> “This is intentional fail-closed behavior. Without verified DataHub and MCP
> evidence, DIC will preserve the draft but will not claim an investigation.”
