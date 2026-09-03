from __future__ import annotations

from .base import AcceptedInput, GameAdapter

SM64_US = GameAdapter(
    schema="n64rf.game-adapter.v1",
    adapter_id="sm64-us",
    game_id="sm64",
    region="US",
    revision="retail-us",
    accepted_inputs=(AcceptedInput(sha1="9bef1128717f958171a4afac3ed78ee2bb4e86ce", byte_order="z64", writable=False, canonical_rule="exact"),),
    byte_order="z64",
    cic_ipl3={"status": "evidence_required_at_intake", "value": None, "source": None, "confidence": None},
    source_pins={"vanilla_reference": "n64decomp/sm64@9921382a68bb0c865e5e45eb594d9c64db59b1af", "modification_target": "HackerN64/HackerSM64@3f1f7f41beac4ff0287bcb5f919efb52856ec27b"},
)
