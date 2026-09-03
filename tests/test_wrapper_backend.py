from __future__ import annotations

import json, os, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
from n64rf.adapters.registry import list_adapters, resolve_adapter
from n64rf.wrapper import inspect_rom
FIXTURE = json.loads((ROOT / "tests/fixtures/goldeneye_007_us.json").read_text(encoding="utf-8"))

class WrapperBackendTests(unittest.TestCase):
    def test_registry_contains_sm64_and_goldeneye(self) -> None: self.assertEqual(list_adapters(), ("goldeneye-007-us", "sm64-us"))
    def test_registry_no_match_on_short_data(self) -> None: self.assertEqual(resolve_adapter(bytes.fromhex("80371240"), "auto")["status"], "NO_MATCH")
    def test_external_goldeneye_fixture_parity(self) -> None:
        env_name = FIXTURE["external_rom_env"]; path = os.environ.get(env_name)
        if not path: self.skipTest(f"set {env_name} to run the external ROM parity fixture")
        receipt = inspect_rom(path, "auto").to_dict()
        self.assertEqual(receipt["source"]["sha1"], FIXTURE["source"]["sha1"]); self.assertEqual(receipt["source"]["sha256"], FIXTURE["source"]["sha256"]); self.assertEqual(receipt["source"]["detected_byte_order"], FIXTURE["source"]["byte_order"])
        self.assertEqual(receipt["adapter"]["adapter_id"], "goldeneye-007-us"); self.assertEqual(receipt["canonical_view"]["sha1"], FIXTURE["canonical"]["sha1"]); self.assertEqual(receipt["canonical_view"]["sha256"], FIXTURE["canonical"]["sha256"]); self.assertEqual(receipt["trailing_data"]["sha1"], FIXTURE["tail"]["sha1"])
        self.assertEqual(receipt["checksum"]["cic"], FIXTURE["cic"]); self.assertEqual(receipt["checksum"]["stored_crc1"], FIXTURE["header"]["crc1"]); self.assertEqual(receipt["checksum"]["stored_crc2"], FIXTURE["header"]["crc2"]); self.assertEqual(receipt["checksum"]["status"], "PASS"); self.assertTrue(receipt["source_integrity"]["unchanged"]); self.assertFalse(receipt["side_effects"]["rom_bytes_modified"]); self.assertFalse(receipt["side_effects"]["canonical_rom_persisted"])

if __name__ == "__main__": unittest.main()
