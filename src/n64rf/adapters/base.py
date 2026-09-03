from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class AcceptedInput:
    sha1: str
    byte_order: str
    writable: bool = False

@dataclass(frozen=True)
class GameAdapter:
    schema: str
    game_id: str
    region: str
    revision: str
    accepted_inputs: tuple[AcceptedInput, ...]
    byte_order: str
    cic_ipl3: dict[str, Any]
    source_pins: dict[str, str]
    memory_layout: dict[str, Any] = field(default_factory=dict)
    segments: dict[str, Any] = field(default_factory=dict)
    compression_formats: tuple[str, ...] = ()
    asset_formats: tuple[str, ...] = ()
    emulator_requirements: tuple[str, ...] = ()
    hardware_constraints: tuple[str, ...] = ()

    def accepts(self, sha1_hex: str, byte_order: str) -> bool:
        return any(
            item.sha1 == sha1_hex.lower()
            and item.byte_order == byte_order
            and item.writable is False
            for item in self.accepted_inputs
        )
