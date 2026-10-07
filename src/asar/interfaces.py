from __future__ import annotations

from typing import Protocol

from .contracts import (
    ActionRequest,
    AuthorityDecision,
    ExecutionResult,
    ModalityEstimate,
    SensorFrame,
    StateEstimate,
)


class DomainAdapter(Protocol):
    """Boundary a real domain implements to connect sensors and actuators to ASAR."""

    def observe(self) -> tuple[SensorFrame, ...]: ...

    def estimate(self, frame: SensorFrame, *, quality: float) -> ModalityEstimate: ...

    def execute(self, *, request: ActionRequest, decision: AuthorityDecision) -> ExecutionResult: ...


class AdaptivePlanner(Protocol):
    """Proposal layer contract. It has no actuator access."""

    gain: float

    def propose(self, state: StateEstimate, *, cycle: int) -> ActionRequest: ...

    def error(self, state: StateEstimate) -> float: ...

    def goal_reached(self, state: StateEstimate) -> bool: ...
