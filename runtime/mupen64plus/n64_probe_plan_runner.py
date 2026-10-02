from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import threading
import time


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a timed Mupen64Plus debugger probe plan.")
    ap.add_argument("plan")
    ap.add_argument("--runtime", required=True)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    rom = Path(plan["rom_path"])
    sha = hashlib.sha256(rom.read_bytes()).hexdigest()
    if sha.lower() != plan["rom_sha256"].lower():
        raise SystemExit(f"ROM SHA256 mismatch: {sha}")
    runtime = Path(args.runtime)
    cmd = [
        str(runtime / "mupen64plus-ui-console.exe"),
        "--debug", "--emumode", "1", "--windowed", "--resolution", "640x480",
        "--plugindir", str(runtime),
        "--gfx", "mupen64plus-video-rice.dll",
        "--audio", "dummy",
        "--input", "mupen64plus-input-sdl.dll",
        "--rsp", "mupen64plus-rsp-hle.dll",
        str(rom),
    ]

    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        cmd, cwd=runtime, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    lines: list[str] = []
    lock = threading.Lock()
    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            with lock:
                lines.append(line)
            with log_path.open("a", encoding="utf-8", errors="replace") as f:
                f.write(line)

    threading.Thread(target=reader, daemon=True).start()
    time.sleep(plan.get("startup_delay_ms", 2500) / 1000)

    assert proc.stdin is not None
    for step in plan["commands"]:
        if proc.poll() is not None:
            break
        proc.stdin.write(step["command"] + "\n")
        proc.stdin.flush()
        time.sleep(step.get("delay_after_ms", 0) / 1000)

    deadline = time.time() + plan.get("timeout_seconds", 45)
    while proc.poll() is None and time.time() < deadline:
        time.sleep(0.1)
    if proc.poll() is None:
        try:
            proc.stdin.write("quit\n")
            proc.stdin.flush()
        except Exception:
            pass
        time.sleep(0.5)
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()

    with lock:
        text = "".join(lines)
    receipt = {
        "schema": "n64.probe_plan_run.v1",
        "plan": str(Path(args.plan)),
        "runtime": str(runtime),
        "rom_sha256": sha,
        "returncode": proc.returncode,
        "log": str(log_path),
        "breakpoint_hits": text.count("Breakpoint @ PC"),
        "debugger_initialized": "Debugger initialized." in text,
    }
    receipt_path = log_path.with_suffix(".receipt.json")
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
