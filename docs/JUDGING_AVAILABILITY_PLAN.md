# Judging Availability Plan

## Verified schedule

Official hackathon rules were accessed on **2026-07-24**:

- submission deadline: **2026-08-10 at 5:00 PM EDT**;
- judging: **2026-08-17 at 10:00 AM EDT through 2026-08-31 at 5:00 PM EDT**;
- winners expected: **approximately 2026-09-08 at 2:00 PM EDT**.

The rules require an easy-access project URL and a consistently runnable
project on its intended platform. They do not state a precise uptime SLA or
explicitly say whether private test credentials may be supplied to judges.
Therefore, credentials are an unresolved organizer question, not an assumed
permission.

Source: [DataHub Hackathon official rules](https://datahub.devpost.com/rules).

## Availability window

Planning target:

- build the clean final VM by **2026-08-07**;
- complete recovery, security, accessibility, and end-to-end checks before
  **2026-08-10 5:00 PM EDT**;
- keep the application continuously available through judging;
- retain the unchanged environment through **2026-09-09** as a one-day
  post-announcement buffer; and
- tear down after explicit approval.

This 33-day window is a reliability choice, not an official rule.

## Access policy

- publish one TLS-protected application URL;
- keep DataHub UI/GMS, MCP, databases, Kafka, OpenSearch, Docker, SSH, and
  administrative endpoints non-public;
- prefer a constrained judge account if organizers confirm credentials are
  acceptable;
- if credentials are not acceptable, provide an anonymous, rate-limited,
  least-privilege application path that cannot perform write-back without an
  explicit approved demo control;
- never place credentials in Devpost text, screenshots, source, logs, or Git;
- test the judge journey in a clean browser with no operator session; and
- provide repository setup instructions as recovery evidence, not as a
  substitute for the primary live demo.

## Readiness gates

Before submission:

1. verify DataHub OSS `v1.6.0`, MCP, backend, and frontend are the actual
   running path;
2. prove runtime evidence originates from DataHub/MCP;
3. complete the NYC Taxi planted freshness incident end to end;
4. verify security, secrets, accessibility, write approval/read-back, and
   disconnected dependency behavior;
5. run clean-install, one-command, smoke, E2E, and submission checks;
6. test VM reboot and application restart;
7. test backup restoration on a separately approved disposable environment;
8. confirm DNS/TLS expiry exceeds 2026-09-09;
9. confirm provider billing alerts and available budget; and
10. freeze reviewed versions and configuration.

## Monitoring and incident response

- use secret-free external HTTPS health checks;
- monitor disk, memory, container health, certificate expiry, and provider
  status;
- retain redacted diagnostics and a restart runbook;
- do not perform discretionary upgrades during judging;
- for failure, restore service on the same final VM first;
- if the provider/VM is irrecoverable, use reviewed configuration to rebuild
  on the backup provider, update DNS, rerun all health/smoke checks, and record
  the change; and
- never claim a fixture or screenshot as a live DataHub-backed recovery.

## Judging risks

- organizer response on credentials may require an access redesign;
- a single VM is a single point of failure;
- provider quota/capacity may delay initial or backup creation;
- the DataHub quickstart is documented for development, not production;
- the 16 GB planning baseline is not runtime-proven for the complete stack;
- DNS propagation can slow provider failover; and
- trial expiry or credit exhaustion must never terminate the judging runtime.

## Teardown

After the approved 2026-09-09 buffer:

- capture public-safe submission evidence and the final cost;
- revoke judge, cloud, DataHub, MCP, model-provider, and deployment
  credentials;
- remove DNS/application access;
- delete the VM and separately billed disks, snapshots, IPs, backups, and
  monitoring resources only with explicit approval;
- verify the provider inventory and billing dashboard show no unintended
  resources; and
- record deletion and rotation completion.
