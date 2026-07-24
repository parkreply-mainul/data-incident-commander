# DataHub MCP Capabilities Baseline

## Scope and classification

This document is based on the official
[DataHub MCP Server guide](https://docs.datahub.com/docs/features/feature-guides/mcp)
and the official
[MCP Server repository](https://github.com/acryldata/mcp-server-datahub), as
reviewed on **2026-07-24**.

Classifications mean:

- **Verified:** explicitly documented by an official source. This is
  documentation verification, not a successful local tool call.
- **Requires runtime verification:** officially documented, but availability,
  schema, permissions, or behavior must be confirmed against the selected
  running server.
- **Unknown:** not established by the reviewed official documentation for the
  project’s required use.

## Official purpose

**Verified.** The DataHub MCP Server implements Model Context Protocol and gives
AI agents access to DataHub metadata. Official use cases include asset search,
metadata and schema inspection, upstream/downstream lineage, usage/query
context, ownership, organizational context, and quality signals.

The official guide documents both a managed MCP Server for DataHub Cloud and a
self-hosted open-source MCP Server that works with DataHub Core.

## Self-hosted installation and execution

| Capability | Classification | Evidence and project interpretation |
| --- | --- | --- |
| Self-hosted server for DataHub Core | Verified | Official guide explicitly supports the open-source self-hosted server with DataHub Core. |
| Package execution with `uvx` | Verified | Official configuration runs `uvx mcp-server-datahub@latest`. |
| `uv` prerequisite | Verified | Official self-hosted instructions require `uv`. |
| Exact MCP package version for this project | Requires runtime verification | `latest` is documented, but this project should pin a tested release. |
| Compatibility with the selected DataHub OSS release | Requires runtime verification | Must be exercised against the actual GMS and tool inventory. |
| Standalone HTTP port for the self-hosted process | Unknown | The reviewed self-hosted instructions describe client-launched execution and do not establish a project port. |

No package has been installed and no MCP process has been started.

## Authentication model

| Capability | Classification | Evidence and project interpretation |
| --- | --- | --- |
| Self-hosted GMS URL configuration | Verified | Official environment variable: `DATAHUB_GMS_URL`. |
| Self-hosted Personal Access Token configuration | Verified | Official environment variable: `DATAHUB_GMS_TOKEN`. |
| Service account for unattended agents | Verified | Official guide recommends a service account rather than a personal token for agentic workflows. |
| Token permissions required by each read tool | Requires runtime verification | Depends on selected DataHub policies and user/service account. |
| Token permissions required by mutation tools | Requires runtime verification | Must be least-privilege and confirmed against the running instance. |
| Local quickstart PAT creation and persistence behavior | Requires runtime verification | Must be tested without recording the token in repository files or logs. |

Secrets must never be committed, placed in command output, or embedded in URLs
stored by this repository.

## Read capabilities

| Capability | Classification | Officially documented tool or behavior |
| --- | --- | --- |
| Structured asset search | Verified | `search` |
| Batch entity metadata retrieval by URN | Verified | `get_entities` |
| Dataset schema-field listing | Verified | `list_schema_fields` |
| Upstream and downstream lineage | Verified | `get_lineage` |
| Paths between two assets or columns | Verified | `get_lineage_paths_between` |
| Dataset query retrieval | Verified | `get_dataset_queries` |
| SQL-context discovery and drafting | Verified | `find_sql_context`, `draft_sql_for_tables` |
| Current authenticated user | Verified | `get_me` |
| Document search | Verified | `search_documents`, `grep_documents`; officially documented as hidden when no documents exist |
| Glossary lifecycle/version inspection | Verified | `list_lifecycle_stages`, `get_glossary_term_versions`, `compare_glossary_term_versions` |
| Pending proposal listing | Verified | `list_pending_proposals` |
| Ownership retrieval for the NYC Taxi assets | Requires runtime verification | Official capability description includes ownership, but the exact entity payload and populated metadata must be observed. |
| Quality-signal retrieval for planted evidence | Requires runtime verification | Official capability description includes quality signals; exact representation and tool response must be observed. |
| Freshness-specific evidence retrieval | Unknown | No dedicated freshness tool or guaranteed freshness field was established by the reviewed sources. |
| Previous incident retrieval | Unknown | No incident-specific MCP read tool was established by the reviewed sources. |

Official tool names are verified only at the documentation level. Sprint runtime
validation must inventory the tools actually exposed by the pinned server and
capture input/output schemas.

## Mutation and write capabilities

Write support must not be inferred merely because tools are documented.

| Capability | Classification | Evidence and project interpretation |
| --- | --- | --- |
| Mutation tools exist in self-hosted MCP Server v0.5.0+ | Verified | Official guide documents availability beginning with v0.5.0. |
| Mutation tools disabled by default | Verified | Official guide requires `TOOLS_IS_MUTATION_ENABLED=true`. |
| Add/remove tags | Requires runtime verification | Officially documented, but selected version, configuration, permissions, and behavior are untested. |
| Add/remove glossary terms | Requires runtime verification | Same runtime gate. |
| Add/remove owners | Requires runtime verification | Same runtime gate. |
| Set/remove domains | Requires runtime verification | Same runtime gate. |
| Update descriptions | Requires runtime verification | Same runtime gate. |
| Add/remove structured properties | Requires runtime verification | Same runtime gate. |
| Set lifecycle stage | Requires runtime verification | Same runtime gate. |
| Save documents | Requires runtime verification | `save_document` is documented, but document availability and project suitability are untested. |
| Glossary authoring and proposals | Requires runtime verification | Tools are documented, but permissions and DataHub Core behavior must be observed. |
| Write a native DataHub incident record | Unknown | No incident-specific mutation tool was established by the reviewed sources. |
| Read a persisted incident back through MCP | Unknown | No incident-specific read-back tool was established. |
| Store and retrieve project incident memory | Unknown | A safe representation and supported read/write path have not been selected. |

Mutation tools must remain disabled during the read-only capability spike.
Documentation verification does not authorize mutation.

## Required runtime capability spike

The future spike must:

1. pin the DataHub OSS, CLI, and MCP Server versions;
2. start only after separate authorization;
3. authenticate with a least-privilege test identity;
4. list the actual MCP tool inventory;
5. record exact input and output schemas;
6. exercise read-only asset search, entity lookup, ownership/quality retrieval,
   and both lineage directions;
7. determine whether freshness and previous incidents are represented;
8. confirm failure and permission behavior;
9. keep all mutation tools disabled; and
10. classify the incident write/read-back path only after observed evidence.

## Project decision boundary

The read investigation must use verified DataHub MCP operations. If no suitable
MCP mutation supports incident memory, the project may evaluate an official
DataHub write API or SDK only if hackathon rules permit it. The actual write
path must be disclosed, human-approved, read back, and never simulated.
