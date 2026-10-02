from __future__ import annotations

from pathlib import Path
import argparse
import json
import struct

from mips_common import decode, is_delay_slot_source


def disassemble(
    data: bytes,
    start: int,
    count: int,
    *,
    rom_base: int = 0x1000,
    vram_base: int = 0x80000400,
) -> list[dict[str, object]]:
    offset = rom_base + (start - vram_base)
    rows: list[dict[str, object]] = []
    delay_source: int | None = None

    for index in range(count):
        file_offset = offset + index * 4
        pc = start + index * 4
        if file_offset < 0 or file_offset + 4 > len(data):
            break
        word = struct.unpack_from(">I", data, file_offset)[0]
        row: dict[str, object] = {
            "pc": pc,
            "pc_hex": f"0x{pc:08X}",
            "rom_offset": file_offset,
            "word": word,
            "word_hex": f"0x{word:08X}",
            "asm": decode(word, pc),
            "delay_slot_of": f"0x{delay_source:08X}" if delay_source is not None else None,
        }
        rows.append(row)
        delay_source = None
        if is_delay_slot_source(word):
            delay_source = pc

    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Minimal N64/VR4300 big-endian disassembler.")
    ap.add_argument("rom")
    ap.add_argument("start", type=lambda x: int(x, 0))
    ap.add_argument("count", type=int)
    ap.add_argument("--rom-base", type=lambda x: int(x, 0), default=0x1000)
    ap.add_argument("--vram-base", type=lambda x: int(x, 0), default=0x80000400)
    ap.add_argument("--json", action="store_true", help="Emit structured rows instead of text.")
    args = ap.parse_args()
    rows = disassemble(
        Path(args.rom).read_bytes(),
        args.start,
        args.count,
        rom_base=args.rom_base,
        vram_base=args.vram_base,
    )
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0

    for row in rows:
        metadata = ""
        if row["delay_slot_of"] is not None:
            metadata = f"  ; delay_slot_of={row['delay_slot_of']}"
        print(
            f"{int(row['pc']):08X}  {int(row['word']):08X}  "
            f"{str(row['asm'])}{metadata}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
