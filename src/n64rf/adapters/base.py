from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1, sha256
from typing import Any

@dataclass(frozen=True)
class AcceptedInput:
    sha1: str
    byte_order: str
    writable: bool = False
    sha256: str | None = None
    size_bytes: int | None = None
    canonical_rule: str = "exact"

@dataclass(frozen=True)
class GameAdapter:
    schema: str
    adapter_id: str
    game_id: str
    region: str
    revision: str | int
    accepted_inputs: tuple[AcceptedInput, ...]
    byte_order: str
    cic_ipl3: dict[str, Any]
    source_pins: dict[str, str]
    header_game_code: str | None = None
    memory_layout: dict[str, Any] = field(default_factory=dict)
    segments: dict[str, Any] = field(default_factory=dict)
    compression_formats: tuple[str, ...] = ()
    asset_formats: tuple[str, ...] = ()
    emulator_requirements: tuple[str, ...] = ()
    hardware_constraints: tuple[str, ...] = ()

    def accepts(self, sha1_hex: str, byte_order: str) -> bool:
        return any(item.sha1 == sha1_hex.lower() and item.byte_order == byte_order and item.writable is False for item in self.accepted_inputs)

    def match_canonical(self, z64: bytes) -> dict[str, Any] | None:
        for candidate in self.accepted_inputs:
            size = candidate.size_bytes if candidate.size_bytes is not None else len(z64)
            if candidate.canonical_rule == "exact" and len(z64) != size:
                continue
            if candidate.canonical_rule == "canonical-prefix" and len(z64) < size:
                continue
            if candidate.canonical_rule not in {"exact", "canonical-prefix"}:
                raise ValueError(f"unsupported canonical rule: {candidate.canonical_rule}")
            view = z64[:size]
            digest1 = sha1(view).hexdigest()
            digest256 = sha256(view).hexdigest()
            if digest1 != candidate.sha1:
                continue
            if candidate.sha256 is not None and digest256 != candidate.sha256:
                continue
            return {"adapter_id": self.adapter_id, "game_id": self.game_id, "region": self.region, "revision": self.revision, "canonical_rule": candidate.canonical_rule, "canonical_size_bytes": size, "canonical_sha1": digest1, "canonical_sha256": digest256, "trailing_bytes": len(z64) - size}
        return None
