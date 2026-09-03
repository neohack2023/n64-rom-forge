from __future__ import annotations
import json
import os
import subprocess
import sys
from pathlib import Path


def run(root: Path) -> dict:
    checks = {}
    subprocess.run([sys.executable, "-m", "compileall", "-q", "src", "scripts"], cwd=root, check=True)
    checks["compileall"] = "PASS"

    for schema in sorted((root / "schemas").glob("*.json")):
        with schema.open("r", encoding="utf-8") as f:
            json.load(f)
    checks["schemas_parse"] = "PASS"

    env = os.environ.copy()
    env.pop("N64RF_GOLDENEYE_FIXTURE", None)
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    checks["unit_tests_output"] = tests.stdout
    if tests.returncode:
        raise RuntimeError("unit tests failed")
    checks["unit_tests"] = "PASS"

    forbidden = subprocess.run([sys.executable, "scripts/check_forbidden_payloads.py", "."], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    checks["forbidden_payload_output"] = forbidden.stdout
    if forbidden.returncode:
        raise RuntimeError("forbidden payload scan failed")
    checks["forbidden_payload_guard"] = "PASS"
    return checks
