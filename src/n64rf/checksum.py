from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .rom_inspector import detect_byte_order, normalize_to_z64

_CIC_SEEDS = {
    "CIC-NUS-6101": 0xF8CA4DDC,
    "CIC-NUS-6102": 0xF8CA4DDC,
    "CIC-NUS-6103": 0xA3886759,
    "CIC-NUS-6105": 0xDF26F436,
    "CIC-NUS-6106": 0x1FEA617A,
}

_IPL3_FINGERPRINTS = {
    ("e24dd796b2fa16511521139d28c8356b", "90bb6cb5"): {
        "family": "6102/7101",
        "ntsc_cic": "CIC-NUS-6102",
    },
}


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


def classify_cic(ipl3: dict[str, Any], region_code: str) -> dict[str, Any]:
    key = (
        str(ipl3.get("md5", "")).lower(),
        str(ipl3.get("crc32", "")).lower().removeprefix("0x"),
    )
    evidence = _IPL3_FINGERPRINTS.get(key)
    if not evidence:
        return {"status": "UNKNOWN", "cic": None, "confidence": "unknown"}
    cic = evidence.get("ntsc_cic") if region_code in {"E", "J"} else None
    if cic is None:
        return {"status": "FAMILY_MATCH_REGION_UNRESOLVED", "cic": None, **evidence, "confidence": "medium"}
    return {"status": "MATCHED", "cic": cic, **evidence, "confidence": "high"}


def _rol32(value: int, shift: int) -> int:
    shift &= 31
    value &= 0xFFFFFFFF
    return ((value << shift) | (value >> ((32 - shift) & 31))) & 0xFFFFFFFF


def recompute_n64_crc(z64: bytes, cic: str) -> tuple[int, int]:
    if cic not in _CIC_SEEDS:
        raise ValueError(f"unsupported CIC: {cic}")
    if len(z64) < 0x101000:
        raise ValueError("ROM too small for N64 checksum range")

    seed = _CIC_SEEDS[cic]
    t1 = t2 = t3 = t4 = t5 = t6 = seed
    for offset in range(0x1000, 0x101000, 4):
        word = int.from_bytes(z64[offset:offset + 4], "big")
        total = t6 + word
        if total > 0xFFFFFFFF:
            t4 = (t4 + 1) & 0xFFFFFFFF
        t6 = total & 0xFFFFFFFF
        t3 ^= word
        rotated = _rol32(word, word & 0x1F)
        t5 = (t5 + rotated) & 0xFFFFFFFF
        t2 ^= rotated if t2 > word else t6 ^ word
        t2 &= 0xFFFFFFFF
        if cic == "CIC-NUS-6105":
            boot_offset = 0x0750 + (offset & 0xFF)
            boot_word = int.from_bytes(z64[boot_offset:boot_offset + 4], "big")
            t1 = (t1 + (boot_word ^ word)) & 0xFFFFFFFF
        else:
            t1 = (t1 + (t5 ^ word)) & 0xFFFFFFFF

    if cic == "CIC-NUS-6103":
        return ((t6 ^ t4) + t3) & 0xFFFFFFFF, ((t5 ^ t2) + t1) & 0xFFFFFFFF
    if cic == "CIC-NUS-6106":
        return ((t6 * t4) + t3) & 0xFFFFFFFF, ((t5 * t2) + t1) & 0xFFFFFFFF
    return (t6 ^ t4 ^ t3) & 0xFFFFFFFF, (t5 ^ t2 ^ t1) & 0xFFFFFFFF


def verify_n64_checksum(z64: bytes, cic_evidence: dict[str, Any]) -> ChecksumReceipt:
    stored_crc1 = int.from_bytes(z64[0x10:0x14], "big")
    stored_crc2 = int.from_bytes(z64[0x14:0x18], "big")
    cic = cic_evidence.get("cic")
    verification: dict[str, Any] = {"status": "NOT_RUN", "cic": cic}
    if cic in _CIC_SEEDS:
        computed_crc1, computed_crc2 = recompute_n64_crc(z64, cic)
        verification = {
            "status": "PASS" if (stored_crc1, stored_crc2) == (computed_crc1, computed_crc2) else "FAIL",
            "cic": cic,
            "computed_crc1": f"0x{computed_crc1:08X}",
            "computed_crc2": f"0x{computed_crc2:08X}",
            "stored_crc1": f"0x{stored_crc1:08X}",
            "stored_crc2": f"0x{stored_crc2:08X}",
        }
    return ChecksumReceipt(
        schema="n64rf.checksum-receipt.v1",
        crc1=f"0x{stored_crc1:08X}",
        crc2=f"0x{stored_crc2:08X}",
        provenance={
            "adapter": "n64rf.checksum.verify_n64_checksum",
            "repair_tool": "project-native n64cksum adapter",
            "repair_tool_status": "NOT_RUN",
            "cic_evidence": cic_evidence,
        },
        repair_performed=False,
        verification=verification,
    )


def read_header_checksums(path: str | Path) -> ChecksumReceipt:
    p = Path(path)
    with p.open("rb") as stream:
        data = stream.read()
    order = detect_byte_order(data[:4])
    z64 = normalize_to_z64(data, order)
    return ChecksumReceipt(
        schema="n64rf.checksum-receipt.v1",
        crc1=f"0x{int.from_bytes(z64[0x10:0x14], 'big'):08X}",
        crc2=f"0x{int.from_bytes(z64[0x14:0x18], 'big'):08X}",
        provenance={
            "adapter": "n64rf.checksum.read_header_checksums",
            "repair_tool": "project-native n64cksum adapter",
            "repair_tool_status": "NOT_RUN",
        },
        repair_performed=False,
        verification={"status": "NOT_RUN"},
    )
