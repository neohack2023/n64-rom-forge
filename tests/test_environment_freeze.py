from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hash_environment import canonical_digest, digest_without_fields


class EnvironmentFreezeContractTests(unittest.TestCase):
    def test_plan_digest_is_stable(self) -> None:
        plan = json.loads((ROOT / "config" / "environment.freeze.plan.json").read_text(encoding="utf-8"))
        self.assertEqual(digest_without_fields(plan, "plan_digest", "plan_digest_rule"), plan["plan_digest"])
        self.assertEqual(plan["base"]["branch"], "main")
        self.assertEqual(plan["base"]["commit"], "65f251cc350d09c375a8d8ae2f2af0d1c8742511")

    def test_environment_schemas_parse(self) -> None:
        for name in ("environment-lock.v1.schema.json", "environment-freeze-receipt.v1.schema.json"):
            parsed = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertEqual(parsed["type"], "object")

    def test_canonical_digest_is_order_independent(self) -> None:
        self.assertEqual(canonical_digest({"b": 2, "a": 1}), canonical_digest({"a": 1, "b": 2}))


if __name__ == "__main__":
    unittest.main()
