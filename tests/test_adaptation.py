from asar.adaptation import GuardedPlannerAdapter
from asar.contracts import Disposition


def test_denied_action_does_not_adapt() -> None:
    adapter = GuardedPlannerAdapter()
    result = adapter.update(
        current_gain=1.2,
        before_error=0.5,
        after_error=0.5,
        disposition=Disposition.DENY,
    )
    assert not result.changed
    assert result.new_gain == 1.2


def test_weak_improvement_can_raise_proposal_gain_but_not_beyond_cap() -> None:
    adapter = GuardedPlannerAdapter(maximum_gain=1.3)
    gain = 1.2
    for _ in range(20):
        gain = adapter.update(
            current_gain=gain,
            before_error=1.0,
            after_error=0.99,
            disposition=Disposition.ALLOW,
        ).new_gain
    assert gain == 1.3


def test_worse_outcome_reduces_gain() -> None:
    adapter = GuardedPlannerAdapter()
    result = adapter.update(
        current_gain=1.5,
        before_error=0.5,
        after_error=0.7,
        disposition=Disposition.ALLOW,
    )
    assert result.changed
    assert result.new_gain < 1.5
