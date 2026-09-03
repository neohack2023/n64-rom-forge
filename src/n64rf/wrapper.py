from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .adapters.registry import resolve_adapter
from .checksum import classify_cic, verify_n64_checksum
from .receipts import WrapperInspectionReceipt
from .rom_inspector import hash_file, inspect_source


def inspect_rom(path: str | Path, adapter_id: str = "auto") -> WrapperInspectionReceipt:
    p = Path(path)
    inspected = inspect_source(p)
    core = inspected.inspection
    z64 = inspected.normalized_bytes

    adapter = resolve_adapter(z64, adapter_id)
    cic = classify_cic(core.ipl3, str(core.header.get("region_code", "")))
    checksum_receipt = verify_n64_checksum(z64, cic)

    canonical_view: dict[str, Any] | None = None
    trailing_data: dict[str, Any] | None = None
    if adapter.get("status") == "MATCHED":
        size = int(adapter["canonical_size_bytes"])
        canonical = z64[:size]
        canonical_view = {
            "byte_order": "z64",
            "size_bytes": size,
            "sha1": hashlib.sha1(canonical).hexdigest(),
            "sha256": hashlib.sha256(canonical).hexdigest(),
            "persisted": False,
        }
        tail = z64[size:]
        if tail:
            trailing_data = {
                "size_bytes": len(tail),
                "sha1": hashlib.sha1(tail).hexdigest(),
                "sha256": hashlib.sha256(tail).hexdigest(),
                "classification": "NONCANONICAL_TRAILING_DATA",
                "persisted": False,
            }

    after_sha1, after_sha256 = hash_file(p)
    source_integrity = "PASS" if (after_sha1, after_sha256) == (core.sha1, core.sha256) else "FAIL"
    source = {
        "path_label": core.path_label,
        "size_bytes": core.size_bytes,
        "filesystem_mode_octal": core.filesystem_mode_octal,
        "filesystem_writable": core.filesystem_writable,
        "wrapper_open_mode": core.wrapper_open_mode,
        "wrapper_source_mutation": source_integrity != "PASS",
        "source_integrity": source_integrity,
        "magic_hex": bytes.fromhex(core.header["magic_hex"]).hex() if core.byte_order == "z64" else None,
        "detected_byte_order": core.byte_order,
        "sha1": core.sha1,
        "sha256": core.sha256,
        "after_sha1": after_sha1,
        "after_sha256": after_sha256,
    }
    # Preserve the source representation magic separately from canonical header magic.
    with p.open("rb") as stream:
        source["magic_hex"] = stream.read(4).hex()

    return WrapperInspectionReceipt(
        schema="n64rf.wrapper-inspection-receipt.v1",
        source=source,
        normalized_view={
            "byte_order": "z64",
            "sha1": core.normalized_sha1,
            "sha256": core.normalized_sha256,
            "persisted": False,
        },
        header=core.header,
        ipl3=core.ipl3,
        cic=cic,
        adapter=adapter,
        canonical_view=canonical_view,
        trailing_data=trailing_data,
        checksum=checksum_receipt.to_dict(),
        side_effects={
            "rom_bytes_modified": False,
            "rom_bytes_persisted": False,
            "canonical_rom_persisted": False,
            "source_integrity": source_integrity,
        },
    )


def wrapper_passed(receipt: WrapperInspectionReceipt) -> bool:
    data = receipt.to_dict()
    return (
        data["source"]["source_integrity"] == "PASS"
        and data["adapter"].get("status") == "MATCHED"
        and data["checksum"].get("verification", {}).get("status") == "PASS"
    )
