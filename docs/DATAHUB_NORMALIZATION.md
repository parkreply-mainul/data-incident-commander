# DataHub Normalization Boundary

## Rule

Raw MCP dictionaries cannot enter the domain layer. A future concrete MCP
client must first validate observed response schemas and construct verified
adapter DTOs. Sprint 8A normalizers accept only those typed DTOs.

Connection configuration is validated before client or normalization work. GMS
literal addresses are allowlisted to loopback, RFC1918 IPv4, or IPv6 ULA;
link-local/metadata and other special or public destinations are rejected.

Implemented DTO boundaries cover:

- asset identity and optional ownership;
- directed lineage edges;
- freshness and quality signals; and
- source operation and observation/retrieval timestamps.

Normalization rejects missing identifiers, naïve timestamps, self/dangling
lineage edges, conflicting duplicate identities, noncanonical payloads, and
configured node-limit overflow. `LineageGraph.create` supplies deterministic
ordering and conflict rejection.

Normalizers preserve external identifiers, evidence references, source
operation, and UTC timestamps. They do not invent display identities, owners,
domains, timestamps, failure causes, quality status, lineage, or confidence.
Signal provenance explicitly identifies runtime-observed adapter DTO input and
states that the raw payload is not retained.

## Pending runtime work

No parser maps `search`, `get_entities`, `get_lineage`, or another tool's raw
payload today. Each parser requires an archived, redacted schema observation
from the pinned runtime, contract tests for malformed/partial variants, and a
review that no unsupported field semantics are inferred.
