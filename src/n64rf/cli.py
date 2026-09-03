from __future__ import annotations

import argparse, json
from dataclasses import asdict
from pathlib import Path
from .adapters.registry import get_adapter, list_adapters
from .wrapper import inspect_rom, verify_rom

def _write_receipt(source: Path, destination: str | None, payload: dict) -> None:
    if destination is None: return
    output = Path(destination)
    if output.resolve() == source.resolve(): raise SystemExit("refusing to overwrite source ROM with receipt")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="N64 ROM Forge read-only intake wrapper"); sub = parser.add_subparsers(dest="command", required=True)
    inspect_p = sub.add_parser("inspect", help="Inspect a ROM without modifying it"); inspect_p.add_argument("rom_path"); inspect_p.add_argument("--adapter", default="auto"); inspect_p.add_argument("--receipt", help="Optional metadata-only JSON receipt path")
    verify_p = sub.add_parser("verify", help="Verify a ROM against one explicit Game Adapter"); verify_p.add_argument("rom_path"); verify_p.add_argument("--adapter", required=True); verify_p.add_argument("--receipt", help="Optional metadata-only JSON receipt path")
    adapters_p = sub.add_parser("adapters", help="Inspect the Game Adapter registry"); adapters_p.add_argument("action", choices=["list", "show"]); adapters_p.add_argument("adapter_id", nargs="?")
    args = parser.parse_args(argv)
    if args.command == "adapters":
        if args.action == "list": print(json.dumps({"adapters": list_adapters()}, indent=2)); return 0
        if not args.adapter_id: raise SystemExit("adapters show requires adapter_id")
        print(json.dumps(asdict(get_adapter(args.adapter_id)), indent=2, sort_keys=True)); return 0
    source = Path(args.rom_path); receipt = inspect_rom(source, args.adapter) if args.command == "inspect" else verify_rom(source, args.adapter); payload = receipt.to_dict(); print(json.dumps(payload, indent=2, sort_keys=True)); _write_receipt(source, args.receipt, payload)
    adapter_ok = payload["adapter"].get("status") == "MATCHED"; checksum_ok = payload["checksum"].get("status") in {"PASS", "NOT_RUN"}; source_ok = payload["source_integrity"].get("unchanged") is True
    return 0 if adapter_ok and checksum_ok and source_ok else 2
