from __future__ import annotations

from hashlib import sha1, sha256
from pathlib import Path
from typing import Any
from .adapters.registry import resolve_adapter
from .checksum import identify_cic, verify_header_checksum
from .receipts import WrapperInspectionReceipt
from .rom_inspector import hash_source, inspect_source

def inspect_rom(path: str | Path, adapter_id: str = "auto") -> WrapperInspectionReceipt:
    p = Path(path); before_sha1, before_sha256 = hash_source(p); inspection, z64 = inspect_source(p)
    adapter = resolve_adapter(z64, adapter_id); checksum = verify_header_checksum(z64, inspection.header, inspection.ipl3); ipl3 = identify_cic(inspection.ipl3, str(inspection.header.get("region_code", "")))
    canonical_view: dict[str, Any] | None = None; trailing_data: dict[str, Any] | None = None
    if adapter.get("status") == "MATCHED":
        size = int(adapter["canonical_size_bytes"]); canonical = z64[:size]
        canonical_view = {"byte_order": "z64", "size_bytes": size, "sha1": sha1(canonical).hexdigest(), "sha256": sha256(canonical).hexdigest(), "persisted": False}
        if len(z64) > size:
            tail = z64[size:]; trailing_data = {"size_bytes": len(tail), "sha1": sha1(tail).hexdigest(), "sha256": sha256(tail).hexdigest(), "classification": "NONCANONICAL_TRAILING_DATA", "persisted": False}
    after_sha1, after_sha256 = hash_source(p)
    source_integrity = {"before_sha1": before_sha1, "after_sha1": after_sha1, "before_sha256": before_sha256, "after_sha256": after_sha256, "unchanged": (before_sha1, before_sha256) == (after_sha1, after_sha256)}
    checksum_summary = {"status": checksum.verification.get("status", "NOT_RUN"), "cic": checksum.cic, "computed_crc1": checksum.computed_crc1, "computed_crc2": checksum.computed_crc2, "stored_crc1": checksum.stored_crc1, "stored_crc2": checksum.stored_crc2, "provenance": checksum.provenance, "repair_performed": checksum.repair_performed, "receipt": checksum.to_dict()}
    return WrapperInspectionReceipt("n64rf.wrapper-inspection-receipt.v1", inspection.source.to_dict(), inspection.normalized_view, inspection.header, ipl3, adapter, canonical_view, trailing_data, checksum_summary, {"rom_bytes_modified": False, "rom_bytes_persisted": False, "canonical_rom_persisted": False}, source_integrity)

def verify_rom(path: str | Path, adapter_id: str) -> WrapperInspectionReceipt:
    receipt = inspect_rom(path, adapter_id)
    if receipt.adapter.get("status") != "MATCHED": raise ValueError(f"ROM did not match adapter {adapter_id}")
    if receipt.checksum.get("status") not in {"PASS", "NOT_RUN"}: raise ValueError("N64 checksum verification failed")
    if not receipt.source_integrity.get("unchanged"): raise RuntimeError("source ROM changed during inspection")
    return receipt
