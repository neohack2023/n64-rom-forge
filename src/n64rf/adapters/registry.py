from __future__ import annotations

from typing import Any

from .base import GameAdapter
from .goldeneye import GOLDENEYE_US
from .sm64 import SM64_US

_ADAPTERS: dict[str, GameAdapter] = {
    adapter.adapter_id: adapter
    for adapter in (SM64_US, GOLDENEYE_US)
}


def list_adapters() -> tuple[str, ...]:
    return tuple(sorted(_ADAPTERS))


def get_adapter(adapter_id: str) -> GameAdapter:
    try:
        return _ADAPTERS[adapter_id]
    except KeyError as exc:
        raise ValueError(f"unknown adapter: {adapter_id}") from exc


def resolve_adapter(z64: bytes, adapter_id: str = "auto") -> dict[str, Any]:
    candidates = _ADAPTERS.values() if adapter_id == "auto" else (get_adapter(adapter_id),)
    matches = [evidence for adapter in candidates if (evidence := adapter.match_canonical(z64)) is not None]
    if not matches:
        return {"status": "NO_MATCH"}
    if len(matches) > 1:
        return {"status": "AMBIGUOUS", "matches": matches}
    return {"status": "MATCHED", **matches[0]}
