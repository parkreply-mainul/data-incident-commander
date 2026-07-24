# Remote Deployment Package

This provider-neutral package is a reviewed future execution boundary for one
Ubuntu LTS VM. It does not provision infrastructure and has not been executed
on a remote host.

`env/remote.env.example` contains public placeholders only. Copy it outside Git
to a mode-0600 runtime file and replace placeholders after explicit
provisioning approval. Never place tokens in command arguments.

Local planning commands:

```bash
make remote-check
make remote-plan
```

Gate 2 uses the standalone, read-only base-host validator:

```bash
bash deploy/scripts/check_gate2_base_host.sh \
  --expected-hostname dic-runtime-01
```

It requires only a pristine Ubuntu 24.04 base host and treats Docker and
project workloads as failures. It accepts absent swap as deferred, performs no
download, and changes nothing. OS Login, IAP, IAM, external-IP absence, and
effective firewall policies remain console-side checks. The script can be
streamed through the approved IAP session without a repository checkout.
`make gate2-host-check` provides the same entry point when
`GATE2_EXPECTED_HOSTNAME` is set.

Gate 3 and later use `check_remote_prerequisites.sh` only after approved
package and Docker installation. That checker requires Docker, Compose, curl,
jq, git, and OpenSSL. Gate 2 must not attempt to satisfy it.

Execution commands remain fail-closed without a configured remote environment
and explicit approval variables. The DataHub quickstart path additionally
requires runtime verification that its generated Compose resources are
project-scoped before startup is permitted.

The Docker installer checks its Ubuntu gate and all commands needed for
pre-install work before conflict inspection or filesystem/repository changes.
Missing prerequisites stop safely; conflicting packages are reported but never
removed automatically.

Verification also requires a runtime-observed, explicit Compose service
inventory. The sorted actual service-label multiset must equal the sorted
expected inventory: missing, unexpected, duplicate, orphaned, or unlabelled
project containers fail verification. Containers outside the configured
Compose project are ignored. Every expected service must then run;
Docker-health-enabled containers must reach `healthy`. `starting` waits within
a bounded timeout, while unhealthy/non-running containers fail. A running
container without a health check fails closed until a verified service-level
probe is configured.
Container health alone never establishes full DataHub readiness:
credential-free application/GMS/frontend probe URLs must first be observed and
recorded in the protected runtime environment.

All health URLs are validated before the first request. Loopback is allowed.
RFC1918 and IPv6 ULA literals require exact canonical membership in
`DIC_APPROVED_HEALTH_HOSTS`. Link-local/metadata, CGNAT, special, public,
userinfo-bearing, fragmented, malformed, and unapproved hosts fail before
`curl`. URL entries are never whitespace-normalized or repaired. Valid probes
run with all upper/lowercase proxy variables removed and curl
`--noproxy '*'`, forcing a direct connection to the validated destination.

The `compose/`, `systemd/`, `nginx/`, and `security/` directories document
future deployment boundaries. They do not claim production readiness.
