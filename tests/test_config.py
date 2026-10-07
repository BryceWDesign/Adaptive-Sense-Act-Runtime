from asar.config import load_surface_config
from asar.scenarios import default_config_path


def test_committed_config_drives_limits_and_fixture() -> None:
    config = load_surface_config(default_config_path())
    assert config.authority_policy.parameter_limits["amplitude"].maximum == 0.6
    assert config.plant.loads["front_left"] == 0.44
    assert config.planner.tolerance == 0.035
