from __future__ import annotations

import fnmatch
import sys
from pathlib import Path

FORBIDDEN_FILE_PATTERNS = ("*.z64", "*.v64", "*.n64", "baserom.*", "*.bps")
FORBIDDEN_DIRS = {"build", "roms", "private-roms", ".git"}

def find_forbidden(root: str | Path) -> list[str]:
    root = Path(root)
    findings: list[str] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if any(part in FORBIDDEN_DIRS for part in rel.parts):
            if path.is_file():
                findings.append(rel.as_posix())
            continue
        if path.is_file() and any(fnmatch.fnmatch(path.name, pat) for pat in FORBIDDEN_FILE_PATTERNS):
            findings.append(rel.as_posix())
    return sorted(set(findings))

def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    root = Path(argv[0]) if argv else Path(".")
    findings = find_forbidden(root)
    if findings:
        print("Forbidden payload(s) detected:", file=sys.stderr)
        for item in findings:
            print(f" - {item}", file=sys.stderr)
        return 2
    print("Forbidden payload guard: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
