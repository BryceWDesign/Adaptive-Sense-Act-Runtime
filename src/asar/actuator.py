from __future__ import annotations

from .contracts import (
    ActionRequest,
    AuthorityDecision,
    Disposition,
    ExecutionResult,
    ExecutionStatus,
)
from .surface import AdaptiveSurfacePlant


class SimulatedAdaptiveSurfaceActuator:
    def __init__(self, plant: AdaptiveSurfacePlant) -> None:
        self.plant = plant

    def execute(self, *, request: ActionRequest, decision: AuthorityDecision) -> ExecutionResult:
        if decision.disposition is Disposition.DENY:
            return ExecutionResult(
                ExecutionStatus.BLOCKED,
                decision.action_id,
                {},
                "independent authority denied execution",
            )
        if request.action == "hold":
            return ExecutionResult(
                ExecutionStatus.HELD,
                decision.action_id,
                {},
                "state held; no physical response requested",
            )
        if request.action != "haptic_cue":
            return ExecutionResult(
                ExecutionStatus.BLOCKED,
                decision.action_id,
                {},
                "simulator has no adapter for the requested action",
            )
        amplitude = float(decision.granted_parameters["amplitude"])
        self.plant.apply_haptic(target=request.target, amplitude=amplitude)
        return ExecutionResult(
            ExecutionStatus.EXECUTED,
            decision.action_id,
            dict(decision.granted_parameters),
            "synthetic adaptive-surface response applied",
        )
