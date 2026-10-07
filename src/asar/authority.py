from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from .contracts import ActionRequest, AuthorityDecision, Disposition, QualityReport, StateEstimate


@dataclass(frozen=True)
class ParameterLimit:
    minimum: float
    maximum: float
    deratable: bool = False


@dataclass(frozen=True)
class AuthorityPolicy:
    allowed_actions: tuple[str, ...]
    allowed_targets: tuple[str, ...]
    required_modalities: tuple[str, ...]
    parameter_limits: Mapping[str, ParameterLimit]
    uncertainty_derate_start: float = 0.25
    uncertainty_stop: float = 0.65


class IndependentActionAuthority:
    """Fail-closed action authority independent from the planner/adaptation layer."""

    def decide(
        self,
        request: ActionRequest,
        state: StateEstimate,
        quality: Mapping[str, QualityReport],
        policy: AuthorityPolicy,
    ) -> AuthorityDecision:
        reasons: list[str] = []
        if request.action not in policy.allowed_actions:
            return self._deny(request, "action_not_allowed")
        if request.target not in policy.allowed_targets:
            return self._deny(request, "target_not_allowed")

        for modality in policy.required_modalities:
            report = quality.get(modality)
            if report is None:
                reasons.append(f"required_modality_missing:{modality}")
            elif not report.valid:
                reasons.append(f"required_modality_invalid:{modality}")
        if reasons:
            return AuthorityDecision(request.action_id, Disposition.DENY, {}, tuple(reasons))

        uncertainty = max(0.0, min(1.0, float(state.uncertainty)))
        if uncertainty >= policy.uncertainty_stop:
            return self._deny(request, "uncertainty_stop")

        if request.action == "hold":
            return AuthorityDecision(request.action_id, Disposition.ALLOW, {}, ("hold_authorized",))

        unknown = sorted(set(request.parameters) - set(policy.parameter_limits))
        if unknown:
            return self._deny(request, "unknown_parameter:" + ",".join(unknown))

        granted: dict[str, float] = {}
        modified = False
        if uncertainty > policy.uncertainty_derate_start:
            span = max(1e-9, policy.uncertainty_stop - policy.uncertainty_derate_start)
            authority_scale = max(
                0.10,
                1.0 - (uncertainty - policy.uncertainty_derate_start) / span,
            )
            reasons.append("uncertainty_derate")
        else:
            authority_scale = 1.0

        for name, raw in request.parameters.items():
            value = float(raw)
            if not math.isfinite(value):
                return self._deny(request, f"nonfinite_parameter:{name}")
            limit = policy.parameter_limits[name]
            bounded = min(max(value, limit.minimum), limit.maximum)
            if limit.deratable:
                bounded = max(limit.minimum, bounded * authority_scale)
            if abs(bounded - value) > 1e-12:
                modified = True
                reasons.append(f"parameter_bounded:{name}")
            granted[name] = round(bounded, 6)

        disposition = Disposition.MODIFY if modified or authority_scale < 0.999999 else Disposition.ALLOW
        if not reasons:
            reasons.append("full_authority")
        return AuthorityDecision(request.action_id, disposition, granted, tuple(reasons))

    @staticmethod
    def _deny(request: ActionRequest, reason: str) -> AuthorityDecision:
        return AuthorityDecision(request.action_id, Disposition.DENY, {}, (reason,))
