# Port Matrix

## Status

This matrix records only ports stated in current official DataHub
documentation. It does not infer project defaults from commonly used framework
ports or from the generic collision checks in `make check`.

Sources:

- [DataHub Quickstart Guide](https://docs.datahub.com/docs/quickstart)
- [DataHub MCP Server guide](https://docs.datahub.com/docs/features/feature-guides/mcp)

## Known official ports

| Service | Port | Official context | Runtime status |
| --- | ---: | --- | --- |
| DataHub quickstart UI | 9002 | Quickstart directs users to `http://localhost:9002`. | Not started or verified on this host |
| DataHub GMS | 8080 | Self-hosted MCP guide gives `http://localhost:8080` as a GMS endpoint example. | Example documented; actual quickstart exposure and health require runtime verification |

These entries do not imply that every DataHub deployment uses these ports.

## Project-configurable ports

No project port has been selected.

| Project service | Selected port | Selection rule |
| --- | --- | --- |
| FastAPI backend | Requires verification | Choose after DataHub/MCP runtime inventory; make it configurable and collision-checked. |
| React/Vite development server | Requires verification | Choose with the frontend toolchain; do not assume a framework default. |
| Frontend preview/production server | Requires verification | Define only after deployment approach is selected. |
| Self-hosted MCP Server | Requires verification | Official local instructions currently describe client-launched `uvx` execution; do not invent an HTTP port. |

## Unknown ports requiring runtime verification

- Host-exposed quickstart ports other than the documented UI and GMS example.
- Internal MySQL port and whether it is exposed to the host.
- Internal OpenSearch port and whether it is exposed to the host.
- Internal Kafka port and whether it is exposed to the host.
- DataHub Actions endpoints, if any are host-exposed.
- Health-check endpoints and their ports.
- Any callback or transport port required by the selected MCP client.
- Backend, frontend, and smoke-test ports.

The actual Compose file generated for the pinned release must be inspected
before startup, then compared with listeners after startup.

## Generic candidate ports are not defaults

The macOS prerequisite checker currently checks these generic candidates for
collisions:

```text
3000 3306 5173 8000 8080 9002 9092 9200
```

Only 9002 and the documented 8080 GMS example have official DataHub context in
this baseline. The other checks are precautionary and must not be represented
as required or default ports.

## Runtime validation record

The future setup spike should record:

1. the pinned Compose file and its declared host mappings;
2. listeners before startup;
3. listeners after startup;
4. UI and GMS health results;
5. MCP transport behavior;
6. selected project ports; and
7. shutdown results confirming that project-managed listeners are released.
