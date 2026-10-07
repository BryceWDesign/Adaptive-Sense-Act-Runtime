from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "MANIFEST.sha256"
EXCLUDED = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}


def included(path: Path) -> bool:
    if path == OUTPUT or not path.is_file():
        return False
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED or part.endswith(".egg-info") for part in relative.parts):
        return False
    if relative.parts[:1] == ("artifacts",) and relative.suffix == ".jsonl":
        return False
    if relative.suffix in {".pyc", ".pyo"}:
        return False
    return True


def main() -> int:
    rows: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not included(path):
            continue
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{sha}  {path.relative_to(ROOT).as_posix()}")
    OUTPUT.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} entries to {OUTPUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
