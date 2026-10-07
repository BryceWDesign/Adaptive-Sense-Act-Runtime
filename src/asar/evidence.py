from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import jsonable

GENESIS = "0" * 64


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    count: int
    issue: str | None = None


class EvidenceLedger:
    """Small append-only hash chain for deterministic prototype evidence receipts."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._entries: list[dict[str, Any]] = []

    @property
    def entries(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._entries)

    def append(self, event_type: str, payload: Any) -> str:
        sequence = len(self._entries)
        previous_digest = self._entries[-1]["digest"] if self._entries else GENESIS
        core = {
            "sequence": sequence,
            "previous_digest": previous_digest,
            "event_type": str(event_type),
            "payload": jsonable(payload),
        }
        entry = {**core, "digest": digest(core)}
        self._entries.append(entry)
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
                stream.write("\n")
        return str(entry["digest"])

    @staticmethod
    def verify_entries(entries: Iterable[dict[str, Any]]) -> VerificationResult:
        previous = GENESIS
        count = 0
        for expected_sequence, entry in enumerate(entries):
            if set(entry) != {"sequence", "previous_digest", "event_type", "payload", "digest"}:
                return VerificationResult(False, count, "unexpected_fields")
            if entry["sequence"] != expected_sequence:
                return VerificationResult(False, count, "sequence_mismatch")
            if entry["previous_digest"] != previous:
                return VerificationResult(False, count, "previous_digest_mismatch")
            core = {
                "sequence": entry["sequence"],
                "previous_digest": entry["previous_digest"],
                "event_type": entry["event_type"],
                "payload": entry["payload"],
            }
            expected_digest = digest(core)
            if entry["digest"] != expected_digest:
                return VerificationResult(False, count, "digest_mismatch")
            previous = expected_digest
            count += 1
        return VerificationResult(True, count, None)

    @classmethod
    def verify_file(cls, path: Path) -> VerificationResult:
        entries: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as stream:
                for line in stream:
                    if line.strip():
                        value = json.loads(line)
                        if not isinstance(value, dict):
                            return VerificationResult(False, len(entries), "entry_not_object")
                        entries.append(value)
        except (OSError, UnicodeError, json.JSONDecodeError):
            return VerificationResult(False, len(entries), "invalid_jsonl")
        return cls.verify_entries(entries)
