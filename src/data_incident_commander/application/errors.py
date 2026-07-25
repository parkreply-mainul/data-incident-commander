"""Application errors mapped to stable transport errors by the API layer."""


class ApplicationError(Exception):
    """Base error safe for application boundary mapping."""


class IncidentNotFound(ApplicationError):
    pass


class IncidentConflict(ApplicationError):
    pass


class ConcurrentUpdateConflict(ApplicationError):
    """The stored incident changed after the caller read it."""


class DependencyUnavailable(ApplicationError):
    pass


class WritebackVerificationFailure(ApplicationError):
    """Mutation may be present, but required read-back proof is unavailable."""


class ProviderOutputMismatch(ApplicationError):
    """Normalized provider output does not belong to the requested incident."""


class InvalidWorkflowTransition(ApplicationError):
    pass
