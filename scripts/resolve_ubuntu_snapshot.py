from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def first_line(command: list[str]) -> str:
    proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return (proc.stdout.splitlines() or [""])[0].strip()


def load_transaction(path: Path) -> list[dict[str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        package, version, arch, filename, digest = line.split("\t")
        rows.append({"package": package, "version": version, "architecture": arch, "filename": filename, "sha256": digest})
    return sorted(rows, key=lambda x: (x["package"], x["architecture"], x["version"], x["filename"]))


def full_manifest() -> list[dict[str, str]]:
    out = subprocess.check_output(["dpkg-query", "-W", "-f=${Package}\t${Version}\t${Architecture}\n"], text=True)
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        package, version, arch = line.split("\t")
        rows.append({"package": package, "version": version, "architecture": arch})
    return sorted(rows, key=lambda x: (x["package"], x["architecture"], x["version"]))


def executable_record(name: str) -> dict[str, str]:
    path = shutil.which(name)
    if not path:
        raise RuntimeError(f"required executable not found: {name}")
    resolved = str(Path(path).resolve())
    version = first_line([path, "--version"])
    return {"name": name, "path": path, "resolved_path": resolved, "sha256": sha256_file(Path(resolved)), "version": version}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", required=True)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--transaction", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--executables", nargs="+", required=True)
    ap.add_argument("--direct-packages", nargs="+", required=True)
    args = ap.parse_args()
    payload = {
        "lane": args.lane,
        "snapshot_id": args.snapshot,
        "direct_packages": args.direct_packages,
        "apt_transaction_packages": load_transaction(Path(args.transaction)),
        "post_install_packages": full_manifest(),
        "executables": [executable_record(x) for x in args.executables],
    }
    Path(args.output).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
