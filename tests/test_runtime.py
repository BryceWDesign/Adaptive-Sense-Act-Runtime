from pathlib import Path

from asar.adapters import AdaptiveSurfaceAdapter
from asar.contracts import Disposition, ExecutionStatus, SensorFrame
from asar.evidence import EvidenceLedger
from asar.planner import BalancePlanner
from asar.runtime import SenseActRuntime
from asar.scenarios import (
    build_adaptive_surface_runtime,
    default_authority_policy,
    default_posture_policy,
    default_pressure_policy,
)
from asar.surface import AdaptiveSurfacePlant


def test_closed_loop_converges_and_records_every_cycle(tmp_path: Path) -> None:
    path = tmp_path / "run.jsonl"
    runtime = build_adaptive_surface_runtime(path)
    results = []
    for _ in range(10):
        result = runtime.cycle()
        results.append(result)
        if result.goal_reached:
            break

    assert results[-1].goal_reached
    assert BalancePlanner.error(results[-1].after) <= runtime.planner.tolerance
    assert all(result.authority.disposition in {Disposition.ALLOW, Disposition.MODIFY} for result in results)
    assert any(result.adaptation.changed for result in results)
    verification = EvidenceLedger.verify_file(path)
    assert verification.passed
    assert verification.count == len(results)


def test_observed_error_drops_over_run(tmp_path: Path) -> None:
    runtime = build_adaptive_surface_runtime(tmp_path / "run.jsonl")
    errors = []
    for _ in range(6):
        result = runtime.cycle()
        errors.append(BalancePlanner.error(result.after))
        if result.goal_reached:
            break
    assert errors == sorted(errors, reverse=True)


def test_invalid_required_sensor_blocks_end_to_end(tmp_path: Path) -> None:
    class StalePosturePlant(AdaptiveSurfacePlant):
        def observe(self) -> tuple[SensorFrame, SensorFrame]:
            pressure, posture = super().observe()
            return pressure, SensorFrame(posture.modality, posture.values, age_ms=1000.0)

    plant = StalePosturePlant(
        {"front_left": 0.44, "front_right": 0.18, "rear_left": 0.27, "rear_right": 0.11},
        response_gain=0.8,
    )
    before = dict(plant.loads)
    runtime = SenseActRuntime(
        adapter=AdaptiveSurfaceAdapter(plant),
        quality_policies={
            "pressure": default_pressure_policy(),
            "posture": default_posture_policy(),
        },
        authority_policy=default_authority_policy(),
        planner=BalancePlanner(),
        evidence_path=tmp_path / "blocked.jsonl",
    )
    result = runtime.cycle()

    assert result.authority.disposition is Disposition.DENY
    assert result.execution.status is ExecutionStatus.BLOCKED
    assert plant.loads == before
