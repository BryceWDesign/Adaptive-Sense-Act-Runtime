from __future__ import annotations

from ..actuator import SimulatedAdaptiveSurfaceActuator
from ..contracts import (
    ActionRequest,
    AuthorityDecision,
    ExecutionResult,
    ModalityEstimate,
    SensorFrame,
)
from ..surface import AdaptiveSurfaceEstimator, AdaptiveSurfacePlant


class AdaptiveSurfaceAdapter:
    """Reference domain adapter used only by the bundled synthetic demonstration."""

    def __init__(self, plant: AdaptiveSurfacePlant) -> None:
        self.plant = plant
        self.estimator = AdaptiveSurfaceEstimator()
        self.actuator = SimulatedAdaptiveSurfaceActuator(plant)

    def observe(self) -> tuple[SensorFrame, ...]:
        return self.plant.observe()

    def estimate(self, frame: SensorFrame, *, quality: float) -> ModalityEstimate:
        if frame.modality == "pressure":
            return self.estimator.pressure(frame, quality)
        if frame.modality == "posture":
            return self.estimator.posture(frame, quality)
        raise ValueError(f"unsupported adaptive-surface modality: {frame.modality}")

    def execute(self, *, request: ActionRequest, decision: AuthorityDecision) -> ExecutionResult:
        return self.actuator.execute(request=request, decision=decision)
