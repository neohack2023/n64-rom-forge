from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.check_forbidden_payloads import find_forbidden

class ForbiddenPayloadTests(unittest.TestCase):
    def test_clean_tree_passes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "src").mkdir()
            (root / "src" / "ok.py").write_text("pass\n", encoding="utf-8")
            self.assertEqual(find_forbidden(root), [])

    def test_rom_and_baserom_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "game.z64").write_bytes(b"x")
            (root / "baserom.us.z64").write_bytes(b"x")
            findings = find_forbidden(root)
            self.assertIn("game.z64", findings)
            self.assertIn("baserom.us.z64", findings)

    def test_build_directory_payload_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "build").mkdir()
            (root / "build" / "artifact.bin").write_bytes(b"x")
            self.assertEqual(find_forbidden(root), ["build/artifact.bin"])

if __name__ == "__main__":
    unittest.main()
