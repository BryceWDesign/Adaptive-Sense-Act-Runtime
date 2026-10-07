from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import ModalityEstimate, SensorFrame

PRESSURE_FIELDS = ("front_left", "front_right", "rear_left", "rear_right")


def pressure_bias(values: Mapping[str, float]) -> tuple[float, float]:
    mapping = dict(values)
    total = sum(float(mapping[name]) for name in PRESSURE_FIELDS)
    if total <= 1e-12:
        return 0.0, 0.0
    left = float(mapping["front_left"]) + float(mapping["rear_left"])
    right = float(mapping["front_right"]) + float(mapping["rear_right"])
    front = float(mapping["front_left"]) + float(mapping["front_right"])
    rear = float(mapping["rear_left"]) + float(mapping["rear_right"])
    return (left - right) / total, (front - rear) / total


def reconstruct_pressure(total: float, lr_bias: float, fb_bias: float) -> dict[str, float]:
    lr = max(-0.98, min(0.98, float(lr_bias)))
    fb = max(-0.98, min(0.98, float(fb_bias)))
    left_fraction = (1.0 + lr) / 2.0
    front_fraction = (1.0 + fb) / 2.0
    right_fraction = 1.0 - left_fraction
    rear_fraction = 1.0 - front_fraction
    return {
        "front_left": total * front_fraction * left_fraction,
        "front_right": total * front_fraction * right_fraction,
        "rear_left": total * rear_fraction * left_fraction,
        "rear_right": total * rear_fraction * right_fraction,
    }


class AdaptiveSurfaceEstimator:
    """Translate domain-specific sensor frames into shared state features."""

    def pressure(self, frame: SensorFrame, quality: float) -> ModalityEstimate:
        lr_bias, fb_bias = pressure_bias(frame.values)
        return ModalityEstimate(
            modality=frame.modality,
            features={"lr_bias": lr_bias, "fb_bias": fb_bias},
            quality=quality,
        )

    def posture(self, frame: SensorFrame, quality: float) -> ModalityEstimate:
        return ModalityEstimate(
            modality=frame.modality,
            features={
                "lr_bias": float(frame.values["lr_bias"]),
                "fb_bias": float(frame.values["fb_bias"]),
            },
            quality=quality,
        )


@dataclass
class AdaptiveSurfacePlant:
    """Deterministic simulation fixture for a pressure+haptic adaptive surface.

    The response model is deliberately synthetic. It does not represent measured behavior
    of a person, animal, medical surface, or real haptic device.
    """

    loads: dict[str, float]
    response_gain: float = 0.45
    posture_scale: float = 0.96
    posture_offset_lr: float = 0.005
    posture_offset_fb: float = -0.004

    def observe(self) -> tuple[SensorFrame, SensorFrame]:
        lr_bias, fb_bias = pressure_bias(self.loads)
        pressure = SensorFrame("pressure", dict(self.loads), age_ms=4.0)
        posture = SensorFrame(
            "posture",
            {
                "lr_bias": max(-1.0, min(1.0, lr_bias * self.posture_scale + self.posture_offset_lr)),
                "fb_bias": max(-1.0, min(1.0, fb_bias * self.posture_scale + self.posture_offset_fb)),
            },
            age_ms=7.0,
        )
        return pressure, posture

    def apply_haptic(self, *, target: str, amplitude: float) -> None:
        total = sum(self.loads.values())
        lr_bias, fb_bias = pressure_bias(self.loads)
        effect = max(0.0, min(0.80, self.response_gain * max(0.0, amplitude)))

        horizontal = "right" if target.endswith("right") else "left" if target.endswith("left") else None
        longitudinal = "rear" if target.startswith("rear") else "front" if target.startswith("front") else None

        expected_horizontal = "right" if lr_bias > 0.0 else "left" if lr_bias < 0.0 else None
        expected_longitudinal = "rear" if fb_bias > 0.0 else "front" if fb_bias < 0.0 else None

        if horizontal is None or expected_horizontal is None:
            next_lr = lr_bias
        elif horizontal == expected_horizontal:
            next_lr = lr_bias * (1.0 - effect)
        else:
            next_lr = lr_bias * (1.0 + effect)

        if longitudinal is None or expected_longitudinal is None:
            next_fb = fb_bias
        elif longitudinal == expected_longitudinal:
            next_fb = fb_bias * (1.0 - effect)
        else:
            next_fb = fb_bias * (1.0 + effect)

        self.loads = reconstruct_pressure(total, next_lr, next_fb)
