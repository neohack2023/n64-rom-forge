from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .rom_inspector import detect_byte_order, _normalize_header

@dataclass(frozen=True)
class ChecksumReceipt:
    schema: str
    crc1: str
    crc2: str
    provenance: dict[str, Any]
    repair_performed: bool
    verification: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def read_header_checksums(path: str | Path) -> ChecksumReceipt:
    p = Path(path)
    with p.open("rb") as f:
        header = f.read(0x40)
    order = detect_byte_order(header[:4])
    normalized = _normalize_header(header, order)
    if len(normalized) < 0x18:
        raise ValueError("ROM is too small to contain CRC1/CRC2")
    crc1 = int.from_bytes(normalized[0x10:0x14], "big")
    crc2 = int.from_bytes(normalized[0x14:0x18], "big")
    return ChecksumReceipt(
        schema="n64rf.checksum-receipt.v1",
        crc1=f"0x{crc1:08X}",
        crc2=f"0x{crc2:08X}",
        provenance={
            "adapter": "n64rf.checksum.read_header_checksums",
            "repair_tool": "project-native n64cksum adapter",
            "repair_tool_status": "NOT_RUN",
        },
        repair_performed=False,
        verification={"status": "NOT_RUN"},
    )
