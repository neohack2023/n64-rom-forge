from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass(frozen=True)
class ExecutionReceipt:
    schema: str
    plan_id: str
    plan_digest: str
    repository: str
    branch: str
    phase0_state: str = "NOT_RUN"
    side_effects: dict[str, Any] = field(default_factory=dict)
    verification: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(frozen=True)
class WrapperInspectionReceipt:
    schema: str
    source: dict[str, Any]
    normalized_view: dict[str, Any]
    header: dict[str, Any]
    ipl3: dict[str, Any]
    adapter: dict[str, Any]
    canonical_view: dict[str, Any] | None
    trailing_data: dict[str, Any] | None
    checksum: dict[str, Any]
    side_effects: dict[str, Any]
    source_integrity: dict[str, Any]
    def to_dict(self) -> dict[str, Any]: return asdict(self)
