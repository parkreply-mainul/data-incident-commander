# Remote Security Checklist

## Before compute

- [ ] Provider, region, SKU, tax, IP, storage, bandwidth, and budget approved.
- [ ] Cloud firewall default deny; only approved SSH sources and HTTPS planned.
- [ ] Named SSH key owner and recovery-console procedure recorded.
- [ ] Teardown owner, date, billing alert, and inventory tags recorded.

## Host

- [ ] Ubuntu 24.04 LTS image and architecture verified.
- [ ] Security updates/reboot decision recorded.
- [ ] Named sudo administrator works before disabling root/password SSH.
- [ ] Docker installed from official apt repository with selected version.
- [ ] Every installer command prerequisite passes before keyring, repository,
      apt, or filesystem mutation.
- [ ] Docker TCP socket absent; docker-group membership separately approved.
- [ ] UFW/DOCKER-USER/cloud-firewall interaction tested.
- [ ] Time synchronization and audit/log retention verified.

## Application boundary

- [ ] Public ingress is HTTPS only.
- [ ] React static assets and `/api/` are the only public application surface.
- [ ] DataHub UI remains private by default.
- [ ] GMS, MCP, MySQL, Kafka, OpenSearch, Docker socket, FastAPI, and internal
      frontend ports are not public.
- [ ] GMS adapter URL uses only the approved loopback/private-address allowlist;
      link-local and cloud-metadata addresses are rejected before token use.
- [ ] GMS and MCP URL ports are absent or valid integers from 1 through 65535;
      malformed and explicit empty ports fail before client initialization.
- [ ] CORS allows only the approved origin.
- [ ] Request size, timeouts, security headers, and rate-limit plan verified.
- [ ] Authentication and judge-access policy approved.

## Secrets and observability

- [ ] Tokens are server-side, mode restricted, least privilege, and rotatable.
- [ ] No token in Git, URLs, process arguments, diagnostics, or client bundle.
- [ ] Logs redact authorization headers, cookies, tool payloads, and URLs when
      sensitive.
- [ ] MCP service identity and DataHub policy scope verified.
- [ ] Runtime-verified Compose service inventory and credential-free health
      probe URLs recorded outside Git.
- [ ] Actual project service labels equal the expected inventory exactly; no
      duplicate, unexpected, orphaned, or unlabelled project containers.
- [ ] Private health probe hosts are exact members of the protected
      `DIC_APPROVED_HEALTH_HOSTS` allowlist; all URLs validate before any curl.
- [ ] Health curl processes remove every upper/lowercase proxy variable and use
      explicit `--noproxy '*'`; URL list entries contain no surrounding
      whitespace or empty separators.
- [ ] Mutation variable absent/false and write-back unavailable.

## Teardown

- [ ] Access disabled before cleanup.
- [ ] Required backup approved and encrypted.
- [ ] Project resource inventory reconciled before exact deletion approval.
- [ ] Tokens/certificates rotated or revoked.
- [ ] DNS, IP, disk, snapshot, VM, monitoring, and billing deletion verified.
