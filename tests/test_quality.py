from asar.contracts import SensorFrame
from asar.quality import SignalPolicy, SignalQualityEvaluator


def test_nominal_signal_is_valid() -> None:
    evaluator = SignalQualityEvaluator()
    report = evaluator.evaluate(
        SensorFrame("x", {"a": 0.5}, age_ms=10.0),
        SignalPolicy(("a",), {"a": (0.0, 1.0)}, max_age_ms=20.0),
    )
    assert report.valid
    assert report.score > 0.9


def test_stale_required_signal_is_invalid() -> None:
    evaluator = SignalQualityEvaluator()
    report = evaluator.evaluate(
        SensorFrame("x", {"a": 0.5}, age_ms=30.0),
        SignalPolicy(("a",), {"a": (0.0, 1.0)}, max_age_ms=20.0),
    )
    assert not report.valid
    assert "stale_signal" in report.reasons


def test_missing_and_out_of_range_are_invalid() -> None:
    evaluator = SignalQualityEvaluator()
    report = evaluator.evaluate(
        SensorFrame("x", {"b": 2.0}, age_ms=0.0),
        SignalPolicy(("a", "b"), {"b": (0.0, 1.0)}),
    )
    assert not report.valid
    assert "missing:a" in report.reasons
    assert "out_of_range:b" in report.reasons
