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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
