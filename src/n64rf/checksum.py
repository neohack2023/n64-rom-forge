from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

CIC_SEEDS = {"CIC-NUS-6101": 0xF8CA4DDC, "CIC-NUS-6102": 0xF8CA4DDC, "CIC-NUS-6103": 0xA3886759, "CIC-NUS-6105": 0xDF26F436, "CIC-NUS-6106": 0x1FEA617A}
IPL3_FINGERPRINTS = {("e24dd796b2fa16511521139d28c8356b", "0x90BB6CB5"): {"family": "6102/7101", "ntsc_cic": "CIC-NUS-6102"}}

@dataclass(frozen=True)
class ChecksumReceipt:
    schema: str
    stored_crc1: str
    stored_crc2: str
    computed_crc1: str | None
    computed_crc2: str | None
    cic: str | None
    provenance: dict[str, Any]
    repair_performed: bool
    verification: dict[str, Any]
    @property
    def crc1(self) -> str: return self.stored_crc1
    @property
    def crc2(self) -> str: return self.stored_crc2
    def to_dict(self) -> dict[str, Any]: return asdict(self)

def _rol32(value: int, shift: int) -> int:
    shift &= 31; value &= 0xFFFFFFFF
    return ((value << shift) | (value >> ((32 - shift) & 31))) & 0xFFFFFFFF

def identify_cic(ipl3: dict[str, Any], region_code: str) -> dict[str, Any]:
    key = (str(ipl3.get("md5", "")), str(ipl3.get("crc32", "")))
    evidence = IPL3_FINGERPRINTS.get(key)
    if evidence is None: return {"status": "UNKNOWN_FINGERPRINT", **ipl3}
    result = {"status": "MATCHED_FINGERPRINT", **ipl3, **evidence}
    if region_code in {"E", "J"}: result["cic"] = evidence["ntsc_cic"]
    return result

def recompute_n64_crc(z64: bytes, cic: str) -> tuple[int, int]:
    if cic not in CIC_SEEDS: raise ValueError(f"unsupported CIC: {cic}")
    if len(z64) < 0x101000: raise ValueError("ROM too small for N64 checksum range")
    seed = CIC_SEEDS[cic]; t1 = t2 = t3 = t4 = t5 = t6 = seed
    for offset in range(0x1000, 0x101000, 4):
        d = int.from_bytes(z64[offset:offset + 4], "big"); total = t6 + d
        if total > 0xFFFFFFFF: t4 = (t4 + 1) & 0xFFFFFFFF
        t6 = total & 0xFFFFFFFF; t3 ^= d; rotated = _rol32(d, d & 0x1F); t5 = (t5 + rotated) & 0xFFFFFFFF
        if t2 > d: t2 ^= rotated
        else: t2 ^= t6 ^ d
        t2 &= 0xFFFFFFFF
        if cic == "CIC-NUS-6105":
            boot_off = 0x0750 + (offset & 0xFF); boot_word = int.from_bytes(z64[boot_off:boot_off + 4], "big"); t1 = (t1 + (boot_word ^ d)) & 0xFFFFFFFF
        else: t1 = (t1 + (t5 ^ d)) & 0xFFFFFFFF
    if cic == "CIC-NUS-6103": crc1, crc2 = ((t6 ^ t4) + t3) & 0xFFFFFFFF, ((t5 ^ t2) + t1) & 0xFFFFFFFF
    elif cic == "CIC-NUS-6106": crc1, crc2 = ((t6 * t4) + t3) & 0xFFFFFFFF, ((t5 * t2) + t1) & 0xFFFFFFFF
    else: crc1, crc2 = (t6 ^ t4 ^ t3) & 0xFFFFFFFF, (t5 ^ t2 ^ t1) & 0xFFFFFFFF
    return crc1, crc2

def verify_header_checksum(z64: bytes, header: dict[str, Any], ipl3: dict[str, Any]) -> ChecksumReceipt:
    cic_evidence = identify_cic(ipl3, str(header.get("region_code", ""))); cic = cic_evidence.get("cic")
    stored_crc1, stored_crc2 = str(header["crc1"]), str(header["crc2"])
    if cic not in CIC_SEEDS:
        return ChecksumReceipt("n64rf.checksum-receipt.v1", stored_crc1, stored_crc2, None, None, None, {"algorithm": "n64rf.checksum", "cic_evidence": cic_evidence}, False, {"status": "NOT_RUN", "reason": "unsupported_or_unknown_cic"})
    crc1, crc2 = recompute_n64_crc(z64, str(cic)); computed_crc1, computed_crc2 = f"0x{crc1:08X}", f"0x{crc2:08X}"
    status = "PASS" if (computed_crc1, computed_crc2) == (stored_crc1, stored_crc2) else "FAIL"
    return ChecksumReceipt("n64rf.checksum-receipt.v1", stored_crc1, stored_crc2, computed_crc1, computed_crc2, str(cic), {"algorithm": "n64rf.checksum", "cic_evidence": cic_evidence}, False, {"status": status})
