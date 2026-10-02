from pathlib import Path
import argparse, json, struct

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("offset", type=lambda x: int(x, 0))
    ap.add_argument("count", type=int)
    ap.add_argument("--base", type=lambda x: int(x, 0))
    ap.add_argument("--out")
    args = ap.parse_args()

    data = Path(args.rom).read_bytes()
    rows = []
    for i in range(args.count):
        off = args.offset + i * 4
        if off + 4 > len(data):
            break
        raw = data[off:off + 4]
        value = struct.unpack(">I", raw)[0]
        signed = struct.unpack(">i", raw)[0]
        row = {"index": i, "rom_offset": off, "value_u32": value, "value_hex": f"0x{value:08X}", "value_s32": signed}
        if args.base is not None:
            target = args.base + value
            row["base_plus_value"] = target
            row["base_plus_value_hex"] = f"0x{target:X}"
            row["base_plus_value_in_rom"] = 0 <= target < len(data)
        rows.append(row)

    report = {
        "schema": "n64.word_window.v1",
        "rom": str(Path(args.rom)),
        "offset": args.offset,
        "count_requested": args.count,
        "base": args.base,
        "rows": rows,
    }
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
