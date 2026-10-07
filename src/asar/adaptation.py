from __future__ import annotations

from dataclasses import dataclass

from .contracts import AdaptationResult, Disposition


@dataclass
class GuardedPlannerAdapter:
    """Adapt proposal gain while leaving final physical authority independent.

    This is a deterministic prototype heuristic. Any proposed gain remains bounded, and
    the independent authority still clamps or denies physical commands after adaptation.
    """

    minimum_gain: float = 0.75
    maximum_gain: float = 2.50
    increase_factor: float = 1.08
    decrease_factor: float = 0.88
    minimum_expected_improvement: float = 0.20

    def update(
        self,
        *,
        current_gain: float,
        before_error: float,
        after_error: float,
        disposition: Disposition,
    ) -> AdaptationResult:
        old = float(current_gain)
        if disposition is Disposition.DENY or before_error <= 1e-12:
            return AdaptationResult(False, old, old, "adaptation_not_authorized_by_outcome")

        improvement = (before_error - after_error) / before_error
        candidate = old
        reason = "gain_retained"
        if after_error > before_error * 1.02:
            candidate = old * self.decrease_factor
            reason = "gain_reduced_after_worse_outcome"
        elif improvement < self.minimum_expected_improvement:
            candidate = old * self.increase_factor
            reason = "gain_increased_after_weak_improvement"

        bounded = max(self.minimum_gain, min(self.maximum_gain, candidate))
        bounded = round(bounded, 6)
        changed = abs(bounded - old) > 1e-12
        if candidate != bounded:
            reason += "+bounded"
        return AdaptationResult(changed, old, bounded, reason)
