# Remote Security Boundary

- Cloud and host firewalls default deny.
- Only SSH from approved administrator sources and public HTTPS are candidates
  for ingress.
- DataHub UI is private by default. GMS, MCP, MySQL, Kafka, OpenSearch, Docker
  socket, FastAPI, and Vite/internal frontend ports are never public.
- SSH uses named administrators and keys. Password and root login are disabled
  only after recovery access is verified.
- Runtime tokens live in server-side restricted files or an approved secret
  store. Logs redact secrets, URLs containing credentials, headers, and tool
  payloads.
- CORS is an explicit application-origin allowlist. Request size, timeouts,
  security headers, and later rate limits are enforced at the proxy.
- Teardown includes project-scoped resource deletion, token rotation, DNS and
  certificate cleanup, and billing verification after explicit approval.

Docker-published ports can bypass UFW rules; Docker's `DOCKER-USER` chain and
the cloud firewall must be verified together before exposure.
