from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AcceptedInput:
    sha1: str
    byte_order: str
    writable: bool = False
    sha256: str | None = None
    size_bytes: int | None = None


@dataclass(frozen=True)
class CanonicalCandidate:
    sha1: str
    byte_order: str = "z64"
    sha256: str | None = None
    size_bytes: int | None = None
    rule: str = "full-image"

    def match(self, z64: bytes) -> dict[str, Any] | None:
        if self.byte_order != "z64":
            raise ValueError("canonical candidates must currently use z64 byte order")
        size = self.size_bytes if self.size_bytes is not None else len(z64)
        if len(z64) < size:
            return None
        if self.rule == "full-image" and len(z64) != size:
            return None
        view = z64[:size]
        sha1_hex = hashlib.sha1(view).hexdigest()
        sha256_hex = hashlib.sha256(view).hexdigest()
        if sha1_hex != self.sha1.lower():
            return None
        if self.sha256 is not None and sha256_hex != self.sha256.lower():
            return None
        return {
            "canonical_rule": self.rule,
            "canonical_size_bytes": size,
            "canonical_sha1": sha1_hex,
            "canonical_sha256": sha256_hex,
            "trailing_bytes": len(z64) - size,
        }


@dataclass(frozen=True)
class GameAdapter:
    schema: str
    adapter_id: str
    game_id: str
    region: str
    revision: str
    accepted_inputs: tuple[AcceptedInput, ...]
    byte_order: str
    cic_ipl3: dict[str, Any]
    source_pins: dict[str, str]
    canonical_candidates: tuple[CanonicalCandidate, ...] = ()
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

    def match_canonical(self, z64: bytes) -> dict[str, Any] | None:
        candidates = self.canonical_candidates or tuple(
            CanonicalCandidate(
                sha1=item.sha1,
                sha256=item.sha256,
                size_bytes=item.size_bytes,
                byte_order="z64",
                rule="full-image",
            )
            for item in self.accepted_inputs
            if item.byte_order == "z64"
        )
        for candidate in candidates:
            evidence = candidate.match(z64)
            if evidence is not None:
                return {
                    "adapter_id": self.adapter_id,
                    "game_id": self.game_id,
                    "region": self.region,
                    "revision": self.revision,
                    **evidence,
                }
        return None
