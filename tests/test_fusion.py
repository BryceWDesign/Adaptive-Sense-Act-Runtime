from asar.contracts import ModalityEstimate
from asar.fusion import ReliabilityWeightedFusion


def test_reliability_weights_state_estimate() -> None:
    state = ReliabilityWeightedFusion().fuse(
        [
            ModalityEstimate("primary", {"x": 0.5}, 1.0),
            ModalityEstimate("secondary", {"x": 0.0}, 0.5),
        ]
    )
    assert abs(state.features["x"] - (0.5 / 1.5)) < 1e-6
    assert state.uncertainty >= 0.5


def test_disagreement_is_not_hidden() -> None:
    state = ReliabilityWeightedFusion().fuse(
        [
            ModalityEstimate("a", {"x": 0.7}, 1.0),
            ModalityEstimate("b", {"x": -0.7}, 1.0),
        ]
    )
    assert state.disagreements["x"] == 1.4
    assert state.uncertainty == 1.0


def test_empty_fusion_is_maximally_uncertain() -> None:
    state = ReliabilityWeightedFusion().fuse([])
    assert state.confidence == 0.0
    assert state.uncertainty == 1.0
