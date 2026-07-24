# Remote Operations Runbook

## Current boundary

This runbook is dry-run preparation. No VM, account, firewall, DNS,
certificate, DataHub service, or MCP process exists.

## Future order

1. Obtain explicit provider, quote, budget, VM, and execution approval.
2. Create default-deny cloud firewall and recovery access.
3. Provision the approved Ubuntu 24.04 LTS host.
4. Verify SSH host key, named administrator, CPU, memory, disk, architecture,
   swap, clock, listeners, and billing inventory.
5. Run the read-only remote prerequisite checker.
6. Before any host modification, verify `sudo`, `curl`, `apt-get`, `dpkg`,
   `dpkg-query`, `install`, `chmod`, `tee`, and `systemctl`; then check each
   conflicting Docker package independently.
7. Install pinned Docker from Docker's official apt repository only after
   approval.
8. Check out the reviewed repository commit without credentials.
9. Create server-side restricted environment/secret files.
10. Resolve and inspect the official v1.6.0 quickstart Compose configuration.
11. Verify Compose project labels, image tags/manifests, bindings, volumes, and
    rollback ownership before pull/start.
12. Obtain the separate DataHub startup approval.
13. Record the exact observed Compose service inventory, verified
    credential-free health probe URLs, and explicit RFC1918/IPv6 ULA health-host
    allowlist in the protected runtime environment.
14. Start only project-scoped services and wait within the configured timeout.
15. Require exact equality between expected and actual project service labels;
    reject missing, unexpected, duplicate, orphaned, or unlabelled project
    containers. Then require every expected container to run and every Docker
    health check to reach `healthy`; fail closed when a running service lacks a
    verified health path.
16. Validate the complete URL list before any request. Permit loopback directly
    and only explicitly allowlisted RFC1918/IPv6 ULA literals; reject public,
    link-local/metadata, special, malformed, credential-bearing, or unapproved
    destinations. Probe only after validation succeeds.
17. Record image identifiers and verify component health/listeners.
18. Install and inspect MCP only in a later separately approved checkpoint.
19. Deploy FastAPI, built React assets, and the reviewed HTTPS proxy boundary.

## Commands

Safe local checks:

```bash
make remote-check
make remote-plan
```

Future remote commands require a noncommitted environment file:

```bash
make remote-deploy REMOTE_ENV=/approved/path/remote.env
make remote-verify REMOTE_ENV=/approved/path/remote.env
make remote-stop REMOTE_ENV=/approved/path/remote.env
make remote-clean REMOTE_ENV=/approved/path/remote.env
```

These commands intentionally fail until approval and runtime gates are met.

## Stop, restart, diagnostics, and rollback

Stop/restart remain gated until quickstart resource ownership is observed;
they must never target unrelated Docker objects. Diagnostics list only
project-labelled container names/status and omit logs, environments, headers,
and inspect payloads. Cleanup requires reviewed project identifiers, two
approval variables, and exact interactive confirmation; no prune, nuke,
wildcard deletion, or provider deletion is implemented.

Rollback stops new access, disables mutation, captures redacted diagnostics,
backs up only after approval, stops owned services, rotates tokens, and deletes
billable resources only after a separate destructive approval.
