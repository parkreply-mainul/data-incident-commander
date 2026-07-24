"""Safe DataHub MCP integration errors."""

from data_incident_commander.application.errors import DependencyUnavailable


class DataHubIntegrationError(Exception):
    """Base internal error; messages must remain public-safe."""


class McpNotConfigured(DependencyUnavailable, DataHubIntegrationError):
    pass


class McpUnavailable(DependencyUnavailable, DataHubIntegrationError):
    pass


class AuthenticationFailure(DependencyUnavailable, DataHubIntegrationError):
    pass


class ToolInventoryUnavailable(DependencyUnavailable, DataHubIntegrationError):
    pass


class RequiredToolMissing(DependencyUnavailable, DataHubIntegrationError):
    pass


class MalformedToolResult(DataHubIntegrationError):
    pass


class NormalizationFailure(DataHubIntegrationError):
    pass


class IntegrationTimeout(DependencyUnavailable, DataHubIntegrationError):
    pass


class PartialResult(DataHubIntegrationError):
    pass


class CapabilityDisabled(DependencyUnavailable, DataHubIntegrationError):
    pass


class MutationDisabled(CapabilityDisabled):
    pass
