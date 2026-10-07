from dataclasses import dataclass

from asar.authority import AuthorityPolicy, ParameterLimit
from asar.contracts import (
    ActionRequest,
    AuthorityDecision,
    ExecutionResult,
    ExecutionStatus,
    ModalityEstimate,
    SensorFrame,
    StateEstimate,
)
from asar.quality import SignalPolicy
from asar.runtime import SenseActRuntime


class ScalarAdapter:
    def __init__(self) -> None:
        self.value = 1.0

    def observe(self) -> tuple[SensorFrame, ...]:
        return (SensorFrame("scalar", {"value": self.value}, age_ms=1.0),)

    def estimate(self, frame: SensorFrame, *, quality: float) -> ModalityEstimate:
        return ModalityEstimate("scalar", {"error": float(frame.values["value"])}, quality)

    def execute(self, *, request: ActionRequest, decision: AuthorityDecision) -> ExecutionResult:
        if not decision.granted_parameters and request.action != "hold":
            return ExecutionResult(ExecutionStatus.BLOCKED, decision.action_id, {}, "blocked")
        if request.action == "hold":
            return ExecutionResult(ExecutionStatus.HELD, decision.action_id, {}, "held")
        step = float(decision.granted_parameters["step"])
        self.value = max(0.0, self.value - step)
        return ExecutionResult(ExecutionStatus.EXECUTED, decision.action_id, {"step": step}, "applied")


@dataclass
class ScalarPlanner:
    gain: float = 0.5
    tolerance: float = 0.05

    def error(self, state: StateEstimate) -> float:
        return abs(float(state.features.get("error", 1.0)))

    def goal_reached(self, state: StateEstimate) -> bool:
        return self.error(state) <= self.tolerance

    def propose(self, state: StateEstimate, *, cycle: int) -> ActionRequest:
        if self.goal_reached(state):
            return ActionRequest(f"{cycle}-hold", "hold", "scalar", {}, "goal reached")
        return ActionRequest(
            f"{cycle}-nudge",
            "nudge",
            "scalar",
            {"step": self.gain * self.error(state)},
            "reduce scalar error",
        )


def test_runtime_is_not_hardwired_to_adaptive_surface() -> None:
    adapter = ScalarAdapter()
    runtime = SenseActRuntime(
        adapter=adapter,
        quality_policies={"scalar": SignalPolicy(("value",), {"value": (0.0, 1.0)}, max_age_ms=10.0)},
        authority_policy=AuthorityPolicy(
            allowed_actions=("hold", "nudge"),
            allowed_targets=("scalar",),
            required_modalities=("scalar",),
            parameter_limits={"step": ParameterLimit(0.0, 0.3, deratable=True)},
            uncertainty_derate_start=0.25,
            uncertainty_stop=0.65,
        ),
        planner=ScalarPlanner(),
    )

    for _ in range(10):
        result = runtime.cycle()
        if result.goal_reached:
            break

    assert result.goal_reached
    assert adapter.value <= 0.05
    assert len(runtime.ledger.entries) > 0
