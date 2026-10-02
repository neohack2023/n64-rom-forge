from pathlib import Path
import argparse, hashlib, json, zlib

CIC_BY_BOOT = {
    "90BB6CB5": "CIC-NUS-6102",
    "98BC2C86": "CIC-NUS-6105",
    "ACC8580A": "CIC-NUS-6106",
    "0B050EE0": "CIC-NUS-6103",
    "6170A4A1": "CIC-NUS-6101",
}

def digest(data, name):
    h = hashlib.new(name)
    h.update(data)
    return h.hexdigest()

def offsets(data, sig, limit=32):
    out, pos = [], 0
    while len(out) < limit:
        pos = data.find(sig, pos)
        if pos < 0:
            break
        out.append(pos)
        pos += 1
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--out")
    args = ap.parse_args()
    path = Path(args.rom)
    data = path.read_bytes()
    boot_crc = f"{zlib.crc32(data[0x40:0x1000]) & 0xffffffff:08X}"
    signatures = {
        "MIO0": b"MIO0", "Yaz0": b"Yaz0", "gzip": b"\x1f\x8b\x08",
        "FORM": b"FORM", "UVRM": b"UVRM", "TABL": b"TABL",
        "zlib_7801": b"\x78\x01", "zlib_789c": b"\x78\x9c",
        "zlib_78da": b"\x78\xda",
    }
    hits = {name: offsets(data, sig) for name, sig in signatures.items()}
    report = {
        "schema": "n64.generic_rom_profile.v1",
        "authority_effect": "NONE",
        "rom": {
            "path": str(path), "size": len(data),
            "md5": digest(data, "md5"), "sha1": digest(data, "sha1"),
            "sha256": digest(data, "sha256"),
        },
        "header": {
            "magic": data[:4].hex(),
            "internal_name": data[0x20:0x34].decode("ascii", "replace").rstrip("\x00 "),
            "game_code": data[0x3B:0x3F].decode("ascii", "replace"),
            "version": data[0x3F],
            "header_entrypoint": f"0x{int.from_bytes(data[8:12], 'big'):08X}",
            "boot_crc32": boot_crc,
            "cic_guess": CIC_BY_BOOT.get(boot_crc, "UNKNOWN"),
        },
        "raw_signature_counts": {name: len(offsets(data, sig, 1000000)) for name, sig in signatures.items()},
        "signature_offsets_sample": {
            name: [f"0x{x:X}" for x in vals] for name, vals in hits.items()
        },
        "evidence_limits": [
            "Raw signatures are candidate evidence only and do not prove resource boundaries.",
            "CIC classification is a boot-code fingerprint heuristic.",
            "This profile is title-blind and contains no web/decomp-derived structural claims.",
        ],
    }
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
