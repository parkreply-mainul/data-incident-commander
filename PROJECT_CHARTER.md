# Project Charter

## Project identity

**Name:** DataIncident Commander  
**Program:** DataHub Agent Hackathon  
**Target category:** Agents That Do Real Work  
**Repository type:** Standalone public Apache 2.0 repository  
**Current status:** Sprint 1B documentation foundation; not implemented

## Mission

Build a professional incident investigation application that uses a running
DataHub OSS instance and verified DataHub MCP Server operations to locate
assets, analyze lineage and operational evidence, calculate impact and
severity, support human decisions, and preserve verified incident memory.

## Non-negotiable real-work guarantee

Runtime investigation evidence and the golden demo must originate from a
running DataHub OSS instance through verified DataHub MCP operations. A
fixture-only, chatbot-only, hard-coded, precomputed, or screenshot-only demo is
not acceptable. The product must visibly fail or report unavailable
dependencies when DataHub or MCP is unavailable. Fixtures are limited to
isolated automated tests and may never simulate successful live integration.

## Primary golden scenario

The primary demonstration is the **NYC Taxi planted freshness incident**. A
synthetic NYC Taxi metadata environment will contain a stale or failed upstream
dataset condition. The investigation must resolve the relevant asset, traverse
both upstream and downstream lineage, collect freshness or quality and
ownership evidence, identify affected dashboards or derived assets, calculate
blast radius, calculate deterministic severity and separate confidence, propose
evidence-backed remediation, retrieve relevant previous incidents, and enter
the human-controlled persistence flow.

Exact asset names, metadata fields, expected owners, incident representation,
and graph shape are subject to validation during the DataHub OSS dataset spike
and verified MCP capability spike. This charter does not invent them.

## Required investigation workflow

The MVP must support:

1. asset resolution with ambiguity handling;
2. bounded upstream lineage traversal;
3. bounded downstream lineage traversal;
4. reproducible blast-radius calculation from retrieved paths;
5. freshness and quality evidence retrieval;
6. ownership and domain retrieval;
7. a provenance-preserving Evidence Ledger;
8. deterministic, versioned severity;
9. confidence and evidence-coverage calculation;
10. explicit known, derived, hypothesized, and unknown separation;
11. evidence-backed remediation;
12. relevant previous incident retrieval and memory;
13. professional desktop visualization and review;
14. explicit human approval;
15. planned DataHub write-back through a verified, permitted path;
16. persisted-payload read-back comparison; and
17. verified recording as incident memory.

The human-controlled lifecycle is:

```text
Draft investigation
  → human review
  → explicit approval
  → write-back
  → read-back
  → payload verification
  → recorded incident memory
```

## Evidence, severity, and confidence contract

- Confirmed findings require evidence references.
- Derived findings require evidence references and a documented calculation.
- Hypotheses and unknowns must not be presented as observed facts.
- The Evidence Ledger preserves provenance, timestamps, conflicts, and gaps.
- Severity measures impact and urgency through deterministic, versioned rules.
- Confidence is separate from severity and ranges from **0.0 to 1.0**.
- Confidence represents evidence coverage and consistency, not model certainty.
- Missing or conflicting evidence lowers confidence.
- Low confidence prevents overconfident root-cause claims.
- The desktop UI displays confidence, coverage, conflicts, and unknowns.

## Success criteria

The MVP is successful only when a reproducible run:

1. proves that runtime evidence was retrieved from live DataHub OSS through
   verified MCP operations;
2. fails visibly when those required dependencies are unavailable;
3. resolves the expected NYC Taxi scenario asset without hidden hard-coding;
4. displays verified upstream and downstream lineage;
5. calculates and explains blast radius, severity, and confidence;
6. attributes material findings and remediation to evidence;
7. retrieves and displays relevant previous incident memory;
8. obtains explicit human approval before mutation;
9. uses a verified and permitted DataHub write path without simulation;
10. reads the persisted record back and verifies payload equivalence;
11. safely handles missing, stale, conflicting, or malicious metadata;
12. provides a professional, accessible desktop experience; and
13. passes clean-install, one-command demo, security, and submission checks.

## Intended stack

### Backend

- Python
- FastAPI
- Pydantic
- pytest

### Frontend

- React
- TypeScript
- Vite

### Integration

- DataHub OSS
- DataHub MCP Server

No dependency or version is selected or installed in Sprint 1B.

## Professional desktop UI commitment

The UI must include investigation input, a live investigation timeline,
severity and root-cause summary, visual upstream/downstream lineage graph,
blast-radius view, Evidence Ledger, confidence and known/unknown panel, owners
and domains, remediation plan, human approval controls, write/read verification
status, previous incident memory, recent incidents, and complete empty, loading,
partial, error, disconnected, success, and resolved states.

Real functionality is implemented and verified before visual polish.
Professional visual quality and accessibility remain a dedicated project phase
and mandatory submission criterion.

## Planned write path and verification gate

Write-back is planned and is not confirmed. It is subject to verification of
supported DataHub MCP mutation capabilities against official documentation and
the actual running tool inventory.

- Prefer a verified MCP mutation tool.
- If MCP provides no appropriate mutation, an officially supported DataHub
  write API or SDK may be documented and used only if hackathon rules permit.
- The required approved DataHub technology remains mandatory for the
  read/investigation path.
- Never simulate successful write-back.
- The final architecture must disclose the actual verified write path.
- Read-back must retrieve the persisted representation and compare normalized
  material fields with the human-approved payload before success is recorded.

## Scope exclusions

- changing source data or pipelines;
- executing remediation automatically;
- contacting or paging owners;
- silently resolving ambiguous assets;
- unrestricted lineage traversal;
- simulated live evidence or simulated persistence;
- production-grade multi-tenancy; and
- support for unrelated metadata platforms.

## Project independence

The repository is completely independent:

- Do not access ParkReply code.
- Do not access SafeRelay code.
- Do not access PIC code.
- Do not copy, import, adapt, reference, or use any of them as hidden
  dependencies, implementation sources, fixtures, or demo data.

Only original repository material and appropriately licensed public
dependencies are permitted.

## Public repository constraints

- Release under Apache License 2.0.
- Do not commit credentials, tokens, private metadata, or real incident data.
- Keep demo metadata synthetic.
- Review dependency licenses before adoption.
- Redact sensitive values from logs, screenshots, and recorded test material.
- Make limitations, unverified capabilities, and actual write paths explicit.

## Risks and mitigations

| Risk | Consequence | Planned mitigation |
| --- | --- | --- |
| Sparse or conflicting metadata | Unreliable conclusions | Lower confidence and expose unknowns |
| Ambiguous asset search | Wrong investigation target | Rank candidates and require confirmation |
| Large or cyclic lineage | Slow or misleading impact analysis | Enforce depth, node, call, and time budgets |
| Hallucinated conclusions | Unsupported root cause or action | Evidence Ledger and claim-level references |
| Severity/confidence conflation | Misleading urgency | Separate deterministic severity from coverage confidence |
| Unsafe mutation | Duplicate or incorrect incident memory | Human approval, stable keys, read-back equivalence |
| MCP capability mismatch | Planned operation unavailable | Verify official docs and actual tool inventory first |
| Demo hard-coding | No real agent work | Require runtime provenance and dependency-failure tests |
| UI polish hides weak behavior | Misleading submission | Verify functionality before dedicated UI polish |

## Governance and Sprint 1B exit criteria

Architecture decisions affecting evidence, severity, confidence, permissions,
memory, or persistence must be documented before implementation. Sprint 1B is
complete when the charter, architecture, implementation plan, test strategy,
environment template, and placeholder command contract consistently express
these requirements. No application or automation implementation belongs in
Sprint 1B.
