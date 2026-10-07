from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .authority import AuthorityPolicy, ParameterLimit
from .planner import BalancePlanner
from .quality import SignalPolicy
from .surface import PRESSURE_FIELDS, AdaptiveSurfacePlant


@dataclass(frozen=True)
class SurfaceRuntimeConfig:
    plant: AdaptiveSurfacePlant
    pressure_policy: SignalPolicy
    posture_policy: SignalPolicy
    authority_policy: AuthorityPolicy
    planner: BalancePlanner


def _number(value: Any, name: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    return float(value)


def load_surface_config(path: Path) -> SurfaceRuntimeConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("configuration root must be an object")

    initial = raw.get("initial_surface")
    if not isinstance(initial, dict):
        raise ValueError("initial_surface must be an object")
    loads_raw = initial.get("loads")
    if not isinstance(loads_raw, dict):
        raise ValueError("initial_surface.loads must be an object")
    loads = {name: _number(loads_raw.get(name), f"loads.{name}") for name in PRESSURE_FIELDS}
    if abs(sum(loads.values()) - 1.0) > 1e-6:
        raise ValueError("initial_surface.loads must sum to 1.0")

    signal_max_age_ms = _number(raw.get("signal_max_age_ms"), "signal_max_age_ms")
    pressure_policy = SignalPolicy(
        required_fields=PRESSURE_FIELDS,
        bounds={name: (0.0, 1.0) for name in PRESSURE_FIELDS},
        max_age_ms=signal_max_age_ms,
    )
    posture_policy = SignalPolicy(
        required_fields=("lr_bias", "fb_bias"),
        bounds={"lr_bias": (-1.0, 1.0), "fb_bias": (-1.0, 1.0)},
        max_age_ms=signal_max_age_ms,
    )

    uncertainty = raw.get("uncertainty")
    actuator_limits = raw.get("actuator_limits")
    if not isinstance(uncertainty, dict) or not isinstance(actuator_limits, dict):
        raise ValueError("uncertainty and actuator_limits must be objects")
    limits: dict[str, ParameterLimit] = {}
    for name, settings in actuator_limits.items():
        if not isinstance(name, str) or not isinstance(settings, dict):
            raise ValueError("invalid actuator limit entry")
        limits[name] = ParameterLimit(
            _number(settings.get("min"), f"{name}.min"),
            _number(settings.get("max"), f"{name}.max"),
            bool(settings.get("deratable", False)),
        )

    authority_policy = AuthorityPolicy(
        allowed_actions=("hold", "haptic_cue"),
        allowed_targets=("surface", "front_left", "front_right", "rear_left", "rear_right"),
        required_modalities=tuple(str(x) for x in raw.get("required_modalities", [])),
        parameter_limits=limits,
        uncertainty_derate_start=_number(uncertainty.get("derate_start"), "uncertainty.derate_start"),
        uncertainty_stop=_number(uncertainty.get("stop"), "uncertainty.stop"),
    )

    planner = BalancePlanner(
        gain=_number(raw.get("planner_gain"), "planner_gain"),
        tolerance=_number(raw.get("balance_tolerance"), "balance_tolerance"),
    )
    plant = AdaptiveSurfacePlant(
        loads=loads,
        response_gain=_number(initial.get("response_gain"), "initial_surface.response_gain"),
        posture_scale=_number(initial.get("posture_scale"), "initial_surface.posture_scale"),
        posture_offset_lr=_number(initial.get("posture_offset_lr"), "initial_surface.posture_offset_lr"),
        posture_offset_fb=_number(initial.get("posture_offset_fb"), "initial_surface.posture_offset_fb"),
    )
    return SurfaceRuntimeConfig(plant, pressure_policy, posture_policy, authority_policy, planner)
