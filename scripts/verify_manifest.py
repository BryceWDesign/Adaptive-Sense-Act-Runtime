from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"


def main() -> int:
    if not MANIFEST.is_file():
        print("manifest missing")
        return 1
    issues: list[str] = []
    checked = 0
    for raw in MANIFEST.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            expected, relative = raw.split("  ", 1)
        except ValueError:
            issues.append(f"invalid row: {raw}")
            continue
        path = ROOT / relative
        if not path.is_file():
            issues.append(f"missing: {relative}")
            continue
        observed = hashlib.sha256(path.read_bytes()).hexdigest()
        if observed != expected:
            issues.append(f"digest mismatch: {relative}")
        checked += 1
    if issues:
        for issue in issues:
            print(issue)
        print(f"manifest verification failed: checked={checked} issues={len(issues)}")
        return 1
    print(f"manifest verification passed: checked={checked}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
