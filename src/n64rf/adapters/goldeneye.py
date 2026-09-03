from __future__ import annotations

from .base import AcceptedInput, CanonicalCandidate, GameAdapter

GOLDENEYE_US = GameAdapter(
    schema="n64rf.game-adapter.v1",
    adapter_id="goldeneye-007-us",
    game_id="goldeneye-007",
    region="US",
    revision="0",
    accepted_inputs=(
        AcceptedInput(
            sha1="abe01e4aeb033b6c0836819f549c791b26cfde83",
            sha256="2cdcec8a9f0cb6e36337f3ee39d8ad105dc8afa6ba1c02d466e8f5b771f9a162",
            byte_order="z64",
            size_bytes=12 * 1024 * 1024,
            writable=False,
        ),
    ),
    canonical_candidates=(
        CanonicalCandidate(
            sha1="abe01e4aeb033b6c0836819f549c791b26cfde83",
            sha256="2cdcec8a9f0cb6e36337f3ee39d8ad105dc8afa6ba1c02d466e8f5b771f9a162",
            byte_order="z64",
            size_bytes=12 * 1024 * 1024,
            rule="canonical-prefix",
        ),
    ),
    byte_order="z64",
    cic_ipl3={
        "status": "evidence_backed_candidate",
        "value": "CIC-NUS-6102",
        "ipl3_md5": "e24dd796b2fa16511521139d28c8356b",
        "ipl3_crc32": "0x90BB6CB5",
        "confidence": "high",
    },
    source_pins={
        "decomp": "n64decomp/007",
        "intake_receipt": "N64RF-GE007-INTAKE-01",
    },
)
