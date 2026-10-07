# Claim boundaries

ASAR v0.1.0 is a software prototype and simulation harness.

## What this release demonstrates

- executable signal-health checks before state estimation;
- reliability-weighted multimodal fusion;
- explicit sensor disagreement and uncertainty;
- separation between a proposal layer and an independent action-authority layer;
- parameter-level actuator envelopes with `ALLOW`, `MODIFY`, and `DENY` outcomes;
- a deterministic closed loop that observes the post-action state before adapting;
- bounded adaptation that cannot raise physical limits;
- tamper-evident, hash-chained cycle evidence; and
- deterministic negative-control validation scenarios.

## What this release does not demonstrate

- safety or efficacy on a real person or animal;
- medical diagnosis, treatment, prevention, or emotional-state modification;
- clinical validity or regulatory compliance;
- real piezoelectric, haptic, robotic, drone, industrial, or power-system control;
- calibrated physical actuator limits;
- trained AI or learned biological inference;
- production readiness, certification, or formal verification; or
- compatibility with any specific patented device.

The adaptive-surface response model is synthetic test data. Its convergence result is evidence
about the software loop under that fixture, not evidence that a person, animal, surface, or
physical device would respond the same way.
