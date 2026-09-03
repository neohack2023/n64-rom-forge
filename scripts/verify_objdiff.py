from __future__ import annotations
import hashlib
import stat
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def download_and_verify(url: str, expected_sha256: str, output: Path) -> dict[str, str | int]:
    req = Request(url, headers={"User-Agent": "n64-rom-forge-phase0-env-freeze"})
    with urlopen(req, timeout=120) as response, output.open("wb") as dst:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
    observed = sha256_file(output)
    if observed != expected_sha256:
        raise RuntimeError(f"objdiff sha256 mismatch: expected {expected_sha256}, got {observed}")
    output.chmod(output.stat().st_mode | stat.S_IXUSR)
    proc = subprocess.run([str(output), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return {"path": str(output), "size": output.stat().st_size, "sha256": observed, "version": (proc.stdout.splitlines() or [""])[0].strip()}
