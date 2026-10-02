from pathlib import Path
import argparse, hashlib, json, struct

def sha256(data):
    return hashlib.sha256(data).hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--lut", type=lambda x: int(x, 0), default=0xED0E0)
    ap.add_argument("--asset-base", type=lambda x: int(x, 0), default=0xED1B0)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--report", required=True)
    args = ap.parse_args()

    rom = Path(args.rom)
    data = rom.read_bytes()
    count = struct.unpack_from(">I", data, args.lut)[0]
    if not 1 <= count <= 4096:
        raise SystemExit(f"invalid section count: {count}")
    offsets = [
        struct.unpack_from(">I", data, args.lut + 4 + i * 4)[0]
        for i in range(count + 1)
    ]
    if offsets[0] != 0:
        raise SystemExit(f"first relative offset is not zero: 0x{offsets[0]:X}")
    if any(a > b for a, b in zip(offsets, offsets[1:])):
        raise SystemExit("asset LUT is not monotonic")
    asset_end = args.asset_base + offsets[-1]
    if asset_end > len(data):
        raise SystemExit("asset LUT exceeds ROM size")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sections = []
    for i in range(count):
        start = args.asset_base + offsets[i]
        end = args.asset_base + offsets[i + 1]
        chunk = data[start:end]
        path = out_dir / f"section_{i:02d}_{start:08X}_{end:08X}.bin"
        path.write_bytes(chunk)
        sections.append({
            "index": i,
            "relative_start": offsets[i],
            "relative_end": offsets[i + 1],
            "rom_start": start,
            "rom_end": end,
            "size": len(chunk),
            "sha256": sha256(chunk),
            "prefix16": chunk[:16].hex(),
            "prefix_ascii": "".join(chr(x) if 32 <= x < 127 else "." for x in chunk[:16]),
            "signature_counts": {
                "MIO0": chunk.count(b"MIO0"),
                "Yaz0": chunk.count(b"Yaz0"),
                "gzip": chunk.count(b"\x1f\x8b\x08"),
                "FORM": chunk.count(b"FORM"),
                "TABL": chunk.count(b"TABL"),
            },
            "dump": str(path),
        })

    report = {
        "schema": "n64.dkr_asset_lut_unpack.v1",
        "authority_effect": "NONE",
        "rom": str(rom),
        "rom_sha256": sha256(data),
        "lut_offset": args.lut,
        "asset_base": args.asset_base,
        "section_count": count,
        "asset_end": asset_end,
        "asset_span": offsets[-1],
        "monotonic": True,
        "sections": sections,
    }
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "section_count": count, "asset_base": hex(args.asset_base),
        "asset_end": hex(asset_end), "asset_span": hex(offsets[-1]),
        "smallest": min(s["size"] for s in sections),
        "largest": max(s["size"] for s in sections),
    }, indent=2))

if __name__ == "__main__":
    main()
