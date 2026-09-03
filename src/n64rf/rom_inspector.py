from __future__ import annotations

import binascii
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, BinaryIO

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
class RomInspection:
    schema: str
    path_label: str
    size_bytes: int
    sha1: str
    sha256: str
    byte_order: str
    filesystem_mode_octal: str
    filesystem_writable: bool
    wrapper_open_mode: str
    header: dict[str, Any]
    ipl3: dict[str, Any]
    normalized_sha1: str
    normalized_sha256: str

    @property
    def read_only(self) -> bool:
        """Compatibility alias for the wrapper I/O policy, not POSIX mode bits."""
        return self.wrapper_open_mode == "rb"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["read_only"] = self.read_only
        return data


@dataclass(frozen=True)
class InspectedRom:
    inspection: RomInspection
    normalized_bytes: bytes


def hash_stream(stream: BinaryIO, chunk_size: int = 1024 * 1024) -> tuple[str, str]:
    h1, h256 = hashlib.sha1(), hashlib.sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        h1.update(chunk)
        h256.update(chunk)
    return h1.hexdigest(), h256.hexdigest()


def hash_file(path: str | Path) -> tuple[str, str]:
    with Path(path).open("rb") as stream:
        return hash_stream(stream)


def detect_byte_order(first4: bytes) -> str:
    return _MAGIC.get(first4, "unknown")


def normalize_to_z64(data: bytes, byte_order: str) -> bytes:
    if byte_order == "z64":
        return data
    if byte_order == "v64":
        if len(data) % 2:
            raise ValueError("v64 input length must be even")
        out = bytearray(data)
        for index in range(0, len(out), 2):
            out[index], out[index + 1] = out[index + 1], out[index]
        return bytes(out)
    if byte_order == "n64":
        if len(data) % 4:
            raise ValueError("n64 input length must be divisible by four")
        out = bytearray()
        for index in range(0, len(data), 4):
            out.extend(reversed(data[index:index + 4]))
        return bytes(out)
    raise ValueError("unsupported or unknown N64 byte order")


def _normalize_header(header: bytes, byte_order: str) -> bytes:
    return normalize_to_z64(header, byte_order)


def parse_header(z64: bytes) -> dict[str, Any]:
    if len(z64) < 0x40:
        raise ValueError("ROM is too small for the N64 header")
    image_name = z64[0x20:0x34].decode("ascii", errors="replace").rstrip("\x00 ").strip()
    game_code = z64[0x3B:0x3F].decode("ascii", errors="replace")
    region_code = chr(z64[0x3E]) if 32 <= z64[0x3E] < 127 else f"0x{z64[0x3E]:02X}"
    return {
        "magic_hex": z64[:4].hex(),
        "clock_rate": int.from_bytes(z64[0x04:0x08], "big"),
        "entry_point": f"0x{int.from_bytes(z64[0x08:0x0C], 'big'):08X}",
        "release": f"0x{int.from_bytes(z64[0x0C:0x10], 'big'):08X}",
        "crc1": f"0x{int.from_bytes(z64[0x10:0x14], 'big'):08X}",
        "crc2": f"0x{int.from_bytes(z64[0x14:0x18], 'big'):08X}",
        "image_name": image_name,
        "game_code": game_code,
        "region_code": region_code,
        "region_name": _REGION_NAMES.get(region_code, "unknown"),
        "revision": z64[0x3F],
    }


def fingerprint_ipl3(z64: bytes) -> dict[str, Any]:
    if len(z64) < 0x1000:
        return {"status": "INSUFFICIENT_DATA"}
    ipl3 = z64[0x40:0x1000]
    crc32 = binascii.crc32(ipl3) & 0xFFFFFFFF
    return {
        "status": "FINGERPRINTED",
        "md5": hashlib.md5(ipl3).hexdigest(),
        "crc32": f"0x{crc32:08X}",
    }


def inspect_source(path: str | Path, *, path_label: str | None = None) -> InspectedRom:
    p = Path(path)
    stat = p.stat()
    with p.open("rb") as stream:
        data = stream.read()

    order = detect_byte_order(data[:4])
    normalized = normalize_to_z64(data, order)
    inspection = RomInspection(
        schema="n64rf.rom-inspection-receipt.v1",
        path_label=path_label or p.name,
        size_bytes=len(data),
        sha1=hashlib.sha1(data).hexdigest(),
        sha256=hashlib.sha256(data).hexdigest(),
        byte_order=order,
        filesystem_mode_octal=oct(stat.st_mode & 0o777),
        filesystem_writable=bool(stat.st_mode & 0o222),
        wrapper_open_mode="rb",
        header=parse_header(normalized),
        ipl3=fingerprint_ipl3(normalized),
        normalized_sha1=hashlib.sha1(normalized).hexdigest(),
        normalized_sha256=hashlib.sha256(normalized).hexdigest(),
    )
    return InspectedRom(inspection=inspection, normalized_bytes=normalized)


def inspect_rom(path: str | Path, *, path_label: str | None = None) -> RomInspection:
    """Compatibility entrypoint returning the core inspection receipt only."""
    return inspect_source(path, path_label=path_label).inspection
