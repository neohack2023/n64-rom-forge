from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from n64rf.wrapper import inspect_rom, wrapper_passed


class WrapperTests(unittest.TestCase):
    def test_goldeneye_fixture_parity_when_available(self) -> None:
        fixture = os.environ.get("N64RF_GOLDENEYE_FIXTURE")
        if not fixture:
            self.skipTest("N64RF_GOLDENEYE_FIXTURE not set")
        expected = json.loads((ROOT / "tests/fixtures/goldeneye_us.expected.json").read_text(encoding="utf-8"))
        receipt = inspect_rom(fixture)
        data = receipt.to_dict()
        self.assertTrue(wrapper_passed(receipt))
        self.assertEqual(data["source"]["sha1"], expected["source_sha1"])
        self.assertEqual(data["source"]["sha256"], expected["source_sha256"])
        self.assertEqual(data["source"]["detected_byte_order"], expected["source_byte_order"])
        self.assertEqual(data["source"]["size_bytes"], expected["source_size_bytes"])
        self.assertEqual(data["source"]["source_integrity"], "PASS")
        self.assertEqual(data["adapter"]["adapter_id"], expected["adapter_id"])
        self.assertEqual(data["canonical_view"]["sha1"], expected["canonical_sha1"])
        self.assertEqual(data["canonical_view"]["sha256"], expected["canonical_sha256"])
        self.assertEqual(data["canonical_view"]["size_bytes"], expected["canonical_size_bytes"])
        self.assertEqual(data["trailing_data"]["sha1"], expected["tail_sha1"])
        self.assertEqual(data["trailing_data"]["sha256"], expected["tail_sha256"])
        self.assertEqual(data["trailing_data"]["size_bytes"], expected["tail_size_bytes"])
        self.assertEqual(data["cic"]["cic"], expected["cic"])
        self.assertEqual(data["checksum"]["verification"]["stored_crc1"], expected["crc1"])
        self.assertEqual(data["checksum"]["verification"]["stored_crc2"], expected["crc2"])
        self.assertEqual(data["checksum"]["verification"]["status"], "PASS")
        self.assertFalse(data["side_effects"]["rom_bytes_modified"])
        self.assertFalse(data["side_effects"]["rom_bytes_persisted"])
        self.assertFalse(data["side_effects"]["canonical_rom_persisted"])


if __name__ == "__main__":
    unittest.main()
