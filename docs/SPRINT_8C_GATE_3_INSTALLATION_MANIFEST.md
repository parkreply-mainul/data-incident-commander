# Sprint 8C Gate 3 Installation Manifest

**Status: PREPARED, NOT APPROVED FOR EXECUTION.**

Accessed sources: 2026-07-25. No command in this document has been executed on
the VM during manifest preparation.

## Verified starting state

- Google Compute Engine `e2-standard-4`: 4 vCPU and 16 GB RAM.
- Ubuntu 24.04 LTS amd64 is running.
- SSH remains through IAP.
- An ephemeral external IPv4 is attached temporarily because outbound internet
  access was unavailable without it.
- No public ingress rule permits SSH, HTTP, HTTPS, DataHub, MCP, databases, or
  application services.
- `apt update` and `apt upgrade` completed.
- Git, Docker Engine, Docker Compose, DataHub, and MCP are absent.
- Local `make remote-check` and `make remote-plan` passed.
- DataHub remains pinned to `v1.6.0`.

These are operator-reported runtime facts. Reconfirm them before execution.

## Temporary Gate 3 network exception

The ephemeral external IPv4 is approved for consideration only as temporary
outbound reachability for Ubuntu packages, Docker's official apt repository,
and later separately approved image downloads. An external address is not
intrinsically outbound-only; effective ingress firewall policy must enforce the
boundary.

Rules:

- SSH continues exclusively through IAP.
- Add no public ingress rule.
- TCP 22 is not opened to the public address.
- HTTP, HTTPS, DataHub, MCP, backend, frontend, database, Kafka, and search
  ports remain closed.
- Before every Gate 3 action, verify the effective firewall still has no
  unintended inherited ingress allow.
- Remove the external IPv4 immediately after deployment work completes or
  after a separately approved private-outbound design such as Cloud NAT is
  verified.
- Removing or replacing the address is a separately approved cloud mutation.
- Do not reserve or promote the ephemeral address to static.

The temporary address adds an official list-price reference of USD 0.005 per
running VM-hour: approximately USD 0.12 per 24 hours or USD 0.84 per seven
days, before tax/currency treatment. Inbound data transfer is listed at no
charge; small outbound requests and any other regional SKU remain subject to
the live billing console. Existing compute and disk charges are unchanged by
this exception.

Sources:

- [Google Cloud external IP configuration](https://cloud.google.com/compute/docs/ip-addresses/configure-static-external-ip-address)
- [Google Cloud external IPv4 price change](https://cloud.google.com/vpc/pricing-announce-external-ips)
- [Google Cloud VPC pricing](https://cloud.google.com/vpc/pricing)
- [Google Cloud VM networking](https://cloud.google.com/compute/docs/networking/network-overview)

## Official Docker package selection

Docker officially supports Ubuntu Noble 24.04 LTS on amd64 and documents the
official apt-repository installation used by
`deploy/scripts/install_docker_ubuntu.sh`.

The following records were observed in Docker's official Noble stable amd64
`Packages.gz` on 2026-07-25:

| Package | Selected/observed apt version |
|---|---|
| `docker-ce` | `5:29.6.2-1~ubuntu.24.04~noble` |
| `docker-ce-cli` | `5:29.6.2-1~ubuntu.24.04~noble` |
| `containerd.io` | `2.2.6-1~ubuntu.24.04~noble` |
| `docker-buildx-plugin` | `0.35.0-1~ubuntu.24.04~noble` |
| `docker-compose-plugin` | `5.3.1-1~ubuntu.24.04~noble` |

The exact reviewed installer input is:

```text
DIC_DOCKER_VERSION=5:29.6.2-1~ubuntu.24.04~noble
```

The installer pins `docker-ce` and `docker-ce-cli` to this value. It does not
pin containerd, Buildx, or Compose; apt resolves those three from the stable
repository at execution time. Therefore the three observed versions above are
expected results, not immutable installer inputs. If repository metadata has
changed, stop and review the resolved versions rather than silently accepting
different packages.

Sources:

- [Docker Engine installation on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [Docker Noble stable amd64 metadata](https://download.docker.com/linux/ubuntu/dists/noble/stable/binary-amd64/)
- [Docker Noble stable amd64 package pool](https://download.docker.com/linux/ubuntu/dists/noble/pool/stable/amd64/)

## Approval boundaries

Each boundary requires a distinct approval:

1. **Package approval:** install only the preflight packages listed below.
2. **Swap approval:** create and persist `/swapfile`.
3. **Transfer approval:** use the operator's existing local Google Cloud
   session and IAP to copy a commit-derived bundle.
4. **Docker approval:** set the protected approval flags and run the reviewed
   installer.
5. **Post-install inspection approval:** run the remote prerequisite checker.
6. **External-IP removal approval:** remove the temporary address when its
   approved work is complete.

None authorizes DataHub image pulls, DataHub startup, MCP installation,
mutation, public application ingress, Docker group membership, or a Docker TCP
listener.

## Exact execution sequence

The following is the proposed sequence. It remains unexecuted. Values in angle
brackets are private operator inputs and must not be committed.

### 0. Reconfirm local reviewed state

From the repository root:

```bash
make remote-check
make remote-plan
git status --short
git rev-parse HEAD
```

Expected: both Make targets pass, status is empty, and the reviewed commit is
recorded.

### 1. Verify the remote base state through IAP

Connect with the operator's existing Google Cloud CLI session:

```bash
gcloud compute ssh <VM_NAME> \
  --project=<PROJECT_ID> \
  --zone=<ZONE> \
  --tunnel-through-iap
```

On the VM, run read-only checks:

```bash
source /etc/os-release
printf 'os=%s version=%s codename=%s\n' "$ID" "$VERSION_ID" "$VERSION_CODENAME"
uname -m
getconf _NPROCESSORS_ONLN
awk '/MemTotal|SwapTotal/ {print}' /proc/meminfo
df -h /
command -v docker git || true
sudo ss -lntup
```

Expected: Ubuntu `24.04`/`noble`, amd64/x86_64, 4 CPUs, guest-visible memory
consistent with the approved 16-GB VM, no Docker/Git, no swap yet, and no
unexpected public listener.

Console-side checks must separately confirm IAP-only SSH, no public ingress,
the ephemeral (not reserved) external IPv4, and unchanged trial/budget state.

### 2. Install only Gate 3 preflight packages

After package approval:

```bash
sudo apt-get update
sudo apt-get install --yes ca-certificates curl jq git openssl
```

`sudo`, `apt-get`, `dpkg`, `dpkg-query`, `install`, `chmod`, `tee`,
`systemctl`, `fallocate`, `mkswap`, and `swapon` are expected base-image
commands. Confirm them before mutation; do not install an unreviewed package if
one is absent:

```bash
for command in sudo apt-get dpkg dpkg-query install chmod tee systemctl \
  fallocate mkswap swapon; do
  command -v "$command" || exit 1
done
for command in curl jq git openssl; do
  "$command" --version >/dev/null || exit 1
done
```

Expected: all commands exit zero. No Docker package is installed.

### 3. Create and verify 2 GiB swap

After swap approval:

```bash
test ! -e /swapfile
sudo fallocate -l 2050M /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
grep -qE '^/swapfile[[:space:]]+none[[:space:]]+swap[[:space:]]' /etc/fstab ||
  printf '/swapfile none swap sw 0 0\n' | sudo tee -a /etc/fstab >/dev/null
swap_kib="$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)"
test "$swap_kib" -ge 2097152
swapon --show
```

Expected: `/swapfile` is active, mode `0600`, persisted once in `/etc/fstab`,
and `SwapTotal` is at least `2097152` KiB. Any pre-existing `/swapfile` stops
the sequence for manual inspection.

### 4. Transfer only reviewed deployment files

Create a bundle from the reviewed commit locally; do not copy `.git`, local
environment files, credentials, or the working tree:

```bash
REVIEWED_COMMIT="$(git rev-parse HEAD)"
GATE3_BUNDLE="/tmp/dic-gate3-${REVIEWED_COMMIT}.tar.gz"
git archive --format=tar.gz --output="$GATE3_BUNDLE" "$REVIEWED_COMMIT" \
  deploy/scripts/common.sh \
  deploy/scripts/install_docker_ubuntu.sh \
  deploy/scripts/check_remote_prerequisites.sh
shasum -a 256 "$GATE3_BUNDLE"
gcloud compute scp \
  --project=<PROJECT_ID> \
  --zone=<ZONE> \
  --tunnel-through-iap \
  "$GATE3_BUNDLE" <VM_NAME>:/tmp/
```

On the VM:

```bash
install -d -m 0700 "$HOME/dic-gate3"
tar -xzf "/tmp/dic-gate3-<REVIEWED_COMMIT>.tar.gz" -C "$HOME/dic-gate3"
sha256sum "/tmp/dic-gate3-<REVIEWED_COMMIT>.tar.gz"
bash -n "$HOME/dic-gate3/deploy/scripts/"*.sh
```

Compare the local and remote SHA-256 values out of band. The archive contains
only committed reviewed scripts, exposes no Git credential, and changes no Git
history.

Create a protected runtime environment file on the VM only:

```bash
install -m 0600 /dev/null "$HOME/dic-gate3/remote.env"
printf '%s\n' \
  'DIC_PROJECT_NAME=data-incident-commander' \
  'DIC_DOCKER_VERSION=5:29.6.2-1~ubuntu.24.04~noble' \
  'DIC_REMOTE_APPROVED=yes' \
  'DIC_REMOTE_EXECUTION_APPROVED=yes' \
  'DIC_EXCLUSIVE_PORTS=80,443' \
  >"$HOME/dic-gate3/remote.env"
```

The two `yes` values may be written only after their corresponding approval.
The file contains no token.

### 5. Run the reviewed Docker installer

First rerun its non-mutating plan:

```bash
bash "$HOME/dic-gate3/deploy/scripts/install_docker_ubuntu.sh" \
  --env "$HOME/dic-gate3/remote.env" \
  --plan
```

After Docker installation approval:

```bash
bash "$HOME/dic-gate3/deploy/scripts/install_docker_ubuntu.sh" \
  --env "$HOME/dic-gate3/remote.env"
```

Expected:

- conflicting Docker packages are absent;
- Docker's official Noble stable repository and key are configured;
- Engine and CLI install at `5:29.6.2-1~ubuntu.24.04~noble`;
- the daemon is active;
- `sudo docker version` succeeds;
- `sudo docker compose version` succeeds;
- no user is added to the Docker group; and
- no image is pulled.

Verify exact resolved packages:

```bash
dpkg-query -W -f='${Package}\t${Version}\n' \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
  docker-compose-plugin
sudo docker version
sudo docker compose version
sudo docker info --format '{{.SecurityOptions}}'
```

Engine/CLI mismatch is a failure. A containerd, Buildx, or Compose version
different from the observed table requires review before continuing.

### 6. Run the Gate 3 remote prerequisite checker

```bash
bash "$HOME/dic-gate3/deploy/scripts/check_remote_prerequisites.sh" \
  --env "$HOME/dic-gate3/remote.env"
```

Expected: Ubuntu, CPU, memory, disk, Docker, Compose, curl, jq, Git, OpenSSL,
daemon, swap visibility, NTP, and exclusive-port checks pass. The operator
remains outside the Docker group, so the checker may use noninteractive sudo.

Stop after this check. Do not pull or start DataHub and do not install MCP.

## Rollback

Rollback is separately approved and project/host-scoped.

### Docker packages and repository

```bash
sudo apt-get purge --yes \
  docker-ce docker-ce-cli containerd.io docker-buildx-plugin \
  docker-compose-plugin docker-ce-rootless-extras
sudo rm -f /etc/apt/sources.list.d/docker.sources
sudo rm -f /etc/apt/keyrings/docker.asc
sudo apt-get update
```

Do not delete `/var/lib/docker` or `/var/lib/containerd` automatically. At this
gate no image or container should exist; inspect both paths before any
separately approved deletion.

### Swap

```bash
swap_before_kib="$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)"
if swapon --show=NAME --noheadings | grep -Fxq /swapfile; then
  sudo swapoff /swapfile
fi
sudo sed -i '\|^/swapfile[[:space:]][[:space:]]*none[[:space:]][[:space:]]*swap[[:space:]]|d' \
  /etc/fstab
sudo rm -f /swapfile
! grep -Eq '^/swapfile[[:space:]]+none[[:space:]]+swap[[:space:]]' /etc/fstab
! swapon --show=NAME --noheadings | grep -Fxq /swapfile
swap_after_kib="$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)"
test "$swap_after_kib" -le "$swap_before_kib"
printf 'SwapTotal before rollback: %s KiB; after rollback: %s KiB\n' \
  "$swap_before_kib" "$swap_after_kib"
```

This removes only an entry whose first three fields are `/swapfile`, `none`,
and `swap`. Other swap devices or files remain untouched. The active-state
guard, exact-entry deletion, and `rm -f` make a repeated approved rollback
idempotent.

### Transferred files

After confirming the exact paths:

```bash
rm -f "/tmp/dic-gate3-<REVIEWED_COMMIT>.tar.gz"
rm -rf "$HOME/dic-gate3"
```

These deletion commands require separate approval. Never use a wildcard or
broader target.

## Remaining execution gates

Gate 3 installation remains **NO-GO** until:

- exact private project, zone, VM, and operator inputs are supplied;
- the effective ingress firewall and temporary ephemeral-IP classification are
  reconfirmed;
- current official package metadata still contains the selected Engine pin;
- the live console cost/credit impact is accepted;
- package, swap, transfer, Docker, inspection, and later IP-removal approvals
  are granted separately; and
- the remote prerequisite check's 16-GB guest-memory handling is confirmed
  against the actual `MemTotal` before relying on it as an acceptance gate.

DataHub startup, MCP installation, and mutation remain unapproved.
