# Remote Runtime Security

## Scope

This is a security design for a future temporary demo VM. Nothing has been
provisioned, configured, or exposed. Provider-specific behavior must be
verified before execution.

## Trust and exposure boundary

```text
Public judge
    |
 HTTPS 443
    |
reverse proxy / application frontend
    |
private host or Docker network
    +-- FastAPI backend
    +-- DataHub MCP Server
    +-- DataHub GMS and frontend
    +-- MySQL, OpenSearch, Kafka
```

Only the application HTTPS entry point should be generally public. DataHub
GMS, DataHub UI, MCP, databases, Kafka, Docker socket, metrics, and
administration endpoints must not be directly internet-accessible.

DataHub warns that quickstart binds service and datastore ports broadly and
uses development credentials. The remote deployment must therefore customize
bindings or place an independently verified firewall/reverse-proxy boundary
before startup. A cloud firewall alone must not be assumed to correct unsafe
host bindings.

## Least-privilege access

- Create one named administrative account; disable routine direct root login.
- Use `sudo` only for documented host administration.
- Treat membership in the Docker group as root-equivalent because Docker
  socket access controls the host.
- Do not expose the Docker daemon over unauthenticated TCP. Prefer local use or
  Docker's documented SSH transport.
- Give the runtime only the repository, network, filesystem, and secret access
  it needs.
- Separate judge-facing application authorization from administrator access
  and DataHub mutation authorization.

Source: [Docker daemon access security](https://docs.docker.com/engine/security/protect-access/).

## SSH key policy

- Use a dedicated Ed25519 key for this temporary runtime.
- Never copy a personal private key into the repository or VM image.
- Restrict SSH at the provider firewall to known administrator IP ranges when
  practical; do not accept the provider's broad `0.0.0.0/0` suggestion without
  review.
- Disable password authentication after key and recovery-console access are
  verified.
- Record the host fingerprint through a trusted channel.
- Do not enable SSH agent forwarding.
- Rotate/remove the key when the VM is deleted.
- Because the code repository is public, clone over HTTPS without a Git
  credential. If private access later becomes necessary, use a repository-only
  read-only deploy key and revoke it after deletion.

GitHub documents deploy keys as repository-scoped and read-only by default, but
also warns they do not expire and their private key remains on the server.

## Firewall and service-port policy

- Default-deny inbound traffic.
- Permit TCP 443 publicly only after TLS and application authentication tests.
- Permit TCP 22 only from approved administrator sources or use a verified
  provider console/private access path.
- Do not expose quickstart ports 3306, 4319, 8080, 9002, 9092, or 9200
  publicly.
- Bind backend and MCP transports to loopback or a private container network
  unless a verified authenticated transport requires otherwise.
- Review both provider firewall and host firewall rules. Docker warns that
  published container ports can bypass some host firewall arrangements.
- Permit outbound access only as required for package repositories, container
  registries, source retrieval, DNS, time synchronization, and approved model
  APIs.

DigitalOcean documents its cloud firewall as stateful, default-deny when no
inbound rule permits traffic, and free of additional charge:
[Cloud Firewall quickstart](https://docs.digitalocean.com/products/networking/firewalls/getting-started/quickstart/).

## Secret storage

- Never store credentials, tokens, private keys, generated signing material, or
  `.env` files in Git.
- Generate production-like demo secrets on the VM through an approved method.
- Store them in a provider secret service or root/runtime-readable file with
  restrictive permissions; exact mechanism requires provider selection.
- Keep secret values out of shell history, process arguments, screenshots,
  support bundles, and CI output.
- Maintain a documented inventory containing secret names and owners, never
  values.
- Use synthetic public-safe metadata only.

## DataHub token handling

- Enable and verify DataHub authentication before any remote mutation path.
- Create a dedicated least-privilege demo identity and token.
- Pass the token to MCP/backend at runtime without committing it.
- Do not expose it to the browser.
- Keep mutation disabled until actual MCP tools, permissions, approval gates,
  and read-back behavior are verified.
- Redact authorization headers, token fragments, signing keys, and salts from
  logs.
- Rotate the token after suspected exposure and at teardown.

## Public demo boundaries

- The judge-facing URL terminates TLS and reaches the application only.
- Direct DataHub UI access is optional and should remain private unless a
  documented judging need justifies authenticated exposure.
- Rate-limit and bound investigation requests.
- Require explicit human approval for any verified mutation.
- Prevent public users from choosing arbitrary MCP tools, URLs, credentials, or
  unbounded lineage traversal.
- Display dependency failure rather than falling back to fixtures.

## Logging and diagnostics

- Log request IDs, health state, evidence identifiers, and timing—not secrets.
- Redact tokens, cookies, authorization headers, SSH material, `.env` content,
  and synthetic signing secrets.
- Restrict log access to administrators.
- Define retention short enough for the temporary judging environment.
- Review diagnostics before including them in public issues or submission
  evidence.

## Deletion and credential rotation

After judging and winner announcement:

1. take only the explicitly approved metadata backup;
2. verify that required submission evidence is preserved without secrets;
3. revoke DataHub, model-provider, Git deploy, DNS, and cloud API credentials;
4. destroy the VM and separately billed volumes, snapshots, reserved IPs, load
   balancers, and DNS records;
5. verify provider billing inventory is empty;
6. remove local known-host entries only after confirming the exact host; and
7. record teardown date and evidence.

Deletion is destructive and requires explicit approval. Powering off a
DigitalOcean Droplet does not stop billing; billing ends when it is destroyed.
