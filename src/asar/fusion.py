from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .contracts import ModalityEstimate, StateEstimate


class ReliabilityWeightedFusion:
    """Fuse feature estimates while exposing disagreement as uncertainty."""

    def fuse(self, estimates: Iterable[ModalityEstimate]) -> StateEstimate:
        rows = list(estimates)
        if not rows:
            return StateEstimate({}, 0.0, 1.0, (), {})

        feature_values: dict[str, list[tuple[float, float]]] = defaultdict(list)
        for estimate in rows:
            weight = max(0.0, min(1.0, float(estimate.quality)))
            for feature, value in estimate.features.items():
                feature_values[feature].append((float(value), weight))

        fused: dict[str, float] = {}
        disagreements: dict[str, float] = {}
        for feature, values in feature_values.items():
            total_weight = sum(weight for _, weight in values)
            if total_weight <= 1e-12:
                fused[feature] = 0.0
            else:
                fused[feature] = sum(value * weight for value, weight in values) / total_weight
            raw = [value for value, _ in values]
            disagreements[feature] = max(raw) - min(raw) if len(raw) > 1 else 0.0

        mean_quality = sum(max(0.0, min(1.0, row.quality)) for row in rows) / len(rows)
        max_disagreement = max((abs(value) for value in disagreements.values()), default=0.0)
        uncertainty = max(1.0 - mean_quality, min(1.0, max_disagreement))
        confidence = 1.0 - uncertainty
        return StateEstimate(
            features={key: round(value, 6) for key, value in fused.items()},
            confidence=round(confidence, 6),
            uncertainty=round(uncertainty, 6),
            modalities=tuple(sorted(row.modality for row in rows)),
            disagreements={key: round(value, 6) for key, value in disagreements.items()},
        )
