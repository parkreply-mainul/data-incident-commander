from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from data_incident_commander.integrations.datahub.capabilities import (
    CapabilityInventory,
    CapabilityName,
    DocumentationStatus,
    McpCapability,
    RuntimeStatus,
    documented_inventory,
)
from data_incident_commander.integrations.datahub.config import DataHubMcpConfig


NOW = datetime(2026, 7, 24, 12, tzinfo=timezone.utc)


def config(**updates) -> DataHubMcpConfig:
    values = {
        "gms_url": "http://datahub-gms:8080",
        "mcp_server_version": "0.5.0",
        "environment_name": "test",
    }
    values.update(updates)
    return DataHubMcpConfig(**values)


def test_configuration_is_strict_and_side_effect_free():
    value = config()
    assert value.mutation_enabled is False
    assert value.mode == "stdio"
    assert value.token_value({}) is None
    assert value.public_configuration()["gms_host_class"] == "private"


def test_stdio_command_pins_exact_server_package_version():
    value = config(mcp_server_version="0.6.0")

    assert value.stdio_command == (
        "uvx",
        "mcp-server-datahub==0.6.0",
        "--transport",
        "stdio",
    )
    assert "latest" not in " ".join(value.stdio_command)


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://10.0.0.1:8080",
        "http://10.255.255.254:8080",
        "http://172.16.0.1:8080",
        "http://172.31.255.254:8080",
        "http://192.168.0.1:8080",
        "http://192.168.255.254:8080",
        "http://[::1]:8080",
        "http://[fc00::1]:8080",
        "http://[fdff:ffff::1]:8080",
    ],
)
def test_configuration_accepts_only_explicit_local_ip_categories(url):
    assert config(gms_url=url).gms_url == url


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254",
        "http://169.254.20.10",
        "http://[fe80::1]",
        "http://100.64.0.1",
        "http://224.0.0.1",
        "http://[ff02::1]",
        "http://0.0.0.0",
        "http://[::]",
        "http://192.0.2.1",
        "http://198.51.100.1",
        "http://203.0.113.1",
        "http://240.0.0.1",
        "http://8.8.8.8",
        "https://public.example.com",
    ],
)
def test_configuration_rejects_special_public_and_metadata_hosts(url):
    with pytest.raises(ValidationError, match="RFC1918") as error:
        config(gms_url=url)
    assert "DATAHUB_GMS_TOKEN" not in str(error.value)


def test_configuration_error_redacts_url_credentials():
    secret = "should-never-appear"
    with pytest.raises(ValidationError) as error:
        config(gms_url=f"https://user:{secret}@localhost:8080")
    assert secret not in str(error.value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("gms_url", "not-a-url"),
        ("gms_url", "https://user:secret@example.com"),
        ("gms_url", "https://public.example.com"),
        ("gms_url", "http://0.0.0.0:8080"),
        ("token_env_var", "token"),
        ("mcp_server_version", "latest"),
        ("mcp_command", ("uvx", "DATAHUB_GMS_TOKEN=secret")),
    ],
)
def test_configuration_rejects_unsafe_or_ambiguous_values(field, value):
    with pytest.raises(ValidationError):
        config(**{field: value})


def test_configuration_never_stores_or_prints_token_value():
    value = config(token_env_var="DIC_TEST_TOKEN")
    assert value.token_value({"DIC_TEST_TOKEN": "super-secret-token"}) == "super-secret-token"
    assert "super-secret-token" not in repr(value)
    assert "super-secret-token" not in str(value.public_configuration())


def test_public_env_example_token_reference_resolves_canonical_variable():
    repository_root = Path(__file__).resolve().parents[3]
    entries = dict(
        line.split("=", 1)
        for line in (repository_root / ".env.example").read_text().splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    assert entries["DATAHUB_GMS_TOKEN_ENV"] == "DATAHUB_GMS_TOKEN"
    assert entries["DATAHUB_GMS_TOKEN"] == ""
    assert "DATAHUB_TOKEN" not in entries

    secret = "controlled-test-token"
    value = config(token_env_var=entries["DATAHUB_GMS_TOKEN_ENV"])
    assert value.token_value({"DATAHUB_GMS_TOKEN": secret}) == secret
    assert secret not in repr(value)
    assert secret not in str(value.public_configuration())


def test_mutation_cannot_be_enabled_from_configuration():
    with pytest.raises(ValidationError, match="mutation"):
        config(mutation_enabled=True)


def test_endpoint_mode_requires_safe_endpoint():
    with pytest.raises(ValidationError):
        config(mode="endpoint")
    with pytest.raises(ValidationError):
        config(mode="endpoint", mcp_endpoint="http://public.example.com/mcp")
    assert config(mode="endpoint", mcp_endpoint="https://mcp.internal/mcp").mode == "endpoint"


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost:8081/mcp",
        "http://127.0.0.1:8081/mcp",
        "http://127.20.30.40:8081/mcp",
        "http://[::1]:8081/mcp",
        "https://[fc00::1]:8081/mcp",
    ],
)
def test_endpoint_mode_accepts_loopback_http_and_private_https(endpoint):
    assert config(mode="endpoint", mcp_endpoint=endpoint).mcp_endpoint == endpoint


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://10.0.0.1:8081/mcp",
        "http://192.168.1.1:8081/mcp",
        "http://[fc00::1]:8081/mcp",
        "http://169.254.169.254/mcp",
        "http://[fe80::1]/mcp",
        "http://public.example.com/mcp",
        "http://[::1",
    ],
)
def test_endpoint_mode_rejects_nonloopback_http_and_malformed_ipv6(endpoint):
    with pytest.raises(ValidationError):
        config(mode="endpoint", mcp_endpoint=endpoint)


@pytest.mark.parametrize("port", [None, 1, 443, 65535])
def test_gms_url_accepts_absent_and_valid_ports(port):
    suffix = "" if port is None else f":{port}"
    value = f"http://localhost{suffix}"
    assert config(gms_url=value).gms_url == value


@pytest.mark.parametrize("port", [None, 1, 443, 65535])
def test_mcp_endpoint_accepts_absent_and_valid_ports(port):
    suffix = "" if port is None else f":{port}"
    value = f"http://localhost{suffix}/mcp"
    assert config(mode="endpoint", mcp_endpoint=value).mcp_endpoint == value


@pytest.mark.parametrize(
    "port",
    ["0", "65536", "bad", "+1", "-1", " 80", "%2080", ""],
)
@pytest.mark.parametrize("field", ["gms_url", "mcp_endpoint"])
def test_integration_urls_reject_malformed_or_out_of_range_ports(field, port):
    value = f"http://localhost:{port}"
    updates = (
        {"gms_url": value}
        if field == "gms_url"
        else {"mode": "endpoint", "mcp_endpoint": value}
    )
    with pytest.raises(ValidationError) as error:
        config(**updates)
    message = str(error.value)
    assert "invalid URL or port syntax" in message or "port" in message
    assert "Port could not be cast" not in message


@pytest.mark.parametrize("field", ["gms_url", "mcp_endpoint"])
def test_bracketed_ipv6_accepts_valid_port_and_rejects_malformed_port(field):
    valid = "http://[::1]:65535"
    updates = (
        {"gms_url": valid}
        if field == "gms_url"
        else {"mode": "endpoint", "mcp_endpoint": valid}
    )
    assert config(**updates)

    malformed = "http://[::1]:bad"
    updates = (
        {"gms_url": malformed}
        if field == "gms_url"
        else {"mode": "endpoint", "mcp_endpoint": malformed}
    )
    with pytest.raises(ValidationError, match="invalid URL or port syntax"):
        config(**updates)


@pytest.mark.parametrize("field", ["gms_url", "mcp_endpoint"])
def test_integration_urls_reject_malformed_bracketed_ipv6(field):
    value = "http://[::1"
    updates = (
        {"gms_url": value}
        if field == "gms_url"
        else {"mode": "endpoint", "mcp_endpoint": value}
    )
    with pytest.raises(ValidationError, match="invalid URL or port syntax"):
        config(**updates)


@pytest.mark.parametrize("field", ["gms_url", "mcp_endpoint"])
def test_port_validation_errors_are_redacted_and_parser_safe(field):
    secret = "port-secret-must-not-appear"
    value = f"http://user:{secret}@localhost:bad"
    updates = (
        {"gms_url": value}
        if field == "gms_url"
        else {"mode": "endpoint", "mcp_endpoint": value}
    )
    with pytest.raises(ValidationError) as error:
        config(**updates)
    message = str(error.value)
    assert secret not in message
    assert "Port could not be cast" not in message
    assert "urllib" not in message


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("maximum_lineage_depth", 0),
        ("maximum_lineage_depth", 21),
        ("maximum_lineage_nodes", 0),
        ("maximum_lineage_nodes", 10_001),
        ("request_timeout_seconds", 0),
        ("request_timeout_seconds", 301),
    ],
)
def test_operational_limits_are_bounded(field, value):
    with pytest.raises(ValidationError):
        config(**{field: value})


def test_documented_inventory_is_never_runtime_observed():
    inventory = documented_inventory("0.5.0")
    assert inventory.observed_at is None
    assert not inventory.required_reads_verified
    assert all(item.runtime_status is RuntimeStatus.UNOBSERVED for item in inventory.capabilities)
    assert all(not item.enabled for item in inventory.capabilities)


def test_observed_capability_requires_timestamp():
    with pytest.raises(ValidationError, match="verified_at"):
        McpCapability(
            name=CapabilityName.ASSET_SEARCH,
            documentation_status=DocumentationStatus.DOCUMENTED,
            runtime_status=RuntimeStatus.OBSERVED,
            enabled=True,
            read_only=True,
            source="controlled-test-inventory",
            version="0.5.0",
            notes="Observed only by this contract test.",
        )


def test_duplicate_capabilities_are_rejected():
    capability = McpCapability(
        name=CapabilityName.ASSET_SEARCH,
        documentation_status=DocumentationStatus.DOCUMENTED,
        read_only=True,
        source="official docs",
        version="0.5.0",
        notes="Unobserved.",
    )
    with pytest.raises(ValidationError, match="unique"):
        CapabilityInventory(server_version="0.5.0", capabilities=(capability, capability))


def test_capability_inventory_order_is_deterministic():
    baseline = documented_inventory("0.5.0")
    reversed_inventory = CapabilityInventory(
        server_version="0.5.0",
        capabilities=tuple(reversed(baseline.capabilities)),
    )
    assert reversed_inventory == baseline


def test_unobserved_inventory_cannot_claim_an_observation_timestamp():
    with pytest.raises(ValidationError, match="unobserved"):
        CapabilityInventory(
            server_version="0.5.0",
            observed_at=NOW,
            capabilities=documented_inventory("0.5.0").capabilities,
        )


def observed_inventory() -> CapabilityInventory:
    required = (
        CapabilityName.ASSET_SEARCH,
        CapabilityName.ENTITY_INSPECTION,
        CapabilityName.UPSTREAM_LINEAGE,
        CapabilityName.DOWNSTREAM_LINEAGE,
        CapabilityName.LINEAGE_PATHS,
        CapabilityName.OWNERSHIP_CONTEXT,
    )
    return CapabilityInventory(
        server_version="0.5.0",
        observed_at=NOW,
        capabilities=tuple(
            McpCapability(
                name=name,
                documentation_status=DocumentationStatus.DOCUMENTED,
                runtime_status=RuntimeStatus.OBSERVED,
                enabled=True,
                read_only=True,
                source="controlled-test-inventory",
                version="0.5.0",
                verified_at=NOW,
                notes="Contract double; not a live runtime claim.",
            )
            for name in required
        ),
    )


def test_explicit_observed_inventory_can_satisfy_required_read_contract():
    assert observed_inventory().required_reads_verified


def observed_capability(
    name: CapabilityName,
    *,
    read_only: bool = True,
    version: str = "0.5.0",
) -> McpCapability:
    return McpCapability(
        name=name,
        documentation_status=DocumentationStatus.DOCUMENTED,
        runtime_status=RuntimeStatus.OBSERVED,
        enabled=True,
        read_only=read_only,
        source="controlled-test-inventory",
        version=version,
        verified_at=NOW,
        notes="Contract double; not a live runtime claim.",
    )


def test_observed_enabled_read_only_capability_is_a_verified_read():
    inventory = observed_inventory()
    assert inventory.verified_read(CapabilityName.ASSET_SEARCH)


def test_mutating_required_capability_cannot_verify_required_reads():
    baseline = observed_inventory()
    capabilities = tuple(
        item.model_copy(update={"read_only": False})
        if item.name is CapabilityName.ASSET_SEARCH
        else item
        for item in baseline.capabilities
    )
    inventory = CapabilityInventory(
        server_version=baseline.server_version,
        observed_at=baseline.observed_at,
        capabilities=capabilities,
    )
    assert not inventory.verified_read(CapabilityName.ASSET_SEARCH)
    assert not inventory.required_reads_verified


def test_mutation_capability_cannot_impersonate_missing_read_capability():
    baseline = observed_inventory()
    capabilities = tuple(
        item
        for item in baseline.capabilities
        if item.name is not CapabilityName.ASSET_SEARCH
    ) + (observed_capability(CapabilityName.MUTATION, read_only=False),)
    inventory = CapabilityInventory(
        server_version="0.5.0",
        observed_at=NOW,
        capabilities=capabilities,
    )
    assert not inventory.required_reads_verified
    assert not inventory.verified_read(CapabilityName.ASSET_SEARCH)
    assert not inventory.verified_read(CapabilityName.MUTATION)


def test_mutation_and_writeback_status_remain_separate_from_required_reads():
    capabilities = observed_inventory().capabilities + (
        observed_capability(CapabilityName.MUTATION, read_only=False),
        observed_capability(CapabilityName.WRITEBACK, read_only=False),
    )
    inventory = CapabilityInventory(
        server_version="0.5.0",
        observed_at=NOW,
        capabilities=capabilities,
    )
    assert inventory.required_reads_verified
    assert not inventory.verified_read(CapabilityName.MUTATION)
    assert not inventory.verified_read(CapabilityName.WRITEBACK)


def test_observed_capability_version_must_match_inventory():
    with pytest.raises(ValidationError, match="versions must match"):
        CapabilityInventory(
            server_version="0.5.0",
            observed_at=NOW,
            capabilities=(
                observed_capability(CapabilityName.ASSET_SEARCH, version="0.6.0"),
            ),
        )


def test_multiple_mixed_observed_versions_are_rejected():
    with pytest.raises(ValidationError, match="versions must match"):
        CapabilityInventory(
            server_version="0.5.0",
            observed_at=NOW,
            capabilities=(
                observed_capability(CapabilityName.ASSET_SEARCH),
                observed_capability(CapabilityName.ENTITY_INSPECTION, version="0.6.0"),
            ),
        )


@pytest.mark.parametrize("version", ["", "   ", " 0.5.0", "0.5.0 "])
def test_capability_version_rejects_missing_or_noncanonical_values(version):
    with pytest.raises(ValidationError):
        observed_capability(CapabilityName.ASSET_SEARCH, version=version)


def test_observed_capability_requires_a_version():
    with pytest.raises(ValidationError):
        McpCapability(
            name=CapabilityName.ASSET_SEARCH,
            documentation_status=DocumentationStatus.DOCUMENTED,
            runtime_status=RuntimeStatus.OBSERVED,
            enabled=True,
            read_only=True,
            source="controlled-test-inventory",
            verified_at=NOW,
            notes="Missing version must fail.",
        )


def test_incompatible_version_representation_is_not_silently_normalized():
    with pytest.raises(ValidationError, match="versions must match"):
        CapabilityInventory(
            server_version="0.5.0",
            observed_at=NOW,
            capabilities=(
                observed_capability(CapabilityName.ASSET_SEARCH, version="v0.5.0"),
            ),
        )


def test_documented_only_capability_may_retain_separate_source_version():
    capability = McpCapability(
        name=CapabilityName.DOCUMENTS,
        documentation_status=DocumentationStatus.DOCUMENTED,
        read_only=True,
        source="official documentation",
        version="documentation-current",
        notes="Not observed at runtime.",
    )
    inventory = CapabilityInventory(
        server_version="0.5.0",
        capabilities=(capability,),
    )
    assert not inventory.required_reads_verified


def test_reordered_matching_observed_inventory_remains_deterministic():
    baseline = observed_inventory()
    reordered = CapabilityInventory(
        server_version=baseline.server_version,
        observed_at=baseline.observed_at,
        capabilities=tuple(reversed(baseline.capabilities)),
    )
    assert reordered == baseline
