from asar.authority import IndependentActionAuthority
from asar.contracts import ActionRequest, Disposition, QualityReport, StateEstimate
from asar.scenarios import default_authority_policy


def good_quality() -> dict[str, QualityReport]:
    return {
        "pressure": QualityReport("pressure", True, 1.0, ("signal_nominal",)),
        "posture": QualityReport("posture", True, 1.0, ("signal_nominal",)),
    }


def state(uncertainty: float = 0.05) -> StateEstimate:
    return StateEstimate(
        {"lr_bias": 0.2, "fb_bias": 0.1},
        1.0 - uncertainty,
        uncertainty,
        ("pressure", "posture"),
        {"lr_bias": 0.01, "fb_bias": 0.01},
    )


def request(amplitude: float = 0.4) -> ActionRequest:
    return ActionRequest(
        "a1",
        "haptic_cue",
        "rear_right",
        {"amplitude": amplitude, "frequency_hz": 160.0, "duration_s": 0.4},
        "test",
    )


def test_nominal_action_allowed() -> None:
    decision = IndependentActionAuthority().decide(request(), state(), good_quality(), default_authority_policy())
    assert decision.disposition is Disposition.ALLOW
    assert decision.granted_parameters["amplitude"] == 0.4


def test_missing_or_invalid_required_modality_denies() -> None:
    quality = good_quality()
    quality["posture"] = QualityReport("posture", False, 0.0, ("stale_signal",))
    decision = IndependentActionAuthority().decide(request(), state(), quality, default_authority_policy())
    assert decision.disposition is Disposition.DENY
    assert any("required_modality_invalid:posture" == reason for reason in decision.reason_codes)


def test_high_uncertainty_denies() -> None:
    decision = IndependentActionAuthority().decide(request(), state(0.8), good_quality(), default_authority_policy())
    assert decision.disposition is Disposition.DENY
    assert decision.reason_codes == ("uncertainty_stop",)


def test_limits_modify_instead_of_silently_exceeding() -> None:
    req = ActionRequest(
        "a2",
        "haptic_cue",
        "rear_right",
        {"amplitude": 2.0, "frequency_hz": 500.0, "duration_s": 5.0},
        "test",
    )
    decision = IndependentActionAuthority().decide(req, state(), good_quality(), default_authority_policy())
    assert decision.disposition is Disposition.MODIFY
    assert decision.granted_parameters == {
        "amplitude": 0.6,
        "frequency_hz": 220.0,
        "duration_s": 0.75,
    }


def test_unknown_action_denies() -> None:
    req = ActionRequest("a3", "unknown", "surface", {}, "test")
    decision = IndependentActionAuthority().decide(req, state(), good_quality(), default_authority_policy())
    assert decision.disposition is Disposition.DENY
