from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json

SOURCE_SHA256 = "7de1a8fb2a9558cfc3d9ad4497df698c1e89cf7095ac1531557df2af40ba8bcf"
PATCH_VRAM = 0x8008F344
ROM_BASE = 0x1000
VRAM_BASE = 0x80000400
PATCH_OFFSET = ROM_BASE + (PATCH_VRAM - VRAM_BASE)
EXPECTED_WORD = 0x10400008
REPLACEMENT_WORD = 0x00000000
CHECKSUM_START = 0x1000
CHECKSUM_LENGTH = 0x100000
CIC_6103_SEED = 0xA3886759


def rol32(value: int, bits: int) -> int:
    bits &= 31
    if bits == 0:
        return value & 0xFFFFFFFF
    return ((value << bits) | (value >> (32 - bits))) & 0xFFFFFFFF
def calculate_crc_6103(data: bytes | bytearray) -> tuple[int, int]:
    t1 = t2 = t3 = t4 = t5 = t6 = CIC_6103_SEED
    end = CHECKSUM_START + CHECKSUM_LENGTH
    for offset in range(CHECKSUM_START, end, 4):
        word = int.from_bytes(data[offset:offset + 4], "big")
        total = t6 + word
        if total > 0xFFFFFFFF:
            t4 = (t4 + 1) & 0xFFFFFFFF
        t6 = total & 0xFFFFFFFF
        t3 ^= word
        rotated = rol32(word, word & 31)
        t5 = (t5 + rotated) & 0xFFFFFFFF
        if t2 > word:
            t2 ^= rotated
        else:
            t2 ^= t6 ^ word
        t1 = (t1 + (t5 ^ word)) & 0xFFFFFFFF
    return ((t6 ^ t4) + t3) & 0xFFFFFFFF, ((t5 ^ t2) + t1) & 0xFFFFFFFF
def patch_rom(source: Path, output: Path) -> dict[str, object]:
    data = bytearray(source.read_bytes())
    source_sha = hashlib.sha256(data).hexdigest()
    if source_sha != SOURCE_SHA256:
        raise ValueError(
            f"unsupported ROM SHA-256 {source_sha}; expected DKR US Rev A {SOURCE_SHA256}"
        )

    before = int.from_bytes(data[PATCH_OFFSET:PATCH_OFFSET + 4], "big")
    if before != EXPECTED_WORD:
        raise ValueError(
            f"patch precondition failed at 0x{PATCH_OFFSET:X}: 0x{before:08X}"
        )

    data[PATCH_OFFSET:PATCH_OFFSET + 4] = REPLACEMENT_WORD.to_bytes(4, "big")
    crc1, crc2 = calculate_crc_6103(data)
    data[0x10:0x14] = crc1.to_bytes(4, "big")
    data[0x14:0x18] = crc2.to_bytes(4, "big")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return {
        "source_sha256": source_sha,
        "output_sha256": hashlib.sha256(data).hexdigest(),
        "patch_vram": f"0x{PATCH_VRAM:08X}",
        "patch_rom_offset": f"0x{PATCH_OFFSET:X}",
        "before": f"0x{before:08X}",
        "after": f"0x{REPLACEMENT_WORD:08X}",
        "crc1": f"0x{crc1:08X}",
        "crc2": f"0x{crc2:08X}",
    }
def main() -> int:
    ap = argparse.ArgumentParser(
        description="Patch DKR US Rev A so the Tracks menu populates every track ID."
    )
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()

    receipt = patch_rom(args.source, args.output)
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
