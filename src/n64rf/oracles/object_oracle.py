from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ObjectOracleReceipt:
    schema: str
    candidate_sha256: str
    reference_sha256: str
    target_identity: str
    objdiff: dict[str, Any]
    collateral_gate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _sha256_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def scaffold_receipt(
    candidate: str | Path,
    reference: str | Path,
    *,
    target_identity: str,
    objdiff_version: str = "v3.8.1",
) -> ObjectOracleReceipt:
    """Prepare evidence for a later objdiff invocation.

    This scaffold deliberately does not claim relocation-aware equivalence. A real
    Phase 0 run must execute the pinned objdiff adapter and replace `status`.
    """
    c, r = Path(candidate), Path(reference)
    return ObjectOracleReceipt(
        schema="n64rf.object-oracle-receipt.v1",
        candidate_sha256=_sha256_file(c),
        reference_sha256=_sha256_file(r),
        target_identity=target_identity,
        objdiff={
            "tool": "encounter/objdiff",
            "version": objdiff_version,
            "status": "NOT_RUN",
            "relocation_aware": True,
        },
        collateral_gate={"status": "NOT_RUN", "changed_objects": []},
    )
