from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import QualityReport, SensorFrame


@dataclass(frozen=True)
class SignalPolicy:
    required_fields: tuple[str, ...]
    bounds: Mapping[str, tuple[float, float]]
    max_age_ms: float = 250.0


class SignalQualityEvaluator:
    """Deterministic signal-health checks used before state estimation.

    The score is an engineering heuristic for this prototype, not a calibrated medical,
    biological, or hardware-quality metric.
    """

    def evaluate(self, frame: SensorFrame, policy: SignalPolicy) -> QualityReport:
        reasons: list[str] = []
        penalties = 0.0

        if frame.age_ms < 0.0 or not math.isfinite(frame.age_ms):
            reasons.append("invalid_age")
        elif frame.age_ms > policy.max_age_ms:
            reasons.append("stale_signal")

        for field in policy.required_fields:
            if field not in frame.values:
                reasons.append(f"missing:{field}")
                continue
            value = frame.values[field]
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                reasons.append(f"nonfinite:{field}")
                continue
            if field in policy.bounds:
                low, high = policy.bounds[field]
                if float(value) < low or float(value) > high:
                    reasons.append(f"out_of_range:{field}")

        for field, value in frame.values.items():
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                if f"nonfinite:{field}" not in reasons:
                    reasons.append(f"nonfinite:{field}")
                continue
            bounds = policy.bounds.get(field)
            if bounds is None:
                continue
            low, high = bounds
            span = max(high - low, 1e-9)
            margin = min(float(value) - low, high - float(value)) / span
            if margin < 0.02:
                penalties += 0.08
            elif margin < 0.08:
                penalties += 0.03

        invalid = any(
            reason.startswith(("missing:", "nonfinite:", "out_of_range:"))
            or reason in {"invalid_age", "stale_signal"}
            for reason in reasons
        )
        score = 0.0 if invalid else max(0.0, min(1.0, 1.0 - penalties))
        if not reasons:
            reasons.append("signal_nominal")
        return QualityReport(frame.modality, not invalid, round(score, 6), tuple(reasons))
