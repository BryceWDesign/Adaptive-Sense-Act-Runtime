from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import Enum, StrEnum
from typing import Any


class Disposition(StrEnum):
    ALLOW = "ALLOW"
    MODIFY = "MODIFY"
    DENY = "DENY"


class ExecutionStatus(StrEnum):
    EXECUTED = "EXECUTED"
    HELD = "HELD"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class SensorFrame:
    modality: str
    values: Mapping[str, float]
    age_ms: float = 0.0


@dataclass(frozen=True)
class QualityReport:
    modality: str
    valid: bool
    score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ModalityEstimate:
    modality: str
    features: Mapping[str, float]
    quality: float


@dataclass(frozen=True)
class StateEstimate:
    features: Mapping[str, float]
    confidence: float
    uncertainty: float
    modalities: tuple[str, ...]
    disagreements: Mapping[str, float]


@dataclass(frozen=True)
class ActionRequest:
    action_id: str
    action: str
    target: str
    parameters: Mapping[str, float]
    rationale: str


@dataclass(frozen=True)
class AuthorityDecision:
    action_id: str
    disposition: Disposition
    granted_parameters: Mapping[str, float]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    action_id: str
    applied_parameters: Mapping[str, float]
    detail: str


@dataclass(frozen=True)
class AdaptationResult:
    changed: bool
    old_gain: float
    new_gain: float
    reason: str


@dataclass(frozen=True)
class CycleResult:
    cycle: int
    before: StateEstimate
    request: ActionRequest
    authority: AuthorityDecision
    execution: ExecutionResult
    after: StateEstimate
    adaptation: AdaptationResult
    goal_reached: bool
    evidence_digest: str


def jsonable(value: Any) -> Any:
    """Convert dataclasses/enums/tuples recursively into JSON-compatible values."""
    if hasattr(value, "__dataclass_fields__"):
        return jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [jsonable(item) for item in value]
    if isinstance(value, list):
        return [jsonable(item) for item in value]
    return value
