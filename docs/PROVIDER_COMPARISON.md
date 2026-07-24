# Provider Comparison

> Historical Sprint 4D paid-provider comparison. Sprint 8C Gate 1A supersedes
> its provider order: Google Cloud Free Trial is the primary free route,
> OVHcloud Public Cloud trial is the free fallback, paid OVHcloud B3-16 is the
> last resort, and AWS is not recommended for the preferred runtime.

## Scope and evidence rules

Research was performed on **2026-07-24** using official provider, DataHub, and
hackathon sources. Prices are current observations, not quotes or purchase
authorization. They can vary by region, currency, tax status, account,
capacity, image, storage, bandwidth, and public-IP choice.

The project screening baseline remains **4 or more vCPU, 16 GB RAM, 50 GB or
more SSD, Ubuntu LTS, Docker Engine, Docker Compose v2, SSH keys, a cloud
firewall, public IPv4, snapshots, and hourly billing**. This is a project
reliability margin over DataHub's documented tested quickstart allocation of
2 CPUs, 8 GB RAM, 2 GB swap, and 13 GB disk; it is not an official DataHub
minimum.

## Current comparison

| Provider and candidate | Published compute | Observed price | Storage/IP/billing notes | Credits and account risk | Assessment |
| --- | --- | ---: | --- | --- | --- |
| **OVHcloud B3-16** | 4 vCore, 16 GB, 100 GB NVMe | **$0.1208/hour** | Hourly use; shelving an hourly instance stops compute billing but retained snapshot/IP costs can remain. Public networking is listed with the instance; the exact selected-region IPv4, snapshot, bandwidth, and tax quote must be confirmed. | First eligible Public Cloud project may receive $200/€200 for one month; valid payment method and eligibility required, then normal billing resumes. Capacity and account validation remain gates. | **Selected primary.** Meets the baseline at the lowest verified all-in compute-and-local-disk rate among the x86 candidates reviewed. |
| **Hetzner CCX23, Nuremberg (`nbg1`)** | 4 dedicated AMD vCPU, 16 GB, 160 GB | **€0.1378/hour, €85.99/month cap**, excluding VAT and IPv4 | Primary IPv4 is €0.50/month excluding VAT; IPv6 is free. Powered-off servers remain billed until deletion. Snapshots, backups, and outbound overage are separate. Free stateful firewall and API/CLI are documented. | No generally available credit is included in this budget. New-account identity review, default limits, capacity, VAT, and currency are risks. | **Selected backup.** Dedicated CPU and predictable monthly cap are strong, but the June 2026 price increase makes it slightly less attractive than OVHcloud. |
| DigitalOcean General Purpose | 4 vCPU, 16 GiB, 50 GiB SSD, 5,000 GiB transfer | $0.1875/hour, $126/month cap | Powered-off Droplets remain billed until destruction. Snapshot is $0.06/GB-month; firewall is no-charge; outbound overage is $0.01/GiB. | No current official universal credit was accepted as a planning fact. Account review and regional capacity remain possible. | Reliable-looking reference, but materially more expensive. |
| Scaleway GP1-XS, Paris | 4 vCPU, 16 GB | €0.09282/hour, about €67.75/month | Published rate excludes storage and public IPv4; Flexible IP is €0.004/hour, snapshot is €0.000044/GB/hour, prices exclude tax, and the selected zone may differ. Egress and IPv6 are included. | No generally available credit was included. Exact 50+ GB block-storage rate, stop-state billing, quota, and generation availability require a console quote. | Potentially competitive, but not selected until full all-in price and stop/rebuild behavior are verified. |
| AWS EC2 `m7i.xlarge`, US East reference | 4 vCPU, 16 GiB | About $0.2016/hour compute, **estimate requiring a fresh calculator quote** | 50 GB gp3 is about $4/month in a region charging $0.08/GB-month; public IPv4 is $0.005/hour. Stopped instances cease compute billing but EBS and associated IPv4 can continue. Per-second Linux billing has a 60-second minimum. | New accounts may receive $100 plus up to $100 earned credit for six months. Free-plan service access and account quotas can limit the candidate size. | Strong operations, high complexity and cost; not a budget leader. |
| Google Compute Engine `e2-standard-4`, US Central reference | 4 vCPU, 16 GB | About $0.134/hour compute, **estimate requiring a fresh calculator quote** | Persistent disk, snapshot, external IPv4, and egress are separate. VM billing has a one-minute minimum then per-second billing; stopped VMs stop compute charges, while retained resources remain billable. | Eligible new customers may receive $300 for 90 days; identity/payment verification and anti-abuse limits apply. | Credit can make development inexpensive, but baseline cost and configuration are less predictable than OVHcloud. |
| Azure `Standard_D4as_v5`, France Central | 4 vCPU, 16 GiB | **$0.202/hour Linux consumption**, queried from the official Retail Prices API | Managed disk, snapshot, Standard public IP, and egress are separate. Only **Stopped (Deallocated)** stops compute billing; disks/networking can continue billing. | Eligible new accounts advertise $200 credit for 30 days; exact eligibility, quotas, and post-credit conversion require account verification. | Capable but cost and operational surface are higher. |
| Oracle Cloud Always Free A1 | Official current free-tenancy allowance totals 2 OCPU and 12 GB; 200 GB block storage is available | $0 within limits | Ubuntu and Arm are offered, but free capacity can be unavailable and home-region selection is permanent for Always Free resources. | A $300/30-day trial exists, but trial resources above Always Free limits can be reclaimed. Capacity reservations are unavailable to Free Tier accounts. | **Rejected.** Current Always Free CPU/RAM is below the project baseline and free capacity is unsuitable for judging reliability. |

The AWS and Google hourly values are comparison estimates rather than captured
provider quotes. They must not be used to authorize spending. Azure's value was
read from the official public Retail Prices API for France Central; it still
excludes ancillary resources and tax.

## Capability screening

All shortlisted paid providers document Linux virtual machines, Ubuntu images,
SSH-key access, public networking, security-group or cloud-firewall controls,
snapshots/images, and APIs or CLIs suitable for reproducible creation. Docker
Engine and Compose v2 are guest software installed from Docker's official
Ubuntu repository, not a provider-specific managed promise.

Provider documentation supports the required broad capabilities, but these
items remain runtime gates for the exact account, region, and SKU:

- quota and immediate capacity;
- Ubuntu LTS image ID and CPU architecture;
- actual public IPv4 allocation and price;
- firewall behavior around Docker-published ports;
- 50+ GB persistent storage performance;
- snapshot restore and IP/DNS change behavior;
- outbound allowance and registry-pull treatment; and
- tax, invoice currency, and payment authorization.

## Official sources

Accessed **2026-07-24**:

- [Hackathon rules](https://datahub.devpost.com/rules)
- [DataHub quickstart](https://docs.datahub.com/docs/quickstart)
- [DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets)
- [DigitalOcean billing](https://docs.digitalocean.com/products/droplets/details/pricing/)
- [Hetzner general-purpose cloud](https://www.hetzner.com/cloud/general-purpose)
- [Hetzner June 2026 price adjustment](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/)
- [Hetzner server overview](https://docs.hetzner.com/cloud/servers/overview/)
- [Hetzner billing FAQ](https://docs.hetzner.com/cloud/billing/faq/)
- [OVHcloud Public Cloud prices](https://www.ovhcloud.com/en/public-cloud/prices/)
- [OVHcloud shelve/pause behavior](https://help.ovhcloud.com/csm/en-public-cloud-compute-shelve-pause-instance?id=kb_article_view&sysparm_article=KB0051230)
- [OVHcloud Public Cloud free trial](https://www.ovhcloud.com/en/public-cloud/free-trial/)
- [Scaleway Virtual Instances pricing](https://www.scaleway.com/en/pricing/virtual-instances/)
- [AWS EC2 pricing](https://aws.amazon.com/ec2/pricing/)
- [AWS stopped-instance costs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/how-ec2-instance-stop-start-works.html)
- [AWS EBS pricing](https://aws.amazon.com/ebs/pricing/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [Google Compute Engine pricing](https://cloud.google.com/products/compute/pricing)
- [Google E2 machine types](https://docs.cloud.google.com/compute/docs/general-purpose-machines)
- [Google Cloud trial](https://cloud.google.com/signup-faqs)
- [Azure Retail Prices API](https://prices.azure.com/api/retail/prices)
- [Azure VM billing states](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing)
- [Azure account offers](https://azure.microsoft.com/en-us/pricing/purchase-options/azure-account)
- [Oracle Free Tier](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm)
- [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)
