#!/usr/bin/env python3
"""Validate all remote health URLs before the shell sends any request."""

from __future__ import annotations

import ipaddress
import sys
from urllib.parse import urlsplit


RFC1918 = tuple(
    ipaddress.ip_network(value)
    for value in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
IPV6_ULA = ipaddress.ip_network("fc00::/7")


def private_project_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    if isinstance(address, ipaddress.IPv4Address):
        return any(
            address in network
            and address not in {network.network_address, network.broadcast_address}
            for network in RFC1918
        )
    return address in IPV6_ULA


def canonical_approved_hosts(raw: str) -> frozenset[str]:
    approved: set[str] = set()
    if not raw:
        return frozenset()
    for value in raw.split(","):
        candidate = value.strip()
        if not candidate:
            raise ValueError("approved health hosts contain an empty entry")
        try:
            address = ipaddress.ip_address(candidate)
        except ValueError as error:
            raise ValueError("approved health hosts must be RFC1918 or IPv6 ULA literals") from error
        if not private_project_address(address):
            raise ValueError("approved health host is not RFC1918 or IPv6 ULA")
        approved.add(address.compressed)
    return frozenset(approved)


def validate_url(raw: str, approved: frozenset[str]) -> str:
    if not raw or raw != raw.strip():
        raise ValueError("health URL is empty or whitespace padded")
    try:
        parsed = urlsplit(raw)
        host = parsed.hostname
        port = parsed.port
    except ValueError as error:
        raise ValueError("health URL is malformed") from error
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("health URL must use HTTP(S) with a host")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("health URL must not contain user information")
    if parsed.query or parsed.fragment:
        raise ValueError("health URL must not contain a query or fragment")
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("health URL port is invalid")

    normalized_host = host.lower()
    if normalized_host == "localhost":
        return raw
    try:
        address = ipaddress.ip_address(normalized_host)
    except ValueError as error:
        raise ValueError("health URL DNS hosts other than localhost are not allowed") from error
    if address.is_loopback:
        return raw
    if private_project_address(address) and address.compressed in approved:
        return raw
    raise ValueError("health URL host is not an approved private or loopback endpoint")


def main() -> int:
    lines = sys.stdin.read().splitlines()
    if len(lines) != 2:
        print("health URL validation input must contain exactly two lines", file=sys.stderr)
        return 2
    try:
        approved = canonical_approved_hosts(lines[1])
        urls = lines[0].split(",")
        if not urls or any(not value for value in urls):
            raise ValueError("health URL list contains an empty entry")
        if len(urls) != len(set(urls)):
            raise ValueError("health URL list contains a duplicate")
        validated = tuple(validate_url(value, approved) for value in urls)
    except ValueError as error:
        print(f"health URL validation error: {error}", file=sys.stderr)
        return 2
    sys.stdout.write("\n".join(validated))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
