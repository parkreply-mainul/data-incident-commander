# Application Services

`InvestigationService` is framework-independent and owns draft creation,
retrieval, deterministic listing, investigation orchestration, workflow
transitions, and repository persistence.

It depends only on protocols:

- `IncidentRepository`
- `EvidenceProvider`
- `IncidentIdProvider`
- `Clock`

Production defaults use UUID identifiers and UTC system time. Tests inject
fixed identifiers and a stepping UTC clock. The service does not receive
FastAPI requests, construct HTTP responses, interpret MCP payloads, or generate
unsupported evidence.

`UnconfiguredEvidenceProvider` is the fail-closed default. A future verified
adapter may implement the protocol after actual DataHub MCP tool inventory and
payloads are inspected. No raw DataHub or MCP schema is assumed here.

Investigation has a DRAFT-only preflight gate. The service rejects any other
workflow state before calling the provider, so invalid requests cannot trigger
external work. A valid DRAFT still receives an explicit dependency-unavailable
error from the default provider without persistence or synthetic evidence.

After an adapter returns a schema-valid normalized report, the service performs
semantic ownership checks before transition or persistence. Incident ID, target
external identifier, `INVESTIGATED` status, and protected draft title must
match. If both the draft and a reported root cause carry an issue category,
those categories must also match. Adapters normalize external payloads; the
application remains responsible for proving that normalized output belongs to
the requested incident.

Evidence providers expose an immutable, side-effect-free readiness descriptor:
configuration, availability, dependency name, and separate DataHub, MCP, and
write-back capabilities. Readiness inspection never calls the provider's
investigation operation.

Listing uses the repository's atomic page operation. The service receives
immutable items and total metadata from one lock-held snapshot rather than
combining separate list and count reads.

Transport request models are converted explicitly into application commands.
Immutable application records contain workflow state and an optional domain
report. A draft has no report, findings, severity, confidence, owners, or
evidence.
