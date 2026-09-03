from __future__ import annotations
import hashlib
import json
from typing import Any


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_digest(value: Any) -> str:
    return "SHA256:" + sha256_hex(canonical_json_bytes(value))


def digest_without_fields(value: dict[str, Any], *fields: str) -> str:
    clone = {k: v for k, v in value.items() if k not in set(fields)}
    return canonical_digest(clone)
