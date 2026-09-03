from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import md5, sha1, sha256
from pathlib import Path
from typing import Any
import binascii

_MAGIC = {
    bytes.fromhex("80371240"): "z64",
    bytes.fromhex("37804012"): "v64",
    bytes.fromhex("40123780"): "n64",
}

_REGION_NAMES = {
    "E": "USA/NTSC",
    "J": "Japan/NTSC",
    "P": "Europe/PAL",
}

@dataclass(frozen=True)
class SourceEvidence:
    path_label: str
    size_bytes: int
    filesystem_mode_octal: str
    filesystem_writable: bool
    wrapper_open_mode: str
    wrapper_source_mutation: bool
    magic_hex: str
    detected_byte_order: str
    sha1: str
    sha256: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(frozen=True)
class RomInspection:
    schema: str
    source: SourceEvidence
    normalized_view: dict[str, Any]
    header: dict[str, Any]
    ipl3: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _hash_bytes(data: bytes) -> tuple[str, str]:
    return sha1(data).hexdigest(), sha256(data).hexdigest()

def detect_byte_order(first4: bytes) -> str:
    return _MAGIC.get(first4, "unknown")

def normalize_to_z64(data: bytes, byte_order: str) -> bytes:
    if byte_order == "z64":
        return data
    if byte_order == "v64":
        if len(data) % 2:
            raise ValueError("v64 input length must be even")
        out = bytearray(data)
        for i in range(0, len(out), 2):
            out[i], out[i + 1] = out[i + 1], out[i]
        return bytes(out)
    if byte_order == "n64":
        if len(data) % 4:
            raise ValueError("n64 input length must be divisible by four")
        out = bytearray()
        for i in range(0, len(data), 4):
            out.extend(reversed(data[i:i + 4]))
        return bytes(out)
    raise ValueError("unsupported or unknown N64 byte order")

def parse_header(z64: bytes) -> dict[str, Any]:
    if len(z64) < 0x40:
        raise ValueError("ROM too small for N64 header")
    region_code = chr(z64[0x3E]) if 32 <= z64[0x3E] < 127 else f"0x{z64[0x3E]:02X}"
    return {
        "magic_hex": z64[:4].hex(),
        "entry_point": f"0x{int.from_bytes(z64[0x08:0x0C], 'big'):08X}",
        "crc1": f"0x{int.from_bytes(z64[0x10:0x14], 'big'):08X}",
        "crc2": f"0x{int.from_bytes(z64[0x14:0x18], 'big'):08X}",
        "image_name": z64[0x20:0x34].decode("ascii", errors="replace").rstrip("\x00 ").strip(),
        "game_code": z64[0x3B:0x3F].decode("ascii", errors="replace"),
        "region_code": region_code,
        "region_name": _REGION_NAMES.get(region_code, "unknown"),
        "revision": z64[0x3F],
    }

def fingerprint_ipl3(z64: bytes) -> dict[str, Any]:
    if len(z64) < 0x1000:
        return {"status": "INSUFFICIENT_DATA"}
    ipl3 = z64[0x40:0x1000]
    crc32_value = binascii.crc32(ipl3) & 0xFFFFFFFF
    return {
        "status": "FINGERPRINTED",
        "md5": md5(ipl3).hexdigest(),
        "crc32": f"0x{crc32_value:08X}",
    }

def inspect_source(path: str | Path) -> tuple[RomInspection, bytes]:
    p = Path(path)
    stat = p.stat()
    with p.open("rb") as stream:
        data = stream.read()
    if len(data) < 4:
        raise ValueError("ROM is too small to contain N64 byte-order magic")
    raw_sha1, raw_sha256 = _hash_bytes(data)
    byte_order = detect_byte_order(data[:4])
    z64 = normalize_to_z64(data, byte_order)
    normalized_sha1, normalized_sha256 = _hash_bytes(z64)
    evidence = SourceEvidence(
        path_label=p.name,
        size_bytes=len(data),
        filesystem_mode_octal=oct(stat.st_mode & 0o777),
        filesystem_writable=bool(stat.st_mode & 0o222),
        wrapper_open_mode="rb",
        wrapper_source_mutation=False,
        magic_hex=data[:4].hex(),
        detected_byte_order=byte_order,
        sha1=raw_sha1,
        sha256=raw_sha256,
    )
    inspection = RomInspection(
        schema="n64rf.rom-inspection-receipt.v1",
        source=evidence,
        normalized_view={"byte_order": "z64", "sha1": normalized_sha1, "sha256": normalized_sha256, "persisted": False},
        header=parse_header(z64),
        ipl3=fingerprint_ipl3(z64),
    )
    return inspection, z64

def hash_source(path: str | Path) -> tuple[str, str]:
    with Path(path).open("rb") as stream:
        data = stream.read()
    return _hash_bytes(data)
