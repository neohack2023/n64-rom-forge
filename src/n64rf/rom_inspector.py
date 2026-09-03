from __future__ import annotations

from dataclasses import dataclass, asdict
from hashlib import sha1, sha256
from pathlib import Path
from typing import BinaryIO, Any

_MAGIC = {
    bytes.fromhex("80371240"): "z64",
    bytes.fromhex("37804012"): "v64",
    bytes.fromhex("40123780"): "n64",
}

@dataclass(frozen=True)
class RomInspection:
    schema: str
    path_label: str
    sha1: str
    sha256: str
    byte_order: str
    read_only: bool
    header: dict[str, Any]
    cic_ipl3_evidence: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _hash_stream(stream: BinaryIO, chunk_size: int = 1024 * 1024) -> tuple[str, str]:
    h1, h256 = sha1(), sha256()
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        h1.update(chunk)
        h256.update(chunk)
    return h1.hexdigest(), h256.hexdigest()

def detect_byte_order(first4: bytes) -> str:
    return _MAGIC.get(first4, "unknown")

def _normalize_header(header: bytes, byte_order: str) -> bytes:
    if byte_order == "z64":
        return header
    if byte_order == "v64":
        if len(header) % 2:
            raise ValueError("v64 header length must be even")
        out = bytearray(header)
        for i in range(0, len(out), 2):
            out[i], out[i + 1] = out[i + 1], out[i]
        return bytes(out)
    if byte_order == "n64":
        if len(header) % 4:
            raise ValueError("n64 header length must be divisible by four")
        out = bytearray()
        for i in range(0, len(header), 4):
            out.extend(reversed(header[i:i + 4]))
        return bytes(out)
    return header

def inspect_rom(path: str | Path, *, path_label: str | None = None) -> RomInspection:
    p = Path(path)
    mode = p.stat().st_mode
    read_only = (mode & 0o222) == 0

    with p.open("rb") as f:
        first = f.read(0x40)
        order = detect_byte_order(first[:4])
        f.seek(0)
        digest1, digest256 = _hash_stream(f)

    normalized = _normalize_header(first, order)
    header: dict[str, Any] = {"magic": normalized[:4].hex()}
    if len(normalized) >= 0x18:
        header.update({
            "clock_rate": int.from_bytes(normalized[0x04:0x08], "big"),
            "entry_point": f"0x{int.from_bytes(normalized[0x08:0x0C], 'big'):08X}",
            "release": f"0x{int.from_bytes(normalized[0x0C:0x10], 'big'):08X}",
            "crc1": f"0x{int.from_bytes(normalized[0x10:0x14], 'big'):08X}",
            "crc2": f"0x{int.from_bytes(normalized[0x14:0x18], 'big'):08X}",
        })

    return RomInspection(
        schema="n64rf.rom-inspection-receipt.v1",
        path_label=path_label or p.name,
        sha1=digest1,
        sha256=digest256,
        byte_order=order,
        read_only=read_only,
        header=header,
        cic_ipl3_evidence=None,
    )
