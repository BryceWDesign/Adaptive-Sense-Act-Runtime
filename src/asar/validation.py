from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from .adaptation import GuardedPlannerAdapter
from .authority import IndependentActionAuthority
from .contracts import ActionRequest, Disposition, ModalityEstimate, QualityReport, StateEstimate
from .evidence import EvidenceLedger
from .fusion import ReliabilityWeightedFusion
from .scenarios import build_adaptive_surface_runtime, default_authority_policy


def _scenario(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def run_validation() -> dict[str, Any]:
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "demo.jsonl"
        runtime = build_adaptive_surface_runtime(path)
        cycles = []
        for _ in range(10):
            result = runtime.cycle()
            cycles.append(result)
            if result.goal_reached:
                break
        verification = EvidenceLedger.verify_file(path)
        nominal_ok = bool(cycles and cycles[-1].goal_reached and verification.passed)
        results.append(
            _scenario(
                "nominal_closed_loop_converges",
                nominal_ok,
                f"cycles={len(cycles)} final_error={runtime.planner.error(cycles[-1].after):.6f}",
            )
        )

    authority = IndependentActionAuthority()
    policy = default_authority_policy()
    quality = {
        "pressure": QualityReport("pressure", True, 1.0, ("signal_nominal",)),
        "posture": QualityReport("posture", True, 1.0, ("signal_nominal",)),
    }
    high_uncertainty = StateEstimate(
        {"lr_bias": 0.2, "fb_bias": 0.1}, 0.20, 0.80, ("pressure", "posture"), {"lr_bias": 0.8}
    )
    request = ActionRequest(
        "validation-high-uncertainty",
        "haptic_cue",
        "rear_right",
        {"amplitude": 0.3, "frequency_hz": 160.0, "duration_s": 0.4},
        "validation",
    )
    denied = authority.decide(request, high_uncertainty, quality, policy)
    results.append(
        _scenario(
            "high_uncertainty_denied",
            denied.disposition is Disposition.DENY,
            ",".join(denied.reason_codes),
        )
    )

    nominal_state = StateEstimate(
        {"lr_bias": 0.2, "fb_bias": 0.1}, 0.95, 0.05, ("pressure", "posture"), {"lr_bias": 0.02}
    )
    bad_quality = dict(quality)
    bad_quality["pressure"] = QualityReport("pressure", False, 0.0, ("stale_signal",))
    stale = authority.decide(request, nominal_state, bad_quality, policy)
    results.append(
        _scenario(
            "invalid_required_sensor_denied",
            stale.disposition is Disposition.DENY,
            ",".join(stale.reason_codes),
        )
    )

    over_request = ActionRequest(
        "validation-envelope",
        "haptic_cue",
        "rear_right",
        {"amplitude": 0.95, "frequency_hz": 500.0, "duration_s": 2.0},
        "validation",
    )
    bounded = authority.decide(over_request, nominal_state, quality, policy)
    bounded_ok = (
        bounded.disposition is Disposition.MODIFY
        and bounded.granted_parameters["amplitude"] == 0.60
        and bounded.granted_parameters["frequency_hz"] == 220.0
        and bounded.granted_parameters["duration_s"] == 0.75
    )
    results.append(_scenario("out_of_envelope_request_bounded", bounded_ok, str(bounded.granted_parameters)))

    fusion = ReliabilityWeightedFusion()
    disagreement = fusion.fuse(
        [
            ModalityEstimate("pressure", {"lr_bias": 0.55, "fb_bias": 0.0}, 1.0),
            ModalityEstimate("posture", {"lr_bias": -0.55, "fb_bias": 0.0}, 1.0),
        ]
    )
    results.append(
        _scenario(
            "sensor_disagreement_surfaces_uncertainty",
            disagreement.uncertainty >= 0.65,
            f"uncertainty={disagreement.uncertainty}",
        )
    )

    ledger = EvidenceLedger()
    ledger.append("one", {"value": 1})
    ledger.append("two", {"value": 2})
    tampered = [copy.deepcopy(entry) for entry in ledger.entries]
    tampered[0]["payload"]["value"] = 999
    tamper_result = EvidenceLedger.verify_entries(tampered)
    results.append(
        _scenario(
            "evidence_tamper_detected",
            not tamper_result.passed,
            str(tamper_result.issue),
        )
    )

    adapter = GuardedPlannerAdapter()
    gain = 1.0
    for _ in range(100):
        update = adapter.update(
            current_gain=gain,
            before_error=1.0,
            after_error=0.99,
            disposition=Disposition.ALLOW,
        )
        gain = update.new_gain
    results.append(
        _scenario(
            "adaptation_remains_bounded",
            adapter.minimum_gain <= gain <= adapter.maximum_gain and gain == adapter.maximum_gain,
            f"gain={gain}",
        )
    )

    passed = all(result["passed"] for result in results)
    return {
        "schema": "asar-validation-v1",
        "version": "0.1.0",
        "passed": passed,
        "scenario_count": len(results),
        "pass_count": sum(1 for result in results if result["passed"]),
        "scenarios": results,
    }


def write_validation_report(path: Path) -> dict[str, Any]:
    report = run_validation()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report
