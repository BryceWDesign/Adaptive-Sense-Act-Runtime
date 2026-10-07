# Adaptive Sense-Act Runtime

**A domain-neutral runtime for uncertainty-aware sensing, bounded actuation, closed-loop adaptation, and reproducible system evidence.**

Adaptive Sense-Act Runtime (ASAR) is a simulation-first software prototype for systems that need to **sense a state, decide what response to propose, independently constrain that response, execute only the granted action, observe the result, and adapt from what actually happened**.

The first reference adapter is a synthetic adaptive surface with a pressure map, an independent posture channel, and bounded haptic feedback. It exists to demonstrate the reusable control architecture, not to claim performance for any particular bed, wearable, horse interface, medical system, robot, drone, or patented device.

**Version:** 0.1.0
**Maintainer:** Bryce Lovell
**License:** Source-Available Evaluation License v1.0
**Status:** Working software prototype; simulation only; not production, clinical, field, or safety-critical software.

## Why this exists

Many adaptive physical-system concepts can be expressed as the same engineering loop:

```text
SENSE
  -> check signal health
  -> estimate state
  -> expose uncertainty/disagreement
  -> propose a response
  -> independently authorize / bound / deny it
  -> execute only the granted action
  -> sense the result
  -> adapt from observed outcome
  -> record evidence that can be replayed and verified
```

ASAR makes those boundaries explicit instead of placing sensing, inference, adaptation, and physical authority inside one opaque controller.

## What v0.1.0 actually implements

### Signal quality before inference

Required sensor channels are checked for missing fields, non-finite values, configured ranges, and stale data. An invalid required modality can block physical authority before execution.

### Reliability-weighted multimodal fusion

Domain adapters translate sensor-specific data into shared state features. ASAR fuses those features using signal quality as reliability weight and exposes cross-modality disagreement as runtime uncertainty.

### Independent physical authority

The planner is allowed to **request** an action. It is not allowed to execute one.

`IndependentActionAuthority` evaluates:

- allowed action kinds;
- allowed targets;
- required sensor health;
- fused uncertainty;
- configured actuator channels; and
- per-parameter actuator limits.

The result is explicit:

```text
ALLOW   -> requested action remains inside the current envelope
MODIFY  -> action may execute only with bounded parameters
DENY    -> actuator execution does not occur
```

### Generalized actuator envelope

The reference surface uses bounded channels for:

- haptic amplitude;
- frequency; and
- duration.

Those are only the first adapter. The authority contract is parameterized so future domain adapters can define their own measurable channels and limits instead of inheriting a robot-specific force/speed interface.

### Closed-loop reassessment

After an authorized synthetic action, ASAR senses the state again. Planner adaptation uses the **observed post-action state**, not an assumption that execution produced the desired effect.

### Bounded adaptation

The bundled adapter may change proposal gain when observed improvement is weak or worsening. It cannot modify physical limits, required sensors, or uncertainty stop thresholds. Every adapted proposal must pass through independent authority again.

### Tamper-evident evidence

Every closed-loop cycle is stored as a canonical JSON receipt in a SHA-256 hash chain. The chain binds the observed state, quality reports, proposed action, authority decision, execution result, post-action state, adaptation decision, and goal state for that cycle.

`asar verify` independently recomputes sequence and chain integrity from disk.

The evidence chain is tamper-evident, not tamper-proof. It is not digitally signed or externally anchored; a party with full write access could replace the complete chain and recompute its digests.

## Reference architecture

```text
Pressure / posture / future domain sensors
                  |
                  v
        Signal-quality checks
                  |
                  v
      Modality state estimates
                  |
                  v
 Reliability-weighted fusion
 disagreement -> uncertainty
                  |
                  v
          Proposal planner
                  |
                  v
      Independent authority
          /      |      \
       DENY    MODIFY   ALLOW
        |         |        |
        |         +---+----+
        |             v
        |      Bounded actuator
        |             |
        |             v
        |      Observe result again
        |             |
        +-------------v
             Outcome comparison
                    |
                    v
            Guarded adaptation
                    |
                    v
         Hash-chained evidence
                    |
                    +----> next cycle
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the subsystem boundaries.

## Quick start

Work from the repository root.

### Windows PowerShell

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m asar.cli demo --evidence-out artifacts\demo.evidence.jsonl
.\.venv\Scripts\python.exe -m asar.cli verify artifacts\demo.evidence.jsonl
.\.venv\Scripts\python.exe scripts\verify_release.py
.\.venv\Scripts\python.exe scripts\verify_manifest.py
```

### Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m asar.cli demo --evidence-out artifacts/demo.evidence.jsonl
.venv/bin/python -m asar.cli verify artifacts/demo.evidence.jsonl
.venv/bin/python scripts/verify_release.py
.venv/bin/python scripts/verify_manifest.py
```

The runtime itself has no third-party runtime dependencies. `pytest` is only required to run the test suite.

## Bundled demo

The committed configuration starts with a synthetic four-zone pressure imbalance. A separate simulated posture channel provides another estimate of the same left/right and fore/aft state.

A typical v0.1.0 run begins with an error near `0.4141`. The first haptic request exceeds the configured amplitude envelope and is therefore **MODIFIED** before execution. Subsequent authorized cycles re-observe the state, and the committed deterministic fixture reaches the configured balance tolerance after 9 cycles.

Representative run:

```text
cycle=0 before=0.4141 after=0.2165 authority=MODIFY
cycle=1 before=0.2165 after=0.1572 authority=ALLOW
...
cycle=8 before=0.0430 after=0.0349 authority=ALLOW

goal_reached=True
evidence_chain=True receipts=9
```

That convergence is a property of the synthetic response fixture. It is **not** evidence that a real person, animal, haptic textile, adaptive bed, robotic surface, or other physical system would respond this way.

See [`docs/DEMO.md`](docs/DEMO.md) and [`VALIDATION_REPORT.md`](VALIDATION_REPORT.md).

## Deterministic validation campaign

Run:

```bash
python -m asar.cli validate
```

v0.1.0 exercises seven explicit scenarios:

1. nominal closed-loop convergence;
2. high uncertainty blocks execution;
3. an invalid required sensor blocks execution;
4. out-of-envelope parameters are bounded before execution;
5. contradictory modalities surface high uncertainty;
6. evidence tampering is detected; and
7. adaptation remains inside its configured bounds.

Local release verification on Python 3.13.5 at handoff:

```text
25 tests passed
7 / 7 deterministic validation scenarios passed
compile check passed
release verification passed
```

The GitHub Actions workflow defines the same test and validation path for Ubuntu and Windows on Python 3.11, 3.12, and 3.13. Those matrix jobs must run in GitHub before claiming CI-green status for the public repository.

## What ASAR can become

ASAR is deliberately domain-neutral. A real integration would add a domain adapter that defines:

- sensor contracts and calibrated quality rules;
- state features and units;
- actuator channels and hard limits;
- domain-specific safety vetoes;
- hardware transport and watchdog behavior;
- outcome metrics;
- adaptation policy; and
- physical/HIL validation evidence.

That allows the same runtime pattern to support very different sense-act systems without pretending that the safety limits or scientific evidence from one domain transfer to another.

## What ASAR does not claim

ASAR v0.1.0 does **not** establish:

- medical diagnosis or treatment efficacy;
- emotional-state measurement or modification validity;
- human or animal safety;
- performance of piezoelectric or haptic materials;
- physical robot, drone, industrial, or power-system safety;
- biological sorting or genetic inference validity;
- regulatory approval;
- production readiness;
- formal verification; or
- rights to implement any third-party patented invention.

See [`docs/CLAIM_BOUNDARIES.md`](docs/CLAIM_BOUNDARIES.md).

## Relationship to earlier research

ASAR was produced after source-level review of three existing Bryce Lovell research repositories:

- **IX-HapticSight** contributed the architectural discipline of keeping physical authority separate from planning and using bounded, fail-closed action envelopes.
- **SynapDrive-AI** contributed the architectural discipline around signal quality, uncertainty, multimodal fusion, post-action reconciliation, and guarded adaptation.
- **IX-BlackFox** contributed the architectural discipline that capability is not authority and that consequential decisions should produce independently checkable evidence.

ASAR is a new composition with no donor repository required at runtime. See [`docs/DONOR_PROVENANCE.md`](docs/DONOR_PROVENANCE.md) for the exact boundary.

## Repository layout

```text
src/asar/
  interfaces.py    domain adapter + planner contracts
  adapters/        reference domain adapters
  quality.py       sensor-health checks
  fusion.py        reliability-weighted state fusion
  planner.py       reference proposal planner
  authority.py     independent ALLOW / MODIFY / DENY boundary
  actuator.py      bounded synthetic actuator adapter
  adaptation.py    post-outcome bounded adaptation
  evidence.py      canonical hash-chained receipts
  runtime.py       closed-loop orchestration
  surface.py       reference adaptive-surface fixture
  config.py        committed configuration loader
  validation.py    deterministic negative-control campaign

scripts/
  verify_release.py   local release verification
  build_manifest.py   SHA-256 release manifest builder
  verify_manifest.py  release manifest verifier

configs/
  adaptive_surface.json

docs/
  ARCHITECTURE.md
  CLAIM_BOUNDARIES.md
  DEMO.md
  DONOR_PROVENANCE.md

tests/
  executable unit and integration tests
```

## License

ASAR is source-available for evaluation under [`LICENSE`](LICENSE). It is not open-source software. The evaluation license does not grant commercial, production, operational, clinical, safety-critical, redistribution, or patent rights.
