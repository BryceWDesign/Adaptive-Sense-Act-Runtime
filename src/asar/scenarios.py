from __future__ import annotations

from pathlib import Path

from .adapters import AdaptiveSurfaceAdapter
from .authority import AuthorityPolicy, ParameterLimit
from .config import load_surface_config
from .planner import BalancePlanner
from .quality import SignalPolicy
from .runtime import SenseActRuntime
from .surface import PRESSURE_FIELDS, AdaptiveSurfacePlant


def default_config_path() -> Path:
    return Path(__file__).resolve().parents[2] / "configs" / "adaptive_surface.json"


def default_pressure_policy() -> SignalPolicy:
    return SignalPolicy(
        required_fields=PRESSURE_FIELDS,
        bounds={name: (0.0, 1.0) for name in PRESSURE_FIELDS},
        max_age_ms=100.0,
    )


def default_posture_policy() -> SignalPolicy:
    return SignalPolicy(
        required_fields=("lr_bias", "fb_bias"),
        bounds={"lr_bias": (-1.0, 1.0), "fb_bias": (-1.0, 1.0)},
        max_age_ms=100.0,
    )


def default_authority_policy() -> AuthorityPolicy:
    return AuthorityPolicy(
        allowed_actions=("hold", "haptic_cue"),
        allowed_targets=("surface", "front_left", "front_right", "rear_left", "rear_right"),
        required_modalities=("pressure", "posture"),
        parameter_limits={
            "amplitude": ParameterLimit(0.0, 0.60, deratable=True),
            "frequency_hz": ParameterLimit(40.0, 220.0, deratable=False),
            "duration_s": ParameterLimit(0.05, 0.75, deratable=True),
        },
        uncertainty_derate_start=0.25,
        uncertainty_stop=0.65,
    )


def build_adaptive_surface_runtime(
    evidence_path: Path | None = None,
    *,
    config_path: Path | None = None,
) -> SenseActRuntime:
    path = config_path or default_config_path()
    if path.exists():
        config = load_surface_config(path)
        return SenseActRuntime(
            adapter=AdaptiveSurfaceAdapter(config.plant),
            quality_policies={
                "pressure": config.pressure_policy,
                "posture": config.posture_policy,
            },
            authority_policy=config.authority_policy,
            evidence_path=evidence_path,
            planner=config.planner,
        )

    plant = AdaptiveSurfacePlant(
        loads={"front_left": 0.44, "front_right": 0.18, "rear_left": 0.27, "rear_right": 0.11},
        response_gain=0.8,
    )
    return SenseActRuntime(
        adapter=AdaptiveSurfaceAdapter(plant),
        quality_policies={
            "pressure": default_pressure_policy(),
            "posture": default_posture_policy(),
        },
        authority_policy=default_authority_policy(),
        evidence_path=evidence_path,
        planner=BalancePlanner(gain=1.6, tolerance=0.035),
    )
