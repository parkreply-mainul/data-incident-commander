# Official Starter versus DataIncident Commander

## Decision labels

- **Reuse concept:** retain the idea, not the source implementation.
- **Adapt:** use the pattern behind one of our existing boundaries.
- **Keep our implementation:** our existing design better satisfies the
  product contract.
- **Reject:** conflicts with evidence, safety, or operability requirements.
- **Runtime verification required:** static evidence is insufficient.

## Structured comparison

| Area | Official starter | DataIncident Commander | Decision |
|---|---|---|---|
| Product shape | One Python script plus a prompt/goal | Domain core, FastAPI application, React desktop UI, integration protocols | **Keep our implementation** |
| DataHub connection | `DataHubClient.from_env()` direct to GMS | Library-neutral MCP client protocol and normalized adapter boundary | **Adapt** direct-client construction only as a fallback adapter |
| Tool surface | Agent Context Kit converted to LangChain tools | Required capabilities normalized behind `EvidenceProvider` | **Keep our implementation**; **runtime verification required** |
| Standalone MCP | Not used | Mandatory on the current live acceptance path | **Keep our implementation** |
| Reasoning | Tool-calling LLM in a LangGraph ReAct loop | Deterministic lineage, blast radius, severity, confidence, state, and memory | **Keep our implementation** |
| LLM | Required by the starter's execution loop | Not required for deterministic investigation; optional future prose assistance | **Reject** an LLM as authority; **reuse concept** only for bounded optional recommendations |
| Read controls | Prompt tells model to inspect first | Application orchestration, typed evidence, provenance, limits, known/unknown split | **Keep our implementation** |
| Mutation | All mutation tools enabled at construction | Disabled by default; planned explicit approval, payload binding, write/read-back | **Reject** starter behavior |
| Approval | Prompt-level conservatism only | Immutable state machine and explicit human approval | **Keep our implementation** |
| Evidence | Model consumes tool results and prints prose | Immutable Evidence Ledger with referential integrity | **Keep our implementation** |
| Severity/confidence | No deterministic contracts | Versioned deterministic engines, separate concepts | **Keep our implementation** |
| Incident memory | None | Deterministic matching contracts; live persistence pending | **Keep our implementation** |
| Readiness | None | Component/capability readiness and fail-closed provider | **Keep our implementation** |
| Error handling | Broad catch and guessed likely cause | Stable public-safe application and integration error models | **Keep our implementation** |
| Persistence | DataHub mutations only | In-memory incident repository now; durable incident/write receipt planned | **Keep our implementation** |
| Tests | None | Unit, API, frontend, integration-contract, deployment regression suites | **Keep our implementation** |
| Dependency management | Unpinned `requirements.txt` | Exact direct pins and lock file where applicable | **Reject** unpinned adoption |
| Local runtime | Assumes local quickstart and 8 GB+ Docker allocation | Local start blocked; approved remote VM strategy | **Keep our implementation** |
| Deployment/security | None | Provider-neutral, approval-gated, private-service deployment plan | **Keep our implementation** |
| Demo complexity | Very low, but dependent on LLM behavior and preexisting metadata | Higher, but deterministic and auditable | **Adapt** the smallest viable live vertical slice |
| Hackathon fit | Uses an explicitly allowed Agent Context Kit path | Uses OSS plus MCP and writes durable incident knowledge | Both can comply; DIC better fits its own acceptance contract |
| Licensing | MIT | Public Apache 2.0 target | **Reuse concepts**, do not vendor |

## Concepts worth adopting

1. Keep the DataHub connection/tool adapter narrow.
2. Make the goal/scenario configuration separate from integration mechanics.
3. Support a swappable optional tool-calling model only after deterministic
   evidence assembly.
4. Demonstrate one concrete, visible write rather than many speculative actions.
5. Fail clearly when referenced catalog objects do not exist.

## Concepts that require adaptation

- Agent Context Kit could implement a fallback `EvidenceProvider` or a
  write-only adapter if standalone MCP mutation is unavailable. It must return
  normalized DTOs, not LangChain messages.
- The starter's “read → act → write back” loop maps to DIC's stricter
  “read → normalize → calculate → review → approve → write → read back.”
- Model selection, if introduced, belongs behind a separate optional protocol.
  It must not determine severity, confidence, state transitions, or whether a
  mutation is authorized.

## Rejected tutorial behaviors

- enabling all mutations during tool construction;
- granting an LLM direct authority to choose and execute writes;
- relying on prompts as an approval mechanism;
- treating a final model message as a write receipt;
- assuming local quickstart, sample data, tags, owners, or asset names exist;
- broad exception handling that guesses the cause;
- unpinned dependencies; and
- accepting a prose sample run as integration proof.

## Compliance interpretation

The [official rules](https://datahub.devpost.com/rules) allow the
“Agents That Do Real Work” category to read through either MCP Server or Agent
Context Kit, and require action plus a result written back. They also permit
starter templates when disclosed and properly licensed.

DataIncident Commander's own charter is stricter: its golden-demo evidence must
come through verified DataHub MCP operations. The starter therefore informs a
fallback but does not justify silently replacing MCP. Any such change would
require an explicit architecture and acceptance-criteria decision.
