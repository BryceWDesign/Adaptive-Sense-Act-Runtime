from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evidence import EvidenceLedger
from .planner import BalancePlanner
from .scenarios import build_adaptive_surface_runtime
from .validation import run_validation


def _demo(args: argparse.Namespace) -> int:
    evidence_path = Path(args.evidence_out)
    if evidence_path.exists():
        evidence_path.unlink()
    runtime = build_adaptive_surface_runtime(evidence_path)
    print("Adaptive Sense-Act Runtime v0.1.0")
    print("Scenario: synthetic adaptive surface")
    print("Claim boundary: simulation only; no physical or clinical performance is claimed.")
    print()
    last = None
    for _ in range(args.cycles):
        last = runtime.cycle()
        before_error = BalancePlanner.error(last.before)
        after_error = BalancePlanner.error(last.after)
        print(
            f"cycle={last.cycle} before={before_error:.4f} after={after_error:.4f} "
            f"request={last.request.action}:{last.request.target} "
            f"authority={last.authority.disposition.value} "
            f"adapt_gain={last.adaptation.new_gain:.3f}"
        )
        if last.goal_reached:
            break
    verification = EvidenceLedger.verify_file(evidence_path)
    print()
    print(f"goal_reached={bool(last and last.goal_reached)}")
    print(f"evidence_chain={verification.passed} receipts={verification.count}")
    print(f"evidence_file={evidence_path}")
    return 0 if last and last.goal_reached and verification.passed else 1


def _verify(args: argparse.Namespace) -> int:
    result = EvidenceLedger.verify_file(Path(args.path))
    print(json.dumps({"passed": result.passed, "count": result.count, "issue": result.issue}, indent=2))
    return 0 if result.passed else 1


def _validate(_: argparse.Namespace) -> int:
    report = run_validation()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="asar", description="Adaptive Sense-Act Runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run the bundled synthetic adaptive-surface loop")
    demo.add_argument("--cycles", type=int, default=10)
    demo.add_argument("--evidence-out", default="artifacts/demo.evidence.jsonl")
    demo.set_defaults(func=_demo)

    verify = sub.add_parser("verify", help="verify a JSONL evidence chain")
    verify.add_argument("path")
    verify.set_defaults(func=_verify)

    validate = sub.add_parser("validate", help="run deterministic release validation scenarios")
    validate.set_defaults(func=_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
