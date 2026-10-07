# Donor provenance

ASAR v0.1.0 was designed after a source-level review of three existing Bryce Lovell research
repositories. The new runtime is a clean composition written for ASAR rather than a wholesale
merge of those projects.

## IX-HapticSight

Concepts retained and generalized:

- an independent physical-action authority separate from planning;
- explicit `ALLOW` / `MODIFY` / `DENY` outcomes;
- conservative multimodal veto behavior;
- bounded actuator envelopes; and
- hardware-in-the-loop / fail-closed validation discipline.

HapticSight's robot-contact-specific force/speed contract was not copied into ASAR. ASAR uses a
parameterized actuator envelope so a domain adapter can define its own bounded channels.

## SynapDrive-AI

Concepts retained and generalized:

- signal-quality gating;
- uncertainty as an explicit runtime quantity;
- reliability-weighted multimodal fusion;
- state estimation before action selection;
- post-action reality/outcome reconciliation; and
- guarded adaptation that remains subordinate to independent authority.

BCI/EEG-specific acquisition, decoding, terminology, and actions were intentionally excluded.

## IX-BlackFox

Concepts retained and generalized:

- capability/proposal is not authority;
- evidence should be bound to the exact decision/event it describes; and
- append-only, independently verifiable evidence should reveal tampering.

ASAR does not embed BlackFox's enterprise identity, delegated authorization, human review board,
MCP gateway, or cryptographic signing stack in v0.1.0. Those concerns are optional future outer
governance, not part of the physical control loop.

## Source-use boundary

ASAR's implementation was written specifically for this repository. No donor package is a runtime
dependency, and no donor repository needs to be installed to run ASAR.
