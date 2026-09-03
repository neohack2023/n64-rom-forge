from .base import AcceptedInput, CanonicalCandidate, GameAdapter
from .goldeneye import GOLDENEYE_US
from .registry import get_adapter, list_adapters, resolve_adapter
from .sm64 import SM64_US

__all__ = [
    "AcceptedInput",
    "CanonicalCandidate",
    "GameAdapter",
    "GOLDENEYE_US",
    "SM64_US",
    "get_adapter",
    "list_adapters",
    "resolve_adapter",
]
