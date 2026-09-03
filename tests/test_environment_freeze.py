from __future__ import annotations
import ast
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

    def test_snapshot_resolver_remains_python36_compatible(self) -> None:
        resolver = ROOT / "scripts" / "resolve_ubuntu_snapshot.py"
        source = resolver.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(resolver), feature_version=(3, 6))

        future_features = {
            alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module == "__future__"
            for alias in node.names
        }
        self.assertNotIn("annotations", future_features)

        builtin_generics = {
            node.value.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id in {"dict", "list", "set", "tuple"}
        }
        self.assertEqual(builtin_generics, set())

        unsupported_text_keywords = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and any(keyword.arg == "text" for keyword in node.keywords)
        ]
        self.assertEqual(unsupported_text_keywords, [])


if __name__ == "__main__":
    unittest.main()
