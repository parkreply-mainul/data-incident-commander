# Official DataHub Starter Agent Audit

## Scope and evidence

This audit was performed on **2026-07-24** against the public
[`lakshay-nasa/datahub-agent-starter`](https://github.com/lakshay-nasa/datahub-agent-starter)
repository at commit
[`c84cea6721fc227d49201ba30c29540cb88c22be`](https://github.com/lakshay-nasa/datahub-agent-starter/commit/c84cea6721fc227d49201ba30c29540cb88c22be).
The repository was shallow-cloned under `/private/tmp`, outside this project,
and was not vendored. Conclusions below come from the implementation, not only
the README.

Evidence classifications:

- **Verified from source** means the cited starter file implements or declares it.
- **Verified from official documentation** means current DataHub 1.6.0
  documentation states it.
- **Tutorial assumption** means the starter expects it but does not verify it.
- **Unknown until live runtime** means neither static source nor documentation
  proves behavior against our pinned server.
- **Unsafe for production-style use** identifies behavior that conflicts with
  DataIncident Commander's fail-closed and human-approval contracts.

## Complete source tree

```text
.env.example
.gitignore
LICENSE
README.md
agent.py
examples/sample-run.md
goal.py
prompts/build-agent.md
prompts/extend-agent.md
requirements.txt
```

There is no package metadata, lock file, test directory, CI workflow,
application server, frontend, persistence layer, deployment automation, or
container definition. The starter calls itself learning material rather than
production code in its
[`README.md`](https://github.com/lakshay-nasa/datahub-agent-starter/blob/c84cea6721fc227d49201ba30c29540cb88c22be/README.md).

## Language and dependencies

| Item | Source finding | Classification |
|---|---|---|
| Python | README recommends 3.11 and says 3.9+ works; no `requires-python` metadata enforces either | Tutorial assumption |
| Dependency manager | `pip install -r requirements.txt` in a `venv` | Verified from source |
| `datahub-agent-context[langchain]` | Direct, **unpinned** requirement; comment says its extra brings `acryl-datahub`, LangChain, and LangChain Core | Verified from source |
| `langgraph` | Direct, **unpinned** requirement | Verified from source |
| `langchain-anthropic` | Direct, **unpinned** default-model provider | Verified from source |
| `python-dotenv` | Direct, **unpinned** requirement | Verified from source |
| `acryl-datahub` | Transitive through Agent Context Kit; no version is pinned | Verified from source |
| MCP client/server package | None | Verified from source |

The exact installed versions are therefore not reproducible from the starter.
Its source provides no Agent Context Kit version, LangChain/LangGraph version,
DataHub SDK version, MCP version, or DataHub server compatibility constraint.
Current official Agent Context Kit documentation requires Python 3.10+, so the
starter's “works on 3.9+” statement must not be adopted without a clean
installation test. See the official
[Agent Context Kit overview](https://docs.datahub.com/docs/dev-guides/agent-context/agent-context)
and [LangChain guide](https://docs.datahub.com/docs/dev-guides/agent-context/langchain).

## Implemented integration architecture

The entire executable path is in
[`agent.py`](https://github.com/lakshay-nasa/datahub-agent-starter/blob/c84cea6721fc227d49201ba30c29540cb88c22be/agent.py):

```text
DATAHUB_GMS_URL + DATAHUB_GMS_TOKEN
          |
          v
DataHubClient.from_env()
          |
          v
build_langchain_tools(client, include_mutations=True)
          |
          +--> DataHub read and mutation tools
          |
LLM selected by AGENT_MODEL
          |
          v
LangGraph create_react_agent(...)
          |
          v
agent.invoke(GOAL) -> final model message
```

### Standalone MCP

**No standalone MCP server is started, consumed, or exposed by the starter.**
There is no MCP dependency, transport, session, endpoint, `list_tools` call, or
MCP result parser. The source comment explicitly says the Agent Context Kit
tools call DataHub directly. The README likewise says “no MCP server to run.”

The official DataHub documentation describes MCP and Python SDK framework
integration as two available routes. It says MCP clients discover server tools
automatically, while the Python route installs `datahub-agent-context` and
builds framework tools. Those statements do not turn the starter itself into
an MCP client or server.

### DataHub connection and authentication

`DataHubClient.from_env()` constructs the connection. The starter's
`.env.example` declares:

- `DATAHUB_GMS_URL`, defaulting to the tutorial's local `http://localhost:8080`;
- `DATAHUB_GMS_TOKEN`, described as a DataHub personal access token;
- `ANTHROPIC_API_KEY` for the default model;
- optional `OPENAI_API_KEY` or `GOOGLE_API_KEY`; and
- optional `AGENT_MODEL` in `provider:model` form.

The source does not validate URL safety, redact configuration objects, test the
connection before tool use, constrain token permissions, or define token
rotation. Authentication success and authorization are runtime concerns.

### Tool registration and discovery

The starter calls:

```python
build_langchain_tools(client, include_mutations=True)
```

This is direct library registration, not MCP runtime discovery. The starter
does not enumerate, validate, pin, or snapshot the returned tool inventory.
Its build prompt names these read tools:

- `search`
- `get_entities`
- `get_lineage`
- `list_schema_fields`

It names these mutation examples:

- `add_tags`
- `add_owners`
- `update_description`

Those names are evidence about the tutorial's expected Agent Context Kit
surface, not proof that our pinned runtime exposes compatible schemas. The
current official DataHub docs list a broader tool set, but Sprint 8C must still
capture the actual installed inventory and schemas.

### Read → reason → act → write loop

1. The system prompt instructs the model to search and inspect DataHub first.
2. LangGraph gives the selected tool-calling LLM the Agent Context Kit tools.
3. The LLM selects reads and interprets their results.
4. The same LLM may select one or more mutation tools because mutations are
   enabled at tool construction.
5. The final model message is printed as the report.

The default goal asks the model to inspect healthcare datasets, identify a
quality or ownership problem, add the `needs-review` tag, and update a
description. The extension prompt additionally asks it to assign an owner.
The sample-run document reports a tag and description update. These are
tutorial demonstrations, not deterministic acceptance evidence for our NYC
Taxi scenario.

## Mutation and safety analysis

Mutation is enabled in Python by `include_mutations=True`. This is distinct
from the standalone MCP server's documented
`TOOLS_IS_MUTATION_ENABLED=true` setting. Current official MCP documentation
states mutation tools require `mcp-server-datahub` v0.5.0+ and annotates them
as non-read-only so compatible clients can request confirmation.

The starter has **no application-enforced human approval**. Its only safety
controls are prompt language (“read first,” “one action,” “be conservative”)
and a README warning to use a local/test catalog. It does not:

- bind approval to a normalized payload;
- separate read and mutation credentials;
- default mutations off;
- require an approver identity and reason;
- verify persisted values by read-back;
- provide idempotency or partial-write recovery; or
- retain an immutable audit history.

Enabling mutation at agent construction gives the LLM immediate access to
write tools. That is unsafe for DataIncident Commander's production-style
design and must not be copied.

## Error handling and verification

`main()` catches a broad `Exception`, prints its message, and speculates that a
missing tag, term, or owner is the likely cause. It has no typed error model,
retry policy, timeout, partial-result handling, request ID, secret-safe
logging, readiness check, or non-zero process exit. A broad exception string
may also expose implementation details.

There are no automated tests. The sample run is prose explicitly described as
actual output that was lightly trimmed, but it provides no machine-verifiable
tool receipts, timestamps, approved payload, or read-back comparison.

## Data and deployment assumptions

- DataHub runs locally via Docker Desktop and quickstart.
- The README recommends 8 GB+ RAM for Docker.
- GMS is reachable at the tutorial URL.
- A personal access token has already been created.
- A healthcare sample dataset and the `needs-review` tag exist, although
  neither is included in the repository.
- The selected LLM provider supports tool calling and has a valid API key.
- There is no remote deployment, security, availability, rollback, or judging
  plan.

These assumptions explain the starter's speed, but they cannot replace our
remote feasibility gates, NYC Taxi ingestion, capability inventory, or
read-back verification.

## License and reuse boundary

The starter is MIT licensed. DataIncident Commander targets Apache 2.0.
Concepts may be studied and attributed, and the hackathon rules permit starter
templates, but no starter source has been copied into this repository. If code
were ever adapted, license notices and submission disclosure would require
explicit review. This audit recommends concept reuse only.

## Audit conclusion

The starter proves a useful concept: Agent Context Kit can turn a direct
DataHub Python client into framework tools with a very small amount of code.
It does **not** prove standalone MCP operation, deterministic evidence
grounding, safe mutation, human approval, runtime readiness, or reproducible
deployment. DataIncident Commander should keep its domain, application, UI,
EvidenceProvider, readiness, and approval architecture.
