from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hash_environment import canonical_digest, digest_without_fields
from verify_objdiff import download_and_verify
from verify_scaffold import run as verify_scaffold

PLAN_PATH = ROOT / "config" / "environment.freeze.plan.json"


def cmd(args: list[str], *, capture: bool = True) -> str:
    p = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE if capture else None, stderr=subprocess.STDOUT if capture else None, check=True)
    return p.stdout.strip() if capture else ""


def verify_plan(plan: dict) -> None:
    observed = digest_without_fields(plan, "plan_digest", "plan_digest_rule")
    if observed != plan["plan_digest"]:
        raise RuntimeError(f"plan digest mismatch: {observed} != {plan['plan_digest']}")
    base = plan["base"]["commit"]
    cmd(["git", "cat-file", "-e", base + "^{commit}"])
    subprocess.run(["git", "merge-base", "--is-ancestor", base, "HEAD"], cwd=ROOT, check=True)
    base_tree = cmd(["git", "show", "-s", "--format=%T", base])
    if base_tree != plan["base"]["tree"]:
        raise RuntimeError(f"base tree drift: {base_tree}")


def verify_index(index_digest: str, expected_amd64: str) -> dict:
    raw = cmd(["docker", "buildx", "imagetools", "inspect", "--raw", f"ubuntu@{index_digest}"])
    data = json.loads(raw)
    matches = [m for m in data.get("manifests", []) if m.get("platform", {}).get("os") == "linux" and m.get("platform", {}).get("architecture") == "amd64"]
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one linux/amd64 manifest in {index_digest}")
    observed = matches[0].get("digest")
    if observed != expected_amd64:
        raise RuntimeError(f"amd64 manifest mismatch for {index_digest}: {observed} != {expected_amd64}")
    return {"index_digest": index_digest, "amd64_manifest_digest": observed}


def build_lane(name: str, dockerfile: str, manifest_digest: str) -> dict:
    tag = f"n64rf-env-freeze:{name}"
    cmd(["docker", "build", "--pull", "--no-cache", "-f", dockerfile, "-t", tag, "."], capture=False)
    image_id = cmd(["docker", "image", "inspect", tag, "--format={{.Id}}"])
    cid = cmd(["docker", "create", tag])
    try:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "lane.json"
            cmd(["docker", "cp", f"{cid}:/n64rf/evidence/lane.json", str(out)], capture=False)
            lane = json.loads(out.read_text(encoding="utf-8"))
    finally:
        subprocess.run(["docker", "rm", "-f", cid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    lane["derived_image_id"] = image_id
    lane["base_manifest_digest"] = manifest_digest
    return lane


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    verify_plan(plan)
    scaffold = verify_scaffold(ROOT)

    images = {lane: verify_index(spec["index_digest"], spec["amd64_manifest_digest"]) for lane, spec in plan["base_images"].items()}

    lanes = {
        "vanilla_reference": build_lane("vanilla-reference", "docker/env/vanilla-reference.Dockerfile", plan["base_images"]["vanilla_reference"]["amd64_manifest_digest"]),
        "hackersm64": build_lane("hackersm64", "docker/env/hackersm64.Dockerfile", plan["base_images"]["hackersm64"]["amd64_manifest_digest"]),
    }

    obj = plan["upstreams"]["objdiff"]
    with tempfile.TemporaryDirectory() as td:
        obj_path = Path(td) / obj["asset"]
        observed_obj = download_and_verify(f"https://github.com/encounter/objdiff/releases/download/{obj['tag']}/{obj['asset']}", obj["sha256"], obj_path)
    if observed_obj["size"] != obj["size"]:
        raise RuntimeError(f"objdiff size mismatch: {observed_obj['size']} != {obj['size']}")

    lock = {
        "schema": "n64rf.environment-lock.v1",
        "canonicalization": "n64rf-canonical-json-v1",
        "repository": {
            "name": plan["repository"], "base_branch": plan["base"]["branch"], "base_commit": plan["base"]["commit"], "base_tree": plan["base"]["tree"],
            "freeze_branch_commit": cmd(["git", "rev-parse", "HEAD"]), "freeze_branch_tree": cmd(["git", "show", "-s", "--format=%T", "HEAD"]),
        },
        "source_pins": plan["upstreams"],
        "base_images": images,
        "snapshots": plan["snapshots"],
        "lanes": lanes,
        "objdiff": {**obj, "observed_sha256": observed_obj["sha256"], "observed_size": observed_obj["size"], "version": observed_obj["version"]},
        "project_built_tools": {"policy": plan["project_built_tools_policy"], "status": "BLOCKED_FOR_PHASE0", "reason": "No ROM-dependent project-built executable is used by this environment-freeze gate."},
        "scaffold_verification": {"compileall": scaffold["compileall"], "schemas_parse": scaffold["schemas_parse"], "unit_tests": scaffold["unit_tests"], "forbidden_payload_guard": scaffold["forbidden_payload_guard"]},
        "network_boundary": plan["workflow"]["network"],
    }
    lock["environment_lock_digest"] = canonical_digest(lock)

    receipt = {
        "schema": "n64rf.environment-freeze-receipt.v1", "task": plan["task"], "plan_id": plan["plan_id"], "plan_digest": plan["plan_digest"], "result": "PASS",
        "repository": plan["repository"], "base_commit": plan["base"]["commit"], "freeze_commit": lock["repository"]["freeze_branch_commit"], "environment_lock_digest": lock["environment_lock_digest"],
        "objdiff_sha256_verified": True, "base_images_verified": True, "package_transactions_frozen": True, "executable_hashes_frozen": True,
        "scaffold_verification": lock["scaffold_verification"],
        "side_effects": {"rom_access": False, "rom_build": False, "asset_extraction": False, "patch_generation": False, "generated_lock_persisted_by_ci": True, "repository_commit_performed_by_ci": False},
    }

    (ROOT / "config" / "environment.lock.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "evidence").mkdir(exist_ok=True)
    (ROOT / "evidence" / "environment-freeze-receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("ENVIRONMENT_LOCK_DIGEST=" + lock["environment_lock_digest"])
    print("RESULT=PASS")


if __name__ == "__main__":
    main()
