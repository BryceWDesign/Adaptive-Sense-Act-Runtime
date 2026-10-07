# Architecture

Adaptive Sense-Act Runtime (ASAR) separates interpretation from physical authority.

```text
sensor frames
    |
    v
signal quality checks
    |
    v
modality-specific state estimates
    |
    v
reliability-weighted fusion + disagreement/uncertainty
    |
    v
planner proposes an action
    |
    v
independent action authority  ----DENY----> no actuator execution
    |
    | ALLOW / MODIFY
    v
bounded actuator adapter
    |
    v
observe resulting state
    |
    v
outcome comparison + bounded planner adaptation
    |
    v
tamper-evident evidence receipt
    +-------------------------------> next cycle
```

## Boundary 1: sensing does not equal truth

Each required modality is checked for missing fields, non-finite values, configured ranges,
and age. Invalid required modalities cause physical authority to fail closed.

## Boundary 2: disagreement is visible

Modalities are converted into shared, normalized features and fused using quality as a reliability weight.
A domain adapter is responsible for mapping raw physical units into comparable bounded features before fusion.
Cross-modality disagreement contributes directly to uncertainty rather than being hidden by an average.

## Boundary 3: planning does not equal authority

The planner can request an action. It cannot execute one. `IndependentActionAuthority` checks:

- action and target allowlists;
- required sensor health;
- fused uncertainty;
- allowed actuator parameters; and
- parameter envelopes.

The authority returns `ALLOW`, `MODIFY`, or `DENY`.

## Boundary 4: adaptation cannot expand physical authority

The bundled adaptation mechanism changes only planner gain. It cannot change actuator limits,
required modalities, or uncertainty stop thresholds. Every adapted request is re-evaluated by
the independent authority.

## Boundary 5: evidence is independently checkable

Each closed-loop cycle is serialized into a canonical JSON payload and appended to a SHA-256
hash chain. `asar verify` recomputes sequence and chain integrity from disk.

## Reference adapter

The bundled adaptive-surface adapter is deliberately synthetic. It presents two modalities:

- a four-zone pressure map; and
- an independent posture estimate of left/right and fore/aft bias.

A haptic cue changes the simulated pressure distribution according to a deterministic response
fixture. This demonstrates control wiring only. It is not a model of human or animal behavior.
