# MCP Capability Verification

## Source checkpoint

Official sources rechecked **2026-07-24**:

- [DataHub MCP Server guide](https://docs.datahub.com/docs/features/feature-guides/mcp)
- [official open-source MCP repository](https://github.com/acryldata/mcp-server-datahub)

The guide documents self-hosted use with DataHub Core, `uvx
mcp-server-datahub@latest`, `DATAHUB_GMS_URL`, and `DATAHUB_GMS_TOKEN`.
Production use must replace `latest` with a tested exact pin.

## Classification

| Capability | Documentation | Runtime | Adapter treatment |
| --- | --- | --- | --- |
| Asset search (`search`) | Documented | Unobserved | Disabled |
| Entity inspection (`get_entities`) | Documented | Unobserved | Disabled |
| Schema fields (`list_schema_fields`) | Documented | Unobserved | No parser |
| Up/down lineage (`get_lineage`) | Documented | Unobserved | Disabled |
| Lineage paths (`get_lineage_paths_between`) | Documented | Unobserved | Disabled |
| Dataset queries (`get_dataset_queries`) | Documented | Unobserved | Outside initial required set |
| Ownership/context in entity metadata | Documented concept | Payload unobserved | Adapter assumption pending verification |
| Document tools | Documented; availability/configuration conditional | Unobserved | Disabled by project default |
| User tools | Documented/configurable | Unobserved | Disabled by project default |
| Mutation tools | Documented for self-hosted v0.5.0+ | Unobserved | Disabled |
| Incident write-back | Unsupported by current evidence | Unobserved | Unavailable |

Mutation documentation says it is enabled with
`TOOLS_IS_MUTATION_ENABLED=true`. This repository never sets that value true.
Documentation does not prove selected-version compatibility, permission,
schema, transport, or successful invocation.

## Runtime inventory gate

A future approved checkpoint must record:

1. exact MCP package version and artifact identity;
2. DataHub OSS v1.6.0 compatibility;
3. initialized transport/session behavior;
4. actual tool names and schemas from list-tools;
5. read-only annotations and enabled/hidden tool behavior;
6. least-privilege authentication and safe failures;
7. exact search, entity, lineage, ownership, quality, and freshness payloads;
8. timeouts, pagination, truncation, and partial results; and
9. mutation absence while the mutation flag is false.

An inventory with UTC observation time and individually observed, enabled
capabilities may satisfy the capability-verification gate only when every
required read identity is present, observed, enabled, explicitly read-only, and
recorded against the inventory's exact server version. The required set is
asset search, entity inspection, upstream/downstream lineage, lineage paths,
and ownership/context. Mutation and write-back never substitute for these
reads. Observed version mismatches reject the inventory before readiness is
calculated.

Capability verification cannot set operational readiness by itself. Readiness
additionally requires implemented, verified investigation orchestration; that
implementation does not exist in Sprint 8A, so provider availability remains
false. Test doubles label their source explicitly and do not constitute runtime
evidence.
