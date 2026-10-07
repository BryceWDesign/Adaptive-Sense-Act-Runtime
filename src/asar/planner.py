from __future__ import annotations

from dataclasses import dataclass

from .contracts import ActionRequest, StateEstimate


@dataclass
class BalancePlanner:
    gain: float = 1.6
    tolerance: float = 0.035

    @staticmethod
    def error(state: StateEstimate) -> float:
        return max(abs(float(state.features.get("lr_bias", 0.0))), abs(float(state.features.get("fb_bias", 0.0))))

    def goal_reached(self, state: StateEstimate) -> bool:
        return self.error(state) <= self.tolerance

    def propose(self, state: StateEstimate, *, cycle: int) -> ActionRequest:
        lr = float(state.features.get("lr_bias", 0.0))
        fb = float(state.features.get("fb_bias", 0.0))
        error = max(abs(lr), abs(fb))
        if error <= self.tolerance:
            return ActionRequest(
                action_id=f"cycle-{cycle}-hold",
                action="hold",
                target="surface",
                parameters={},
                rationale="estimated imbalance is inside the configured tolerance",
            )

        horizontal = "right" if lr > 0.0 else "left"
        longitudinal = "rear" if fb > 0.0 else "front"
        target = f"{longitudinal}_{horizontal}"
        amplitude = max(0.25, min(0.95, self.gain * error))
        return ActionRequest(
            action_id=f"cycle-{cycle}-cue",
            action="haptic_cue",
            target=target,
            parameters={
                "amplitude": round(amplitude, 6),
                "frequency_hz": 160.0,
                "duration_s": 0.40,
            },
            rationale=(
                f"reduce estimated lr_bias={lr:+.4f} and fb_bias={fb:+.4f}; "
                f"cue target={target}"
            ),
        )
