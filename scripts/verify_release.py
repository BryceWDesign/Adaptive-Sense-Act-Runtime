from __future__ import annotations

import compileall
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from asar.validation import write_validation_report  # noqa: E402


def main() -> int:
    compile_ok = compileall.compile_dir(SRC, quiet=1)
    report = write_validation_report(ROOT / "artifacts" / "validation-report.json")
    required = [
        ROOT / "LICENSE",
        ROOT / "README.md",
        ROOT / "VALIDATION_REPORT.md",
        ROOT / "docs" / "ARCHITECTURE.md",
        ROOT / "docs" / "CLAIM_BOUNDARIES.md",
        ROOT / "docs" / "DONOR_PROVENANCE.md",
        ROOT / "configs" / "adaptive_surface.json",
    ]
    files_ok = all(path.is_file() and path.stat().st_size > 0 for path in required)
    summary = {
        "schema": "asar-release-verification-v1",
        "compile": compile_ok,
        "required_files": files_ok,
        "validation": report["passed"],
        "validation_scenarios": report["scenario_count"],
        "validation_passed": report["pass_count"],
        "passed": bool(compile_ok and files_ok and report["passed"]),
    }
    (ROOT / "artifacts" / "release-verification.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
