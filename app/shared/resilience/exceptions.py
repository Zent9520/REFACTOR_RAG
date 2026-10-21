class CapacityError(RuntimeError):
    """Base error for local backpressure and dependency capacity."""


class UserCapacityExceededError(CapacityError):
    pass


class PipelineCapacityExceededError(CapacityError):
    pass


class DependencyQueueTimeoutError(CapacityError):
    pass


class TokenBudgetExceededError(CapacityError):
    pass


class DependencyUnavailableError(CapacityError):
    pass
