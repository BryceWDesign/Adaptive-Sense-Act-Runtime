# Demo: synthetic adaptive surface

The first reference scenario is intentionally small enough to falsify.

A synthetic four-zone surface begins with an asymmetric pressure distribution. Two independent
modalities estimate left/right and fore/aft imbalance:

1. the pressure map itself; and
2. a simulated independent posture channel.

The runtime checks each signal, fuses the state, proposes a haptic cue, asks the independent
authority for execution permission, applies only the granted parameters, observes the new state,
and then decides whether planner gain should change.

Run:

```bash
python -m pip install -e .
asar demo --evidence-out artifacts/demo.evidence.jsonl
asar verify artifacts/demo.evidence.jsonl
```

Expected behavior under the committed fixture:

- the first action is a bounded haptic cue;
- actuator parameters outside the configured envelope are never applied;
- the estimated imbalance falls over successive observed cycles;
- the loop reaches the configured balance tolerance; and
- the evidence chain verifies after the run.

This scenario is not intended to simulate a specific patented horse blanket, medical bed, or
other physical product. It demonstrates the reusable control/validation layer beneath a class of
sense-act-feedback systems.
