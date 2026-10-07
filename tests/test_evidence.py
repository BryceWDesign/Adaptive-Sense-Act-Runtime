import copy
from pathlib import Path

from asar.evidence import EvidenceLedger


def test_hash_chain_verifies_and_tamper_fails(tmp_path: Path) -> None:
    path = tmp_path / "evidence.jsonl"
    ledger = EvidenceLedger(path)
    ledger.append("a", {"x": 1})
    ledger.append("b", {"x": 2})

    valid = EvidenceLedger.verify_file(path)
    assert valid.passed
    assert valid.count == 2

    entries = [copy.deepcopy(item) for item in ledger.entries]
    entries[0]["payload"]["x"] = 99
    invalid = EvidenceLedger.verify_entries(entries)
    assert not invalid.passed
    assert invalid.issue == "digest_mismatch"


def test_reordering_fails() -> None:
    ledger = EvidenceLedger()
    ledger.append("a", {"x": 1})
    ledger.append("b", {"x": 2})
    entries = list(ledger.entries)
    entries.reverse()
    result = EvidenceLedger.verify_entries(entries)
    assert not result.passed
