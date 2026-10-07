from __future__ import annotations

from pathlib import Path

from asar.evidence import EvidenceLedger
from asar.planner import BalancePlanner
from asar.scenarios import build_adaptive_surface_runtime


def main() -> int:
    path = Path("artifacts/adaptive-surface-demo.jsonl")
    path.parent.mkdir(exist_ok=True)
    path.unlink(missing_ok=True)
    runtime = build_adaptive_surface_runtime(path)

    for _ in range(10):
        result = runtime.cycle()
        print(
            f"cycle={result.cycle:02d} "
            f"before={BalancePlanner.error(result.before):.4f} "
            f"after={BalancePlanner.error(result.after):.4f} "
            f"authority={result.authority.disposition.value:6s} "
            f"target={result.request.target:11s} "
            f"goal={result.goal_reached}"
        )
        if result.goal_reached:
            break

    verification = EvidenceLedger.verify_file(path)
    print(f"evidence_chain={verification.passed} receipts={verification.count}")
    return 0 if result.goal_reached and verification.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
