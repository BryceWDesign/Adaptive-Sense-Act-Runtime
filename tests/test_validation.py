from asar.validation import run_validation


def test_validation_campaign_passes() -> None:
    report = run_validation()
    assert report["passed"]
    assert report["pass_count"] == report["scenario_count"]
    assert report["scenario_count"] >= 6
