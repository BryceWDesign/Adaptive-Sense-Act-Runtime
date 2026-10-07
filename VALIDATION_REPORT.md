# Adaptive Sense-Act Runtime v0.1.0 Validation Report

**Validation environment:** Python 3.13.5, Linux container
**Evidence scope:** software tests and deterministic simulation only.

## Release verification

Observed local results at handoff:

- Python compile check: PASS
- automated test suite: **25 passed**
- deterministic validation campaign: **7 / 7 scenarios passed**
- editable package install with `--no-build-isolation --no-deps`: PASS
- CLI adaptive-surface demo: PASS
- demo convergence: **9 closed-loop cycles** under the committed synthetic fixture
- demo evidence-chain verification: PASS, **9 receipts**
- alternate scalar domain-adapter integration test: PASS

## Deterministic validation scenarios

1. Nominal closed-loop convergence: PASS
2. High uncertainty denies execution: PASS
3. Invalid required sensor denies execution: PASS
4. Out-of-envelope actuator request is bounded: PASS
5. Cross-modality disagreement surfaces uncertainty: PASS
6. Hash-chain tampering is detected: PASS
7. Adaptation remains within configured bounds: PASS

## Domain-neutrality check

The test suite constructs a second, non-surface adapter with a scalar sensor and scalar actuator.
It runs through the same `SenseActRuntime`, quality gate, fusion, independent authority,
post-action observation, adaptation, and evidence path. This verifies that the orchestration
runtime is not hardwired to the bundled pressure/haptic example.

## Physical / clinical evidence

None.

No HIL rig, person, animal, medical device, piezoelectric textile, robot, drone, industrial
machine, or power system was connected for this release. The bundled adaptive-surface response
is a deterministic software fixture and must not be interpreted as measured physical behavior.

## CI status

The repository defines a GitHub Actions matrix for Ubuntu and Windows on Python 3.11, 3.12,
and 3.13. Those jobs have not been observed from this local handoff environment. Public CI
should be considered unverified until the repository is pushed and the workflow completes.
