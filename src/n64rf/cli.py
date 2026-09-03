from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters.registry import get_adapter, list_adapters
from .wrapper import inspect_rom, wrapper_passed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="N64 ROM Forge read-only intake wrapper")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="Inspect a ROM without modifying it")
    inspect_p.add_argument("rom_path")
    inspect_p.add_argument("--adapter", default="auto")
    inspect_p.add_argument("--receipt", help="Optional JSON receipt path; metadata only")

    verify_p = sub.add_parser("verify", help="Verify a ROM against one explicit Game Adapter")
    verify_p.add_argument("rom_path")
    verify_p.add_argument("--adapter", required=True)
    verify_p.add_argument("--receipt", help="Optional JSON receipt path; metadata only")

    adapters_p = sub.add_parser("adapters", help="Inspect the Game Adapter registry")
    adapters_p.add_argument("action", choices=["list", "show"])
    adapters_p.add_argument("adapter_id", nargs="?")
    return parser


def _write_receipt(receipt_path: str | None, rom_path: str, rendered: str) -> None:
    if not receipt_path:
        return
    out = Path(receipt_path)
    if out.resolve() == Path(rom_path).resolve():
        raise SystemExit("refusing to overwrite source ROM with receipt")
    out.write_text(rendered + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "adapters":
        if args.action == "list":
            print(json.dumps({"adapters": list_adapters()}, indent=2))
            return 0
        if not args.adapter_id:
            raise SystemExit("adapters show requires <adapter_id>")
        print(json.dumps(get_adapter(args.adapter_id).__dict__, indent=2, default=lambda value: value.__dict__))
        return 0

    receipt = inspect_rom(args.rom_path, args.adapter)
    rendered = json.dumps(receipt.to_dict(), indent=2, sort_keys=True)
    print(rendered)
    _write_receipt(args.receipt, args.rom_path, rendered)
    return 0 if wrapper_passed(receipt) else 2


if __name__ == "__main__":
    raise SystemExit(main())
