# Runtime Architecture Decision

## Status

**Decision:** retain **Option A, standalone MCP as the primary integration**.

**Fallback:** use **Option D, MCP for all investigation reads with Agent Context
Kit considered only for verified write-back**, and only if the pinned
standalone MCP runtime cannot provide a suitable mutation.

This is a planning decision, not runtime verification. No dependency,
infrastructure, server, or mutation was enabled during Sprint 8B.

## Decision drivers

- preserve the project's mandatory DataHub OSS and MCP acceptance contract;
- minimize changes to the implemented `EvidenceProvider` and MCP adapter
  boundary;
- keep deterministic calculations and approval outside any LLM/tool loop;
- make tool discovery and provenance observable;
- keep mutation disabled until a separate approval;
- minimize services and credentials on the judging VM; and
- produce a repeatable, fail-closed demo.

## Options

Scores are relative planning judgments: **low**, **medium**, or **high** risk or
effort. Runtime facts remain subject to Sprint 8C.

| Option | Time | Runtime complexity / memory | Read and write fit | Approval/testability | Compliance and demo risk | Decision |
|---|---|---|---|---|---|---|
| **A. Standalone MCP primary** | Low–medium: current boundary already targets it | One additional private process; exact footprint unknown | Official read tools and v0.5.0+ mutations are documented; actual v1.6.0 inventory unobserved | Strong: inventory, DTO normalization, approval, and receipts remain in DIC | Lowest risk against DIC's explicit MCP requirement | **Primary** |
| **B. Agent Context Kit in FastAPI** | Medium: new SDK adapter, dependencies, direct GMS path | No MCP process; Python dependencies and GMS credential in backend | Starter demonstrates direct read/write tool construction | Good only after removing LangGraph/LLM authority and adding our controls | Rules allow it, but it fails DIC's current MCP-origin acceptance contract | Not selected |
| **C. Agent Context Kit primary plus MCP compatibility adapter** | High | Two overlapping integration paths | Broadest theoretical coverage | Duplicate normalization, readiness, and error paths | “Compatibility” MCP could become ceremonial rather than evidence origin | Reject |
| **D. MCP reads, Agent Context Kit only for write-back** | Medium–high and deferred | Adds SDK only if needed | Keeps evidence on MCP; provides documented direct SDK fallback candidate | Approval can select one verified write adapter and require MCP/SDK read-back | Compliant if disclosed and rules permit the official SDK fallback | **Fallback** |
| **E. Another official path** | Unknown | Unknown | DataHub Skills and Analytics Agent serve different use cases | Requires separate audit | Higher schedule risk | Runtime verification only |

## Why the starter does not change the primary

The official starter is optimized for teaching: it directly converts Agent
Context Kit capabilities into LangChain tools and lets a tool-calling LLM run
the loop. That reduces tutorial code, but Data Incident Commander has already
implemented the boundaries the starter omits: evidence provenance,
deterministic calculation, safe errors, component readiness, optimistic
concurrency, human approval, and a professional UI.

Replacing those layers with the starter would increase safety risk and discard
working project-specific value. Adding Agent Context Kit beside MCP now would
also introduce two unverified external contracts. The fastest reliable path is
to complete the adapter already prepared.

## Primary runtime flow

```text
React responder UI
       |
       v
FastAPI InvestigationService
       |
       v
DataHubMcpEvidenceProvider
       |
       v
verified MCP client + captured tool inventory
       |
       v
self-hosted DataHub MCP Server (private, mutations off)
       |
       v
DataHub OSS v1.6.0 (private GMS)
```

The deterministic domain core calculates graph impact, severity, confidence,
and memory matches from normalized evidence. An LLM is **not required** for
this read-only investigation path. If later used to improve remediation prose,
its output remains inferred, evidence-linked, and non-authoritative.

## Write path decision gate

1. Verify the standalone MCP version and actual mutation inventory.
2. Keep MCP mutation disabled during all read-path tests.
3. Select one minimal incident-memory write representation only after DataHub
   metadata support is observed.
4. Bind the exact normalized payload to explicit human approval.
5. Prefer the verified MCP mutation.
6. If absent or unsuitable, evaluate a pinned Agent Context Kit/direct SDK
   adapter under the hackathon rules and project charter.
7. Never expose mutation tools to an unconstrained ReAct loop.
8. Declare success only after independent read-back equals the approved payload.

Option D is not automatically authorized by this document.

## Version gates

| Component | Static finding | Gate |
|---|---|---|
| DataHub OSS | Project pin `v1.6.0` | Start and health-check on approved VM |
| DataHub CLI | Project pin `acryl-datahub==1.6.0` | Verify against server |
| MCP Server | Official docs say mutation requires `mcp-server-datahub` v0.5.0+ | Select exact release; install; capture version and tools |
| Agent Context Kit | Starter leaves `datahub-agent-context[langchain]` unpinned | Resolve an exact compatible version only if fallback is invoked |
| Python | Official current Kit docs require 3.10+; project runtime targets 3.11 | Clean install on selected Ubuntu |
| LangChain/LangGraph | Starter unpinned | Not required on primary deterministic path |
| LLM provider | Starter defaults to Anthropic and supports alternatives | Optional for DIC; separate credential approval if used |

No static source establishes DataHub OSS 1.6.0 compatibility with a particular
MCP or Agent Context Kit release. That must be observed.

## Go criteria

- approved remote host meets the 4-vCPU/16-GB/50-GB project gates;
- DataHub v1.6.0 is healthy through verified endpoints;
- selected MCP release and authentication are recorded;
- required read-only tools are observed with schemas and version;
- one asset search, lineage query, ownership query, and quality/freshness check
  normalize without invented fields;
- runtime evidence carries MCP provenance;
- application readiness becomes operational only after those checks; and
- mutation remains disabled.

## No-go criteria

- MCP cannot authenticate to the pinned DataHub OSS runtime;
- required read capabilities are missing, mutating, or version-mismatched;
- expected evidence cannot be normalized without guessing;
- infrastructure breaches resource, exposure, or budget gates;
- the application can claim success when MCP/DataHub is unavailable; or
- write-back cannot be placed behind approval and read-back verification.
