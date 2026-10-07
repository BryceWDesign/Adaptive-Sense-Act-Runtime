from asar.surface import AdaptiveSurfacePlant, pressure_bias, reconstruct_pressure


def test_pressure_roundtrip_preserves_bias_and_total() -> None:
    values = reconstruct_pressure(1.0, 0.4, -0.2)
    lr, fb = pressure_bias(values)
    assert abs(sum(values.values()) - 1.0) < 1e-12
    assert abs(lr - 0.4) < 1e-12
    assert abs(fb + 0.2) < 1e-12


def test_simulated_haptic_reduces_imbalance() -> None:
    plant = AdaptiveSurfacePlant(
        {"front_left": 0.44, "front_right": 0.18, "rear_left": 0.27, "rear_right": 0.11},
        response_gain=0.45,
    )
    before = max(abs(x) for x in pressure_bias(plant.loads))
    plant.apply_haptic(target="rear_right", amplitude=0.5)
    after = max(abs(x) for x in pressure_bias(plant.loads))
    assert after < before


def test_wrong_haptic_direction_worsens_corresponding_bias() -> None:
    plant = AdaptiveSurfacePlant(
        {"front_left": 0.44, "front_right": 0.18, "rear_left": 0.27, "rear_right": 0.11},
        response_gain=0.8,
    )
    before_lr, before_fb = pressure_bias(plant.loads)
    plant.apply_haptic(target="front_left", amplitude=0.5)
    after_lr, after_fb = pressure_bias(plant.loads)
    assert abs(after_lr) > abs(before_lr)
    assert abs(after_fb) > abs(before_fb)
