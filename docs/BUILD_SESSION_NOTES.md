# Official Build Session Notes

## Evidence boundary

Reviewed **2026-07-24**:

- [Build a DataHub AI Agent in 30 Minutes (Live Tutorial + MCP Setup)](https://youtu.be/_7cOIsvjFB0),
  published on the Devpost YouTube channel;
- the public YouTube title, description, timestamps, and linked resources;
- the official starter source at commit
  [`c84cea6721fc227d49201ba30c29540cb88c22be`](https://github.com/lakshay-nasa/datahub-agent-starter/commit/c84cea6721fc227d49201ba30c29540cb88c22be);
- current [DataHub quickstart](https://docs.datahub.com/docs/quickstart),
  [MCP guide](https://docs.datahub.com/docs/features/feature-guides/mcp), and
  [Agent Context Kit guide](https://docs.datahub.com/docs/dev-guides/agent-context/agent-context);
  and
- the [official hackathon rules](https://datahub.devpost.com/rules).

YouTube advertised an English auto-generated caption track, but caption content
was not retrievable through the read-only metadata request used for this audit.
No transcript or video was downloaded. Consequently, the table below reports
only details observable in the official description or corroborated by source
and official documentation. It does not reconstruct unobserved on-screen
commands.

## Observable session sequence

| Time | Official description | Audit interpretation |
|---|---|---|
| 00:00–07:19 | Welcome, hackathon, DataHub, UI schemas/lineage/ownership | Product and category context |
| 08:29 | “Spin up DataHub locally in 2 commands” | Exact two commands are not printed in the description; current docs use CLI installation then `datahub docker quickstart` |
| 09:39 | Sample data versus real datasets | The starter later assumes healthcare metadata; the repository contains no dataset loader |
| 12:04 | MCP, Skills, Agent Context Kit | Distinct integration choices are introduced |
| 13:08 | Self-hosted OSS Core MCP setup | Confirms MCP is demonstrated in the session, not that the starter consumes it |
| 13:51 | GMS URL, tokens, mutation/write-back | Configuration is demonstrated; exact values and successful mutation state require runtime observation |
| 15:09 | Mutation toggle troubleshooting | Indicates mutation enablement can be gated by runtime/server configuration |
| 17:51 | Live MCP connection test | Exact observed inventory and tool schemas are not present in the description |
| 21:44 | Build a custom agent | Corroborated by the linked starter source |
| 28:09 | Framework, tools, model | Starter maps these to LangGraph, Agent Context Kit, and a provider LLM |
| 30:18 | “22 agent tools (10 read / 12 write)” | Time-bound video claim; do not use as our inventory because current docs and runtime may differ |
| 34:22 | MCP versus Agent Context Kit versus Skills | Corroborates that these are alternatives/complements, not one hidden transport |
| 37:10 | Auto-assign owners and flag issues | The starter extension prompt requests `add_owners`; on-screen success was not independently captured |
| 44:05 | Open-source Analytics Agent | Reference implementation, not part of the starter |
| 46:26 | Solve a real problem, not just a demo | Aligns with DIC's real-work acceptance rule |

## Starter workflow corroborated by source

The starter README documents:

```text
create venv
pip install -r requirements.txt
copy .env.example to .env
set DataHub GMS URL/token and an LLM key
python agent.py
```

Its code then constructs `DataHubClient.from_env()`, calls
`build_langchain_tools(..., include_mutations=True)`, initializes the chosen
chat model, constructs a LangGraph ReAct agent, and invokes the configured
goal. This direct Agent Context Kit path is separate from the session's MCP
client setup.

The source's reported write actions are:

- add `needs-review`;
- update a dataset description; and
- in the extension prompt, add an owner.

The sample-run prose says the first two were reflected in the UI. It does not
show an approved payload, machine-readable receipt, or read-back comparison.

## Differences and caution points

1. **MCP versus starter:** the session covers both, while `agent.py` uses only
   Agent Context Kit directly.
2. **Tool count:** the description's 10-read/12-write count is not a substitute
   for Sprint 8C `list_tools` evidence.
3. **Python:** the starter says 3.9+; current Agent Context Kit documentation
   says Python 3.10+.
4. **Dependencies:** the starter pins no versions.
5. **Sample data:** no loader or healthcare dataset is included in the starter.
6. **Mutation:** the starter enables writes immediately; current MCP docs use a
   separate environment gate and version requirement.
7. **Approval:** neither starter source nor its sample output implements DIC's
   human approval and payload binding.
8. **Success:** UI visibility in tutorial prose is not equivalent to read-back
   payload verification.
9. **Deployment:** local quickstart is unsuitable for this 8 GB Mac under the
   project's documented feasibility decision.

## Commands that are verified versus deferred

Verified from current official documentation:

- install the DataHub CLI;
- run `datahub docker quickstart`;
- install Agent Context Kit with
  `pip install "datahub-agent-context[langchain]"`; and
- build Agent Context Kit LangChain tools read-only by default, with mutation
  explicitly opted in.

Verified from starter source:

- `pip install -r requirements.txt`;
- `python agent.py`; and
- direct `DataHubClient.from_env()` construction.

Deferred until Sprint 8C:

- the exact pinned self-hosted MCP install/start command;
- the actual tool inventory and schemas;
- the pinned Agent Context Kit version, if fallback evaluation is authorized;
- the NYC Taxi ingestion command and actual asset identifiers; and
- every mutation and read-back command.
